"""Small selected-stage graphs composed from the host's native nodes."""

import json
import copy
from pathlib import Path

import folder_paths

from .profiles import PROFILES, GUIDANCE, angle_asset, camera_prompt, model_id, capabilities, lora_compatible
from .runtime import store
from .store import digest, pair_approved, draft_inputs, MESH_DEFAULTS, ApprovalRequired, CapabilityError
from . import camera_guides, prompt_contracts

MODELS = json.loads(Path(__file__).with_name("models.lock.json").read_text(encoding="utf-8"))["models"]


def local_lora(name):
    root = Path(folder_paths.base_path).resolve() / 'models' / 'loras'
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Choose a LoRA inside this Comfy installation's models/loras folder.")
    if not path.is_file():
        raise ValueError(f"LoRA file is missing from this Comfy installation: {name}")
    return str(path)


class Graph:
    def __init__(self):
        self.nodes = {}

    def add(self, node_type, title=None, **inputs):
        key = str(len(self.nodes) + 1)
        self.nodes[key] = {"class_type": node_type, "inputs": inputs,
                           "_meta": {"title": title or node_type}}
        return [key, 0]

    @staticmethod
    def out(node, index):
        return [node[0], index]


def model_name(key):
    return MODELS[key]["name"]


def selected_image_model(asset, verify=False):
    if not asset.get('settings', {}).get('image_checkpoint'):
        return None
    from .civitai_native import selected_model
    return selected_model(asset, verify)


def checkpoint_names():
    from .civitai_native import installed_records
    return list(dict.fromkeys([MODELS[key]['name'] for key in ('sdxl_base', 'sdxl_juggernaut')] +
        [item['relative_path'] for item in installed_records() if item['kind'] == 'Checkpoint' and item['family'] == 'sdxl']))


def lora_provenance(item, path):
    from .civitai_native import installed_records
    checksum = digest(path)
    source = next((record for record in installed_records() if record['kind'] == 'LORA'
                   and record['relative_path'] == item['name'] and record['sha256'] == checksum), None)
    return {'sha256': checksum, **({'civitai': {key: source[key] for key in
        ('model_id', 'version_id', 'file_id', 'source_url', 'model_name', 'version_name', 'permissions')}} if source else {})}


def mesh_backend(asset):
    backend = asset["settings"]["mesh_backend"]
    if backend == "pixal_multiview" and not any(v["enabled"] and v.get("current") and not v.get("stale") for v in asset["views"]):
        if asset["settings"].get("include_design", True) and asset["design"].get("approved"):
            return "pixal_single"
    return backend


def source_fov(asset, revision=None):
    settings = asset["settings"]
    mode = settings.get("mesh_fov_mode", "manual")
    if asset.get("schema_version") == 2:
        return mode, settings["mesh_fov"]
    if mode == "auto":
        if revision is None:
            source = asset["design"] if settings.get("include_design", True) and asset["design"].get("current") else next(
                (v for v in asset["views"] if v["enabled"] and v.get("current") and not v.get("stale")), {})
            revision = next((r for r in source.get("revisions", []) if r["id"] == source.get("current")), {})
        recipe = revision.get("recipe", {})
        if recipe.get("preserve_camera_frame") and recipe.get("requested_camera"):
            return "guide", recipe["requested_camera"]["fov"]
    return mode, settings["mesh_fov"]


def required_models(asset, stage="image", camera=False, slot="design", action="generate"):
    asset = angle_asset(asset, stage, slot, action)
    if stage == "draft":
        result = [asset["settings"].get("draft_backend", "pixal_multiview"), "shape_vae", "dino", "birefnet"]
        if asset["settings"].get("draft_appearance", "geometry") == "color":
            result.append("texture_vae")
        if result[0] == "pixal_single" and source_fov(asset)[0] == "auto":
            result.append("moge2")
        return result
    if stage == "image":
        profile = PROFILES[asset["profile"]]
        if profile.get("family") == "sdxl":
            result = [] if selected_image_model(asset) else [model_id(asset)]
            references = asset.get("sources", asset.get("references", []))
            if any(r.get("enabled", True) for r in references) or action in ("three_quarter", "reference_view", "build_mesh_package"):
                result += ["sdxl_ipadapter", "sdxl_vision"]
            for item in asset.get("loras", []):
                if (item.get("enabled", True) and (float(item.get("strength", 1)) or float(item.get("strength_clip", item.get("strength", 1))))
                        and item.get("name") == MODELS["sdxl_pixel_art"]["name"]):
                    result.append("sdxl_pixel_art")
            return result
        result = [profile["encoder"], profile["vae"]]
        if not selected_image_model(asset):
            result.insert(0, model_id(asset))
        route = asset["settings"].get("angle_route", "references") if slot not in ("design", "initial", "view_01", "view_05") else "references"
        adapter = GUIDANCE[route]["profiles"][asset["profile"]] if route != "references" else None
        if adapter:
            result.append(adapter)
        if camera or asset["settings"].get("camera_lora"):
            if not profile.get("camera"):
                raise ValueError("This model variant has no configured camera LoRA.")
            result.append(profile["camera"])
        return result
    if stage in ("master", "game", "guide"):
        return []
    if stage in ("prepare", "foreground"):
        return ["birefnet"]
    result = [mesh_backend(asset), "shape_vae", "texture_vae", "dino", "birefnet"]
    if result[0] == "pixal_single" and source_fov(asset)[0] == "auto":
        result.append("moge2")
    return result


def load_image(graph, asset, revision, title):
    return graph.add("AW_LoadImage", title, asset_id=asset["id"], relative_path=revision["file"],
                     **({"expected_sha256": revision["sha256"]} if asset.get("schema_version") == 2 else {}))


def guidance_inputs(asset, slot, action):
    route = asset["settings"].get("angle_route", "references")
    if route == "references" or action != "generate" or slot in ("design", "initial", "view_01", "view_05"):
        return None
    if not pair_approved(asset):
        raise ValueError("Approve the front and back before generating guided angles.")
    draft = next((d for d in asset["drafts"] if d["id"] == asset.get("selected_draft")), None)
    if not draft or draft.get("stale") or not draft.get("approved"):
        raise ValueError("Build and approve the draft before using mesh guidance.")
    view = store().slot(asset, slot)
    pose = {key:view[key] for key in ("azimuth", "elevation", "fov")}
    guide = next((g for g in reversed(asset["guides"]) if g["slot"] == slot and not g.get("stale")
                  and g["draft"] == draft["id"] and g["draft_sha256"] == draft["sha256"] and g["pose"] == pose), None)
    kind = GUIDANCE[route]["map"]
    if not guide or kind not in guide["files"]:
        raise ValueError(f"Render current {kind} camera guides for this angle first. AnyAngle needs a draft with color.")
    image = guide["files"][kind]
    if digest(store().path(asset["id"], image["file"])) != image["sha256"]:
        raise ValueError("The saved camera guide changed on disk. Render it again before generating.")
    rear = route == "klein_depth" and 90 < float(view["azimuth"]) % 360 < 270
    source = store().revision(asset, "view_05" if rear else "design", approved=True)
    appearance = {k:source[k] for k in ("id", "file", "sha256")}
    appearance.update(role="approved back appearance" if rear else "approved front appearance",
                      instructions="Preserve this object's identity, colors, materials and proportions.")
    control = {**image, "id":guide["id"], "role":f"requested camera {kind} guide",
               "instructions":"Use this framing, silhouette and camera. Its rough details may need refinement."}
    refs = [appearance, control] if route == "qwen_anyangle" else [control, appearance]
    return guide, refs


