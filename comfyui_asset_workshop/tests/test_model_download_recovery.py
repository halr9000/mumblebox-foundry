"""First-use access recovery exercises the real downloader without account/network access."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch
import urllib.error


class ModelDownloadRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.body = b'weights'
        self.model = dict(repo='lab/example', revision='pinned', file='weights/tiny.safetensors',
                          name='tiny.safetensors', size=7, category='diffusion_models',
                          sha256=hashlib.sha256(self.body).hexdigest(),
                          license_url='https://huggingface.co/lab/example/blob/main/LICENSE')
        catalog = {'first': self.model, 'second': {**self.model, 'name': 'second.safetensors',
                                                  'file': 'weights/second.safetensors'}}
        package = types.ModuleType('download_fixture')
        package.__path__ = []
        self.folders = {'diffusion_models': [str(self.root / 'models' / 'diffusion_models')]}
        modules = {'download_fixture': package,
                   'download_fixture.hf_auth': types.SimpleNamespace(token=lambda: 'hf_fixture_not_a_real_token'),
                   'download_fixture.recipes': types.SimpleNamespace(MODELS=catalog,
                       required_models=lambda asset, *args: asset['selected']),
                   'download_fixture.runtime': types.SimpleNamespace(configuration=lambda: {'root': str(self.root)}),
                   'download_fixture.store': types.SimpleNamespace(
                       contained=lambda root, name: root / name,
                       digest=lambda path: hashlib.sha256(path.read_bytes()).hexdigest(),
                       atomic_json=lambda path, value: path.write_text(json.dumps(value))),
                   'folder_paths': types.SimpleNamespace(base_path=str(self.root),
                       get_folder_paths=lambda category: self.folders.get(category, []),
                       add_model_folder_path=lambda *args, **kwargs: None)}
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location('download_fixture.models',
                Path(__file__).parents[1] / 'models.py')
            self.models = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.models)

    def denied(self, code):
        return types.SimpleNamespace(open=lambda request, **kwargs: self.raise_http(request, code))

    def raise_http(self, request, code):
        raise urllib.error.HTTPError(request.full_url, code, 'denied', {}, None)

    def wait(self):
        end = time.monotonic() + 3
        while self.models.DOWNLOAD_LOCK.locked() and time.monotonic() < end:
            time.sleep(.005)
        self.assertFalse(self.models.DOWNLOAD_LOCK.locked(), 'Download worker did not release its lock')

    def test_denied_access_identifies_exact_repository_without_exposing_token(self):
        for code in (401, 403):
            with self.subTest(code=code), patch.object(self.models.urllib.request, 'build_opener',
                                                       return_value=self.denied(code)):
                with self.assertRaises((ValueError, urllib.error.HTTPError)):
                    self.models.download_one(self.model)
                recovery = self.models.DOWNLOAD.get('recovery', {})
                self.assertEqual(recovery.get('kind'), 'access')
                self.assertEqual(recovery.get('repo_url'), 'https://huggingface.co/lab/example')
                self.assertEqual(recovery.get('model'), 'tiny.safetensors')
                self.assertEqual(recovery.get('http_status'), code)
                self.assertNotIn('hf_fixture_not_a_real_token', json.dumps(self.models.DOWNLOAD))

    def test_server_failure_is_not_claimed_to_require_repository_approval(self):
        asset = {'id': 'project1', 'profile': 'klein4', 'selected': ['first']}
        with patch.object(self.models.urllib.request, 'build_opener', return_value=self.denied(503)):
            self.models.start_download(asset)
            self.wait()
        state = self.models.DOWNLOAD
        self.assertEqual(state['status'], 'failed')
        self.assertNotEqual((state.get('recovery') or {}).get('kind'), 'access')
        self.assertNotIn('Gated models', state['error'])
        self.assertEqual(state['request']['model_ids'], ['first'])

    def test_retry_keeps_original_batch_and_reuses_completed_files(self):
        first = self.root / 'models' / 'diffusion_models' / 'tiny.safetensors'
        asset = {'id': 'project1', 'profile': 'klein4', 'selected': ['first', 'second']}
        def first_attempt(request, **kwargs):
            if request.full_url.endswith('/second.safetensors'):
                return self.raise_http(request, 403)
            response = io.BytesIO(self.body)
            response.status = 200
            return response
        with patch.object(self.models.urllib.request, 'build_opener',
                          return_value=types.SimpleNamespace(open=first_attempt)):
            self.models.start_download(asset)
            self.wait()
        asset['selected'] = []
        responses = []
        def opened(request, **kwargs):
            responses.append(request.full_url)
            body = io.BytesIO(self.body)
            body.status = 200
            return body
        with patch.object(self.models.urllib.request, 'build_opener',
                          return_value=types.SimpleNamespace(open=opened)):
            self.models.start_download(asset, retry=True)
            self.wait()
        self.assertEqual(self.models.DOWNLOAD['status'], 'complete')
        self.assertEqual(self.models.DOWNLOAD['request']['model_ids'], ['first', 'second'])
        self.assertEqual((first.parent / 'second.safetensors').read_bytes(), self.body)
        self.assertEqual(first.read_bytes(), self.body)
        self.assertEqual(len(responses), 1, 'An installed verified file was downloaded again')
        self.assertFalse(self.models.DOWNLOAD.get('recovery'))

    def test_retry_cannot_be_redirected_to_another_project(self):
        asset = {'id': 'project1', 'profile': 'klein4', 'selected': ['first']}
        with patch.object(self.models.urllib.request, 'build_opener', return_value=self.denied(403)):
            self.models.start_download(asset)
            self.wait()
        with self.assertRaises(ValueError):
            self.models.start_download({**asset, 'id': 'other'}, retry=True)
        self.assertEqual(self.models.DOWNLOAD['status'], 'failed')

    def test_paused_download_keeps_its_partial_file_and_retry_descriptor(self):
        asset = {'id': 'project1', 'profile': 'klein4', 'selected': ['first']}
        def pause(request, **kwargs):
            self.models.DOWNLOAD['cancel'] = True
            response = io.BytesIO(self.body)
            response.status = 200
            return response
        with patch.object(self.models.urllib.request, 'build_opener',
                          return_value=types.SimpleNamespace(open=pause)):
            self.models.start_download(asset)
            self.wait()
        self.assertEqual(self.models.DOWNLOAD['status'], 'paused')
        self.assertEqual(self.models.DOWNLOAD.get('request', {}).get('asset_id'), 'project1')
        self.assertTrue(any((self.root / 'models').rglob('*.part')))


if __name__ == '__main__':
    unittest.main()
