# Mumblebox: one approved image to a mesh and agent package

Date: 2026-10-22. Status: proposed design for Brian's review. Planning only; nothing described as new below has been implemented by this document.

## 1. The product in plain English

Describe an object, upload a picture, or supply several reference pictures. Develop and edit the image until it shows the object clearly from a three-quarter angle. Explicitly approve that image. Send **exactly that image** to Pixal3D to make one mesh. Finish the mesh on the GPU. Download it together with the approved image, four additional design-reference pictures, and instructions that help a coding agent finish the asset in Blender.

The extra pictures communicate design and style. They do not feed reconstruction, prove hidden geometry, or become separate meshes that are joined together. A generated rear picture can suggest what the back should look like; it does not establish that the exported mesh contains that detail.

The intended result is a useful modeling head start for game and print assets. It is not a promise of production topology, a rig, exact unseen geometry, collision, LODs, wall thickness, or a print-ready solid. The agent package must make that distinction explicit.

Implement the new journey behind a separate `workflows/Mumblebox Single Image.json` launcher using the existing controls node with an explicit `single_image_agent` mode. Keep `workflows/Asset Workshop.json` and its legacy route available through validation. This is one package and one resource owner, not another Comfy instance or duplicated inference service.

## 2. Accepted decisions and scope

These requirements come from Brian's latest instructions, which supersede earlier front/back, ten-angle, contact-sheet, calibrated multiview, rough-mesh guidance, SDXL/MV-Adapter, and two-pass experiments.

1. Work inside the existing Comfy Desktop. Preserve the Mumblebox workflow and data until the replacement path is mechanically proved. No Pinokio implementation.
2. Retain the existing GUI's visual direction and useful controls. Simplify the journey rather than introducing a new framework, theme system, or unrelated redesign.
3. Accept text, one uploaded image, and multiple reference images. The user chooses which references are used; enforce each model's actual capabilities and explain limits before queuing.
4. Retain five image families: Klein 4B, Klein 9B, Qwen Image 2.1, Qwen Image Edit 2511, and FLUX 3 Image Klein. Keep existing variants in Advanced settings. Do not silently substitute a different model or variant.
5. **LoRA support is required for every supported image-model family.** Selection, enable/disable, strength, trigger text, compatibility errors, and saved provenance are core features. A model appearing in a menu is not proof that its LoRA path works.
6. Generation, enhancement, reference handling, editing, and three-quarter instructions are model-aware. Qwen Edit 2511 requires an image; it must not pretend to support text-only generation.
7. All existing masking tools apply to the initial image, the final mesh-input image, and additional references. Preserve full-resolution editing, visible selections, comparison, accept/discard, tool icons, sliders, and resets.
8. A suitable uploaded three-quarter picture can be adopted directly. Do not force an image-model pass that the user does not need.
9. The mesh input is an explicitly approved image revision. No implicit latest-image fallback and no additional views in Pixal3D conditioning.
10. The package contains four extra front/back/left/right design-reference images, custom instructions, requested dimensions and target use, actual settings and seeds, and provenance. View names describe requests; review and verification are separate fields.
11. Humans and coding agents share the same projects, jobs, approvals, history, settings, and resource owner. Provide a small MCP interface and companion skill for this Comfy workflow.
12. Validate first on the 16 GB GPU / 64 GB RAM machine. Include a selectable **Low memory — 8 GB VRAM** preset in the first implementation, labeled **Experimental — needs tester validation**. Unload between heavy stages and use GPU finishing for both presets. Actual 8 GB hardware support remains unverified until testers complete the whole flow on suitable hardware.
13. Startup is clean. Previous work is reopened explicitly through History using **Reuse parameters**. Every displayed image can be downloaded.
14. No automatic assembly of separately generated meshes. Automatic component decomposition, a reusable parts library, new marketplace integrations, Pinokio, and standalone packaging are later proposals.

## 3. The complete user journey

### Step 1 — Create image

Opening Mumblebox shows a fresh draft and explains: “Describe what you want to make, or upload an image. Add reference images if they help show the design.” History remains available without restoring yesterday's images into the new draft.

The model section shows the family, variant, licensing link, **Which model should I use?**, Advanced generation controls, and LoRAs. Help explains documented capabilities and measured local results separately; it does not invent rankings such as “best for people.” An incompatible task is explained beside the control, with the required next action.

