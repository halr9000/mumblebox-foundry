"""Contracts that prevent wrong settings, references and selected branches reaching Comfy."""
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

class WizardContracts(unittest.TestCase):
    def module(self, name):
        try:
            return __import__("foundry.workflows.image_to_3d." + name, fromlist=["*"])
        except ModuleNotFoundError:
            self.fail("The image-to-3D " + name + " contract is not implemented")

    def test_explicit_overrides_win_without_mutating_defaults(self):
        d = self.module("definition")
        effective = d.resolve_settings("default", {"refine_seed": 0, "cpu_offload": False})
        self.assertEqual(effective["refine_seed"], 0)
        self.assertFalse(effective["cpu_offload"])
        self.assertEqual(d.resolve_settings("default", {})["refine_seed"], 42)
        with self.assertRaises(ValueError):
            d.resolve_settings("low", {})
        with self.assertRaises(ValueError):
            d.resolve_settings("default", {"refine_resolution": 999})

    def test_reference_labels_follow_actual_order_after_deletion(self):
        p = self.module("prompts")
        refs = [{"id": "whole", "filename": "whole.png", "role": "primary", "description": ""},
                {"id": "rear", "filename": "rear.png", "role": "back", "description": "Rear of the same asset"}]
        result = p.bind_references("characters", refs)
        self.assertEqual(result["bindings"], {"image1": "whole.png", "image2": "rear.png"})
        self.assertIn("<image2>", result["prompt"])
        self.assertIn("Rear of the same asset", result["prompt"])
        primary_only = p.bind_references("characters", refs[:1])
        self.assertEqual(primary_only["prompt"], p.CHARACTER_PROMPT)
        with self.assertRaises(ValueError):
            p.bind_references("characters", [])
        with self.assertRaises(ValueError):
            p.bind_references("characters", refs[:1] * 11)

    def test_output_closure_omits_unselected_output_node(self):
        g = self.module("graph")
        prompt = {"1": {"class_type": "LoadImage", "inputs": {"image": "a.png"}},
                  "2": {"class_type": "PreviewImage", "inputs": {"images": ["1", 0]}},
                  "3": {"class_type": "ExpensiveQuads", "inputs": {"mesh": ["1", 0]}}}
        result = g.ancestor_prompt(prompt, ["2"])
        self.assertEqual(set(result), {"1", "2"})
        self.assertEqual(set(prompt), {"1", "2", "3"})
        result["1"]["inputs"]["image"] = "b.png"
        self.assertEqual(prompt["1"]["inputs"]["image"], "a.png")


    def test_stage_compiler_skips_models_for_print_and_packages_only_selected(self):
        g = self.module("graph")
        d = self.module("definition")
        run = {"id": "a"*32, "name": "Alien", "slug": "alien", "category": "characters",
               "references": [{"id":"a","filename":"alien.png","role":"primary","description":""}],
               "settings": d.resolve_settings("default", {}),
               "selection": {"schema":"mumblebox.export-selection/1","variants":{"print":{"formats":["stl"]}}},
               "checkpoints": {"clean":"C:/output/clean.glb", "print":"C:/output/print.stl",
                               "front":"views/front.png [output]", "decoded":"C:/output/decoded.glb",
                               "left":"views/left.png [output]", "back":"views/back.png [output]", "right":"views/right.png [output]"}}
        self.assertIn("2003", g.compile_stage("refinement", run))
        self.assertIn("2015", g.compile_stage("refinement", run))
        self.assertIn("2023", g.compile_stage("texture", run))
        print_graph = g.compile_stage("print", run)
        classes = {n["class_type"] for n in print_graph.values()}
        self.assertNotIn("Hi3DRefine", classes)
        self.assertNotIn("Hi3DTrellis2TextureMesh", classes)
        self.assertNotIn("UNETLoader", classes)
        package = g.compile_stage("package", run)
        self.assertEqual(set(package), {"3010"})
        self.assertEqual(package["3010"]["inputs"]["saved_print"], "C:/output/print.stl")
        geometry = g.compile_stage("geometry", run)
        self.assertNotIn("1574", geometry)
        self.assertEqual(geometry["324"]["inputs"]["front"], ["9101", 0])
        self.assertEqual(geometry["9101"]["inputs"]["image"], "views/front.png [output]")

    def test_default_profile_is_saved_and_future_profiles_are_rejected(self):
        import tempfile
        from foundry.preferences import Preferences
        with tempfile.TemporaryDirectory() as temp:
            preferences = Preferences(Path(temp) / "preferences.json")
            self.assertEqual(preferences.read()["profile"], "default")
            preferences.update({"profile":"default", "theme":"light"})
            self.assertEqual(preferences.read()["theme"], "light")
            with self.assertRaises(ValueError):
                preferences.update({"profile":"high"})

if __name__ == "__main__":
    unittest.main()
