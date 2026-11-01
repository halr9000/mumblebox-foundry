"""Standalone post-refinement gates; no product GUI integration."""
import json
from pathlib import Path
import numpy as np
from .pipeline_nodes import topology_report

def repair_needed(vertices, faces):
    import trimesh
    report = topology_report(vertices, faces)
    probe = trimesh.Trimesh(vertices, faces, process=False)
    report["positive_volume"] = bool(probe.volume > 0)
    needed = not (report["watertight"] and report["winding_consistent"]
                  and report["nonmanifold_edges"] == 0 and report["degenerate_faces"] == 0
                  and report["positive_volume"])
    report["solid_repair_needed"] = needed
    report["not_tested"] = ["self intersections", "wall thickness", "physical printability"]
    return needed, report

def export_print_candidate(vertices, faces, height_mm, path, check_interrupt=None):
    import trimesh
    if not np.isfinite(height_mm) or height_mm <= 0:
        raise ValueError("Print height must be positive and finite")
    needed, topology = repair_needed(vertices, faces)
    if needed:
        raise ValueError("Print candidate requires closed, consistently wound, nondegenerate geometry")
    mesh = trimesh.Trimesh(np.array(vertices, dtype=np.float64, copy=True),
                           np.array(faces, dtype=np.int64, copy=True), process=False)
    bounds = mesh.bounds
    height = float(mesh.extents[1])
    if height <= 1e-12:
        raise ValueError("Mesh has no measurable Y height")
    scale = float(height_mm / height)
    center = (bounds[0] + bounds[1]) / 2
    v = (mesh.vertices - center) * scale
    # Right-handed Y-up to Z-up, then stand on the Z=0 build plate.
    v = v[:, [0, 2, 1]]
    v[:, 1] *= -1
    v[:, 2] -= v[:, 2].min()
    mesh.vertices = v
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(path, file_type="stl")
    exported, repair = ensure_stl_connectivity(path, height_mm, check_interrupt)
    report = {"export_topology": exported, "contact_repair": repair, "output": str(path), "format": "STL", "units": "millimetres",
              "up_axis": "Z", "height_mm": float(mesh.extents[2]),
              "dimensions_mm": mesh.extents.tolist(), "source_to_mm_scale": scale,
              "faces": len(mesh.faces), "source_geometry_unchanged": True,
              "topology": topology, "physically_validated": False,
              "not_tested": ["self intersections", "minimum wall thickness",
                             "supports", "slicer acceptance", "physical printing"]}
    path.with_suffix(".report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

class Hi3DNeedsSolidRepair:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"mesh": ("MESH",)}}
    RETURN_TYPES = ("BOOLEAN", "STRING")
    RETURN_NAMES = ("needs_solid_repair", "connectivity_report")
    FUNCTION = "check"
    CATEGORY = "Hi3D/Automatic workflow"
    def check(self, mesh):
        from ..pipeline_workers.refine_client import arrays
        needed, report = repair_needed(*arrays(mesh))
        payload = json.dumps(report)
        return {"ui": {"text": [payload]}, "result": (needed, payload)}

class Hi3DPrintCandidate:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "mesh": ("MESH",),
            "height_mm": ("FLOAT", {"default": 100., "min": 1., "max": 2000., "step": 1.}),
            "filename_prefix": ("STRING", {"default": "3d/PrintCandidate/print-100mm"})}}
    RETURN_TYPES = ("FILE_3D", "STRING")
    RETURN_NAMES = ("print_stl", "print_report")
    FUNCTION = "export"
    OUTPUT_NODE = True
    CATEGORY = "Hi3D/Automatic workflow"
    def export(self, mesh, height_mm, filename_prefix):
        import folder_paths
        from comfy_api.latest import Types
        from ..pipeline_workers.refine_client import arrays
        folder, name, counter, _, _ = folder_paths.get_save_image_path(
            filename_prefix, folder_paths.get_output_directory())
        destination = Path(folder) / f"{name}_{counter:05}_.stl"
        import comfy.model_management as mm
        report = export_print_candidate(*arrays(mesh), height_mm, destination, mm.throw_exception_if_processing_interrupted)
        payload = json.dumps(report)
        return {"ui": {"text": [payload]}, "result": (Types.File3D(str(destination)), payload)}

NODE_CLASS_MAPPINGS = {c.__name__: c for c in (Hi3DNeedsSolidRepair, Hi3DPrintCandidate)}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Hi3DNeedsSolidRepair": "Hi3D — check whether solid repair is needed",
    "Hi3DPrintCandidate": "Hi3D — scaled print candidate (STL)",
}


def ensure_stl_connectivity(path, height_mm, check_interrupt=None):
    import importlib.util
    import shutil
    import uuid
    import trimesh
    mesh = trimesh.load(path, force="mesh")
    repair = None
    if not (mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0):
        from .runtime import WORKERS, work_root, worker_python
        from ..pipeline_workers import trellis_bridge_runtime as runtime
        root = work_root()
        job = root / "print-jobs" / uuid.uuid4().hex
        job.mkdir(parents=True)
        before = path.with_name(path.stem + ".pre-contact-repair.stl")
        shutil.copy2(path, before)
        request = {"source":str(before), "output":str(path), "height_mm":height_mm}
        (job / "request.json").write_text(json.dumps(request),encoding="utf-8")
        runtime.run_worker([worker_python(),
                            "-u", str(WORKERS / "print_repair_worker.py"), str(job / "request.json")],
                           job / "worker.log", check_interrupt or (lambda: None))
        repair = json.loads((job / "report.json").read_text(encoding="utf-8"))
        mesh = trimesh.load(path, force="mesh")
    topology = {"watertight":bool(mesh.is_watertight),
                "winding_consistent":bool(mesh.is_winding_consistent),
                "positive_volume":bool(mesh.volume > 0),
                "triangles":len(mesh.faces), "dimensions_mm":mesh.extents.tolist()}
    if not all(topology[k] for k in ("watertight", "winding_consistent", "positive_volume")):
        raise RuntimeError("STL re-import failed the geometry gate")
    return topology, repair
