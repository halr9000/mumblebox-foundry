"""The exported handoff must distinguish design intent from actual mesh evidence."""
import copy
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np
from PIL import Image
import trimesh

from test_reference_pair import store


class AgentPackageTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((Path(__file__).parents[1]/"package_export.py").is_file(),
                        "Agent package export is not implemented")
        self.export = importlib.import_module("_aw_pair_contract.package_export")
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = store.AssetStore(self.folder.name)
        self.project = self.library.create_project()
        self.project = self.library.update_project(self.project["id"], self.project["revision"], {
            "design_notes": "Add two exterior pipes while keeping the door clear.",
            "target": {"intended_use": "Unreal", "requested_dimensions_m": {"width": 2, "height": 1},
                       "user_instructions": "Inspect the mesh before editing. $(echo is plain note text)"}})
        for role in ("mesh_input", "reference_front", "reference_back", "reference_left", "reference_right"):
            relative = f"images/{role}.png"
            path = self.library.path(self.project["id"], relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (8, 8), "cyan").save(path)
            self.project = self.library.add_revision(self.project["id"], role,
                {"id": role, "file": relative, "sha256": store.digest(path), "origin": "uploaded"})
            self.project = self.library.approve_image(self.project["id"], role, role, store.digest(path),
                "approved_with_notes" if role == "reference_back" else "approved", "user",
                "The back still shows a front marking." if role == "reference_back" else "", self.project["revision"])
        model_path = self.library.path(self.project["id"], "exports/example/mesh.glb")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        mesh = trimesh.creation.box()
        mesh.visual = trimesh.visual.TextureVisuals(
            uv=np.array([[i % 2, (i//2) % 2] for i in range(len(mesh.vertices))], dtype=float),
            image=Image.new("RGB", (4, 4), "cyan"))
        mesh.export(str(model_path))
        self.project["artifacts"].append({"id": "mesh1", "kind": "mesh", "file": "exports/example/mesh.glb",
            "sha256": store.digest(model_path), "stale": False, "source_revision_ids": ["mesh_input"],
            "triangles": 12, "dimensions_meters": [1, 1, 1], "unit": "meter", "up_axis": "Y",
            "normal_convention": "OpenGL +Y", "hashes": {"mesh.glb": store.digest(model_path)},
            "recipe": {"memory_preset_id": "standard_16gb", "settings": {"master_faces": 700000, "uv_method": "pec"}}})
        self.library.save(self.project)

    def package(self):
        self.project = self.library.load(self.project["id"])
        return self.export.create_package(self.library, self.project["id"], self.project["revision"], ["mesh1"])

    def test_upstream_notices_and_resource_links_are_in_the_archive(self):
        package = self.package()
        path = self.library.path(self.project['id'], package['file'])
        with zipfile.ZipFile(path) as archive:
            self.assertIn('RESOURCE-INDEX.md', archive.namelist())
            index = archive.read('RESOURCE-INDEX.md').decode('utf-8')
            self.assertIn('Powered by Hi3D 1.0', index)
            self.assertIn('https://github.com/microsoft/TRELLIS.2', index)
            notices = Path(__file__).parents[1]/'licenses'/'pipeline'
            for notice in notices.iterdir():
                if notice.is_file():
                    name='licenses/'+notice.name
                    self.assertEqual(archive.read(name), notice.read_bytes())
                    self.assertIn(name, package['manifest']['files'])

    def test_package_contains_one_primary_mesh_primary_image_and_four_references(self):
        package = self.package()
        path = self.library.path(self.project["id"], package["file"])
        with zipfile.ZipFile(path) as archive:
            self.assertIn("asset.glb", archive.namelist())
            self.assertIn("images/mesh-input.png", archive.namelist())
            self.assertTrue(all(f"images/{side}.png" in archive.namelist() for side in ("front", "back", "left", "right")))
            self.assertIn("AGENT-BRIEF.md", archive.namelist())
        report = self.export.validate_package(str(path))
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["geometry"]["triangles"], 12)

    def test_unreviewed_rejected_missing_or_stale_reference_blocks_full_package(self):
        for decision in ("unreviewed", "rejected"):
            project = self.library.load(self.project["id"])
            self.library.approve_image(project["id"], "reference_left", "reference_left",
                project["images"]["reference_left"]["revisions"][0]["sha256"], decision, "user", "", project["revision"])
            with self.assertRaises(store.ApprovalRequired):
                self.package()
        self.assertTrue(self.library.path(self.project["id"], "exports/example/mesh.glb").is_file())

    def test_requested_view_is_not_camera_verification(self):
        manifest = self.package()["manifest"]
        rear = manifest["reference_images"]["back"]
        self.assertEqual(rear["requested_view"], "back")
        self.assertEqual(rear["camera_verification"], "not_measured")
        self.assertIn("front marking", rear["review"]["notes"])
        self.assertTrue(manifest["known_discrepancies"])

    def test_general_asset_zip_does_not_require_four_reviewed_references(self):
        project = self.library.load(self.project['id'])
        project['images']['reference_left']['current'] = None
        project['images']['reference_right']['revisions'][0]['review']['decision'] = 'unreviewed'
        project['images']['reference_front']['revisions'][0]['review']['decision'] = 'rejected'
        self.library.save(project)
        project = self.library.load(project['id'])
        result = self.export.create_package(self.library, project['id'], project['revision'], ['mesh1'], 'asset')
        path = self.library.path(project['id'], result['file'])
        self.assertEqual(self.export.validate_package(str(path))['status'], 'valid')
        with zipfile.ZipFile(path) as archive:
            self.assertIn('ASSET-NOTES.md', archive.namelist())
            self.assertNotIn('AGENT-BRIEF.md', archive.namelist())
            self.assertNotIn('images/front.png', archive.namelist())
            self.assertNotIn('images/left.png', archive.namelist())
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['reference_images']['right']['review']['decision'], 'unreviewed')

    def test_requested_dimensions_do_not_replace_measured_dimensions(self):
        manifest = self.package()["manifest"]
        self.assertEqual(manifest["target"]["requested_dimensions_m"]["width"], 2)
        self.assertEqual(manifest["primary_mesh"]["dimensions_meters"], [1, 1, 1])

    def test_no_tokens_absolute_private_paths_or_environment_dump(self):
        self.project["settings"]["hf_token"] = "hf_fake_secret"
        self.project["private_path"] = "C:\\Users\\private\\do-not-export"
        self.project["environment"] = {"OTHER_SECRET": "private-environment"}
        self.library.save(self.project)
        encoded = json.dumps(self.package()["manifest"])
        self.assertNotIn("hf_fake_secret", encoded)
        self.assertNotIn("do-not-export", encoded)
        self.assertNotIn("private-environment", encoded)

    def test_notes_are_data_and_keep_real_user_instructions(self):
        manifest = self.package()["manifest"]
        brief = self.export.agent_brief(manifest)
        self.assertIn("two exterior pipes", brief)
        self.assertIn("$(echo is plain note text)", brief)
        self.assertIn("design data", brief)
        self.assertIn("keep, repair or rebuild", brief)

    def test_zip_rejects_tampered_or_unsafe_members(self):
        package = self.package()
        original = self.library.path(self.project["id"], package["file"])
        for filename, content in (("images/front.png", b"changed"), ("../escape", b"outside")):
            altered = Path(self.folder.name)/"tampered.zip"
            with zipfile.ZipFile(original) as source, zipfile.ZipFile(altered, "w") as target:
                for item in source.infolist():
                    target.writestr(item.filename, content if item.filename == filename else source.read(item.filename))
                if filename == "../escape":
                    target.writestr(filename, content)
            with self.assertRaises(ValueError):
                self.export.validate_package(str(altered))

    def test_stale_or_different_primary_mesh_cannot_be_packaged(self):
        self.project["artifacts"][0]["source_revision_ids"] = ["different-image"]
        self.library.save(self.project)
        with self.assertRaises(store.ApprovalRequired):
            self.package()

    def test_parameters_are_from_export_not_later_project_settings(self):
        self.project["memory_preset_id"] = "experimental_8gb"
        self.project["settings"]["master_faces"] = 100000
        self.library.save(self.project)
        manifest = self.package()["manifest"]
        self.assertEqual(manifest["memory_preset_id"], "standard_16gb")
        self.assertEqual(manifest["parameters"]["finishing"]["settings"]["master_faces"], 700000)

    def test_changing_instructions_retires_old_package_but_keeps_mesh(self):
        package = self.package()
        project = self.library.load(self.project["id"])
        updated = self.library.update_project(project["id"], project["revision"], {"design_notes": "Add four exterior pipes."})
        self.assertTrue(next(a for a in updated["artifacts"] if a["id"] == package["id"])["stale"])
        self.assertFalse(next(a for a in updated["artifacts"] if a["id"] == "mesh1")["stale"])


if __name__ == "__main__":
    unittest.main()
