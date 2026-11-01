"""UI and MCP must share one revision-safe job and visible submission gate."""
import asyncio
import copy
import importlib
from pathlib import Path
import tempfile
import unittest

from test_reference_pair import store


class NativeQueue:
    def __init__(self):
        self.active = set()
        self.finished = asyncio.Event()

    def active_ids(self):
        return set(self.active)

    async def submit(self, graph, prompt_id, client_id):
        self.active.add(prompt_id)
        return prompt_id

    async def wait(self, prompt_id, timeout, cancelled):
        await self.finished.wait()
        self.active.discard(prompt_id)
        return {"status": {"status_str": "success", "completed": True}}

    def cancel(self, prompt_id):
        self.active.discard(prompt_id)
        self.finished.set()


class Lifecycle:
    def __init__(self, native):
        self.native = native

    async def barrier(self):
        if self.native.active:
            raise ValueError("Wait for the other workflow before releasing memory.")

    def track(self, prompt_id, owner):
        pass

    def cancel(self, prompt_id):
        pass

    def status(self):
        return {"status": "released", "pending_jobs": 0}


class AgentJobTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        location = Path(__file__).parents[1] / "jobs.py"
        self.assertTrue(location.is_file(), "The shared durable job owner has not been implemented")
        self.module = importlib.import_module("_aw_pair_contract.jobs")
        self.folder = tempfile.TemporaryDirectory()
        self.library = store.AssetStore(self.folder.name)
        self.project = self.library.create_project()
        self.project = self.library.update_project(self.project["id"], self.project["revision"], {"prompt": "A fish"})
        self.native = NativeQueue()
        self.events = asyncio.Queue()
        self.engine = self.module.JobCoordinator(self.library, self.native, Lifecycle(self.native),
            lambda project, snapshot, stage, job: {"graph": {"1": {"class_type": "TestOutput", "inputs": {}}}},
            lambda event: self.events.put_nowait(event), visible_timeout=1)
        self.engine.connect("desktop", True)
        self.addAsyncCleanup(self.cleanup)

    async def cleanup(self):
        for task in list(self.engine.tasks.values()):
            task.cancel()
        await asyncio.gather(*list(self.engine.tasks.values()), return_exceptions=True)
        self.folder.cleanup()

    def start(self, key="request1", **kwargs):
        return self.engine.start(self.project["id"], self.project["revision"],
                                 "create_image", key, kwargs)

    async def test_same_request_key_returns_same_job_and_never_queues_twice(self):
        first = self.start()
        second = self.start()
        self.assertEqual(first["id"], second["id"])
        saved = self.library.load(self.project["id"])
        self.assertEqual(len(saved["jobs"]), 1)
        self.assertEqual(saved["jobs"][0]["prompt_ids"], [])

    async def test_changed_snapshot_with_same_key_conflicts(self):
        self.start()
        with self.assertRaises(store.JobConflict):
            self.start(role="mesh_input")

    async def test_no_connected_visible_client_prevents_submission(self):
        self.engine.connect("desktop", False)
        with self.assertRaises(store.JobConflict):
            self.start()
        self.assertEqual(self.library.load(self.project["id"])["jobs"], [])

    async def test_wrong_graph_ack_is_rejected(self):
        job = self.start()
        event = await asyncio.wait_for(self.events.get(), 1)
        with self.assertRaises(store.JobConflict):
            self.engine.ack_visible(job["id"], event["stage_id"], "wrong", "desktop")
        self.assertEqual(self.engine.get(self.project["id"], job["id"])["prompt_ids"], [])

    async def test_ui_and_agent_see_same_project_job_and_error(self):
        job = self.start()
        user = self.engine.get(self.project["id"], job["id"])
        agent = self.engine.get(self.project["id"], job["id"])
        self.assertEqual(user, agent)
        self.assertNotIn("snapshot", user)
        self.assertEqual(user["snapshot_revision"], self.project["revision"])

    async def test_reconnect_does_not_requeue(self):
        job = self.start()
        self.engine.connect("desktop", False)
        self.engine.connect("desktop", True)
        self.assertEqual(self.start()["id"], job["id"])
        self.assertEqual(len(self.library.load(self.project["id"])["jobs"]), 1)

    async def test_cancel_deletes_or_interrupts_only_owned_prompt_ids(self):
        job = self.start()
        event = await asyncio.wait_for(self.events.get(), 1)
        self.engine.ack_visible(job["id"], event["stage_id"], event["graph_hash"], "desktop")
        for _ in range(20):
            if self.engine.get(self.project["id"], job["id"])["prompt_ids"]:
                break
            await asyncio.sleep(0)
        self.native.active.add("foreign-prompt")
        self.engine.cancel(self.project["id"], job["id"])
        await asyncio.wait_for(asyncio.gather(*list(self.engine.tasks.values()), return_exceptions=True), 1)
        self.assertEqual(self.native.active, {"foreign-prompt"})
        self.assertEqual(self.engine.get(self.project["id"], job["id"])["state"], "cancelled")

    async def test_restart_reconciliation_never_blindly_resumes(self):
        job = self.start()
        self.engine.reconcile()
        actual = self.engine.get(self.project["id"], job["id"])
        self.assertEqual(actual["state"], "interrupted")
        self.assertEqual(actual["prompt_ids"], [])

    async def test_snapshot_does_not_recursively_embed_prior_jobs(self):
        self.start()
        p = self.library.load(self.project["id"])
        snapshot = self.library.job_snapshot(p["id"], p["revision"])
        self.assertEqual(snapshot["jobs"], [])

    async def test_retry_preserves_completed_stage_without_requeuing_it(self):
        job = self.start()
        self.engine.cancel(self.project["id"], job["id"])
        await asyncio.gather(*list(self.engine.tasks.values()), return_exceptions=True)
        saved = self.library.load(self.project["id"])
        previous = saved["jobs"][0]
        previous["stages"][0].update(state="completed", result={"revision": "already-created"})
        previous["state"] = "failed"
        self.library.save(saved)
        self.project = self.library.load(self.project["id"])
        resumed = self.start("retry1", resume_job_id=job["id"])
        self.assertEqual(resumed["stages"][0]["state"], "completed")
        self.assertEqual(resumed["stages"][0]["result"], {"revision": "already-created"})
        await asyncio.gather(*list(self.engine.tasks.values()), return_exceptions=True)
        self.assertEqual(self.engine.get(self.project["id"], resumed["id"])["prompt_ids"], [])

    async def test_retry_retains_the_material_session_and_variant_payload(self):
        first=self.engine.start(self.project['id'],self.project['revision'],'apply_materials','material1',{'session_id':'session1'})
        self.engine.cancel(self.project['id'],first['id'])
        await asyncio.gather(*list(self.engine.tasks.values()),return_exceptions=True)
        saved=self.library.load(self.project['id'])
        resumed=self.engine.start(saved['id'],saved['revision'],'apply_materials','retry-material1',{'resume_job_id':first['id']})
        self.assertEqual(self.engine._job(saved['id'],resumed['id'])['payload'].get('session_id'),'session1')

    async def test_geometry_stage_uses_mesh_seed_instead_of_image_seed(self):
        project=self.library.update_project(self.project['id'],self.project['revision'],{'settings':{'requested_seed':77,'mesh_requested_seed':42}})
        captured=[]
        self.engine.build_stage=lambda project,snapshot,stage,job:(captured.append(snapshot['settings']['seed']) or {'graph':{'1':{'class_type':'TestOutput','inputs':{}}}})
        job=self.engine.start(project['id'],project['revision'],'finish_mesh','seed-check',{})
        saved=self.library.load(project['id']);saved['jobs'][-1]['stages'][0]['name']='geometry';self.library.save(saved)
        await asyncio.wait_for(self.events.get(),1)
        self.assertEqual(captured,[42])
        self.engine.cancel(project['id'],job['id'])


if __name__ == "__main__":
    unittest.main()
