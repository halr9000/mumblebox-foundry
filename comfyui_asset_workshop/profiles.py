"""Explicit model families and native Comfy recipes; never automatic substitution."""

import copy

PROFILES = {
    "sdxl_base": dict(label="SDXL Base 1.0", model="sdxl_base", family="sdxl", steps=30, cfg=7.0,
                      references=10, camera=None),
    "sdxl_juggernaut": dict(label="Juggernaut XL v9", model="sdxl_juggernaut", family="sdxl", steps=35, cfg=5.0,
                            references=10, camera=None),
    "qwen21": dict(label="Qwen Image 2.1 7B", model="qwen21", encoder="qwen21_clip",
                   vae="qwen21_vae", clip_type="qwen_image", steps=25, cfg=1.0,
                   references=10, camera="qwen21_angles"),
    "qwen2511": dict(label="Qwen Image Edit 2511", model="qwen2511", encoder="qwen2511_clip",
                    vae="qwen2511_vae", clip_type="qwen_image", steps=40, cfg=4.0,
                    references=3, camera="qwen2511_angles", edit_only=True),
    "klein_base": dict(label="FLUX.2 Klein 9B base", model="klein_base", encoder="klein_clip",
                       vae="flux_vae", clip_type="flux2", steps=20, cfg=5.0,
                       references=100, reference_limit_kind="native graph ceiling; quality beyond a few references is unverified",
                       camera=None),
    "klein_distilled": dict(label="FLUX.2 Klein 9B distilled", model="klein_distilled", encoder="klein_clip",
                            vae="flux_vae", clip_type="flux2", steps=4, cfg=1.0,
                            references=100, reference_limit_kind="native graph ceiling; quality beyond a few references is unverified",
                            camera=None),
    "klein_kv": dict(label="FLUX.2 Klein 9B KV", model="klein_kv", encoder="klein_clip",
                     vae="flux_vae", clip_type="flux2", steps=4, cfg=1.0,
                     references=100, reference_limit_kind="native graph ceiling; quality beyond a few references is unverified",
                     camera="klein_angles"),
    "klein4": dict(label="FLUX.2 Klein 4B", model="klein4", encoder="klein4_clip",
                  vae="flux_vae", clip_type="flux2", steps=4, cfg=1.0,
                  references=100, reference_limit_kind="native graph ceiling; quality beyond a few references is unverified",
                  camera=None),
    "klein4_base": dict(label="FLUX.2 Klein 4B base", model="klein4_base", encoder="klein4_clip",
                       vae="flux_vae", clip_type="flux2", steps=20, cfg=5.0,
                       references=100, camera=None),
    "flux3_base": dict(label="FLUX 3 Image Klein base", model="flux3_base", encoder="flux3_clip",
                       vae="flux_vae", clip_type="flux3", steps=50, cfg=3.5,
                       references=10, camera="flux3_angles"),
    "flux3_distilled": dict(label="FLUX 3 Image Klein distilled", model="flux3_distilled", encoder="flux3_clip",
                            vae="flux_vae", clip_type="flux3", steps=16, cfg=1.0,
                            references=10, camera=None),
}


def lora_compatible(declared, selected):
    return declared == selected or (PROFILES.get(declared, {}).get("family") == "sdxl"
                                    and PROFILES.get(selected, {}).get("family") == "sdxl")


