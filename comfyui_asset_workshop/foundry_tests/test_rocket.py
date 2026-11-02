"""Automatic continuation uses the same checkpoints, cancellation and exports as the wizard."""
import asyncio
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_to_3d.runs import WizardRuns


class RocketTests(unittest.IsolatedAsyncioTestCase):
    def service(self, root, variants):
        class Native:
            def active_ids(self):return set()
        class Lifecycle:
            async def release(self, reason):return {"status":"released"}
        service=WizardRuns(root,root,root,Native(),Lifecycle,lambda:False,None,{})
        run={"id":"a"*32,"status":"ready","stage":"","stages":{},"outputs":{},"events":[],
             "selection":{"variants":{k:{"formats":["glb"]} for k in variants}}}
        service.save(run)
        service.metadata=lambda r:{}
        service.prepare_dependencies=AsyncMock()
        return service,run

    async def test_dependencies_finish_before_first_generation(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["game_compact"])
            service.prepare_dependencies=WizardRuns.prepare_dependencies.__get__(service)
            service.fresh=Mock(return_value=False)
            order=[]
            async def stage(run,name,**kwargs):order.append("run:"+name)
            service.stage=stage
            with patch("foundry.workflows.image_to_3d.readiness.ensure",side_effect=lambda name,*args:order.append("prepare:"+name)):
                await service.execute(run,"rocket")
            self.assertEqual(order[:5],["prepare:turnaround","prepare:geometry","prepare:refinement","prepare:texture","run:turnaround"])

    async def test_dependency_failure_stops_before_generation_and_keeps_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["game_compact"])
            run["stages"]["refinement"]={"saved":True}
            service.prepare_dependencies=WizardRuns.prepare_dependencies.__get__(service)
            service.fresh=Mock(return_value=False)
            service.stage=AsyncMock()
            with patch("foundry.workflows.image_to_3d.readiness.ensure",side_effect=ValueError("Access unavailable")):
                await service.execute(run,"finish")
            service.stage.assert_not_awaited()
            self.assertEqual(run["status"],"failed")
            self.assertEqual(run["stages"]["refinement"],{"saved":True})

    async def test_preflight_reuses_saved_stages_and_print_only_avoids_texture(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["print"])
            service.prepare_dependencies=WizardRuns.prepare_dependencies.__get__(service)
            service.fresh=Mock(side_effect=lambda run,name:name=="turnaround")
            with patch("foundry.workflows.image_to_3d.readiness.ensure") as ensure:
                await service.prepare_dependencies(run,"rocket")
            self.assertEqual([call.args[0] for call in ensure.call_args_list],["geometry","refinement"])

    async def test_rocket_print_only_keeps_geometry_and_skips_texture_and_game_bakes(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["print"])
            service.stage=AsyncMock()
            await service.execute(run,"rocket")
            self.assertEqual([c.args[1] for c in service.stage.await_args_list],
                             ["turnaround","geometry","refinement","print","package"])
            self.assertEqual(run["status"],"complete")
            self.assertEqual(run["cleanup"]["status"],"released")

    async def test_rocket_selected_game_budget_never_runs_unselected_quad_branch(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["game_compact"])
            service.stage=AsyncMock()
            await service.execute(run,"rocket")
            self.assertEqual([c.args[1] for c in service.stage.await_args_list],
                             ["turnaround","geometry","refinement","texture","compact","package"])

    async def test_duplicate_start_returns_same_job_and_completed_retry_does_not_resubmit(self):
        with tempfile.TemporaryDirectory() as temp:
            service,run=self.service(temp,["print"])
            gate=asyncio.Event()
            async def execute(run,op):
                await gate.wait();run["status"]="complete";service.tasks.pop(run["id"],None);service.save(run)
            service.execute=AsyncMock(side_effect=execute)
            first=service.start(run["id"],"rocket","agent",request_id="same-request")
            task=service.tasks[run["id"]]
            again=service.start(run["id"],"rocket","agent",request_id="same-request")
            self.assertEqual(first["id"],again["id"])
            gate.set();await task
            service.start(run["id"],"rocket","agent",request_id="same-request")
            self.assertEqual(service.execute.call_count,1)
            with self.assertRaises(ValueError):service.start(run["id"],"finish","agent",request_id="same-request")

    async def test_error_or_cancel_preserves_completed_stage_and_releases_memory(self):
        for failure in [ValueError("Test stage failed"),asyncio.CancelledError()]:
            with tempfile.TemporaryDirectory() as temp:
                service,run=self.service(temp,["print"])
                async def stage(r,name,**kwargs):
                    if name=="geometry":raise failure
                    r["stages"][name]={"saved":True}
                service.stage=stage
                await service.execute(run,"rocket")
                self.assertIn("turnaround",run["stages"])
                self.assertNotIn("package",run["stages"])
                self.assertIn(run["status"],["failed","cancelled"])
                self.assertEqual(run["cleanup"]["status"],"released")

if __name__=="__main__":unittest.main()