def active_references(asset, slot, action):
    library = store()
    references = []
    if slot == "design" and asset.get("initial", {}).get("current"):
        references.append({**library.revision(asset, "initial"), "id": "initial_image",
                           "role": "main starting image",
                           "instructions": "Use this as the main design reference. Apply the user's requested changes."})
    if slot != "design":
        if action == "correct":
            references.append({**library.revision(asset, slot), "id": slot, "role": "image to correct",
                               "instructions": "Keep this view's camera and change only the requested detail."})
        else:
            if slot == "view_01":
                raise ValueError("Create or replace the front in Step 1. It becomes the front mesh image when the pair is approved.")
            if slot != "view_05" and not pair_approved(asset):
                raise ValueError("Review and approve the front and back before generating the remaining angles.")
            references.append({**library.revision(asset, "design", approved=slot != "view_05"),
                               "id": "front_reference", "role": "front of this exact object",
                               "instructions": "Preserve the object's identity, silhouette, colors, materials and parts. This image establishes its FRONT; change the camera to the requested view."})
            if slot != "view_05":
                references.append({**library.revision(asset, "view_05", approved=True),
                                   "id": "back_reference", "role": "approved back of the SAME object",
                                   "instructions": "Use these rear details on the BACK only. Combine this with the front reference to show one consistent object from the requested camera. Do not duplicate parts shown in both images."})
    references.extend(reference for reference in asset["references"] if reference.get("enabled", True))
    # Source revisions remain in History. Do not recursively embed their recipes
    # in every new result: a sequence of edits would grow the manifest each time.
    keys = ("id", "file", "sha256", "created", "role", "instructions", "enabled")
    return [{key: reference[key] for key in keys if key in reference} for reference in references]


def view_instructions(view):
    azimuth = float(view["azimuth"]) % 360
    elevation = float(view["elevation"])
    faces = {
        0: ("front", "back, left side and right side",
            "The front is square to the camera. Do not show a quarter view."),
        45: ("front and right side", "back and left side",
             "Look toward the front-right corner. Both faces occupy substantial, roughly equal widths; show the side depth clearly. A straight front picture is incorrect."),
        90: ("right side", "front, back and left side",
             "The right side is square to the camera. Show its full side silhouette and thickness; no front-facing picture or mirrored left-side picture."),
        135: ("back and right side", "front and left side",
              "Look toward the back-right corner. Both faces occupy substantial, roughly equal widths; show the side depth clearly. A straight back picture is incorrect."),
        180: ("back", "front, left side and right side",
              "The back is square to the camera. Front-mounted details must not appear on this face."),
        225: ("back and left side", "front and right side",
              "Look toward the back-left corner. Both faces occupy substantial, roughly equal widths; show the side depth clearly. A straight back picture is incorrect."),
        270: ("left side", "front, back and right side",
              "The left side is square to the camera. Show its full side silhouette and thickness; no front-facing picture or mirrored right-side picture."),
        315: ("front and left side", "back and right side",
              "Look toward the front-left corner. Both faces occupy substantial, roughly equal widths; show the side depth clearly. A straight front picture is incorrect."),
    }
    nearest = min(faces, key=lambda angle: abs((angle-azimuth+180) % 360-180))
    visible, hidden, framing = faces[nearest]
    if elevation >= 89:
        return ("Look straight down. The top surface and top-mounted features must dominate. "
                "The underside is hidden; do not substitute a front or side view.")
    if elevation <= -89:
        return ("Look straight upward at the bottom. The underside, bottom-mounted features and underside of the base must dominate. "
                "The top surface is hidden. Suspend the object against a plain background with no floor obstructing it.")
    vertical = (
        f"Look downward from {elevation:g} degrees above the object. The top surface AND the {visible} must be clearly visible. "
        "The underside is hidden. A level-height picture is incorrect."
        if elevation > 0 else
        f"Look upward from {abs(elevation):g} degrees below the object. The underside, including the underside of any base, AND the {visible} must be clearly visible. "
        "The top surface is hidden. Suspend the object against a plain background with no floor hiding the bottom. A normal back picture is incorrect."
        if elevation < 0 else
        "Camera at the object's mid-height. Do not look down onto the top or up at the underside."
    )
    return (f"Required visible faces: {visible}. Hidden faces: {hidden}. {framing} {vertical} "
            f"Show all design features assigned to the visible {visible}, in their specified positions. "
            f"Do not move features from the hidden {hidden} onto a visible face. "
            "Preserve all visible protrusions, handles, openings and supports; retain occlusion by the body where appropriate.")


