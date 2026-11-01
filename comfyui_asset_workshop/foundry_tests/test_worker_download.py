"""Exercise the actual downloader with a small mocked HTTP response."""
import hashlib
import importlib.util
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

PACK=Path(__file__).resolve().parents[1]

class WorkerDownloadTests(unittest.TestCase):
    def test_configured_snapshot_download_is_verified_reused_and_confined(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);destination=root/"snapshots"
            package=types.ModuleType("_download_test");package.__path__=[str(PACK)]
            paths=types.ModuleType("folder_paths");paths.base_path=str(root)
            paths.add_model_folder_path=Mock();paths.get_folder_paths=Mock(return_value=[])
            auth=types.ModuleType("_download_test.hf_auth");auth.token=lambda:None
            recipes=types.ModuleType("_download_test.recipes");recipes.MODELS={};recipes.required_models=lambda *a:[]
            runtime=types.ModuleType("_download_test.runtime")
            runtime.configuration=lambda:{"pipeline_runtime":{"trellis_models":str(destination)}}
            modules={"_download_test":package,"folder_paths":paths,"_download_test.hf_auth":auth,
                     "_download_test.recipes":recipes,"_download_test.runtime":runtime}
            with patch.dict(sys.modules,modules):
                spec=importlib.util.spec_from_file_location("_download_test.models",PACK/"models.py")
                models=importlib.util.module_from_spec(spec);spec.loader.exec_module(models)
                response=io.BytesIO(b"abc");response.status=200;response.headers={}
                opener=Mock();opener.open.return_value=response
                model={"category":"worker","name":"repo/model.bin","repo":"owner/repo","revision":"a"*40,
                       "file":"model.bin","sha256":hashlib.sha256(b"abc").hexdigest(),"size":3}
                with patch.object(models.urllib.request,"build_opener",return_value=opener):
                    models.download_one(model,destination_root=destination)
                    self.assertEqual((destination/"repo/model.bin").read_bytes(),b"abc")
                    models.download_one(model,destination_root=destination)
                    self.assertEqual(opener.open.call_count,1)
                    with self.assertRaises(ValueError):
                        models.download_one(model,destination_root=root/"unapproved")
                    with self.assertRaises(ValueError):
                        models.download_one({**model,"name":"../escape.bin"},destination_root=destination)
                    (destination/"repo/model.bin").write_bytes(b"mine")
                    with self.assertRaisesRegex(ValueError,"will not be replaced"):
                        models.download_one(model,destination_root=destination)
                    self.assertEqual((destination/"repo/model.bin").read_bytes(),b"mine")

if __name__=="__main__":unittest.main()
