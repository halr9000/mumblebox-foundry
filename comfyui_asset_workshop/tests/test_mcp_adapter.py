"""Thin agent client uses the same HTTP contract, not another execution owner."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


class MCPAdapterTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).parents[1] / 'agent' / 'client.py'
        self.assertTrue(source.is_file(), 'The agent HTTP adapter is not built')
        spec = importlib.util.spec_from_file_location('mumblebox_agent_client_test', source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.client = self.module.LocalAPI('http://127.0.0.1:8188')
        self.calls = []

    def response(self, request, **kwargs):
        self.calls.append(request)
        result = io.BytesIO(json.dumps({'id': 'fixture', 'state': 'awaiting_review'}).encode())
        result.headers = {'Content-Type': 'application/json'}
        return result

    def test_tools_use_same_routes_and_request_key_as_gui(self):
        with patch.object(self.client.opener, 'open', side_effect=self.response):
            self.client.start_job('project1', 7, 'three_quarter', 'request1', {})
        call = self.calls[0]
        self.assertEqual(call.full_url, 'http://127.0.0.1:8188/asset-workshop/v2/projects/project1/jobs')
        self.assertEqual(json.loads(call.data)['request_key'], 'request1')
        self.assertEqual(json.loads(call.data)['expected_revision'], 7)

    def test_remote_target_and_arbitrary_server_paths_are_rejected(self):
        for target in ('https://example.com', 'http://192.168.1.4:8188', 'http://127.0.0.1:8188/private'):
            with self.assertRaises(ValueError):
                self.module.LocalAPI(target)
        with self.assertRaises(ValueError):
            self.client.read_artifact('../other', 'file1')
        with self.assertRaises(ValueError):
            self.client.read_artifact('project1', 'C:\\private\\file')

    def test_agent_review_is_always_labeled_agent(self):
        with patch.object(self.client.opener, 'open', side_effect=self.response):
            self.client.review_image('project1', 3, 'mesh_input', 'image1', 'a'*64, 'approved', '')
        self.assertEqual(json.loads(self.calls[0].data)['reviewer'], 'agent')

    def test_default_artifact_read_fetches_metadata_only(self):
        with patch.object(self.client.opener, 'open', side_effect=self.response):
            result = self.client.read_artifact('project1', 'image1')
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0].full_url.endswith('/artifacts/image1?metadata=1'))
        self.assertNotIn('data', result)
        self.assertIn('download_url', result)

    def test_import_reads_only_authorized_input_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.png'
            path.write_bytes(b'fixture png bytes')
            with self.assertRaises(ValueError):
                self.client.import_image('project1', 1, str(path))
            permitted = self.module.LocalAPI('http://127.0.0.1:8188', input_files=[path])
            with patch.object(permitted.opener, 'open', side_effect=self.response):
                permitted.import_image('project1', 1, str(path))
            self.assertIn(b'name="role"', self.calls[-1].data)
            self.assertIn(b'fixture png bytes', self.calls[-1].data)

    def test_http_approval_error_preserves_status_and_saved_artifacts(self):
        payload = {'error': 'Approve the mesh input first', 'type': 'ApprovalRequired', 'artifacts': ['master1']}
        error = urllib.error.HTTPError('local', 409, 'Conflict', {}, io.BytesIO(json.dumps(payload).encode()))
        with patch.object(self.client.opener, 'open', side_effect=error):
            with self.assertRaises(self.module.APIError) as caught:
                self.client.start_job('project1', 1, 'build_mesh_package', 'request1', {})
        self.assertEqual(caught.exception.status, 409)
        self.assertEqual(caught.exception.details, payload)

    def test_pipeline_controls_and_material_choices_use_project_owner(self):
        self.assertTrue(callable(getattr(self.client,"save_pipeline",None)),"Agent must reach the shared pipeline settings owner")
        with patch.object(self.client.opener,'open',side_effect=self.response):
            self.client.save_pipeline('project1',7,{'texture_provider':'trellis2'})
            self.client.select_pipeline_artifact('project1',8,'paint1')
            self.client.save_material_choices('project1','session1',3,{'version':1,'regions':[]})
        self.assertTrue(self.calls[0].full_url.endswith('/projects/project1/pipeline'))
        self.assertEqual(self.calls[0].method,'PATCH')
        self.assertTrue(self.calls[1].full_url.endswith('/pipeline/select'))
        self.assertEqual(json.loads(self.calls[2].data)['expected_draft_revision'],3)

    def test_asset_export_audience_is_explicit_and_agent_default_remains_strict(self):
        with patch.object(self.client.opener,'open',side_effect=self.response):
            self.client.export_package('project1',7,['mesh1'],audience='asset')
            self.client.export_package('project1',7,['mesh1'])
        self.assertEqual(json.loads(self.calls[0].data)['audience'],'asset')
        self.assertEqual(json.loads(self.calls[1].data)['audience'],'agent')


if __name__ == '__main__':
    unittest.main()
