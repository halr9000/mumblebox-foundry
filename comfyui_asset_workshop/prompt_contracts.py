"""Task-specific language adapted from pinned publisher guidance.

These instructions run in our existing local assistant. They are not the Qwen PE
or BFL PUP checkpoints. Exact adapter trigger/order is owned by recipes.py.
"""
import re

VERSION = 2
CATEGORIES = {
    "props": "Preserve the object's silhouette, part counts, materials, markings and functional openings.",
    "characters": "Preserve identity, fixed pose, specified limb and finger counts, clothing and equipment attachments. Do not impose human anatomy on a differently specified character.",
    "creatures": "Preserve the specified anatomy, limb and appendage counts, head and tail direction, pose and marking placement. Do not add human hands or manufactured panels.",
    "vehicles": "Preserve travel direction, rigid proportions, wheel, engine and fin counts, openings and the assigned side of every fitting.",
    "environment": "Preserve structural silhouette, openings, repeated element counts, roof and base treatment, specified connection faces and vegetation branching. Depict one requested piece rather than an entire scene.",
}
SOURCES = {
    "sdxl": ["https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0",
             "https://huggingface.co/RunDiffusion/Juggernaut-XL-v9",
             "https://github.com/cubiq/ComfyUI_IPAdapter_plus/blob/main/NODES.md"],
    "klein": ["https://github.com/black-forest-labs/skills/blob/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/t2i-prompting.md",
              "https://github.com/black-forest-labs/skills/blob/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/i2i-prompting.md"],
    "qwen21": ["https://github.com/QwenLM/Qwen-Image-2.1/tree/ab96caa944157ca28a4f36b695c3047549f48f98/prompt_rewrite/prompts"],
    "qwen2511": ["https://huggingface.co/Qwen/Qwen-Image-Edit-2511", "https://github.com/QwenLM/Qwen-Image"],
    "flux3": ["https://github.com/black-forest-labs/flux-3-image-klein/blob/bfc8889a4497f846416f253a3972a1941ac698b9/src/flux3/pup_prompts_external_vlm.json"],
}


def family(profile):
    if profile in ("sdxl_base", "sdxl_juggernaut"):
        return "sdxl"
    if profile in ("klein4", "klein4_base", "klein_base", "klein_distilled", "klein_kv"):
        return "klein"
    if profile in ("flux3_base", "flux3_distilled"):
        return "flux3"
    if profile in ("qwen21", "qwen2511"):
        return profile
    raise ValueError("No prompting guidance is configured for this image model.")