def sdxl_image_recipe(asset, job, slot, refs, edit, task_contract, angle_prompt=None):
    graph = Graph()
    settings, profile = asset["settings"], PROFILES[asset["profile"]]
    resolution = int(settings["resolution"])
    steps, cfg = int(settings.get("steps") or profile["steps"]), float(settings.get("cfg") or profile["cfg"])
    seed = int(settings["seed"])
    task = task_contract["user"]["task"] if task_contract else "create_image"
    prompt = task_contract["prompt"] if task_contract else (edit["prompt"] if edit else angle_prompt or asset["prompt"])
    if not prompt.strip():
        if not refs:
            raise ValueError("Describe the asset or add a reference image first.")
        prompt = "A clear, complete image of the object in the visual references, preserving its design."
    negative_prompt = settings.get("sdxl_negative_prompt", "")
    chosen = selected_image_model(asset)
    checkpoint = graph.add("AW_LoadSDXLCheckpoint", profile["label"],
                           checkpoint_name=chosen['relative_path'] if chosen else model_name(model_id(asset)))
    model, clip, vae = checkpoint, graph.out(checkpoint, 1), graph.out(checkpoint, 2)
    reports, loras = [], []
    for item in asset["loras"]:
        strength = float(item.get("strength", 1))
        text_strength = float(item.get("strength_clip", strength))
        if not item.get("enabled", True) or not (strength or text_strength):
            continue
        if not lora_compatible(item.get("profile"), asset["profile"]):
            raise CapabilityError("Choose an SDXL LoRA for this checkpoint or disable it.")
        path = local_lora(item["name"])
        loaded = graph.add("AW_LoadSDXLLoRA", item["name"], model=model, clip=clip, lora_name=str(Path(item["name"])),
                           strength_model=strength, strength_clip=text_strength)
        model, clip = loaded, graph.out(loaded, 1)
        reports.append(graph.out(loaded, 2))
        loras.append({**item, **lora_provenance(item, path), "validation": "SDXL family declared; matching checked during execution"})
        if item.get("trigger"):
            prompt += ", " + item["trigger"].strip()
    bindings = [f"Reference {i+1}: {ref.get('role', 'appearance')}. {ref.get('instructions', '')}" for i, ref in enumerate(refs)]
    instructions = [ref["instructions"].strip() for ref in refs if ref.get("instructions", "").strip()]
    if instructions:
        prompt += " Desired reference details: " + "; ".join(instructions)
    images = [load_image(graph, asset, ref, bindings[i]) for i, ref in enumerate(refs)]
    influence = float(settings.get("sdxl_reference_strength", .8))
    ingredient_images = [image for ref, image in zip(refs, images) if not edit or ref["file"] != edit["source"]["file"]]
    if ingredient_images and influence:
        padded = [graph.add("ResizeAndPadImage", "Keep the complete reference without stretching",
                           image=image, target_width=resolution, target_height=resolution,
                           padding_color="white", interpolation="lanczos") for image in ingredient_images]
        batch = padded[0]
        for image in padded[1:]:
            batch = graph.add("ImageBatch", image1=batch, image2=image)
        adapter = graph.add("IPAdapterModelLoader", ipadapter_file=model_name("sdxl_ipadapter"))
        vision = graph.add("CLIPVisionLoader", clip_name=model_name("sdxl_vision"))
        model = graph.add("IPAdapterAdvanced", "SDXL visual references — not measured camera views", model=model,
                          ipadapter=adapter, image=batch, clip_vision=vision, weight=influence, weight_type="linear",
                          combine_embeds="average", start_at=0.0, end_at=1.0, embeds_scaling="V only")
    width = height = resolution
    denoise = 1.0
    if edit or (images and task == "create_image" and settings.get("sdxl_source_mode", "reference") == "img2img"):
        pixels = graph.add("ImageScaleToTotalPixels", "Preserve source proportions", image=images[0],
                           upscale_method="lanczos", megapixels=resolution**2 / 1048576, resolution_steps=32)
        dimensions = graph.add("GetImageSize", image=pixels)
        width, height = dimensions, graph.out(dimensions, 1)
        if edit:
            mask_image = load_image(graph, asset, edit["mask"], "Selected area — white means edit")
            mask = graph.add("ImageToMask", image=mask_image, channel="red")
            latent = graph.add("VAEEncodeForInpaint", "SDXL masked edit", pixels=pixels, vae=vae, mask=mask, grow_mask_by=0)
            denoise = float(settings.get("sdxl_edit_denoise", .85))
        else:
            latent = graph.add("VAEEncode", pixels=pixels, vae=vae)
            denoise = float(settings.get("sdxl_img2img_denoise", .65))
    else:
        latent = graph.add("EmptyLatentImage", width=resolution, height=resolution, batch_size=1)
    dimensions = dict(width=width, height=height, crop_w=0, crop_h=0, target_width=width, target_height=height)
    positive = graph.add("CLIPTextEncodeSDXL", clip=clip, text_g=prompt, text_l=prompt, **dimensions)
    negative = graph.add("CLIPTextEncodeSDXL", clip=clip, text_g=negative_prompt, text_l=negative_prompt, **dimensions)
    model = graph.add("AW_ModelBudget", model=model, extra_gb=settings["extra_vram_headroom_gb"])
    samples = graph.add("KSampler", model=model, positive=positive, negative=negative, latent_image=latent,
                        seed=seed, steps=steps, cfg=cfg, sampler_name=settings.get("sdxl_sampler", "dpmpp_2m"),
                        scheduler=settings.get("sdxl_scheduler", "karras"), denoise=denoise)
    if settings["tiled_vae"]:
        decoded = graph.add("VAEDecodeTiled", samples=samples, vae=vae, tile_size=512, overlap=64, temporal_size=64, temporal_overlap=8)
    else:
        decoded = graph.add("VAEDecode", samples=samples, vae=vae)
    details = {"profile": asset["profile"], "steps": steps, "cfg": cfg, "seed": seed, "prompt": prompt,
               "negative_prompt": negative_prompt, "references": refs, "loras": loras, "settings": settings.copy(),
               "sampler": settings.get("sdxl_sampler", "dpmpp_2m"), "scheduler": settings.get("sdxl_scheduler", "karras"),
               "denoise": denoise, "reference_conditioning": "IP-Adapter Plus SDXL; visual resemblance, not measured cameras",
               "models": {key: MODELS[key] for key in required_models(asset, "image", action=task)}}
    if chosen:
        details['checkpoint'] = {key: value for key, value in chosen.items() if key not in ('path', 'download_url')}
    if edit:
        details["edit"] = edit
    if task_contract:
        details.update(task=task, requested_view=task_contract["requested_view"], camera_verification="not_measured",
                       prompt_guidance=task_contract["sources"], memory_preset_id=asset["memory_preset_id"],
                       preset_overrides=asset["preset_overrides"])
    saved = graph.add("AW_SaveImage", image=decoded, asset_id=asset["id"], slot=slot, job_id=job["id"], recipe=json.dumps(details),
                      **{f"lora_reports.lora{i+1}": report for i, report in enumerate(reports)})
    graph.add("PreviewImage", images=saved)
    return graph, details, bindings


