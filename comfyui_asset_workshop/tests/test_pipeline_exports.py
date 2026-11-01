import importlib
import unittest
from test_reference_pair import store
class PipelineProvenanceTests(unittest.TestCase):
    def test_pipeline_provenance_survives_without_machine_paths(self):
        m=importlib.import_module("_aw_pair_contract.package_export")
        recipe={"pipeline_version":"validated_v1","texture_provider":"trellis2","variant":"balanced_250k","material_model":"gvecchio/StableMaterials","material_model_revision":"pinned","settings":{"texture_steps":20,"material_steps":4,"worker_python":"C:/private/python.exe"},"optimization":{"target_triangles":250000,"source_texture":"C:/private/secret.glb","seconds":5},"material_assignments":{"regions":[{"kind":"faces","id":0,"prompt":"cotton","face_ranges":[[0,10]]}]}}
        result=m.recipe_parameters(recipe)
        self.assertEqual(result.get("texture_provider"),"trellis2")
        self.assertEqual(result["settings"].get("texture_steps"),20)
        self.assertEqual(result["optimization"]["target_triangles"],250000)
        self.assertNotIn("source_texture",result["optimization"])
        self.assertNotIn("worker_python",result["settings"])
