"""Read-only, dependency-free checks for explicitly configured isolated runtimes."""
from pathlib import Path
from urllib.parse import urlparse
PATHS={"worker_python","comfy_core","trellis_repo","trellis_models","stable_materials","material_cache","blender","qremeshify"}
WRAPPER_REVISION="b0e84c0f29857a444e8bcb5b9be2ea218e96efd0"
def validate_runtime(config):
    if not isinstance(config,dict) or config.keys()-PATHS-{"hi3d_url"}:raise ValueError("Unknown pipeline runtime setting")
    result=dict(config)
    for key in PATHS & config.keys():
        p=Path(config[key])
        if not p.is_absolute() or any("onedrive" in part.lower() for part in p.parts):raise ValueError("Choose absolute runtime paths outside OneDrive")
    if "hi3d_url" in config:
        u=urlparse(config["hi3d_url"])
        if u.scheme!="http" or u.hostname not in ("localhost","127.0.0.1","::1") or u.username or u.password or u.query or u.fragment:raise ValueError("Hi3D must use a local HTTP service")
    return result

def inspect_runtime(config):
    config=validate_runtime(config)
    missing=[k for k in ("worker_python","comfy_core","trellis_repo","trellis_models") if not config.get(k) or not Path(config[k]).exists()]
    trellis=not missing
    materials=trellis and bool(config.get("stable_materials")) and Path(config["stable_materials"]).is_dir()
    return {"providers":{"trellis2":{"available":trellis,"label":"TRELLIS.2 (recommended)","reason":"" if trellis else "Configure isolated runtime: "+", ".join(missing)},"pixal3d":{"available":False,"label":"Pixal3D texture only","reason":"The separate Pixal3D texture model is not installed and has not passed final-mesh testing. Use TRELLIS.2."}},"materials_available":materials,"hi3d_configured":bool(config.get("hi3d_url")),"wrapper_revision":WRAPPER_REVISION}
