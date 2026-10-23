"""New image tasks bind only their explicit sources and selected model variant."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_reference_pair import recipes, store, runtime, prompt_contracts
from importlib import import_module

profiles = import_module("_aw_pair_contract.profiles")


class ImageTaskContractTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = store.AssetStore(self.folder.name)
        recipes.store = runtime.store = lambda: self.library
        self.project = self.library.create_project()
        self.assertTrue(callable(getattr(recipes, "image_task_recipe", None)),
                        "New image roles need an explicit native recipe contract")

    def image(self, role="source", name="source1"):
        path = self.library.path(self.project["id"], f"images/{name}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        record = {"id": name, "file": f"images/{name}.png", "sha256": store.digest(path)}
        self.project = self.library.add_revision(self.project["id"], role, record)
        return record

    def recipe(self, task="create_image", role="design", profile="klein4"):
        snapshot = copy.deepcopy(self.project)
        snapshot["profile"] = profile
        snapshot["prompt"] = "A small red toy camera with one large round front lens."
        return recipes.image_task_recipe(self.project, snapshot, task, role, "attempt1")

    def test_all_nine_profiles_have_task_defaults_license_and_lora_metadata(self):
        self.image()
        for name in ("qwen21", "qwen2511", "klein_base", "klein_distilled", "klein_kv",
                     "klein4", "klein4_base", "flux3_base", "flux3_distilled"):
            with self.subTest(name=name):
                capability = profiles.capabilities(name)
                self.assertTrue(capability["license"]["url"].startswith("https://"))
                self.assertEqual(capability["lora"]["profile"], name)
                result = self.recipe(profile=name)
                loaders = [node for node in result["graph"].values() if node["class_type"] == "UNETLoader"]
                self.assertEqual(len(loaders), 1)
                self.assertEqual(result["details"]["profile"], name)
                self.assertEqual(result["details"]["steps"], capability["defaults"]["steps"])

    def test_edit2511_requires_source(self):
        with self.assertRaises(store.CapabilityError):
            self.recipe(profile="qwen2511")

    def test_references_never_silently_truncate(self):
        for index in range(4):
            self.image(name=f"source{index}")
        with self.assertRaises(store.CapabilityError):
            self.recipe(profile="qwen2511")
        result = self.recipe(profile="klein4")
        self.assertEqual(len(result["details"]["references"]), 4)
        self.assertEqual(len([n for n in result["graph"].values() if n["class_type"] == "AW_LoadImage"]), 4)

    def test_three_quarter_does_not_inherit_front_only_instruction(self):
        self.image("design")
        for name in profiles.PROFILES:
            result = self.recipe("three_quarter", "mesh_input", name)
            self.assertIn("three-quarter", result["details"]["prompt"])
            self.assertNotIn("no three-quarter rotation", result["details"]["prompt"])
            self.assertEqual(result["details"]["camera_verification"], "not_measured")
            output = next(n for n in result["graph"].values() if n["class_type"] == "AW_SaveImage")
            self.assertEqual(output["inputs"]["slot"], "mesh_input")

    def test_reference_task_uses_primary_and_explicit_notes_not_previous_generated_views(self):
        primary = self.image("mesh_input", "primary")
        self.project = self.library.approve_image(self.project["id"], "mesh_input", primary["id"],
            primary["sha256"], "approved", "user", "", self.project["revision"])
        self.image("reference_front", "oldfront")
        self.project["design_notes"] = "The back has a yellow carrying strap."
        result = self.recipe("reference_view", "reference_back")
        self.assertEqual([r["id"] for r in result["details"]["references"]], ["primary"])
        self.assertIn("yellow carrying strap", result["details"]["prompt"])
        self.assertEqual(result["details"]["requested_view"], "back")
        self.assertEqual(result["details"]["camera_verification"], "not_measured")

    def test_unapproved_primary_cannot_generate_package_references(self):
        self.image("mesh_input", "primary")
        with self.assertRaises(store.ApprovalRequired):
            self.recipe("reference_view", "reference_back")

    def test_disabled_and_zero_strength_loras_are_noops(self):
        self.project["loras"] = [
            {"name": "missing.safetensors", "profile": "qwen21", "strength": 1, "enabled": False},
            {"name": "also-missing.safetensors", "profile": "qwen21", "strength": 0, "enabled": True}]
        result = self.recipe()
        self.assertFalse(any(n["class_type"] == "AW_LoadModelLoRA" for n in result["graph"].values()))

    def test_family_variant_mismatch_fails(self):
        self.project["loras"] = [{"name": "base-only.safetensors", "profile": "klein4_base",
                                  "strength": 1, "enabled": True}]
        with self.assertRaises(store.CapabilityError):
            self.recipe()

    def test_lora_provenance_records_hash_strength_trigger_and_matching_report_connection(self):
        record = self.image()
        root = Path(self.folder.name)
        path = root / 'models' / 'loras' / 'matched.safetensors'
        path.parent.mkdir(parents=True)
        path.write_bytes(self.library.path(self.project['id'], record['file']).read_bytes())
        self.project["loras"] = [{"name": "matched.safetensors", "profile": "klein4",
                                  "strength": .8, "trigger": "test style", "enabled": True}]
        with patch.object(recipes.folder_paths, "base_path", str(root), create=True):
            result = self.recipe()
        details = result["details"]["loras"][0]
        self.assertEqual(details["sha256"], record["sha256"])
        self.assertEqual(details["strength"], .8)
        self.assertIn("test style", result["details"]["prompt"])
        lora_id = next(k for k,n in result["graph"].items() if n["class_type"] == "AW_LoadModelLoRA")
        save = next(n for n in result["graph"].values() if n["class_type"] == "AW_SaveImage")
        self.assertEqual(save["inputs"].get("lora_reports.lora1"), [lora_id, 1])

    def test_lora_cannot_escape_this_installation_or_borrow_another_models_folder(self):
        root = Path(self.folder.name)
        with patch.object(recipes.folder_paths, 'base_path', str(root), create=True):
            for name in ('../../../other-app/weights.safetensors', str(root / 'outside.safetensors')):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    recipes.local_lora(name)
            with self.assertRaisesRegex(ValueError, 'missing'):
                recipes.local_lora('not-installed.safetensors')

    def test_flux3_uses_current_full_scene_contract_and_variant_settings(self):
        self.image("design")
        contract = prompt_contracts.image_task("flux3_distilled", "three_quarter",
            "A red toy camera", "", None)
        self.assertIn("caption", contract["system"].lower())
        self.assertNotIn("<image1>", contract["prompt"])
        self.assertEqual(self.recipe("three_quarter", "mesh_input", "flux3_base")["details"]["steps"], 50)
        self.assertEqual(self.recipe("three_quarter", "mesh_input", "flux3_distilled")["details"]["steps"], 16)

    def test_selected_asset_category_reaches_actual_generation_prompt(self):
        for category, instruction in prompt_contracts.CATEGORIES.items():
            with self.subTest(category=category):
                self.project["category"] = category
                result = self.recipe()
                self.assertIn(instruction, result["details"]["prompt"])

    def test_source_conditioned_creation_uses_editing_guidance_for_selected_family(self):
        self.image()
        original = prompt_contracts.contract
        with patch.object(prompt_contracts, "contract", wraps=original) as contract:
            self.recipe(profile="qwen21")
        self.assertTrue(contract.call_args.args[2],
                        "Creation from uploaded references needs the model's reference-editing guidance")

    def test_camera_adapter_trigger_stays_at_start_of_native_prompt(self):
        self.image()
        root = Path(self.folder.name)
        path = root / 'models' / 'loras' / 'camera.safetensors'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'camera fixture')
        for profile, trigger in (("qwen21", "<mva> front-right quarter view, eye-level shot"),
                                 ("qwen2511", "<sks> front-right quarter view eye-level shot medium shot")):
            with self.subTest(profile=profile), patch.object(recipes.folder_paths, 'base_path', str(root), create=True):
                self.project['loras'] = [{'name': 'camera.safetensors', 'profile': profile,
                    'strength': 1, 'enabled': True, 'trigger': trigger}]
                self.assertTrue(self.recipe(profile=profile)['details']['prompt'].startswith(trigger))


if __name__ == "__main__":
    unittest.main()
