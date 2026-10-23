# Questions, evidence, and proposed decisions

Date: 2026-10-22. Research dispositions are complete; recommendations below await Brian's review. They do not authorize implementation. Source links and versions are in [SOURCE-REGISTER.md](SOURCE-REGISTER.md); fuller reasoning is in [REPORT.md](REPORT.md).

## Authority and accepted boundaries

- Current authorization: execute the approved research plan and report; no Comfy changes, generation, training, installs or spending.
- Preserve the existing Mumblebox workflow and completed experiment. Work and research artifacts remain on E:.
- Target 16 GB VRAM / 64 GB RAM, with actual release of models between stages and GPU-heavy finishing.
- Uploaded image remains a valid starting point. A particular image-generation family is not required to create that source.
- The failed draft-mesh-guided second-mesh runtime route stays retired. Researching projection mathematics does not revive it.
- Human editing and approval are legitimate parts of a useful workflow. Preserve raw outputs and count repair effort.
- SDXL is permitted for investigation. All five old image models need not survive. Klein/Qwen are not rejected by default, and custom adapters remain possible.
- Stop after a finite research package; then discuss the proposal. No automatic implementation goal follows this report.

## R00–R12 coverage

| Work package | Answer / evidence | Disposition and remaining boundary |
|---|---|---|
| R00 — Lessons and scope | Existing `mumblebox_camera_experiment/RESULTS.md` documents successful true-view controls, failed generated-view improvement, camera errors and damaging reduction. | Preserve repairs/masters. Retire that runtime feedback route. Old results are not new proof. |
| R01 — Exact adapter | Source and config confirm trained cross-view/reference attention, one RGB reference, camera-ray condition, six level orthographic targets. Standard I2MV is distinct from geometry-guided weights and beta counts. | Select standard released I2MV as the primary image hypothesis. Pose accuracy still needs measurement. |
| R02 — Workflows and recent activity | Five families audited in WORKFLOW-INVENTORY; actual baseline, LoRA and 3D-Pack graph paths inspected. Recent loader issue and community memory code identify current integration risks. | Reuse the author recipe, not a screenshot. No verified newer complete route found in bounded discovery. |
| R03 — Base and derivative | Official SDXL plus exact ordinary Juggernaut XL v9 selected. No verified end-to-end I2MV mesh demonstration for that derivative. | One baseline, one derivative. Generic Juggernaut generation presets do not override MV-Adapter's sampler recipe. |
| R04 — Camera/crop contract | MV-Adapter targets orthographic rays; Pixal inspected feature projection divides by depth. Existing camera repair handles pinhole transforms, not demonstrated ortho support. | Primary is conditional on an exact projection bridge/control test. Far-distance approximation is also mathematically legitimate, with a measurable error bound. No guessed FOV pass. |
| R05 — Reconstruction | Pixal is locally exercised, but its proposed new input contract is unproven. Paper reconstruction uses StableNormal/NeuS; Era3D provides an actual ortho implementation. T3lescope unreleased; Gaussian Wrapping targets posed capture and has restricted terms. | Primary conditional Pixal; one ortho-NeuS fallback. New leads remain watchlist/rejected-for-this-use, not extra integrations. |
| R06 — Input and identity | Author preprocessing, explicit BiRefNet selection, reference conditioning, fixed output framing and model-specific prompts are concrete. Mask errors and independent recropping can corrupt evidence. | Preserve source and affine transforms. Count edits. Do not treat VLM approval or angle captions as calibrated camera proof. |
| R07 — LoRA/style/anime | Author I2MV LoRA graph actually consumes an image. Exact example style file provenance is unresolved; text-only anime demos are different evidence. | One licensed style check only after geometry success, or use that optional budget for a correction check. No style catalog. |
| R08 — Hardware/platform | Installed versions differ substantially from author requirements. Custom Diffusers pipelines hold CUDA objects outside normal Comfy ownership. Published image inference memory is close to 16 GB. | Version-isolated experiment integration, real stage release, measured peak/cleanup. No downgrade of the working desktop. Windows and peak feasibility are runtime unknowns. |
| R09 — Finishing/value | Existing GPU PEC/voxel bake path and full-master evidence can be reused for Pixal. Earlier QEM caused damage. NeuS vertex colors cannot be passed as Pixal voxels. | Full-master quality first, bounded GPU exports, separate game/print checks. No automatic cleanup/quality label. Blender-first cost remains a bounded later comparison. |
| R10 — Rights and portability | Exact cards/licenses differ across backbone, adapter, VAE, remover, features, reconstruction and rendering libraries. DINOv3 is not MIT; nvdiffrast is not blanket unrestricted commercial code. | Maintain per-artifact notices/conditions and local paths. No commercial badge based only on the top-level repository. No license acceptance performed. |
| R11 — Training and data | MV trainer/config and paired Blender rendering resources exist. Full MV training is substantially larger than ordinary LoRA. Official Klein guidance supports a small local training candidate; Qwen and new FLUX 3 camera LoRAs establish practical precedents. | Existing weights first. If evidence demands training, begin with a paired camera-edit Klein 4B feasibility pilot; no need to assume a full architecture port. Depth optional. No fair speed comparison found. |
| R12 — Synthesis and stop | One primary, one fallback, shared count/time limits, explicit controls and quality gates are specified. Unknowns each have a narrow next probe. | Research complete when document/integrity review passes. Stop for Brian; do not execute the proposal. |

