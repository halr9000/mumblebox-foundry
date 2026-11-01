"""Curated credit copy joined to the finishing package's authoritative resource registry."""
import json
import sys
from pathlib import Path

def catalog():
    curated = json.loads((Path(__file__).parent / "catalog" / "credits.json").read_text(encoding="utf-8"))
    registry_path = Path(__file__).resolve().parents[1] / "finishing" / "package_resources.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path and registry_path.is_file() else {}
    for item in curated:
        resource = registry.get(item["id"], {})
        item.update({k: resource[k] for k in ("name", "source", "version", "stage", "note") if k in resource})
        item["registry_backed"] = bool(resource)
    return {"credits": curated, "github": "https://github.com/mumblebox-gpt",
            "donate": None, "homepage": None, "pinokio": None,
            "resource_registry_available": bool(registry),
            "workflow": {"id": "image-to-3d/v1", "name": "Create a 3D Asset from an Image",
                         "input": "One overall image and optional described references", "wizard": False}}
