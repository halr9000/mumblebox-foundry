# Remaining uncertainties and the smallest useful follow-up

These questions are part of the completed research result. They are not hidden promises that every candidate works. Reading questions and runtime questions are separated so the next phase does not become another broad literature loop.

## Priority P0 — settle before choosing the default guided route

### F1. Does native DA3 provide usable cameras for our images?

- **Decision affected:** whether automatic camera estimation can improve Pixal3D multiview inputs.
- **Known evidence:** native Small/Base multiview node exists locally and matches inspected upstream source; cards specify Apache 2.0; joint depth/pose is supported. No local generated-object accuracy test was run.
- **Method:** validation V1/V3. Check the complete resized-input/output K contract; known matrices; symmetry; nonoverlap; contradictory images; and reconstruction impact. Inspect the owning model/preprocess code only where the test exposes uncertainty.
- **Dependencies:** deterministic renderer, original frames and transforms, an accepted small/base checkpoint, cleared GPU stages.
- **Sufficient evidence:** projection tests pass, useful pose accuracy on asymmetric objects, honest ambiguity detection, and no material mesh regression against true-camera controls.
- **Stop rule:** compare Small and Base once on the fixed set. If neither helps, do not make them mandatory or launch a general estimator search. Use known-camera/single-image fallback and consider F4.
- **Type:** runtime prerequisite. More benchmark reading cannot settle our generated-image distribution.

### F2. Are the model-specific control contracts correctly applied?

- **Decision affected:** which guided-image lane is trustworthy enough to compare.
- **Known evidence:** exact RefControl, fal Edit/Lightning and T8 AnyAngle graphs were inspected. T8's October controlled comparison found image-order sensitivity. Local recipes already contain structural-control branches.
- **Method:** trace selected graph from input references through encoders/latents to sampler; compare roles, variant, map conventions and parameter defaults. Perform a bounded paired order/map test on two fixed objects.
- **Dependencies:** original/rough image pair at recorded dimensions, pinned weights/graph, unchanged seed for paired diagnostics.
- **Sufficient evidence:** actual encoded reference order and control tensors match the selected recipe; visible orientation responds; identity remains usable.
- **Stop rule:** correct documented mismatches, then run V4. Do not create a universal prompt as a substitute for a trained input contract.
- **Type:** focused source inspection plus runtime prerequisite.

### F3. Does multiview reconstruction help once the cameras are correct?

- **Decision affected:** whether generated extra views are worth their cost and whether the two-pass option should exist by default.
- **Known evidence:** cropping influenced the historical toy-camera proportions, but did not prove correctness. Native cardinal slots and custom-camera routes differ. Newer integrated methods support geometry-aware reconstruction in principle.
- **Method:** fixed six-subject B0/B1 comparison followed by generated-evidence reconstruction, with geometry metrics and held-out renders.
- **Dependencies:** F1/F2 where estimated/generated evidence is used; correct exact-camera test set first.
- **Sufficient evidence:** compatible extra views improve useful geometry on enough categories to justify the added work; bad views are identifiable without pretending all are equally valuable.
- **Stop rule:** retain the best baseline if generated multiview evidence fails. Do not keep increasing view count.
- **Type:** runtime prerequisite.

### F4. Can camera-only or limited-shape fitting fix a meaningful subset cheaply?

- **Decision affected:** whether to write a small deterministic custom node before training.
- **Known evidence:** OpenCV PnP, CubeSLAM, Kaolin camera APIs and PyTorch3D optimization examples provide real mechanisms. They require landmarks, a proxy or reliable image evidence; none solves arbitrary hidden geometry.
- **Method:** one asymmetric rigid prop and one building, then a withheld subject. Fit camera only with multiple starts; add bounded dimensions only after that passes. Test ambiguous/symmetric negative controls.
- **Dependencies:** permitted renderer/optimizer, masks/landmarks, fixed projection conventions and an explicit loss.
- **Sufficient evidence:** lower held-out reprojection/geometry error without implausible shape distortion or confident false fits.
- **Stop rule:** if the proxy bias dominates or only the fitted images improve, do not expand to organic subjects. Document the narrower category or reject.
- **Type:** small research prototype requiring future implementation approval.