## Decisions proposed for approval

| ID | Proposed decision | Why | Reopen only if |
|---|---|---|---|
| D01 | Test coordinated-view generation as the novel hypothesis. | It changes how pictures share information; it is not another wording sweep. | Released recipe cannot run or fails declared quality gates. |
| D02 | Keep the image model used for the initial design independent of the specialist multiview stage. | Preserves image upload and Qwen/Klein design quality without forcing them to solve every stage. | Reference preservation is demonstrably inadequate. |
| D03 | Make camera compatibility the first technical gate. | A bad projection can make an otherwise good image test meaningless. | A verified existing bridge is found; then reuse it instead of writing another. |
| D04 | Prefer direct orthographic feature projection for the primary Pixal probe. | Avoids inventing pinhole metadata for orthographic targets. | Exact support cannot be applied coherently; a predeclared distant-camera approximation meets the same error/control gates. |
| D05 | Keep StableNormal/orthographic NeuS as the sole reconstruction fallback. | Closest released family to the paper's tested reconstruction assumptions. | Windows/GPU/license/export integration cannot pass within the bounded setup budget. |
| D06 | Test standard six-view weights first. | Matches training; prevents untrained elevations from contaminating the hypothesis. | Evidence supports a different released variant and Brian approves a revised count. |
| D07 | Permit a few edits, with raw and assisted scores separate. | User wants practical assets, not a no-human-input contest. | Correction effort becomes repetitive redesign or masks systematic failures. |
| D08 | Do not train before knowing which requirement is missing. | Avoids a large dataset/model project when released weights might suffice. | A repeatable failure survives correct integration and has a training-specific hypothesis. |
| D09 | Retain lightweight Klein/Qwen as a future research-backed option. | There is actual training support and released camera-LoRA precedent. | Controlled evidence rules out the required camera/identity behavior for the chosen backbone. |
| D10 | No automatic GUI or Pinokio work. | Workflow quality is the current decision. | Brian approves product integration after evidence review. |

## Direct answers to Brian's added questions

**Do Klein/Qwen need a big adapter?** Unknown; possibly not. A small paired-edit LoRA may exploit capabilities already present. Parameter count is not the success criterion. A model can re-angle convincingly while still changing dimensions or hidden features enough to hurt reconstruction.

**Is Klein training faster than SDXL?** A short Klein LoRA run is documented as feasible. No controlled comparison for this camera task was located. Compare the same resolution, data, trainable parameters, hardware, optimizer, validation and success threshold. Do not compare four-step image inference with training time or a tiny LoRA with full MV-Adapter training.

**Does an adapter require depth?** Not generally. The released I2MV baseline uses viewing-ray information, not a draft object's depth. A paired LoRA can learn camera edits from source/target RGB and camera labels. Render masks, cameras, depth and normals in a future owned dataset because they are useful evaluation/supervision assets; use only what the chosen architecture supports.

**Can editing fix errors?** Often, and it is allowed. Correct the image for an image defect; correct the guide for a guide defect; correct the projection/transform for a camera defect. Repairing one frame does not automatically repair its neighbors. Evaluate the assisted workflow honestly instead of calling it fully automatic.

**Can orthographic and perspective cameras be translated?** Yes: exact re-rendering with known geometry; depth-assisted pixel reprojection with visibility limits; a bounded distant-perspective approximation; or a reconstruction integration that directly accepts orthographic rays. A flat image alone does not supply an exact universal depth-aware conversion. The existence of mathematical bridges supports a compatibility probe, not a guaranteed mesh-quality claim.

**What happens after research?** Review the recommendation and adjust the finite validation proposal. Approve one experiment, adopt its bounded implementation goal, run it visibly, and stop for results. Max is useful for the decision review; Extra High is a reasonable execution choice. Model selection does not replace an explicit hypothesis, evidence or stop rule.

## Unresolved questions are bounded, not hidden

The consequential unresolved items are current-stack runtime compatibility, orthographic Pixal behavior, actual generated-view geometry, derivative/style preservation, memory peaks, fallback GPU feasibility/export, exact artifact rights at release time, and local paired-LoRA training throughput. Each has an action and rejection rule in [FOLLOW-UP.md](FOLLOW-UP.md). No unknown is represented as a completed local test.
