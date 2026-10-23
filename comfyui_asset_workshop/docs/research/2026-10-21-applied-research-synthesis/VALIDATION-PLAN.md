# Finite validation for the next Mumblebox iteration

This is a proposed future experiment. No step below was executed in this research session. Brian reviews the recommendation before implementation. The aim is to settle a product decision, not keep optimizing until every image is perfect.

## Decision to make

Does a camera-aware, model-specific route improve the first usable mesh over the clean existing baseline on a 16 GB GPU / 64 GB RAM Windows machine? Does optional guided refinement add enough value to justify its time and complexity? If not, retain the simpler baseline and identify the narrow unresolved failure.

## Fixed evaluation set

Use six owned or clearly licensed ground-truth meshes. Freeze their dimensions and identifying features before rendering. Keep the test objects out of any later training data.

| ID | Subject | What it tests |
|---|---|---|
| A | Asymmetric toy camera with one side grip and a protruding lens | Camera orientation, front/rear identity, body thickness, small attachments |
| B | Wrench or bracket with a through-hole and a thin handle | Planarity, open holes, thin geometry, surface bumps |
| C | Small building with an off-center door and a side window | Parallel walls, corners, roof pitch, side assignment |
| D | Simple vehicle with distinct front/rear and visible wheel spacing | Wheel count, axle placement, length/width proportions, underside coverage |
| E | Stylized person in a fixed neutral pose with a backpack | Articulation, limb separation, face/body identity, occluded accessories |
| F | Creature with an asymmetric horn or tail | Organic geometry, appendages, self-occlusion and category generalization |

Also use two creative images without known 3D truth for a final user-experience check. Do not report numerical ground-truth geometry accuracy for those. Their purpose is to establish whether the workflow is understandable and the result is useful to Brian.

Render a reference orbit with exact cameras, masks and neutral material. Retain withheld elevations and diagonals. Use the same renderer, physical object scale, image size and coordinate definition across each comparison. Material variants should not leak the test geometry into training.

## Frozen variables and run records

- Exact model/adapter/encoder/VAE revisions and quantization.
- Complete recipe, reference order/roles, prompt compilation and seed policy.
- Per-image original dimensions, pixel transform, K, world-to-camera transform and confidence/source.
- Same mask and framing when comparing conditioning methods; no hidden independent recrops.
- Same geometry sampler seed, resolution, steps/guidance, decoder/token settings and export target where the comparison allows it.
- Record actual device, time by stage, startup/sampling/export peak VRAM, process RAM and cleanup behavior.
- Preserve failed outputs and concise reasons. A technically failed run is not a quality score.

The proposed numerical gates below are engineering criteria, not claims from the papers. They may be changed before running the test, then remain fixed for that comparison.

## V1 — Prove image/camera plumbing before judging AI

Run deterministic projection checks for all six meshes and at least eight known cameras, including elevation, a rear view, a changed FOV and a non-square frame. Exercise exact panel extraction, crop, pad and resize.

Verify:

1. Known landmarks reproject within one pixel at the chosen output size, allowing a documented raster-edge tolerance.
2. Recomputed K follows the actual pixel transform; no unrecorded anisotropic stretch or bounding-box normalization.
3. World/camera axes, handedness, degrees/radians, matrix direction and object-relative left/right agree.
4. Depth, normals and masks come from the same camera and map conventions match the target adapter.
5. Native Pixal cardinal slots receive cardinal cameras; arbitrary cameras use the compatible custom path.
6. The relevant checkpoint is genuinely multiview. TRELLIS first-image behavior is represented honestly.
7. Omitted camera outputs, fallback identities and invalid numeric values are marked unknown, not accepted as calibration.

**Pass:** all deterministic checks pass. **Failure:** repair the owning camera/preparation code and rerun the affected checks. Do not spend image-generation attempts compensating for a failed projection test.

## V2 — Establish reconstruction baselines

For each of A–F, make:

- B0: the existing clean single-image baseline from a useful three-quarter view.
- B1: the current supported multiview route using four exact known-camera renders.

This is 12 planned mesh reconstructions. The four views must suit the actual camera contract; do not relabel diagonals to use a cardinal-only input.

