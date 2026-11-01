import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('catalog_test', Path(__file__).parents[1] / 'lora_catalog.py')
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def tensor(shape):
    return {'shape': shape, 'dtype': 'BF16'}


class LoRACatalogTests(unittest.TestCase):
    def test_sdxl_cannot_be_offered_as_flux(self):
        header = {'__metadata__': {'ss_base_model_version': 'sdxl_base_v0-9'},
                  'lora_unet_input_blocks_1.lora_down.weight': tensor([16, 320])}
        self.assertEqual(catalog.identify(header), ['sdxl_base', 'sdxl_juggernaut'])
        self.assertEqual(catalog.identify(header, {'profile': 'klein4', 'family': 'klein4'}), [])

    def test_klein_fused_shapes_distinguish_4b_9b_and_flux1(self):
        key = 'transformer.single_transformer_blocks.0.attn.to_out.lora_A.weight'
        self.assertEqual(catalog.identify({key: tensor([16, 12288])}), ['klein4', 'klein4_base'])
        self.assertEqual(catalog.identify({key: tensor([16, 16384])}), ['klein_base', 'klein_distilled', 'klein_kv'])
        self.assertEqual(catalog.identify({key: tensor([16, 3072])}), [])
        # Klein's dual-stream attention uses a similar name to Qwen.
        self.assertEqual(catalog.identify({key: tensor([16, 12288]),
            'transformer.transformer_blocks.0.attn.to_q.lora_A.weight': tensor([16, 3072])}), ['klein4', 'klein4_base'])

    def test_qwen_versions_are_not_interchangeable(self):
        key = 'transformer.transformer_blocks.0.attn.to_q.lora_A.weight'
        self.assertEqual(catalog.identify({key: tensor([16, 3072])}), [], 'Generic attention alone is ambiguous')
        header = {key: tensor([16, 3072]), 'transformer.transformer_blocks.0.img_mlp.net.0.proj.lora_A.weight': tensor([16, 3072])}
        self.assertEqual(catalog.identify(header), ['qwen2511'])
        header = {key: tensor([16, 4096]), '__metadata__': {'ss_base_model_version': 'qwen_image_2'}}
        self.assertEqual(catalog.identify(header), ['qwen21'])

    def test_base_and_installed_source_restrictions_are_retained(self):
        header = {'__metadata__': {'ss_base_model_version': 'flux2_klein_base_4b'},
                  'diffusion_model.double_blocks.0.img_attn.proj.lora_A.weight': tensor([16, 3072])}
        self.assertEqual(catalog.identify(header), ['klein4_base'])
        self.assertEqual(catalog.identify(header, {'profile': 'klein4', 'family': 'klein4'}), [])
        header['__metadata__']['ss_base_model_version'] = 'flux2_klein_4b'
        self.assertEqual(catalog.identify(header, {'profile': 'klein4', 'family': 'klein4'}), ['klein4'])

    def test_unknown_conflicting_and_non_adapter_files_are_hidden(self):
        self.assertEqual(catalog.identify({'weight': tensor([16, 3072])}), [])
        self.assertEqual(catalog.identify({'mystery.lora_A.weight': tensor([16, 3072])}), [])
        self.assertEqual(catalog.identify({'__metadata__': {'ss_base_model_version': 'sdxl'},
            'single_transformer_blocks.0.attn.to_out.lora_A.weight': tensor([16, 12288])}), [])

    def test_file_replacement_changes_cache_key_and_legacy_files_stay_hidden(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'anything.safetensors'
            path.write_bytes(b'first')
            with patch.object(catalog, '_inspect', return_value=['klein4']) as inspect:
                self.assertEqual(catalog.entry(path, path.name)['profiles'], ['klein4'])
                first = inspect.call_args.args
                path.write_bytes(b'replacement')
                catalog.entry(path, path.name)
                self.assertNotEqual(first, inspect.call_args.args)
                self.assertEqual(catalog.entry(path.with_suffix('.pt'), 'flux.pt')['profiles'], [])


if __name__ == '__main__':
    unittest.main()