def image_recipe(asset, job, slot, action, angle_prompt=None, edit=None, task_contract=None, references=None):
    asset = angle_asset(asset, "image", slot, action) if task_contract is None else asset
    graph = Graph()
    settings, profile = asset["settings"], PROFILES[asset["profile"]]
    guided = guidance_inputs(asset, slot, action) if task_contract is None else None
    refs = ([{**edit["source"], "role": "image to edit", "instructions": "Keep this camera, framing and design."},
             *[reference for reference in asset["references"] if reference.get("enabled", True)]]
            if edit else active_references(asset, slot, action)) if task_contract is None else references
    if guided:
        refs = guided[1]
    if len(refs) > profile["references"]:
        raise ValueError(f"{profile['label']} recipe accepts {profile['references']} active images; this request has {len(refs)}, including its edit source and design. Disable some ingredient references.")
    if profile.get("edit_only") and not refs:
        raise ValueError("Qwen Edit 2511 needs an image. Load a design/reference, or explicitly choose a text-to-image profile for the design stage.")
    if profile.get("family") == "sdxl":
        return sdxl_image_recipe(asset, job, slot, refs, edit, task_contract, angle_prompt)
    if not refs and not asset["prompt"].strip():
        raise ValueError("Describe the asset or add a reference image first.")
    bindings = []
    for index, ref in enumerate(refs):
        token = (f"<image{index + 1}>" if asset["profile"] == "qwen21" else
                 f"the {['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth'][index]} image" if asset["profile"].startswith("flux3") else
                 f"Picture {index + 1}" if asset["profile"].startswith("qwen") else f"Figure {index + 1}")
        bindings.append(f"{token} = {ref['id']}: {ref.get('role', '')}. {ref.get('instructions', '')}")
    prompt = asset["prompt"].strip() or "Create a clear, complete image of the object in the main reference, preserving its design."
    view = store().slot(asset, slot) if task_contract is None and slot not in ("design", "initial") else None
    use_camera = view is not None and action == "generate" and settings.get("camera_lora")
    if edit:
        instruction = ("Rebuild the gray selected area of the first image. Fill it seamlessly with the requested content. "
                       if edit.get("replace_detail") else "Edit only the selected area of the first image. ")
        prompt = (instruction + "Keep its camera viewpoint, framing, materials and all other details unchanged. "
                  + edit["prompt"])
    elif view is not None:
        if action == "correct":
            if not view.get("correction", "").strip():
                raise ValueError("Enter the change in this view's correction box first.")
            prompt = "Edit the first image. Keep its camera viewpoint and framing unchanged. " + view["correction"]
        else:
            if not angle_prompt:
                raise ValueError("Prepare this angle's instructions before generating it.")
            camera = camera_prompt(asset["profile"], view) if use_camera else (
                f"View the same object from its {view['name']}, "
                f"azimuth {view['azimuth']} degrees and elevation {view['elevation']} degrees.")
            prompt = (angle_prompt if asset["profile"].startswith("flux3") and not use_camera
                      else camera + "\n" + angle_prompt)
    elif slot == "design":
        prompt = (angle_prompt or prompt) + ("\nCreate the FRONT reference image of this one object. Face its front directly toward the camera "
                   "at the object's mid-height, with no three-quarter rotation. Keep the entire object in frame on a "
                   "plain neutral background. The description may define hidden back and side features for later views; "
                   "do not move those features onto the front.")
    if task_contract is not None:
        prompt = task_contract["prompt"]
    expanded_angle = (asset["profile"].startswith("flux3") and view is not None
                      and action == "generate" and not use_camera)
    if guided:
        route = settings["angle_route"]
        if route == "klein_depth":
            # The published 9B RefControl workflow uses only its trigger. An
            # identity/pose caption can override the depth camera (tested locally).
            prompt = ("refcontrol" if asset["profile"] == "klein_base" else
                      "refcontrol. Recreate the object in image 2 using the depth, camera and framing in image 1. " + (angle_prompt or asset["prompt"]))
        elif route == "qwen_anyangle":
            prompt = "Change the camera angle from <image2> to <image1>. " + (angle_prompt or asset["prompt"])
        else:
            prompt = ("Convert the depth image in Picture 1 into a finished image of the object in Picture 2. "
                      "Keep Picture 1's exact camera, outline and framing; use Picture 2 for identity, materials and colors. "
                      + (angle_prompt or asset["prompt"]))
    elif not expanded_angle and (not use_camera or len(refs) > 1):
        prompt += "\n" + "\n".join(bindings)
    chosen = selected_image_model(asset)
    model = graph.add("UNETLoader", profile["label"],
                      unet_name=str(Path(chosen['relative_path'])) if chosen else model_name(model_id(asset)), weight_dtype="default")
    lora_record = []
    lora_reports = []
    for item in asset["loras"]:
        if not item.get("enabled", True) or float(item["strength"]) == 0:
            continue
        if item.get("profile") != asset["profile"]:
            raise ValueError(f"LoRA {item['name']} is labeled for {item.get('profile')}, not this model profile.")
        path = local_lora(item["name"])
        record = {**item, **lora_provenance(item, path), "validation": "variant declared by caller; tensor matching and visual compatibility need review"}
        lora_record.append(record)
        model = graph.add("AW_LoadModelLoRA", item["name"], model=model,
                          lora_name=str(Path(item["name"])), strength_model=float(item["strength"]))
        if task_contract is not None:
            lora_reports.append(graph.out(model, 1))
        if item.get("trigger"):
            trigger = item["trigger"].strip()
            if task_contract is not None and trigger.startswith(("<mva>", "<sks>")):
                # Published camera adapters require their camera grammar first.
                prompt = trigger + "\n" + prompt
            else:
                prompt += "\n" + trigger
    if use_camera:
        camera = profile["camera"]
        strength = 1.3 if camera == "klein_angles" else .9
        model = graph.add("AW_LoadModelLoRA", "Camera control", model=model,
                          lora_name=model_name(camera), strength_model=strength)
        lora_record.append({"name": model_name(camera), "sha256": MODELS[camera]["sha256"], "strength": strength,
                            "validation": "published camera recipe; generated pose remains estimated"})
    if guided:
        adapter = GUIDANCE[settings["angle_route"]]["profiles"][asset["profile"]]
        if adapter:
            strength = float(settings.get("guide_strength", 1))
            model = graph.add("AW_LoadModelLoRA", "Mesh camera guidance", model=model,
                              lora_name=model_name(adapter), strength_model=strength)
            lora_record.append({"name":model_name(adapter), "sha256":MODELS[adapter]["sha256"], "strength":strength,
                                "validation":"published reference order; native rendered guide comparison"})
    clip = graph.add("CLIPLoader", "Selected model text / image encoder",
                     clip_name=model_name(profile["encoder"]), type=profile["clip_type"], device="default")
    vae = graph.add("VAELoader", vae_name=model_name(profile["vae"]))
    images = [load_image(graph, asset, ref, bindings[i]) for i, ref in enumerate(refs)]
    if edit:
        mask_image = load_image(graph, asset, edit["mask"], "Selected area — white means edit")
        mask = graph.add("ImageToMask", image=mask_image, channel="red")
        if edit.get("replace_detail"):
            # Hide the old detail from reference conditioning as well as the
            # target latent. The untouched source is retained for final compositing.
            size = graph.add("GetImageSize", image=images[0])
            neutral = graph.add("EmptyImage", "Neutral fill inside selection",
                                width=size, height=graph.out(size, 1), batch_size=1, color=0x808080)
            images[0] = graph.add("ImageCompositeMasked", "Replace selected reference detail",
                                  destination=images[0], source=neutral, mask=mask,
                                  x=0, y=0, resize_source=False)
    resolution = int(settings["resolution"])
    steps, cfg = int(settings.get("steps") or profile["steps"]), float(settings.get("cfg") or profile["cfg"])
    seed = int((view or {}).get("seed") if (view or {}).get("seed") is not None else settings["seed"])
    if asset["profile"] == "qwen21":
        model = graph.add("QwenImage21Cache", model=model, device=settings["cache_device"], dtype=settings["cache_precision"])
        conditioning = graph.add("TextEncodeQwenImage21", clip=clip, vae=vae, prompt=prompt, negative_prompt="",
                                 resolution=resolution, **{f"images.image_{i+1}": image for i, image in enumerate(images)})
        positive, negative, latent = conditioning, graph.out(conditioning, 1), graph.out(conditioning, 2)
    elif asset["profile"] == "qwen2511":
        model = graph.add("ModelSamplingAuraFlow", model=model, shift=3.1, sampling="flow")
        # Match the full non-Lightning native recipe.
        model = graph.add("CFGNorm", model=model, strength=1.0)
        refs_inputs = {f"image{i+1}": image for i, image in enumerate(images)}
        positive = graph.add("TextEncodeQwenImageEditPlus", clip=clip, vae=vae, prompt=prompt, **refs_inputs)
        negative = graph.add("TextEncodeQwenImageEditPlus", clip=clip, vae=vae, prompt="", **refs_inputs)
        positive = graph.add("FluxKontextMultiReferenceLatentMethod", conditioning=positive, reference_latents_method="index_timestep_zero")
        negative = graph.add("FluxKontextMultiReferenceLatentMethod", conditioning=negative, reference_latents_method="index_timestep_zero")
        scaled = graph.add("ImageScaleToTotalPixels", image=images[0], upscale_method="lanczos",
                           megapixels=resolution**2 / 1048576, resolution_steps=32)
        latent = graph.add("VAEEncode", pixels=scaled, vae=vae)
    else:
        positive = graph.add("CLIPTextEncode", clip=clip, text=prompt)
        negative = graph.add("CLIPTextEncode", clip=clip, text="")
        if images and asset["profile"].startswith("klein"):
            if asset["profile"] == "klein_kv":
                negative = graph.add("ConditioningZeroOut", conditioning=positive)
            dimensions = None
            for image in images:
                scaled = graph.add("ImageScaleToTotalPixels", image=image, upscale_method="lanczos",
                                   megapixels=resolution**2 / 1048576, resolution_steps=16)
                if dimensions is None:
                    dimensions = graph.add("GetImageSize", image=scaled)
                reference = graph.add("VAEEncode", pixels=scaled, vae=vae)
                positive = graph.add("ReferenceLatent", conditioning=positive, latent=reference)
                negative = graph.add("ReferenceLatent", conditioning=negative, latent=reference)
            latent = graph.add("EmptyFlux2LatentImage", width=dimensions, height=graph.out(dimensions, 1), batch_size=1)
        elif images:
            conditioning = graph.add("ReferenceMultiLatent", positive=positive, negative=negative, vae=vae,
                                     resolution="resize", **{"resolution.megapixels": resolution**2 / 1048576},
                                     **{f"images.image{i}": image for i, image in enumerate(images)})
            positive, negative, latent = conditioning, graph.out(conditioning, 1), graph.out(conditioning, 2)
        else:
            latent = graph.add("EmptyFlux2LatentImage", width=resolution, height=resolution, batch_size=1)
        if asset["profile"] == "klein_kv":
            model = graph.add("FluxKVCache", model=model)
    if edit:
        original = graph.add("ImageScaleToTotalPixels", "Original image for masked editing",
                             image=images[0], upscale_method="lanczos",
                             megapixels=resolution**2 / 1048576, resolution_steps=32)
        latent = graph.add("VAEEncode", pixels=original, vae=vae)
        latent = graph.add("SetLatentNoiseMask", "Generate inside the selected area", samples=latent, mask=mask)
    model = graph.add("AW_ModelBudget", model=model, extra_gb=settings["extra_vram_headroom_gb"])
    if asset["profile"].startswith("klein"):
        noise = graph.add("RandomNoise", noise_seed=seed)
        guider = graph.add("CFGGuider", model=model, positive=positive, negative=negative, cfg=cfg)
        sampler = graph.add("KSamplerSelect", sampler_name="euler")
        # Empty/reference latent size is recovered by a native latent-size node if present.
        # All image references retain aspect ratio; scheduler is parameterized below.
        if images:
            width, height = dimensions, graph.out(dimensions, 1)
        else:
            width = height = resolution
        sigmas = graph.add("Flux2Scheduler", steps=steps, width=width, height=height)
        samples = graph.add("SamplerCustomAdvanced", noise=noise, guider=guider, sampler=sampler, sigmas=sigmas, latent_image=latent)
    else:
        samples = graph.add("KSampler", model=model, positive=positive, negative=negative, latent_image=latent,
                            seed=seed, steps=steps, cfg=cfg, sampler_name="euler", scheduler="simple", denoise=1.0)
    if settings["tiled_vae"]:
        decoded = graph.add("VAEDecodeTiled", samples=samples, vae=vae, tile_size=512, overlap=64, temporal_size=64, temporal_overlap=8)
    else:
        decoded = graph.add("VAEDecode", samples=samples, vae=vae)
    details = {"profile": asset["profile"], "steps": steps, "cfg": cfg, "seed": seed,
               "prompt": prompt, "references": refs, "loras": lora_record,
               "camera": view and {k: view[k] for k in ("azimuth", "elevation", "fov", "camera_source")},
               "models": {k: MODELS[k] for k in required_models(asset, slot="design" if task_contract else slot, action=action)},
               "settings": settings.copy()}
    if chosen:
        details['checkpoint'] = {key: value for key, value in chosen.items() if key not in ('path', 'download_url')}
    if guided:
        guide = guided[0]
        details.update(guide=guide["id"], draft=guide["draft"], preserve_camera_frame=True,
                       requested_camera=guide["camera"], angle_route=settings["angle_route"])
        details["camera"]["known"] = False
    if edit:
        details["edit"] = edit
    if task_contract is not None:
        details.update(task=task_contract["user"]["task"], requested_view=task_contract["requested_view"],
                       camera_verification="not_measured", prompt_guidance=task_contract["sources"],
                       memory_preset_id=asset["memory_preset_id"], preset_overrides=asset["preset_overrides"])
    source_recipe = (edit["source"].get("recipe", {}) if edit else
                     store().revision(asset, slot).get("recipe", {}) if action=="correct" else {})
    if source_recipe.get("preserve_camera_frame") and not guided:
        # A local edit retains the source framing and its guide dependency.
        # These are still requested/estimated cameras, never measured AI poses.
        for key in ("guide","draft","requested_camera","preserve_camera_frame","angle_route"):
            if key in source_recipe: details[key]=source_recipe[key]
    saved = graph.add("AW_SaveImage", image=decoded, asset_id=asset["id"], slot=slot, job_id=job["id"], recipe=json.dumps(details),
                      **{f"lora_reports.lora{i+1}": report for i, report in enumerate(lora_reports)})
    graph.add("PreviewImage", images=saved)
    return graph, details, bindings