Compare geometry without texture as well as the textured export. B1 tells us whether accurate extra evidence helps the existing reconstruction path. If B1 does not beat B0 on a category, generating more views is not yet the justified repair for that category.

**Pass:** technically valid meshes/exports and interpretable quality differences. **Decision:** retain the best supported baseline per category. **Stop condition:** no parameter search beyond the fixed presets in this baseline stage.

## V3 — Test camera estimation against truth and contradictions

Compare DA3 Small and Base on the six known sets. Include altered framing and deliberately corrupted sets: duplicate front labeled rear; mirrored view; changed part count; wrong body thickness; nonoverlapping textureless views. This is at most 12 main estimator evaluations plus small corruption checks.

Measure rotation error, focal/projection consistency, reprojection error, and whether uncertainty is detected. Align only the legitimate global coordinate/scale freedom. Do not use per-view arbitrary warps to make estimates look correct.

**Provisional promotion gate:** median rotation error no greater than 10 degrees and 90th percentile no greater than 20 degrees on the suitable asymmetric known-camera subset, with no systematic 180-degree flips. Ambiguous symmetric cases must be reported separately. These gates are a starting product tolerance, not a guarantee of downstream accuracy.

A candidate also has to avoid confidently approving the deliberately contradictory sets. On at most six suitable sets, reconstruct with the best estimated cameras and compare against B1's true cameras. Promotion ultimately depends on mesh impact, not only angular error.

**If unsuccessful:** do not make estimation mandatory. Use known cameras where available, manual review and the smaller/single-image fallback. Consider deterministic camera-only fitting on the subset with sufficient landmarks. Do not open a sweep through every pose model.

## V4 — Compare complete image-control recipes

First verify the exact family-specific encoder, reference order, guide format, sampler and adapter compatibility. AnyAngle's original-first/rough-second check is one explicit paired diagnostic, not a universal image-number assumption.

The main comparison is:

- I1: Klein 4B with its documented depth-plus-reference adapter.
- I2: Qwen 2.1 AnyAngle with the documented original/rough roles, where its research-use terms permit the evaluation.

Use four requested target views for each of A–F: 48 planned outputs. Prefer one informative elevated view over four nearly redundant angles. The baseline mesh is fixed for guide rendering. AnyAngle gets its documented RGB guide; depth-only cannot be silently substituted and then called a fair test of AnyAngle. The RGB risk is recorded separately.

Permit at most one review-driven replacement per subject per route: 12 extra outputs. Add at most four diagnostic outputs for reference-order or map-format verification. Total cap: **64 main comparison image outputs**. Do not improve one route through many retries while leaving the other at its first seed.

Use brief capability checks for the remaining supported families, capped separately at three outputs per family. Those establish correct wiring/defaults and an honest support description; they do not claim equally good multiview performance for every model.

**Image acceptance:** complete object; intended side/elevation reasonably present; no essential missing/extra part; compatible major proportions; no unwanted pose change; plausible unchanged identity. Record the failure type. An attractive image can fail.

**Decision:** choose the route with the best useful-view rate and downstream geometry at acceptable cost. If the existing recipes fail systematically, stop the quality comparison and use the saved failures to define a custom-adapter pilot. Do not respond with unbounded prompt churn.

## V5 — Reconstruct from the approved generated evidence

For each of A–F, reconstruct once from the selected route's accepted images/cameras, up to six meshes. Compare to B0 and B1. Use as many genuinely useful views as the supported path can consume; do not pad the set with bad images to reach a target count.

This is the decisive test of whether good-looking generated views improve a mesh. If they do not, retain B0/B1 and report which failure remains: image contradiction, camera estimation, reconstruction limitation or mask loss.

## V6 — One optional improvement branch

Select at most four representative cases with a clear baseline defect. Choose **one** of the following for this comparison:

- camera/limited-shape fitting using approved masks/landmarks;
- compatible direct geometry refinement, if terms and memory permit;
- a second guided-image pass with targeted views.

Do not stack all three before learning which helps. For a second image pass, cap it at four target images per case, 16 outputs, and one final reconstruction per case. Use the same saved first mesh; do not regenerate the entire history.

**Promotion:** at least a 10% median reduction in the chosen normalized geometry error on the applicable known-truth cases, or a clearly predeclared feature-recovery benefit that the scalar metric misses; no increase in catastrophic feature/topology failures; acceptable measured latency and memory. Report both improvements and regressions.