### F5. Does the exact selected stack have an honest commercial-use path?

- **Decision affected:** default versus optional model/control/refinement route and release labels.
- **Known evidence:** core Pixal3D is currently MIT; DINOv3 and some renderers have separate terms. Qwen 2.1, Klein 9B, FLUX 3 and UltraShape have different conditions. A separate VGGT commercial checkpoint does not resolve every derived checkpoint's lineage.
- **Method:** build the dependency bill for only the selected graph; pin each code/weight/encoder/adapter/renderer and its terms. Resolve original versus commercial VGGT derivation where relevant. Clarify missing Mix3R permissions only if it becomes a serious candidate.
- **Dependencies:** an exact candidate graph, not a product name.
- **Sufficient evidence:** every included component has a documented permissible route for the intended use, or the lane is explicitly conditional and omitted from the permissive default.
- **Stop rule:** do not pursue opaque lineage indefinitely. Prefer the known permitted alternative. No license acceptance, private credential use or vendor contact is part of this research task.
- **Type:** focused reading/possibly later authorized clarification; release prerequisite, not a reason to block all local research candidates.

## Priority P1 — after the baseline comparison

### F6. Does direct geometry refinement beat another image-generation pass?

- **Decision affected:** optional improvement stage and user-facing quality controls.
- **Known evidence:** UltraShape accepts a rough mesh and image; its community example is real but Hunyuan-oriented. Startup memory and conditional license remain relevant. Geometry changes require texture rebaking.
- **Method:** choose either an eligible UltraShape bridge or the deterministic fitter, keep the same baseline mesh, and compare four representative cases. Record thin parts, holes, proportions and runtime.
- **Dependencies:** scale/orientation bridge, allowed terms, memory-safe initialization and a saved baseline.
- **Sufficient evidence:** the V6 improvement gate with no catastrophic feature losses.
- **Stop rule:** one branch and one documented preset correction. Reject it if it only improves shading or copies proxy mistakes; no endless refinement chain.
- **Type:** runtime comparison after F3.

### F7. Is a focused Klein 4B control adapter trainable usefully on 16 GB?

- **Decision affected:** whether custom training is justified and whether any rental should be proposed.
- **Known evidence:** Musubi's training forward supports multiple control latents; RefControl establishes the conditioning idea. Full fine-tuning examples use much larger resources and narrower tasks.
- **Method:** object-disjoint owned-data pilot. First test a small batch at 512 resolution with frozen base, cached encodings, supported quantization/checkpointing/offload. Measure actual peak memory and steps/second, then a capped training run and unseen-object evaluation.
- **Dependencies:** F2/F3 failures that define an actual learning target, data rights, working exact trainer and checkpoint mapping.
- **Sufficient evidence:** stable local training and measurable held-out camera/proportion improvement over existing adapters, including downstream mesh quality.
- **Stop rule:** do not scale data or buy compute for a loss that does not learn the intended behavior on a small controlled problem. If memory alone prevents the meaningful pilot, present measured requirements and a capped rental proposal.
- **Type:** later experimental training; not authorized to run now.

### F8. Can Pixal3D adaptation improve a repeatable geometry defect?

- **Decision affected:** image adapter versus mesh adapter investment.
- **Known evidence:** WorldSculpt has actual Pixal3D LoRA code and released calibrated-scene adapters. Its data, camera setup and occlusion task differ from ours.
- **Method:** inspect exact training config/loss/latent preparation for the proposed category; measure minimal local forward/backward peak; train only if correct-camera baselines show a persistent model limitation. Test unseen meshes and clean versus corrupted inputs.
- **Dependencies:** ground-truth geometry, lawful checkpoint/data lineage, a stable training/export contract and F3 results.
- **Sufficient evidence:** improvement of the targeted surface/feature failure without broad degradation, at a justified cost.
- **Stop rule:** no universal “all game assets” training attempt from a tiny category pilot. If the complete trainer or resources are unavailable, leave this as a scoped longer-term option.
- **Type:** focused additional source work then a future training experiment.

