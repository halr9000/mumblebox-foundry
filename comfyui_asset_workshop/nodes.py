"""Disk boundaries around native Comfy image and reconstruction operations."""

import json
import math
import os
import time
import uuid
import copy
import struct
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image, PngImagePlugin
from safetensors.torch import load_file, save_file

from comfy_api.latest import IO, Types
from comfy_extras.nodes_trellis2 import _orbit_camera_to_world
from comfy_extras.nodes_bg_removal import RemoveBackground

from .runtime import store
from .store import LOCK, atomic_json, digest, identifier
from . import image_edits, foreground, camera_guides, pixal_conditioning, recipes


def strings(*names):
    return [IO.String.Input(name) for name in names]


def save_png(tensor, path, metadata=None):
    if tensor.shape[0] != 1:
        raise ValueError("One asset revision must contain exactly one image.")
    array = (tensor[0].detach().cpu().clamp(0, 1).numpy() * 255).round().astype(np.uint8)
    if array.ndim == 3 and array.shape[-1] == 1:
        array = array[:, :, 0]
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngImagePlugin.PngInfo()
    if metadata:
        info.add_text("asset_workshop", json.dumps(metadata))
    temporary = path.with_suffix(".part")
    Image.fromarray(array).save(temporary, format="PNG", pnginfo=info)
    os.replace(temporary, path)


class ModelBudget(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_ModelBudget", display_name="Additional sampler VRAM headroom",
            category="Asset Workshop",
            inputs=[IO.Model.Input("model"), IO.Float.Input("extra_gb", default=0, min=0, max=12, step=.5)],
            outputs=[IO.Model.Output()],
        )

    @classmethod
    def execute(cls, model, extra_gb):
        result = model.clone()
        required = result.memory_required
        # Per-clone estimate only. No process-wide memory or startup settings change.
        result.memory_required = lambda input_shape: required(input_shape) + int(extra_gb * 1024**3)
        return IO.NodeOutput(result)


class PrepareView(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_PrepareView", display_name="Mask, frame and save reconstruction view",
            category="Asset Workshop",
            inputs=[IO.Image.Input("image"), IO.Mask.Input("alpha_mask"),
                    IO.BackgroundRemoval.Input("bg_removal_model", optional=True),
                    *strings("asset_id", "slot", "revision_id"),
                    IO.Float.Input("padding", default=1.1, min=1, max=2),
                    IO.String.Input("foreground_id", default="", optional=True),
                    IO.Boolean.Input("preserve_frame", default=False, optional=True)],
            outputs=[IO.Image.Output(), IO.String.Output(display_name="prepared path")],
        )

    @classmethod
    def execute(cls, image, alpha_mask, asset_id, slot, revision_id, padding,
                bg_removal_model=None, foreground_id="", preserve_frame=False):
        if image.shape[0] != 1:
            raise ValueError("Prepare one view per card.")
        library = store()
        revision = library.revision(library.load(asset_id), slot)
        if revision["id"] != revision_id:
            raise ValueError("The image changed after preparation was queued. Prepare the current image again.")
        record = revision.get("foreground")
        if foreground_id and (not record or record["id"] != foreground_id):
            raise ValueError("The foreground changed after preparation was queued. Prepare it again.")
        if not record:
            # LoadImage MASK is inverted alpha; BiRefNet returns object-white alpha.
            existing_alpha = bool((alpha_mask > .95).float().mean() >= .001)
            if not existing_alpha and bg_removal_model is None:
                raise ValueError("A background-removal model is required for this image's first cutout.")
            mask = 1 - alpha_mask if existing_alpha else RemoveBackground.execute(bg_removal_model, image)[0]
            alpha = Image.fromarray((mask[0].detach().cpu().clamp(0, 1).numpy()*255).round().astype(np.uint8))
            record = foreground.create(library, asset_id, slot, revision_id, alpha,
                                       origin="source_alpha" if existing_alpha else "birefnet")
            foreground.accept(library, asset_id, slot, record["id"])
        foreground.validate(library, asset_id, revision, record)
        with Image.open(library.path(asset_id, revision["file"])) as source:
            with Image.open(library.path(asset_id, record["mask_file"])) as alpha:
                rgb, _, metadata = foreground.frame(source, alpha, padding, preserve_frame=preserve_frame)
        prepared = torch.from_numpy(np.array(rgb).astype(np.float32)/255).unsqueeze(0)
        relative = f"prepared/{identifier(slot)}/{identifier(revision_id)}-{record['id']}-pad{padding:g}-frame{int(preserve_frame)}.png"
        metadata.update(slot=slot, revision=revision_id, foreground=record,
                        alpha_preserved=record["origin"] == "source_alpha")
        save_png(prepared, library.path(asset_id, relative), metadata)
        atomic_json(library.path(asset_id, relative + ".json"), metadata)
        return IO.NodeOutput(prepared, relative)


