"""Observe owned jobs and release native execution caches at idle boundaries.

No model tensors are retained here. The native prompt worker performs the reset;
we do not reset its executor or unload models concurrently with inference.
"""
import asyncio
import copy
import time


class ResourceLifecycle:
    def __init__(self, queue, sample, record, *, interval=.5, timeout=60,
                 settle_samples=4, live_tensor_limit=256 * 1024**2):
        self.queue, self.sample, self.record = queue, sample, record
        self.interval, self.timeout = interval, timeout
        self.settle_samples, self.live_tensor_limit = settle_samples, live_tensor_limit
        self.lock = asyncio.Lock()
        self.tasks = {}
        self.cancelled = set()
        self.state = {"status": "idle"}

    def status(self):
        return {**copy.deepcopy(self.state), "pending_jobs": len(self.tasks)}

    @staticmethod
    def peaks(previous, current):
        # One maximum per metric, not an ever-growing stream of samples.
        return {key: max(previous.get(key, 0), current[key]) for key in
                ("process_rss", "torch_allocated", "torch_reserved", "vram_used", "ram_used")}

    async def release(self, reason):
        async with self.lock:
            if self.queue.get_tasks_remaining():
                raise ValueError("Comfy has a queued or running job. Memory release waits until it is idle.")
            before = self.sample()
            report = {"status": "releasing", "reason": reason, "before": before,
                      "started": time.time(), "peak_observed": self.peaks({}, before)}
            self.state = report
            self.queue.set_flag("unload_models", True)
            self.queue.set_flag("free_memory", True)
            deadline = time.monotonic() + self.timeout
            stable, previous = 0, None
            while time.monotonic() < deadline:
                await asyncio.sleep(self.interval)
                after = self.sample()
                report["after"] = after
                report["peak_observed"] = self.peaks(report["peak_observed"], after)
                flags = self.queue.get_flags(reset=False)
                if self.queue.get_tasks_remaining():
                    report["status"] = "failed"
                    report["error"] = "Another Comfy job started during memory release. Wait for it, then use Unload models before continuing."
                    raise ValueError(report["error"])
                # A notification during post-job GC can precede the worker's
                # next queue wait. Wake it again only for unconsumed requests.
                for flag in ("unload_models", "free_memory"):
                    if flags.get(flag):
                        self.queue.set_flag(flag, True)
                ready = (not flags.get("free_memory") and not flags.get("unload_models")
                         and after["loaded_models"] == 0
                         and after["torch_allocated"] <= self.live_tensor_limit)
                if ready and previous is not None:
                    stable = stable + 1 if (abs(after["process_rss"] - previous["process_rss"]) < 64 * 1024**2
                                           and abs(after["torch_allocated"] - previous["torch_allocated"]) < 16 * 1024**2) else 0
                else:
                    stable = 0
                previous = after if ready else None
                if stable >= self.settle_samples:
                    report.update(status="released", finished=time.time())
                    return copy.deepcopy(report)
            report.update(status="failed", finished=time.time(),
                          error="Comfy memory did not finish releasing within 60 seconds. Your saved results are intact. Retry Unload models before another heavy stage.")
            raise ValueError(report["error"])

    def track(self, prompt_id, owner):
        if prompt_id not in self.tasks:
            self.tasks[prompt_id] = asyncio.create_task(self._watch(prompt_id, owner))

    def cancel(self, prompt_id):
        if prompt_id in self.tasks:
            self.cancelled.add(prompt_id)

    async def _watch(self, prompt_id, owner):
        before = self.sample()
        peak = self.peaks({}, before)
        started = time.monotonic()
        seen = False
        report = None
        try:
            while True:
                current = self.sample()
                peak = self.peaks(peak, current)
                running, pending = self.queue.get_current_queue_volatile()
                active = {item[1] for item in running + pending}
                seen = seen or prompt_id in active
                history = self.queue.get_history(prompt_id).get(prompt_id)
                done = history is not None or prompt_id in self.cancelled or seen
                if prompt_id not in active and done:
                    if active:
                        # Another workflow is running; never interrupt it to free memory.
                        await asyncio.sleep(self.interval)
                        continue
                    reason = "cancelled" if prompt_id in self.cancelled else "stage finished"
                    report = await self.release(reason)
                    break
                if not seen and history is None and time.monotonic() - started > 120:
                    # Validation may reject a prompt after the on-prompt hook. It never ran.
                    report = {"status": "not_queued", "reason": "Prompt did not enter the queue."}
                    break
                await asyncio.sleep(self.interval)
        except Exception as error:
            report = {**self.status(), "status": "failed", "error": str(error)}
        finally:
            try:
                if report is not None:
                    report.update(prompt_id=prompt_id, stage_before=before,
                                  peak_observed=self.peaks(peak, report.get("peak_observed", peak)))
                    self.record(owner, report)
            finally:
                self.cancelled.discard(prompt_id)
                self.tasks.pop(prompt_id, None)

    async def barrier(self):
        tasks = list(self.tasks.values())
        if tasks:
            await asyncio.gather(*tasks)
        if self.state.get("status") == "failed":
            raise ValueError(self.state["error"])
