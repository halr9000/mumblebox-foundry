import importlib.util
from pathlib import Path
import unittest

import numpy as np
import trimesh


ROOT = Path(__file__).parents[1] / "pipeline_workers"


class ZeroEdgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('runtime', ROOT / 'trellis_bridge_runtime.py')
        cls.runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runtime)

    def test_collapses_connected_zero_edge_without_welding_touching_components(self):
        self.assertTrue(hasattr(self.runtime, 'clean_zero_edges'))
        v = np.array([[1,0,0],[-1,0,0],[1,0,0],[0,-1,0],[0,0,1],[0,0,-1],
                      [1,0,0],[2,0,0],[1,1,0],[1,0,1]], dtype=np.float32)
        f = np.array([[0,2,4],[2,1,4],[1,3,4],[3,0,4],
                      [2,0,5],[1,2,5],[3,1,5],[0,3,5],
                      [6,8,7],[6,7,9],[6,9,8],[7,8,9]])
        before_v, before_f = v.copy(), f.copy()
        out_v, out_f, report = self.runtime.clean_zero_edges(v, f)
        nonzero = np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]], v[f[:,2]]-v[f[:,0]]),axis=1)>0
        np.testing.assert_array_equal(out_v[out_f], v[f[nonzero]])
        self.assertEqual(report['collapsed_zero_edges'], 1)
        self.assertEqual(report['removed_zero_area_faces'], 2)
        self.assertEqual(len(out_v)-len(np.unique(out_v,axis=0)), 1)
        self.assertTrue(trimesh.Trimesh(out_v,out_f,process=False).is_watertight)
        np.testing.assert_array_equal(v,before_v)
        np.testing.assert_array_equal(f,before_f)

    def test_rejects_nonmanifold_edge_instead_of_merging_it(self):
        self.assertTrue(hasattr(self.runtime, 'clean_zero_edges'))
        v=np.array([[0,0,0],[0,0,0],[1,0,0],[0,1,0],[0,0,1]],dtype=np.float32)
        f=np.array([[0,1,2],[1,0,3],[0,1,4]])
        with self.assertRaisesRegex(ValueError,'manifold'):
            self.runtime.clean_zero_edges(v,f)

    def test_clean_mesh_is_unchanged(self):
        self.assertTrue(hasattr(self.runtime, 'clean_zero_edges'))
        mesh=trimesh.creation.icosphere(subdivisions=1)
        v,f,report=self.runtime.clean_zero_edges(mesh.vertices,mesh.faces)
        np.testing.assert_array_equal(v,mesh.vertices)
        np.testing.assert_array_equal(f,mesh.faces)
        self.assertEqual(report['collapsed_zero_edges'],0)


if __name__=='__main__':
    unittest.main()
