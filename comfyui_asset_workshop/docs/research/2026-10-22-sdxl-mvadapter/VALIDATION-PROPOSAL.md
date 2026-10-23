# Proposed finite experiment — not executed

Date: 2026-10-22. Requires Brian's approval and a new implementation goal. This document is the finite test design resulting from research, not authorization to install or generate.

## Hypothesis and routes

**Hypothesis:** generating several views jointly with a trained cross-view adapter can preserve object structure well enough to improve a first mesh, provided the reconstruction uses the correct camera/frame contract. Limited human selection/correction can be part of a successful practical workflow.

Primary: approved source image → BiRefNet/accepted alpha → SDXL I2MV MV-Adapter six-view batch → image review and camera-bearing bundle → validated orthographic Pixal feature projection → one full master → optional texture → GPU PEC/bake → export.

Only fallback: replace Pixal reconstruction with StableNormal plus the Era3D orthographic NeuS family; keep source, generator and evaluation fixed. This is conditional and has its own memory, normal-coordinate and export gate. It is not an automatic second full campaign.

No draft-mesh/image/second-mesh loop. No new image-family sweep, camera-LoRA training, GUI, Pinokio, paid services or public release work. Known meshes may generate **test fixtures** with exact cameras; those are ground-truth controls, not the intended user's runtime input.

## Gate V0 — correct inputs and viable execution before image trials

Use three owned known-truth fixtures, selected before generation:

1. Asymmetric prop with a clear front/back distinction, a hole and a thin part.
2. Spaceship-relevant mechanical component with distinct mounting faces, protrusions and a measurable proportion.
3. Meaningful organic/character subject with limbs and a distinct rear feature; no replacement with another box.

Choose a source view in the image adapter's demonstrated input region, preferably showing more than one face. The paper's evaluation distribution is evidence about what was evaluated, not a universal guarantee for arbitrary uploads. Save source images, truth meshes, camera matrices, projection types, masks, scales and all preprocessing transforms.

Before loading the image model, validate the projection bridge algebraically and against known landmark renders. Test at least front, oblique and side views. A common object coordinate system and exact frame transforms must map landmarks to approximately one pixel at the selected resolution. Include intentionally wrong view order, mirror convention and independent recropping as negative controls; those must fail the checks.

Preferred primary bridge: explicit orthographic projection at all feature-sampling stages. A distant-perspective bridge is permissible only if selected and documented **before** the generated-image comparison, with an analytical pixel-error bound over the normalized object's depth. Do not switch formulas after seeing which generated result looks nicest.

Then reconstruct one known true-view control. Mathematical projection correctness alone is not enough: the model must retain useful geometry from the correctly posed inputs. Continue the other two true-view controls only after that passes. These count within the reconstruction budget below. Reject the primary if it requires guessed FOV, inconsistent per-view scaling, destructive changes to the working pipeline, or unusable true-view geometry.

Check the image worker's exact dependency/import/load path without downgrading the desktop. The first actual generation is the first counted V1 batch, not an unrecorded series of smokes. Actual workflow changes and generations must be visible in the existing Comfy Desktop. Source inspection or backend success alone does not satisfy visible proof.

Fallback may be considered after a primary V0 rejection, before expanding V1. Prove correct normal-coordinate conversion, orthographic rays, GPU surface extraction, viable dependency terms, and a defined export path. Retain failed-primary evidence and subtract spent work from the same total budget. If the remaining budget cannot answer the fallback's question, stop and ask for a revised experiment rather than silently replenishing it.

Proposed setup timebox: at most four active engineering hours for V0 and runtime integration before a review checkpoint. Download waiting time should be reported separately. If that timebox expires without a defensible runnable contract, return the concrete evidence and stop; do not silently turn compatibility work into a new framework or consume the quality-testing allocation on invalid inputs. This timebox is part of the proposal for approval, not a forecast of completion time.

## Gate V1 — one documented recipe, then one derivative

