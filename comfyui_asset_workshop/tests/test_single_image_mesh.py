"""Only the exact approved primary may condition a new Pixal mesh."""
import copy
import tempfile
import unittest

from test_reference_pair import recipes, store, runtime


class SingleImageMeshTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = store.AssetStore(self.folder.name)
        recipes.store = runtime.store = lambda: self.library
        self.project = self.library.create_project()
        self.assertTrue(callable(getattr(recipes, "single_image_mesh_recipe", None)),
                        "The strict single-image reconstruction entry point is missing")

    def image(self, role, name):
        path = self.library.path(self.project["id"], f"images/{name}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        record = {"id": name, "file": f"images/{name}.png", "sha256": store.digest(path)}
        self.project = self.library.add_revision(self.project["id"], role, record)
        return record

    def primary(self):
        record = self.image("mesh_input", "primary")
        self.project = self.library.approve_image(self.project["id"], "mesh_input", "primary", record["sha256"],
            "approved", "user", "", self.project["revision"])
        return record

    def test_mesh_conditions_exactly_one_approved_hash(self):
        primary = self.primary()
        self.image("reference_back", "other")
        result = recipes.single_image_mesh_recipe(self.project, self.project, "mesh-stage")
        graph = result["graph"]
        images = [n for n in graph.values() if n["class_type"] == "AW_LoadImage"]
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["inputs"]["relative_path"], primary["file"])
        self.assertEqual(images[0]["inputs"]["expected_sha256"], primary["sha256"])
        self.assertEqual(len([n for n in graph.values() if n["class_type"] == "Pixal3DConditioning"]), 1)
        self.assertFalse(any(n["class_type"] in ("AW_PixalViews", "Trellis2Conditioning") for n in graph.values()))
        model = next(n for n in graph.values() if n["class_type"] == "UNETLoader")
        self.assertEqual(model["inputs"]["unet_name"], "pixal3d_bf16.safetensors")

    def test_unapproved_primary_and_changed_file_are_rejected(self):
        record = self.image("mesh_input", "primary")
        with self.assertRaises(store.ApprovalRequired):
            recipes.single_image_mesh_recipe(self.project, self.project, "mesh-stage")
        self.project = self.library.approve_image(self.project["id"], "mesh_input", "primary", record["sha256"],
            "approved", "user", "", self.project["revision"])
        self.library.path(self.project["id"], record["file"]).write_bytes(b"different")
        with self.assertRaises(store.ApprovalRequired):
            recipes.single_image_mesh_recipe(self.project, self.project, "mesh-stage")

    def test_moge_fov_is_horizontal_degrees_of_prepared_image(self):
        self.primary()
        graph = recipes.single_image_mesh_recipe(self.project, self.project, "mesh-stage")["graph"]
        conversion = next(n for n in graph.values() if n["class_type"] == "MoGeGeometryToFOV")
        self.assertEqual((conversion["inputs"]["axis"], conversion["inputs"]["unit"]), ("horizontal", "degrees"))
        self.assertTrue(any(n["class_type"] == "AW_SaveMaster" for n in graph.values()))

    def test_finish_uses_saved_master_and_pec_without_image_or_pixal_models(self):
        self.primary()
        master = {"id": "raw1", "kind": "master", "file": "masters/raw1/checkpoint.json", "stale": False}
        result = recipes.finish_saved_master_recipe(self.project, master, "finish-stage")
        graph = result["graph"]
        self.assertFalse(any(n["class_type"] in ("UNETLoader", "CLIPVisionLoader", "Pixal3DConditioning", "AW_LoadImage") for n in graph.values()))
        unwrap = next(n for n in graph.values() if n["class_type"] == "UnwrapMesh")
        self.assertIn("pec", unwrap["inputs"].values())
        self.assertEqual(next(n for n in graph.values() if n["class_type"] == "AW_LoadMaster")["inputs"]["master_id"], "raw1")

    def test_cpu_uv_fallback_is_rejected_in_new_mode(self):
        self.primary()
        self.project["settings"]["uv_method"] = "adaptive"
        with self.assertRaises(store.CapabilityError):
            recipes.finish_saved_master_recipe(self.project, {"id": "raw1", "stale": False}, "finish-stage")

    def test_game_finishing_uses_saved_master_and_game_settings(self):
        self.primary()
        master = {'id': 'raw1', 'kind': 'master', 'stale': False}
        self.project['artifacts'].append({'id': 'finished1', 'kind': 'mesh', 'export_kind': 'master', 'master': 'raw1', 'stale': False})
        self.project['task_payload'] = {'export_kind': 'game'}
        result = recipes.finish_saved_master_recipe(self.project, master, 'game-stage')
        graph = result['graph']
        self.assertEqual(result['details']['kind'], 'game')
        self.assertEqual(next(n for n in graph.values() if n['class_type']=='DecimateMesh')['inputs']['target_face_count'], self.project['settings']['game_faces'])
        self.assertFalse(any(n['class_type']=='UNETLoader' for n in graph.values()))

    def test_game_finishing_requires_a_completed_matching_master_export(self):
        self.primary()
        self.project['task_payload'] = {'export_kind': 'game'}
        with self.assertRaises(store.ApprovalRequired):
            recipes.finish_saved_master_recipe(self.project, {'id': 'raw1', 'stale': False}, 'game-stage')

    def test_reconstruction_recipe_records_exact_model_hashes(self):
        self.primary()
        result = recipes.single_image_mesh_recipe(self.project, self.project, "mesh-stage")
        self.assertIn("models", result["details"])
        self.assertEqual(result["details"]["models"]["pixal_single"]["sha256"], recipes.MODELS["pixal_single"]["sha256"])


if __name__ == "__main__":
    unittest.main()