**Rejection:** no material geometry benefit, recurrent identity loss, copied proxy defects, destroyed thin parts, unacceptable runtime, or failure to fit safely. Keep the baseline. One documented preset adjustment is allowed for a known configuration issue; a new architecture requires a separate decision.

## Measures that matter

| Measure | How to use it honestly |
|---|---|
| Relative dimension/landmark error | Compare known body ratios, wheel centers, doors, handles and appendages after a single legitimate rigid/scale alignment. |
| Surface distance / F-score | Sample surfaces consistently and normalize by object size. Record alignment and thresholds. Texture must not affect the score. |
| Held-out silhouette overlap | Render viewpoints not used in fitting/generation. Helps expose a shape that only looks correct in the input views. |
| Essential feature checklist | Count expected holes/parts, topology connections and open gaps. Smoothness alone cannot replace this. |
| Human shape score | Blind or randomized side-by-side review where practical: 1 unusable, 2 major repair, 3 useful base, 4 minor cleanup, 5 unusually faithful. |
| Game/print usefulness | Correct import, scale/orientation, UV/material integrity, or print-specific dimensions/thickness/manifold checks. |
| User effort | Replacements, mask corrections and decisions needed for an accepted mesh. |
| Resources | Whole-job wall time, stage time, startup/sampling/export VRAM peaks, RAM, and cleanup after success/failure/cancel. |

COLMAP/learned confidence/VLM comments are secondary diagnostics, not ground truth. A failed feature match on a plain plastic toy is not automatic proof that the view is invalid. A confident geometric prediction on contradictory images is not proof they are valid.

## V7 — Mechanical product checks

In Brian's existing visible Comfy Desktop, narrate the current test and overall scope. Exercise the actual installed controls:

- Start clean; create/upload; enhance and auto-describe with model awareness.
- Add described references; edit the initial image and a generated view; apply/keep/retry masks.
- Generate; cancel; recover; select/deselect; clear one/all with the required confirmation.
- Verify stale angles do not survive a new design as accepted evidence.
- Switch family; verify defaults, seed behavior, LoRA strength and compatible adapters.
- Generate geometry-only and textured outputs where supported; save/download/reload the files.
- Check history reuse/deletion semantics and parameter provenance.
- Check visible stage progress, resource readouts, unload and failure cleanup.

These checks verify existing requirements and any changed behavior. They are not authorization for a new UI design or unrelated feature expansion.

## Overall budget and stopping point

**Model support is earned by the test.** The five researched families are candidates, not a release requirement. Record a qualified role (initial design, editing, guided angles), or remove a failing model from the supported set if it has no useful role. Keep user data and recorded model provenance intact. After checking the documented setup and repairing concrete integration defects, reject an unproductive quality route rather than extending prompts, adapters and seeds indefinitely. A narrow category restriction is acceptable when the evidence supports it and the UI explains it. Supporting one successful model is an acceptable outcome. A failed test establishes a practical limit of this route and setup, not a universal proof about the model's capabilities.

Planned mesh reconstructions: 12 baselines + up to 6 camera-estimation comparisons + 6 generated-evidence meshes + up to 4 optional-improvement meshes = **at most 28 principal mesh runs**, before necessary technical reruns. Do not expand this into the Cartesian product of five image models, all adapters, all seeds and all export settings. A technical defect is repaired and retested; a quality experiment reaches a decision rather than becoming an endless defect list.

The iteration is ready for user review when:

1. Camera/preprocessing contracts pass.
2. All six subjects have recorded results and failure classifications.
3. At least one documented route reaches “useful base” or better on at least four of the six, without concealing failures in the other categories. This is a provisional release-to-Brian threshold, not a claim of general reliability.
4. The optional improvement branch is either promoted by evidence or rejected with the baseline retained.
5. Export/history/cancel/cleanup and changed controls pass mechanical checks.
6. Model support, category limits, licensing and memory settings are accurately explained.

If the quality threshold is not met, stop the **comparison** with its evidence and a precise next proposal. Do not label the product complete or keep adding adapters without a decision. If it is met, stop optimization and let Brian use the workflow. Perfection across all models and views is explicitly not required.

