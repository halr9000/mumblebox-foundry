# SDXL implementation plan

**Goal:** Implement and verify the accepted SDXL single-image design in the existing installation.

**Spec:** ../specs/2026-10-23-sdxl-single-image.md

**Method:** Execute inline under Brian's implementation authorization. No new worktree, subagent, commit, unrelated refactor, or further approval loop. Preserve current UI design and all other routes. No weight downloads before the first-use tests.

## Task 1 — Profiles, settings, prompting, dependencies

Owners: profiles.py, store.py, prompt_contracts.py, models.lock.json, recipes.py:required_models; tests/test_sdxl_workflow.py.

- [x] Write and run failing tests for SDXL profiles, shared-family LoRA compatibility, dependency selection, settings round-trip on existing jobs, and model-aware prompt guidance.
- [x] Add pinned SDXL Base, Juggernaut, SDXL IP-Adapter, matching vision encoder, optional sample LoRA metadata. Keep the sample LoRA disabled unless selected.
- [x] Add validated SDXL settings and model-specific capability/default/help/license information. Preserve old project behavior and settings.
- [x] Verify targeted tests; record source/metadata decisions here once.

## Task 2 — Complete native graph route and loader boundaries

Owners: recipes.py, nodes.py, lora_compatibility.py, __init__.py, single_image_routes.py; tests/test_sdxl_workflow.py and loader tests.

- [x] Write failing graph/loader tests for checkpoint ownership, positive/negative CLIP conditioning, four-channel latent, LoRA model+CLIP matching, aspect-preserving references, and img2img/inpaint settings.
- [x] Add a native checked checkpoint loader and checked dual-target SDXL LoRA loader. Use the host's checkpoint and patching operations; no custom inference math.
- [x] Build SDXL text, reference, img2img and masked-edit graphs. Use native ResizeAndPadImage and installed IPAdapter Advanced; reuse the existing output/editor composition owner.
- [x] Pass the exact task into dependency checks so reference/edit/package stages receive all needed files before queueing.
- [ ] Validate native graph structure and regression tests before inference.

## Task 3 — GUI and first-use controls

Owners: web/single-image.js, single_image_routes.py local LoRA listing; tests/sdxl-controls.mjs and tests/download-recovery.mjs.

- [x] Add failing UI behavior checks for shared-family LoRA selection, reset/default preservation, and task-specific first-use request payloads.
- [x] Add the two model choices, SDXL-specific controls/help, optional sample LoRA choice, and per-LoRA CLIP strength.
- [x] Reuse existing download/recovery dialogs, credential vault, editing tools, History and exports. Do not start generation automatically after download or weaken license/access explanations.
- [ ] Run scoped suite, JS checks and mechanical control checks. Activate in existing idle Desktop under Brian's restart authorization.

## Task 4 — Bounded real first-use validation

- [x] Check exact checkpoint paths, hash the existing SDXL Base file, record and move it into a recoverable E: quarantine outside model paths. Confirm both selected checkpoint files are missing.
- [ ] In visible Desktop select SDXL Base, enter a simple asset prompt, click Generate, review actual missing-model setup, click Download, verify installation, then click Generate once and retain its usable output.
- [ ] Repeat first-use download and one generation for Juggernaut. No artistic rerolls.
- [ ] Verify one genuine SDXL LoRA + multiple-reference route and one source/inpaint route. Compare outside-mask pixels; keep original source/outputs.
- [ ] Confirm the approved image still enters the existing one-image mesh/export route using graph/package checks and existing valid artifacts; run at most one mesh regression only if needed to prove a changed connection.
- [ ] Verify model unloading, empty queues, no leaked hooks/credentials, saved actual parameters, preserved existing projects and old routes. Show outputs; mark the goal complete only when the spec's conditions pass.

## Review focus

- CLIP-only/model-only SDXL LoRAs and zero strengths must behave honestly.
- First-use checks must include visual adapters for tasks with implicit design/primary references, not only uploaded source rows.
- Existing jobs lack newly introduced SDXL settings; adding the route must not make them uneditable.
- The source mode must not silently convert a requested reference composition into image-to-image copying.
- Outside-mask pixels and input aspect ratios must survive editing/reference preparation.

## Progress

- Goal adopted. Existing Desktop idle and connected, live Mumblebox controls visible.
- Git root/common dir confirmed on E:, detached HEAD; preexisting tracked modifications and comfyui-mcp preserved. No .codegraph index.
- Found only sd_xl_base_1.0.safetensors among the selected checkpoint names in this installation; no checkpoint has been moved or downloaded yet.
- Metadata checked directly from Hugging Face: SDXL Base revision 462165984030d82259a11f4367a4eed129e94a7b; Juggernaut revision cf419233522daa0b9ea36c3aff98fa2cab1fb0fb; IP-Adapter revision 018e402774aeeddd60609b4ecdb7e298259dc729; sample LoRA revision 8bf4a4d9ea283e00a51fafda8e0539f8248ea037. All public at inspection.
- Existing IPAdapter nodes and native ResizeAndPadImage are registered. No new extension or dependency is required at present.
- Complete regression suite: 186 Python tests passed; JS syntax, SDXL controls and download-recovery checks passed. Both text-only graphs passed the restarted backend's native validation. Reference/LoRA native validation awaits their first-use downloads.
- Mechanical Desktop review confirmed SDXL defaults (30 steps, CFG 7, 1024), negative prompt, sampler/schedule, reference/source controls and separate text LoRA strength controls are installed.
- Brian requested automatic controls on workflow load. Added one-time opening per loaded Mumblebox launcher; actual Desktop reload opened clean controls without clicking. Dedicated JS checks also preserve an existing job and deliberate closure. Later suggestions are queued until this SDXL job is finished.
- Existing Base checkpoint hash matched the pinned source. Recoverable backup and restoration instructions: .backups/sdxl-first-use-2026-10-23/RESTORE.json. Both selected checkpoint files absent before the real first-use test. No weights have yet been downloaded.
- Desktop relaunched with --updated and lost its backend/control ports during control checks. Reopened the same installation with local debugging under existing restart authorization; no GPU job or download was active.