def contract(profile, action, has_images, category="props"):
    name = family(profile)
    if category not in CATEGORIES or action not in ("describe", "enhance"):
        raise ValueError("Choose a supported asset type and description action.")
    task = "describe" if action == "describe" else "edit" if has_images else "create"
    if name == "qwen2511" and task == "create":
        raise ValueError("Qwen Edit 2511 needs an image. Upload a reference or choose a creation model.")
    limits = {"klein": 640, "qwen21": 1200, "qwen2511": 900, "flux3": 1200, "sdxl": 640}
    if action == "describe":
        instruction = ("Report only visible object facts in plain English. Never invent hidden surfaces, "
                       "counts, materials, or unseen anatomy. Do not add a new scene or change the object. "
                       "Use ordinary descriptive prose, without reference tokens or editing commands.")
    elif name == "sdxl":
        instruction = ("Write an SDXL visual prompt describing the finished asset. Put the subject, visible shape, materials, "
                       "colors and requested style first, then composition, background and lighting. Keep it concise and concrete. "
                       "Preserve the user's style rather than forcing photorealism. Do not use Qwen image tokens, FLUX JSON, "
                       "editing conversations, invented LoRA tags or guessed trigger words. The application handles reference "
                       "conditioning and canvas size. Describe desired visible results rather than asking the model to reason. "
                       "Do not append a negative prompt; it has its own control. For Juggernaut, avoid stuffing generic quality "
                       "tags or heavy negatives into the prompt. Return only the prompt.")
    elif name == "klein":
        instruction = ("Write focused natural prose for FLUX.2 Klein. Put the subject and requested operation first. "
                       "For creation, describe the subject, its attributes, pose, style, background and lighting. "
                       "For reference editing, state the exact change, identify references in ordinary words "
                       "such as 'the first image', and explicitly preserve the other identity details. "
                       "Prefer concise concrete wording to a long scene description or keyword list. "
                       "Use positive descriptions, without a separate negative prompt or model-weight syntax.")
    elif name == "qwen21":
        instruction = ("Prepare a Qwen Image 2.1 request. " +
            ("Write a precise editing directive anchored to the supplied images. Separate the changed attribute "
             "from the retained appearance. For multiple references use <image1>, <image2>, etc. in their supplied order; "
             "each reference contributes only its assigned role. Keep existing on-image text unchanged unless requested. "
             if has_images else
             "Describe the finished image as an observer in one detailed English paragraph. Preserve every specified "
             "subject, count, color and spatial constraint. Transcribe requested on-image wording exactly in quotes. ") +
            "The application owns the output canvas: keep this single asset fully visible on a square neutral background. "
            "Return the rewritten prose only; do not append aspect-ratio JSON or change canvas settings.")
    elif name == "qwen2511":
        instruction = ("Write a Qwen Image Edit 2511 editing instruction, not a Qwen 2.1 PE response. "
                       "Name the specific change and the visual appearance to retain. Identify inputs as Picture 1, "
                       "Picture 2 and Picture 3 in the supplied order, each with its assigned role. Keep identity, "
                       "structure and any text outside the requested change consistent. Use plain instructions, "
                       "without Qwen 2.1 image tokens, aspect-ratio metadata or unrelated scene elaboration.")
    else:
        instruction = ("Prepare the FLUX 3 Image Klein prompt as a full caption of the final scene in one continuous prose block. "
            "Describe the finished subject, concrete colors/materials, spatial placement, form, background and lighting. "
            "For an edit describe the resulting image, including unchanged visual context; do not return only a short change command. "
            "Refer to references by ordinal or visible content, never angle-bracket tokens. "
            "If no medium is specified, use a studio photograph. Preserve explicit style choices and avoid promotional adjectives. " +
            "Preserve all explicit counts, locations, constraints and quoted text. Use concrete spatial relations. "
            "Do not output headings, explanations, coordinates, JSON, annotation IDs or reference tokens.")
    instruction += "\nAsset type guidance: " + CATEGORIES[category]
    return {"id": f"{name}-{task}-v{VERSION}", "profile": profile, "category": category,
            "task": task, "sources": SOURCES[name], "instruction": instruction,
            "max_tokens": 768 if action == "describe" else limits[name],
            "helper": "Local vision assistant with publisher-guided instructions; not official PE/PUP weights"}


def image_task(profile_id: str, task: str, user_description: str, design_notes: str,
               requested_view: str | None, *, category: str = "props",
               has_images: bool | None = None) -> dict:
    if task not in ("create_image", "three_quarter", "edit_image", "reference_view"):
        raise ValueError("Choose a supported image task.")
    name = family(profile_id)
    if category not in CATEGORIES:
        raise ValueError("Choose a supported asset type.")
    views = {"front": "a full front view at mid-height", "back": "a full back view at mid-height",
             "left": "a full left-side view at mid-height", "right": "a full right-side view at mid-height"}
    if task == "reference_view" and requested_view not in views:
        raise ValueError("Choose front, back, left or right for the design reference.")
    camera = ("a front-right three-quarter view, approximately 45 degrees around the object, "
              "showing both its front and side with a little of the top visible"
              if task == "three_quarter" else views.get(requested_view, "the requested composition"))
    preserve = ("Show one complete object with consistent proportions and all extremities inside the frame. "
                "Use a plain neutral background and clear lighting. Keep the requested style, materials, "
                "part counts and features on their assigned surfaces. Do not add a contact sheet or multiple panels.")
    preserve += " " + CATEGORIES[category]
    if task == "reference_view":
        subject = "the same object as the approved primary reference"
        preserve += " Show features belonging to this visible side; do not transfer front-only features onto the back or sides."
    else:
        subject = user_description.strip() or "the same object as the selected reference images"
    source_conditioned = (task != "create_image" or profile_id == "qwen2511") if has_images is None else has_images
    system = contract(profile_id, "enhance", source_conditioned, category)["instruction"]
    system += ("\nRewrite for the requested view. Include only features visible on that side; preserve explicit "
               "unseen-side requirements as design constraints rather than copying them onto visible surfaces.")
    if name == "sdxl":
        subject = user_description.strip().rstrip("., ") or "object matching the visual references"
        kind = {"props":"single object", "characters":"single character, coherent anatomy",
                "creatures":"single creature, coherent anatomy", "vehicles":"single vehicle",
                "environment":"single environment piece"}[category]
        composition = "front-right three-quarter view" if task == "three_quarter" else views.get(requested_view, "")
        prompt = ", ".join(part for part in (subject, composition, kind, "one viewpoint", "full object visible",
                            "plain neutral background", "clear lighting") if part)
    elif name == "flux3":
        prompt = f"An image of {subject}, shown in {camera}. {preserve}"
    elif name == "klein":
        prompt = f"Show {subject} in {camera}. {preserve}"
    elif name == "qwen2511":
        prompt = f"Recreate {subject} using Picture 1, changing the viewpoint to {camera}. {preserve}"
    else:
        prompt = f"Create {subject}, shown in {camera}. {preserve}"
    if task == "edit_image":
        prompt = (f"{user_description}. Same subject, materials, lighting and camera as the source image."
                  if name == "sdxl" else
                  f"A finished image of the same subject, with this requested change: {user_description}. "
                  "The camera, framing and every detail outside the selection remain unchanged."
                  if name == "flux3" else
                  f"Edit only the selected area of the first image: {user_description}. "
                  "Keep camera, framing and all unselected details unchanged.")
    if design_notes.strip():
        prompt += " Explicit design requirements: " + design_notes.strip()
    return {"system": system, "category": category, "user": {"description": user_description, "design_notes": design_notes,
            "task": task, "requested_view": requested_view}, "prompt": prompt,
            "requested_view": "front-right three-quarter" if task == "three_quarter" else requested_view,
            "sources": SOURCES[name], "camera_verification": "not_measured"}