Baseline: exact SDXL base, released standard image-conditioned MV-Adapter, FP16-fix VAE, six 768 × 768 targets, DDPM with interpolated SNR shift 8, CFG 3, reference conditioning 1, 50 steps. Freeze model hashes and scheduler. Save the actual seed; random mode must resolve to a recorded integer.

Derivative: only `RunDiffusion/Juggernaut-XL-v9/Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`, subject to its exact terms. Same source, camera set, seed policy and sampler recipe. No Lightning, alternate SDXL checkpoint, generic prompt sweep or multiple CFG trials.

Run one baseline batch on the first fixture. Inspect all six. If it produces grossly conflicting geometry, do not fill the budget with more of the same. A documented technical defect can consume a technical retry. A poor but technically valid image is a quality result, not a free retry.

After technical success, complete the paired baseline/derivative batches across all three fixtures. Preserve every output. Generate jointly; retain model residency for that batch. Release the image pipeline before reconstruction.

Selection rule: try all six as candidates, select at least four coherent views spanning near-front, rear and both sides. Four near-duplicate front images do not qualify. Preserve the real camera entries and original frames for the selected subset. If the engine requires a first-view canonical frame, apply a proven common coordinate transformation; do not silently reinterpret the selected first image as “front.”

Reject a set with changed part counts, mirrored handedness, invented major attachments, absent essential features, clipping or incompatible proportions. A tiny surface blemish is not equivalent to a missing limb. Write those fixture-specific distinctions before seeing results. A VLM may assist review, but cannot be the sole source of geometric approval.

## Gate V2 — compare full geometry and a fresh case

For each known fixture preserve:

- Single-image Pixal baseline from the same approved source.
- True-camera, true-view reconstruction in the selected multiview engine.
- SDXL-generated-view reconstruction, if its view set is coherent.
- Juggernaut-generated-view reconstruction, if coherent.

If the fallback engine differs from the single-image baseline, the comparison measures the **whole proposed pipeline**, not the adapter alone. True-view controls help separate reconstruction limitations from generated-view limitations. Do not overclaim causality.

Evaluate full masters before reduction or texture:

1. One shared rigid/similarity alignment and common scale convention; no per-axis stretch to conceal wrong proportions.
2. Symmetric surface-distance distribution normalized to the truth object's bounding-box diagonal; report median and a tail statistic, not just one favorable number.
3. Silhouette agreement from held-out directions, chosen before the test and including an elevated view for inspection.
4. Declared essential-feature checklist: holes, thin parts, appendage counts, handedness, attachment positions, front/rear identity.
5. Connected components, obvious holes/intersections and practical editability. Report rather than pretending every legitimate open surface is a defect.

Suggested quality gate, a proposed project threshold rather than a scientific law: at least two of the three controlled subjects improve normalized median error by 10% or more over the single-image baseline, without new catastrophic feature failures. Report all subjects, tail errors and silhouettes. The organic/character subject must remain recognizable and useful; primitive success alone is insufficient.

Use one fresh fourth design with the winning route. Compare its single-image and multiview meshes. Require correct declared essential parts/proportions and a coherent selected set. If it has no true mesh, do not invent a numerical accuracy percentage. Its result tests practical generalization, not hidden ground truth.

If baseline works but Juggernaut does not, keep baseline. If neither is useful, stop with a negative result. “Completed generation” and “exported a file” do not satisfy quality.

## Limited manual correction and optional style slot

Preserve raw automatic outputs and metrics first. Then one optional slot may be used for **either**:

- One six-view style batch and one associated reconstruction, after the no-style route passes; or
- Up to six targeted edited-image outputs on one preselected problematic subject and one assisted reconstruction. No more than two attempts on any one image, and no redesign of the whole subject.

This shares the existing optional six-image/one-mesh budget; it is not an additional allowance. Changes can correct a mask, isolated feature or one inconsistent view. A camera/projection defect must be corrected in its owner rather than hidden by image edits. Inspect all affected views afterward.

