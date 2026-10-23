"""Project edits cannot silently change the image approved for reconstruction."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


spec = importlib.util.spec_from_file_location("agent_project_store", Path(__file__).parents[1] / "store.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AgentProjectTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.library = module.AssetStore(self.temporary.name)
        self.assertTrue(callable(getattr(self.library, "create_project", None)),
                        "AssetStore needs the approved schema-2 project contract")
        self.project = self.library.create_project()
        self.sequence = 0

    def image(self, role="mesh_input"):
        self.sequence += 1
        relative = f"originals/image-{self.sequence}.png"
        path = self.library.path(self.project["id"], relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = f"unchanged source pixels {self.sequence}".encode()
        path.write_bytes(content)
        record = {"id": f"image-{self.sequence}", "file": relative,
                  "sha256": hashlib.sha256(content).hexdigest(), "recipe": {"seed": 42}}
        self.project = self.library.add_revision(self.project["id"], role, record)
        return record

    def approve(self, record, role="mesh_input", decision="approved"):
        self.project = self.library.approve_image(self.project["id"], role, record["id"],
            record["sha256"], decision, "user", "", self.project["revision"])

    def test_fresh_project_has_no_images_jobs_or_approval(self):
        p = self.project
        self.assertEqual(p["schema_version"], 2)
        self.assertEqual(p["profile"], "klein4")
        self.assertEqual(p["settings"]["mesh_backend"], "pixal_single")
        self.assertEqual(p["memory_preset_id"], "standard_16gb")
        self.assertEqual(p["jobs"], [])
        self.assertEqual(p["sources"], [])
        self.assertFalse(any(slot["current"] for slot in p["images"].values()))
        with self.assertRaises(module.ApprovalRequired):
            self.library.mesh_input(p["id"])

    def test_restoring_a_cleared_source_restores_the_description_input(self):
        record = self.image('source')
        self.project = self.library.clear_images(self.project['id'], self.project['revision'])
        self.assertIsNone(self.project['images']['source']['current'])
        self.project = self.library.update_project(self.project['id'], self.project['revision'],
                                                   {'source_selection': [record['id']]})
        self.assertEqual(self.project['images']['source']['current'], record['id'])
        self.assertTrue(self.project['sources'][0]['enabled'])

    def test_stale_revision_or_hash_cannot_approve_or_start(self):
        record = self.image()
        with self.assertRaises(module.ProjectConflict):
            self.library.approve_image(self.project["id"], "mesh_input", record["id"],
                record["sha256"], "approved", "user", "", 0)
        with self.assertRaises(module.ApprovalRequired):
            self.library.approve_image(self.project["id"], "mesh_input", record["id"],
                "0"*64, "approved", "user", "", self.project["revision"])
        self.approve(record)
        with self.assertRaises(module.ProjectConflict):
            self.library.job_snapshot(self.project["id"], 0)
        self.library.path(self.project["id"], record["file"]).write_bytes(b"changed")
        with self.assertRaises(module.ApprovalRequired):
            self.library.mesh_input(self.project["id"])

    def test_settings_only_change_does_not_revoke_pixel_approval(self):
        record = self.image()
        self.approve(record)
        frozen = self.library.job_snapshot(self.project["id"], self.project["revision"])
        self.project = self.library.update_project(self.project["id"], self.project["revision"],
            {"settings": {"requested_seed": 92}, "profile": "qwen21"})
        self.assertEqual(self.library.mesh_input(self.project["id"])["id"], record["id"])
        self.assertEqual(frozen["profile"], "klein4")
        self.assertEqual(frozen["settings"]["requested_seed"], -1)

    def test_primary_edit_stales_mesh_and_package_but_reference_edit_only_stales_package(self):
        record = self.image()
        self.approve(record)
        self.project["artifacts"] = [{"id": "mesh1", "kind": "mesh", "stale": False},
                                     {"id": "package1", "kind": "package", "stale": False}]
        self.library.save(self.project)
        self.image("reference_back")
        artifacts = self.project["artifacts"]
        self.assertFalse(artifacts[0]["stale"])
        self.assertTrue(artifacts[1]["stale"])
        self.image()
        self.assertTrue(all(a["stale"] for a in self.project["artifacts"]))
        with self.assertRaises(module.ApprovalRequired):
            self.library.mesh_input(self.project["id"])

    def test_reuse_legacy_parameters_creates_clean_draft(self):
        legacy = self.library.create("Legacy ten views")
        manifest = self.library.path(legacy["id"], "asset.json")
        original = manifest.read_bytes()
        reused = self.library.reuse_parameters(legacy["id"])
        self.assertNotEqual(reused["id"], legacy["id"])
        self.assertEqual(reused["schema_version"], 2)
        self.assertEqual(reused["settings"]["mesh_backend"], "pixal_single")
        self.assertFalse(any(slot["current"] for slot in reused["images"].values()))
        self.assertEqual(reused["jobs"], [])
        self.assertEqual(manifest.read_bytes(), original)
        self.assertEqual(json.loads(original)["schema"], 1)

    def test_explicit_image_reuse_copies_original_but_requires_new_approval(self):
        record = self.image()
        self.approve(record)
        reused = self.library.reuse_parameters(self.project["id"], include_images=True)
        copied = reused["images"]["mesh_input"]["revisions"][0]
        self.assertEqual(self.library.path(reused["id"], copied["file"]).read_bytes(),
                         self.library.path(self.project["id"], record["file"]).read_bytes())
        with self.assertRaises(module.ApprovalRequired):
            self.library.mesh_input(reused["id"])

    def test_source_edits_preserve_originals_and_approved_generated_pixels(self):
        source = self.image("source")
        primary = self.image()
        self.approve(primary)
        self.image("source")
        self.assertEqual(len(self.project["sources"]), 2)
        self.assertTrue(self.library.path(self.project["id"], source["file"]).is_file())
        self.assertEqual(self.library.mesh_input(self.project["id"])["id"], primary["id"])

    def test_unknown_mutations_cannot_replace_approval_or_queue_state(self):
        with self.assertRaises(ValueError):
            self.library.update_project(self.project["id"], self.project["revision"],
                                        {"jobs": [{"id": "invented"}]})
        self.assertEqual(self.library.load(self.project["id"])["jobs"], [])


if __name__ == "__main__":
    unittest.main()
