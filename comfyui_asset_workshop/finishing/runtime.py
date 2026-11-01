"""One configured runtime for all finishing nodes; worker requests carry explicit paths."""
from pathlib import Path
import shutil

WORKERS=Path(__file__).resolve().parents[1]/"pipeline_workers"

def settings():
    import folder_paths
    from ..runtime import configuration
    from ..pipeline_capabilities import validate_runtime
    config=validate_runtime(configuration().get("pipeline_runtime",{}))
    config.setdefault("comfy_core",str(Path(folder_paths.__file__).resolve().parent))
    config.setdefault("blender",shutil.which("blender") or "")
    return config

def worker_python():
    value=settings().get("worker_python","")
    if not value or not Path(value).is_file():
        raise ValueError("Configure pipeline_runtime.worker_python in ComfyUI user/asset-workshop.json; see INSTALL.md")
    return value

def work_root():
    import folder_paths
    return Path(folder_paths.get_output_directory())/"3d"/".foundry-work"