Use **Auto describe my image** for visible uploaded content. Its tooltip states that it describes an image already uploaded. **Enhance description** uses the selected model's guidance and shows its proposed wording before acceptance. Neither operation silently invents features on unseen sides. Users can describe those features explicitly in their own design notes.

Generate image is right-aligned. A successful result advances to Step 2 for review; it does not start reconstruction. Uploaded images, generated alternatives, and revisions remain selectable and editable. Changing model settings changes the next attempt, not the contents of an existing image.

### Step 2 — Approve three-quarter view

Explain: “Choose one image for the mesh. A clear three-quarter view usually shows more of the object's depth. Keep the entire object visible.” The user can adopt a suitable existing image, request a three-quarter version using the chosen references and model, or edit a result.

A three-quarter request asks for visible front and side surfaces, complete framing, consistent proportions, an uncluttered background, and preservation of explicit design features. It does not turn a generated angle into a measured camera. A user can deliberately approve a different view after seeing that explanation.

**Approve image for mesh** freezes that revision and its hash. Editing or replacing its pixels revokes the current approval and makes dependent current mesh/package results stale. Old results remain in History. Adjusting a seed or LoRA for a future attempt does not revoke an already approved image.

After approval, **Generate mesh and reference views** starts the complete package job. Its explanation says that only this approved picture builds the mesh. There is no hidden multiview branch.

### Step 3 — Mesh & agent package

The job first produces four design references while the selected image family is available. Each is conditioned on the same approved image and the user's explicit design notes, plus deliberately selected extra sources within that model's capacity. Do not automatically accumulate generated references as increasingly authoritative inputs.

Then release image-stage resources, prepare foreground and camera information, reconstruct one Pixal3D mesh, release reconstruction resources, and finish/export on the GPU. Show the current phase and progress on this page, alongside persistent CPU/RAM/VRAM information and **Unload models**. A queue position or coarse progress report must not masquerade as a reliable completion percentage.

Reference review remains visible: inspect front, back, left, and right; regenerate or edit an individual reference; record discrepancies. A requested “back” that shows the front must never be marked camera-verified. Users may keep an imperfect reference with an explicit note. Rejected or missing references keep the full four-reference package incomplete; the completed mesh remains independently downloadable.

After review, **Download agent package** freezes the current artifacts into a ZIP. Download mesh and individual images remain available separately. A failed ZIP does not force generation or reconstruction to run again.

## 4. Exact image-model boundaries

| Family | Existing variants retained | Behavior in this iteration |
| --- | --- | --- |
| Klein 4B | `klein4`, `klein4_base` | Text and image-reference tasks; family-specific prompts and matching LoRAs. Proposed fresh-project default is distilled 4B, subject to this implementation's validation. |
| Klein 9B | `klein_base`, `klein_distilled`, `klein_kv` | Existing variants remain explicit; base, distilled, and KV compatibility must not be assumed interchangeable. |
| Qwen Image 2.1 | `qwen21` | Existing image/text path and reference binding retained; research-license conditions displayed. |
| Qwen Image Edit 2511 | `qwen2511` | Image-conditioned tasks only; require a source before generation. |
| FLUX 3 Image Klein | `flux3_base`, `flux3_distilled` | Use current FLUX 3 task guidance and full scene descriptions where prescribed; base and distilled controls differ. Do not reuse FLUX 1/2 guidance as if it covered FLUX 3. |

`profiles.py` is the sole source of capabilities, defaults, reference limits, parameter help, license links, and task support. Remove duplicate default maps in the browser. Preserve current native graph support rather than inventing one universal sampler or instruction.

Reference caps are input limits, not quality promises: the existing high Klein graph limit does not prove that a hundred references are useful. Show a modest suggested selection, allow supported larger inputs, and reject a request exceeding a genuine model/node limit without silently dropping images.

LoRAs are loaded from the selected Comfy installation's registered local directories. Record file hash, declared compatibility, enabled state, strength, trigger text, and matched patch results. Reject zero matches, unsupported mappings, and family/variant mismatches before expensive work where possible. Do not modify checkpoint files. Structural compatibility and visual behavior are separate evidence. An optional camera LoRA remains optional and honestly described; it is not a prerequisite for the one-image path.

