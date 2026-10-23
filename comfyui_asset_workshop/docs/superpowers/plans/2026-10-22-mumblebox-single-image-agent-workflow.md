# Mumblebox Single-Image Agent Workflow Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` for native inline implementation. Brian's no-subagent, existing-instance, and repository instructions govern. No implementation is authorized by creation of this plan. Do not create a branch/worktree or commit/push merely because a generic skill suggests it.

**Goal:** Build the complete Comfy-only path from text/uploaded references to one approved mesh-input image, one Pixal3D mesh, GPU finishing, four design-reference images, and a usable human/agent package.

**Architecture:** Retain the existing Asset Workshop package, editor, native image/mesh recipes, AssetStore, and resource coordinator. Add server-owned job orchestration shared by the current GUI and a thin local MCP adapter, plus an immutable export-package writer. Replace new-project multiview defaults with explicit single-image approvals without silently migrating or losing legacy records.

**Tech Stack:** Existing ComfyUI v0.42.1 Python environment, native Comfy nodes, plain JavaScript/CSS frontend, JSON project storage, Python standard-library packaging, official Python MCP SDK for the local adapter. No new frontend framework or inference server.

**Spec:** [Complete design](../specs/2026-10-22-mumblebox-single-image-agent-workflow-design.md).

## Accepted validation scope correction — 2026-10-23

Latest clarification: complete all implementation, wiring, model-route and GUI functional checks, memory handling and actual package export before handing the tool over. Do not use immediate hands-on access as a reason to defer unfinished product work. Stop additional mesh-quality testing and artistic comparisons; reasonable meshes are sufficient. The existing fish export proves reconstruction/finishing, and the cancelled character run stays cancelled. Repair confirmed defects and finish the functional requirements; do not call incomplete wiring complete.

Brian clarified during live testing that the target is working workflows producing reasonable starting meshes, not improving the models or achieving accurate pictures from every family. This newer decision overrides the exhaustive Task 10 image-comparison matrix and quality requirements below. The 48 planned image calls and paired artistic comparisons are no longer completion requirements; retain their existing results as evidence without repeating them. The existing 50-call ceiling remains a maximum, not a target.

Finish representative real generation smoke checks for the supported image routes, the remaining two of three diverse single-image mesh exports, and actual downloadable package validation. Keep the already reasonable character design; do not reroll it for beauty or camera precision. Repair demonstrated product defects in controls, settings, resource handling, finishing or export. Disclose ordinary AI anatomy/detail/viewpoint limitations rather than chasing them with repeated generations. Additional reference pictures are advisory design/style information with explicit actual-versus-requested-view notes; they do not prove hidden geometry or enter reconstruction. No family or LoRA lane may be falsely labeled runtime-validated. Report any exact unproven compatibility limitation alongside the working tool instead of starting another research campaign.

Stop after presenting the actual reasonable exported results, package/download proof and concise passed/limited/unproven status. Preserve the current product scope, existing Desktop, source data and one-image reconstruction contract. No new feature, model family, adapter-training, redesign or alternative reconstruction experiment is authorized by this correction.

## Global Constraints

- Work only in `E:\Comfyui-installs\ComfyUI (1)\ComfyUI` and this installation's configured E-drive model/data/output locations. Never create development state in OneDrive or another app's directories.
- Package root `P = custom_nodes/comfyui_asset_workshop`; all relative filenames below are within P unless explicitly prefixed `Comfy root`.
- Preserve the existing Mumblebox workflow, data, detached root commit, dirty native files, and unrelated changes. No automatic cleanup/reset/update/commit/push.
- Work visibly in Brian's existing Comfy Desktop; verify a real live change before later asset work. No second instance or hidden fallback. This document is planning only.
- Build the full path before heavy inference validation. Targeted cheap tests are part of each implementation task, not a replacement for building the full workflow.
- Primary validated target: 16 GB GPU / 64 GB RAM. Include the selectable **Low memory — 8 GB VRAM (Experimental)** preset now; physical 8 GB and system-RAM requirements await testers. Reuse one lifecycle owner, unload between heavy prompts, and use PEC GPU finishing for both presets.
- Exactly one approved `mesh_input` revision enters Pixal3D. Four extra images are design references only. No hidden calibrated multiview, SDXL/MV-Adapter, rough-mesh guidance, or mesh assembly branch.
- Retain five families and nine existing profile IDs. LoRAs are core for every family, with explicit variant compatibility and actual local proof.
- Standard fresh default proposal: `klein4`, image resolution 1024, shape 1536, master-face target 700,000, texture 4096, remesh off, PEC. Experimental 8 GB preset: `klein4`, image 768, shape 1024, master-face target 100,000, texture 1024, additional headroom estimate 2 GiB, VAE tiling on, stage unloading required; native precision. Legacy jobs retain saved settings.
- Native sampling defaults remain structure 12/7.5, shape 20/7.5, refine 12/7.5, material 12/1. MoGe horizontal FOV in degrees; explicit manual starting value 49.13 degrees.
- Review states, image authority, partial packages, licensing, resource use, and quality limitations must be stated honestly. No geometry guarantee from a reference image.
- Stop after the acceptance campaign and presentation, or after a demonstrated feasibility limit; do not redefine the problem or begin Pinokio.

