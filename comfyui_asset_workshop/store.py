"""Asset revisions and job-owned storage. No model tensors are retained here."""

import hashlib
import copy
import json
import math
import os
import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import TypedDict

LOCK = threading.RLock()
ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")

IMAGE_ROLES = ("source", "design", "mesh_input", "reference_front", "reference_back",
               "reference_left", "reference_right")
REVIEW_DECISIONS = ("unreviewed", "approved", "approved_with_notes", "rejected")
PROFILE_IDS = ("qwen21", "qwen2511", "klein_base", "klein_distilled", "klein_kv",
               "klein4", "klein4_base", "flux3_base", "flux3_distilled", "sdxl_base", "sdxl_juggernaut")


class ProjectConflict(ValueError):
    pass


class ApprovalRequired(ValueError):
    pass


class CapabilityError(ValueError):
    pass


class JobConflict(ValueError):
    pass


class Approval(TypedDict):
    image_revision_id: str
    sha256: str
    decision: str
    reviewer: str
    notes: str
    timestamp: float
    camera_verification: str


class ImageRevision(TypedDict, total=False):
    id: str
    file: str
    sha256: str
    recipe: dict
    review: Approval
    requested_view: str


class Artifact(TypedDict, total=False):
    id: str
    kind: str
    file: str
    sha256: str
    source_revision_ids: list[str]
    job_id: str
    stale: bool


class Job(TypedDict, total=False):
    id: str
    project_id: str
    request_key: str
    snapshot: dict
    kind: str
    state: str
    phase: str
    prompt_ids: list[str]
    artifacts: list[str]
    attempts: int
    error: dict | None
    release_receipts: list[dict]


class Package(Artifact, total=False):
    manifest: dict


class Project(TypedDict, total=False):
    schema_version: int
    id: str
    revision: int
    images: dict[str, dict]
    sources: list[dict]
    settings: dict
    jobs: list[Job]
    artifacts: list[Artifact]
    memory_preset_id: str
    preset_overrides: list[str]


def identifier(value):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError("Use letters, numbers, underscores or hyphens for asset and revision IDs.")
    return value


def contained(root, *parts):
    root = Path(root).resolve()
    result = root.joinpath(*parts).resolve()
    if not result.is_relative_to(root) or result == root:
        raise ValueError("The requested path is outside this asset folder.")
    return result


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".part")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        # Windows readers/indexers can briefly deny replacement even after our
        # own write handle closes. Retry only sharing/access locks, boundedly;
        # never truncate the existing manifest as a fallback.
        for attempt in range(8):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as error:
                if getattr(error, "winerror", None) not in (5, 32, 33) or attempt == 7:
                    raise
                time.sleep(min(.02 * 2**attempt, .32))
    finally:
        temporary.unlink(missing_ok=True)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def description_context(data):
    inputs = {key:data.get(key) for key in ("prompt", "profile", "references")}
    inputs.update(category=data.get("category", "props"), initial=data.get("initial", {}).get("current"))
    return hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def default_views():
    names = ["Front", "Front right", "Right", "Rear right", "Back",
             "Rear left", "Left", "Front left", "Upper front", "Lower rear"]
    views = []
    for index, name in enumerate(names):
        views.append({
            "id": f"view_{index + 1:02}", "name": name, "enabled": True,
            "azimuth": index * 45 if index < 8 else (0 if index == 8 else 180),
            "elevation": 0 if index < 8 else (60 if index == 8 else -30),
            "camera_source": "generated_estimate", "fov": 20,
            "correction": "", "current": None, "approved": None, "revisions": [],
        })
    return views


def invalidate_mesh(data):
    """Retire results for changed reconstruction inputs without deleting files."""
    for result in (*data["masters"], *data["exports"]):
        result["stale"] = True
    data["selected_export"] = None
    data["selected_master"] = None


def reset_angles(data):
    """A new design starts a new angle set; revision files remain in History."""
    data["pair_approval"] = None
    for view in data["views"]:
        view.update(current=None, approved=None, enabled=False, stale=False, correction="", seed=None)
    invalidate_mesh(data)


def invalidate_pair(data):
    data["pair_approval"] = None
    for view in data["views"]:
        if view["id"] not in ("view_01", "view_05"):
            view["stale"] = True
            view["approved"] = None
    invalidate_mesh(data)


def pair_approved(data):
    front = data["design"]
    back = next((v for v in data["views"] if v["id"] == "view_05"), {})
    front_view = next((v for v in data["views"] if v["id"] == "view_01"), {})
    back_revision = next((r for r in back.get("revisions", []) if r["id"] == back.get("current")), {})
    pair = {"front": front.get("current"), "back": back.get("current")}
    return bool(all(pair.values()) and data.get("pair_approval") == pair
                and front.get("approved") == pair["front"] and back.get("approved") == pair["back"]
                and front_view.get("current") == pair["front"]
                and back_revision.get("front_revision") == pair["front"]
                and (back.get("azimuth"), back.get("elevation")) == (180, 0)
                and not front.get("stale") and not back.get("stale"))


def draft_inputs(data):
    """Draft sources, independent of later angle attempts and their seeds."""
    backend = data["settings"].get("draft_backend", "pixal_multiview")
    inputs = []
    slots = [("design", data["design"])]
    if backend == "pixal_multiview":
        sources = data["settings"].get("draft_source_views", ["view_01", "view_05"])
        slots = [("design", data["design"]) if source == "view_01" else
                 (source, next(v for v in data["views"] if v["id"] == source)) for source in sources]
    for slot_id, slot in slots:
        revision = next((r for r in slot.get("revisions", []) if r["id"] == slot.get("current")), {})
        mask = revision.get("foreground", {})
        pose = next((v for v in data["views"] if v["id"] == ("view_01" if slot_id == "design" else slot_id)), {})
        inputs.append({"slot": slot_id, "revision": revision.get("id"), "sha256": revision.get("sha256"),
                       "foreground": mask.get("id"), "mask_sha256": mask.get("mask_sha256"),
                       "pose": {key: pose.get(key) for key in ("azimuth", "elevation", "fov")}})
    return {"backend": backend, "inputs": inputs,
            **({"source_fov":{"mode":data["settings"].get("mesh_fov_mode","manual"),
                              "value":data["settings"].get("mesh_fov",49.13)}} if backend=="pixal_single" else {}),
            "approved": pair_approved(data) if backend == "pixal_multiview" else bool(data["design"].get("current") and not data["design"].get("stale"))}


def refresh_guidance(data):
    """Retire only guidance derived from changed references or camera positions."""
    drafts = data.setdefault("drafts", [])
    guides = data.setdefault("guides", [])
    expected = draft_inputs(data)
    for draft in drafts:
        if draft.get("dependencies") != expected:
            draft.update(stale=True, approved=False)
    available = {draft["id"] for draft in drafts if not draft.get("stale")}
    if data.get("selected_draft") not in available:
        data["selected_draft"] = None
    poses = {view["id"]: {key:view.get(key) for key in ("azimuth", "elevation", "fov")} for view in data["views"]}
    stale = set()
    for guide in guides:
        if guide["draft"] not in available or guide.get("pose") != poses.get(guide["slot"]):
            guide["stale"] = True
        if guide.get("stale"):
            stale.add(guide["id"])
    for view in data["views"]:
        revision = next((r for r in view.get("revisions", []) if r["id"] == view.get("current")), {})
        if revision.get("recipe", {}).get("guide") in stale and not view.get("stale"):
            view.update(stale=True, approved=None)
            invalidate_mesh(data)