The proposed fresh-project default is an operational starting point, not a proven artistic winner. Existing projects keep their recorded selection when explicitly reused. A licensing badge links to actual model terms; it never treats a user's ability to download weights as proof of unrestricted commercial operation.

## 5. Foreground, camera, reconstruction, finishing

### Foreground and camera

Retain `foreground.py`, local BiRefNet, and existing image-editor masks. Keep the original full-resolution image untouched. Save the actual foreground mask and preprocessing transform used for reconstruction. Preview it, allow a correction, and do not silently crop off antennas, handles, fins, or feet.

Use the native Pixal3D single-image preparation, including its documented padding of approximately 1.1. Preserve aspect ratio; record fit, padding, and resulting dimensions. No manual per-view zoom or resizing because there are no extra reconstruction views.

Use existing `LoadMoGeModel` → `MoGeInference` → `MoGeGeometryToFOV` for the prepared image. `Pixal3DConditioning.camera_angle_x` takes **horizontal degrees**; record the actual conversion and value. MoGe estimates perspective, not unseen geometry or guaranteed ground-truth calibration. If unavailable, stop that stage and offer explicit manual FOV rather than a hidden numerical fallback. Retain 49.13 degrees as the existing manual starting value, clearly labeled an estimate. Never interpret the Pinokio screenshot's 0.2 radians as degrees.

### One Pixal3D reconstruction

Use the existing `pixal_single` weights, `Pixal3DConditioning`, DINOv3/NAF image features, TRELLIS shape/texture VAEs, and native structure → shape → refine → material nodes. The conditioning image count is exactly one and its hash must match the approved mesh input.

Save the raw mesh and voxel/material state through `AW_SaveMaster` before finishing. Keep a link from the master to the exact source revision, foreground transform, FOV, requested/actual seed, settings, and model hashes. This allows finishing to be retried without running Pixal3D again.

Preserve the existing default structure/shape/refine/material sampling values (12/7.5, 20/7.5, 12/7.5, 12/1). Preserve the existing 1536 shape resolution, 700,000 master-face target, and 4096 master texture as the proposed initial quality preset; expose their costs and alternatives rather than silently weakening this machine's settings. These are current configured values, not newly proved optimal values. Native preflight and bounded validation determine whether this preset fits the target machine.

### GPU finishing and export

Retain native decimation, normal smoothing, **PEC** UV unwrapping, voxel texture baking, texture application, uniform scaling, and GLB export. Preserve raw geometry. Propose remeshing **off** in the new default because it can alter detail; keep the existing option in Advanced with its tradeoff explained. Existing legacy jobs retain their original remesh setting.

PEC is the required GPU route. Do not switch to the previously slow CPU adaptive route on failure. CPU orchestration, filesystem writes, and serialization are normal; this requirement concerns heavy finishing operations. If an operation cannot use the expected GPU backend, report which operation failed instead of saying “GPU export” succeeded.

Keep optional existing game-resolution export, PBR maps, normals/AO, and STL. Geometry-only downloads are useful, but do not claim that downloading geometry skips already performed texture inference. Uniform scaling can match a selected height. Requested width/height/depth and measured exported dimensions remain different fields; never distort all three axes silently.

## 6. Memory ownership and failure handling

Reuse `resource_lifecycle.py` as the only Comfy memory-release owner. Reuse `description_helper.py` for the optional local text helper. No second model manager or separate agent inference backend.

| Boundary | Required behavior |
| --- | --- |
| Local description helper → image model | Helper process exits; its owned resources are released before image generation. |
| Within an image graph | Native Comfy model/text-encoder offloading; no permanent duplicate model or encoder held by UI/MCP code. |
| Between image tasks | Initially retain the existing release-after-prompt policy. Reuse disk model files; do not optimize residency before correctness and measured headroom. Residency is not image consistency. |
| Last reference → Pixal3D | Wait for owned prompt completion and confirmed model release before loading reconstruction weights. |
| Foreground/FOV → reconstruction | Native graph offloading plus existing resource budget; release separate preparatory prompts before the next heavy prompt. |
| Reconstruction → finishing | Persist master, release reconstruction models, then queue GPU finishing from saved state. |
| Completion, error, cancel | Wait for owned work to stop, record actual artifacts/status, release safely, and report the next available action. |

