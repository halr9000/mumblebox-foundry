"""First-use worker readiness: no startup downloads, no silent replacement."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

PACK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("worker_models", PACK/"foundry/workflows/image_to_3d/worker_models.py")

class WorkerModelsTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def health(self, ready=False, state="idle", present=False, checking=False):
        return {"models":{"ready":ready,"download":{"state":state},
                          "components":{"hi3d":{"present":present}}},
                "model_checking":checking,"active":None}

    def test_ready_refiner_does_not_download(self):
        request=Mock(return_value=self.health(ready=True, present=True))
        self.module.ensure_hi3d("http://localhost:8378",request,lambda:False,Mock(),lambda:None)
        self.assertEqual([c.args[1] for c in request.call_args_list],["/api/health"])

    def test_missing_refiner_downloads_only_when_refinement_is_requested(self):
        request=Mock(side_effect=[self.health(),{"started":True},
                                  self.health(state="downloading"),self.health(ready=True,present=True)])
        progress=Mock()
        self.module.ensure_hi3d("http://localhost:8378",request,lambda:False,progress,lambda:None)
        self.assertEqual(sum(c.args[1]=="/api/models/download" for c in request.call_args_list),1)
        self.assertTrue(any(c.args[0]["phase"]=="downloading" for c in progress.call_args_list))

    def test_present_unverified_refiner_verifies_without_download(self):
        request=Mock(side_effect=[self.health(present=True),{},self.health(ready=True,present=True)])
        self.module.ensure_hi3d("http://localhost:8378",request,lambda:False,Mock(),lambda:None)
        self.assertEqual(request.call_args_list[1].args[1],"/api/models/verify")

    def test_failed_download_is_not_reported_ready(self):
        request=Mock(side_effect=[self.health(),{"started":True},self.health(state="failed")])
        with self.assertRaisesRegex(ValueError,"download"):
            self.module.ensure_hi3d("http://localhost:8378",request,lambda:False,Mock(),lambda:None)

    def test_cancellation_never_starts_another_download_or_refinement(self):
        request=Mock()
        with self.assertRaises(InterruptedError):
            self.module.ensure_hi3d("http://localhost:8378",request,lambda:True,Mock(),lambda:None)
        request.assert_not_called()

    def test_join_existing_download_does_not_start_duplicate(self):
        request=Mock(side_effect=[self.health(state="downloading"),self.health(ready=True,present=True)])
        self.module.ensure_hi3d("http://localhost:8378",request,lambda:False,Mock(),lambda:None)
        self.assertTrue(all(c.args[1]=="/api/health" for c in request.call_args_list))

    def test_snapshot_verifies_existing_files_and_fetches_missing_only(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            present=root/"repo"/"present.bin";present.parent.mkdir();present.write_bytes(b"existing")
            items=[{"name":"repo/present.bin","size":8,"sha256":hashlib.sha256(b"existing").hexdigest()},
                   {"name":"repo/missing.bin","size":3,"sha256":hashlib.sha256(b"new").hexdigest()}]
            def fetch(item,destination):(destination/item["name"]).write_bytes(b"new")
            download=Mock(side_effect=fetch)
            receipts=root/"receipts.json"
            self.module.ensure_files(items,root,receipts,download,lambda:False,Mock())
            self.assertEqual(download.call_count,1)
            self.assertEqual(download.call_args.args[0]["name"],"repo/missing.bin")
            self.module.ensure_files(items,root,receipts,download,lambda:False,Mock())
            self.assertEqual(download.call_count,1)

    def test_changed_weights_are_preserved_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);file=root/"model.bin";file.write_bytes(b"mine")
            download=Mock()
            with self.assertRaisesRegex(ValueError,"preserved"):
                self.module.ensure_files([{"name":"model.bin","size":4,"sha256":"0"*64}],root,
                                         root/"receipts.json",download,lambda:False,Mock())
            download.assert_not_called()
            self.assertEqual(file.read_bytes(),b"mine")

    def test_snapshot_path_cannot_escape_model_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(ValueError):
                self.module.ensure_files([{"name":"../escape","size":4,"sha256":"0"*64}],root,
                                         root/"receipts.json",Mock(),lambda:False,Mock())

if __name__=="__main__":unittest.main()
