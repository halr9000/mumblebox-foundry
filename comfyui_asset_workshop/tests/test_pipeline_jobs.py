import importlib
import unittest
from test_reference_pair import store
class PipelineJobTests(unittest.TestCase):
    def test_geometry_flow_and_standalone_operations_share_stages(self):
        m=importlib.import_module("_aw_pair_contract.jobs")
        stages=m.JobCoordinator.stages("build_geometry",{},"job1")
        self.assertEqual([s["name"] for s in stages],["reference_view"]*4+["prepare","geometry","refine","cleanup"])
        for kind,name in {"texture_mesh":"texture","prepare_variant":"variant","prepare_material_guide":"material_guide","apply_materials":"materials"}.items():
            self.assertIn(kind,m.KINDS)
            self.assertEqual(m.JobCoordinator.stages(kind,{},"job2")[0]["name"],name)
