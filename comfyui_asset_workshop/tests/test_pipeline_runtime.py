import importlib.util
from pathlib import Path
import tempfile
import unittest
spec=importlib.util.spec_from_file_location("pipeline_capabilities",Path(__file__).parents[1]/"pipeline_capabilities.py")
class RuntimeTests(unittest.TestCase):
    def module(self):
        self.assertTrue(Path(spec.origin).is_file(),"Owned runtime preflight must exist")
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    def test_missing_runtime_is_truthfully_unavailable(self):
        m=self.module();r=m.inspect_runtime({})
        self.assertFalse(r["providers"]["trellis2"]["available"])
        self.assertIn("Configure",r["providers"]["trellis2"]["reason"])
        self.assertFalse(r["providers"]["pixal3d"]["available"])
    def test_remote_service_and_unsafe_paths_are_rejected(self):
        m=self.module()
        for cfg in ({"hi3d_url":"http://example.com"},{"worker_python":"relative/python.exe"}):
            with self.assertRaises(ValueError):m.validate_runtime(cfg)
    def test_unknown_config_rejected(self):
        with self.assertRaises(ValueError):self.module().validate_runtime({"extra":"value"})
