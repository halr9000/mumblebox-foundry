"""Blender entry point, used only in the new window created by Open in Blender."""
import sys
import json
from pathlib import Path
import bpy

mesh, receipt = (Path(value).resolve() for value in sys.argv[sys.argv.index('--') + 1:][:2])
try:
    if mesh.suffix.lower() != '.glb' or not mesh.is_file():
        raise ValueError('The exported GLB is missing.')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(mesh))
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'
            for region in area.regions:
                if region.type == 'WINDOW':
                    with bpy.context.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_selected(use_all_regions=False)
                    break
    result = {'mesh_objects': sum(obj.type == 'MESH' for obj in bpy.context.scene.objects), 'file': mesh.name}
except Exception as error:
    result = {'error': str(error)}
receipt.write_text(json.dumps(result), encoding='utf-8')