def angle_text(profile, parts, view, route="references"):
    """Compile shared physical facts into the selected family's requested view."""
    name = family(profile)
    faces = {0:["front"],45:["front","right"],90:["right"],135:["back","right"],
             180:["back"],225:["back","left"],270:["left"],315:["front","left"]}
    az, elevation = float(view["azimuth"])%360, float(view["elevation"])
    nearest = min(faces,key=lambda x:abs((x-az+180)%360-180))
    visible = list(faces[nearest]) if abs(elevation)<89 else []
    if elevation: visible.append("top" if elevation>0 else "underside")
    facts = "; ".join(f"{face}: {parts[face]}" for face in visible if parts.get(face))
    preserve = " Preserve its construction and keep features on their assigned surfaces."
    if parts.get("pose"): preserve += " Keep this pose: " + parts["pose"] + "."
    if route != "references":
        # The adapter's trigger already names the guide camera and reference order.
        # Repeating free-form camera/degree instructions can compete with that guide.
        return parts["identity"].rstrip(".") + ". Visible surface details: " + facts + "." + preserve
    if abs(elevation)>=89:
        camera = "directly above, exposing the top" if elevation>0 else "directly below, exposing the underside"
    else:
        camera = " and ".join(faces[nearest]) + (" three-quarter view" if len(faces[nearest])==2 else " view, square to the camera")
        camera += (f", looking down from {elevation:g} degrees above" if elevation>0 else
                   f", looking upward from {abs(elevation):g} degrees below" if elevation<0 else ", at mid-height")
    opening = ("Show the same " if name=="klein" else "Change the viewpoint of the same " if name=="qwen2511" else "Create an image of the same ")
    output = opening + parts["identity"].rstrip(".") + " from its " + camera + ". "
    output += "Visible details: " + facts + "." + preserve
    if len(faces[nearest])==2 and abs(elevation)<89:
        left,right={45:("right","front"),135:("back","right"),225:("left","back"),315:("front","left")}[nearest]
        output += f" The {left} surface appears on image-left and the {right} surface on image-right."
    output += " Show the complete object on a plain neutral background."
    if elevation<0: output += " Keep the underside unobstructed by a floor."
    return output


def validate_output(text, finish_reason=None):
    text = text.strip() if isinstance(text,str) else ""
    if (not text or finish_reason=="length" or len(text)>16000
            or re.search(r"<\/?think\b|```|^\s*(?:here is|here's)\b",text,re.I)):
        raise ValueError("The assistant returned incomplete or unusable text. Your original description is unchanged; retry or keep your own text.")
    return text