def approved_primary(snapshot):
    slot = snapshot["images"]["mesh_input"]
    revision = next((r for r in slot["revisions"] if r["id"] == slot["approved"] == slot["current"]), None)
    if revision is None or revision["review"]["decision"] not in ("approved", "approved_with_notes"):
        raise ApprovalRequired("Approve one image for the mesh first.")
    path = store().path(snapshot["id"], revision["file"])
    if not path.is_file() or digest(path) != revision["sha256"]:
        raise ApprovalRequired("The approved image changed; import and approve it again.")
    return copy.deepcopy(revision)


def image_task_recipe(project: dict, snapshot: dict, task: str, role: str, attempt_id: str) -> dict:
    asset = copy.deepcopy(snapshot)
    profile = capabilities(asset["profile"])
    references = [copy.deepcopy(r) for r in asset["sources"] if r.get("enabled", True)]
    edit = asset.get("task_payload", {}).get("edit") if task == "edit_image" else None
    requested_view = role.removeprefix("reference_") if task == "reference_view" else None
    if task == "reference_view":
        references.insert(0, {**approved_primary(asset), "role": "approved primary design"})
    elif task == "three_quarter":
        design = asset["images"]["design"]
        primary = next((r for r in design["revisions"] if r["id"] == design["current"]), None)
        if primary:
            references.insert(0, {**primary, "role": "chosen design"})
    elif edit:
        references.insert(0, {**edit["source"], "role": "image to edit"})
    unique = {}
    for record in references:
        unique.setdefault(record["sha256"], {key: record[key] for key in
            ("id", "file", "sha256", "role", "instructions") if key in record})
    references = list(unique.values())
    if profile["source_required"] and not references:
        raise CapabilityError("Qwen Edit 2511 needs a source image. Upload one or explicitly choose a creation model.")
    if len(references) > profile["max_references"]:
        raise CapabilityError(f"{profile['label']} accepts {profile['max_references']} source images; choose which references to use.")
    for item in asset["loras"]:
        if item.get("enabled", True) and (float(item.get("strength", 1)) or float(item.get("strength_clip", 0))) and not lora_compatible(item.get("profile"), asset["profile"]):
            raise CapabilityError(f"LoRA {item['name']} is not declared compatible with {asset['profile']}. Disable it or choose a matching variant.")
    description = edit["prompt"] if edit else asset["prompt"]
    contract = prompt_contracts.image_task(asset["profile"], task, description, asset["design_notes"], requested_view,
        category=asset["category"], has_images=bool(references))
    if asset.get("task_payload", {}).get("expanded_prompt"):
        contract["prompt"] = asset["task_payload"]["expanded_prompt"]
    graph, details, bindings = image_recipe(asset, {"id": attempt_id}, role, "generate",
        edit=edit, task_contract=contract, references=references)
    return {"graph": graph.nodes, "details": details, "bindings": bindings, "role": role}