def capabilities(profile_id: str) -> dict:
    profile = PROFILES[profile_id]
    if profile.get("family") == "sdxl":
        family_name, architecture = "SDXL", "sdxl"
        license_info = {"label": "Commercial use subject to OpenRAIL conditions",
                        "url": "https://huggingface.co/RunDiffusion/Juggernaut-XL-v9" if profile_id == "sdxl_juggernaut"
                        else "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md"}
    elif profile_id.startswith("klein4"):
        family_name, architecture = "Klein 4B", "klein4"
        license_info = {"label": "Commercial use allowed — Apache 2.0",
                        "url": "https://huggingface.co/black-forest-labs/FLUX.2-klein-4B"}
    elif profile_id.startswith("klein"):
        family_name, architecture = "Klein 9B", "klein9"
        license_info = {"label": "Commercial model operation has conditions; output terms differ",
                        "url": "https://huggingface.co/black-forest-labs/FLUX.2-klein-9B/blob/main/LICENSE.md"}
    elif profile_id.startswith("flux3"):
        family_name, architecture = "FLUX 3 Image Klein", "flux3"
        license_info = {"label": "Commercial use has conditions — FLUX Kommunity",
                        "url": "https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md"}
    elif profile_id == "qwen21":
        family_name, architecture = "Qwen Image 2.1", "qwen21"
        license_info = {"label": "Research license — review commercial-use conditions",
                        "url": "https://huggingface.co/Qwen/Qwen-Image-2.1"}
    else:
        family_name, architecture = "Qwen Image Edit 2511", "qwen2511"
        license_info = {"label": "Commercial use allowed — Apache 2.0",
                        "url": "https://huggingface.co/Qwen/Qwen-Image-Edit-2511"}
    purposes = {
        "sdxl_base": "Standard SDXL checkpoint with its dual text encoders and VAE. A mature route for SDXL styles and LoRAs; references use IP-Adapter rather than instruction-based editing.",
        "sdxl_juggernaut": "Juggernaut XL v9 is an SDXL fine-tune geared toward photographic rendering. It shares SDXL LoRAs and uses its own 35-step, CFG 5 defaults.",
        "klein4": "Fast four-step starting choice for creating and editing images on this 16 GB system.",
        "klein4_base": "Klein 4B with more sampling control; its 20-step default takes longer than the distilled version.",
        "klein_distilled": "A larger four-step image model. Its model and text encoder use more memory than Klein 4B.",
        "klein_base": "The larger Klein base model with 20-step sampling and adjustable guidance; allow more time and memory.",
        "klein_kv": "Reference-editing variant with reference caching. Use it when working from supplied images; correct angles remain unguaranteed.",
        "qwen21": "Create from text or combine up to ten source references. It has its own prompting and commercial-use conditions.",
        "qwen2511": "Edit or reinterpret uploaded images. A source is required; its 40-step default can be considerably slower.",
        "flux3_distilled": "Create or edit from a full description of the finished image, using the distilled 16-step default.",
        "flux3_base": "FLUX 3 with 50-step base sampling and adjustable guidance; use a full description and allow more time.",
    }
    return {"id": profile_id, "label": profile["label"], "family": family_name,
            "tasks": ["create_image", "three_quarter", "edit_image", "reference_view", "describe", "enhance"],
            "source_required": bool(profile.get("edit_only")), "max_references": profile["references"],
            "reference_limit_kind": profile.get("reference_limit_kind", "native input limit"),
            "defaults": {"steps": profile["steps"], "cfg": profile["cfg"], "resolution": 1024,
                         **({"sampler": "dpmpp_2m", "scheduler": "karras", "reference_strength": .8,
                             "img2img_denoise": .65, "edit_denoise": .85, "negative_prompt": "collage, contact sheet, grid, multiple panels, multiple views, repeated objects"} if architecture == "sdxl" else {})},
            "license": license_info, "lora": {"profile": profile_id, "architecture": architecture,
                "variant_check_required": architecture != "sdxl", "validation": "Actual LoRA compatibility requires matching tensors and visual review."},
            "help": {"purpose": purposes[profile_id] + " Review the result before making a mesh.",
                "steps": f"Default {profile['steps']} for this variant. More steps take longer and do not guarantee better results.",
                "cfg": f"Default {profile['cfg']:g} for this variant. Stronger guidance may follow text more closely but can introduce artifacts.",
                "references": "Choose references that agree. A supported input count does not guarantee consistent details or cameras.",
                "lora": ("Choose SDXL LoRAs. These two SDXL checkpoints share the same architecture, but each style can behave differently. Model strength changes the image model; text strength changes matching CLIP layers when the LoRA includes them. Set both to zero to disable it. SD 1.5, Flux and Qwen LoRAs are incompatible."
                         if architecture == "sdxl" else "Choose weights made for this exact model variant. Zero strength disables an adapter. Camera adapters are optional and do not guarantee a correct view.")}}

