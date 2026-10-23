"""Both native SDXL LoRA patch destinations must be retained and reported."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sdxl_lora_boundary', Path(__file__).parents[1] / 'lora_compatibility.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Patcher:
    def __init__(self, prefix):
        self.prefix = prefix
        self.model = self.cond_stage_model = self.patcher = self
        self.applied = {}

    def clone(self):
        return Patcher(self.prefix)

    def add_patches(self, weights, strength):
        matched = [key for key in weights if key.startswith(self.prefix)]
        self.applied.update({key: strength for key in matched})
        return matched

    def set_attachments(self, *args):
        pass


class SDXLLoRALoadingTests(unittest.TestCase):
    def run_loader(self, weights, model_strength=.8, clip_strength=.4):
        lora = types.ModuleType('comfy.lora')
        lora.model_lora_keys_unet = lambda model, keys: {**keys, 'unet': 'model.weight'}
        lora.model_lora_keys_clip = lambda model, keys: {**keys, 'text_encoder': 'clip.weight'}
        lora.load_lora = lambda values, keys: values
        convert = types.ModuleType('comfy.lora_convert')
        convert.convert_lora = lambda values: values
        comfy = types.ModuleType('comfy')
        comfy.lora, comfy.lora_convert = lora, convert
        model, clip, report = Patcher('model.'), Patcher('clip.'), {}
        with patch.dict(sys.modules, {'comfy': comfy, 'comfy.lora': lora, 'comfy.lora_convert': convert}):
            result = module.load_checked_sdxl(model, clip, weights, model_strength, clip_strength, report=report)
        return result, report, model, clip

    def test_model_and_clip_weights_receive_their_separate_strengths(self):
        (model, clip), report, original_model, original_clip = self.run_loader({'model.weight': 'a', 'clip.weight': 'b'})
        self.assertEqual(model.applied, {'model.weight': .8})
        self.assertEqual(clip.applied, {'clip.weight': .4})
        self.assertEqual((report['model_patches'], report['clip_patches']), (1, 1))
        self.assertFalse(original_model.applied)
        self.assertFalse(original_clip.applied)

    def test_clip_only_lora_is_valid_with_model_strength_zero(self):
        (model, clip), report, _, _ = self.run_loader({'clip.weight': 'b'}, 0, .5)
        self.assertFalse(model.applied)
        self.assertEqual(clip.applied, {'clip.weight': .5})
        self.assertEqual(report['applied_patches'], 1)

    def test_unmatched_weights_are_rejected_instead_of_reported_as_loaded(self):
        with self.assertRaises(ValueError):
            self.run_loader({'other_architecture.weight': 'x'})


if __name__ == '__main__':
    unittest.main()
