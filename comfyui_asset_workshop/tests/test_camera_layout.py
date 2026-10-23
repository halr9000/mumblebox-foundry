"""Quarter-view instructions must agree with the native Pixal camera basis."""
import ast
from pathlib import Path
import unittest

tree = ast.parse((Path(__file__).parents[1] / "description_helper.py").read_text(encoding="utf-8"))
scope = {}
exec(compile(ast.Module(body=[node for node in tree.body
                             if isinstance(node, ast.FunctionDef) and node.name == "side_prompt"],
                        type_ignores=[]), "side_prompt", "exec"), scope)


class CameraLayoutTests(unittest.TestCase):
    def test_screen_order_matches_native_orbit(self):
        # Native front=(0,-1,0), right=(-1,0,0); UI azimuth is negated
        # before _orbit_camera_to_world. Project face centers onto its
        # right vector to obtain these screen-left / screen-right pairs.
        expected = {45: ("right", "front"), 135: ("back", "right"),
                    225: ("left", "back"), 315: ("front", "left")}
        parts = dict.fromkeys(("identity", "front", "back", "left", "right", "top", "underside", "pose"), "")
        parts.update(identity="test object", front="screen", back="vents", left="connector", right="panel")
        for azimuth, (left, right) in expected.items():
            with self.subTest(azimuth=azimuth):
                prompt = scope["side_prompt"](parts, {"azimuth": azimuth, "elevation": 0})
                self.assertIn(f"the object's {left} face on the LEFT of the picture", prompt)
                self.assertIn(f"the object's {right} face on the RIGHT", prompt)

    def test_polar_views_do_not_get_quarter_layout(self):
        parts = dict.fromkeys(("identity", "front", "back", "left", "right", "top", "underside", "pose"), "")
        for elevation in (-90, 90):
            prompt = scope["side_prompt"](parts, {"azimuth": 45, "elevation": elevation})
            self.assertNotIn("LEFT of the picture", prompt)


if __name__ == "__main__":
    unittest.main()