The existing release contract waits up to 60 seconds for an idle queue, consumed unload flags, zero loaded Comfy models, low live tensor allocation (256 MiB), and stable memory samples. It is a release verification, not a guarantee that Windows process RAM returns to its starting value. Standard keeps the agreed 8 GiB free RAM / 1.5 GiB free VRAM preflight floors; the experimental preset's hardware-derived RAM reserve is specified below. Expose what each reserve means. Added model headroom is an estimate, not a hard VRAM cap.

Do not unload, cancel, or interrupt another workflow's job. If foreign work occupies the queue, wait or explain the conflict. Cancel is scoped to recorded prompt IDs and helper ownership. On restart, reconcile recorded native jobs; do not automatically rerun uncertain generation. If a requested stage fails, later dependent stages do not run. Completed stages remain reusable.

### Selectable memory presets

Brian's additional accepted requirement: ship the low-memory option as part of this iteration, then invite testers. Do not defer the selectable preset itself until physical 8 GB testing is available.

`memory_policy.py` owns the preset values and explanations; `profiles.py` still owns model capabilities and native parameter defaults. The GUI and MCP use the same resolved settings. Show **Standard — 16 GB VRAM** and **Low memory — 8 GB VRAM (Experimental)** near model/memory settings. Detection may recommend a preset; selecting Apply is explicit and never rewrites existing approved images or a running job's frozen snapshot. Show a summary of changed settings and mark individual overrides as Custom. Retain a Reset preset button.

| Setting | Standard starting values | Experimental 8 GB starting values | Explanation shown to the user |
| --- | --- | --- | --- |
| Fresh image model | Klein 4B distilled | Klein 4B distilled | A smaller model is the starting choice; other families remain selectable with honest memory warnings. |
| Generated image/reference resolution | 1024 | 768 | Smaller generated images need less memory but capture less fine detail. Original uploads remain untouched. |
| Shape target resolution | 1536 | 1024 | Less dense reconstruction reduces memory demand and may lose small/thin shapes. The installed upsample node's minimum is 1024; do not pass an invalid 512 value. |
| Master texture size | 4096 | 1024 | Smaller maps reduce bake/export memory and surface detail; this does not by itself reduce every earlier material-inference allocation. |
| Master decimation target | 700,000 faces | 100,000 faces | A lighter export can lose small features; this target affects finishing, not earlier reconstruction memory. Preserve the raw master. |
| Additional model headroom | Existing detected recommendation | 2 GiB starting estimate | Encourages earlier native offloading; it is not a hard 8 GB allocation cap. |
| Image VAE tiling / stage unloading | On / required | On / required | Smaller decode sections and unloading avoid retaining unnecessary GPU models. |
| Reference cache | Existing detected recommendation | CPU when system RAM is at least 28 GiB; otherwise off | Saving GPU memory can cost system RAM or recomputation time. |
| Optional description helper | Existing detected recommendation | Q4 when available; unloaded before image inference | Smaller helper weights can save RAM. Missing optional Q4 files require an explicit download or skipping the helper, not a hidden model install. |
| Remesh / UV method | Off / PEC | Off / PEC | Preserve shape by default and keep heavy finishing on the GPU. |

Use supported native model precision for the selected variant; do not invent a universal quantization toggle or silently replace a chosen model. Keep LoRAs available in low-memory mode. When Apply changes families, show which existing LoRA selections are incompatible and retain their configuration without applying them to the wrong model.

For the 8 GB preset use the existing RAM-reserve recommendation `min(8, max(2, round(total_system_ram_gib / 8)))` GiB, with an editable explanation, and the existing 1.5 GiB free-VRAM preflight floor. Record the detected mode, effective reserve, actual hardware, settings and overrides in each job/package. No application-wide launcher change, forced restart, fake 8 GB memory cap, or automatic CPU finishing fallback.

Explain: “This preset aims to reduce GPU memory use. It may be slower because models move between GPU memory and system RAM. 8 GB GPU support and system RAM requirements are still being tested.” Larger models remain available as deliberate choices, not automatically advertised as fitting this preset.

