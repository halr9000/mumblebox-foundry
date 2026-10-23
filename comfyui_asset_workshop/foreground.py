"""Revisioned foreground alpha, separate from generative edit selections."""
import json
import math
import time
import uuid

from PIL import Image, ImageChops, ImageFilter

from .store import LOCK, atomic_json, digest, identifier, invalidate_mesh


def frame(image, alpha, padding=1.1, size=1024, preserve_frame=False):
    if image.size != alpha.size:
        raise ValueError("The foreground mask must match the source image dimensions.")
    alpha = alpha.convert("L")
    bounds = alpha.point(lambda p: 255 if p > 12 else 0).getbbox()
    if not bounds:
        raise ValueError("The foreground is empty. Keep some of the object before continuing.")
    if not 1 <= padding <= 2 or not 8 <= size <= 4096:
        raise ValueError("Invalid foreground framing settings.")
    w, h = image.size
    if preserve_frame:
        side = max(w, h)
        left, top = (w-side)//2, (h-side)//2
    else:
        side = math.ceil(max(bounds[2]-bounds[0], bounds[3]-bounds[1]) * padding)
        left = math.floor((bounds[0]+bounds[2]-side)/2)
        top = math.floor((bounds[1]+bounds[3]-side)/2)
    crop = (left, top, left+side, top+side)
    rgba = image.convert("RGBA")
    rgba.putalpha(alpha)
    rgba = rgba.crop(crop).resize((size, size), Image.Resampling.LANCZOS)
    rgb = Image.new("RGB", rgba.size)
    rgb.paste(rgba, mask=rgba.getchannel("A"))
    scale = size/side
    return rgb, rgba, {
        "bounding_box_xyxy": list(bounds), "crop_box_xyxy": list(crop),
        "original_size": [w, h], "size": [size, size], "padding": padding,
        "preserve_frame": preserve_frame,
        "source_to_prepared": [scale, 0, -left*scale, 0, scale, -top*scale],
        "clipped_silhouette": bounds[0] <= 1 or bounds[1] <= 1 or bounds[2] >= w-1 or bounds[3] >= h-1,
    }


def create(library, asset_id, slot, revision_id, mask, *, origin, feather=0):
    asset = library.load(asset_id)
    revision = library.revision(asset, slot)
    if revision["id"] != revision_id:
        raise ValueError("The image changed. Open background removal again.")
    source_path = library.path(asset_id, revision["file"])
    if digest(source_path) != revision["sha256"]:
        raise ValueError("The source image changed on disk. Import it again.")
    if not 0 <= feather <= 32:
        raise ValueError("Edge softness must be between 0 and 32 pixels.")
    with Image.open(source_path) as source:
        if source.width*source.height > 40_000_000 or source.size != mask.size:
            raise ValueError("The foreground mask must match the source and be below 40 megapixels.")
        alpha = mask.convert("L")
        if feather:
            alpha = ImageChops.multiply(alpha, alpha.filter(ImageFilter.GaussianBlur(feather)))
        # Validate without using the framed result: saved cutout remains in source coordinates.
        _, _, metadata = frame(source, alpha, size=8, preserve_frame=True)
        cutout = source.convert("RGBA")
        cutout.putalpha(alpha)
    key = uuid.uuid4().hex[:16]
    base = f"foreground/{identifier(slot)}/{key}"
    alpha_file, cutout_file = base + "/alpha.png", base + "/cutout.png"
    directory = library.path(asset_id, base)
    directory.mkdir(parents=True, exist_ok=False)
    alpha.save(library.path(asset_id, alpha_file))
    cutout.save(library.path(asset_id, cutout_file))
    record = {"id": key, "slot": slot, "source_revision": revision_id,
              "source_sha256": revision["sha256"], "mask_file": alpha_file,
              "mask_sha256": digest(library.path(asset_id, alpha_file)),
              "cutout_file": cutout_file, "cutout_sha256": digest(library.path(asset_id, cutout_file)),
              "origin": origin, "feather": feather, "created": time.time(),
              "clipped_silhouette": metadata["clipped_silhouette"],
              "bounding_box_xyxy": metadata["bounding_box_xyxy"], "reviewed": origin == "manual"}
    atomic_json(directory / "foreground.json", record)
    return record


def validate(library, asset_id, revision, record):
    if record["source_revision"] != revision["id"] or record["source_sha256"] != revision["sha256"]:
        raise ValueError("The foreground belongs to a different image revision.")
    if digest(library.path(asset_id, revision["file"])) != revision["sha256"]:
        raise ValueError("The source image changed on disk. Import it again.")
    for file_key, hash_key in (("mask_file", "mask_sha256"), ("cutout_file", "cutout_sha256")):
        if digest(library.path(asset_id, record[file_key])) != record[hash_key]:
            raise ValueError("A saved foreground file changed. Review background removal again.")


def accept(library, asset_id, slot, candidate_id):
    path = library.path(asset_id, f"foreground/{identifier(slot)}/{identifier(candidate_id)}/foreground.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    with LOCK:
        asset = library.load(asset_id)
        revision = library.revision(asset, slot)
        if revision["id"] != record["source_revision"]:
            raise ValueError("The image changed while the cutout was open. Its original files are retained.")
        validate(library, asset_id, revision, record)
        if revision.get("foreground", {}).get("id") == record["id"]:
            return asset
        revision["foreground"] = record
        if asset.get("schema_version") == 2:
            library._stale_project_artifacts(asset, slot)
            return library.save(asset)
        # The front card and multiview front are aliases of the same original image.
        if slot in ("design", "view_01"):
            counterpart = library.slot(asset, "view_01" if slot == "design" else "design")
            for alias in counterpart["revisions"]:
                if alias["id"] == revision["id"]:
                    alias["foreground"] = record
        invalidate_mesh(asset)
        return library.save(asset)