def approved_views(asset):
    library = store()
    if asset.get("schema_version") == 2:
        return [("mesh_input", approved_primary(asset), None)]
    if asset["settings"]["mesh_backend"] == "pixal_multiview" and not pair_approved(asset):
        raise ValueError("Approve the front and back before making a multiview mesh. Single-image mesh modes remain available in Settings.")
    selected = [v for v in asset["views"] if v["enabled"] and v.get("current") and not v.get("stale")]
    if mesh_backend(asset) != "pixal_multiview":
        if asset["settings"].get("include_design", True) and asset["design"].get("current"):
            return [("design", library.revision(asset, "design"), None)]
        if selected:
            return [(selected[0]["id"], library.revision(asset, selected[0]["id"]), None)]
        raise ValueError("Select at least one image to include in the mesh.")
    result = []
    for view in selected:
        result.append((view["id"], library.revision(asset, view["id"]), view))
    if not result:
        raise ValueError("Select at least one image to include in the mesh.")
    if len(result) > 100:
        raise ValueError("This graph supports up to 100 prepared inputs. Split this asset's view set explicitly.")
    return result


def preparation(graph, asset):
    selected = approved_views(asset)
    background = (graph.add("LoadBackgroundRemovalModel", bg_removal_name=model_name("birefnet"))
                  if any(not revision.get("foreground") for _, revision, _ in selected) else None)
    prepared, paths, cameras = [], [], []
    for slot, revision, view in selected:
        source = load_image(graph, asset, revision, view["name"] if view else "Accepted design")
        image = graph.add("AW_PrepareView", image=source, alpha_mask=graph.out(source, 1),
                          **({"bg_removal_model": background} if not revision.get("foreground") else {}),
                          asset_id=asset["id"], slot=slot,
                          revision_id=revision["id"], foreground_id=revision.get("foreground", {}).get("id", ""),
                          # Pixal multiview projects pixels with the supplied cameras;
                          # independently fitting each silhouette changes that projection.
                          preserve_frame=bool(mesh_backend(asset) == "pixal_multiview" or revision.get("camera", {}).get("known") or revision.get("recipe", {}).get("preserve_camera_frame")),
                          padding=1.0 if asset["settings"]["mesh_backend"] == "trellis2" else 1.1)
        prepared.append(image)
        paths.append(graph.out(image, 1))
        if view:
            pose = {k: view[k] for k in ("id", "azimuth", "elevation", "fov", "camera_source")}
            requested = revision.get("recipe", {}).get("requested_camera")
            if requested:
                pose.update(requested_camera=requested, camera_source="mesh_guided_estimate")
            cameras.append(pose)
    return selected, prepared, paths, cameras


def foreground_recipe(asset, job, slot):
    graph = Graph()
    revision = store().revision(asset, slot)
    source = load_image(graph, asset, revision, "Original image")
    background = (graph.add("LoadBackgroundRemovalModel", bg_removal_name=model_name("birefnet"))
                  if not revision.get("foreground") else None)
    image = graph.add("AW_PrepareView", image=source, alpha_mask=graph.out(source, 1),
                      **({"bg_removal_model": background} if background else {}), asset_id=asset["id"], slot=slot,
                      revision_id=revision["id"], foreground_id=revision.get("foreground", {}).get("id", ""),
                      padding=1.1, preserve_frame=bool(mesh_backend(asset) == "pixal_multiview" or revision.get("camera", {}).get("known") or revision.get("recipe", {}).get("preserve_camera_frame")))
    graph.add("PreviewImage", images=image)
    graph.add("AW_FinishPreparation", asset_id=asset["id"], job_id=job["id"],
              **{"paths.view0": graph.out(image, 1)})
    return graph, {"slot": slot, "revision": revision}, ["Save editable foreground alpha and cutout. Preserve the original image."]