# The distributed lock pins these sources to exact revisions, sizes and SHA-256.
# Destination names avoid collisions between unrelated pytorch_lora_weights files.
SOURCES = {
    "sdxl_base": ("stabilityai/stable-diffusion-xl-base-1.0", "sd_xl_base_1.0.safetensors", "checkpoints"),
    "sdxl_juggernaut": ("RunDiffusion/Juggernaut-XL-v9", "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors", "checkpoints"),
    "sdxl_ipadapter": ("h94/IP-Adapter", "sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors", "ipadapter"),
    "sdxl_vision": ("h94/IP-Adapter", "models/image_encoder/model.safetensors", "clip_vision", "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"),
    "sdxl_pixel_art": ("nerijs/pixel-art-xl", "pixel-art-xl.safetensors", "loras", "sdxl-pixel-art-xl.safetensors"),
    "qwen21": ("Comfy-Org/Qwen-Image-2.1", "diffusion_models/qwen_image_2.1_int8_convrot.safetensors"),
    "qwen21_clip": ("Comfy-Org/Qwen-Image-2.1", "text_encoders/qwen3vl_8b_int8_convrot.safetensors"),
    "qwen21_vae": ("Comfy-Org/Qwen-Image-2.1", "vae/qwen_image_2.1_vae_bf16.safetensors"),
    "qwen21_bf16": ("Comfy-Org/Qwen-Image-2.1", "diffusion_models/qwen_image_2.1_bf16.safetensors"),
    "qwen2511": ("Comfy-Org/Qwen-Image-Edit_ComfyUI", "split_files/diffusion_models/qwen_image_edit_2511_fp8mixed.safetensors"),
    "qwen2511_clip": ("Comfy-Org/HunyuanVideo_1.5_repackaged", "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"),
    "qwen2511_vae": ("Comfy-Org/Qwen-Image_ComfyUI", "split_files/vae/qwen_image_vae.safetensors"),
    "klein_base": ("black-forest-labs/FLUX.2-klein-base-9b-fp8", "flux-2-klein-base-9b-fp8.safetensors", "diffusion_models"),
    "klein_distilled": ("black-forest-labs/FLUX.2-klein-9b-fp8", "flux-2-klein-9b-fp8.safetensors", "diffusion_models"),
    "klein_kv": ("black-forest-labs/FLUX.2-klein-9b-kv-fp8", "flux-2-klein-9b-kv-fp8.safetensors", "diffusion_models"),
    "klein_clip": ("Comfy-Org/flux2-klein-9B", "split_files/text_encoders/qwen_3_8b_fp8mixed.safetensors"),
    "klein4": ("black-forest-labs/FLUX.2-klein-4b-fp8", "flux-2-klein-4b-fp8.safetensors", "diffusion_models"),
    "klein4_base": ("black-forest-labs/FLUX.2-klein-base-4b-fp8", "flux-2-klein-base-4b-fp8.safetensors", "diffusion_models"),
    "klein4_depth": ("thedeoxen/refcontrol-FLUX.2-klein-4B-reference-depth-lora", "flux2_klein_4b_refcontrol_depth.safetensors", "loras"),
    "klein9_depth": ("thedeoxen/refcontrol-FLUX.2-klein-9B-reference-depth-lora", "flux2_klein_9b_refcontrol_depth.safetensors", "loras"),
    "qwen21_anyangle": ("lilylilith/QI_2.1_AnyAngle", "QI2.1_AnyAngle.safetensors", "loras"),
    "klein4_clip": ("Comfy-Org/flux2-klein-4B", "split_files/text_encoders/qwen_3_4b_fp4_flux2.safetensors"),
    "flux3_base": ("black-forest-labs/flux-3-image-klein-comfy", "diffusion_models/flux3-image-klein-base-int8-convrot.safetensors"),
    "flux3_distilled": ("black-forest-labs/flux-3-image-klein-comfy", "diffusion_models/flux3-image-klein-int8-convrot.safetensors"),
    "flux3_base_bf16": ("black-forest-labs/flux-3-image-klein-comfy", "diffusion_models/flux3-image-klein-base-bf16.safetensors"),
    "flux3_distilled_bf16": ("black-forest-labs/flux-3-image-klein-comfy", "diffusion_models/flux3-image-klein-bf16.safetensors"),
    "flux3_clip": ("black-forest-labs/flux-3-image-klein-comfy", "text_encoders/qwen3vl_4b_int8_convrot.safetensors"),
    "flux_vae": ("Comfy-Org/flux2-dev", "split_files/vae/flux2-vae.safetensors",
                 "vae", "flux2-vae-comfy.safetensors"),
    "qwen2511_angles": ("fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA",
                        "qwen-image-edit-2511-multiple-angles-lora.safetensors", "loras"),
    "qwen21_angles": ("akhaliq/Qwen-Image-2.1-Multiple-Angles-LoRA",
                      "checkpoints_v2/angles_v2_full_qwen21_multiple_angles_v2_qwen21_multiple_angles_v2_000001500.safetensors", "loras"),
    "flux3_angles": ("akhaliq/flux-3-image-klein-angles-lora",
                     "pytorch_lora_weights.safetensors", "loras", "flux3-klein-base-angles.safetensors"),
    "klein_angles": ("Alexali/multiple-angles-flux2K", "multiple-angles-flux-klein-9b.safetensors", "loras"),
    "pixal_multiview": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_multiview_bf16.safetensors"),
    "pixal_single": ("Comfy-Org/Pixal3D", "diffusion_models/pixal3d_bf16.safetensors"),
    "trellis2": ("Comfy-Org/TRELLIS.2", "diffusion_models/trellis_2_bf16.safetensors"),
    "shape_vae": ("Comfy-Org/Pixal3D", "vae/trellis_2_shape_vae_bf16.safetensors"),
    "texture_vae": ("Comfy-Org/Pixal3D", "vae/trellis_2_texture_vae_bf16.safetensors"),
    "dino": ("Comfy-Org/Pixal3D", "clip_vision/dino_v3_L_naf_fp32.safetensors"),
    "birefnet": ("Comfy-Org/BiRefNet", "background_removal/birefnet.safetensors"),
}

