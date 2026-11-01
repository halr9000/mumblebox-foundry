"""The agent is a bounded client of the wizard service, not a second runner."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"agent"))
from foundry_client import FoundryAPI

class FoundryAgentTests(unittest.TestCase):
    def test_localhost_and_ids_are_enforced(self):
        for url in ["https://example.com","http://127.0.0.1:8188/other","http://user@localhost"]:
            with self.assertRaises(ValueError):FoundryAPI(url)
        client=FoundryAPI();client.request=Mock()
        with self.assertRaises(ValueError):client.get_run("../private")
        client.request.assert_not_called()

    def test_start_uses_existing_run_owner_and_same_retry_key(self):
        client=FoundryAPI();client.request=Mock(return_value={"id":"a"*32})
        client.start("a"*32,"rocket","retry-one")
        self.assertEqual(client.request.call_args.args,("/wizard/runs/"+"a"*32+"/start",
            {"operation":"rocket","request_id":"retry-one","client_id":"foundry-agent"}))
        with self.assertRaises(ValueError):client.start("a"*32,"shell","other")

    def test_status_is_small_and_package_uses_same_download_route(self):
        client=FoundryAPI();client.request=Mock(return_value={"id":"a"*32,"outputs":{"large":"data"},"package":{"files":3}})
        self.assertNotIn("outputs",client.get_run("a"*32))
        self.assertTrue(client.package("a"*32)["download_url"].endswith("/wizard/runs/"+"a"*32+"/package"))

    def test_upload_requires_authorized_file_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/"reference.png";file.write_bytes(b"source")
            client=FoundryAPI();client.upload_api.request=Mock()
            with self.assertRaises(ValueError):client.import_reference(str(file))
            client=FoundryAPI(input_files=[file]);client.upload_api.request=Mock(return_value={"name":"agent-test.png","subfolder":"foundry-agent","type":"input"})
            result=client.import_reference(str(file),"back","Rear of the same asset")
            self.assertEqual(result["role"],"back")
            self.assertEqual(result["filename"],"foundry-agent/agent-test.png")
            self.assertEqual(file.read_bytes(),b"source")
            self.assertIn(b'name="overwrite"\r\n\r\nfalse',client.upload_api.request.call_args.args[1])

if __name__=="__main__":unittest.main()
