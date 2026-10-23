"""Portable paths: the host's output folder, never a developer's drive letter."""

import json
import os
from pathlib import Path

import folder_paths

from .store import AssetStore, atomic_json

CONFIG = Path(folder_paths.get_user_directory()) / "asset-workshop.json"


def configuration():
    data = json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.is_file() else {}
    data.setdefault("root", str(Path(folder_paths.get_output_directory()) / "AssetWorkshop"))
    return data


def store():
    return AssetStore(configuration()["root"])


def set_root(value):
    path = Path(value).expanduser()
    if not path.is_absolute() or "onedrive" in str(path).lower().split(os.sep):
        raise ValueError("Choose an absolute local folder outside OneDrive.")
    if any(p.lower() == "onedrive" for p in path.parts):
        raise ValueError("The asset library must be outside OneDrive.")
    path.mkdir(parents=True, exist_ok=True)
    data = configuration()
    data["root"] = str(path.resolve())
    atomic_json(CONFIG, data)
    return data


def request_startup_headroom(value):
    value = float(value)
    if not 0 <= value <= 64:
        raise ValueError("Requested startup headroom must be between 0 and 64 GB.")
    data = configuration()
    data["pending_vram_headroom_gb"] = value
    atomic_json(CONFIG, data)
    return {"requested_gb": value, "launch_argument": f"--vram-headroom {value:g}",
            "applied": False, "instruction": "Set this argument in your Comfy launcher's startup settings, then restart when ready. Saving the request here does not restart or alter the launcher."}
