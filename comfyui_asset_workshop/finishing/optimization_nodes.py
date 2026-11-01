"""Visible native graph entry for isolated established optimization tools."""
import importlib.util
import json
from pathlib import Path
import uuid

from .runtime import WORKERS, work_root, worker_python, settings
from ..pipeline_workers import trellis_bridge_runtime as runtime


class Hi3DOptimizeAndRebake:
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {
            'mesh': ('MESH',),
            'texture_source_path': ('STRING', {'default': ''}),
            'method': (['quadric', 'quadriflow'], {'default': 'quadric'}),
            'target_triangles': ('INT', {'default': 250000, 'min': 1000, 'max': 2000000, 'step': 1000}),
            'texture_size': ('INT', {'default': 4096, 'min': 512, 'max': 8192, 'step': 512}),
            'planar_quadric': ('BOOLEAN', {'default': False}),
            'run_name': ('STRING', {'default': 'frog-250k-quadric'}),
        }, 'optional': {'textured_glb': ('FILE_3D',)}}
    RETURN_TYPES = ('MESH', 'IMAGE', 'STRING')
    RETURN_NAMES = ('optimized_textured_mesh', 'base_color', 'report')
    FUNCTION = 'optimize'
    CATEGORY = 'Hi3D/Optimization experiment'
    OUTPUT_NODE = True

    def optimize(self, mesh, texture_source_path, method, target_triangles, texture_size,
                 planar_quadric, run_name, textured_glb=None):
        import numpy as np
        import torch
        from PIL import Image
        import comfy.model_management as mm
        import folder_paths
        from comfy_api.latest import Types
        from ..pipeline_workers.refine_client import arrays

        source = textured_glb.get_source() if textured_glb is not None else texture_source_path
        if not isinstance(source, str) or not Path(source).is_file():
            raise ValueError('Connect a disk-backed textured GLB or supply its existing path')
        job = work_root() / 'optimization-jobs' / uuid.uuid4().hex
        job.mkdir(parents=True)
        v, f = arrays(mesh)
        np.savez(job / 'master.npz', vertices=v, faces=f)
        request = {'mesh': str(job / 'master.npz'), 'texture_source': source, 'method': method,
                   'target_triangles': target_triangles, 'texture_size': texture_size,
                   'planar_quadric': planar_quadric}
        request.update(settings())
        (job / 'request.json').write_text(json.dumps(request, indent=2), encoding='utf-8')
        mm.unload_all_models()
        mm.soft_empty_cache()
        runtime.run_worker([worker_python(), '-u',
                            str(WORKERS / 'mesh_optimize_worker.py'), str(job / 'request.json')],
                           job / 'worker.log', mm.throw_exception_if_processing_interrupted)
        data = np.load(job / 'result.npz')
        def image(name):
            return torch.from_numpy(np.asarray(Image.open(job / name).convert('RGB')).copy().astype(np.float32) / 255).unsqueeze(0)
        base = image('baked-base-color.png')
        output = Types.MESH(vertices=torch.from_numpy(data['vertices'].copy()).float().unsqueeze(0),
                            faces=torch.from_numpy(data['faces'].copy()).long().unsqueeze(0),
                            uvs=torch.from_numpy(data['uvs'].copy()).float().unsqueeze(0),
                            normals=torch.from_numpy(data['normals'].copy()).float().unsqueeze(0),
                            texture=base, metallic_roughness=image('baked-metallic-roughness.png'))
        report = (job / 'report.json').read_text(encoding='utf-8')
        import re
        safe = re.sub(r'[^A-Za-z0-9_.-]', '_', run_name)[:120] or 'optimized'
        directory = Path(folder_paths.get_output_directory()) / '3d' / 'OptimizationLab'
        directory.mkdir(parents=True, exist_ok=True)
        (directory / (safe + '-report.json')).write_text(report, encoding='utf-8')
        return {'ui': {'text': [report]}, 'result': (output, base, report)}


NODE_CLASS_MAPPINGS = {'Hi3DOptimizeAndRebake': Hi3DOptimizeAndRebake}
NODE_DISPLAY_NAME_MAPPINGS = {'Hi3DOptimizeAndRebake': 'Optimize + rebake final-mesh textures (experiment)'}