### F9. Does a VLM design record reduce user corrections?

- **Decision affected:** model-aware enhance/auto-describe behavior and hidden-surface planning.
- **Known evidence:** local VLMs can describe/plan, but published tests show weaknesses around 3D inference. A fluent hidden-surface story is not observed truth.
- **Method:** compare the same descriptions with and without an approved visible/proposed/uncertain record on a fixed small set; count invented essential changes and user corrections. Test object-relative side naming.
- **Dependencies:** local helper lifecycle, stable schema, user approval and per-family prompt compiler.
- **Sufficient evidence:** fewer contradictory features and edits without a large speed/memory penalty.
- **Stop rule:** retain ordinary human description if the helper adds unreliable complexity. Never make its judgment the sole acceptance gate.
- **Type:** runtime/product comparison; no additional general VLM search needed first.

### F10. Which memory and export settings should be the 16 GB profile?

- **Decision affected:** safe recommended quality defaults, visible limits and speed.
- **Known evidence:** existing lifecycle/PEC paths are present. Several external loaders demonstrate how startup peaks can precede their “low memory” mode. Sparse geometry complexity matters independently of image resolution.
- **Method:** measure sequential stages, startup, cancellation/failure, dense/thin objects, texture size and GPU finishing; inspect only the owner of an observed leak or duplicate load.
- **Dependencies:** a selected route and frozen quality preset.
- **Sufficient evidence:** repeated completion within agreed reserve, no process-memory growth across repeated jobs and acceptable GPU export time.
- **Stop rule:** document a conservative preset and its measured limitations. Do not claim an 8 GB profile or optimize every backend now.
- **Type:** required runtime engineering after route selection.

## Priority P2 — research only if a remaining gap warrants it

| Question | Why it matters | Next evidence and stopping point |
|---|---|---|
| Could explicit camera tokens, joint-view attention or persistent 3D feature memory beat paired control? | Addresses remaining camera and cross-view disagreement at a deeper level | The CVPR 2026 Viewpoint Tokens code supplies an actual camera-MLP/training precedent, but not Klein/Qwen weights. Begin with a compatible-base two-target-view prototype and permitted data. Keep identity and camera accuracy as separate tests. Stop if it cannot beat the existing adapter before scaling. |
| Could an independent implementation replace a uniquely restrictive component? | May preserve a valuable capability with simpler terms | Written behavioral spec, permitted dependencies, training/data requirement and comparison budget. Reject a rewrite if a simpler permitted tool already meets the need. |
| Does Kaolin/FlexiCubes improve actual geometry in our representation? | Differentiable surface extraction could help a fitting stage | Check SDF/volume conversion and a fixed optimization task. Reject if conversion destroys fine geometry or the fitted score improves only training views. |
| Would Warp/CUDA/TensorRT offer a worthwhile speedup? | Could reduce a measured bottleneck | Profile first, benchmark a single expensive stable operation, include compile/startup/cache cost. No rewrite from language preference alone. |
| Is DLSS 5 useful for an optional preview? | Could improve rendered presentation | Authorized SDK, exact GPU compatibility, clean renderer buffers and a preview-only benchmark. Never use enhanced appearance as geometry evidence. |
| Would Replicator be better than a small Blender render script for data? | Scalable labels/randomization if training expands | Compare setup effort and needed labels on the actual data specification. Stop if the simpler existing renderer already supplies them. |
| Can recent integrated systems fit our target hardware and terms? | Future replacement may surpass the current route | Exact checkpoint lineage, a released runnable path and measured startup/steady-state memory. Do not import a 24–80 GB research stack based on a showcase. |
| Do recent video workflows add new evidence? | Practitioners sometimes expose useful integration details early | Search the last month for an identified missing capability; obtain transcript/graph and trace to source. Stop when a lead only repeats an already inspected method. |

## Overall stop for follow-up work

The present research is complete once the questions above are documented, not once every future experiment has succeeded. The next phase should execute the selected finite validation plan after discussion. Further reading is justified only when it can change a specific decision that the current sources and tests cannot settle.