A successful preset smoke on Brian's 16 GB machine proves that the settings and workflow are connected. It does not prove operation on an 8 GB card, even if measured use happens to be below 8 GB. Tester reports must identify GPU/VRAM, system RAM, Comfy mode, chosen model/LoRAs, effective settings, peaks, timings, failed stage and actual exported result. Actual 8 GB support needs real whole-flow tests; an untested experimental preset may still ship clearly labeled.

A reboot remains Brian's physical action if genuinely necessary; no routine restart-as-cleanup strategy.

## 7. Shared project, job, and approval contracts

Extend `AssetStore` to schema 2. It remains the sole durable JSON owner; use atomic writes, bounded history reads, revision checks, and contained paths. No parallel database.

Image role types: `source`, `design`, `mesh_input`, `reference_front`, `reference_back`, `reference_left`, `reference_right`. There can be multiple source records, identified by their own revision IDs; they are reusable inputs rather than extra mesh slots. Source pictures use the same editor and download controls; an accepted edit creates a new source revision and preserves the original. Editing a source does not retroactively change an already generated primary image. Each revision records source hashes, prompt, profile/variant, actual seed/settings/LoRAs, original/generated/edited provenance, requested view, and review.

Review records distinguish `unreviewed`, `approved`, `approved_with_notes`, and `rejected`. Record reviewer, revision/hash, notes, and time. User/agent visual review is not measured camera verification; camera verification remains `not_measured` unless an actual measurement is supplied with evidence. Agent review is visibly labeled as agent review.

An approved `mesh_input` revision is the sole reconstruction authority. Source image changes invalidate its dependent current artifacts. A reference-only edit invalidates the package, not the already valid mesh. Prompt/model setting changes affect future attempts. Old files remain available in History.

Keep schema-1 projects readable, including their legacy views/exports. **Reuse parameters** creates a fresh schema-2 project; it does not queue legacy graphs or silently reinterpret ten old angle slots as a new approved primary. Reusing images is an explicit separate choice. Startup does not write to or mutate old projects.

Retain existing local Hugging Face authentication and model-download controls rather than building a new integration. Never export credentials. Show actual bytes downloaded against known total bytes when available, including per-file progress; if the total is unknown, say so instead of fabricating a percentage. Resolve all model destinations through this Comfy installation's E-drive configuration, without borrowing another application's models or output folder.

Add a narrow `jobs.py` coordinator that uses this store, the existing recipe builders, native Comfy queue, and existing lifecycle owner. Browser and MCP both call it. Freeze settings at job start. Track phase, native prompt IDs, artifact IDs, attempt number, error, and memory-release receipt. An idempotency key plus project revision prevents duplicate queue submissions and stale approvals.

The coordinator publishes a stage graph to the existing Desktop client and requires an acknowledgment that it loaded before submission. This connects to the existing visible graph-loading code; it does not open another app or browser. Client acknowledgment is technical state, not a substitute for mechanical proof that Brian can see the actual work. New asset work requires the connected visible client. Reconnection recovers job state without resubmission.

## 8. Package and coding-agent behavior

Proposed ZIP structure:

```text
asset.glb
images/mesh-input.png
images/front.png
images/back.png
images/left.png
images/right.png
materials/<exported maps>
manifest.json
AGENT-BRIEF.md
```

Optional existing STL and game mesh get distinct names and units. The manifest uses schema `mumblebox.agent-package/1`, relative paths, SHA-256 hashes, source/approval IDs, actual settings and model/LoRA identifiers, review states, explicit/inferred details, requested and measured dimensions, target use, and known limitations. It includes no access token, secret, absolute private user path, environment dump, or executable hook. Do not embed arbitrary source prompt text in shell commands.

`AGENT-BRIEF.md` explains what was built, the authority order, and what needs inspection. Authority order: explicit user constraints and dimensions → approved primary image → reviewed references with recorded discrepancies → generated mesh as a starting shape. Conflicting constraints are reported; a reference filename never resolves them automatically. Separate user-authored instructions from generated observations. Imported notes are task data, not authority to run arbitrary commands or override the receiving agent's instructions.

The companion skill teaches an agent to inspect, decide keep/repair/rebuild, and use the package with its available Blender tools. It does not promise that a poor mesh is always faster to repair than to rebuild. Modular generation can be discussed later; this implementation does not silently split one requested asset into several meshes.