def mesh_recipe(asset, job, prepare_only=False, draft=False, geometry_only=False):
    graph = Graph()
    if draft:
        asset = copy.deepcopy(asset)
        asset["settings"]["mesh_backend"] = asset["settings"].get("draft_backend", "pixal_multiview")
        asset["settings"]["seed"] = asset["settings"].get("draft_seed", 0)
        for view in asset["views"]:
            view["enabled"] = view["id"] in asset["settings"].get("draft_source_views", ["view_01", "view_05"])
    settings = {**MESH_DEFAULTS, **asset["settings"], "mesh_backend": mesh_backend(asset)}
    if draft:
        settings.update({k:v for k,v in MESH_DEFAULTS.items() if k.endswith(("steps","cfg"))})
    else:
        settings["seed"] = settings.get("mesh_seed", settings["seed"])
    selected, images, paths, cameras = preparation(graph, asset)
    details = {"backend": settings["mesh_backend"], "settings": settings.copy(),
               "inputs": [{"slot": slot, "revision": rev, "camera": pose} for slot, rev, pose in selected]}
    if asset.get("schema_version") == 2:
        details.update(models={key: MODELS[key] for key in required_models(asset, "prepare" if prepare_only else "mesh")},
                       memory_preset_id=asset["memory_preset_id"], preset_overrides=asset["preset_overrides"])
    if draft:
        details.update(dependencies=draft_inputs(asset), resolution=512,
                       appearance=settings.get("draft_appearance", "geometry"))
    if prepare_only:
        for image in images:
            graph.add("PreviewImage", images=image)
        graph.add("AW_FinishPreparation", asset_id=asset["id"], job_id=job["id"],
                  **{f"paths.view{i}": path for i, path in enumerate(paths)})
        return graph, details, [f"{len(images)} images prepared; no reconstruction queued."]
    vision = graph.add("CLIPVisionLoader", clip_name=model_name("dino"))
    if settings["mesh_backend"] == "pixal_multiview":
        condition = graph.add("AW_PixalViews", clip_vision_model=vision, cameras=json.dumps(cameras),
                              scope=(settings.get("draft_appearance", "geometry") + "_draft") if draft else "full",
                              **{f"images.view{i}": image for i, image in enumerate(images)})
    elif settings["mesh_backend"] == "trellis2":
        condition = graph.add("Trellis2Conditioning", clip_vision_model=vision, image=images[0])
    else:
        mode, fov = source_fov(asset, selected[0][1])
        if mode == "auto":
            moge = graph.add("LoadMoGeModel", model_name=model_name("moge2"))
            geometry = graph.add("MoGeInference", moge_model=moge, image=images[0], resolution_level=9,
                                 fov_x_degrees=0, batch_size=1, force_projection=True, apply_mask=True, refine_steps=3 if geometry_only else 0)
            fov = graph.add("MoGeGeometryToFOV", moge_geometry=geometry, axis="horizontal", unit="degrees")
        details["source_camera"] = {"mode":mode, "record":f"jobs/{job['id']}-camera.json"}
        fov = graph.add("AW_RecordSourceFOV", fov=fov, asset_id=asset["id"], job_id=job["id"], mode=mode)
        condition = graph.add("Pixal3DConditioning", clip_vision_model=vision, image=images[0], camera_angle_x=fov)
    positive, negative = condition, graph.out(condition, 1)
    model = graph.add("UNETLoader", unet_name=model_name(settings["mesh_backend"]), weight_dtype="default")
    shape_vae = graph.add("VAELoader", vae_name=model_name("shape_vae"))
    structure_model = graph.add("CFGOverride", model=model, cfg=1, start_percent=.667, end_percent=1)
    structure_model = graph.add("RescaleCFG", model=structure_model, multiplier=.7)
    structure_model = graph.add("ModelSamplingSD3", model=structure_model, shift=5)
    structure_model = graph.add("AW_ModelBudget", model=structure_model, extra_gb=settings["extra_vram_headroom_gb"])
    shape_model = graph.add("CFGOverride", model=model, cfg=1, start_percent=.769, end_percent=1)
    shape_model = graph.add("RescaleCFG", model=shape_model, multiplier=.5)
    shape_model = graph.add("AW_ModelBudget", model=shape_model, extra_gb=settings["extra_vram_headroom_gb"])
    empty = graph.add("EmptyTrellis2LatentStructure", batch_size=1)

    def sample(model_input, pos, neg, latent, steps, cfg, scheduler="normal", offset=0):
        return graph.add("KSampler", model=model_input, positive=pos, negative=neg, latent_image=latent,
                         seed=int(settings["seed"]) + offset, steps=steps, cfg=cfg,
                         sampler_name="euler", scheduler=scheduler, denoise=1.0)

    structure = sample(structure_model, positive, negative, empty, settings["mesh_structure_steps"], settings["mesh_structure_cfg"], offset=14)
    voxel = graph.add("VaeDecodeStructureTrellis2", samples=structure, vae=shape_vae, resolution="32")
    shape = graph.add("Trellis2ShapeStage", positive=positive, negative=negative, voxel=voxel)
    shape_sample = sample(shape_model, shape, graph.out(shape, 1), graph.out(shape, 2), settings["mesh_shape_steps"], settings["mesh_shape_cfg"])
    if draft:
        upscale, high_sample = shape, shape_sample
    else:
        upscale = graph.add("Trellis2UpsampleStage", positive=shape, negative=graph.out(shape, 1),
                            shape_latent=shape_sample, vae=shape_vae, target_resolution=int(settings["shape_resolution"]))
        high_sample = sample(shape_model, upscale, graph.out(upscale, 1), graph.out(upscale, 2), settings["mesh_refine_steps"], settings["mesh_refine_cfg"], "simple")
    mesh = graph.add("VaeDecodeShapeTrellis", samples=high_sample, vae=shape_vae)
    if geometry_only:
        details["pipeline_version"] = "validated_v1"
        saved = graph.add("AW_SaveGeometry", mesh=mesh, asset_id=asset["id"], stage_id=job["id"],
                          geometry_stage="coarse", parent_id="", recipe=json.dumps(details))
        glb = graph.add("MeshToFile3D", mesh=saved)
        graph.add("Preview3DAdvanced", model_3d=glb, viewport_state="", width=1024, height=1024)
        return graph, details, ["Shape-only Pixal3D checkpoint. No texture generation before refinement and cleanup."]
    if draft and settings.get("draft_appearance", "geometry") == "geometry":
        return save_draft_graph(graph, mesh, asset, job, details, paths)
    texture_vae = graph.add("VAELoader", vae_name=model_name("texture_vae"))
    texture_model = graph.add("AW_ModelBudget", model=model, extra_gb=settings["extra_vram_headroom_gb"])
    texture = graph.add("Trellis2TextureStage", positive=upscale, negative=graph.out(upscale, 1), shape_latent=high_sample)
    tex_sample = sample(texture_model, texture, graph.out(texture, 1), graph.out(texture, 2), settings["mesh_material_steps"], settings["mesh_material_cfg"], offset=1)
    tex_voxel = graph.add("VaeDecodeTextureTrellis", samples=tex_sample, vae=texture_vae, shape_subdivides=graph.out(mesh, 1))
    if draft:
        painted = graph.add("PaintMesh", mesh=mesh, voxel_colors=tex_voxel)
        return save_draft_graph(graph, painted, asset, job, details, paths)
    checkpoint = graph.add("AW_SaveMaster", mesh=mesh, voxel=tex_voxel, asset_id=asset["id"],
                           job_id=job["id"], recipe=json.dumps(details))
    glb = graph.add("MeshToFile3D", mesh=checkpoint)
    graph.add("Preview3DAdvanced", model_3d=glb, viewport_state="", width=1024, height=1024)
    return graph, details, [f"{len(images)} approved images reach {settings['mesh_backend']}. Raw native master saved before finishing."]


def save_draft_graph(graph, mesh, asset, job, details, paths):
    glb = graph.add("MeshToFile3D", mesh=mesh)
    saved = graph.add("AW_SaveDraft", mesh=mesh, model_3d=glb, asset_id=asset["id"], job_id=job["id"],
                      recipe=json.dumps(details), **{f"paths.view{i}":path for i,path in enumerate(paths)})
    graph.add("Preview3DAdvanced", model_3d=saved, viewport_state="", width=1024, height=1024)
    return graph, details, ["Save a 512-resolution draft for camera guides. Review its shape before approving it. Final mesh quality settings are unchanged."]


def guide_recipe(asset, job, slot):
    draft = next((d for d in asset.get("drafts", []) if d["id"] == asset.get("selected_draft")), None)
    if not draft or draft.get("stale") or not draft.get("approved"):
        raise ValueError("Review and approve a current draft before rendering camera guides.")
    view = next(v for v in asset["views"] if v["id"] == slot)
    pose = {key:view[key] for key in ("azimuth", "elevation", "fov")}
    camera = camera_guides.orbit(draft, pose)
    graph = Graph()
    source = graph.add("AW_LoadDraft", asset_id=asset["id"], draft_id=draft["id"])
    mesh = graph.add("Get3DComponents", model_3d=source)
    camera_node = graph.add("CreateCameraInfo", mode="look_at",
        **{f"mode.position_{axis}":value for axis,value in zip("xyz",camera["position"])},
        **{f"target_{axis}":value for axis,value in zip("xyz",camera["target"])},
        roll=0, fov=camera["fov"], zoom=1, camera_type="perspective")
    common = dict(mesh=mesh, width=1024, height=1024, background="#000000", camera_info=camera_node)
    depth = graph.add("RenderMesh", "Render depth — near is white", mode="depth", **common)
    normal = graph.add("RenderMesh", "Render surface normals", mode="normal", **common)
    color = graph.add("RenderMesh", "Render draft appearance", mode="vertex colors", **common) if draft["appearance"] == "color" else None
    details = {"draft":draft["id"], "draft_sha256":draft["sha256"], "slot":slot,
               "pose":pose, "camera":camera, "appearance":draft["appearance"]}
    graph.add("AW_SaveGuide", asset_id=asset["id"], job_id=job["id"], recipe=json.dumps(details),
              depth=depth, normal=normal, mask=graph.out(depth,1),
              **({"color":color} if color else {}))
    return graph, details, [f"Render {view['name']} from the approved draft. No image-generation or reconstruction model is loaded."]


