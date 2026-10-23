"""Native patch matching must fail clearly and report what actually applied."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("checked_lora", Path(__file__).parents[1] / "lora_compatibility.py")
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)


class PatchModel:
    def __init__(self, applied=("layer1", "layer2")):
        self.model = object()
        self.applied = applied
        self.weights = {"original": "unchanged"}

    def clone(self):
        return PatchModel(self.applied)

    def add_patches(self, patches, strength):
        self.weights = dict(patches)
        return self.applied


class CheckedLoRALoadingTests(unittest.TestCase):
    def setUp(self):
        native = types.ModuleType("comfy")
        native.__path__ = []
        native.lora = types.ModuleType("comfy.lora")
        native.lora_convert = types.ModuleType("comfy.lora_convert")
        native.model_base = types.ModuleType("comfy.model_base")
        native.model_base.Flux3 = type("Flux3", (), {})
        native.lora.model_lora_keys_unet = lambda model, mapping: {"layer1": "target1", "layer2": "target2"}
        native.lora.load_lora = lambda weights, mapping: weights
        native.lora_convert.convert_lora = lambda weights: weights
        self.external = patch.dict(sys.modules, {"comfy": native, "comfy.lora": native.lora,
            "comfy.lora_convert": native.lora_convert, "comfy.model_base": native.model_base})
        self.external.start()
        self.addCleanup(self.external.stop)

    def test_zero_strength_keeps_original_model_and_reports_disabled(self):
        model, report = PatchModel(), {}
        self.assertIs(compatibility.load_checked(model, {}, 0, report=report), model)
        self.assertEqual(report["status"], "disabled")

    def test_zero_or_partial_invalid_patch_fails(self):
        with self.assertRaisesRegex(ValueError, "did not match"):
            compatibility.load_checked(PatchModel(), {}, 1)
        with self.assertRaisesRegex(ValueError, "Only part"):
            compatibility.load_checked(PatchModel(("layer1",)), {"layer1": 1, "layer2": 2}, 1)

    def test_success_reports_counts_and_does_not_mutate_original_model(self):
        model, report = PatchModel(), {}
        result = compatibility.load_checked(model, {"layer1": 1, "layer2": 2}, .8, report=report)
        self.assertIsNot(result, model)
        self.assertEqual(model.weights, {"original": "unchanged"})
        self.assertEqual(report, {"status": "matched_weights", "matched_patches": 2,
                                 "applied_patches": 2, "visual_compatibility": "not_verified"})


if __name__ == "__main__":
    unittest.main()
