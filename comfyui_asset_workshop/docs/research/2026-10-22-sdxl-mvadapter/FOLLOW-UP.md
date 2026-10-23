# Consequential unknowns and finite follow-up

Date: 2026-10-22. This is a prioritized set of questions for later approval, not an active second research pass. Do not execute all rows automatically. The immediate proposed experiment is in [VALIDATION-PROPOSAL.md](VALIDATION-PROPOSAL.md).

## Before any generated-view campaign

| ID | Unknown | Smallest useful next action | Evidence required / stop rule |
|---|---|---|---|
| F01 | Does exact orthographic conditioning work with the selected Pixal weights? | Trace all feature projection consumers, implement one explicit contract in the independent experiment, then use known rendered geometry. | Approximately one-pixel landmark agreement, failing negative controls, useful true-view master. If projection is right but the model fails, reject that pairing; do not blame image prompting. |
| F02 | Can distant perspective approximate the required rays safely? | If selected instead of the direct bridge, derive error over the normalized object's depth and verify it with the same known cameras. | Record focal/distance/normalization, numerical error and model behavior. A guessed FOV or attractive preview is not a pass. This is an alternative bridge inside F01, not extra unlimited trials. |
| F03 | Can the authored image pipeline run on the current GPU without damaging the desktop? | Select a version-isolated runtime and inspect GPU support, then one counted baseline batch after the camera gate. | Exact import/load path, installed visible output, peak memory, cleanup. No global downgrade; no repeated installation carousel. Two technical retry events cover the whole proposed experiment. |
| F04 | Can the orthographic NeuS fallback fit/run legally and on GPU? | Only if primary is rejected: trace normal transforms, actual imported dependencies, GPU extraction and export representation. | One known control within the remaining budget. Do not infer nvdiffrast necessity from a full requirements file, or infer its absence without checking the execution import path. Reject if fit/GPU/terms/export cannot be resolved narrowly. |

## Questions answered by the bounded comparison

| ID | Unknown | Probe | Stop / decision |
|---|---|---|---|
| F05 | Are views geometrically consistent, rather than merely attractive? | Three varied known objects, fixed batches, view/feature review and full-master metrics. | Fail if coherent coverage is missing or geometry gates fail. Do not sweep seeds indefinitely. |
| F06 | Does Juggernaut improve this task? | One exact ordinary v9 checkpoint paired with official base. | Retain only if it preserves consistency and practical mesh quality. A nicer picture alone does not earn support. |
| F07 | Are a few edits enough? | Use the optional slot for one bounded correction check, retain raw outputs, count attempts and time. | An assisted success is labeled assisted. If it requires repeated redesign or exceeds its allocation, stop and revise the product promise. |
| F08 | Can style remain compatible? | Only after core success and only if the optional slot was not used for corrections: one licensed LoRA, one batch, one reconstruction. | Reject style support if essential features or shape degrade. No anime/model catalog expansion. |
| F09 | Does the selected route export usable files without retaining memory? | Up to two geometry-preserving GPU finishing checks, actual reopen, cancel/error release check. | Geometry-only is not PBR proof. UV/bake problems are reported separately from reconstruction quality. No hidden CPU fallback. |

## Custom training: a possible later decision, not the next automatic action

**Research question:** can a small paired camera-edit LoRA teach enough viewpoint and design preservation on Klein 4B to avoid a larger architecture? This is distinct from training a style LoRA or porting SDXL's MV weights. The user's idea is retained on its merits.

