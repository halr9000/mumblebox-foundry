import sys
import unittest
import numpy as np
from PIL import Image
from pathlib import Path
import tempfile
sys.path.insert(0,str(Path(__file__).parents[1]/"pipeline_workers"))
import trimesh

class MaterialRegionTests(unittest.TestCase):
    def test_material_application_preserves_color_geometry_and_unselected_pixels(self):
        from material_regions import compose_material
        mesh=trimesh.Trimesh(vertices=[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],faces=[[0,1,2],[0,2,3]],process=False)
        mesh.visual=trimesh.visual.TextureVisuals(uv=np.array([[0,0],[1,0],[1,1],[0,1]]),material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.new('RGB',(8,8),(80,30,150)),metallicRoughnessTexture=Image.new('RGB',(8,8),(0,50,70))))
        original_v=mesh.vertices.copy();original_f=mesh.faces.copy();original_uv=mesh.visual.uv.copy();original_color=np.array(mesh.visual.material.baseColorTexture)
        mask=np.zeros((8,8),bool);mask[:,:4]=True
        maps={'roughness':Image.new('L',(4,4),230),'metallic':Image.new('L',(4,4),0),'normal':Image.new('RGB',(4,4),(128,128,255))}
        out=compose_material(mesh,[{'mask':mask,'maps':maps,'strength':1,'detail':.2,'tiles':2,'metallic':'nonmetal'}])
        np.testing.assert_array_equal(out.vertices,original_v);np.testing.assert_array_equal(out.faces,original_f);np.testing.assert_array_equal(out.visual.uv,original_uv)
        np.testing.assert_array_equal(np.array(out.visual.material.baseColorTexture),original_color)
        mr=np.array(out.visual.material.metallicRoughnessTexture)
        self.assertTrue(np.all(mr[mask,1]==230));self.assertTrue(np.all(mr[mask,2]==0));self.assertTrue(np.all(mr[~mask]==[0,50,70]))
        np.testing.assert_array_equal(np.array(mesh.visual.material.metallicRoughnessTexture),np.full((8,8,3),[0,50,70],dtype=np.uint8))

    def test_selection_distinguishes_color_groups_from_connected_patches(self):
        from material_regions import region_mask,validate_edits
        face_map=np.array([[1,2,0],[3,4,0]],np.uint32)
        palette=np.array([0,0,0,1],np.uint16);patches=np.array([0,0,1,2],np.uint32)
        np.testing.assert_array_equal(region_mask(face_map,palette,patches,'color',0),[[True,True,False],[True,False,False]])
        np.testing.assert_array_equal(region_mask(face_map,palette,patches,'patch',1),[[False,False,False],[True,False,False]])
        with self.assertRaises(ValueError):validate_edits({'regions':[{'kind':'patch','id':-1,'prompt':'cloth'}]},2,3)
        with self.assertRaises(ValueError):validate_edits({'regions':[{'kind':'color','id':9,'prompt':'cloth'}]},2,3)

    def test_low_resolution_guide_does_not_replace_full_resolution_colors(self):
        from material_regions import make_color_guide
        source=Image.fromarray(np.arange(48*32*3,dtype=np.uint8).reshape(32,48,3))
        original=np.array(source).copy();guide=make_color_guide(source,16)
        self.assertEqual(guide.size,(16,16));np.testing.assert_array_equal(np.array(source),original)

if __name__=='__main__':unittest.main()

class PaletteGroupingTests(unittest.TestCase):
    def test_nearly_identical_shades_form_one_region(self):
        from material_regions import build_regions
        pixels=np.full((32,32,3),[240,100,16],np.uint8);pixels[:,16:]=[236,96,15]
        mesh=trimesh.Trimesh(vertices=[[0,0,0],[1,0,0],[1,1,0],[0,1,0]],faces=[[0,1,2],[0,2,3]],process=False)
        mesh.visual=trimesh.visual.TextureVisuals(uv=np.array([[0,0],[1,0],[1,1],[0,1]]),material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(pixels)))
        _,labels,_,_=build_regions(mesh,32,8)
        self.assertEqual(len(np.unique(labels)),1)

class FullResolutionRegionTests(unittest.TestCase):
    def test_regions_sample_original_color_even_when_preview_downsampling_blends_islands(self):
        from material_regions import build_regions
        pixels=np.zeros((128,128,3),np.uint8)
        pixels[20:22,20:22]=[240,100,16];pixels[100:102,100:102]=[20,180,40]
        vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[3,0,0],[4,0,0],[3,1,0]])
        mesh=trimesh.Trimesh(vertices=vertices,faces=[[0,1,2],[3,4,5]],process=False)
        uv=np.array([[20.5/127,1-20.5/127]]*3+[[100.5/127,1-100.5/127]]*3)
        mesh.visual=trimesh.visual.TextureVisuals(uv=uv,material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(pixels)))
        _,labels,_,meta=build_regions(mesh,8,4)
        first=next(r for r in meta['regions'] if r['id']==labels[0])
        self.assertGreater(first['rgb'][0],200)
        self.assertLess(first['rgb'][2],40)

class PaintedRegionTests(unittest.TestCase):
    def test_manual_face_selection_only_changes_selected_triangles(self):
        from material_regions import region_mask,validate_edits
        fmap=np.array([[1,2,3],[4,0,5]],np.uint32)
        colors=np.array([0,0,0,0,0],np.uint16);patches=np.arange(5,dtype=np.uint32)
        edit={'regions':[{'kind':'faces','id':0,'prompt':'Glossy eyes','face_ranges':[[1,3],[4,5]]}]}
        validate_edits(edit,1,5,faces=5)
        result=region_mask(fmap,colors,patches,'faces',0,face_ranges=[[1,3],[4,5]])
        np.testing.assert_array_equal(result,[[False,True,True],[False,False,True]])
        with self.assertRaises(ValueError):validate_edits({'regions':[{'kind':'faces','id':0,'prompt':'cloth','face_ranges':[[0,999]]}]},1,5,faces=5)

class MaterialLayoutDefaultTests(unittest.TestCase):
    def test_missing_gltf_color_factor_is_the_valid_white_default(self):
        import importlib.util
        from unittest.mock import patch
        spec=importlib.util.spec_from_file_location('owned_material_worker',Path(__file__).parents[1]/'pipeline_workers/material_stage_worker.py')
        worker=importlib.util.module_from_spec(spec);spec.loader.exec_module(worker)
        class PastLayoutCheck(Exception):pass
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp);mesh=trimesh.creation.box()
            mesh.visual=trimesh.visual.TextureVisuals(uv=np.zeros((len(mesh.vertices),2)),material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.new('RGBA',(4,4),(80,30,150,255)),metallicRoughnessTexture=Image.new('RGB',(4,4),(0,100,0)),metallicFactor=1,roughnessFactor=1))
            source=folder/'source.glb';mesh.export(source)
            with patch.object(worker,'build_regions',side_effect=PastLayoutCheck):
                with self.assertRaises(PastLayoutCheck):worker.prepare({'folder':str(folder/'session'),'mesh':str(source),'guide_size':32,'palette_count':4})
