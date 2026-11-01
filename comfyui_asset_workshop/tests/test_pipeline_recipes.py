import copy
import importlib
import unittest
from unittest.mock import patch
from test_reference_pair import recipes,store
class PipelineGraphTests(unittest.TestCase):
    def test_shape_only_graph_has_checkpoint_and_no_texture(self):
        asset={"id":"p1","settings":{**store.default_settings(),"mesh_backend":"pixal_single"}}
        with patch.object(recipes,"preparation",return_value=([("mesh_input",{"id":"img"}, {})],[["1",0]],[],[])),patch.object(recipes,"source_fov",return_value=("manual",40)):
            try:g,_,_=recipes.mesh_recipe(asset,{"id":"stage1"},geometry_only=True)
            except TypeError:self.fail("Shape-only reconstruction recipe is required")
        kinds=[n["class_type"] for n in g.nodes.values()]
        self.assertIn("AW_SaveGeometry",kinds)
        self.assertNotIn("Trellis2TextureStage",kinds)
        self.assertNotIn("AW_SaveMaster",kinds)
    def test_texture_recipe_binds_one_selected_geometry(self):
        module=importlib.import_module("_aw_pair_contract.pipeline_recipes")
        p={"id":"p1","pipeline":{"settings":{},"selected_geometry_id":"g1"},"artifacts":[{"id":"g1","kind":"geometry","geometry_stage":"clean","file":"g.npz","sha256":"abc"}]}
        snap=copy.deepcopy(p)
        r=module.build_stage_recipe(p,snap,{"id":"stage1","name":"texture"},{"payload":{}})
        types=[n["class_type"] for n in r["graph"].values()]
        self.assertEqual(types,["AW_TextureSaved","Preview3DAdvanced"])
        node=next(iter(r["graph"].values()))
        self.assertEqual(node["inputs"]["source_id"],"g1")
        p["artifacts"][0]["stale"]=True
        with self.assertRaises(ValueError):module.build_stage_recipe(p,snap,{"id":"stage1","name":"texture"},{"payload":{}})

    def test_variant_bakes_match_saved_texture_not_pending_next_run_settings(self):
        module=importlib.import_module("_aw_pair_contract.pipeline_recipes")
        p={"id":"p1","pipeline":{"settings":{"texture_size":2048},"selected_texture_id":"t1"},"artifacts":[{"id":"t1","kind":"mesh","geometry_id":"g1","texture_size":4096}]}
        result=module.build_stage_recipe(p,copy.deepcopy(p),{"id":"stage1","name":"variant"},{"payload":{}})
        bake=next(n for n in result["graph"].values() if n["class_type"]=="BakeNormalMapFromMesh")
        self.assertEqual(bake['inputs']['resolution'],4096)

    def test_existing_variant_and_detailed_master_are_reused_without_optimization(self):
        module=importlib.import_module("_aw_pair_contract.pipeline_recipes")
        p={"id":"p1","pipeline":{"settings":{},"selected_texture_id":"t1"},"artifacts":[{"id":"t1","kind":"mesh","geometry_id":"g1","variant":"detailed"},{"id":"low1","kind":"mesh","parent_artifact_id":"t1","appearance_stage":"variant","variant":"balanced_250k"}]}
        for variant,aid in [('detailed','t1'),('balanced_250k','low1')]:
            result=module.build_stage_recipe(p,copy.deepcopy(p),{'id':'stage1','name':'variant'},{'payload':{'variant':variant}})
            nodes=list(result['graph'].values())
            self.assertEqual(nodes[0]['class_type'],'AW_UseSavedStage')
            self.assertEqual(nodes[0]['inputs']['artifact_id'],aid)
            self.assertNotIn('AW_OptimizeSaved',[n['class_type'] for n in nodes])
