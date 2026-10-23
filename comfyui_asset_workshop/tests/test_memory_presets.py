"""An experimental 8 GB preset changes settings without rewriting approved images."""
import copy
import importlib
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from test_reference_pair import store


class MemoryPresetTests(unittest.TestCase):
    def setUp(self):
        native = types.ModuleType("comfy")
        native.__path__ = []
        native.model_management = types.ModuleType("comfy.model_management")
        native.model_management.vram_state = types.SimpleNamespace(name="NORMAL_VRAM")
        with patch.dict(sys.modules, {"comfy": native, "comfy.model_management": native.model_management}):
            self.policy = importlib.import_module("_aw_pair_contract.memory_policy")
        self.assertTrue(callable(getattr(self.policy, "preset_settings", None)), "Memory presets have not been implemented")
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = store.AssetStore(self.folder.name)
        self.project = self.library.create_project()
        self.hardware = {"vram_total_gb": 16, "vram_free_gb": 14, "ram_total_gb": 64,
                         "ram_free_gb": 40, "startup_reserve_gb": 0, "comfy_mode": "NORMAL_VRAM"}

    def test_experimental_8gb_preset_has_supported_explicit_values(self):
        result = self.policy.preset_settings("experimental_8gb", self.hardware)
        settings = result["settings"]
        self.assertEqual(result["profile"], "klein4")
        self.assertEqual([settings[k] for k in ("resolution", "shape_resolution", "master_texture", "master_faces")],
                         [768, 1024, 1024, 100000])
        self.assertEqual(settings["extra_vram_headroom_gb"], 2)
        self.assertTrue(settings["tiled_vae"] and settings["release_between_stages"])
        self.assertEqual(settings["uv_method"], "pec")
        self.assertFalse(settings["remesh"])
        self.assertEqual(settings["cache_device"], "cpu")
        self.assertEqual(settings["min_ram_free_gb"], 8)
        self.assertEqual(settings["min_vram_free_gb"], 1.5)
        self.assertEqual(result["validation"]["status"], "experimental")

    def test_fresh_project_matches_its_standard_preset_label(self):
        expected = self.policy.preset_settings('standard_16gb', self.hardware)
        self.assertEqual(self.project['profile'], expected['profile'])
        for key, value in expected['settings'].items():
            with self.subTest(setting=key):
                self.assertEqual(self.project['settings'][key], value)

    def test_ram_reserve_and_cache_follow_actual_system_ram(self):
        hardware = {**self.hardware, "ram_total_gb": 16}
        settings = self.policy.preset_settings("experimental_8gb", hardware)["settings"]
        self.assertEqual(settings["min_ram_free_gb"], 2)
        self.assertEqual(settings["cache_device"], "off")

    def test_apply_preset_preserves_originals_approval_and_running_snapshot(self):
        self.project["images"]["mesh_input"] = {"current": "original", "approved": "original", "revisions": [{"id": "original"}]}
        self.project["jobs"] = [{"snapshot": {"settings": {"resolution": 1024}}}]
        original = copy.deepcopy(self.project)
        result = self.policy.apply_preset(self.project, "experimental_8gb", self.hardware)
        self.assertEqual(self.project, original)
        self.assertEqual(result["images"], original["images"])
        self.assertEqual(result["jobs"], original["jobs"])
        self.assertEqual(result["settings"]["mesh_shape_steps"], 20)

    def test_low_memory_keeps_loras_and_reports_family_mismatch(self):
        self.project["profile"] = "qwen21"
        self.project["loras"] = [{"name": "qwen-style", "profile": "qwen21", "enabled": True}]
        result = self.policy.apply_preset(self.project, "experimental_8gb", self.hardware)
        self.assertEqual(result["loras"], self.project["loras"])
        self.assertTrue(self.policy.preset_settings("experimental_8gb", self.hardware)["explanations"])

    def test_16gb_host_smoke_is_not_marked_8gb_hardware_validated(self):
        result = self.policy.preset_settings("experimental_8gb", self.hardware)
        self.assertFalse(result["validation"]["hardware_validated"])
        self.assertIn("tester", result["validation"]["message"].lower())

    def test_unknown_preset_does_not_change_saved_settings(self):
        original = copy.deepcopy(self.project)
        with self.assertRaises(ValueError):
            self.policy.apply_preset(self.project, "unknown", self.hardware)
        self.assertEqual(self.project, original)

    def test_overrides_and_reset_are_shared_between_ui_and_agent(self):
        self.assertTrue(callable(getattr(self.policy, "project_patch", None)))
        changes = self.policy.project_patch(self.project, {"memory_preset_id": "experimental_8gb"}, self.hardware)
        self.project = self.library.update_project(self.project["id"], self.project["revision"], changes)
        edited = self.policy.project_patch(self.project, {"settings": {"master_texture": 2048}}, self.hardware)
        self.project = self.library.update_project(self.project["id"], self.project["revision"], edited)
        self.assertIn("master_texture", self.project["preset_overrides"])
        reset = self.policy.project_patch(self.project, {"memory_preset_id": "experimental_8gb"}, self.hardware)
        self.project = self.library.update_project(self.project["id"], self.project["revision"], reset)
        self.assertEqual(self.project["settings"]["master_texture"], 1024)
        self.assertEqual(self.project["preset_overrides"], [])

    def test_preflight_refuses_vram_below_user_reserve(self):
        with patch.object(self.policy, "hardware_info", return_value={**self.hardware, "vram_free_gb": .5}):
            with self.assertRaisesRegex(ValueError, "VRAM"):
                self.policy.preflight(self.project, "image")


if __name__ == "__main__":
    unittest.main()