class FinishPreparation(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_FinishPreparation", display_name="Save prepared-view checkpoint",
            category="Asset Workshop", is_output_node=True,
            inputs=[*strings("asset_id", "job_id"),
                    IO.Autogrow.Input("paths", template=IO.Autogrow.TemplatePrefix(
                        IO.String.Input("path", force_input=True), prefix="view", min=1, max=100))],
            outputs=[],
        )

    @classmethod
    def execute(cls, asset_id, job_id, paths):
        store().complete_job(asset_id, job_id, {"prepared": list(paths.values())})
        return IO.NodeOutput(ui={"asset_workshop": [{"prepared": list(paths.values())}]})


class AssetScale(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_ScaleMesh", display_name="Set meters and ground-center pivot",
            category="Asset Workshop",
            inputs=[IO.Mesh.Input("mesh"), IO.Float.Input("height_meters", default=1, min=.001, max=100000)],
            outputs=[IO.Mesh.Output()],
        )

    @classmethod
    def execute(cls, mesh, height_meters):
        result = copy.copy(mesh)
        count = int(mesh.vertex_counts[0]) if mesh.vertex_counts is not None else mesh.vertices.shape[1]
        vertices = mesh.vertices[:, :count]
        low, high = vertices.amin(dim=1, keepdim=True), vertices.amax(dim=1, keepdim=True)
        height = high[:, :, 1] - low[:, :, 1]
        if bool((height < 1e-8).any()):
            raise ValueError("Cannot scale a mesh with zero height.")
        pivot = (low + high) * .5
        pivot[:, :, 1] = low[:, :, 1]
        result.vertices = (mesh.vertices - pivot) * (height_meters / height).unsqueeze(-1)
        return IO.NodeOutput(result)


class AssetImage(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_SaveImage", display_name="Save asset image revision",
            category="Asset Workshop", is_output_node=True,
            inputs=[IO.Image.Input("image"), *strings("asset_id", "slot", "job_id", "recipe"),
                    IO.Autogrow.Input("lora_reports", template=IO.Autogrow.TemplatePrefix(
                        IO.String.Input("report", force_input=True), prefix="lora", min=0, max=100), optional=True)],
            outputs=[IO.Image.Output()],
        )

    @classmethod
    def execute(cls, image, asset_id, slot, job_id, recipe, lora_reports=None):
        library = store()
        details = json.loads(recipe)
        if lora_reports:
            details["lora_validation"] = [json.loads(value) for value in lora_reports.values()]
        if details.get("edit"):
            if image.shape[0] != 1:
                raise ValueError("An image edit must produce exactly one preview.")
            array = (image[0].detach().cpu().clamp(0, 1).numpy() * 255).round().astype(np.uint8)
            result, revision = image_edits.save_candidate(
                library, asset_id, slot, job_id, Image.fromarray(array), details)
            preview = torch.from_numpy(np.array(result.convert("RGB"), dtype=np.float32) / 255).unsqueeze(0)
            return IO.NodeOutput(preview, ui={"asset_workshop": [revision]})
        revision_id = uuid.uuid4().hex[:16]
        relative = f"images/{identifier(slot)}/{revision_id}.png"
        path = library.path(asset_id, relative)
        save_png(image, path, details)
        revision = {"id": revision_id, "file": relative, "sha256": digest(path),
                    "created": time.time(), "recipe": details}
        library.add_revision(asset_id, slot, revision)
        library.complete_job(asset_id, job_id, {"slot": slot, "revision": revision_id})
        return IO.NodeOutput(image, ui={"asset_workshop": [revision]})


