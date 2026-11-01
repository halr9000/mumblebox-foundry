"""Versioned creator recipes and explicit ordered image references."""
from pathlib import PurePosixPath
from .definition import CATEGORIES
from .turnaround import model_spec, RECIPE_VERSION

CHARACTER_PROMPT = "Turn the character in <image1> into an orthographic 3D modeling reference sheet: a single horizontal row of four equal-width panels, evenly spaced. From left to right: 1) front view. 2) left side view, an exact 90° profile, snout pointing to the left edge of the image, only one eye visible, the near arm pointing straight at the camera and strongly foreshortened, the far arm hidden behind the body. 3) back view, exactly 180°. 4) right side view, an exact 90° profile, snout pointing to the right edge of the image, only one eye visible, near arm foreshortened toward the camera, far arm hidden. The camera orbits a completely static character: same T-pose and same head direction in every view, the character never turns toward the camera. Identical outfit, colors, proportions and scale in all views, each character centered in its panel, feet on the same baseline, no overlap between views. Flat, even lighting, solid black background, no text, no labels."

# Camera/layout contract follows PixelArtistry's MIT-licensed prompt formula.
# The character text is preserved verbatim from our successful native graph.
SOURCE = "https://github.com/pixelartistry/PixelArtistry-Pixal3D-Multiview"
OBJECT_PROMPT = (
    "Turn the {subject} in <image1> into an orthographic 3D modeling reference sheet: "
    "a single horizontal row of four equal-width panels, evenly spaced. From left to right: "
    "1) front view. 2) left side view, an exact 90-degree profile. "
    "3) back view, exactly 180 degrees. 4) right side view, an exact 90-degree profile. "
    "The camera orbits a completely static {subject}: same orientation and shape in every view. "
    "Identical details, colors, materials, proportions and scale in all views, each subject centered "
    "in its panel with generous empty margins, aligned to the same baseline, no overlap between views. "
    "Flat, even lighting, solid black background, no text, no labels."
)
SUBJECTS = {"creatures": "creature", "vehicles": "vehicle",
            "props": "object", "environment": "environment piece"}
CATEGORY_DETAILS = {
    "creatures": "Preserve the creature's actual anatomy, limb count, natural stance and all existing tails, wings or horns. Keep limbs and appendages in the same position while the camera orbits; do not humanize its body or add parts. Side views show the true profile, with hidden far-side parts naturally occluded.",
    "vehicles": "Keep the chassis, wheel count, wheelbase, wings, landing gear and attached components fixed. Preserve actual left-right asymmetry; do not mirror markings or invent wheels. Side views show the full length and true depth; the rear shows the corresponding rear construction, not a second front.",
    "props": "Keep all attached components, handles, fasteners and openings in their fixed locations. Side views show the object's real thickness and depth. The back must be the corresponding rear surface and construction, not a mirrored front. Use a supplied rear reference for unseen construction when available.",
    "environment": "Show a single isolated, coherent environment piece. Preserve its footprint, roofline, openings, overhangs and structural features in all views. Keep vegetation and attached details fixed. Do not turn the image into a landscape, scene layout or collection of separate objects."
}
ROLE_TEXT = {"back": "Rear of the same asset; use for rear construction.",
             "face": "Face or identity reference; preserve the primary asset's other features.",
             "component": "Component reference; apply only as described.",
             "style": "Visual style reference; preserve the primary asset's structure.",
             "detail": "Detail reference; apply only as described."}

def bind_references(category, references, model_id="qwen21"):
    spec = model_spec(model_id)
    if category not in {x["id"] for x in CATEGORIES}:
        raise ValueError("Choose an available asset category.")
    if not isinstance(references, list) or not 1 <= len(references) <= spec["max_references"]:
        raise ValueError(f"{spec['name']} supports 1–{spec['max_references']} references in this workflow. Remove excess cards or choose another model; references are never silently dropped.")
    if not all(isinstance(item, dict) for item in references):
        raise ValueError("Each reference must be an image card.")
    if references[0].get("role") != "primary":
        raise ValueError("The first image must show the overall asset.")
    bindings, notes, ids = {}, [], set()
    for index, item in enumerate(references, 1):
        identifier, filename = item.get("id"), item.get("filename")
        if not isinstance(identifier, str) or not identifier or identifier in ids:
            raise ValueError("Each reference needs a unique image ID.")
        ids.add(identifier)
        if not isinstance(filename, str) or not filename or "\\" in filename:
            raise ValueError("Choose an uploaded reference image.")
        path = PurePosixPath(filename)
        if path.is_absolute() or ".." in path.parts or ":" in filename:
            raise ValueError("Reference files must belong to the input directory.")
        description = item.get("description", "")
        if not isinstance(description, str):
            raise ValueError("Reference descriptions must be text.")
        description = description.strip()
        if len(description) > 800:
            raise ValueError("Keep each reference description under 800 characters.")
        bindings["image" + str(index)] = filename
        if index > 1:
            role = item.get("role", "detail")
            if role not in ROLE_TEXT:
                raise ValueError("Choose a supported reference purpose.")
            if role in ("component", "style", "detail") and not description:
                raise ValueError("Describe what image " + str(index) + " contributes to the asset.")
            notes.append("<image" + str(index) + ">: " + ROLE_TEXT[role] + " " + description)
        elif description:
            notes.append("<image1>: " + description)
    prompt = CHARACTER_PROMPT if category == "characters" else OBJECT_PROMPT.format(subject=SUBJECTS[category])
    if category != "characters":
        prompt += " " + CATEGORY_DETAILS[category]
    if notes:
        prompt += ("\n\nReference instructions: <image1> is the primary overall asset. "
                   "Additional references apply only to the described part or view; keep other primary details unchanged.\n"
                   + "\n".join(notes))
    # Native encoders use different ordered reference labels. Keep role notes
    # and their indices together instead of duplicating a prompt per variant.
    for index in range(len(references),0,-1):
        token = f"<image{index}>"
        if model_id == "qwen2511":
            prompt = prompt.replace(token,f"Picture {index}")
        elif model_id.startswith("flux3"):
            prompt = prompt.replace(token,f"<ref_image_{index-1}>")
        elif model_id.startswith("klein"):
            prompt = prompt.replace(token,f"image {index}")
    if model_id.startswith("flux3"):
        prompt = "The finished image is an orthographic four-view reference sheet of this exact same asset. " + prompt
    return {"prompt": prompt, "bindings": bindings, "source": SOURCE,
            "recipe": category + "/" + model_id + "/" + RECIPE_VERSION,
            "guidance": "Published character text" if category == "characters" else "Foundry category adaptation of the published four-view layout"}
