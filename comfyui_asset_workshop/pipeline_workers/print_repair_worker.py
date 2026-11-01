"""Repair only an STL copy whose normal re-import loses manifold connectivity.

Uses MeshLib's published localized repair, with its voxel repair as a bounded fallback.
https://github.com/MeshInspector/MeshLib/blob/master/python_scripts/mesh_repair.py
"""
import json
from pathlib import Path
import sys
import time
import numpy as np
import trimesh
import pymeshlab
from meshlib import mrmeshpy as mr

def check(path):
    mesh = trimesh.load(path, force="mesh")
    ms = pymeshlab.MeshSet()
    ms.add_mesh(pymeshlab.Mesh(vertex_matrix=np.asarray(mesh.vertices),
                              face_matrix=np.asarray(mesh.faces, dtype=np.int32)))
    ms.compute_selection_by_self_intersections_per_face()
    intersections = int(ms.current_mesh().face_selection_array().sum())
    result = {"watertight": bool(mesh.is_watertight),
              "winding_consistent": bool(mesh.is_winding_consistent),
              "positive_volume": bool(mesh.volume > 0),
              "zero_area_faces": int((mesh.area_faces == 0).sum()),
              "self_intersection_selected_faces": intersections,
              "triangles": len(mesh.faces), "dimensions_mm": mesh.extents.tolist()}
    good = all(result[k] for k in ("watertight", "winding_consistent", "positive_volume"))
    return mesh, result, good and intersections == 0 and result["zero_area_faces"] == 0

def main():
    request_path = Path(sys.argv[1])
    req = json.loads(request_path.read_text(encoding="utf-8"))
    folder = request_path.parent
    started = time.monotonic()
    source = Path(req["source"])
    out = Path(req["output"])
    mesh = mr.loadMesh(source)
    settings = mr.SelfIntersections.Settings()
    settings.maxExpand = 2
    settings.relaxIterations = 2
    settings.method = mr.SelfIntersections.Settings.Method.CutAndFill
    settings.touchIsIntersection = True
    mr.SelfIntersections.fix(mesh, settings)
    candidate = folder / "localized.stl"
    mr.saveMesh(mesh, candidate)
    repaired, topology, good = check(candidate)
    method = "MeshLib localized CutAndFill; maxExpand2; relaxIterations2"
    voxel_size = None
    if not good:
        mesh = mr.loadMesh(source)
        voxel_size = float(req["height_mm"]) / 512.
        print("Local repair insufficient; voxel contact repair", voxel_size, flush=True)
        mr.fixSelfIntersections(mesh, voxel_size)
        candidate = folder / "voxel.stl"
        mr.saveMesh(mesh, candidate)
        repaired, topology, good = check(candidate)
        method = "MeshLib fixSelfIntersections voxel repair; height/512"
    if not good:
        raise RuntimeError("Print contact repair did not pass re-import checks: " + json.dumps(topology))
    repaired.apply_scale(float(req["height_mm"]) / float(repaired.extents[2]))
    repaired.apply_translation([0, 0, -float(repaired.bounds[0,2])])
    repaired.export(out, file_type="stl")
    final, topology, good = check(out)
    if not good:
        raise RuntimeError("Final STL quantization broke geometry checks: " + json.dumps(topology))
    original = trimesh.load(source, force="mesh")
    distances = []
    for a, b in ((original, final), (final, original)):
        points, _ = trimesh.sample.sample_surface(a, 2000, seed=42)
        _, d, _ = trimesh.proximity.closest_point(b, points)
        distances.extend(d.tolist())
    if max(distances) > float(req["height_mm"]) * .01:
        raise RuntimeError("Print repair exceeded sampled 1%-of-height deviation limit")
    report = {"method": method, "voxel_size_mm": voxel_size,
              "source_preserved": str(source), "export_topology": topology,
              "sampled_surface_error_mm": {"samples": 4000, "seed":42,
                  "mean":float(np.mean(distances)), "p95":float(np.percentile(distances,95)),
                  "max":float(max(distances))},
              "seconds":time.monotonic()-started}
    (folder / "report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report),flush=True)

if __name__ == "__main__":
    main()
