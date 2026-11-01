"""Portable install contract: no downloads, preserved state, repeatability, rollback."""
import argparse, importlib.util, json, tempfile, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("installer",Path(__file__).with_name("install_foundry.py"))
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="foundry-install-")
        self.root=Path(self.temp.name);self.core=self.root/"core"
        (self.core/"custom_nodes").mkdir(parents=True)
        (self.core/"folder_paths.py").write_text("# host fixture")
        self.repo=self.root/"wrapper";self.repo.mkdir();(self.repo/"__init__.py").write_text("")
        self.models=self.root/"weights";self.models.mkdir();(self.models/"keep.txt").write_text("model sentinel")
        self.exe=self.root/"python.exe";self.exe.write_text("fixture")
        self.user=self.core/"user";self.user.mkdir()
        (self.user/"asset-workshop.json").write_text(json.dumps({"theme":"keep","pipeline_runtime":{"stable_materials":"preserve"}}))
        self.args=argparse.Namespace(comfy=str(self.core),user_directory=None,worker_python=str(self.exe),trellis_repo=str(self.repo),trellis_models=str(self.models),blender=str(self.exe),hi3d_url="http://127.0.0.1:8378")
    def tearDown(self):self.temp.cleanup()
    def test_install_and_repeat_preserve(self):
        installer.install(self.args)
        target=self.core/"custom_nodes/comfyui_asset_workshop"
        self.assertTrue((target/"foundry/routes.py").is_file())
        config=json.loads((self.user/"asset-workshop.json").read_text())
        self.assertEqual(config["theme"],"keep")
        self.assertEqual(config["pipeline_runtime"]["stable_materials"],"preserve")
        installer.install(self.args)
        changes=sorted((self.user/"mumblebox-foundry/install-backups").glob("*/changed-files.json"))
        self.assertEqual(json.loads(changes[-1].read_text()),[])
        self.assertEqual((self.models/"keep.txt").read_text(),"model sentinel")
        self.assertFalse(any(target.rglob("*.safetensors")))
    def test_changed_file_backup(self):
        target=self.core/"custom_nodes/comfyui_asset_workshop";target.mkdir()
        (target/"models.py").write_text("previous module")
        installer.install(self.args)
        backups=list((self.user/"mumblebox-foundry/install-backups").glob("*/custom-node/models.py"))
        self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_text(),"previous module")
    def test_remote_service_rejected_before_writes(self):
        self.args.hi3d_url="http://example.com"
        with self.assertRaises(ValueError):installer.install(self.args)
        self.assertFalse((self.core/"custom_nodes/comfyui_asset_workshop").exists())
    def test_onedrive_runtime_rejected_before_writes(self):
        self.args.worker_python=str(self.root/"OneDrive/python.exe")
        with self.assertRaises(ValueError):installer.install(self.args)
        self.assertFalse((self.core/"custom_nodes/comfyui_asset_workshop").exists())

if __name__=="__main__":unittest.main()