def export_recipe(asset, job, kind, master_id):
    graph = Graph()
    settings = asset["settings"]
    if kind == "game" and asset.get("schema_version") != 2:
        master = next((m for m in reversed(asset["masters"]) if m.get("approved")), None)
        if not master:
            raise ValueError("Build, review and accept a textured master before making the game export.")
    else:
        master = next((m for m in asset["masters"] if m["id"] == master_id), None)
    if not master:
        raise ValueError("The selected native master does not exist.")
    source = graph.add("AW_LoadMaster", asset_id=asset["id"], master_id=master["id"])
    raw, voxel = source, graph.out(source, 1)
    mesh = raw
    if settings["remesh"]:
        mesh = graph.add("RemeshMesh", mesh=mesh, resolution=768, sign_mode="solid",
                         **{"sign_mode.fill": 20, "sign_mode.qef": True}, band=1, project_back=0,
                         fix_poles=False, smooth_iters=int(settings["smoothing"]),
                         drop_small_components=0, precluster_max_verts=20000000)
    mesh = graph.add("DecimateMesh", mesh=mesh, target_face_count=int(settings[f"{kind}_faces"]), placement_mode="midpoint")
    mesh = graph.add("MeshSmoothNormals", mesh=mesh, crease_angle=float(settings["crease_angle"]))
    mesh = graph.add("UnwrapMesh", mesh=mesh, segmenter=settings["uv_method"],
                     resolution=int(settings[f"{kind}_texture"]), padding=4, weld_distance=.0002)
    textures = graph.add("BakeTextureFromVoxel", mesh=mesh, voxel_colors=voxel,
                         texture_size=int(settings[f"{kind}_texture"]), reference_mesh=raw)
    normal = graph.add("BakeNormalMapFromMesh", low_poly=mesh, high_poly=raw,
                       resolution=int(settings["normal_resolution"]), cage_distance=.05, ignore_backfaces=True) if settings.get("bake_normal", True) else None
    ao = graph.add("BakeAmbientOcclusion", low_poly=mesh, high_poly=raw,
                   resolution=int(settings["ao_resolution"]), samples=64, max_distance=.71, strength=1, bias=.01) if settings.get("bake_ao", True) else None
    painted = graph.add("ApplyTextureToMesh", mesh=mesh, base_color=textures, metallic=graph.out(textures, 1),
                        roughness=graph.out(textures, 2), **({"normal_map": normal} if normal else {}),
                        **({"occlusion": ao} if ao else {}))
    scaled = graph.add("AW_ScaleMesh", mesh=painted, height_meters=float(settings["asset_height"]))
    glb = graph.add("MeshToFile3D", mesh=scaled)
    saved = graph.add("AW_Export", model_3d=glb, mesh=scaled, asset_id=asset["id"], master_id=master["id"],
                      job_id=job["id"], kind=kind, metallic=graph.out(textures, 1), roughness=graph.out(textures, 2),
                      **({"ao": ao} if ao else {}))
    graph.add("Preview3DAdvanced", model_3d=saved, viewport_state="", width=1024, height=1024)
    details = {"master": master["id"], "kind": kind, "settings": settings.copy()}
    if asset.get("schema_version") == 2:
        details.update(memory_preset_id=asset["memory_preset_id"], preset_overrides=asset["preset_overrides"])
    return graph, details, [f"{kind.capitalize()} export uses saved native data. No image or reconstruction model is loaded."]


def single_image_mesh_recipe(snapshot: dict, prepared: dict, attempt_id: str, geometry_only=False) -> dict:
    primary = approved_primary(snapshot)
    current = approved_primary(prepared)
    if (current["id"], current["sha256"]) != (primary["id"], primary["sha256"]):
        raise ApprovalRequired("The approved image changed after this job was prepared.")
    asset = copy.deepcopy(snapshot)
    if current.get("foreground"):
        for revision in asset["images"]["mesh_input"]["revisions"]:
            if revision["id"] == primary["id"]:
                revision["foreground"] = copy.deepcopy(current["foreground"])
    asset["settings"]["mesh_backend"] = "pixal_single"
    requested = asset["settings"]["mesh_requested_seed"]
    asset["settings"]["mesh_seed"] = asset["settings"]["seed"] if requested < 0 else int(requested)
    if geometry_only:
        asset["settings"].update(mesh_refine_steps=20,shape_resolution=asset.get("pipeline",{}).get("settings",{}).get("shape_resolution",1024))
    graph, details, bindings = mesh_recipe(asset, {"id": attempt_id}, geometry_only=geometry_only)
    details["primary_image"] = {key: primary[key] for key in ("id", "file", "sha256")}
    return {"graph": graph.nodes, "details": details, "bindings": bindings}


def finish_saved_master_recipe(snapshot: dict, master_artifact: dict, attempt_id: str) -> dict:
    if snapshot["settings"]["uv_method"] != "pec":
        raise CapabilityError("This workflow requires PEC GPU finishing. CPU adaptive unwrapping is not a fallback.")
    if master_artifact.get("stale"):
        raise ApprovalRequired("This master belongs to older reconstruction inputs. Choose the matching History project.")
    primary = approved_primary(snapshot)
    inputs = master_artifact.get("recipe", {}).get("inputs", [])
    if inputs and any(item["revision"]["id"] != primary["id"] for item in inputs):
        raise ApprovalRequired("This master belongs to a different mesh-input image.")
    asset = copy.deepcopy(snapshot)
    asset["masters"] = [master_artifact]
    height = asset.get("target", {}).get("requested_dimensions_m", {}).get("height")
    if height is not None:
        asset["settings"]["asset_height"] = height
    kind = asset.get("task_payload", {}).get("export_kind", "master")
    if kind not in ("master", "game"):
        raise ValueError("Choose a master or game export.")
    if kind == "game" and not any(a["kind"] == "mesh" and a.get("export_kind") == "master" and
            a.get("master") == master_artifact["id"] and not a.get("stale") for a in asset["artifacts"]):
        raise ApprovalRequired("Complete and review the matching master export before requesting its game version.")
    graph, details, bindings = export_recipe(asset, {"id": attempt_id}, kind, master_artifact["id"])
    return {"graph": graph.nodes, "details": details, "bindings": bindings}


def build(asset, job, stage, slot="design", action="generate", angle_prompt=None, edit=None):
    if stage == "image":
        return image_recipe(asset, job, slot, action, angle_prompt, edit)
    if stage == "foreground":
        return foreground_recipe(asset, job, slot)
    if stage == "draft":
        return mesh_recipe(asset, job, draft=True)
    if stage == "guide":
        return guide_recipe(asset, job, slot)
    if stage in ("prepare", "mesh"):
        return mesh_recipe(asset, job, stage == "prepare")
    if stage in ("master", "game"):
        return export_recipe(asset, job, stage, slot)
    raise ValueError("Unknown stage.")
