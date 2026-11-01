"""Pipeline state is lazy, immutable and bound to one appearance lineage."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("pipeline_contract_store", Path(__file__).parents[1] / "store.py")
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)

class PipelineStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = store.AssetStore(self.temp.name)
        self.project = self.library.create_project()

    def initialize(self):
        fn = getattr(self.library, "update_pipeline", None)
        self.assertTrue(callable(fn), "AssetStore must own revision-safe pipeline state")
        return fn(self.project["id"], self.project["revision"], {})

    def test_legacy_read_never_initializes_or_rewrites_pipeline(self):
        path = self.library.path(self.project["id"], "asset.json")
        before = path.read_bytes()
        self.assertNotIn("pipeline", self.library.load(self.project["id"]))
        self.assertEqual(before, path.read_bytes())

    def test_explicit_initialization_uses_validated_defaults_preserving_old_settings(self):
        before = copy.deepcopy(self.project["settings"])
        result = self.initialize()
        self.assertEqual(result["pipeline"]["version"], "validated_v1")
        self.assertEqual(result["pipeline"]["settings"]["texture_provider"], "trellis2")
        self.assertEqual(result["pipeline"]["settings"]["output_variant"], "balanced_250k")
        self.assertEqual(result["pipeline"]["settings"]["refine_resolution"], 1536)
        self.assertEqual(before, result["settings"])

    def test_selecting_new_geometry_does_not_export_the_previous_appearance(self):
        p=self.initialize()
        for aid,kind in (("g1","geometry"),("g2","geometry"),("paint1","mesh")):
            path=self.library.path(p["id"],aid+".npz");path.write_bytes(aid.encode())
            p["artifacts"].append({"id":aid,"kind":kind,"file":path.name,"sha256":store.digest(path),"geometry_id":"g1" if kind=="mesh" else None})
        p["pipeline"].update(selected_geometry_id="g1",selected_appearance_id="paint1",selected_texture_id="paint1")
        self.library.save(p)
        q=self.library.select_pipeline_artifact(p["id"],p["revision"],"g2")
        self.assertIsNone(q["pipeline"]["selected_appearance_id"])
        self.assertEqual(len(q["artifacts"]),3)

    def test_wrong_revision_and_unknown_provider_are_rejected(self):
        result = self.initialize()
        with self.assertRaises(store.ProjectConflict):
            self.library.update_pipeline(result["id"], self.project["revision"], {})
        with self.assertRaises(ValueError):
            self.library.update_pipeline(result["id"], result["revision"], {"texture_provider": "imaginary"})
        with self.assertRaises(ValueError):
            self.library.update_pipeline(result["id"], result["revision"], {"texture_steps": float("nan")})

    def test_selection_checks_hash_project_and_appearance_without_deleting_prior_outputs(self):
        p = self.initialize()
        def add(name, parent=None, variant="detailed"):
            path = self.library.path(p["id"], "exports/" + name + ".glb")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            r = {"id":name,"kind":"mesh","file":"exports/"+name+".glb","sha256":store.digest(path),
                 "parent_artifact_id":parent,"variant":variant,"pipeline_version":"validated_v1","stale":False}
            p["artifacts"].append(r)
            return r
        base = add("base")
        balanced = add("balanced", "base", "balanced_250k")
        edited = add("edited", "balanced", "balanced_250k")
        edited["material_revision"] = 1
        unrelated = add("other")
        self.library.save(p)
        fn = getattr(self.library, "select_pipeline_artifact", None)
        self.assertTrue(callable(fn), "Pipeline selection must use the same project owner")
        selected = fn(p["id"], p["revision"], "edited")
        self.assertEqual(selected["pipeline"]["selected_appearance_id"], "edited")
        self.assertEqual(len(selected["artifacts"]), 4)
        self.library.path(p["id"], edited["file"]).write_bytes(b"changed")
        with self.assertRaises(ValueError):
            fn(p["id"], selected["revision"], "edited")
        with self.assertRaises(ValueError):
            fn(p["id"], selected["revision"], "outside-project")

class PipelineRecordingTests(PipelineStateTests):
    def test_cancelled_stage_cannot_publish_current_output(self):
        p=self.initialize()
        p["jobs"]=[{"id":"job1","state":"running","cancel_requested":True,"artifacts":[],
            "snapshot":{"images":{"mesh_input":{"approved":"image1"}}},
            "stages":[{"id":"stage1","state":"running"}]}]
        self.library.save(p)
        path=self.library.path(p["id"],"exports/late.glb");path.parent.mkdir(parents=True);path.write_bytes(b"late")
        with self.assertRaises(store.JobConflict):
            self.library.record_pipeline_artifact(p["id"],"stage1",{"id":"late","kind":"mesh","file":"exports/late.glb","sha256":store.digest(path)})

    def test_changed_parent_cannot_receive_an_output(self):
        p=self.initialize()
        p["images"]["mesh_input"]["approved"]="image1"
        p["jobs"]=[{"id":"job1","state":"running","artifacts":[],
            "snapshot":{"images":{"mesh_input":{"approved":"image1"}}},"stages":[{"id":"stage1","state":"running"}]}]
        folder=self.library.path(p["id"],"exports");folder.mkdir(parents=True)
        parent=folder/"parent.glb";parent.write_bytes(b"original")
        p["artifacts"].append({"id":"parent","kind":"mesh","file":"exports/parent.glb","sha256":store.digest(parent),"stale":False})
        output=folder/"out.glb";output.write_bytes(b"output")
        self.library.save(p);parent.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.library.record_pipeline_artifact(p["id"],"stage1",{"id":"out","kind":"mesh","parent_artifact_id":"parent","file":"exports/out.glb","sha256":store.digest(output)})

if __name__ == "__main__":
    unittest.main()