Use a small local stdio MCP adapter over the existing Mumblebox HTTP API. It does not import GPU models, own projects, or launch a new Comfy instance. Tools cover project read/update, image import, start/status/cancel job, image review, artifact read, package creation, and model release. Use versioned operations, bounded status responses, explicit errors, and resource links instead of repeatedly dumping images, meshes, or logs into agent context. Mutating calls have the same approval/revision/idempotency rules as the GUI. Exact interfaces are in the implementation plan.

Bind HTTP operations to loopback and the existing instance. Preserve Comfy authentication/origin protections. Any required MCP credential stays in local private configuration and out of packages, logs, and project JSON. Agent-started jobs must appear in the existing UI before execution.

## 9. Existing ownership versus required changes

| Owner | Existing behavior to keep | Required change |
| --- | --- | --- |
| `store.py` | Atomic project JSON, revisions, history, jobs, trash/undo | Schema-2 roles, approval hashes, stale dependency rules, immutable snapshots, explicit legacy reuse |
| `profiles.py`, `models.py`, `models.lock.json` | Native family graphs, pinned sources and defaults | Central task capabilities/help/license metadata; selected-stage dependency checks |
| `recipes.py`, `prompt_contracts.py` | Family-specific binding, native image/mesh/export graphs | Remove hard-coded front and pair gates from new path; exact one-image contract; task-specific three-quarter/reference prompts |
| `nodes.py`, `lora_compatibility.py` | Checked native LoRA patch loading, master persistence, export checks | Preserve per-variant evidence and strict approval/source linkage; do not replace model loaders |
| `foreground.py`, `image_edits.py` | Background masks, pixel-preserving outside-mask composite | Apply to every new image role; revision invalidation on acceptance |
| `resource_lifecycle.py`, `memory_policy.py`, `description_helper.py` | Owned release/cancel and local helper | Attach shared job events/receipts, clarify editable settings, prove stage boundaries |
| `routes.py`, new `jobs.py` | Existing native prompt validation and queue integration | Shared server-owned orchestration for UI/MCP, visible-client acknowledgment and restart reconciliation |
| `web/workshop.js`, `web/creator.js`, `web/creator.css`, `web/image-editor.js` | Dark/cyan style, editor, visible graph loading, downloads | Three-step journey, new roles, honest progress/reviews, durable job display, single default source |
| Existing `workflows/Asset Workshop.json`, new `workflows/Mumblebox Single Image.json` | Existing saved workflow remains intact | Separate explicit mode/launcher for the new flow; no automatic replacement before proof |
| New `package_export.py` | Existing checked GLB/maps/STL reused | Immutable manifest/brief/ZIP from allowlisted recorded artifacts |
| New `agent/mcp_server.py`, companion skill | No app-specific server source located in this inspection | Thin local adapter and user/agent operating instructions; not a new inference service |

Current source inspection found the old frontend/store defaults still describe front/back, ten views, and `pixal_multiview`. The new workflow therefore requires a real ownership change, not just hiding old tabs. Existing mesh and editor code are substantial reusable pieces, but this new journey, package, and shared MCP execution are not already complete.

## 10. Validation budget and stopping condition

Build the complete path before the bounded heavy inference campaign. Cheap targeted contract tests accompany implementation; they do not substitute for the full workflow. No endless artistic adjustment or fresh research survey.

Budget: 48 planned image inferences across five families and retained variants, plus two explicitly recorded corrective attempts; three full single-image Pixal3D reconstructions; at most one necessary reconstruction retry per failing asset after a demonstrated defect. Finishing retries reuse the master. The implementation plan gives the exact matrix. Ordinary product bugs must be repaired and retested; exhausting the image-quality budget does not excuse broken controls.

Use three visibly different assets: a mechanical engine-like prop, a fish/organic creature, and a clothed character with an explicit rear design detail. Build the character's rear reference as design intent; inspect honestly whether the single-image mesh contains it. Do not promise a hidden backpack just because its picture exists. Every image family is tested for generation/editing/references/LoRA behavior, but the same Pixal engine need not reconstruct every family/variant combination.