## Review Focus

1. An image changes while an agent starts a job: reject a stale approval before queuing; Task 1/3 tests cover this.
2. An old ten-angle History entry is reused: create a clean new draft without silently sending its angles to reconstruction; Task 1/7 tests cover this.
3. A cancel or unload arrives while another workflow is running: affect only owned work, and do not release global models beneath a foreign job; Task 3/4 tests cover this.
4. A LoRA has the right family label but wrong variant or unusable tensor mapping: fail clearly, preserve source weights, and record actual match evidence; Task 2 tests cover this.
5. A package's “back” image is actually another front, or its custom notes contain command-like text: preserve review/authority distinctions and treat notes as data, with no automatic execution; Task 5/8 tests cover this.

## Execution and interface conventions

Commands run from the Comfy root, using its verified `.venv\Scripts\python.exe`. Example targeted command (substitute the exact test filename listed by each task):

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s 'custom_nodes\comfyui_asset_workshop\tests' -p 'test_agent_projects.py' -v
```

Each task follows test → demonstrate relevant failure → implement → pass → proportionate review. Do not rerun unrelated expensive tests after every edit. Existing tests remain applicable to legacy behavior; add tests for the new mode instead of weakening them to hide regressions.

Record acceptance evidence once in `docs/validation/single-image-agent-workflow/RESULTS.md`, with actual artifact IDs, commands, and proof levels. Add machine-readable run records in that same directory only when needed to reproduce the campaign. Source review, automated tests, mechanical UI proof, agent-tool proof, and visual quality judgments are different evidence types.

### Data contracts to implement

All following signatures are proposed interfaces, not claims that they already exist. `Project`, `Job`, `ImageRevision`, `Approval`, `Artifact`, and `Package` are validated JSON-shaped records owned by `store.py`; define shared TypedDicts there. `ProjectConflict`, `ApprovalRequired`, `CapabilityError`, and `JobConflict` are explicit error classes there. Do not create a second persistence owner.

- `Project`: schema_version=2, id, revision (integer), sources, image role/revision records, settings, memory_preset_id (`standard_16gb|experimental_8gb|custom`), preset_overrides, design_notes, target, jobs, artifacts, timestamps. Retain existing legacy payloads read-only.
- `Approval`: image_revision_id, sha256, decision (`unreviewed|approved|approved_with_notes|rejected`), reviewer (`user|agent`), notes, timestamp; camera_verification=`not_measured` unless actual evidence exists.
- `Job`: id, project_id, request_key, snapshot, kind, state, phase, prompt_ids, artifacts, attempts, error, release_receipts. State=`queued|running|awaiting_review|completed|failed|cancelled|interrupted`; completed means that job's declared output exists, not that the whole product is done.
- `Artifact`: id, kind, relative stored path, SHA-256, source_revision_ids, job_id, settings/provenance, stale flag. Readers resolve IDs through AssetStore; no arbitrary file-serving paths.
- `target`: intended_use, requested_dimensions_m, scale_axis=`height`, user_instructions; measured dimensions come from export rather than overwriting this request.
- Job kinds=`create_image|three_quarter|edit_image|reference_view|build_mesh_package|finish_mesh`. `build_mesh_package` generates four references, reconstructs once, finishes, then enters `awaiting_review`. Packaging is an explicit action after review.

## Task 1 — Project roles, approval, and clean History reuse

**Files:** Modify `store.py`; create `tests/test_agent_projects.py`; retain `tests/test_reference_pair.py` for legacy mode.

**Interfaces:**

- `AssetStore.create_project() -> Project`
- `AssetStore.update_project(project_id: str, expected_revision: int, changes: dict) -> Project`
- `AssetStore.approve_image(project_id: str, role: str, image_revision_id: str, sha256: str, decision: str, reviewer: str, notes: str, expected_revision: int) -> Project`
- `AssetStore.mesh_input(project_id: str) -> ImageRevision` returns only the currently approved exact revision or raises `ApprovalRequired`.
- `AssetStore.reuse_parameters(project_id: str, include_images: bool = False) -> Project` creates a fresh schema-2 project; no job queued.
- `AssetStore.job_snapshot(project_id: str, expected_revision: int) -> dict` freezes actual image approvals, inputs, settings, LoRAs, and target metadata. Jobs retain that snapshot even when next-attempt settings change.

- [ ] Add `test_fresh_project_has_no_images_jobs_or_approval`: schema 2, default `klein4`, empty current results, single-image mesh mode, no legacy views.
- [ ] Add `test_stale_revision_or_hash_cannot_approve_or_start`: optimistic revision conflict and mismatched content hash both reject before a native prompt exists.
- [ ] Add `test_settings_only_change_does_not_revoke_pixel_approval` and `test_primary_edit_stales_mesh_and_package_but_reference_edit_only_stales_package` with explicit current/history assertions.
- [ ] Add `test_reuse_legacy_parameters_creates_clean_draft`: old JSON remains byte-identical; new ID/revision; no imported angle approval, no queued work; explicit image reuse keeps provenance but requires a new approval.
- [ ] Run the targeted tests to demonstrate the missing contracts; implement them using existing atomic writes, path containment, and revision storage.
- [ ] Pass targeted and existing store/history tests; inspect one legacy fixture plus one new project round-trip. Do not mutate Brian's actual History as a fixture.

## Task 2 — Model-aware image tasks and complete LoRA contracts

**Files:** Modify `profiles.py`, `prompt_contracts.py`, `recipes.py`, `nodes.py`, `lora_compatibility.py`; create `tests/test_image_task_contracts.py`; extend `tests/test_prompt_contracts.py`, `tests/test_lora_compatibility.py`.

**Interfaces:**

- `profiles.capabilities(profile_id: str) -> dict`: supported tasks, required inputs, actual reference cap, defaults/ranges/help, license URL/badge, variant, LoRA architecture.
- `prompt_contracts.image_task(profile_id: str, task: str, user_description: str, design_notes: str, requested_view: str | None) -> dict`: distinct system/user instruction fields and preservation constraints using the family's actual guidance.
- `recipes.image_task_recipe(project: dict, snapshot: dict, task: str, role: str, attempt_id: str) -> dict`: native graph plus complete parameter/provenance metadata. Legacy recipe entry points stay available for legacy records.
- Existing `AW_LoadModelLoRA` and `load_checked` remain native loading owners; do not add a second patch loader.

- [ ] Add `test_all_nine_profiles_have_task_defaults_license_and_lora_metadata`, `test_edit2511_requires_source`, and `test_references_never_silently_truncate`.
- [ ] Add `test_three_quarter_does_not_inherit_front_only_instruction` and `test_reference_task_uses_primary_and_explicit_notes_not_previous_generated_views`.
- [ ] Add `test_flux3_uses_current_full_scene_contract_and_variant_settings`; preserve documented reference tokens per family. Enhancement cannot replace the user's prompt until accepted.
- [ ] Add `test_disabled_and_zero_strength_loras_are_noops`, `test_family_variant_mismatch_fails`, `test_zero_or_partial_invalid_patch_fails`, and `test_lora_provenance_records_hash_strength_trigger_and_matches`. Assert the original model/checkpoint is not mutated.
- [ ] Demonstrate relevant failing tests, then implement the task contracts. Remove new-mode hard-coded front/pair gates; retain legacy reading/execution boundaries. Derive browser defaults from server capabilities.
- [ ] Pass targeted tests and inspect serialized graphs for all nine profiles. Count selected reference bindings and verify requested/actual variant, sampler, guidance, steps, precision, and enabled LoRA chain. Static graphs are not visual LoRA proof; Task 10 supplies that proof.

## Task 3 — One shared, visible job coordinator

**Files:** Create `jobs.py`, `tests/test_agent_jobs.py`; modify `routes.py`, `store.py`, `web/workshop.js`.

**Interfaces:**

- `JobCoordinator.start(project_id: str, expected_revision: int, kind: str, request_key: str, payload: dict) -> Job`
- `JobCoordinator.get(project_id: str, job_id: str) -> Job`
- `JobCoordinator.cancel(project_id: str, job_id: str) -> Job`
- `JobCoordinator.ack_visible(job_id: str, stage_id: str, graph_hash: str, client_id: str) -> None`
- `JobCoordinator.reconcile() -> None` compares recorded prompt IDs to actual native queue/history after startup; uncertain work becomes interrupted, never silently requeued.
- Native queue validation/submission remains through the current Comfy instance's supported queue API; `recipes` produces graphs, `AssetStore` stores state, and `resource_lifecycle` owns cleanup.

New API prefix `/asset-workshop/v2`:

| Operation | Request | Response |
| --- | --- | --- |
| `POST /projects` | empty body | Project |
| `GET /projects/{id}` | id | Project with bounded current job summary |
| `PATCH /projects/{id}` | expected_revision, allowlisted changes | Project or 409 |
| `POST /projects/{id}/images` | multipart image + expected_revision + role | Project and ImageRevision |
| `POST /projects/{id}/reviews` | exact approval fields | Project or 409 |
| `POST /projects/{id}/jobs` | kind, request_key, expected_revision, payload | Job or explicit conflict/capability error |
| `GET /projects/{id}/jobs/{job_id}` | ids | Job |
| `POST /projects/{id}/jobs/{job_id}/cancel` | ids | Job |
| `POST /jobs/{job_id}/visible` | stage_id, graph_hash, client_id | acknowledgment |
| `POST /projects/{id}/packages` | expected_revision, artifact selection | Package or incomplete-review error |
| `GET /projects/{id}/artifacts/{artifact_id}` | recorded artifact ID | authenticated metadata/download |
| `POST /release` | owned job context or explicit idle manual release | lifecycle receipt or busy status |

- [ ] Add `test_same_request_key_returns_same_job_and_never_queues_twice` and `test_changed_snapshot_with_same_key_conflicts`.
- [ ] Add `test_ui_and_agent_see_same_project_job_and_error`; no browser-only job authority remains.
- [ ] Add `test_no_connected_visible_client_prevents_submission`, `test_wrong_graph_ack_is_rejected`, and `test_reconnect_does_not_requeue`.
- [ ] Add `test_cancel_deletes_or_interrupts_only_owned_prompt_ids`, `test_foreign_job_prevents_global_unload`, and `test_restart_reconciliation_never_blindly_resumes`.
- [ ] Demonstrate failures, implement shared coordinator and bounded event/status payloads. A 30-second missing visible acknowledgment leaves the stage unqueued with a retryable explanation. Load the graph in the existing Desktop client; never substitute a browser or new app instance.
- [ ] Pass targeted tests using a deterministic fake native queue plus route contract tests. Mechanically prove graph visibility later in Task 9/10; acknowledgments alone do not earn visual proof.

## Task 4 — Strict single-image Pixal3D and stage cleanup

**Files:** Modify `recipes.py`, `foreground.py`, `nodes.py`, `resource_lifecycle.py`, `memory_policy.py`, `jobs.py`; create `tests/test_single_image_mesh.py`, `tests/test_memory_presets.py`; extend `tests/test_resource_lifecycle.py`, `tests/test_pixal_conditioning.py`, `tests/test_foreground.py`.

**Interfaces:**

- `recipes.single_image_mesh_recipe(snapshot: dict, prepared: dict, attempt_id: str) -> dict`
- `recipes.finish_saved_master_recipe(snapshot: dict, master_artifact: dict, attempt_id: str) -> dict`
- Existing preparation and `AW_SaveMaster`/`AW_LoadMaster` nodes persist source/preparation/FOV linkage; no new reconstruction engine.
- Existing resource lifecycle `track`, `release`, and cancellation/barrier operations are reused. Extend receipts to job records without a parallel cleanup path.
- `memory_policy.preset_settings(preset_id: str, hardware: dict) -> dict` returns values, explanations, changed-model/LoRA warnings and validation status from the spec's preset table. `memory_policy.apply_preset(asset: dict, preset_id: str, hardware: dict) -> dict` applies only after explicit selection; preserve originals, approved pixel revisions and frozen running snapshots. Read capabilities from `profiles.py`; do not duplicate family rules.

- [ ] Add `test_mesh_conditions_exactly_one_approved_hash`: assert one Pixal image binding, `pixal_single` weights, and zero bindings from reference roles. No fallback to an arbitrary current design or angle.
- [ ] Add `test_foreground_preserves_aspect_and_records_padding_transform`; transparent backgrounds and thin structures use existing mask handling without destructive stretching.
- [ ] Add `test_moge_fov_is_horizontal_degrees_of_prepared_image` and `test_missing_moge_requires_explicit_manual_choice`; manual 49.13 stays visibly estimated.
- [ ] Add `test_release_failure_prevents_next_heavy_stage`, `test_error_cancel_and_success_all_record_cleanup`, and `test_helper_exits_before_image_prompt`.
- [ ] Add `test_finish_uses_saved_master_and_pec_without_image_or_pixal_models` and `test_export_failure_does_not_rerun_reconstruction`.
- [ ] Add `test_experimental_8gb_preset_has_supported_explicit_values`: assert `klein4`, image 768, shape 1024 (not invalid 512), texture 1024, faces 100000, estimated headroom 2, tiling/unloading on, remesh off, PEC. Assert cache is CPU at system RAM >=28 GiB and off below that; RAM reserve is `min(8, max(2, round(total_system_ram_gib / 8)))`, with 1.5 GiB free VRAM floor. Sampling steps remain unchanged.
- [ ] Add `test_apply_preset_preserves_originals_approval_and_running_snapshot`, `test_overrides_and_reset_are_shared_between_ui_and_agent`, `test_low_memory_keeps_lora_support_and_rejects_wrong_family_patches`, and `test_16gb_host_smoke_is_not_marked_8gb_hardware_validated`. Assert no global launcher flags, forced restart, CPU-finishing fallback or silent model switch outside explicit preset Apply.
- [ ] Demonstrate failures, wire existing single-image nodes and saved-master finishing. Keep standard quality settings and add the separate experimental preset exactly as specified; remesh off for fresh projects, raw master before finishing. Use optional Q4 helper only if available or explicitly downloaded; skipping it must leave manual prompting usable. Preflight actual node schemas and selected local model files; do not inspect/download unrelated model inventories.
- [ ] Pass targeted/legacy tests; statically validate complete prepared-image → MoGe/FOV → Pixal structure/shape/refine/material → saved master → PEC finish → checked export graphs against the installed Comfy schemas. No inference yet.

## Task 5 — Immutable agent package and honest instructions

**Files:** Create `package_export.py`, `tests/test_agent_package.py`; modify `routes.py`, `store.py`.

**Interfaces:**

- `package_export.create_package(library: AssetStore, project_id: str, expected_revision: int, artifact_ids: list[str]) -> Package`
- `package_export.agent_brief(manifest: dict) -> str`
- `package_export.validate_package(path: str) -> dict` returns file/hash/schema/geometry-reference consistency results; this function does not run imported commands or Blender.

- [ ] Add `test_package_contains_one_primary_mesh_primary_image_and_four_references` using schema `mumblebox.agent-package/1` and the exact ZIP layout from the spec. Include optional existing exports/maps with explicit names/units.
- [ ] Add `test_unreviewed_rejected_missing_or_stale_reference_blocks_full_package`; `approved_with_notes` is allowed and notes appear in the brief. The independent completed mesh stays downloadable.
- [ ] Add `test_requested_view_is_not_camera_verification` and `test_requested_dimensions_do_not_replace_measured_dimensions`.
- [ ] Add `test_user_and_agent_reviews_and_explicit_and_inferred_details_stay_distinct`.
- [ ] Add `test_zip_uses_recorded_contained_files_and_valid_checksums`, `test_no_tokens_absolute_private_paths_or_environment_dump`, and `test_notes_are_quoted_data_not_executable_hooks`. Unsafe ZIP member paths and changed source files fail validation.
- [ ] Demonstrate failures, implement using standard-library ZIP/JSON/hash utilities and existing checked export metadata. Separate schema validation from actual later Blender import proof.
- [ ] Pass targeted tests; inspect a fixture ZIP and generated brief. Verify explicit authority order and known-limits language. Package creation must be repeatable from existing artifacts with no generation or global model loads.

## Task 6 — Editor role coverage and reference review

**Files:** Modify `image_edits.py`, `web/image-editor.js`, `web/creator.js`, `jobs.py`; create `tests/test_editor_roles.py`; extend existing edit/foreground tests where appropriate.

**Interfaces:**

- Existing `openImageEditor({...})` and `image_edits.create(...)` remain the editor contracts. Map new roles to exact source revisions without a second editor.
- `JobCoordinator.start(..., kind="edit_image", payload={role, source_revision_id, selection_artifact_id, instruction, feather, replace_detail})` uses the same task/profile/LoRA snapshot as other image work.
- Review action uses Task 1's `approve_image` for all roles; only approved `mesh_input` grants reconstruction permission.

- [ ] Add `test_all_seven_image_role_types_can_edit_and_download` and `test_stale_edit_source_cannot_replace_current_pixels`. Include two separately identified source records; editing either creates its own revision, preserves its original and does not alter already generated primary pixels. The six design/mesh/reference roles also support review.
- [ ] Add `test_outside_mask_pixels_are_identical_after_accept` and `test_discard_keeps_original_and_approval_unchanged`.
- [ ] Demonstrate failures, connect new roles to the existing full-resolution editor, retaining brush/rectangle/polygon, animated contrasting selection, finish-polygon state, icons, brush-size/edge-softness sliders and resets.
- [ ] Provide per-reference Regenerate, Clear this image, Edit image, Download image, and review status. Explain disabled actions beside their prerequisites; do not merely gray out unexplained controls.
- [ ] Pass targeted tests; defer actual pointer/control proof to the shared mechanical campaign. No new wand/segmentation model, style trainer, or fresh editor feature in this task.

## Task 7 — Simplified GUI, History, settings, and downloads

**Files:** Modify `web/creator.js`, `web/creator.css`, `web/workshop.js`, `routes.py`, `store.py`; create `workflows/Mumblebox Single Image.json`; preserve `workflows/Asset Workshop.json` until the new mode passes.

**Interfaces:** Browser uses only Task 3's shared job API and profile capability responses for new projects. Existing native graph loader remains the visible-stage bridge. Store optimistic revision conflicts show “This project changed. Review the latest version before continuing.” No silently lost updates.

- [ ] Create the separate launcher with the existing controls node property `asset_workshop_mode="single_image_agent"`; route only this explicit mode to the new journey/API. Keep the old launcher and its existing mode working until the new path passes. This is a mode boundary within the current package, not a second app or resource manager.
- [ ] Build the three steps **Create image → Approve three-quarter view → Mesh & agent package**, preserving existing dark/cyan tokens and readable layout. Keep History and Settings as utility tabs. No new theme/logo/layout framework work.
- [ ] Use exact copy from the spec for auto-describe/enhance/approval and one-image explanation. Put Advanced model controls below primary actions; compact seed input with randomize/lock controls and model-specific help. No group-project “we/let's” product wording.
- [ ] Surface image model/variant, compatible LoRAs, purpose/limits help, licensing link, actual versus requested seed, and editable quality controls beside the relevant stage. Saving overrides affects the next attempt; resetting restores that selected model's defaults.
- [ ] Add the Standard / Low memory preset selector, experimental status, changed-settings preview and explicit Apply, individual overrides/Custom indication and Reset preset. Show the spec's quality/speed/system-RAM explanations. Detection recommends without overwriting saved choices. A manual larger-model choice remains possible with honest warnings and matching LoRA validation. Preserve full-resolution uploads. Distinguish 8 GB VRAM from system RAM and do not label host smokes as physical 8 GB validation.
- [ ] Keep progress and errors on the active work page; show CPU/RAM/VRAM and Unload models with plain explanation. The button must not pretend to free unrelated applications' RAM or cancel another workflow.
- [ ] Retain History preview/pagination/delete/undo, add/retain Clear history with confirmation, Clear all current images with confirmation, and individual clear controls. Confirmations describe the actual trash/recovery policy rather than falsely promising irreversible deletion.
- [ ] Fresh opening leaves old results in History. Reuse parameters creates a new draft; explicit image reuse still requires approval. Every preview, editor, reference, History image, and mesh image offers a real download.
- [ ] Retain existing local Hugging Face authentication and model-download controls. Keep credentials private; show actual bytes/known total and honest unknown-total progress. Verify selected download/output destinations are this Comfy installation's E-drive paths, without borrowing another app's model directories. This retains an existing capability rather than adding a marketplace integration.
- [ ] Run relevant store/route tests. Mechanically exercise the actual installed controls in Task 9/10; browser DOM checks alone do not prove these interactions. Do not rewrite existing History storage to achieve the UI simplification.

## Task 8 — Thin MCP adapter and companion skill

**Files:** Create `agent/mcp_server.py`, `agent/requirements.txt`, `agent/README.md`, `skills/mumblebox-assets/SKILL.md`, `tests/test_mcp_adapter.py`; reuse Task 3 routes. Pin the actual compatible official SDK version selected in implementation preflight; do not invent a version from this planning document.

**Interfaces:** All tools forward to the same local HTTP owner; no GPU imports or direct AssetStore writes in the adapter.

| Tool | Parameters | Result |
| --- | --- | --- |
| `get_project` | project_id optional | bounded project/capability/current-job data; missing ID describes fresh state without restoring History |
| `save_project` | project_id optional, expected_revision, changes | created/updated Project; allowed fields only |
| `import_image` | project_id, expected_revision, authorized local path, role | uploaded ImageRevision; adapter reads only explicitly authorized input roots/files |
| `start_job` | project_id, expected_revision, kind, request_key, payload | shared Job and visible status |
| `get_job` | project_id, job_id | shared bounded status/artifact IDs |
| `cancel_job` | project_id, job_id | owned cancellation status |
| `review_image` | project_id, expected_revision, role, revision_id, sha256, decision, notes | labeled agent review; never disguised as Brian's approval |
| `read_artifact` | project_id, artifact_id, mode=`metadata|preview|full` | metadata/resource link; full content only on explicit request, no automatic mesh/base64 dumps |
| `export_package` | project_id, expected_revision, artifact_ids | package metadata/resource link or review errors |
| `release_models` | optional owned job context | existing lifecycle receipt or busy conflict |

- [ ] Add `test_tools_use_same_routes_and_idempotency_as_gui`, `test_agent_cannot_skip_primary_approval`, `test_agent_review_is_labeled_agent`, and `test_tools_cannot_invoke_arbitrary_code_or_fetch_arbitrary_server_paths`.
- [ ] Add `test_default_responses_are_bounded_metadata_not_full_binary` and `test_mcp_error_preserves_retry_and_partial_artifacts`.
- [ ] Demonstrate failures, implement the stdio adapter using the official SDK and local-only HTTP calls. Preserve existing origin/auth protections. Never export credentials or bind a new inference endpoint to the network.
- [ ] Write the companion skill around the actual tool contracts: clarify intent/dimensions, prepare/edit/approve one image, start visible job, inspect result/references, choose keep/repair/rebuild, export package, hand off to available Blender tools. Explain single-image hidden-detail limits. Do not silently decompose an asset or start a parts library.
- [ ] Pass targeted tests and protocol initialization/tool/resource checks. Installation of a dependency or connection configuration belongs to the later authorized implementation; no credential is needed in this planning pass.

## Task 9 — Complete-path readiness and mechanical fault proof

**Files:** Modify only owners of discovered defects; record results in `docs/validation/single-image-agent-workflow/RESULTS.md`.

- [ ] Confirm the existing Desktop instance and visible connection. Preserve the current workflow and selected project before the first live implementation change. Record actual installed node schemas, selected model/LoRA files/hashes, writable E-drive outputs, SDK versions, hardware, and current free resources. Do not inspect unrelated app tabs or model stores.
- [ ] Run the package's scoped suite once after integration:

```powershell
& '.\.venv\Scripts\python.exe' -m unittest discover -s 'custom_nodes\comfyui_asset_workshop\tests' -v
```

- [ ] Validate native graphs for every planned stage/profile against the actual installed nodes. This is not inference proof. Resolve a missing required artifact before claiming readiness; do not silently change family/variant or lower the quality preset.
- [ ] Mechanically operate fresh start, text/upload/multiple refs, model-specific help, Advanced settings/reset, both memory presets/Apply/override/reset, LoRA enabled/disabled/wrong variant, all editor tools, individual/global clearing, History reuse/delete/undo/clear confirmations, every image download, resource controls, and actual active-page progress. Record observations; avoid adding extra generation calls outside Task 10's matrix.
- [ ] Use controlled job fixtures and owned prompts to prove stale approval, duplicate request, client reconnect, error, and cancellation behavior. Foreign queue work prevents destructive global cleanup. Do not interrupt Brian's unrelated live job as a test.
- [ ] Confirm UI and MCP share the same IDs, snapshot, visible phase, errors, and artifacts. No pending implementation placeholders or browser-only orchestration remain before proceeding to inference.

## Task 10 — Bounded real inference and exported results

### Fixed image campaign

Five canonical profiles: `klein4`, `klein_distilled`, `qwen21`, `qwen2511`, `flux3_distilled`. Four additional retained variants: `klein4_base`, `klein_base`, `klein_kv`, `flux3_base`. Use matched, licensed LoRA artifacts for the actual variant. A base-only LoRA cannot stand in for a distilled/KV test. If no credible compatible artifact can be obtained within approved scope, report that exact limit rather than granting LoRA credit.

| Campaign component | Count | Evidence required |
| --- | ---: | --- |
| Per canonical family: create or source-conditioned result with compatible LoRA on; masked edit; requested three-quarter result; four reference views | 7 × 5 = 35 | actual pixels, settings/seed/LoRA provenance; Qwen Edit uses an uploaded source |
| Paired zero-strength image against each canonical LoRA-on result, same other inputs and seed | 1 × 5 = 5 | real matched-versus-zero evidence, not just file load logs |
| Each of four additional variants: matched LoRA-on and zero pair | 2 × 4 = 8 | variant-specific patch and image evidence; no checkpoint mutation |
| Focused quality corrections after a recorded failure | at most 2 total | named cause/hypothesis, fixed inputs, no random prompt sweep |
| **Image ceiling** | **50** | 48 planned + 2 corrective |

This tests shared task behavior and LoRAs; it is not an artistic ranking of nine variants. Record each call in the campaign ledger before queuing. Fixing a product defect requires targeted regression proof; it does not authorize quietly restarting the entire image campaign or changing the goal. If genuinely necessary regression calls exceed this budget, report the defect and proposed additional bounded proof to Brian before spending them.

### Three end-to-end exports

Use the approved results for (A) a mechanical engine-like prop with visible distinct parts, (B) an organic fish, and (C) a clothed character with a requested rear detail. Choose across at least three canonical image families. Do not use a crate/beacon for all cases. Retain actual primary images and assess what is visible versus inferred.

Allocate the Klein 4B image calls and fish reconstruction to the experimental 8 GB preset on the available 16 GB host; use Standard for the other two exports. This exercises both presets without increasing the 50-image / three-reconstruction budget. Label the fish run **experimental-preset smoke on 16 GB hardware**, not an 8 GB pass. Record actual hardware, system RAM, Comfy mode, overrides, stage peaks/timing and artifacts in the existing results record. Prepare that same compact record for future testers; do not add a telemetry service or wait indefinitely for outside testers before completing implementation.

- [ ] Per asset, visually inspect and explicitly approve the mesh input, review foreground, record actual MoGe/manual FOV, then run **one** Pixal3D reconstruction and saved-master GPU finishing. Four reference tasks come from the campaign above, not extra calls. The character need not have its requested unseen rear detail in the mesh; report its absence as single-image inference, not a successful hidden-geometry control.
- [ ] Prove the native image count is one and hash-matched. Observe helper exit, image-model release before reconstruction, reconstruction release before finishing, and cleanup after completion. Record actual peak/free memory and timings rather than a hardware marketing claim.
- [ ] Allow at most one reconstruction retry per asset after a demonstrated software/configuration defect. No image reroll to conceal bad geometry. GPU finishing repairs/retries reuse saved masters and never silently take the CPU adaptive path.
- [ ] Reopen actual exported GLBs and textures in the existing Comfy viewer. With Brian's prior Blender authorization and a usable visible connection, import at least one actual GLB into the existing Blender instance, check scale/orientation/maps and compare against the primary. If Blender visibility cannot be established, report import proof as missing rather than manufacturing it from a parser check.
- [ ] Review and package four references per full asset package. Inspect the actual ZIP, hashes, brief, requested/measured dimensions, units, licenses/provenance, and safe paths. State any contradiction. Missing/rejected views mean incomplete package; mesh-only download can still work.
- [ ] Present three actual mesh exports and packages/partial-package reasons, three primary images, visible comparisons, memory/timing results, and keep/repair/rebuild judgments. Show where the single-image model invented or omitted details. Do not claim automatic game/print readiness.

### Runtime bounds and diagnosis

Per call: image generation maximum 20 minutes; reconstruction maximum 30 minutes; GPU finishing maximum 15 minutes; lifecycle release maximum 60 seconds. The helper uses its existing bounded startup/timeout behavior. No native progress/liveness change for five minutes triggers diagnosis using job events, process and GPU activity; absent coarse percentage alone is not a hang. A confirmed time-bound failure cancels only owned work, preserves partial artifacts and releases resources. Explain before raising a limit; do not invent new unbounded runs.

Before each heavy prompt, enforce the effective preset's free-memory floors and release contract: Standard's agreed 8 GiB RAM reserve, the experimental preset's hardware-derived RAM reserve, and 1.5 GiB VRAM for both. A reserve is a preflight guard, not proof of model fit. If a preset cannot fit this actual host, diagnose the exact stage and present the smallest explicit setting change. Do not silently substitute the low-memory preset for Standard, or call a current-host smoke verified 8 GB operation.

## Success, rejection, and stop

### Mark implementation complete only when

- [ ] The full new journey runs in Brian's actual existing Desktop with no hidden reconstruction branch; legacy Mumblebox/History remain intact and startup is clean.
- [ ] All five families have actual generation/edit/three-quarter/reference and compatible LoRA evidence; retained variants have the specified LoRA pairs or an explicitly accepted scope change. No unproven lane is labeled validated.
- [ ] Exactly one approved image enters each of three completed Pixal reconstructions; no reference or second mesh is substituted.
- [ ] Three actual nonempty, finite, usable starting meshes and textured GLBs reopen. A critical visible object part cannot simply be missing while the result is called a pass. State residual bumps, topology, thin-detail and hidden-side limitations. “Usable” means keep or repair is justified from the visible comparison; a result requiring a full rebuild is a failed quality case.
- [ ] Full packages contain the required reviewed artifacts and honest instructions; incomplete packages remain labeled incomplete. All required package paths and actual downloads work.
- [ ] Resource release, GPU finishing, owned cancellation/retry, defaults/help, History, editor tools, GUI/MCP shared state, privacy/path constraints, and target dimensions pass their required proof.
- [ ] Both memory presets are implemented, selectable/editable and honestly labeled; the experimental preset completes the allocated current-host smoke. Physical 8 GB testing and its system-RAM requirement remain visibly unverified until real tester evidence exists. Pending external validation does not block release of the clearly labeled experimental option.
- [ ] Show actual results and summarize passed/failed/unproven rows, not a percentage invented from time spent. Release owned models and stop for Brian's review.

### Reject a working-solution claim when

The one-image/approval contract is violated; a family or LoRA silently swaps; exports are empty/corrupt or require full rebuilding; missing geometry is claimed present because its reference exists; required family/tool routes remain unusable; a failed cleanup is ignored; a foreign job is interrupted; required mechanical or exported proof is absent; or a fundamental hardware/model limitation prevents the accepted complete path within the bounded campaign.

A product defect is repair-and-retest work. A demonstrated model/architecture/hardware limit after the bounded diagnosis is a review checkpoint: present actual failures and the closest working subset, without marking unfinished implementation achieved. Do not start a new method, discard core requirements, train an adapter, add TRELLIS comparisons, or extend tests silently. Brian decides any changed scope.

## Coverage and review record

Spec sections 1–3: Tasks 1/3/6/7. Section 4: Task 2 plus Task 10's family matrix. Section 5: Task 4 and the actual export checks. Section 6: Tasks 3/4/9/10. Section 7: Tasks 1/3/7. Section 8: Tasks 5/8. Section 9: task ownership map above. Sections 10–12: the bounded campaign, stopping conditions, and preflight uncertainty record.

Plan self-review before presentation: confirm shared names/signatures match across tasks; every listed tool has an owning API; new record types have one owner; no new implementation is described as existing; no step introduces a second persistence/memory/inference service; all five Review Focus cases have named tests; LoRA and smaller-hardware requirements remain correctly scoped; no model/quality/GUI work occurred during planning. Document the final check outcome with the presentation rather than adding another planning phase.

Self-review outcome, 2026-10-22: all spec sections map to tasks above; shared roles, review decisions, job kinds, tools, route ownership and resource ownership checked for consistency. Source-input editor coverage, retained authentication/download progress, and a separate launcher were added during review. Brian's subsequent requested 8 GB preset is a core implementation item in Tasks 1/4/7/9/10, with real-hardware validation explicitly separate. The installed upsample node requires target resolution >=1024, so the preset uses 1024. Local document/link/placeholder checks pass. These are document checks, not application tests or evidence that the proposed workflow runs. The existing root Git changes are unchanged; only these two planning documents were created/updated in the ignored custom-node directory. No application code/workflow edits, generation, model installation, app restart, commit, or push occurred.