def bounded_number(value, minimum, maximum, name, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    if value < minimum or value > maximum or (integer and int(value) != value):
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return int(value) if integer else value


MESH_DEFAULTS = {
    "mesh_structure_steps":12, "mesh_structure_cfg":7.5,
    "mesh_shape_steps":20, "mesh_shape_cfg":7.5,
    "mesh_refine_steps":12, "mesh_refine_cfg":7.5,
    "mesh_material_steps":12, "mesh_material_cfg":1.0,
    "mesh_requested_seed":-1, "mesh_fov":49.13, "mesh_fov_mode":"manual",
}


def default_settings():
    return {
        **MESH_DEFAULTS,
        "resolution": 1024, "seed": 0, "requested_seed": -1, "steps": None, "cfg": None,
        "cache_device": "cpu", "cache_precision": "default", "tiled_vae": True,
        "shape_resolution": 1536, "mesh_backend": "pixal_multiview",
        "game_faces": 100000, "master_faces": 700000,
        "master_texture": 4096, "game_texture": 2048,
        "normal_resolution": 2048, "ao_resolution": 1024,
        "remesh": True, "smoothing": 0, "crease_angle": 45,
        "uv_method": "pec", "extra_vram_headroom_gb": 0,
        "min_ram_free_gb": 8, "min_vram_free_gb": 1.5,
        "cache_limit_gb": 20, "unit": "meter", "asset_height": 1.0,
        "camera_lora": False, "image_precision": "native", "bake_ao": True, "bake_normal": True,
        "seed_mode": "randomize", "helper_precision": "q8", "include_design": True,
        "memory_overrides": [], "release_between_stages": True,
        "draft_backend": "pixal_multiview", "draft_appearance": "geometry", "draft_seed": 0,
        "angle_profile": "same", "angle_route": "references", "angle_steps": None,
        "angle_cfg": None, "guide_strength": 1, "angle_camera_lora": False,
        "image_checkpoint": "",
        "sdxl_negative_prompt": "collage, contact sheet, grid, multiple panels, multiple views, repeated objects", "sdxl_sampler": "dpmpp_2m", "sdxl_scheduler": "karras",
        "sdxl_source_mode": "reference", "sdxl_reference_strength": .8,
        "sdxl_img2img_denoise": .65, "sdxl_edit_denoise": .85,
    }

SETTING_RANGES = {
    "sdxl_reference_strength": (-1, 5, False), "sdxl_img2img_denoise": (0, 1, False), "sdxl_edit_denoise": (0, 1, False),
    **{key: (1,150,True) if key.endswith("steps") else (0,30,False)
       for key in MESH_DEFAULTS if key.endswith(("steps","cfg"))},
    "mesh_requested_seed":(-1,2**53-16,True), "mesh_seed":(0,2**53-16,True),
    "mesh_fov":(1,170,False),
    "resolution": (256, 2048, True), "seed": (0, 2**53 - 1, True),
    "requested_seed": (-1, 2**53 - 1, True),
    "steps": (1, 150, True), "cfg": (.1, 30, False), "shape_resolution": (1024, 2048, True),
    "game_faces": (100, 50000000, True), "master_faces": (0, 50000000, True),
    "master_texture": (64, 8192, True), "game_texture": (64, 8192, True),
    "normal_resolution": (64, 8192, True), "ao_resolution": (64, 8192, True),
    "smoothing": (0, 20, True), "crease_angle": (0, 180, False),
    "extra_vram_headroom_gb": (0, 12, False), "min_ram_free_gb": (1, 128, False),
    "min_vram_free_gb": (0, 24, False), "cache_limit_gb": (1, 500, False),
    "asset_height": (.001, 100000, False),
    "draft_seed": (0, 2**53 - 1, True),
    "angle_steps": (1, 150, True), "angle_cfg": (.1, 30, False), "guide_strength": (0, 2, False),
}
SETTING_CHOICES = {
    "sdxl_sampler": ("dpmpp_2m", "dpmpp_2m_sde", "euler", "euler_ancestral", "heun"),
    "sdxl_scheduler": ("karras", "normal", "exponential", "simple"),
    "sdxl_source_mode": ("reference", "img2img"),
    "mesh_fov_mode":("manual","auto"),
    "cache_device": ("cpu", "gpu", "auto", "off"),
    "cache_precision": ("default", "int8", "int4"),
    "mesh_backend": ("pixal_multiview", "pixal_single", "trellis2"),
    "uv_method": ("adaptive", "pec"), "unit": ("meter",),
    "image_precision": ("native", "bf16"),
    "seed_mode": ("randomize", "fixed", "increment", "decrement"),
    "helper_precision": ("q8", "q4"),
    "draft_backend": ("pixal_multiview", "pixal_single", "trellis2"),
    "draft_appearance": ("geometry", "color"),
    "angle_route": ("references", "klein_depth", "qwen_anyangle", "qwen_edit_depth"),
    "angle_profile": ("same", "qwen21", "qwen2511", "klein4", "klein4_base", "klein_base",
                      "klein_distilled", "klein_kv", "flux3_base", "flux3_distilled"),
}


class AssetStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.assets = self.root / "assets"
        self.cache = self.root / "work-cache"

    def directory(self, asset_id):
        return contained(self.assets, identifier(asset_id))

    def path(self, asset_id, relative):
        return contained(self.directory(asset_id), relative)

    def load(self, asset_id):
        with self.path(asset_id, "asset.json").open(encoding="utf-8") as stream:
            data = json.load(stream)
        if data.get("schema_version") == 2:
            return data
        data.setdefault("drafts", [])
        data.setdefault("guides", [])
        data.setdefault("selected_draft", None)
        data.setdefault("category", "props")
        data["settings"].setdefault("bake_normal", True)
        for key,value in MESH_DEFAULTS.items():
            data["settings"].setdefault(key,value)
        return data

    def save(self, data):
        if data.get("schema_version") == 2:
            data["revision"] += 1
        else:
            refresh_guidance(data)
        data["updated"] = time.time()
        atomic_json(self.path(data["id"], "asset.json"), data)
        return data

    def create(self, name):
        asset_id = uuid.uuid4().hex[:12]
        return self.save({
            "schema": 1, "id": asset_id, "name": str(name)[:160],
            "created": time.time(), "updated": time.time(), "prompt": "", "tags": [],
            "profile": "qwen21", "category": "props", "references": [], "loras": [],
            "views": default_views(),
            "design": {"current": None, "approved": None, "revisions": []},
            "initial": {"current": None, "approved": None, "revisions": []},
            "masters": [], "exports": [], "jobs": [],
            "settings": default_settings(),
        })

    def create_project(self) -> Project:
        settings = {key: value for key, value in default_settings().items()
                    if not key.startswith(("draft_", "angle_", "guide_")) and key != "include_design"}
        settings.update(mesh_backend="pixal_single", mesh_fov_mode="auto", remesh=False, extra_vram_headroom_gb=1)
        with LOCK:
            return self.save({
                "schema_version": 2, "id": uuid.uuid4().hex[:12], "revision": 0,
                "name": "New asset", "created": time.time(), "updated": time.time(),
                "prompt": "", "category": "props", "tags": [], "profile": "klein4", "loras": [],
                "sources": [], "images": {role: {"current": None, "approved": None, "revisions": []}
                                           for role in IMAGE_ROLES},
                "settings": settings, "design_notes": "", "jobs": [], "artifacts": [],
                "memory_preset_id": "standard_16gb", "preset_overrides": [],
                "target": {"intended_use": "game", "requested_dimensions_m": {},
                           "scale_axis": "height", "user_instructions": ""},
            })

    def update_pipeline(self, project_id, expected_revision, changes):
        state_module = _pipeline_contracts()
        checked = state_module.validate_settings(changes)
        with LOCK:
            data = self._checked_project(project_id, expected_revision)
            state = state_module.initialize(data)
            state["settings"].update(checked)
            return self.save(data)

    def select_pipeline_artifact(self, project_id, expected_revision, artifact_id):
        with LOCK:
            data = self._checked_project(project_id, expected_revision)
            row = next((r for r in data["artifacts"] if r["id"] == identifier(artifact_id)), None)
            if not row or row.get("stale") or row.get("kind") not in ("geometry", "mesh"):
                raise ValueError("Choose a current geometry or appearance from this project")
            path = self.path(project_id, row["file"])
            if not path.is_file() or digest(path) != row["sha256"]:
                raise ValueError("The recorded pipeline artifact changed on disk")
            state = _pipeline_contracts().initialize(data)
            state["selected_geometry_id" if row["kind"] == "geometry" else "selected_appearance_id"] = row["id"]
            if row["kind"] == "geometry":
                previous=next((a for a in data["artifacts"] if a["id"]==state.get("selected_appearance_id")),None)
                if previous and previous.get("geometry_id")!=row["id"]:
                    state.update(selected_texture_id=None,selected_appearance_id=None)
            elif row.get("geometry_id"):
                state["selected_geometry_id"]=row["geometry_id"]
                ancestor=row;seen=set()
                while ancestor and ancestor["id"] not in seen:
                    seen.add(ancestor["id"])
                    if ancestor.get("appearance_stage")=="texture":state["selected_texture_id"]=ancestor["id"];break
                    ancestor=next((a for a in data["artifacts"] if a["id"]==ancestor.get("parent_artifact_id")),None)
            return self.save(data)

    def record_pipeline_artifact(self, project_id, stage_id, record):
        with LOCK:
            data = self._checked_project(project_id)
            found = [(j,s) for j in data["jobs"] for s in j["stages"] if s["id"] == identifier(stage_id)]
            if len(found) != 1: raise ValueError("Output must belong to one recorded pipeline stage")
            job,stage = found[0]
            if job.get("cancel_requested") or job["state"] not in ("queued", "running"):
                raise JobConflict("This pipeline job no longer owns a running stage")
            row = copy.deepcopy(record)
            identifier(row["id"])
            if row.get("kind") not in ("geometry","mesh"): raise ValueError("Unsupported pipeline artifact")
            path = self.path(project_id, row["file"])
            if not path.is_file() or digest(path) != row.get("sha256"):
                raise ValueError("Pipeline output hash did not verify")
            for parent_key in ("parent_artifact_id","geometry_id"):
                parent_id = row.get(parent_key)
                if parent_id:
                    parent = next((a for a in data["artifacts"] if a["id"] == parent_id), None)
                    if not parent or parent.get("stale"):
                        raise ValueError("Pipeline parent is missing, stale or belongs to another project")
                    parent_path = self.path(project_id, parent["file"])
                    if not parent_path.is_file() or digest(parent_path) != parent["sha256"]:
                        raise ValueError("Pipeline parent changed on disk")
            existing = next((a for a in data["artifacts"] if a["id"] == row["id"]),None)
            if existing:
                if existing["sha256"] != row["sha256"]: raise ValueError("Immutable artifact identity conflict")
                return copy.deepcopy(existing)
            approved = job["snapshot"]["images"]["mesh_input"]["approved"]
            row.update(job_id=job["id"],stage_id=stage_id,pipeline_version="validated_v1",
                       source_revision_ids=[approved],stale=data["images"]["mesh_input"]["approved"]!=approved)
            data["artifacts"].append(row);job["artifacts"].append(row["id"])
            key="geometry" if row["kind"]=="geometry" else "appearance"
            stage["result"]={**stage.get("result",{}),key:row["id"]}
            if not row["stale"]:
                state=_pipeline_contracts().initialize(data)
                state["selected_geometry_id" if key=="geometry" else "selected_appearance_id"]=row["id"]
                if key=="geometry":state.update(selected_texture_id=None,selected_appearance_id=None)
                if row.get("appearance_stage")=="texture":state["selected_texture_id"]=row["id"]
            self.save(data)
            return copy.deepcopy(row)

    def _checked_project(self, project_id, expected_revision=None):
        data = self.load(project_id)
        if data.get("schema_version") != 2:
            raise ValueError("Use Reuse parameters to create a new single-image project.")
        if expected_revision is not None and data["revision"] != expected_revision:
            raise ProjectConflict("This project changed. Review the latest version before continuing.")
        return data

    @staticmethod
    def _stale_project_artifacts(data, role):
        if role in ("source", "design"):
            return
        for artifact in data["artifacts"]:
            if role == "mesh_input" or artifact["kind"] == "package":
                artifact["stale"] = True

    def update_project(self, project_id: str, expected_revision: int, changes: dict) -> Project:
        allowed = {"name", "prompt", "category", "tags", "profile", "loras", "settings",
                   "design_notes", "target", "source_selection", "source_details", "memory_preset_id", "preset_overrides"}
        if not isinstance(changes, dict) or changes.keys() - allowed:
            raise ValueError("Unknown project setting; jobs and approvals use their own actions.")
        with LOCK:
            data = self._checked_project(project_id, expected_revision)
            package_context = copy.deepcopy([data["prompt"], data["design_notes"], data["target"]])
            for key, limit in (("name", 160), ("prompt", 32000), ("design_notes", 32000)):
                if key in changes:
                    if not isinstance(changes[key], str) or len(changes[key]) > limit:
                        raise ValueError(f"{key} must be text no longer than {limit} characters.")
                    data[key] = changes[key]
            if "profile" in changes:
                if changes["profile"] not in PROFILE_IDS:
                    raise ValueError("Choose a supported image model.")
                if data["profile"] != changes["profile"]:
                    data["settings"]["image_checkpoint"] = ""
                data["profile"] = changes["profile"]
            if "category" in changes:
                if changes["category"] not in ("props", "characters", "creatures", "vehicles", "environment"):
                    raise ValueError("Choose a supported asset type.")
                data["category"] = changes["category"]
            if "tags" in changes:
                if not isinstance(changes["tags"], list) or any(not isinstance(t, str) for t in changes["tags"]):
                    raise ValueError("Tags must be a list of text values.")
                data["tags"] = [t[:80] for t in changes["tags"][:50]]
            for key, value in changes.get("settings", {}).items():
                if key not in data["settings"] and key not in default_settings():
                    raise ValueError(f"Unknown single-image setting: {key}.")
                if key == "mesh_backend" and value != "pixal_single":
                    raise ValueError("This workflow uses one image and Pixal3D.")
                if key == "release_between_stages" and value is not True:
                    raise ValueError("Model unloading between heavy stages is required.")
                if key in SETTING_RANGES:
                    low, high, integer = SETTING_RANGES[key]
                    data["settings"][key] = None if value is None and key in ("steps", "cfg") else bounded_number(value, low, high, key, integer)
                elif key in SETTING_CHOICES:
                    if value not in SETTING_CHOICES[key]:
                        raise ValueError(f"Unknown {key} choice.")
                    data["settings"][key] = value
                elif key == "image_checkpoint":
                    if not isinstance(value, str) or value and (not value.isdigit() or len(value) > 12):
                        raise ValueError("Choose an installed checkpoint or the official model.")
                    data["settings"][key] = value
                elif key == "sdxl_negative_prompt":
                    if not isinstance(value, str) or len(value) > 16000:
                        raise ValueError("The negative prompt must be text no longer than 16000 characters.")
                    data["settings"][key] = value
                elif isinstance(data["settings"].get(key), bool):
                    if not isinstance(value, bool):
                        raise ValueError(f"{key} must be true or false.")
                    data["settings"][key] = value
                elif key == "memory_overrides":
                    if not isinstance(value, list) or any(k not in data["settings"] for k in value):
                        raise ValueError("Choose existing memory settings to override.")
                    data["settings"][key] = list(dict.fromkeys(value))
            if "loras" in changes:
                checked = []
                for item in changes["loras"]:
                    name = str(item.get("name", ""))
                    if Path(name).is_absolute() or ".." in Path(name).parts:
                        raise ValueError("Choose a LoRA in Comfy's registered folders.")
                    checked.append({"name": name, "profile": str(item.get("profile", "")),
                                    "strength": bounded_number(item.get("strength", 1), -2, 2, "LoRA strength"),
                                    "strength_clip": bounded_number(item.get("strength_clip", item.get("strength", 1)), -2, 2, "LoRA text strength"),
                                    "enabled": bool(item.get("enabled", True)), "trigger": str(item.get("trigger", ""))[:8000]})
                data["loras"] = checked
            if "target" in changes:
                target = changes["target"]
                if not isinstance(target, dict) or target.keys() - data["target"].keys():
                    raise ValueError("Unknown target property.")
                if target.get("scale_axis", "height") != "height":
                    raise ValueError("Use uniform scaling by height; dimensions are design instructions.")
                dimensions = target.get("requested_dimensions_m", data["target"]["requested_dimensions_m"])
                if not isinstance(dimensions, dict) or dimensions.keys() - {"width", "height", "depth"}:
                    raise ValueError("Dimensions use width, height and depth in meters.")
                for name, value in dimensions.items():
                    bounded_number(value, .000001, 1000000, name)
                if any(not isinstance(target[key], str) or len(target[key]) > 32000
                       for key in target if key != "requested_dimensions_m"):
                    raise ValueError("Target instructions must be text.")
                data["target"].update(copy.deepcopy(target))
            if "source_selection" in changes:
                selected = changes["source_selection"]
                known = {source["id"] for source in data["sources"]}
                if not isinstance(selected, list) or any(v not in known for v in selected):
                    raise ValueError("Choose uploaded source image IDs.")
                for source in data["sources"]:
                    source["enabled"] = source["id"] in selected
                    if source["enabled"]:
                        source.pop("cleared", None)
                if selected and data["images"]["source"]["current"] is None:
                    data["images"]["source"]["current"] = selected[-1]
            if "source_details" in changes:
                details = changes["source_details"]
                known = {source["id"]: source for source in data["sources"]}
                if not isinstance(details, dict) or details.keys() - known.keys():
                    raise ValueError("Choose existing source image IDs.")
                for source_id, values in details.items():
                    if not isinstance(values, dict) or values.keys() - {"role", "instructions"}:
                        raise ValueError("Source descriptions use a role and instructions.")
                    if any(not isinstance(v, str) or len(v) > 8000 for v in values.values()):
                        raise ValueError("Reference instructions must be text below 8000 characters.")
                    known[source_id].update(values)
            if "memory_preset_id" in changes:
                if changes["memory_preset_id"] not in ("standard_16gb", "experimental_8gb", "custom"):
                    raise ValueError("Unknown memory preset.")
                data["memory_preset_id"] = changes["memory_preset_id"]
            if "preset_overrides" in changes:
                if not isinstance(changes["preset_overrides"], list) or any(k not in data["settings"] and k != "profile" for k in changes["preset_overrides"]):
                    raise ValueError("Unknown preset override.")
                data["preset_overrides"] = list(dict.fromkeys(changes["preset_overrides"]))
            if package_context != [data["prompt"], data["design_notes"], data["target"]]:
                for artifact in data["artifacts"]:
                    if artifact["kind"] == "package":
                        artifact["stale"] = True
            return self.save(data)

    def approve_image(self, project_id: str, role: str, image_revision_id: str, sha256: str,
                      decision: str, reviewer: str, notes: str, expected_revision: int) -> Project:
        if decision not in REVIEW_DECISIONS or reviewer not in ("user", "agent"):
            raise ValueError("Choose a supported review decision and reviewer.")
        if not isinstance(notes, str) or len(notes) > 32000:
            raise ValueError("Review notes must be text no longer than 32000 characters.")
        with LOCK:
            data = self._checked_project(project_id, expected_revision)
            slot = self.slot(data, role)
            record = next((r for r in slot["revisions"] if r["id"] == image_revision_id), None)
            if record is None or record["sha256"] != sha256:
                raise ApprovalRequired("The image revision or hash changed; review the current image.")
            path = self.path(project_id, record["file"])
            if not path.is_file() or digest(path) != sha256:
                raise ApprovalRequired("The image file changed; import it as a new revision.")
            accepted = decision in ("approved", "approved_with_notes")
            if slot["current"] != image_revision_id or not accepted:
                self._stale_project_artifacts(data, role)
            slot.update(current=image_revision_id, approved=image_revision_id if accepted else None)
            record["review"] = {"image_revision_id": image_revision_id, "sha256": sha256,
                                "decision": decision, "reviewer": reviewer, "notes": notes,
                                "timestamp": time.time(), "camera_verification": "not_measured"}
            return self.save(data)

    def clear_images(self, project_id, expected_revision, role=None, revision_id=None):
        with LOCK:
            project = self._checked_project(project_id, expected_revision)
            if any(job["state"] in ("queued", "running") for job in project["jobs"]):
                raise JobConflict("Stop the current job before clearing its images.")
            roles = IMAGE_ROLES if role is None else (role,)
            for name in roles:
                slot = self.slot(project, name)
                if name == "source":
                    for source in project["sources"]:
                        if revision_id is None or source["id"] == revision_id:
                            source["enabled"] = False
                            source["cleared"] = True
                if revision_id is None or slot["current"] == revision_id:
                    slot.update(current=None, approved=None, stale=True)
                self._stale_project_artifacts(project, name)
            return self.save(project)

    def select_image(self, project_id, expected_revision, role, revision_id):
        with LOCK:
            project = self._checked_project(project_id, expected_revision)
            slot = self.slot(project, role)
            record = next((r for r in slot["revisions"] if r["id"] == revision_id), None)
            if record is None or digest(self.path(project_id, record["file"])) != record["sha256"]:
                raise ApprovalRequired("Choose an unchanged image from this project.")
            if slot["current"] != revision_id:
                slot.update(current=revision_id, approved=None, stale=False)
                self._stale_project_artifacts(project, role)
            return self.save(project)

    def adopt_image(self, project_id, expected_revision, source_role, revision_id, role):
        with LOCK:
            project = self._checked_project(project_id, expected_revision)
            self.slot(project, role)
            record = next((r for r in self.slot(project, source_role)["revisions"] if r["id"] == revision_id), None)
            if record is None or digest(self.path(project_id, record["file"])) != record["sha256"]:
                raise ApprovalRequired("Choose an unchanged image from this project.")
            adopted = copy.deepcopy(record)
            adopted.update(id=uuid.uuid4().hex[:16], created=time.time(),
                           adopted_from={"role": source_role, "revision_id": revision_id})
            adopted.pop("review", None)
            return self.add_revision(project_id, role, adopted)

    def mesh_input(self, project_id: str) -> ImageRevision:
        with LOCK:
            data = self._checked_project(project_id)
            slot = data["images"]["mesh_input"]
            record = next((r for r in slot["revisions"] if r["id"] == slot["approved"] == slot["current"]), None)
            if record is None or record["review"]["decision"] not in ("approved", "approved_with_notes"):
                raise ApprovalRequired("Approve one image for the mesh first.")
            path = self.path(project_id, record["file"])
            if not path.is_file() or digest(path) != record["sha256"]:
                raise ApprovalRequired("The approved image changed; import and approve it again.")
            return copy.deepcopy(record)

    def job_snapshot(self, project_id: str, expected_revision: int) -> dict:
        with LOCK:
            project = self._checked_project(project_id, expected_revision)
            result = {key: copy.deepcopy(value) for key, value in project.items() if key not in ("jobs", "images")}
            selected = {r["id"] for r in project["sources"] if r.get("enabled", True)}
            result["images"] = {}
            for role, slot in project["images"].items():
                needed = {slot["current"], slot["approved"]} | (selected if role == "source" else set())
                result["images"][role] = {**copy.deepcopy(slot), "revisions":
                    [copy.deepcopy(r) for r in slot["revisions"] if r["id"] in needed]}
            result["jobs"] = []
            return result

    def reuse_parameters(self, project_id: str, include_images: bool = False) -> Project:
        with LOCK:
            previous = self.load(project_id)
            result = self.create_project()
            for key in ("name", "prompt", "profile", "category", "tags", "loras", "design_notes", "target"):
                if key in previous:
                    result[key] = copy.deepcopy(previous[key])
            result["settings"].update({key: copy.deepcopy(value) for key, value in previous["settings"].items()
                                       if key in result["settings"]})
            result["settings"].update(mesh_backend="pixal_single", release_between_stages=True, uv_method="pec")
            result["reused_from"] = project_id
            self.save(result)
            if include_images:
                roles = previous.get("images", {"design": previous.get("design", {}),
                                                 "source": previous.get("initial", {})})
                for role, slot in roles.items():
                    if role not in IMAGE_ROLES:
                        continue
                    selected = slot.get("current")
                    originals = slot.get("revisions", [])
                    for record in originals if role == "source" else [r for r in originals if r["id"] == selected]:
                        source = self.path(project_id, record["file"])
                        relative = f"originals/{identifier(record['id'])}{source.suffix}"
                        destination = self.path(result["id"], relative)
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, destination)
                        copied = {**copy.deepcopy(record), "file": relative, "sha256": digest(destination),
                                  "reused_from": {"project": project_id, "revision": record["id"]}}
                        result = self.add_revision(result["id"], role, copied)
            return self.load(result["id"])

    def update(self, asset_id, patch):
        with LOCK:
            data = self.load(asset_id)
            previous_settings = data["settings"].copy()
            previous_back = next((v.copy() for v in data["views"] if v["id"] == "view_05"), {})
            # Generator controls apply to the next attempt. They do not change
            # the content of reviewed images or revoke approval of those files.
            before = json.dumps({k: data[k] for k in ("prompt", "references")}, sort_keys=True)
            if "view_selection" in patch:
                selection = patch["view_selection"]
                known = {view["id"]: view for view in data["views"]}
                if (not isinstance(selection, dict) or len(selection) > len(known)
                        or any(key not in known or not isinstance(value, bool)
                               for key, value in selection.items())):
                    raise ValueError("Choose existing angles with true or false selection values.")
                for view_id, enabled in selection.items():
                    if known[view_id]["enabled"] != enabled:
                        known[view_id]["enabled"] = enabled
                        invalidate_mesh(data)
            for key, length in (("name", 160), ("prompt", 32000)):
                if key in patch:
                    if not isinstance(patch[key], str) or len(patch[key]) > length:
                        raise ValueError(f"{key} is too long or is not text.")
                    data[key] = patch[key]
            if "category" in patch:
                if patch["category"] not in ("props", "characters", "creatures", "vehicles", "environment"):
                    raise ValueError("Choose a supported asset type.")
                data["category"] = patch["category"]
            provenance = data.get("prompt_provenance")
            if provenance and provenance.get("text_sha256") != hashlib.sha256(data["prompt"].encode()).hexdigest():
                data["prompt_provenance"] = None
            if "tags" in patch:
                values = patch["tags"].split(",") if isinstance(patch["tags"], str) else patch["tags"]
                data["tags"] = [str(tag).strip()[:80] for tag in values[:50] if str(tag).strip()]
            if "profile" in patch:
                if patch["profile"] not in ("qwen21", "qwen2511", "klein_base", "klein_distilled",
                                             "klein_kv", "klein4", "klein4_base", "flux3_base", "flux3_distilled"):
                    raise ValueError("Unknown image profile.")
                data["profile"] = patch["profile"]
            if "references" in patch:
                known = {ref["id"]: ref for ref in data["references"]}
                references = []
                for ref in patch["references"]:
                    if ref["id"] not in known:
                        raise ValueError("Upload the reference before adding it to the asset.")
                    current = known[ref["id"]].copy()
                    for key in ("role", "instructions"):
                        current[key] = str(ref.get(key, ""))[:8000]
                    current["enabled"] = bool(ref.get("enabled", True))
                    references.append(current)
                data["references"] = references
            if "loras" in patch:
                loras = []
                for item in patch["loras"]:
                    name = str(item.get("name", ""))
                    if Path(name).is_absolute() or ".." in Path(name).parts:
                        raise ValueError("Choose a LoRA inside Comfy's registered LoRA folders.")
                    loras.append({"name": name, "profile": str(item.get("profile", "")),
                                  "strength": bounded_number(item.get("strength", 1), -2, 2, "LoRA strength"),
                                  "trigger": str(item.get("trigger", ""))[:8000],
                                  "enabled": bool(item.get("enabled", True))})
                data["loras"] = loras
            if "views" in patch:
                if not 1 <= len(patch["views"]) <= 100:
                    raise ValueError("This view graph supports 1 to 100 cards.")
                existing = {view["id"]: view for view in data["views"]}
                views, seen = [], set()
                for view in patch["views"]:
                    view_id = identifier(view["id"])
                    if view_id in seen or view_id == "design":
                        raise ValueError("View IDs must be distinct.")
                    seen.add(view_id)
                    old = existing.get(view_id, {"id": view_id, "current": None, "approved": None,
                                                "revisions": [], "camera_source": "generated_estimate"})
                    current = old.copy()
                    current.update(name=str(view.get("name", view_id))[:160],
                                   enabled=bool(view.get("enabled", True)),
                                   correction=str(view.get("correction", ""))[:16000])
                    for key, low, high in (("azimuth", 0, 360), ("elevation", -90, 90), ("fov", 2, 169)):
                        value = bounded_number(view.get(key, 20 if key == "fov" else 0), low, high, key)
                        if key in old and value != old[key]:
                            current["stale"] = True
                            invalidate_mesh(data)
                        current[key] = value
                    if view.get("seed") is not None:
                        current["seed"] = bounded_number(view["seed"], 0, 2**53 - 1, "view seed", True)
                    else:
                        current["seed"] = None
                    requested = view.get("current")
                    if requested is not None:
                        if not any(r["id"] == requested for r in current["revisions"]):
                            raise ValueError("Unknown view revision.")
                        current["current"] = requested
                    elif "current" in view:
                        current["current"] = None
                        current["approved"] = None
                    if current.get("current") != old.get("current"):
                        invalidate_mesh(data)
                    views.append(current)
                if [(v["id"], v["enabled"]) for v in data["views"]] != [(v["id"], v["enabled"]) for v in views]:
                    invalidate_mesh(data)
                data["views"] = views
                back = next((v for v in views if v["id"] == "view_05"), {})
                if any(previous_back.get(k) != back.get(k) for k in ("current", "azimuth", "elevation")):
                    invalidate_pair(data)
            for slot_id in ("design", "initial"):
                target = data.setdefault(slot_id, {"current": None, "approved": None, "revisions": []})
                if slot_id not in patch or "current" not in patch[slot_id]:
                    continue
                requested = patch[slot_id]["current"]
                if requested is not None and not any(r["id"] == requested for r in target["revisions"]):
                    raise ValueError(f"Unknown {slot_id} revision.")
                if target["current"] != requested:
                    target["current"] = requested
                    if requested is None:
                        target["approved"] = None
                    if slot_id == "design":
                        reset_angles(data)
                    invalidate_mesh(data)
            if "settings" in patch:
                for key, value in patch["settings"].items():
                    if key in SETTING_RANGES:
                        if value is None and key in ("steps", "cfg", "angle_steps", "angle_cfg"):
                            data["settings"][key] = None
                        else:
                            low, high, integer = SETTING_RANGES[key]
                            data["settings"][key] = bounded_number(value, low, high, key, integer)
                    elif key in SETTING_CHOICES:
                        if value not in SETTING_CHOICES[key]:
                            raise ValueError(f"Unknown {key} choice.")
                        data["settings"][key] = value
                    elif key == "draft_source_views":
                        known = {view["id"] for view in data["views"]}
                        if not isinstance(value, list) or not value or any(not isinstance(v, str) or v not in known for v in value):
                            raise ValueError("Choose existing views for the draft sources.")
                        data["settings"][key] = list(dict.fromkeys(value))
                    elif key=="memory_overrides":
                        allowed={"extra_vram_headroom_gb","min_ram_free_gb","cache_device",
                                 "tiled_vae","image_precision","cache_precision","helper_precision",
                                 "release_between_stages"}
                        if not isinstance(value,list) or any(k not in allowed for k in value):
                            raise ValueError("Unknown memory override.")
                        data["settings"][key]=list(dict.fromkeys(value))
                    elif key in ("remesh", "tiled_vae", "camera_lora", "angle_camera_lora", "bake_ao", "bake_normal", "include_design", "release_between_stages"):
                        data["settings"][key] = bool(value)
            shared_export_keys = ("remesh", "smoothing", "crease_angle", "uv_method", "normal_resolution",
                                  "ao_resolution", "bake_ao", "bake_normal", "asset_height")
            for output in data["exports"]:
                relevant = (*shared_export_keys, f"{output['kind']}_faces", f"{output['kind']}_texture")
                if any(previous_settings.get(k) != data["settings"].get(k) for k in relevant):
                    output["stale"] = True
            after = json.dumps({k: data[k] for k in ("prompt", "references")}, sort_keys=True)
            if before != after:
                invalidate_pair(data)
                data["design"]["stale"] = True
                for view in data["views"]:
                    view["stale"] = True
            return self.save(data)

    def slot(self, data, slot):
        if data.get("schema_version") == 2:
            if slot not in IMAGE_ROLES:
                raise ValueError("Choose an existing image role.")
            return data["images"][slot]
        if slot in ("design", "initial"):
            return data.setdefault(slot, {"current": None, "approved": None, "revisions": []})
        return next(view for view in data["views"] if view["id"] == identifier(slot))

    def add_revision(self, asset_id, slot, revision, select=True):
        with LOCK:
            data = self.load(asset_id)
            target = self.slot(data, slot)
            if data.get("schema_version") == 2:
                identifier(revision["id"])
                path = self.path(asset_id, revision["file"])
                if not path.is_file() or digest(path) != revision["sha256"]:
                    raise ApprovalRequired("The image file is missing or changed; import it again.")
                if any(r["id"] == revision["id"] for r in target["revisions"]):
                    return data
                record = copy.deepcopy(revision)
                record["review"] = {"image_revision_id": record["id"], "sha256": record["sha256"],
                    "decision": "unreviewed", "reviewer": "user", "notes": "",
                    "timestamp": time.time(), "camera_verification": "not_measured"}
                target["revisions"].append(record)
                if slot == "source" and select:
                    data["sources"].append({**copy.deepcopy(record), "enabled": True})
                if select:
                    target.update(current=record["id"], approved=None, stale=False)
                    self._stale_project_artifacts(data, slot)
                return self.save(data)
            if slot == "view_05":
                revision = {**revision, "front_revision": data["design"].get("current")}
            existing = next((r for r in target["revisions"] if r["id"] == revision["id"]), None)
            if existing is None:
                target["revisions"].append(revision)
            if not select:
                return self.save(data)
            target["current"] = revision["id"]
            target["approved"] = None
            target["stale"] = False
            if slot == "design":
                reset_angles(data)
            elif slot != "initial":
                target["enabled"] = True
                if slot == "view_05":
                    invalidate_pair(data)
            invalidate_mesh(data)
            return self.save(data)

    def approve(self, asset_id, slot, revision_id):
        with LOCK:
            data = self.load(asset_id)
            target = self.slot(data, slot)
            revision = next(r for r in target["revisions"] if r["id"] == identifier(revision_id))
            if not self.path(asset_id, revision["file"]).is_file():
                raise ValueError("The image revision is missing.")
            if digest(self.path(asset_id, revision["file"])) != revision["sha256"]:
                raise ValueError("The image changed on disk; import it again as a new revision.")
            if slot == "design" and target["current"] != revision_id:
                reset_angles(data)
            elif slot == "view_05" and target["current"] != revision_id:
                invalidate_pair(data)
            elif target["current"] != revision_id:
                invalidate_mesh(data)
            target["current"] = revision_id
            target["approved"] = revision_id
            target["stale"] = False
            return self.save(data)

    def approve_pair(self, asset_id):
        with LOCK:
            data = self.load(asset_id)
            front = self.revision(data, "design")
            back = self.revision(data, "view_05")
            if back.get("front_revision") != front["id"]:
                raise ValueError("Generate the back from the current front before approving this pair.")
            for revision in (front, back):
                path = self.path(asset_id, revision["file"])
                if not path.is_file() or digest(path) != revision["sha256"]:
                    raise ValueError("A reference image is missing or changed. Upload it again before approval.")
            front_view = self.slot(data, "view_01")
            back_view = self.slot(data, "view_05")
            if (back_view["azimuth"], back_view["elevation"]) != (180, 0):
                raise ValueError("The back reference must use the straight-back camera at 180 degrees and zero elevation.")
            if not any(r["id"] == front["id"] for r in front_view["revisions"]):
                front_view["revisions"].append(front.copy())
            front_view.update(current=front["id"], approved=front["id"], stale=False,
                              enabled=True, azimuth=0, elevation=0)
            data["design"].update(approved=front["id"], stale=False)
            back_view.update(approved=back["id"], stale=False, enabled=True)
            data["pair_approval"] = {"front": front["id"], "back": back["id"]}
            return self.save(data)

    def revision(self, data, slot, approved=False):
        target = self.slot(data, slot)
        revision_id = target["approved"] if approved else target["current"]
        if not revision_id:
            raise ValueError(f"Approve an image for {slot} first." if approved else f"Generate {slot} first.")
        return next(r for r in target["revisions"] if r["id"] == revision_id)

    def list_assets(self):
        result = []
        if self.assets.is_dir():
            for directory in self.assets.iterdir():
                if directory.is_dir() and ID.fullmatch(directory.name):
                    path = self.path(directory.name, "asset.json")
                    if path.is_file():
                        data = self.load(directory.name)
                        entry={k: data[k] for k in ("id", "name", "updated")}
                        if data.get("schema_version") == 2:
                            slots = data["images"]
                            slot = next((slots[role] for role in ("mesh_input", "design", "source")
                                         if slots[role]["current"]), {})
                        else:
                            slot=data["design"] if data["design"].get("current") else data.get("initial",{})
                        preview=next((r for r in slot.get("revisions",[]) if r["id"]==slot.get("current")),None)
                        entry.update(thumbnail=preview["file"] if preview else None,
                                     profile=data["profile"],prompt=data["prompt"],
                                     seed=preview.get("recipe",{}).get("seed") if preview else None,
                                     schema_version=data.get("schema_version", 1),
                                     exports=len([a for a in data["artifacts"] if a["kind"] == "mesh"])
                                     if data.get("schema_version") == 2 else len(data["exports"]))
                        result.append(entry)
        return sorted(result, key=lambda entry: entry["updated"], reverse=True)

    def history(self, asset_id, offset=0, limit=12):
        data=self.load(asset_id)
        if data.get("schema_version") == 2:
            offset, limit = max(0, int(offset)), min(100, max(1, int(limit)))
            jobs = [j for j in reversed(data["jobs"]) if j["state"] in ("completed", "awaiting_review")]
            return {"entries": copy.deepcopy(jobs[offset:offset+limit]), "total": len(jobs),
                    "offset": offset, "limit": limit}
        jobs=[j for j in reversed(data["jobs"]) if j["status"]=="complete"]
        entries=[]
        for job in jobs[offset:offset+limit]:
            entry={k:job[k] for k in ("id","stage","created","status")}
            path=self.path(asset_id,f"jobs/{job['id']}.json")
            snapshot=json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
            saved=snapshot["asset"] if snapshot else data
            result=job.get("result",{})
            slot=result.get("slot")
            revision=None
            if slot:
                revision=next((r for r in self.slot(data,slot)["revisions"] if r["id"]==result.get("revision")),None)
            details=revision.get("recipe",{}) if revision else {}
            entry.update(profile=details.get("profile",saved["profile"]),prompt=details.get("edit",{}).get("prompt",saved["prompt"]),
                         image_edit=bool(details.get("edit")),
                         parameters=details or saved["settings"],
                         seed=details.get("seed",saved["settings"]["seed"]),
                         thumbnail=revision["file"] if revision else None,
                         can_restore=bool(snapshot),slot=slot,
                         parameters_file=f"jobs/{job['id']}.json" if snapshot else None)
            entries.append(entry)
        return {"entries":entries,"total":len(jobs),"offset":offset,"limit":limit}

    def restore_generation(self, asset_id, job_id):
        with LOCK:
            data=self.load(asset_id)
            job=next(j for j in data["jobs"] if j["id"]==identifier(job_id))
            if job["status"]!="complete":
                raise ValueError("Choose a completed generation from History.")
            snapshot=json.loads(self.path(asset_id,f"jobs/{job_id}.json").read_text(encoding="utf-8"))
            saved=snapshot["asset"]
            if saved["id"]!=data["id"]:
                raise ValueError("This generation belongs to a different asset.")
            for key in ("prompt","profile","settings","loras","references"):
                data[key]=saved[key]
            data["category"] = saved.get("category", "props")
            data["prompt_provenance"] = copy.deepcopy(saved.get("prompt_provenance"))
            data["pair_approval"] = saved.get("pair_approval")
            data["settings"]["requested_seed"]=data["settings"]["seed"]
            data["settings"]["seed_mode"]="fixed"
            # A restored run keeps its recorded memory settings rather than
            # adapting them to today's hardware until the user requests that.
            memory_keys=("extra_vram_headroom_gb","min_ram_free_gb","cache_device","tiled_vae",
                         "image_precision","cache_precision","helper_precision","release_between_stages")
            data["settings"]["memory_overrides"]=[key for key in memory_keys if key in data["settings"]]
            for slot in ("initial","design"):
                previous=saved.get(slot,{})
                current=data.setdefault(slot,{"revisions":[],"current":None,"approved":None})
                for key in ("current","approved","stale"):
                    if key in previous: current[key]=previous[key]
            existing={v["id"]:v for v in data["views"]}
            data["views"]=[{**old,"revisions":existing.get(old["id"],old)["revisions"]} for old in saved["views"]]
            # A foreground edit updates a revision's selected mask, not its
            # original pixels. Restore the mask from this job's snapshot too.
            for old_slot in (saved.get("initial",{}),saved["design"],*saved["views"]):
                for old_revision in old_slot.get("revisions",[]):
                    if old_revision["id"] not in (old_slot.get("current"),old_slot.get("approved")):
                        continue
                    for current_slot in (data["initial"],data["design"],*data["views"]):
                        for revision in current_slot["revisions"]:
                            if revision["id"]==old_revision["id"]:
                                if old_revision.get("foreground"):
                                    revision["foreground"]=copy.deepcopy(old_revision["foreground"])
                                else:
                                    revision.pop("foreground",None)
            # Restore which saved results matched those exact inputs. Keep newer
            # files in History, but do not present them as this restored run.
            for collection in ("masters", "exports", "drafts", "guides"):
                prior = {record["id"]: record for record in saved.get(collection, [])}
                for record in data[collection]:
                    record["stale"] = prior[record["id"]].get("stale", False) if record["id"] in prior else True
                    if collection=="drafts":
                        record["approved"]=prior.get(record["id"],{}).get("approved",False)
            result=job.get("result",{})
            data["selected_draft"]=result.get("draft") or saved.get("selected_draft")
            if result.get("draft"):
                draft=next(d for d in data["drafts"] if d["id"]==result["draft"])
                draft.update(stale=False,approved=False)
                # Automatic cutouts can be created after the pre-run snapshot.
                for prepared in draft.get("prepared",[]):
                    for current_slot in (data["design"],*data["views"]):
                        for revision in current_slot["revisions"]:
                            if revision["id"]==prepared["revision"]:
                                revision["foreground"]=copy.deepcopy(prepared["foreground"])
            if result.get("guide"):
                guide=next(g for g in data["guides"] if g["id"]==result["guide"])
                guide["stale"]=False
            if result.get("slot"):
                target=self.slot(data,result["slot"])
                revision=next(r for r in target["revisions"] if r["id"]==result["revision"])
                if not self.path(asset_id,revision["file"]).is_file():
                    raise ValueError("This generation's image is missing. Current work was not changed.")
                if result["slot"] == "design":
                    reset_angles(data)
                elif result["slot"] == "initial" and revision.get("recipe",{}).get("edit"):
                    data["design"].update(current=None,approved=None,stale=False)
                    reset_angles(data)
                else:
                    if result["slot"] == "view_05" and target.get("current") != revision["id"]:
                        invalidate_pair(data)
                    for output in (*data["masters"],*data["exports"]):
                        output["stale"]=True
                target.update(current=revision["id"],approved=revision["id"],stale=False)
                actual_seed=revision.get("recipe",{}).get("seed",data["settings"]["seed"])
                data["settings"].update(seed=actual_seed,requested_seed=actual_seed)
            for target in (data["initial"],data["design"],*data["views"]):
                for selected in (target.get("current"),target.get("approved")):
                    if not selected: continue
                    revision=next((r for r in target["revisions"] if r["id"]==selected),None)
                    if not revision or not self.path(asset_id,revision["file"]).is_file():
                        raise ValueError("An image used by this generation is missing. Current work was not changed.")
                    foreground=revision.get("foreground",{})
                    for kind in ("mask","cutout"):
                        if foreground.get(f"{kind}_file") and digest(self.path(asset_id,foreground[f"{kind}_file"])) != foreground.get(f"{kind}_sha256"):
                            raise ValueError("A saved foreground file changed. Current work was not changed.")
            if any(not self.path(asset_id,ref["file"]).is_file() for ref in data["references"]):
                raise ValueError("A reference used by this generation is missing. Current work was not changed.")
            data["selected_export"]=result.get("export")
            data["selected_master"]=result.get("master")
            if result.get("export"):
                output=next(e for e in data["exports"] if e["id"]==result["export"])
                if not self.path(asset_id,output["file"]).is_file():
                    raise ValueError("This exported file is missing. Current work was not changed.")
                output["stale"]=False
                data["selected_master"]=output["master"]
            if data["selected_master"]:
                master=next(m for m in data["masters"] if m["id"]==data["selected_master"])
                master["stale"]=False
            if data["selected_draft"]:
                draft=next(d for d in data["drafts"] if d["id"]==data["selected_draft"])
                if digest(self.path(asset_id,draft["file"]))!=draft["sha256"]:
                    raise ValueError("This draft file changed. Current work was not changed.")
            return self.save(data)

    def record_description(self, data, action, text, contract):
        record = {"id":uuid.uuid4().hex[:16], "action":action, "contract":contract,
                  "context":description_context(data), "profile":data["profile"],
                  "category":data.get("category", "props"), "original_prompt":data["prompt"],
                  "suggested":text, "created":time.time()}
        atomic_json(self.path(data["id"], f"descriptions/{record['id']}.json"), record)
        return record

    def accept_description(self, asset_id, suggestion_id, text):
        if not isinstance(text,str) or not text.strip() or len(text)>32000:
            raise ValueError("Enter a usable suggested description before accepting it.")
        path=self.path(asset_id,f"descriptions/{identifier(suggestion_id)}.json")
        with LOCK:
            data=self.load(asset_id)
            record=json.loads(path.read_text(encoding="utf-8"))
            if record["context"]!=description_context(data):
                raise ValueError("The model, asset type, description or references changed. Request a new suggestion for these inputs; your text is unchanged.")
            record.update(accepted=text.strip(), accepted_at=time.time())
            atomic_json(path,record)
            data=self.update(asset_id,{"prompt":text.strip()})
            data["prompt_provenance"]={"id":record["id"],"profile":record["profile"],
                "category":record["category"],"contract":record["contract"],
                "text_sha256":hashlib.sha256(text.strip().encode()).hexdigest()}
            return self.save(data)

    def trash_asset(self, asset_id):
        with LOCK:
            data=self.load(asset_id)
            source=self.directory(asset_id)
            if source.name!=asset_id or source.parent!=self.assets.resolve():
                raise ValueError("Asset folder ownership could not be verified.")
            trash_root=contained(self.root,"trash")
            trash_root.mkdir(parents=True,exist_ok=True)
            token=uuid.uuid4().hex
            destination=contained(trash_root,token)
            source.rename(destination)
            atomic_json(destination/"trash.json",{"owner":"mumblebox-creator","asset":asset_id,"name":data["name"],"deleted":time.time()})
            return {"token":token,"name":data["name"],"asset":asset_id}

    def undo_delete(self, token):
        with LOCK:
            trash_root=contained(self.root,"trash")
            source=contained(trash_root,identifier(token))
            if source.name!=token or source.parent!=trash_root:
                raise ValueError("Deleted asset folder ownership could not be verified.")
            marker=json.loads((source/"trash.json").read_text(encoding="utf-8"))
            if marker.get("owner")!="mumblebox-creator":
                raise ValueError("This folder is not a deleted Mumblebox asset.")
            target=self.directory(identifier(marker["asset"]))
            if target.exists(): raise ValueError("That asset already exists in History.")
            source.rename(target)
            (target/"trash.json").unlink()
            return self.load(marker["asset"])

    def clear_history(self, asset_ids):
        with LOCK:
            current = {entry["id"] for entry in self.list_assets()}
            if not isinstance(asset_ids, list) or set(asset_ids) != current:
                raise ValueError("History changed since confirmation. Refresh History and try again.")
            deleted = []
            try:
                for asset_id in sorted(current):
                    deleted.append(self.trash_asset(asset_id))
            except Exception:
                for entry in reversed(deleted):
                    self.undo_delete(entry["token"])
                raise
            return {"deleted": deleted}

    def create_job(self, asset_id, stage):
        job = {"id": uuid.uuid4().hex, "asset": identifier(asset_id),
               "stage": stage, "created": time.time(), "status": "preparing"}
        folder = contained(self.cache, job["id"])
        folder.mkdir(parents=True, exist_ok=False)
        atomic_json(folder / "owner.json", {"owner": "comfyui-asset-workshop", **job})
        with LOCK:
            data = self.load(asset_id)
            data["jobs"].append(job)
            self.save(data)
        return job

    def complete_job(self, asset_id, job_id, result):
        with LOCK:
            data = self.load(asset_id)
            if data.get("schema_version") == 2:
                for job in data["jobs"]:
                    stage = next((s for s in job["stages"] if s["id"] == job_id), None)
                    if stage:
                        stage["result"] = copy.deepcopy(result)
                        self.save(data)
                        return
                raise ValueError("The output does not belong to a recorded job stage.")
            job = next(j for j in data["jobs"] if j["id"] == identifier(job_id))
            job.update(status="complete", completed=time.time(), result=result)
            if result.get("export"): data["selected_export"]=result["export"]
            if result.get("master"): data["selected_master"]=result["master"]
            if result.get("draft"): data["selected_draft"]=result["draft"]
            self.save(data)
            self.cleanup_job(job_id)

    def cleanup_job(self, job_id):
        folder = contained(self.cache, identifier(job_id))
        marker = folder / "owner.json"
        if not marker.is_file():
            return
        owner = json.loads(marker.read_text(encoding="utf-8"))
        if owner.get("owner") != "comfyui-asset-workshop" or owner.get("id") != job_id:
            raise ValueError("Temporary folder ownership could not be verified.")
        # Resolve every directory, including Windows junctions, before deletion.
        for current, directories, files in os.walk(folder, followlinks=False):
            for name in directories + files:
                contained(folder, str(Path(current, name).relative_to(folder)))
        shutil.rmtree(folder)


def _pipeline_contracts():
    # Store is also used directly by the existing no-Comfy contract tests.
    import importlib.util
    import sys
    name = "_mumblebox_pipeline_contracts"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("pipeline_state.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[name] = module
    return sys.modules[name]