Pass means: the actual installed GUI and MCP share correct jobs; every family has real compatible LoRA evidence; approved-input hashes and one-image conditioning are proved; editing, downloads, cleanup, History and cancellation work; both memory presets are selectable/editable and the experimental preset has a complete-path smoke on the available host; three exports reopen with finite geometry and actual texture files; requested/measured dimensions and limitations are reported; four-reference agent packages are inspectable and safe. Visual results are shown, with an explicit keep/repair/rebuild assessment. Reference consistency is reviewed, not assumed perfect. Physical 8 GB tester validation is a separately reported pending result, not a prerequisite for shipping an honestly labeled experimental preset.

Reject the claim of a working solution if reconstruction receives extra or unapproved images, the wrong model silently runs, exported files are corrupt/empty, cleanup fails and subsequent stages continue, a required family's LoRA route cannot be demonstrated, or package references are passed off as guaranteed geometry. A genuine model/hardware limit is documented as a limit, with actual results and the closest supported behavior. Do not move the goalposts or declare partial work complete.

Stop after the accepted behavior and proof pass and actual exports/packages are presented for Brian's review. Also stop for review if a demonstrated feasibility limit prevents that result after focused diagnosis and the bounded attempts. No automatic Pinokio work, new model family, two-pass experiment, or replacement research campaign follows.

## 11. Evidence and remaining uncertainties

Evidence level for this design: current source inspection and existing recorded experiment results. This planning pass ran no generation, application tests, UI proof, or new hardware measurements.

Local baseline: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI`, detached Comfy commit `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18` (v0.42.1). Existing root modifications in mesh postprocess/save/TRELLIS nodes and untracked `comfyui-mcp/` are preserved. The latter contains generation database files, not located app-specific MCP server source. Package code is under `custom_nodes/comfyui_asset_workshop`. No development output belongs in OneDrive or another app's directories.

Relevant existing records: `docs/research/2026-10-20-model-guidance/REPORT.md`, `docs/research/2026-10-21-applied-research-synthesis/REPORT.md`, and sibling `custom_nodes/mumblebox_sdxl_joint/COMPARISON.md`. Historical recommendations do not override this one-image decision. The failed calibrated multiview experiment is not proof that Pixal benefits from no extra image in every possible circumstance; it is sufficient reason not to revive that route here.

Primary source links checked for the narrow design questions:

- [Pixal3D code and release notes](https://github.com/TencentARC/Pixal3D): current release builds on TRELLIS.2 and adds explicit pixel alignment. This motivates its role; it is not a new head-to-head benchmark.
- [TRELLIS.2 code and examples](https://github.com/microsoft/TRELLIS.2): related image-to-PBR-mesh option, not a newly proved superior route for any object category. Keep existing support; no added comparison campaign in this iteration.
- [FLUX 3 Image Klein Comfy guidance](https://huggingface.co/black-forest-labs/flux-3-image-klein-comfy) and [license](https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md): current task instructions and conditional commercial terms.
- [Klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) and [Klein 9B license](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B/blob/main/LICENSE.md): distinguish model-operation permissions from output terms. Do not label all Klein variants Apache-licensed.
- [Qwen Image 2.1](https://huggingface.co/Qwen/Qwen-Image-2.1) and [Edit 2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511): different license/capability records.
- [MCP server protocol guide](https://modelcontextprotocol.io/docs/develop/build-server): a local tool interface does not require Pinokio.

Uncertainties to resolve in implementation preflight/validation, without changing the objective: installed selected files and hashes; actual LoRA artifacts for each architecture/variant; full 1536/4096 preset headroom; experimental 8 GB preset behavior and system-RAM demand; visible-client acknowledgment after reconnect; MCP transport/version compatibility; four-reference quality; per-object keep/repair/rebuild value. None is represented as runtime-proved here. Physical 8 GB results await testers and must be reported separately from current-host proof.

## 12. Review decisions

Approval of this proposal accepts the three-step flow, one approved Pixal input, four extra agent references, core LoRAs, shared visible UI/MCP jobs, a core selectable experimental 8 GB preset, and the bounded proof campaign. Brian explicitly requested inclusion of that preset after the first plan presentation. Proposed fresh defaults requiring review are Klein 4B distilled, current 1536/4096 standard quality settings, the low-memory table above, and remeshing off with PEC finishing. They are explicit starting settings, not claims of universal quality or proved 8 GB support.

No Brian-only information is required to finish the plan. Implementation remains stopped until Brian approves it. The next phase is to build the complete path described in the companion plan, then run its bounded validation, show the actual results, and stop for review.
