"""LoRA compatibility at the native loader boundary; never rewrite model files."""
import logging
import re


def load_checked_sdxl(model, clip, weights, strength_model, strength_clip, metadata=None, report=None):
    import comfy.lora
    import comfy.lora_convert

    key_map = comfy.lora.model_lora_keys_unet(model.model, {})
    key_map = comfy.lora.model_lora_keys_clip(clip.cond_stage_model, key_map)
    loaded = comfy.lora.load_lora(comfy.lora_convert.convert_lora(weights), key_map)
    if not loaded:
        raise ValueError("This LoRA did not match the SDXL checkpoint or its text encoders. Choose an SDXL LoRA.")
    result, text = model.clone(), clip.clone()
    model_keys = set(result.add_patches(loaded, strength_model))
    clip_keys = set(text.add_patches(loaded, strength_clip))
    applied = model_keys | clip_keys
    if not applied or set(loaded) - applied:
        raise ValueError("Comfy could not apply all recognized SDXL LoRA weights. No image was generated.")
    if metadata:
        result.set_attachments("lora_metadata", metadata)
        text.patcher.set_attachments("lora_metadata", metadata)
    if report is not None:
        report.update(status="matched_weights", matched_patches=len(loaded), applied_patches=len(applied),
                      model_patches=len(model_keys), clip_patches=len(clip_keys), visual_compatibility="not_verified")
    return result, text


def flux3_aliases(native):
    """Diffusers FLUX 3 block names, preserving Comfy's fused-QKV slice targets.

    Names correspond to diffusers/models/transformers/transformer_flux3.py and
    comfy/ldm/flux3/model.py. An upstream mapping always takes precedence.
    """
    result = dict(native)
    projections = {
        "q_proj": "attn.to_q", "k_proj": "attn.to_k", "v_proj": "attn.to_v",
        "attn_out": "attn.to_out.0", "mlp_in": "ff.linear_in", "mlp_out": "ff.linear_out",
    }
    pattern = re.compile(
        r"diffusion_model\.(single_blocks|txt_mode_blocks|content_mode_blocks\.(?:image|image_cond))"
        r"\.(\d+)\.(q_proj|k_proj|v_proj|attn_out|mlp_in|mlp_out)$"
    )
    for key, target in native.items():
        match = pattern.fullmatch(key)
        if not match:
            continue
        block, index, projection = match.groups()
        block = block.replace("single_blocks", "single_transformer_blocks").replace("content_mode_blocks", "mode_blocks")
        result.setdefault(f"transformer.{block}.{index}.{projections[projection]}", target)
    return result


def load_checked(model, weights, strength, metadata=None, report=None):
    import comfy.lora
    import comfy.lora_convert
    import comfy.model_base

    if strength == 0:
        if report is not None:
            report.update(status="disabled")
        return model
    key_map = comfy.lora.model_lora_keys_unet(model.model, {})
    if isinstance(model.model, comfy.model_base.Flux3):
        key_map = flux3_aliases(key_map)
    loaded = comfy.lora.load_lora(comfy.lora_convert.convert_lora(weights), key_map)
    if not loaded:
        raise ValueError("This LoRA did not match any weights in the selected image model. Choose a compatible LoRA or disable it.")
    result = model.clone()
    applied = result.add_patches(loaded, strength)
    if not applied:
        raise ValueError("Comfy could not apply this LoRA to the selected image model. No image was generated.")
    if set(loaded) - set(applied):
        raise ValueError("Only part of this LoRA matched the selected image model. Choose a compatible LoRA or disable it.")
    if report is not None:
        report.update(status="matched_weights", matched_patches=len(loaded), applied_patches=len(applied),
                      visual_compatibility="not_verified")
    if metadata:
        result.set_attachments("lora_metadata", metadata)
    logging.info("Mumblebox LoRA: applied %d weight adjustments at strength %g", len(applied), strength)
    return result