Existing evidence: [BFL's training guide](https://docs.bfl.ai/flux_2/flux2_klein_training) supports local small-model training; [AI Toolkit's Klein implementation](https://github.com/ostris/ai-toolkit/blob/14f8f95090689b585093e5aaf48bc1e2e0a67ea4/extensions_built_in/diffusion_models/flux2/flux2_klein_model.py) and its parent model include reference conditioning. A short style recipe is not proof that a general orientation function can be learned with the same dataset or time budget.

Before proposing a training run:

1. Name the exact failure to improve: pose error, scale drift, missing rear identity, feature copying, or inconsistent shape. Do not train against the vague goal “make everything better.”
2. Check the exact parent checkpoint, paired-image trainer, quantization/offload support, LoRA save/reload format and license. Use undistilled Base as the initial Klein training candidate, not an assumed four-step inference shortcut.
3. Render a small owned, paired dataset with source/target RGB, alpha, cameras and common object scale. Save depth/normals if cheap; decide separately whether they are inputs, supervision or just evaluation. Split by object/family before training.
4. Perform one later approved forward/backward memory probe at the chosen resolution. Record training, validation, caching and checkpoint costs. Fitting inference does not prove training fits.
5. If feasible, approve a short fixed-step pilot with unseen-object evaluation. Compare the unmodified base to the trained model at identical settings. No full-data expansion until useful held-out behavior appears.

A prospective small pilot could use roughly 200 owned varied objects, several paired camera moves each, and a reserved object-family test split. Those numbers are an **experimental design suggestion**, not a proven recipe or promise of generalization. The first pilot's purpose is to detect learnability and failure modes, not ship a universal model.

The fal Qwen angle release is a practical precedent; its saved Comfy graph combines an angle LoRA with a separate Lightning speed LoRA and samples one edited image. The grammar and modifiers are specific to that artifact. That graph demonstrates a reusable image-edit recipe, not shared cross-view attention or accurate reconstructed cameras. Its card names a hosted trainer; local training throughput for this exact Qwen variant was not established. The larger base model still affects training memory even when trainable LoRA weights are small. [Released graph](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA/blob/e3066224ab74263f4a5b6179cd1a3b0a15577e44/comfyui-workflow-multiple-angles.json).

A fresh [FLUX 3 Klein angle LoRA](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora) links a paired dataset and training script, with explicit object-hallucination limitations. If a later training decision is made, inspect that exact script/data lineage as a finite reference. Do not add FLUX 3 support merely because this lead exists.

**Training stop rule:** if the small pilot does not beat the base on held-out objects, do not expand dataset size or rent hardware by default. Diagnose whether labels, paired conditioning, data variety, architecture or evaluation explain it, then bring one evidence-based decision to Brian. A new cross-view architecture is a separate proposal, not a routine LoRA tweak.

## Money and scheduling

Default budget remains $0. No rental is necessary for the current research or proposed released-weight comparison. If a future pilot requires rental, first measure local/proxy throughput and estimate steps, evaluation and storage.

For scale only, [Runpod's public page](https://www.runpod.io/pricing), checked 2026-10-22, lists an A100 80 GB option at $1.79/hour. At that displayed rate, 10 compute hours are $17.90 and 24 are $42.96, before storage and other charges. Availability, setup time and actual training throughput may change the outcome. This is arithmetic, not a quote or a promise that $50 trains the desired adapter.

## Watchlist with explicit release triggers

| Lead | Revisit only when | Finite investigation |
|---|---|---|
| T3lescope | Official code, weights and terms are published. | Verify small-object/low-view inputs, camera requirements, exact 16 GB memory path and a reproducible example. Two focused source passes; if still unavailable, keep on watchlist. No package-name guessing. |
| Gaussian Wrapping | A real-capture use case and acceptable implementation terms become relevant. | Verify actual input capture/pose requirements and hardware. Do not reinterpret it as a single-image completion adapter. |
| New compatible Comfy MV workflow | Downloadable graph plus owner code/current-version evidence exists. | Trace actual reference and camera connections. Do not replace a working integration on the strength of a video thumbnail. |
| New local trainer | Exact backbone and paired-reference support are implemented. | Check one config and owning conditioning path, then request a bounded runtime pilot if justified. |

No recurring monitoring or automation was created. These are triggers for a later deliberate research request.

## Before public distribution, not before the research discussion

Refresh the licenses of exact selected files, including DINOv3/NAF, optional renderer components and any style weights. Record code notices separately from model and asset rights. Verify the regional gating metadata on selected repositories. Correct overbroad local license labels in a future authorized implementation; this research did not edit the model manifest.

For portability, audit explicit Comfy-local model/cache/output paths, download integrity, resumability, storage cleanup ownership, cancellation and restart behavior. Do not borrow another app's models or claim a single local install proves all Windows systems. Broader GPU-card support is later scope.

For value, a later equal-time AI-plus-cleanup versus Blender-first trial on one spaceship part can measure total correction burden. Record both human time and agent effort; token cost is not inferable from paper benchmarks. This is not a reason to turn the current bounded geometry experiment into a full game-production benchmark.

## Next discussion

Read the recommendation together, settle the primary bridge and correction allowance, then approve or revise the finite validation proposal. If approved, create a new implementation/test goal with those exact limits and visible Comfy requirements. If Brian prefers the lightweight LoRA hypothesis first, explicitly replace the proposed experiment rather than silently adding a third route and extra budgets.

Stop after this research package. No training, deployment, model download, GPU experiment, GUI work or integration proceeds automatically.
