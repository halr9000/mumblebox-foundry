"""Image-purpose guidance; native model recipes remain the conditioning owner."""
from .definition import is_pair

GUIDANCE={
    "characters":"Full-body front view. Relaxed A-pose, arms separated from the torso, hands visible, feet apart. Preserve the character's proportions.",
    "creatures":"Complete creature from the front in a natural stable stance. Show all limbs and appendages without overlapping the body where practical.",
    "props":"One complete prop viewed directly from the front, with all attached parts visible and no cut-off edges.",
    "vehicles":"One complete vehicle viewed directly from the front, level and centered, with wheels and other attached parts intact.",
    "environment":"One complete building or environment piece viewed from the front, isolated from surrounding scenery, keeping its foundation and roof in frame.",
}
SOURCES=["https://huggingface.co/Qwen/Qwen-Image-Edit-2511",
         "https://huggingface.co/black-forest-labs/FLUX.2-klein-4B"]

def compile_prompt(config, side, edit=None):
    paired=is_pair(config["category"])
    if side not in (("front","back") if paired else ("single",)):raise ValueError("Choose a view belonging to this creation.")
    if edit is not None:
        prompt="Edit only the selected area of the first image. Keep the camera, framing and everything outside it unchanged. "+edit.strip()
        task="edit_image"
    elif side=="back":
        prompt=("Show the exact same subject from the first image, viewed directly from behind. "
                "Keep the same pose, proportions, scale, colors and materials. Keep the whole subject in frame on the same plain background.")
        if config["back"]:prompt+=" Back details: "+config["back"]
        task="reference_view"
    else:
        prompt=config["description"]
        if paired:
            if config["front"]:prompt+="\nFront details: "+config["front"]
            prompt+="\n"+GUIDANCE[config["category"]]+" Plain neutral background, even studio lighting, generous enough framing to retain the complete silhouette. One subject, one view, no labels or collage."
        task="create_image"
    return {"user":{"task":task},"prompt":prompt.strip(),"requested_view":side,"sources":SOURCES if paired or edit else [],
            "guidance":"Foundry image-purpose guidance; camera angles are requested, not measured."}