class LoadAssetImage(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_LoadImage", display_name="Load saved asset image",
            category="Asset Workshop", inputs=[*strings("asset_id", "relative_path"),
                IO.String.Input("expected_sha256", default="", optional=True)],
            outputs=[IO.Image.Output(), IO.Mask.Output()],
        )

    @classmethod
    def execute(cls, asset_id, relative_path, expected_sha256=""):
        path = store().path(asset_id, relative_path)
        if expected_sha256 and digest(path) != expected_sha256:
            raise ValueError("The queued source image changed. Import and approve it again before generating.")
        with Image.open(path) as source:
            image = source.convert("RGBA")
            rgba = torch.from_numpy(np.asarray(image, dtype=np.float32).copy() / 255)[None]
        return IO.NodeOutput(rgba[..., :3], 1 - rgba[..., 3])

    @classmethod
    def fingerprint_inputs(cls, asset_id, relative_path, expected_sha256=""):
        return digest(store().path(asset_id, relative_path))


class SDXLCheckpoint(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(node_id="AW_LoadSDXLCheckpoint", display_name="Load local SDXL checkpoint, text encoders and VAE",
            category="Asset Workshop", inputs=[IO.Combo.Input("checkpoint_name", options=recipes.checkpoint_names())],
            outputs=[IO.Model.Output(), IO.Clip.Output(), IO.Vae.Output()])

    @classmethod
    def execute(cls, checkpoint_name):
        import folder_paths
        import comfy.sd
        root = Path(folder_paths.base_path).resolve() / "models"
        path = (root / "checkpoints" / checkpoint_name).resolve()
        if not path.is_relative_to(root / "checkpoints") or not path.is_file():
            raise ValueError("Download this SDXL checkpoint into this Comfy installation before generating.")
        model, clip, vae, *_ = comfy.sd.load_checkpoint_guess_config(str(path), output_vae=True, output_clip=True,
            embedding_directory=[str(root / "embeddings")])
        return IO.NodeOutput(model, clip, vae)


class SDXLModelLoRA(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        import folder_paths
        return IO.Schema(node_id="AW_LoadSDXLLoRA", display_name="Load SDXL model and text-encoder LoRA",
            category="Asset Workshop", inputs=[IO.Model.Input("model"), IO.Clip.Input("clip"),
                IO.Combo.Input("lora_name", options=folder_paths.get_filename_list("loras")),
                IO.Float.Input("strength_model", default=1, min=-2, max=2, step=.05),
                IO.Float.Input("strength_clip", default=1, min=-2, max=2, step=.05)],
            outputs=[IO.Model.Output(), IO.Clip.Output(), IO.String.Output(display_name="LoRA validation")])

    @classmethod
    def execute(cls, model, clip, lora_name, strength_model, strength_clip):
        import comfy.utils
        from .lora_compatibility import load_checked_sdxl
        if not (strength_model or strength_clip):
            return IO.NodeOutput(model, clip, json.dumps({"name": lora_name, "status": "disabled"}))
        path = recipes.local_lora(lora_name)
        weights, metadata = comfy.utils.load_torch_file(path, safe_load=True, return_metadata=True)
        report = {}
        result, text = load_checked_sdxl(model, clip, weights, strength_model, strength_clip, metadata, report)
        report.update(name=lora_name, sha256=digest(path), strength=strength_model, strength_clip=strength_clip)
        return IO.NodeOutput(result, text, json.dumps(report))


class VerifiedModelLoRA(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        import folder_paths
        return IO.Schema(
            node_id="AW_LoadModelLoRA", display_name="Load compatible image-model LoRA",
            category="Asset Workshop",
            inputs=[IO.Model.Input("model"),
                    IO.Combo.Input("lora_name", options=folder_paths.get_filename_list("loras")),
                    IO.Float.Input("strength_model", default=1, min=-100, max=100, step=.01)],
            outputs=[IO.Model.Output(), IO.String.Output(display_name="LoRA validation")],
        )

    @classmethod
    def execute(cls, model, lora_name, strength_model):
        import folder_paths
        import comfy.utils
        from .lora_compatibility import load_checked
        if strength_model == 0:
            return IO.NodeOutput(model, json.dumps({"name": lora_name, "status": "disabled"}))
        path = recipes.local_lora(lora_name)
        weights, metadata = comfy.utils.load_torch_file(path, safe_load=True, return_metadata=True)
        report = {}
        result = load_checked(model, weights, strength_model, metadata, report=report)
        report.update(name=lora_name, sha256=digest(path), strength=strength_model)
        return IO.NodeOutput(result, json.dumps(report))


MESH_TENSORS = ("vertices", "faces", "uvs", "vertex_colors", "texture",
                "metallic_roughness", "vertex_counts", "face_counts",
                "normals", "tangents", "normal_map", "emissive")


class SourceFOV(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(node_id="AW_RecordSourceFOV", display_name="Record source camera perspective",
            category="Asset Workshop", inputs=[IO.Float.Input("fov",force_input=True),
            *strings("asset_id","job_id"),IO.Combo.Input("mode",options=["manual","auto","guide"])],
            outputs=[IO.Float.Output()])

    @classmethod
    def execute(cls,fov,asset_id,job_id,mode):
        value=float(fov)
        if not math.isfinite(value) or not 1<=value<=170:
            raise ValueError("Source FOV must be between 1 and 170 degrees. Try a manual value for this image.")
        atomic_json(store().path(asset_id,f"jobs/{identifier(job_id)}-camera.json"),
                    {"horizontal_degrees":value,"mode":mode,"estimator":"MoGe-2" if mode=="auto" else None,
                     "frame":"prepared image","object_angle_measured":False})
        return IO.NodeOutput(value)


def camera_record(library,asset_id,details):
    camera=details.get("source_camera")
    if camera and camera.get("record"):
        camera.update(json.loads(library.path(asset_id,camera["record"]).read_text(encoding="utf-8")))
    return details


class AssetDraft(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_SaveDraft", display_name="Save draft mesh for camera guides",
            category="Asset Workshop", is_output_node=True,
            inputs=[IO.Mesh.Input("mesh"), IO.File3DGLB.Input("model_3d"),
                    *strings("asset_id", "job_id", "recipe"),
                    IO.Autogrow.Input("paths", template=IO.Autogrow.TemplatePrefix(
                        IO.String.Input("path", force_input=True), prefix="view", min=1, max=100))],
            outputs=[IO.File3DGLB.Output()],
        )

    @classmethod
    def execute(cls, mesh, model_3d, asset_id, job_id, recipe, paths):
        if mesh.vertices.shape[0] != 1 or not bool(torch.isfinite(mesh.vertices).all()):
            raise ValueError("The draft must contain one finite mesh.")
        library = store()
        details = camera_record(library,asset_id,json.loads(recipe))
        prepared = [json.loads(library.path(asset_id, path+".json").read_text(encoding="utf-8")) for path in paths.values()]
        for source in details["dependencies"]["inputs"]:
            metadata = next(item for item in prepared if item["revision"] == source["revision"])
            mask = metadata["foreground"]
            if mask["source_sha256"] != source["sha256"]:
                raise ValueError("The draft input changed during preparation. Rebuild it from the current images.")
            source.update(foreground=mask["id"], mask_sha256=mask["mask_sha256"])
        draft_id = uuid.uuid4().hex[:16]
        base = f"drafts/{draft_id}"
        folder = library.path(asset_id, base)
        folder.mkdir(parents=True, exist_ok=False)
        target = folder / "draft.glb"
        temporary = folder / "draft.part"
        model_3d.save_to(str(temporary))
        os.replace(temporary, target)
        with target.open("rb") as stream:
            magic, version, length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2 or length != target.stat().st_size:
            raise ValueError("The draft GLB failed its format check.")
        record = {"id":draft_id, "file":f"{base}/draft.glb", "sha256":digest(target),
                  "created":time.time(), "recipe":details, "dependencies":details["dependencies"],
                  "prepared":prepared, "appearance":details["appearance"], "resolution":512,
                  "triangles":int(mesh.face_counts[0]) if mesh.face_counts is not None else int(mesh.faces.shape[1]),
                  "bounds_min":mesh.vertices.amin(dim=1)[0].detach().cpu().tolist(),
                  "bounds_max":mesh.vertices.amax(dim=1)[0].detach().cpu().tolist(),
                  "up_axis":"Y", "stale":False, "approved":False}
        atomic_json(folder / "draft.json", record)
        with LOCK:
            asset = library.load(asset_id)
            asset["drafts"].append(record)
            library.save(asset)
        library.complete_job(asset_id, job_id, {"draft":draft_id})
        return IO.NodeOutput(Types.File3D(str(target), "glb"), ui={"asset_workshop":[{"draft":draft_id}]})


class LoadAssetDraft(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(node_id="AW_LoadDraft", display_name="Load approved draft mesh",
                         category="Asset Workshop", inputs=strings("asset_id", "draft_id"),
                         outputs=[IO.File3DGLB.Output()])

    @classmethod
    def execute(cls, asset_id, draft_id):
        library = store()
        asset = library.load(asset_id)
        draft = next(item for item in asset["drafts"] if item["id"] == draft_id)
        if draft.get("stale") or not draft.get("approved"):
            raise ValueError("Review and approve a current draft before rendering camera guides.")
        path = library.path(asset_id, draft["file"])
        if digest(path) != draft["sha256"]:
            raise ValueError("The draft changed on disk. Build and review it again.")
        return IO.NodeOutput(Types.File3D(str(path), "glb"))


class AssetGuide(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(node_id="AW_SaveGuide", display_name="Save camera guide images",
            category="Asset Workshop", is_output_node=True,
            inputs=[*strings("asset_id", "job_id", "recipe"), IO.Image.Input("depth"),
                    IO.Image.Input("normal"), IO.Mask.Input("mask"), IO.Image.Input("color", optional=True)],
            outputs=[])

    @classmethod
    def execute(cls, asset_id, job_id, recipe, depth, normal, mask, color=None):
        details = json.loads(recipe)
        if mask.shape != (1,1024,1024) or not bool((mask > .5).any()):
            raise ValueError("The guide camera did not see the draft. Check its shape and camera settings.")
        if not bool(torch.isfinite(depth).all()) or not bool(torch.isfinite(normal).all()):
            raise ValueError("The guide renderer produced invalid pixels.")
        guide_id = uuid.uuid4().hex[:16]
        library = store()
        base = f"guides/{guide_id}"
        maps = {"depth":depth, "normal":normal, "silhouette":mask[...,None]}
        if color is not None:
            maps["color"] = color
        files = {}
        for kind, tensor in maps.items():
            path = library.path(asset_id, f"{base}/{kind}.png")
            save_png(tensor, path, details)
            files[kind] = {"file":f"{base}/{kind}.png", "sha256":digest(path)}
        record = {"id":guide_id, **details, "files":files, "created":time.time(), "stale":False}
        with LOCK:
            asset = library.load(asset_id)
            draft = next(d for d in asset["drafts"] if d["id"] == details["draft"])
            if draft.get("stale") or not draft.get("approved") or draft["sha256"] != details["draft_sha256"]:
                raise ValueError("The approved draft changed during rendering. Render fresh guides.")
            asset["guides"].append(record)
            library.save(asset)
        atomic_json(library.path(asset_id, f"{base}/guide.json"), record)
        library.complete_job(asset_id, job_id, {"guide":guide_id})
        return IO.NodeOutput(ui={"asset_workshop":[{"guide":guide_id}]})


class AssetMaster(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_SaveMaster", display_name="Checkpoint raw mesh and native voxel data",
            category="Asset Workshop", is_output_node=True,
            inputs=[IO.Mesh.Input("mesh"), IO.Voxel.Input("voxel"),
                    *strings("asset_id", "job_id", "recipe")],
            outputs=[IO.Mesh.Output(), IO.Voxel.Output()],
        )

    @classmethod
    def execute(cls, mesh, voxel, asset_id, job_id, recipe):
        if mesh.vertices.shape[0] != 1:
            raise ValueError("Checkpoint one asset at a time.")
        library = store()
        master_id = uuid.uuid4().hex[:16]
        folder = library.path(asset_id, f"masters/{master_id}")
        folder.mkdir(parents=True, exist_ok=False)
        fields = {}
        # Each native field is saved separately to avoid a second full CPU copy.
        for name in MESH_TENSORS:
            value = getattr(mesh, name, None)
            if isinstance(value, torch.Tensor):
                filename = f"mesh_{name}.safetensors"
                save_file({"value": value.detach().cpu().contiguous()}, str(folder / filename))
                fields[name] = filename
        voxel_fields = {}
        for name in ("data", "voxel_colors"):
            value = getattr(voxel, name, None)
            if isinstance(value, torch.Tensor):
                filename = f"voxel_{name}.safetensors"
                save_file({"value": value.detach().cpu().contiguous()}, str(folder / filename))
                voxel_fields[name] = filename
        record = {
            "schema": 1, "id": master_id, "created": time.time(), "mesh": fields,
            "voxel": voxel_fields, "resolution": voxel.resolution,
            "unlit": mesh.unlit, "occlusion_in_mr": mesh.occlusion_in_mr,
            "recipe": camera_record(library,asset_id,json.loads(recipe)), "stale": False, "approved": False,
            "hashes": {p.name: digest(p) for p in folder.glob("*.safetensors")},
            "bounds_min": mesh.vertices.amin(dim=1)[0].detach().cpu().tolist(),
            "bounds_max": mesh.vertices.amax(dim=1)[0].detach().cpu().tolist(),
            "vertices": int(mesh.vertex_counts[0]) if mesh.vertex_counts is not None else int(mesh.vertices.shape[1]),
            "triangles": int(mesh.face_counts[0]) if mesh.face_counts is not None else int(mesh.faces.shape[1]),
        }
        atomic_json(folder / "checkpoint.json", record)
        with LOCK:
            data = library.load(asset_id)
            saved = {**record, "file": f"masters/{master_id}/checkpoint.json"}
            if data.get("schema_version") == 2:
                saved.update(kind="master", sha256=digest(folder / "checkpoint.json"), stage_id=job_id,
                             source_revision_ids=[item["revision"]["id"] for item in record["recipe"]["inputs"]])
                job = next(j for j in data["jobs"] if any(s["id"] == job_id for s in j["stages"]))
                saved["job_id"] = job["id"]
                saved["stale"] = data["images"]["mesh_input"]["approved"] not in saved["source_revision_ids"]
                data["artifacts"].append(saved)
                job["artifacts"].append(master_id)
            else:
                data["masters"].append(saved)
            library.save(data)
        library.complete_job(asset_id, job_id, {"master": master_id})
        return IO.NodeOutput(mesh, voxel, ui={"asset_workshop": [{"master": master_id}]})


class LoadAssetMaster(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_LoadMaster", display_name="Resume saved native master",
            category="Asset Workshop", inputs=strings("asset_id", "master_id"),
            outputs=[IO.Mesh.Output(), IO.Voxel.Output()],
        )

    @classmethod
    def execute(cls, asset_id, master_id):
        library = store()
        base = f"masters/{identifier(master_id)}"
        record = json.loads(library.path(asset_id, f"{base}/checkpoint.json").read_text())

        def read(filename):
            path = library.path(asset_id, f"{base}/{filename}")
            if digest(path) != record["hashes"][filename]:
                raise ValueError(f"Checkpoint integrity check failed: {filename}")
            return load_file(str(path), device="cpu")["value"]

        mesh = Types.MESH(**{k: read(v) for k, v in record["mesh"].items()},
                          unlit=record.get("unlit", False),
                          occlusion_in_mr=record.get("occlusion_in_mr", False))
        voxel = Types.VOXEL(**{k: read(v) for k, v in record["voxel"].items()},
                            resolution=record["resolution"])
        return IO.NodeOutput(mesh, voxel)


class AssetExport(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_Export", display_name="Save separate GLB and PBR textures",
            category="Asset Workshop", is_output_node=True,
            inputs=[IO.File3DGLB.Input("model_3d"), IO.Mesh.Input("mesh"),
                    *strings("asset_id", "master_id", "job_id"),
                    IO.Combo.Input("kind", options=["master", "game"]),
                    IO.Image.Input("metallic", optional=True),
                    IO.Image.Input("roughness", optional=True),
                    IO.Image.Input("ao", optional=True)],
            outputs=[IO.File3DGLB.Output()],
        )

    @classmethod
    def execute(cls, model_3d, mesh, asset_id, master_id, job_id, kind,
                metallic=None, roughness=None, ao=None):
        if kind not in ("master", "game"):
            raise ValueError("Unknown export kind.")
        library = store()
        export_id = uuid.uuid4().hex[:16]
        base = f"exports/{kind}/{export_id}"
        folder = library.path(asset_id, base)
        folder.mkdir(parents=True, exist_ok=False)
        target = folder / f"{kind}.glb"
        temporary = folder / "model.part"
        model_3d.save_to(str(temporary))
        os.replace(temporary, target)
        with target.open("rb") as stream:
            magic, version, length = struct.unpack("<4sII", stream.read(12))
        if magic != b"glTF" or version != 2 or length != target.stat().st_size:
            raise ValueError("The exported file failed its GLB header/length check.")
        if mesh.uvs is None or mesh.texture is None or not bool(torch.isfinite(mesh.vertices).all()):
            raise ValueError("The textured export is missing UVs/texture or contains non-finite vertices.")
        maps = {"base_color": mesh.texture, "normal_opengl": mesh.normal_map,
                "metallic": metallic, "roughness": roughness, "occlusion": ao}
        for name, tensor in maps.items():
            if tensor is not None:
                save_png(tensor, folder / f"{name}.png")
        faces = int(mesh.face_counts[0]) if mesh.face_counts is not None else int(mesh.faces.shape[1])
        record = {"id": export_id, "kind": kind, "master": identifier(master_id),
                  "created": time.time(), "file": f"{base}/{kind}.glb", "triangles": faces,
                  "hashes": {p.name: digest(p) for p in folder.iterdir() if p.is_file()},
                  "normal_convention": "OpenGL +Y", "up_axis": "Y",
                  "unit": "meter", "pivot": "ground center"}
        record["dimensions_meters"] = (mesh.vertices.amax(dim=1) - mesh.vertices.amin(dim=1))[0].detach().cpu().tolist()
        if kind == "master":
            vertex_count = int(mesh.vertex_counts[0]) if mesh.vertex_counts is not None else mesh.vertices.shape[1]
            print_mesh = trimesh.Trimesh(
                vertices=mesh.vertices[0, :vertex_count].detach().cpu().numpy(),
                faces=mesh.faces[0, :faces].detach().cpu().numpy(), process=False)
            # Print files use millimeters and Z-up; the textured GLB remains meters/Y-up.
            print_mesh.apply_transform(np.array([[1000, 0, 0, 0], [0, 0, -1000, 0],
                                                 [0, 1000, 0, 0], [0, 0, 0, 1]]))
            print_mesh.merge_vertices(digits_vertex=8)
            print_mesh.export(str(folder / "print-mm.stl"), file_type="stl")
            record["print"] = {
                "file": f"{base}/print-mm.stl", "unit": "millimeter", "up_axis": "Z",
                "dimensions_mm": print_mesh.extents.tolist(),
                "watertight": bool(print_mesh.is_watertight),
                "winding_consistent": bool(print_mesh.is_winding_consistent),
                "solid_volume": bool(print_mesh.is_volume),
                "components": int(print_mesh.body_count),
                "degenerate_faces": int((~print_mesh.nondegenerate_faces()).sum()),
                "unchecked": ["wall thickness", "self-intersections", "printer/material tolerances", "supports"],
            }
            record["hashes"]["print-mm.stl"] = digest(folder / "print-mm.stl")
        recipe_file = library.cache / identifier(job_id) / "recipe.json"
        if recipe_file.is_file():
            record["recipe"] = json.loads(recipe_file.read_text(encoding="utf-8"))
        project = library.load(asset_id)
        if project.get("schema_version") == 2:
            stage = next(s for job in project["jobs"] for s in job["stages"] if s["id"] == job_id)
            record["recipe"] = json.loads(library.path(asset_id, stage["graph_file"]).read_text(encoding="utf-8"))["details"]
        atomic_json(folder / "export.json", record)
        with LOCK:
            data = library.load(asset_id)
            if data.get("schema_version") == 2:
                master = next(a for a in data["artifacts"] if a["id"] == master_id)
                job = next(j for j in data["jobs"] if any(s["id"] == job_id for s in j["stages"]))
                record.update(export_kind=kind, kind="mesh", job_id=job["id"],
                              source_revision_ids=master["source_revision_ids"],
                              stale=master["stale"], sha256=digest(target))
                data["artifacts"].append(record)
                job["artifacts"].append(export_id)
            else:
                data["exports"].append(record)
            library.save(data)
        library.complete_job(asset_id, job_id, {"export": export_id})
        return IO.NodeOutput(Types.File3D(str(target), "glb"), ui={"asset_workshop": [record]})


class PixalViewSet(IO.ComfyNode):
    @classmethod
    def define_schema(cls):
        return IO.Schema(
            node_id="AW_PixalViews", display_name="Pixal3D — every approved camera view",
            category="Asset Workshop",
            description="All connected views condition one asset. Generated camera values remain estimates.",
            inputs=[IO.ClipVision.Input("clip_vision_model"),
                    IO.String.Input("cameras", multiline=True),
                    IO.Combo.Input("scope", options=["full", "geometry_draft", "color_draft"], default="full", optional=True),
                    IO.Autogrow.Input("images", template=IO.Autogrow.TemplatePrefix(
                        IO.Image.Input("image"), prefix="view", min=1, max=100))],
            outputs=[IO.Conditioning.Output(display_name="positive"),
                     IO.Conditioning.Output(display_name="negative")],
        )

    @classmethod
    def execute(cls, clip_vision_model, cameras, images, scope="full"):
        poses = json.loads(cameras)
        if not poses or len(poses) != len(images):
            raise ValueError("Every connected image must have one matching camera record.")
        ordered, matrices, fovs = [], [], []
        for index, pose in enumerate(poses):
            image = images[f"view{index}"]
            if image.shape[0] != 1 or tuple(image.shape[1:3]) != (1024, 1024):
                raise ValueError("Prepare each view as one 1024-square image before conditioning.")
            fov = float(pose["fov"])
            azimuth, elevation = float(pose["azimuth"]), float(pose["elevation"])
            if not all(math.isfinite(x) for x in (fov, azimuth, elevation)) or not 1 < fov < 170 or not -90 <= elevation <= 90:
                raise ValueError("Invalid camera angles.")
            fov = math.radians(fov)
            # UI orbit: front=0/right=90. Native Pixal rig: front=0/left=90.
            matrix = (torch.tensor([camera_guides.pixal_camera(pose["requested_camera"])], dtype=torch.float32)
                      if pose.get("requested_camera") else
                      _orbit_camera_to_world([(360 - azimuth) % 360], [elevation], 1.1 * 0.5 / math.tan(fov / 2)))
            matrices.append(matrix)
            fovs.append(fov)
            ordered.append(image[..., :3] if image.shape[-1] == 3 else image[..., :3] * image[..., 3:4])
        return pixal_conditioning.build_conditioning(
            clip_vision_model, torch.cat(ordered), torch.cat(matrices),
            torch.tensor(fovs), torch.ones(1), num_views=len(poses), scope=scope)
