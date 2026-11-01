import copy
import json
import numpy as np


def vertices(mesh):
    value = mesh.vertices
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    value = np.asarray(value)
    if value.ndim == 3:
        if len(value) != 1:
            raise ValueError("The automatic workflow accepts one object at a time")
        value = value[0]
        counts = getattr(mesh, "vertex_counts", None)
        if counts is not None:
            value = value[:int(counts[0])]
    if value.ndim != 2 or value.shape[1] != 3 or not len(value) or not np.isfinite(value).all():
        raise ValueError("Mesh vertices must be finite, nonempty XYZ coordinates")
    return value.astype(np.float64, copy=False)

def transformed(mesh, scale, offset):
    """Uniform positive scale + translation; preserve faces, UVs and normals."""
    import torch
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(offset).all():
        raise ValueError("Invalid mesh transform")
    output = copy.copy(mesh)
    v = mesh.vertices
    if not hasattr(v, "device"):
        v = torch.as_tensor(v, dtype=torch.float32)
    output.vertices = v * float(scale) + torch.as_tensor(offset, dtype=v.dtype, device=v.device)
    return output

def frame_for(mesh, span=0.96):
    v = vertices(mesh)
    lower, upper = v.min(axis=0), v.max(axis=0)
    extent = float((upper - lower).max())
    if extent <= 1e-12:
        raise ValueError("Cannot normalize a zero-size mesh")
    return {"center": ((lower + upper) / 2).tolist(), "scale": float(span / extent), "span": float(span)}

class Hi3DNormalizeMesh:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"mesh": ("MESH",), "span": ("FLOAT", {"default": 0.96, "min": 0.1, "max": 0.98, "step": 0.01})}}
    RETURN_TYPES = ("MESH", "HI3D_MESH_FRAME")
    RETURN_NAMES = ("normalized_mesh", "original_frame")
    FUNCTION = "normalize"
    CATEGORY = "Hi3D/Automatic workflow"

    def normalize(self, mesh, span):
        frame = frame_for(mesh, span)
        return transformed(mesh, frame["scale"], -np.array(frame["center"]) * frame["scale"]), frame

class Hi3DRestoreMeshFrame:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"mesh": ("MESH",), "original_frame": ("HI3D_MESH_FRAME",)}}
    RETURN_TYPES = ("MESH",)
    FUNCTION = "restore"
    CATEGORY = "Hi3D/Automatic workflow"

    def restore(self, mesh, original_frame):
        return (transformed(mesh, 1 / original_frame["scale"], np.array(original_frame["center"])),)

class Hi3DAlignToSource:
    """Recover scale/translation for texture projection; never rotate or warp.

    Hi3D's repeated voxelization and final normalization discard the original
    frame. This is an approximate registration, not an exact inverse. Keep the
    untouched Hi3D output as the geometry reference and record fit residuals.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"mesh": ("MESH",), "source_mesh": ("MESH",)}}
    RETURN_TYPES = ("MESH", "STRING")
    RETURN_NAMES = ("mesh_in_source_frame", "alignment_report")
    FUNCTION = "align"
    CATEGORY = "Hi3D/Automatic workflow"

    def align(self, mesh, source_mesh):
        from scipy.spatial import cKDTree
        source, target = vertices(mesh), vertices(source_mesh)
        sf, tf = frame_for(mesh), frame_for(source_mesh)
        scale = sf["scale"] / tf["scale"]
        offset = np.array(tf["center"]) - np.array(sf["center"]) * scale
        rng = np.random.default_rng(42)
        sample = source[rng.choice(len(source), min(30000, len(source)), replace=False)]
        # Query the full source surface vertex set; dense Pixal meshes make this
        # a close surface approximation without allocating face-pair matrices.
        tree = cKDTree(target)
        initial_scale = scale
        for _ in range(20):
            transformed_sample = sample * scale + offset
            distances, indices = tree.query(transformed_sample, workers=1)
            keep = distances <= np.quantile(distances, 0.8)
            a, b = sample[keep], target[indices[keep]]
            ac, bc = a.mean(axis=0), b.mean(axis=0)
            denominator = np.square(a - ac).sum()
            if denominator <= 1e-20:
                break
            new_scale = float(((a - ac) * (b - bc)).sum() / denominator)
            new_scale = float(np.clip(new_scale, initial_scale * 0.9, initial_scale * 1.1))
            new_offset = bc - ac * new_scale
            delta = abs(new_scale - scale) + np.linalg.norm(new_offset - offset)
            scale, offset = new_scale, new_offset
            if delta < 1e-7:
                break
        distances, _ = tree.query(sample * scale + offset, workers=1)
        diagonal = float(np.linalg.norm(np.ptp(target, axis=0)))
        report = {"method": "uniform scale and translation; 80% trimmed nearest-vertex fit", "approximate": True,
                  "scale": scale, "translation": offset.tolist(), "samples": len(sample),
                  "median_distance_over_source_diagonal": float(np.median(distances) / diagonal),
                  "p95_distance_over_source_diagonal": float(np.quantile(distances, 0.95) / diagonal)}
        return transformed(mesh, scale, offset), json.dumps(report)

def topology_report(raw_vertices, faces):
    import trimesh
    mesh = trimesh.Trimesh(raw_vertices, faces, process=False)
    def edge_counts(value):
        _, counts = np.unique(value.edges_sorted, axis=0, return_counts=True)
        return {'boundary_edges': int((counts == 1).sum()),
                'nonmanifold_edges': int((counts > 2).sum()),
                'watertight': bool(value.is_watertight),
                'winding_consistent': bool(value.is_winding_consistent)}
    unique, inverse = np.unique(raw_vertices, axis=0, return_inverse=True)
    probe = edge_counts(trimesh.Trimesh(unique, inverse[faces], process=False))
    probe['note'] = 'Merges coincident UV seams and deliberately separated touching sheets; not authoritative mesh connectivity.'
    return {'report_version': 2, 'render_vertices': len(raw_vertices),
            'unique_positions': len(unique), 'faces': len(faces), **edge_counts(mesh),
            'coincident_position_probe': probe,
            'degenerate_faces': int((mesh.area_faces <= 1e-14).sum()),
            'bounds': mesh.bounds.tolist(), 'extents': mesh.extents.tolist()}
