"""Process and coordinate handling for the isolated TRELLIS.2 experiment."""
import os
from pathlib import Path
import subprocess
import time

import numpy as np


def mesh_frame(vertices):
    lower, upper = vertices.min(axis=0), vertices.max(axis=0)
    extent = float((upper - lower).max())
    if not np.isfinite(vertices).all() or extent <= 0:
        raise ValueError('Mesh must have finite coordinates and nonzero extent')
    return {'center': (lower + upper) / 2, 'scale': 0.99999 / extent}


def restore_vertices(vertices, frame):
    return vertices / frame['scale'] + frame['center']


def texture_reference_rgb(image):
    """Honor cutout alpha before RGB-only DINO conditioning, on black as upstream preprocessing does."""
    from PIL import Image
    background = Image.new('RGBA', image.size, (0, 0, 0, 255))
    return Image.alpha_composite(background, image.convert('RGBA')).convert('RGB')


def clean_zero_edges(vertices, faces, max_collapses=256):
    """Collapse exact zero-length mesh edges, preserving unconnected touching sheets.

    The manifold link condition limits each collapse to its two zero-area faces.
    Every retained triangle keeps exactly the same three geometric positions.
    """
    v, original_faces = np.asarray(vertices), np.asarray(faces)
    if v.ndim != 2 or v.shape[1] != 3 or original_faces.ndim != 2 or original_faces.shape[1] != 3:
        raise ValueError('Expected one XYZ triangle mesh')
    if not np.isfinite(v).all() or not len(v) or not len(original_faces):
        raise ValueError('Expected finite, nonempty mesh geometry')
    if original_faces.min() < 0 or original_faces.max() >= len(v):
        raise ValueError('Mesh face index is out of range')
    f = original_faces
    collapsed = removed = 0
    while True:
        candidates = []
        for left, right in ((0, 1), (1, 2), (2, 0)):
            keep = np.all(v[f[:, left]] == v[f[:, right]], axis=1) & (f[:, left] != f[:, right])
            if keep.any():
                candidates.append(np.sort(f[keep][:, [left, right]], axis=1))
        if not candidates:
            break
        if collapsed >= max_collapses:
            raise ValueError('Exact zero-edge cleanup exceeded its bounded collapse limit')
        a, b = map(int, np.unique(np.concatenate(candidates), axis=0)[0])
        incident_a, incident_b = np.any(f == a, axis=1), np.any(f == b, axis=1)
        edge_faces = f[incident_a & incident_b]
        opposite = set(edge_faces.ravel()) - {a, b}
        shared = (set(f[incident_a].ravel()) - {a}) & (set(f[incident_b].ravel()) - {b})
        if len(edge_faces) != 2 or len(opposite) != 2 or shared != opposite:
            raise ValueError('Zero-length edge fails the manifold link condition; refusing to weld it')
        updated = f.copy()
        updated[updated == b] = a
        valid = (updated[:, 0] != updated[:, 1]) & (updated[:, 1] != updated[:, 2]) & (updated[:, 2] != updated[:, 0])
        if int((~valid).sum()) != 2:
            raise ValueError('Zero-edge collapse would remove unexpected faces')
        f = updated[valid]
        collapsed += 1
        removed += 2
    report = {'method': 'exact connected zero-edge collapse with manifold link condition',
              'collapsed_zero_edges': collapsed, 'removed_zero_area_faces': removed,
              'input_faces': len(original_faces), 'output_faces': len(f),
              'unconnected_coincident_positions': 'preserved; no global position welding'}
    if not collapsed:
        return v, f, report
    used, inverse = np.unique(f, return_inverse=True)
    return v[used].copy(), inverse.reshape(-1, 3).astype(f.dtype), report


def run_worker(command, log_path, check_interrupt):
    log_path = Path(log_path)
    try:
        from .worker_process import OwnedWorker
    except ImportError:
        import importlib.util
        spec=importlib.util.spec_from_file_location('mumblebox_owned_worker',Path(__file__).with_name('worker_process.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);OwnedWorker=module.OwnedWorker
    with log_path.open('w',encoding='utf-8') as log:
        owner=OwnedWorker(command,log);process=owner.process
        monitored=any(str(part).endswith('trellis_texture_worker.py') for part in command)
        key='trellis:'+str(process.pid)
        if monitored:
            from .activity import update, read_worker, remove
            update(key,'TRELLIS.2')
        try:
            started=time.monotonic()
            while process.poll() is None:
                check_interrupt()
                if monitored:read_worker(key,'TRELLIS.2',log_path.with_name('model-residency.json'),process.pid)
                if time.monotonic()-started>3600:raise TimeoutError('Isolated worker exceeded one hour')
                time.sleep(.25)
        finally:
            try:
                if process.poll() is None:owner.stop()
            finally:
                owner.close()
                if monitored:remove(key)
    if process.returncode:
        detail = log_path.read_text(encoding='utf-8', errors='replace')[-7000:]
        raise RuntimeError(f'TRELLIS.2 worker failed ({process.returncode}). Log: {log_path}\n{detail}')
