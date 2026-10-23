"""Camera contracts independent of the GPU renderer."""
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("workshop_camera", Path(__file__).parents[1] / "camera_guides.py")
camera = importlib.util.module_from_spec(spec)
spec.loader.exec_module(camera)


class CameraGuideTests(unittest.TestCase):
    draft = {"bounds_min": [-.2, -.5, -.1], "bounds_max": [.2, .5, .1]}

    def test_reconstruction_projection_keeps_exact_render_frame_and_pole_roll(self):
        # The render target must land at the image centre after the glTF->Pixal
        # conversion, including nonzero mesh-centre offsets and vertical views.
        draft={"bounds_min":[-.1,-.4,0],"bounds_max":[.3,.6,.2]}
        for azimuth,elevation in ((0,0),(90,0),(180,-30),(45,60),(0,90),(0,-90)):
            c=camera.orbit(draft,{"azimuth":azimuth,"elevation":elevation,"fov":20})
            matrix=camera.pixal_camera(c)
            target=[c["target"][0],-c["target"][2],c["target"][1]]
            relative=[target[i]-matrix[i][3] for i in range(3)]
            local=[sum(relative[i]*matrix[i][axis] for i in range(3)) for axis in range(3)]
            self.assertAlmostEqual(local[0],0);self.assertAlmostEqual(local[1],0)
            self.assertAlmostEqual(local[2],-c["distance"])
            for axis in range(3):
                self.assertAlmostEqual(sum(matrix[i][axis]**2 for i in range(3)),1)
        front=camera.pixal_camera(camera.orbit(self.draft,{"azimuth":0,"elevation":0,"fov":20}))
        self.assertEqual([row[:3] for row in front[:3]],[[1,0,0],[0,0,-1],[0,1,0]])

    def test_front_right_back_left_match_pixal_y_up_coordinates(self):
        expected = [(0, 0, 1), (-1, 0, 0), (0, 0, -1), (1, 0, 0)]
        for azimuth, direction in zip((0, 90, 180, 270), expected):
            record = camera.orbit(self.draft, {"azimuth": azimuth, "elevation": 0, "fov": 20})
            for actual, wanted in zip(record["position"], direction):
                self.assertAlmostEqual(actual / record["distance"], wanted)

    def test_fixed_sphere_framing_fits_every_corner_at_poles_and_oblique_angles(self):
        for elevation in (-90, -45, 0, 45, 90):
            record = camera.orbit(self.draft, {"azimuth": 45, "elevation": elevation, "fov": 20})
            self.assertTrue(all(math.isfinite(v) for v in record["position"]))
            self.assertLess(math.asin(record["radius"] / record["distance"]), math.radians(10))
            self.assertEqual(record["target"], [0, 0, 0])
            self.assertEqual(record["size"], [1024, 1024])
            self.assertFalse(record["crop"])

    def test_invalid_bounds_or_projection_are_rejected_before_render(self):
        for draft, fov in ((self.draft, 0), (self.draft, float("nan")),
                           ({"bounds_min": [0, 0, 0], "bounds_max": [0, 0, 0]}, 20)):
            with self.assertRaises(ValueError):
                camera.orbit(draft, {"azimuth": 0, "elevation": 0, "fov": fov})


if __name__ == "__main__":
    unittest.main()