Record time, number of edits, rejected attempts and the user's approval effort. An assisted result may justify a **human-assisted candidate**, clearly labeled, even if the automatic result is weaker. Do not relabel the raw automatic scores or claim general robustness from rescuing one subject. More extensive manual work belongs in a separate usability decision.

## Gate V3 — GPU finishing, actual saved files, and release

Finish at most two selected geometries. Reuse saved geometry; do not regenerate images or shape to test an export change. Keep an untouched full master.

Primary path may use the already exercised Pixal texture generation and native GPU PEC/voxel bake. Preserve current preset initially; any finishing change must be justified by a measured defect. Heavy processing stays on GPU. Normal CPU orchestration and file writing are expected.

For fallback, prove the vertex-color/radiance-to-UV bridge before claiming textured export. A geometry-only or vertex-colored mesh can be an intermediate success, but does not fulfill a claimed PBR texture deliverable. Do not attach Pixal's voxel baker to incompatible data or infer metalness from an RGB picture without an explicit method.

Reopen actual exported files in the existing visible viewer. Verify geometry, material/texture references, UV bounds and image presence. Prove the geometry-only path bypasses texture/UV work. Report game and print diagnostics separately. Record controlled cancellation and one focused error-cleanup check without deliberately exhausting the system.

## Shared hard limits

| Item | Maximum |
|---|---|
| Image checkpoints | Official SDXL base plus one exact Juggernaut candidate. |
| Known fixtures | Three varied owned objects. |
| Core batches | Six batches × six views = 36 images. |
| Fresh held-out design | One batch × six = 6 more; running total 42. |
| Optional slot | Six style images OR up to six targeted edit outputs; total 48. |
| Normal reconstruction allocation | 3 single controls + 3 true-view controls + 6 generated comparisons + 2 held-out controls + 1 optional comparison = 15. |
| Technical reruns | Two total events. Each event is one image batch OR one reconstruction, with its observed defect recorded. |
| Absolute ceilings | At most 60 generated images and 17 reconstructions. These are separate ceilings, not permission for four retry events. |
| Texture/export checks | At most two chosen geometries. |
| New training / paid compute | Zero. |

Do not fabricate scores for skipped failed sets to fill the table. Unused budget is not a reason to keep experimenting after the decision is clear. Primary/fallback share the limits. A different view count, new backbone or broader repair campaign requires a new decision.

Proposed runtime guardrails, to be approved with the experiment: 20 minutes per image batch, 60 minutes per reconstruction, 20 minutes per finishing job. Exceeding a guardrail stops that candidate for review rather than triggering CPU fallback. These are runaway-job limits, not predicted performance or acceptable product latency. Keep frequent meaningful progress narration while jobs run.

Proposed memory reserves: approximately 1.5 GiB VRAM and 8 GiB available system RAM. Record peak reserved/allocated GPU memory, host working set, available RAM and stage-release behavior. No second heavy app running concurrently. Do not claim reclaim from an `empty_cache()` call without observing release of live objects.

## Explicit rejection and stopping rules

Stop the route before downstream generation if projection/crop semantics are unproven, true-view controls are unusable, the GPU path cannot fit, required terms are incompatible, or the runtime integration would damage the working desktop.

Stop the candidate after its quality gates fail. Do not compensate with indefinite seeds, a growing helper stack, all five old image models, unbounded category tuning or another mesh feedback pass. Two exhausted technical retry events mean return to Brian with the defect and evidence.

After the capped run, deliver the fixtures, full masters, rejected outputs, seeds/settings, stage timings/memory, raw versus assisted judgments, actual reopened exports, and a plain-English verdict:

- **Promising automatic candidate:** gates pass on raw outputs within bounds.
- **Promising assisted candidate:** defined limited correction produces a useful result; exact assistance and weaker raw scores disclosed.
- **Partial technical result:** some stages work but geometry, exports or hardware gates remain unmet.
- **Negative experiment:** no acceptable improvement under the declared conditions.

Then unload test models and stop for review. Do not declare a working Mumblebox solution from a partial/negative experiment. Do not integrate the experiment into the preserved main workflow or start GUI work automatically.
