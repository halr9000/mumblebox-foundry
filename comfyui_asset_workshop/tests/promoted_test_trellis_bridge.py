import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).parents[1] / "pipeline_workers"


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'trellis_bridge_runtime.py'
        if path.exists():
            spec = importlib.util.spec_from_file_location('bridge_runtime', path)
            cls.runtime = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.runtime)
        else:
            cls.runtime = None

    def test_restores_upstream_normalization_on_asymmetric_object(self):
        self.assertIsNotNone(self.runtime, 'TRELLIS bridge runtime is missing')
        points = np.array([[3., -4., 8.], [7., -4., 8.], [4., -1., 8.], [5., -3., 10.]])
        frame = self.runtime.mesh_frame(points)
        # TRELLIS postprocessing has already reversed its Y/Z axis conversion.
        normalized = (points - frame['center']) * frame['scale']
        np.testing.assert_allclose(self.runtime.restore_vertices(normalized, frame), points)

    def test_texture_reference_uses_alpha_instead_of_hidden_background_rgb(self):
        from PIL import Image
        self.assertTrue(hasattr(self.runtime, 'texture_reference_rgb'))
        source = Image.fromarray(np.array([[[255, 0, 0, 0], [0, 0, 255, 255],
                                           [255, 0, 0, 128]]], dtype=np.uint8))
        prepared = self.runtime.texture_reference_rgb(source)
        np.testing.assert_array_equal(np.asarray(prepared), [[[0, 0, 0], [0, 0, 255], [128, 0, 0]]])
        self.assertEqual(prepared.mode, 'RGB')
        self.assertEqual(source.getpixel((0, 0)), (255, 0, 0, 0))

    def test_worker_failure_reports_saved_error(self):
        self.assertIsNotNone(self.runtime, 'TRELLIS bridge runtime is missing')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, 'specific-worker-error'):
                self.runtime.run_worker([sys.executable, '-c', 'raise RuntimeError("specific-worker-error")'], Path(temp) / 'worker.log', lambda: None)

    def test_cancellation_terminates_owned_worker(self):
        self.assertIsNotNone(self.runtime, 'TRELLIS bridge runtime is missing')
        with tempfile.TemporaryDirectory() as temp:
            def cancel():
                raise InterruptedError('cancelled')
            with self.assertRaises(InterruptedError):
                self.runtime.run_worker([sys.executable, '-c', 'import time;time.sleep(30)'], Path(temp) / 'worker.log', cancel)


if __name__ == '__main__':
    unittest.main()
