"""One durable job owner for visible human and agent requests."""
import asyncio
import copy
import hashlib
import inspect
import json
import secrets
import time
import uuid

from .store import LOCK, IMAGE_ROLES, ApprovalRequired, JobConflict, atomic_json, identifier
from . import image_edits

KINDS = ("create_image", "three_quarter", "edit_image", "reference_view", "prepare_foreground", "build_mesh_package", "finish_mesh", "build_geometry", "texture_mesh", "prepare_variant", "prepare_material_guide", "apply_materials")
REFERENCES = ("reference_front", "reference_back", "reference_left", "reference_right")
ACTIVE = ("queued", "running")


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class JobCoordinator:
    def __init__(self, library, native, lifecycle, build_stage, emit, *, visible_timeout=30):
        self.library, self.native, self.lifecycle = library, native, lifecycle
        self.build_stage, self.emit = build_stage, emit
        self.visible_timeout = visible_timeout
        self.tasks, self.pending, self.clients = {}, {}, {}

    def connect(self, client_id, visible):
        identifier(client_id)
        self.clients[client_id] = {"seen": time.monotonic(), "visible": bool(visible)}
        if visible:
            for pending in self.pending.values():
                if pending["client_id"] == client_id:
                    self.emit(pending["event"])

    def _visible_client(self):
        current = time.monotonic()
        return next((key for key, value in reversed(list(self.clients.items()))
                     if value["visible"] and current-value["seen"] <= 15), None)

    def _job(self, project_id, job_id):
        project = self.library.load(project_id)
        return next(j for j in project["jobs"] if j["id"] == identifier(job_id))

    def _change(self, project_id, job_id, *, stage_id=None, **changes):
        with LOCK:
            project = self.library.load(project_id)
            job = next(j for j in project["jobs"] if j["id"] == job_id)
            target = next(s for s in job["stages"] if s["id"] == stage_id) if stage_id else job
            target.update(copy.deepcopy(changes))
            job["updated"] = time.time()
            self.library.save(project)
            return copy.deepcopy(job)

    def get(self, project_id, job_id):
        job = copy.deepcopy(self._job(project_id, job_id))
        job.pop("snapshot", None)
        job.pop("payload", None)
        job.pop("request_fingerprint", None)
        job["stages"] = [{k: s[k] for k in ("id", "name", "role", "state", "prompt_id", "result", "error") if k in s}
                         for s in job["stages"]]
        return job

    @staticmethod
    def stages(kind, payload, job_id):
        if kind == "build_geometry":
            names = [("reference_view", role) for role in REFERENCES] + [("prepare", "mesh_input"),("geometry","mesh_input"),("refine","mesh_input"),("cleanup","mesh_input")]
        elif kind in ("texture_mesh","prepare_variant","prepare_material_guide","apply_materials"):
            names = [({"texture_mesh":"texture","prepare_variant":"variant","prepare_material_guide":"material_guide","apply_materials":"materials"}[kind],"mesh_input")]
        elif kind == "build_mesh_package":
            names = [("reference_view", role) for role in REFERENCES] + [("prepare", "mesh_input"),
                      ("mesh", "mesh_input"), ("finish", "mesh_input")]
        elif kind == "finish_mesh":
            names = [("finish", "mesh_input")]
        else:
            role = payload.get("role", "mesh_input" if kind == "three_quarter" else "design")
            if kind == "reference_view" and role not in REFERENCES:
                raise ValueError("Choose front, back, left or right for the reference image.")
            names = [(kind, role)]
        return [{"id": f"{job_id[:20]}-s{index+1}", "name": name, "role": role, "state": "queued"}
                for index, (name, role) in enumerate(names)]

    def start(self, project_id, expected_revision, kind, request_key, payload):
        identifier(request_key)
        if kind not in KINDS or not isinstance(payload, dict) or payload.keys() - {"role", "edit", "expanded_prompt", "master_id", "export_kind", "resume_job_id", "source_id", "variant", "session_id"}:
            raise ValueError("Choose a supported job and its explicit settings.")
        request_hash = fingerprint({"kind": kind, "revision": expected_revision, "payload": payload})
        with LOCK:
            project = self.library.load(project_id)
            previous = next((j for j in project["jobs"] if j.get("request_key") == request_key), None)
            if previous:
                if previous["request_fingerprint"] != request_hash:
                    raise JobConflict("This request key belongs to different inputs. Use a new key for a new attempt.")
                return self.get(project_id, previous["id"])
            snapshot = self.library.job_snapshot(project_id, expected_revision)
            if "pipeline" in snapshot:
                sessions=snapshot["pipeline"].get("material_sessions",{})
                sid=payload.get("session_id")
                snapshot["pipeline"]["material_sessions"]={sid:sessions[sid]} if sid in sessions else {}
            if kind == "edit_image":
                if payload.get("role") not in IMAGE_ROLES or not isinstance(payload.get("edit"), str):
                    raise ValueError("Choose a saved selection for this image; file paths cannot be supplied as edit inputs.")
                image_edits.load(self.library, project, payload["edit"], payload["role"])
            client_id = self._visible_client()
            if not client_id:
                raise JobConflict("Open the single-image controls in this Comfy Desktop before starting a job.")
            if self.tasks or self.native.active_ids():
                raise JobConflict("Another Comfy job is active. Wait for it before starting this job.")
            if kind in ("reference_view", "build_mesh_package", "build_geometry", "texture_mesh"):
                self.library.mesh_input(project_id)
            job_id = uuid.uuid4().hex
            stages = self.stages(kind, payload, job_id)
            artifacts = []
            if payload.get("resume_job_id"):
                original = self._job(project_id, payload["resume_job_id"])
                if original["kind"] != kind or original["state"] not in ("failed", "cancelled", "interrupted"):
                    raise JobConflict("Retry only an interrupted, cancelled or failed job of the same kind.")
                if kind in ("build_mesh_package", "build_geometry", "texture_mesh", "reference_view") and (
                        original["snapshot"]["images"]["mesh_input"]["approved"] != snapshot["images"]["mesh_input"]["approved"]):
                    raise ApprovalRequired("The primary image changed. Start a new job instead of reusing the old stages.")
                original_payload=copy.deepcopy(original["payload"])
                for key,value in payload.items():
                    if key!="resume_job_id" and value!=original_payload.get(key):
                        raise JobConflict("Retry preserves the original operation inputs. Start a new job to change them.")
                payload={**original_payload,"resume_job_id":original["id"]}
                snapshot = copy.deepcopy(original["snapshot"])
                stages = copy.deepcopy(original["stages"])
                for index, stage in enumerate(stages):
                    if stage["state"] != "completed":
                        stage.update(id=f"{job_id[:20]}-s{index+1}", state="queued")
                        stage.pop("prompt_id", None)
                        stage.pop("error", None)
                artifacts = list(original["artifacts"])
            job = {"id": job_id, "project_id": project_id, "kind": kind, "request_key": request_key,
                   "request_fingerprint": request_hash, "snapshot_revision": expected_revision,
                   "snapshot": snapshot, "payload": copy.deepcopy(payload), "client_id": client_id,
                   "state": "queued", "phase": "Preparing", "prompt_ids": [], "artifacts": artifacts,
                   "attempts": 1, "error": None, "release_receipts": [], "cancel_requested": False,
                   "stages": stages, "created": time.time(), "updated": time.time()}
            project["jobs"].append(job)
            self.library.save(project)
            self.tasks[job_id] = asyncio.create_task(self._run(project_id, job_id))
            return self.get(project_id, job_id)

    def ack_visible(self, job_id, stage_id, graph_hash, client_id):
        pending = self.pending.get(stage_id)
        if (not pending or pending["job_id"] != job_id or pending["graph_hash"] != graph_hash
                or pending["client_id"] != client_id or client_id != self._visible_client()):
            raise JobConflict("The visible workflow does not match this stage. Reconnect the controls and retry.")
        if not pending["future"].done():
            pending["future"].set_result(True)

    def cancel(self, project_id, job_id):
        job = self._job(project_id, job_id)
        if job["state"] not in ACTIVE:
            return self.get(project_id, job_id)
        self._change(project_id, job_id, cancel_requested=True, phase="Stopping this job")
        for prompt_id in job["prompt_ids"]:
            self.lifecycle.cancel(prompt_id)
            self.native.cancel(prompt_id)
        for stage in job["stages"]:
            pending = self.pending.get(stage["id"])
            if pending and not pending["future"].done():
                pending["future"].set_result(False)
        return self.get(project_id, job_id)

    def reconcile(self):
        active = self.native.active_ids()
        for entry in self.library.list_assets():
            if entry.get("schema_version") != 2:
                continue
            project = self.library.load(entry["id"])
            for job in project["jobs"]:
                if job["state"] not in ACTIVE:
                    continue
                self._change(project["id"], job["id"], state="interrupted", phase="Review interrupted job",
                    error={"message": "Comfy restarted. Recorded artifacts are preserved; no stage was automatically resubmitted.",
                           "native_prompts_still_active": sorted(set(job["prompt_ids"]) & active)})

    async def _run(self, project_id, job_id):
        try:
            for index in range(len(self._job(project_id, job_id)["stages"])):
                job = self._job(project_id, job_id)
                if job["cancel_requested"]:
                    raise asyncio.CancelledError()
                if job["state"] == "interrupted":
                    return
                stage = job["stages"][index]
                if stage["state"] == "completed":
                    continue
                if job["kind"] in ("build_mesh_package", "build_geometry", "texture_mesh"):
                    approved = self.library.mesh_input(project_id)
                    original = job["snapshot"]["images"]["mesh_input"]["approved"]
                    if approved["id"] != original:
                        raise ApprovalRequired("The approved mesh image changed. Start a new job with that image.")
                await self.lifecycle.barrier()
                if self.native.active_ids():
                    raise JobConflict("Another workflow started. Its job will not be interrupted.")
                snapshot = copy.deepcopy(job["snapshot"])
                snapshot["task_payload"] = copy.deepcopy(job["payload"])
                if stage["name"] == "edit_image":
                    snapshot["task_payload"]["edit"] = image_edits.load(self.library,
                        self.library.load(project_id), job["payload"]["edit"], stage["role"])
                requested = snapshot["settings"]["mesh_requested_seed" if stage["name"] in ("mesh","geometry") else "requested_seed"]
                snapshot["settings"]["seed"] = secrets.randbelow(2**32) if requested < 0 else int(requested)
                self._change(project_id, job_id, state="running", phase=f"Preparing {index+1}/{len(job['stages'])}: {stage['name']}")
                built = self.build_stage(self.library.load(project_id), snapshot, stage, job)
                if inspect.isawaitable(built):
                    built = await built
                graph = built["graph"]
                graph_hash = fingerprint(graph)
                graph_path = f"jobs/{job_id}/{stage['id']}.json"
                atomic_json(self.library.path(project_id, graph_path), {"graph": graph, "details": built.get("details", {})})
                self._change(project_id, job_id, state="running", phase=f"{index+1}/{len(job['stages'])}: {stage['name']}")
                self._change(project_id, job_id, stage_id=stage["id"], state="awaiting_visible", graph_file=graph_path)
                event = {"job_id": job_id, "project_id": project_id, "stage_id": stage["id"],
                         "client_id": job["client_id"], "graph_hash": graph_hash, "graph": graph}
                future = asyncio.get_running_loop().create_future()
                self.pending[stage["id"]] = {**event, "future": future, "event": event}
                self.emit(event)
                await asyncio.wait_for(future, self.visible_timeout)
                self.pending.pop(stage["id"], None)
                if self._job(project_id, job_id)["cancel_requested"]:
                    raise asyncio.CancelledError()
                prompt_id = str(uuid.uuid4())
                ids = self._job(project_id, job_id)["prompt_ids"] + [prompt_id]
                self._change(project_id, job_id, prompt_ids=ids)
                self._change(project_id, job_id, stage_id=stage["id"], prompt_id=prompt_id, state="running")
                actual_id = await self.native.submit(graph, prompt_id, job["client_id"])
                if actual_id != prompt_id:
                    raise JobConflict("Comfy returned a different prompt identity; inspect the queue before retrying.")
                self.lifecycle.track(prompt_id, (project_id, job_id))
                timeout = 3900 if stage["name"] in ("geometry","refine","texture","variant","material_guide","materials") else 1800 if stage["name"] == "mesh" else 900 if stage["name"] == "finish" else 1200
                cancelled = lambda: self._job(project_id, job_id)["cancel_requested"]
                if cancelled():
                    self.lifecycle.cancel(prompt_id)
                    self.native.cancel(prompt_id)
                history = await self.native.wait(prompt_id, timeout, cancelled)
                if cancelled():
                    raise asyncio.CancelledError()
                if history.get("status", {}).get("status_str") != "success":
                    raise ValueError("The native Comfy stage failed. Inspect its recorded error before retrying.")
                await self.lifecycle.barrier()
                observed = self._job(project_id, job_id)
                receipts = observed["release_receipts"] + [observed.get("resources", self.lifecycle.status())]
                self._change(project_id, job_id, release_receipts=receipts)
                self._change(project_id, job_id, stage_id=stage["id"], state="completed")
            await self.lifecycle.barrier()
            final = "awaiting_review" if self._job(project_id, job_id)["kind"] == "build_mesh_package" else "completed"
            self._change(project_id, job_id, state=final, phase="Review mesh and references" if final == "awaiting_review" else "Completed")
        except asyncio.CancelledError:
            job = self._job(project_id, job_id)
            for prompt_id in job["prompt_ids"]:
                self.lifecycle.cancel(prompt_id)
                self.native.cancel(prompt_id)
            self._change(project_id, job_id, state="cancelled", phase="Cancelled")
        except Exception as error:
            job = self._job(project_id, job_id)
            for prompt_id in job["prompt_ids"]:
                self.lifecycle.cancel(prompt_id)
                self.native.cancel(prompt_id)
            self._change(project_id, job_id, state="failed", phase="Stopped at failed stage",
                         error={"message": str(error) or type(error).__name__, "type": type(error).__name__})
        finally:
            for stage_id, pending in list(self.pending.items()):
                if pending["job_id"] == job_id:
                    self.pending.pop(stage_id, None)
            try:
                await self.lifecycle.barrier()
            except ValueError as error:
                self._change(project_id, job_id, cleanup_error=str(error))
            self.tasks.pop(job_id, None)