ORBIT8 = {0: "front view", 45: "front-right quarter view", 90: "right side view",
          135: "back-right quarter view", 180: "back view", 225: "back-left quarter view",
          270: "left side view", 315: "front-left quarter view"}
ORBIT12 = {0: "front view", 30: "front-right view", 60: "front-right quarter view",
           90: "right side view", 120: "back-right quarter view", 150: "back-right view",
           180: "back view", 210: "back-left view", 240: "back-left quarter view",
           270: "left side view", 300: "front-left quarter view", 330: "front-left view"}
ELEVATIONS = {-30: "low-angle shot", 0: "eye-level shot", 30: "elevated shot",
              60: "high-angle shot", 90: "top-down shot"}

# Published adapter contracts. The depth/color render is an image reference, not
# a ControlNet tensor, and the generated camera still needs human review.
GUIDANCE = {
    "klein_depth": {"profiles":{"klein4_base":"klein4_depth", "klein_base":"klein9_depth"},
                    "map":"depth", "steps":20, "cfg":5.0},
    "qwen_anyangle": {"profiles":{"qwen21":"qwen21_anyangle"},
                      "map":"color", "steps":25, "cfg":3.0},
    "qwen_edit_depth": {"profiles":{"qwen2511":None},
                        "map":"depth", "steps":40, "cfg":4.0},
}


def angle_asset(asset, stage="image", slot="design", action="generate"):
    """Resolve stage-local controls without replacing saved design settings."""
    if stage != "image" or slot in ("design", "initial", "view_01", "view_05"):
        return asset
    result = copy.deepcopy(asset)
    settings = result["settings"]
    selected = settings.get("angle_profile", "same")
    result["profile"] = asset["profile"] if selected == "same" else selected
    profile = PROFILES[result["profile"]]
    route = settings.get("angle_route", "references") if action == "generate" else "references"
    if route != "references" and (route not in GUIDANCE or result["profile"] not in GUIDANCE[route]["profiles"]):
        raise ValueError("This angle method does not match the chosen model. Choose Klein Base for depth, Qwen 2.1 for AnyAngle, or Qwen Edit 2511 for experimental depth editing.")
    defaults = GUIDANCE.get(route, profile)
    settings["steps"] = settings.get("angle_steps") or defaults["steps"]
    settings["cfg"] = settings.get("angle_cfg") or defaults["cfg"]
    settings["angle_route"] = route
    settings["camera_lora"] = bool(settings.get("angle_camera_lora", False)) if route == "references" and action == "generate" else False
    if result["profile"] != asset["profile"]:
        settings["image_precision"] = "native"
    # A style adapter belongs to its declared model, not the whole asset.
    result["loras"] = [item for item in asset["loras"] if item.get("profile") == result["profile"]]
    return result


def model_id(asset):
    key = PROFILES[asset["profile"]]["model"]
    if asset["settings"].get("image_precision") == "bf16":
        if key + "_bf16" not in SOURCES:
            raise ValueError("This profile has no pinned BF16 recipe. Choose its native quantized recipe.")
        key += "_bf16"
    return key


def camera_prompt(profile, view):
    angles = ORBIT12 if profile == "qwen21" else ORBIT8
    azimuth, elevation = float(view["azimuth"]) % 360, float(view["elevation"])
    elevations = {0, 30, 60, 90} if profile == "qwen21" else {-30, 0, 30, 60}
    if profile == "flux3_base":
        elevations.add(90)
    if azimuth not in angles or elevation not in elevations:
        raise ValueError("This angle is outside this model's camera-control presets. Change the angle settings, choose another image model, or turn off Use camera control to use plain-text instructions.")
    if not PROFILES[profile].get("camera"):
        raise ValueError("No verified camera adapter is configured for this variant. Choose a supported camera profile or approximate text prompting.")
    if profile in ("qwen2511", "klein_kv"):
        return f"<sks> {angles[azimuth]} {ELEVATIONS[elevation]} medium shot"
    return f"<mva> {angles[azimuth]}, {ELEVATIONS[elevation]}"
