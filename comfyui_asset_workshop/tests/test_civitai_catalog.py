import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('civitai_catalog', ROOT / 'civitai_catalog.py')
catalog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = catalog
spec.loader.exec_module(catalog)


def resource(kind='LORA', base='SDXL 1.0'):
    return {'id': 10, 'name': 'Example', 'type': kind, 'description': '<p>Use <b>example</b>.</p>',
            'modelVersions': [{'id': 20, 'name': 'v1', 'baseModel': base, 'trainedWords': ['example'],
                'files': [{'id': 30, 'name': 'weights.safetensors', 'type': 'Model', 'sizeKB': 1024,
                    'metadata': {'format': 'SafeTensor'}, 'hashes': {'SHA256': 'a' * 64},
                    'downloadUrl': 'https://civitai.com/api/download/models/20?token=do-not-retain&fileId=30'}]}]}


class CatalogTests(unittest.TestCase):
    def test_lora_weight_file_category_model_is_accepted(self):
        result = catalog.resolve_file(resource(), 20, 30, 'sdxl_base', 'LORA')
        self.assertEqual(result['family'], 'sdxl')
        self.assertEqual(result['file_id'], 30)
        self.assertNotIn('token', result['download_url'])
        self.assertEqual(result['category'], 'loras')

    def test_checkpoint_cannot_be_imported_through_lora_route(self):
        with self.assertRaises(catalog.CivitaiError):
            catalog.resolve_file(resource('Checkpoint'), 20, 30, 'sdxl_base', 'LORA')

    def test_wrong_variant_is_rejected_even_when_filename_looks_right(self):
        with self.assertRaises(catalog.CivitaiError):
            catalog.resolve_file(resource(base='Flux.2 Klein 9B'), 20, 30, 'klein4', 'LORA')

    def test_base_checkpoint_family_is_explicit(self):
        result = catalog.resolve_file(resource('Checkpoint'), 20, 30, 'sdxl_juggernaut', 'Checkpoint')
        self.assertEqual(result['category'], 'checkpoints')

    def test_a_version_or_file_from_another_resource_is_rejected(self):
        for version, file in [(21, 30), (20, 31)]:
            with self.assertRaises(catalog.CivitaiError):
                catalog.resolve_file(resource(), version, file, 'sdxl_base', 'LORA')

    def test_unverified_file_hash_or_archive_cannot_be_installed(self):
        for change in [{'hashes': {}}, {'name': 'archive.zip', 'metadata': {'format': 'Other'}}]:
            data = resource()
            data['modelVersions'][0]['files'][0].update(change)
            with self.assertRaises(catalog.CivitaiError):
                catalog.resolve_file(data, 20, 30, 'sdxl_base', 'LORA')

    def test_external_url_and_embedded_credentials_are_rejected(self):
        for url in ['https://evil.example/civitai.com/models/10', 'http://civitai.com/models/10',
                    'https://user:password@civitai.com/models/10']:
            with self.assertRaises(catalog.CivitaiError):
                catalog.parse_resource_url(url)
        self.assertEqual(catalog.parse_resource_url('https://civitai.red/models/10?modelVersionId=20'),
                         {'model_id': 10, 'version_id': 20})

    def test_current_qwen_label_is_not_confused_with_edit_model(self):
        self.assertTrue(catalog.compatible('qwen21', 'Qwen 2.1'))
        self.assertFalse(catalog.compatible('qwen2511', 'Qwen 2.1'))
        self.assertFalse(catalog.compatible('qwen2511', 'Qwen'))

    def test_remote_description_is_plain_text(self):
        self.assertEqual(catalog.plain_text('<p>Hello</p><script>steal()</script><p>World</p>'), 'Hello\nWorld')

    def test_http_errors_have_specific_recovery_without_raw_secrets(self):
        for status, kind in [(401, 'authentication'), (403, 'access'), (429, 'limit'), (503, 'service')]:
            error = catalog.http_error(status)
            self.assertEqual(error.kind, kind)
            self.assertTrue(error.message)


if __name__ == '__main__':
    unittest.main()
