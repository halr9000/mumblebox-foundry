import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
import json
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType('aw_civitai_download_test')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
for name in ('civitai_catalog', 'civitai_downloads'):
    spec = importlib.util.spec_from_file_location(package.__name__ + '.' + name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
Downloader = module.Downloader


class Response:
    def __init__(self, data, status=200, headers=None):
        self.data, self.status_code = data, status
        self.headers = headers or {'Content-Length': str(len(data)), 'Content-Type': 'application/octet-stream'}
    def close(self): pass
    def iter_content(self, chunk_size):
        for i in range(0, len(self.data), 64): yield self.data[i:i+64]


class Transport:
    def __init__(self, data): self.data, self.calls = data, []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        offset = int(kwargs['headers'].get('Range', 'bytes=0-')[6:-1])
        headers = {'Content-Length': str(len(self.data)-offset), 'Content-Type': 'application/octet-stream'}
        if offset: headers['Content-Range'] = f'bytes {offset}-{len(self.data)-1}/{len(self.data)}'
        return Response(self.data[offset:], 206 if offset else 200, headers)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = b'validated test weights' * 100
        self.transport = Transport(self.data)
        self.descriptor = {'model_id': 1, 'version_id': 2, 'file_id': 3, 'profile': 'sdxl_base',
            'family': 'sdxl', 'kind': 'LORA', 'category': 'loras', 'name': 'same-name.safetensors',
            'model_name': 'Example', 'version_name': 'v1', 'base_model': 'SDXL 1.0',
            'size_bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest(),
            'download_url': 'https://civitai.com/api/download/models/2?fileId=3',
            'source_url': 'https://civitai.com/models/1?modelVersionId=2', 'triggers': ['example'],
            'notes': '', 'permissions': {}}
        self.manager = Downloader(self.root, lambda **args: dict(self.descriptor), lambda: None,
                                  threading.Lock(), self.transport, lambda path, item: None)

    def start(self):
        self.manager.start({'model_id': 1, 'version_id': 2, 'file_id': 3, 'profile': 'sdxl_base', 'kind': 'LORA'})
        self.manager.worker.join(3)
        self.assertFalse(self.manager.worker.is_alive())
        return self.manager.status()

    def test_verified_download_is_published_and_indexed(self):
        result = self.start()
        self.assertEqual(result['status'], 'completed', result)
        installed = self.manager.installed()[0]
        self.assertEqual((self.root / 'loras' / installed['relative_path']).read_bytes(), self.data)
        self.assertEqual(result['bytes'], len(self.data))

    def test_wrong_hash_is_not_installed(self):
        self.descriptor['sha256'] = '0' * 64
        self.assertEqual(self.start()['status'], 'failed')
        self.assertEqual(self.manager.installed(), [])
        self.assertEqual(list((self.root / 'loras').rglob('*.safetensors')), [])

    def test_different_existing_file_is_preserved(self):
        self.start()
        installed = self.manager.installed()[0]
        path = self.root / 'loras' / installed['relative_path']
        path.write_bytes(b'keep existing user file')
        self.assertEqual(self.start()['status'], 'failed')
        self.assertEqual(path.read_bytes(), b'keep existing user file')

    def test_range_resume_uses_existing_verified_identity(self):
        partial = self.manager.partial_path(self.descriptor)
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(self.data[:96])
        self.assertEqual(self.start()['status'], 'completed')
        self.assertEqual(self.transport.calls[0][1]['headers']['Range'], 'bytes=96-')

    def test_html_error_is_not_a_download(self):
        self.transport.get = lambda *args, **kwargs: Response(b'<html>Access denied</html>', headers={'Content-Type': 'text/html'})
        self.assertEqual(self.start()['status'], 'failed')
        self.assertEqual(self.manager.installed(), [])

    def test_incorrect_range_is_not_published(self):
        partial = self.manager.partial_path(self.descriptor)
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(self.data[:96])
        self.transport.get = lambda *args, **kwargs: Response(self.data[96:], 206, {
            'Content-Range': f'bytes 0-{len(self.data)-1}/{len(self.data)}'})
        self.assertEqual(self.start()['status'], 'failed')
        self.assertEqual(self.manager.installed(), [])

    def test_cancel_discards_partial_and_retry_succeeds(self):
        original = self.transport.get
        def cancelling(*args, **kwargs):
            response = original(*args, **kwargs)
            self.manager.control('cancel')
            return response
        self.transport.get = cancelling
        self.assertEqual(self.start()['status'], 'cancelled')
        self.assertFalse(self.manager.partial_path(self.descriptor).exists())
        self.transport.get = original
        self.assertEqual(self.start()['status'], 'completed')

    def test_pause_retains_partial_and_resume_finishes(self):
        original = self.transport.get
        def pausing(*args, **kwargs):
            response = original(*args, **kwargs)
            def chunks(chunk_size):
                yield self.data[:64]
                self.manager.control('pause')
                yield self.data[64:128]
            response.iter_content = chunks
            return response
        self.transport.get = pausing
        self.assertEqual(self.start()['status'], 'paused')
        self.assertEqual(self.manager.partial_path(self.descriptor).stat().st_size, 64)
        self.transport.get = original
        self.assertEqual(self.start()['status'], 'completed')
        self.assertEqual(self.transport.calls[-1][1]['headers']['Range'], 'bytes=64-')

    def test_redirect_does_not_forward_authorization_to_storage_host(self):
        self.manager.token = lambda: 'private-connection'
        calls = []
        def redirect(url, **kwargs):
            calls.append(kwargs['headers'])
            return Response(b'', 302, {'Location': 'https://bucket.r2.cloudflarestorage.com/file'}) if len(calls)==1 else Response(self.data)
        self.transport.get = redirect
        self.assertEqual(self.start()['status'], 'completed')
        self.assertIn('Authorization', calls[0])
        self.assertNotIn('Authorization', calls[1])

    def test_unknown_content_length_still_verifies_hash(self):
        self.transport.get = lambda *args, **kwargs: Response(self.data, headers={'Content-Type': 'application/octet-stream'})
        self.assertEqual(self.start()['status'], 'completed')

    def test_complete_partial_is_verified_without_requesting_past_end(self):
        partial = self.manager.partial_path(self.descriptor)
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(self.data)
        self.assertEqual(self.start()['status'], 'completed')
        self.assertEqual(self.transport.calls, [])

    def test_shared_download_gate_prevents_second_writer(self):
        self.manager.gate.acquire()
        try:
            with self.assertRaises(Exception): self.manager.start({'model_id':1,'version_id':2,'file_id':3,'profile':'sdxl_base','kind':'LORA'})
        finally:
            self.manager.gate.release()

    def test_included_guides_share_civitai_store_and_preserve_existing_entries(self):
        self.start()
        guide = json.loads((ROOT / 'lora_guides.json').read_text(encoding='utf-8'))['guides'][0]
        model = json.loads((ROOT / 'models.lock.json').read_text())['models'][guide['model_key']]
        path = self.root / 'loras' / model['name']
        path.write_bytes(b'fixture weights')
        with patch.object(module, 'file_hash', return_value=model['sha256']) as hasher:
            result = module.register_included_lora_info(self.root, [model['name']])
            self.assertEqual(result['registered'], [model['name']])
            module.register_included_lora_info(self.root, [model['name']])
            self.assertEqual(hasher.call_count, 1, 'Unchanged files must not be rehashed on every refresh')
        records = self.manager.installed()
        self.assertEqual(len(records), 2)
        included = next(r for r in records if r['source_provider'] == 'huggingface')
        self.assertEqual(included['creator'], guide['creator'])
        self.assertEqual(included, json.loads(path.with_suffix('.civitai.json').read_text(encoding='utf-8')))
        self.assertIn('guide', included)
        original = next(r for r in records if r['source_provider'] == 'civitai')
        self.assertEqual(original['source_url'], self.descriptor['source_url'])
        self.assertNotIn('download_url', original)

    def test_unmatched_weights_never_acquire_an_included_identity(self):
        guide = json.loads((ROOT / 'lora_guides.json').read_text(encoding='utf-8'))['guides'][0]
        model = json.loads((ROOT / 'models.lock.json').read_text())['models'][guide['model_key']]
        path = self.root / 'loras' / model['name']
        path.parent.mkdir();path.write_bytes(b'different weights with the same filename')
        result = module.register_included_lora_info(self.root, [model['name']])
        self.assertEqual(result['unrecognized'], [model['name']])
        self.assertEqual(self.manager.installed(), [])

    def test_model_info_preserves_user_fields_and_rejects_outside_path(self):
        self.start()
        original = self.manager.installed()[0]
        target = self.root / original['category'] / original['relative_path']
        original['user_notes'] = 'Keep my note'
        module.publish_model_info(self.root, target, original)
        saved = module.publish_model_info(self.root, target, {**self.descriptor, 'creator': 'Source author'})
        self.assertEqual(saved['user_notes'], 'Keep my note')
        self.assertEqual(saved['creator'], 'Source author')
        with self.assertRaises(Exception):
            module.publish_model_info(self.root, self.root.parent / 'escape.safetensors', self.descriptor)


if __name__ == '__main__': unittest.main()
