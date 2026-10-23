"""Lifecycle contracts around the real coordinator; the native worker is external."""
import asyncio
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("resource_lifecycle", Path(__file__).parents[1] / "resource_lifecycle.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class NativeWorker:
    def __init__(self):
        self.running = []
        self.pending = []
        self.history = {}
        self.flags = {}
        self.models = 1
        self.rss = 4096
        self.live = 1024

    def get_current_queue_volatile(self):
        return self.running, self.pending

    def get_tasks_remaining(self):
        return len(self.running) + len(self.pending)

    def get_history(self, prompt):
        return {prompt: self.history[prompt]} if prompt in self.history else {}

    def set_flag(self, key, value):
        self.flags[key] = value

    def get_flags(self, reset=False):
        return self.flags.copy()

    def sample(self):
        return {"process_rss": self.rss, "torch_allocated": self.live,
                "torch_reserved": self.live, "vram_used": self.live,
                "ram_used": self.rss, "ram_available": 8192, "loaded_models": self.models}

    async def consume(self, finish=True):
        while not self.flags:
            await asyncio.sleep(.001)
        self.flags.clear()
        # Consuming flags precedes actual worker cleanup. The coordinator must wait.
        await asyncio.sleep(.01)
        if finish:
            self.models, self.rss, self.live = 0, 512, 0


class ResourceLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.native = NativeWorker()
        self.saved = []
        self.manager = module.ResourceLifecycle(
            self.native, self.native.sample, lambda owner, report: self.saved.append((owner, report)),
            interval=.002, timeout=.1, settle_samples=3, live_tensor_limit=32)

    async def test_release_waits_for_worker_and_records_observed_memory(self):
        consumer = asyncio.create_task(self.native.consume())
        report = await self.manager.release("manual")
        await consumer
        self.assertEqual(report["status"], "released")
        self.assertEqual(report["after"]["process_rss"], 512)
        self.assertEqual(report["after"]["torch_allocated"], 0)
        self.assertEqual(report["before"]["process_rss"], 4096)

    async def test_consumed_flags_are_not_proof_of_release(self):
        consumer = asyncio.create_task(self.native.consume(finish=False))
        with self.assertRaisesRegex(ValueError, "memory"):
            await self.manager.release("manual")
        await consumer
        self.assertEqual(self.manager.status()["status"], "failed")

    async def test_idle_worker_missed_notification_is_reawakened(self):
        # The native worker may still be doing post-job GC when flags are set.
        # Its next queue wait cannot hear that earlier notification.
        notified = asyncio.Event()
        original = self.native.set_flag
        calls = 0

        def set_flag(key, value):
            nonlocal calls
            original(key, value)
            calls += 1
            if calls > 2:
                notified.set()

        self.native.set_flag = set_flag

        async def sleeping_worker():
            await notified.wait()
            await self.native.consume()

        worker = asyncio.create_task(sleeping_worker())
        try:
            report = await self.manager.release("stage finished")
            self.assertEqual(report["status"], "released")
            self.assertEqual(report["after"]["loaded_models"], 0)
        finally:
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

    async def test_active_foreign_job_is_never_released(self):
        self.native.running = [(0, "foreign")]
        with self.assertRaisesRegex(ValueError, "running"):
            await self.manager.release("manual")
        self.assertEqual(self.native.flags, {})
        self.assertEqual(self.native.running, [(0, "foreign")])

    async def test_completed_and_failed_owned_prompts_release_without_ui(self):
        for outcome in ("success", "error"):
            with self.subTest(outcome=outcome):
                self.setUp()
                self.native.history["ours"] = {"status": {"completed": outcome == "success", "status_str": outcome}}
                consumer = asyncio.create_task(self.native.consume())
                self.manager.track("ours", ("asset", "job"))
                await self.manager.barrier()
                await consumer
                self.assertEqual(len(self.saved), 1)
                self.assertEqual(self.saved[0][1]["status"], "released")
                self.assertEqual(self.saved[0][1]["prompt_id"], "ours")
                self.assertEqual(self.manager.status()["pending_jobs"], 0)

    async def test_cancel_waits_for_queue_drain_and_then_releases(self):
        self.native.running = [(0, "ours")]
        self.manager.track("ours", ("asset", "job"))
        self.manager.cancel("ours")
        await asyncio.sleep(.008)
        self.assertEqual(self.native.flags, {})
        self.native.running = []
        consumer = asyncio.create_task(self.native.consume())
        await self.manager.barrier()
        await consumer
        self.assertEqual(self.saved[0][1]["reason"], "cancelled")

    async def test_next_stage_cannot_pass_failed_cleanup(self):
        self.native.history["ours"] = {"status": {"completed": True, "status_str": "success"}}
        self.manager.track("ours", ("asset", "job"))
        consumer = asyncio.create_task(self.native.consume(finish=False))
        with self.assertRaisesRegex(ValueError, "memory"):
            await self.manager.barrier()
        await consumer
        self.assertEqual(self.saved[0][1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
