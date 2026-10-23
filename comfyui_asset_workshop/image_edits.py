"""Saved selections and reviewable image-edit candidates."""

import io
import json
import time
import uuid

from PIL import Image, ImageChops, ImageFilter, PngImagePlugin

from .store import LOCK, atomic_json, digest, identifier, reset_angles


def create(library, asset_id, slot, revision_id, prompt, mask_bytes, feather=0, replace_detail=False):
    if type(replace_detail) is not bool:
        raise ValueError("Replace selected details must be true or false.")
    prompt = str(prompt).strip()
    if not prompt or len(prompt) > 16000:
        raise ValueError("Describe the change in 1 to 16000 characters.")
    feather = int(feather)
    if not 0 <= feather <= 32:
        raise ValueError("Edge softness must be between 0 and 32 pixels.")
    asset = library.load(asset_id)
    source = library.revision(asset, slot)
    if source["id"] != revision_id:
        raise ValueError("This image changed. Close the editor and open its latest version.")
    source_path = library.path(asset_id, source["file"])
    if digest(source_path) != source["sha256"]:
        raise ValueError("The source image changed on disk. Import it again before editing.")
    with Image.open(source_path) as original, Image.open(io.BytesIO(mask_bytes)) as uploaded:
        if uploaded.size != original.size or uploaded.width * uploaded.height > 40_000_000:
            raise ValueError("The selection must match the image dimensions and be below 40 megapixels.")
        mask = uploaded.convert("L")
    if not mask.getbbox():
        raise ValueError("Select the area you want to change first.")
    if feather:
        # Fade inward only; never expand the area the user allowed us to change.
        mask = ImageChops.multiply(mask, mask.filter(ImageFilter.GaussianBlur(feather)))
    edit_id = uuid.uuid4().hex[:16]
    relative = f"edits/{edit_id}/mask.png"
    path = library.path(asset_id, relative)
    path.parent.mkdir(parents=True, exist_ok=False)
    mask.save(path, format="PNG")
    record = {
        "id": edit_id, "slot": identifier(slot), "prompt": prompt,
        "source": {k: source[k] for k in ("id", "file", "sha256")},
        "mask": {"file": relative, "sha256": digest(path), "size": list(mask.size)},
        "feather": feather, "replace_detail": replace_detail, "created": time.time(),
    }
    atomic_json(library.path(asset_id, f"edits/{edit_id}/edit.json"), record)
    return record


def load(library, asset, edit_id, slot):
    record = json.loads(library.path(asset["id"], f"edits/{identifier(edit_id)}/edit.json").read_text())
    if record["slot"] != slot or library.revision(asset, slot)["id"] != record["source"]["id"]:
        raise ValueError("The image changed since this selection was made. Open the editor again.")
    for image in (record["source"], record["mask"]):
        if digest(library.path(asset["id"], image["file"])) != image["sha256"]:
            raise ValueError("An edit input changed on disk. Make a new selection before retrying.")
    return record


def composite(library, asset_id, generated, edit):
    with Image.open(library.path(asset_id, edit["source"]["file"])) as image:
        original = image.convert("RGBA")
    with Image.open(library.path(asset_id, edit["mask"]["file"])) as image:
        mask = image.convert("L")
    generated = generated.convert("RGBA").resize(original.size, Image.Resampling.LANCZOS)
    return Image.composite(generated, original, mask)


def save_candidate(library, asset_id, slot, job_id, generated, details):
    result = composite(library, asset_id, generated, details["edit"])
    revision_id = uuid.uuid4().hex[:16]
    relative = f"images/{identifier(slot)}/{revision_id}.png"
    path = library.path(asset_id, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngImagePlugin.PngInfo()
    info.add_text("asset_workshop", json.dumps(details))
    temporary = path.with_suffix(".part")
    result.save(temporary, format="PNG", pnginfo=info)
    temporary.replace(path)
    revision = {"id": revision_id, "file": relative, "sha256": digest(path),
                "created": time.time(), "recipe": details, "edit_accepted": False}
    library.add_revision(asset_id, slot, revision, select=False)
    library.complete_job(asset_id, job_id, {"slot": slot, "revision": revision_id, "edit_preview": True})
    return result, revision


def accept(library, asset_id, slot, revision_id):
    with LOCK:
        asset = library.load(asset_id)
        target = library.slot(asset, slot)
        candidate = next(r for r in target["revisions"] if r["id"] == identifier(revision_id))
        edit = candidate.get("recipe", {}).get("edit")
        if not edit:
            raise ValueError("Choose a generated edit preview.")
        if target["current"] != edit["source"]["id"]:
            if target["current"] == candidate["id"] and candidate.get("edit_accepted"):
                return asset
            raise ValueError("The original changed while this preview was open. Your preview is saved in History.")
        load(library, asset, edit["id"], slot)
        if asset.get("schema_version") == 2:
            target.update(current=candidate["id"], approved=None, stale=False)
            candidate["edit_accepted"] = True
            if slot == "source":
                original = next((r for r in asset["sources"] if r["id"] == edit["source"]["id"]), None)
                enabled = original.get("enabled", True) if original else True
                if original:
                    original["enabled"] = False
                asset["sources"].append({**candidate, "enabled": enabled})
            library._stale_project_artifacts(asset, slot)
            return library.save(asset)
        asset = library.approve(asset_id, slot, revision_id)
        next(r for r in library.slot(asset, slot)["revisions"] if r["id"] == revision_id)["edit_accepted"] = True
        if slot == "initial":
            asset["design"].update(current=None, approved=None, stale=False)
            reset_angles(asset)
        elif slot != "design":
            library.slot(asset, slot)["enabled"] = True
        for result in (*asset["masters"], *asset["exports"]):
            result["stale"] = True
        asset["selected_master"] = None
        asset["selected_export"] = None
        return library.save(asset)
