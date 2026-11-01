import ast
from pathlib import Path
import time
import uuid
import unittest
from types import SimpleNamespace
class OutputPathTests(unittest.TestCase):
    def test_record_uses_project_directory_without_requesting_an_empty_asset_path(self):
        tree=ast.parse((Path(__file__).parents[1]/"pipeline_nodes.py").read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="output_record")
        namespace={"time":time,"uuid":uuid,"digest":lambda p:"hash"}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"pipeline-output-contract","exec"),namespace)
        def path(pid,rel):raise ValueError("Empty asset paths are intentionally disallowed")
        lib=SimpleNamespace(path=path,directory=lambda pid:Path('/project'),record_pipeline_artifact=lambda pid,sid,row:row,complete_job=lambda *args:None)
        row=namespace["output_record"](lib,"p1","s1",Path('/project/pipeline/result.glb'))
        self.assertEqual(row["file"],"pipeline/result.glb")

    def test_refine_and_texture_use_verified_transparent_cutout(self):
        tree=ast.parse((Path(__file__).parents[1]/"pipeline_nodes.py").read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="reference")
        namespace={"digest":lambda p:"cutout-hash"}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"pipeline-reference-contract","exec"),namespace)
        record={"id":"img","file":"original.png","sha256":"original-hash","foreground":{"source_sha256":"original-hash","cutout_file":"cutout.png","cutout_sha256":"cutout-hash"}}
        lib=SimpleNamespace(mesh_input=lambda pid:record,path=lambda pid,rel:Path('/project')/rel,load=lambda pid:{"jobs":[]})
        self.assertEqual(namespace["reference"](lib,"p1"),Path('/project/cutout.png'))
        namespace["digest"]=lambda p:"changed"
        with self.assertRaises(ValueError):namespace["reference"](lib,"p1")

    def test_canonical_map_export_does_not_reencode_glb_or_drop_alpha(self):
        tree=ast.parse((Path(__file__).parents[1]/"pipeline_nodes.py").read_text())
        fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="material_sidecars"),None)
        self.assertIsNotNone(fn,"Canonical output must include matching separate maps")
        import tempfile
        import numpy as np
        import trimesh
        from PIL import Image
        import hashlib
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"mesh.glb";mesh=trimesh.creation.box()
            color=Image.new('RGBA',(4,4),(40,80,120,177))
            mesh.visual=trimesh.visual.TextureVisuals(uv=np.zeros((len(mesh.vertices),2)),material=trimesh.visual.material.PBRMaterial(baseColorTexture=color,metallicRoughnessTexture=Image.new('RGB',(4,4),(255,120,7)),metallicFactor=1,roughnessFactor=1))
            mesh.export(path);before=path.read_bytes()
            namespace={"trimesh":trimesh,"Image":Image,"np":np,"digest":lambda p:hashlib.sha256(p.read_bytes()).hexdigest()}
            exec(compile(ast.Module(body=[fn],type_ignores=[]),"canonical-sidecars","exec"),namespace)
            result=namespace["material_sidecars"](path)
            self.assertEqual(before,path.read_bytes())
            self.assertEqual(Image.open(path.parent/'base_color.png').getpixel((0,0)),(40,80,120,177))
            self.assertEqual(Image.open(path.parent/'metallic.png').getpixel((0,0)),7)
            self.assertIn('base_color.png',result['hashes'])

    def test_variant_glb_uses_native_uvs_without_a_second_vertical_flip(self):
        tree=ast.parse((Path(__file__).parents[1]/"pipeline_nodes.py").read_text())
        fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="variant_mesh"),None)
        self.assertIsNotNone(fn,"Native-to-trimesh UV conversion must be explicit")
        import numpy as np,trimesh,json,struct
        namespace={"np":np,"trimesh":trimesh}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),"variant-uv-contract","exec"),namespace)
        uv=np.array([[.1,.2],[.9,.2],[.5,.9]],np.float32);before=uv.copy()
        mesh=namespace['variant_mesh'](np.array([[0,0,0],[1,0,0],[0,1,0]]),np.array([[0,1,2]]),uv,trimesh.visual.material.PBRMaterial())
        blob=mesh.export(file_type='glb');length=struct.unpack_from('<I',blob,12)[0];description=json.loads(blob[20:20+length]);binary=20+length+8
        index=description['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0'];a=description['accessors'][index];v=description['bufferViews'][a['bufferView']]
        stored=np.frombuffer(blob,dtype='<f4',count=a['count']*2,offset=binary+v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,2)
        np.testing.assert_allclose(stored,uv,atol=1e-7);np.testing.assert_array_equal(uv,before)
