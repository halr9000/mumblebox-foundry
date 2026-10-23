# WorldSculpt single-object research plan

Date: 2026-10-23

Status: Plan complete and reviewed; awaiting Brian's decision to authorize research. The research described below has not been executed under this goal.

## 1. Purpose and authorization

Brian wants several pictures of the same object to contribute to one useful mesh, including deliberate details on the back and sides. Earlier generated views sometimes disagreed, and earlier reconstruction suffered from camera, framing, scale, or geometry conflicts. WorldSculpt is a candidate because its released design reportedly adds trained multiview aggregation and geometry adaptations to Pixal3D.

The central research question is:

> Can the released WorldSculpt single-object workflow use a small set of imperfect but intentional reference images to produce one better mesh, with practical input preparation and resource use on Brian's 16 GB GPU and 64 GB RAM system?

The current authorization is to create this research plan and stop for review. It does not authorize carrying out the research. Creation of the plan or completion of its planning goal must not trigger research automatically.

If Brian subsequently authorizes research, that pass should inspect existing research, primary sources, released code, workflow JSON, configurations, and artifact metadata. It should produce an implementation proposal for review. Installation, executable imports of unfamiliar code, model loading, generation, benchmarking, training, purchases, and Comfy changes require a later implementation authorization.

No research findings are newly established by this document. Technical details supplied by Brian or retained from earlier investigation are leads to verify against a pinned release. An unresolved runtime question must remain unresolved until runtime work is authorized.

## 2. Accepted decisions and boundaries

- The target is one object reconstructed from several observations of that same object into one mesh. It is not a room-scanning or scene-composition project.
- Start from the supplied `worldsculpt_instance.json` workflow in ComfyUI-WorldSculpt. Inspect its actual nodes and connections before proposing changes. Do not design a substitute graph from scratch by default.
- The supplied workflow is expected to define the intended adapter and aggregator wiring. Verify that expectation, the required weight files, and the active execution path.
- A later experiment belongs in a completely separate ordinary-node workflow in Brian's existing Comfy Desktop. No custom GUI is needed.
- Keep the main Mumblebox workflow saved. Integration into it is a subsequent decision if the independent workflow proves useful.
- Target the current Windows system with 16 GB GPU memory and 64 GB system RAM. Record the exact GPU, software versions, and available headroom during later authorized inspection. The supplied material names an RTX 4080 SUPER; this is not a new hardware measurement.
- Prioritize local, free inference, stage-appropriate model unloading, and GPU finishing. Ordinary CPU orchestration is expected; identify expensive CPU computation rather than claiming every instruction must run on the GPU.
- Use models owned by the authorized Comfy installation. Do not borrow resources or output locations from Swarm or another application's installation.
- Keep research documents and any later approved project artifacts in the existing authorized non-OneDrive project on E:. No installs or writes to D:, Swarm, or OneDrive.
- The parked Civitai integration is outside this goal.
- No image model is preselected for this experiment. Investigate whether the authors recommend an image generator or multiview source, and what evidence supports that recommendation.
- The user supplies pictures of one object. Do not substitute separately generated component meshes joined together as evidence that multiview reconstruction works.
- Modest disagreement between AI-generated views is the target hypothesis. Neither learned weighting nor successful scene reconstruction proves that contradictory generated views are reconciled.
- No custom training, encoder replacement, new adapter architecture, Pinokio work, MCP redesign, or broad model survey is a default part of this pass. Record a concrete dependency only if evidence makes it necessary.

## 3. What must be answered

The research must explain three things at different levels of certainty:

1. **Mechanism:** what each component contains, what it receives, what it learns or computes, where information is combined, and why that could improve geometry.
2. **Practical path:** the released workflow, matching artifacts, input contract, settings, installation recipe, resource strategy, and exported result.
3. **Evidence and decision:** what has been demonstrated, what remains an inference, what our particular pictures still require testing, and whether a bounded independent implementation is justified.

The investigation must make room for a negative answer. If the method needs trustworthy camera information that cannot be obtained from our references, or if the release cannot fit the available hardware through supported execution, say precisely where the path stops. Do not change the objective to make a different task look successful.

## 4. Starting evidence and source discipline

### 4.1 Material already supplied

Brian supplied a detailed WorldSculpt summary in this conversation. It describes the architecture, two adaptation stages, trained aggregators, camera/mask requirements, community workflows, checkpoints, training configuration, and licensing. Treat it as a useful research index; verify important implementation claims before recommending a build.

Existing local source snapshots were located by filename while preparing this plan:

`docs/research/2026-10-21-applied-research-synthesis/sources/`

Files include `AlayaLab--WorldSculpt--README.md`, `AlayaLab--WorldSculpt--LICENSE`, `AlayaLab--WorldSculpt--tree.json`, `AlayaLab--WorldSculpt--inference.py`, `AlayaLab--WorldSculpt--inference.sh`, and `AlayaLab--WorldSculpt--pixal3d_multiview--lora.py`.

Their contents were not re-examined for this planning goal. The later research pass should read the relevant existing notes and snapshots first, extract the usable evidence once, and refresh only gaps, changed releases, or unresolved claims. Historical recommendations do not override the decisions in section 2.

### 4.2 Primary starting links

These are supplied research targets, not newly checked sources in this planning pass:

- Official implementation: <https://github.com/AlayaLab/WorldSculpt>
- Project page: <https://alaya-lab.github.io/WorldSculpt/>
- Paper: <https://arxiv.org/html/2609.05416v1>
- Weights and training configurations: <https://huggingface.co/AlayaLab/WorldSculpt/tree/main>
- Community Comfy integration: <https://github.com/jtydhr88/ComfyUI-WorldSculpt>
- Base Pixal3D: <https://github.com/TencentARC/Pixal3D>
- WorldSculpt license: <https://github.com/AlayaLab/WorldSculpt/blob/main/LICENSE>
- Component notices: <https://github.com/AlayaLab/WorldSculpt/blob/main/THIRD_PARTY_LICENSES.md>
- DINOv3 license: <https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md>

### 4.3 How evidence will be recorded

For every material conclusion, record a claim ID, source URL or local file, source version/commit, relevant section or symbol, date inspected, meaning for our workflow, and remaining uncertainty. Link code to the corresponding method description rather than treating a README as proof of every implementation detail.

Use explicit evidence labels:

| Label | Meaning |
| --- | --- |
| Supplied lead | A statement from the conversation or an older note, awaiting verification |
| Author-documented | Described in current official guidance or the paper |
| Source-confirmed | A pinned implementation or configuration supports the claim |
| Published result | A stated experiment supports the claim under its documented conditions |
| Community-reported | An identifiable user or maintainer reports a result with stated conditions |
| Inference | A reasoned conclusion that has not been directly demonstrated |
| Runtime-unverified | Requires our later authorized execution to establish |
| Contradicted or unavailable | The evidence disagrees, or the necessary artifact/capability is absent |

Separate paper capability from released-code capability, official implementation from community wrapper, real photographed observations from synthetic renders and AI-generated views, and source inspection from local runtime proof.

Prioritize official repositories, author papers, model cards, configurations, licenses, examples, and maintainer answers. Use relevant GitHub issues, Hugging Face discussions, Reddit posts, Civitai workflows, and YouTube demonstrations as targeted discovery aids. Trace technical claims to primary code or reproducible first-hand evidence. For video discovery, favor the last month as Brian previously requested; older official material is appropriate when it documents the release under examination. Record exact versions and timestamps when a demonstration matters.

Do not contact authors, post questions, accept model terms, install skills, or download weight tensors merely to collect evidence. Identify such requirements for a later authorized step. Search for an official skill in the project's own repositories and documentation first; a community skill must not be presented as official.

## 5. Research questions and required outputs

The following work packages define the future research. Their checkboxes are deliberately unchecked. Each package must produce its named answer, or a precise evidence gap; finding many links is not completion.

### R01 — Official guidance, release identity, and existing lessons

**Question:** What is the authoritative, currently released way to operate WorldSculpt, and what do our existing notes already establish?

- [ ] Read the relevant saved WorldSculpt material and extract previously established facts, open questions, and sources without repeating the broad earlier surveys.
- [ ] Find any official `SKILL.md`, agent guide, cookbook, configuration reference, installation guide, FAQ, troubleshooting guide, and supplementary material. Record absence honestly if none is found.
- [ ] Establish the exact official code commit/release, weight revision, paper revision, Comfy wrapper commit, and example workflow revision that form a compatible set.
- [ ] Identify corrections or important maintainer responses since the paper and initial release. Investigate version mismatches that affect our path.
- [ ] Create a glossary explaining terms such as feature, voxel, conditioning, canonical frame, aggregator, LoRA, sparse structure, and shape decoder in ordinary language.

**Evidence:** Official file trees and documents; existing local research; release history and relevant maintainer statements.

**Output / completion:** A short source map and version table, a list of authoritative operating guidance, and a ledger of inherited claims that were verified or left open. No promise of an official skill unless one is actually located.

### R02 — Recommended image source or creation engine

**Question:** Do the authors recommend a particular image generator, multiview generator, renderer, or camera-control method for preparing input?

- [ ] Search official examples, documentation, paper input descriptions, author demonstrations, configurations, and issues for an explicit recommendation.
- [ ] Distinguish a recommended inference input pipeline from a training-data renderer, a convenient demo image generator, or a community preference.
- [ ] Determine whether the intended inputs are real static-object observations, posed renders, generated views, or several supported categories.
- [ ] For any suggested engine, identify whether it supplies actual camera parameters, a commanded angle only, or no usable camera information.
- [ ] Check whether the authors demonstrate its outputs entering WorldSculpt end to end. A visually consistent sheet alone does not establish camera-compatible reconstruction.
- [ ] If no engine is recommended, say so and define the required input properties. Examine our existing image routes only against those properties; do not invent an official preference or reopen every image-model comparison.

**Evidence:** Explicit author statements, example scripts and datasets, workflow input provenance, and relevant reproducible demonstrations.

**Output / completion:** A recommendation-status table: official recommendation / demonstrated source / community suggestion / unsupported. Include what camera and consistency information each source actually supplies and whether an upstream dependency is essential or optional.

### R03 — Mechanism: what the adapters and aggregators actually do

**Question:** How does information in several pictures influence the geometry of one object?

- [ ] Trace one object's data through image encoding, feature refinement, camera projection, shared 3D coordinates, aggregation, sparse structure, detailed shape, and mesh decoding.
- [ ] For each component, record fixed computation versus learned parameters, input/output meaning, tensor shape where needed, training objective, and the stage it influences.
- [ ] Inspect the actual per-location aggregation formula: validity masks, visibility handling, view statistics, learned weighting, residual terms, normalization, and any hard filtering. Determine whether a view can be discarded, merely downweighted, or still affect a pooled residual.
- [ ] Trace anchor-view/global conditioning separately from local multiview conditioning. Explain how anchor choice can influence identity, pose, or geometry.
- [ ] Identify the LoRA target modules, rank and alpha, scaling semantics, loading order, and additional trained conditioning projections. Determine which weights each checkpoint contains.
- [ ] Explain how frozen Pixal3D shape knowledge fills unseen regions and what the new conditioning changes about that process.
- [ ] Inspect single-view behavior, missing-view handling, empty masks, out-of-frame projected locations, and missing aggregator fallbacks. Identify any path that silently substitutes averaging or ignores a reference.
- [ ] Trace a concrete example: a backpack visible only from the rear. Show where that visual evidence can affect occupied volume and detailed geometry, and what happens when front and rear evidence disagree.

**Evidence:** Paper equations and ablations tied to pinned inference, projection, LoRA-loading, and aggregator code. Use diagrams and limited pseudocode to explain the mechanism, not to invent a replacement implementation.

**Output / completion:** A readable component diagram and component cards explaining what each part does and why it is needed. Clearly answer whether all required components together are necessary and what evidence supports any claimed error tolerance.

### R04 — Training, demonstrated robustness, and disagreement limits

**Question:** Which imperfections is the released model trained or demonstrated to tolerate, and which of our problems remain outside that evidence?

- [ ] Verify the training data, fixed-object assumptions, view-count sampling, stage-specific training, loss functions, parameter freezing, precision, iterations, and released configuration completeness.
- [ ] Quantify documented camera-pose perturbations, mask errors, occlusion, downsampling, and view sampling where sources give values. Record unknown magnitudes rather than treating all noise as equivalent.
- [ ] Examine ablations for learned aggregation versus averaging, adapters/projections, number of views, anchor selection, and other relevant components. Record metrics, input conditions, and limits of the comparisons.
- [ ] Separate missing observations, uncertain cameras, incorrect masks, texture disagreement, shape disagreement, and changed articulation. These can fail for different reasons.
- [ ] Look for direct tests of AI-generated multi-view inputs, inconsistent anatomy or proportions, moving accessories, and conflicting object counts. Record when no such evaluation is found.
- [ ] Determine whether a different pose is supported, requires a separate alignment method, or violates the method's static-geometry assumption.
- [ ] Identify cases where more views worsen a result and whether the released system exposes confidence, reliability, or user-controlled view exclusion.
- [ ] Explain whether uncertainty is measurable from the released outputs or would require additional development. Do not equate attention or aggregation weights with calibrated confidence without evidence.

**Evidence:** Training configuration and implementation, paper and supplements, author results, and directly relevant issue reproductions.

**Output / completion:** A tolerance table with one row per error type, evidence level, tested severity if known, expected consequence, and open question for our later experiment. Clearly identify the limit between modest observation error and contradictory object definitions.

### R05 — Cameras, coordinate systems, and input preparation

**Question:** How can our separate images be placed into the common geometry that the released workflow expects?

- [ ] Document the exact input schema and example files: images, masks, intrinsics, extrinsics, object localization, coordinate conventions, units, and identifiers.
- [ ] Trace camera-to-world versus world-to-camera transforms, handedness, axes, origin, anchor-aligned canonicalization, bounding-box scale, and image/camera ordering.
- [ ] Establish support for perspective and orthographic cameras, field-of-view definitions and units, principal point, and camera distance. Do not assume a view label supplies these values.
- [ ] Specify how crop, padding, resizing, rotation, and alpha handling must update image coordinates, camera intrinsics, masks, and bookkeeping together.
- [ ] Determine how inconsistent framing, projected object scale, off-center subjects, and different aspect ratios affect reconstruction. Avoid independently resizing each object to an arbitrary bounding box.
- [ ] Investigate the supplied camera/depth estimation route and the actual roles of Depth Anything 3, mask tracking, and coarse localization. Determine which pieces a single isolated object needs.
- [ ] Examine camera estimation with opposite views and little overlap, weak texture, symmetry, transparent/reflective surfaces, and AI-generated contradictions. Explain how camera-estimation errors can masquerade as fusion failure.
- [ ] Distinguish camera estimation from genuine calibration. Establish what can be verified geometrically and which estimates would be guesses.
- [ ] Determine when a known-camera renderer or physical capture could provide a diagnostic control without becoming a substitute for our intended generated-image use.
- [ ] Distinguish a camera moving around a stationary object from a fixed camera filming a rotating object. Establish the required object-relative transforms and background treatment if turntable photographs are considered as a control or an additional input type.
- [ ] Explain any real restrictions on converting perspective and orthographic views. Do not prescribe a general 2D correction that requires unavailable depth or geometry.

**Evidence:** Official example schemas and preprocessing code, wrapper scene/view/estimate nodes, camera-estimator documentation, and precise failure reports.

**Output / completion:** An input contract with a worked, non-executed example and camera-convention table. Provide supported preparation options for calibrated renders, real photographs, and AI-generated references. Mark any missing reliable bridge as a feasibility issue rather than filling it with nominal angles.

### R06 — Masks, background removal, object detail, and view selection

**Question:** What constitutes a usable observation for this workflow, and how much preparation would Brian or another user have to perform?

- [ ] Establish mask type, resolution, polarity, alpha behavior, edge treatment, holes, and how masks influence projected evidence and coarse object bounds.
- [ ] Identify existing suitable background-removal or masking nodes, their licenses and resource needs, and whether manual mask correction is useful. A whole-room tracking stack must be justified for a single object.
- [ ] Check treatment of thin structures, internal openings, translucent parts, cast shadows, partly occluded geometry, and an object cut off by the image border.
- [ ] Investigate supported view counts, view spacing, overlap, elevations, and anchor choice. Determine whether a small reference set can meet the method's requirements.
- [ ] Examine evidence across hard-surface props, vehicles, building-like assets, people, creatures, and organic shapes. Separate model capability from our inference about a category.
- [ ] Determine whether view-selection guidance exists and how users could exclude a known bad observation without destroying camera associations.
- [ ] Clarify whether text descriptions enter reconstruction at all. If text only influences image creation, the proposed workflow must state that honestly.

**Evidence:** Preprocessing implementation, author recommendations, representative examples, and relevant category-specific failure evidence.

**Output / completion:** A practical input-quality checklist and a small view-selection recommendation with its evidence. Identify unavoidable manual work and distinguish it from optional cleanup.

### R07 — Supplied Comfy workflow and complete artifact inventory

**Question:** What is already wired in the provided single-object graph, what files does it require, and what must actually change for our use?

- [ ] Read `worldsculpt_instance.json` as the primary graph. Map every node, connection, input, intermediate result, and output to its implementing code and required package.
- [ ] Verify both stage-specific LoRAs, both trained aggregators, and all required conditioning projections are used on the executed path. Identify loader defaults that can leave an adapter unused.
- [ ] Check the base-model format, compatible checkpoint revision, LoRA patch targets, scaling, and decoder/encoder compatibility. Verify the reported BF16 versus INT8 restriction.
- [ ] Distinguish core Comfy nodes, custom WorldSculpt nodes, optional estimator nodes, and scene-only nodes. Retain only justified single-object dependencies in the proposal.
- [ ] Compare the wrapper path with official inference for cropping, camera transforms, batching, global conditioning, structure decoding, shape conditioning, and finishing. Record meaningful deviations.
- [ ] Inspect workflow serialization, file selection, model directories, validation errors, and how an ordinary user identifies missing files.
- [ ] Determine how to verify that all learned components are active without guessing from the fact that a mesh was produced: patch-match evidence, resolved file identities, selected node outputs, and absence of averaging fallback.
- [ ] Identify exact existing Mumblebox or native nodes that could be reused later, with no edits during research. If local code ownership needs investigation, follow the repository's existing tool contract.

**Artifact inventory requirements:** For every required or optional file, record publisher, repository/revision, exact filename, file role, stage, size, format/dtype, matching architecture, license, gate/authentication, destination in the approved installation, and why it is needed. Recheck whether an equivalent verified file is already locally owned before proposing a download.

**Supplied artifact leads to verify:**

| Candidate artifact | Reported role | Question to resolve |
| --- | --- | --- |
| `pixal3d_bf16.safetensors` | Reconstruction backbone | Compatible revision, dtype and LoRA application |
| `dino_v3_L_naf_fp32.safetensors` | Image feature extraction/refinement | Exact encoder variant, preprocessing, precision and terms |
| `trellis_2_shape_vae_bf16.safetensors` | Shape decoding | Matching representation and memory needs |
| `ss_ft64_mv_lora_ibr_texverse/ckpts/denoiser_step0015000.pt` | Structure-stage adaptation | Contents, projection weights and target modules |
| `ss_ft64_mv_lora_ibr_texverse/ckpts/mv_aggregator_step0015000.pt` | Structure-stage fusion | Matching dimensions and actual use |
| `shape_ft1024_mv_lora_ibr_texverse_fixedmem05/ckpts/denoiser_step0015000.pt` | Shape-stage adaptation | Contents, matching base and supported resolutions |
| `shape_ft1024_mv_lora_ibr_texverse_fixedmem05/ckpts/mv_aggregator_step0015000.pt` | Shape-stage fusion | Matching configuration and actual use |
| Additional texture, camera, mask, and decoder artifacts | Conditional dependencies | Whether required for the chosen single-object path |

**Output / completion:** One complete graph map, a bill of materials, and a change ledger containing only necessary deviations from the supplied workflow. File sizes or successful loading must not be represented as end-to-end proof.

### R08 — Every relevant setting and its effect

**Question:** Which settings control useful behavior, which must match training, and which are merely implementation details?

- [ ] Inventory settings in workflow widgets, node definitions, official command-line examples, inference configuration, and checkpoint configuration. Include important hidden defaults.
- [ ] Cover view count/order/anchor, camera and box normalization, crop margin, image/feature resolution, mask handling, structure resolution, shape resolution, sampling steps, guidance, seed, adapter scaling, and any aggregation controls actually exposed.
- [ ] Cover decoding, remeshing, simplification, texture/UV resolution, precision, attention backend, batching, offloading, and cache behavior where supported.
- [ ] Trace each setting to code that reads it. Flag exposed-but-unused settings, mismatches between UI and backend defaults, and fixed architectural values that must not be treated as tuning knobs.
- [ ] Record supported values, documented defaults, the authors' explanation, expected memory/runtime effect, and evidence for quality effects. Keep our proposed defaults separate from the authors' recommendations.
- [ ] Determine whether settings interact, such as guidance with training conventions, resolution with checkpoint stages, or camera parameters with crop transforms.
- [ ] Look for supported category-specific settings. Propose them only where there is evidence; do not create many profiles because categories sound useful.

**Output / completion:** A settings dictionary containing: name; plain-English purpose; stage/node/config owner; accepted values; official default; wrapper default; recommended initial value and reason; dependency on other settings; resource impact; evidence; and whether it should be exposed in the later ordinary-node graph. Unknown quality effects must be labeled unknown.

### R09 — Installation and Windows/Comfy compatibility

**Question:** What exact installation would reproduce the supplied workflow in the existing Comfy Desktop without disrupting Mumblebox?

- [ ] Identify required Comfy backend/frontend versions and native Pixal3D/TRELLIS.2 interfaces. Compare the pinned wrapper imports and node contracts with the installed source during later authorized read-only research.
- [ ] Establish Python, PyTorch, CUDA, driver, package, compiled extension, and operating-system requirements. Separate supported Windows installation from Linux-only evidence.
- [ ] Examine installation and first-use code for implicit downloads, dependency changes, authentication, build tools, and optional components that become mandatory on a particular branch.
- [ ] Locate official installation commands, model locations, file naming rules, import troubleshooting, and known conflicts. Verify their meaning before including them in the proposal; do not execute them during research.
- [ ] Identify existing locally owned compatible assets through narrow read-only checks, without loading models or reaching into other applications' stores.
- [ ] Specify version pinning, safe trusted artifact loading, resumable downloads, file integrity checks where available, and actionable handling of gated access. Do not retrieve or print credentials in the report.
- [ ] Determine whether installation requires restarting Comfy and what visible recovery would be needed. A later implementation should preserve saved workflows and use the existing Desktop instance.
- [ ] Provide a reversible installation recipe: target directory, exact package/files to add, limited environment changes, compatibility checks, and how to remove only the added components if needed.

**Output / completion:** A source-backed, unexecuted installation recipe and compatibility table. Clearly distinguish a supported recipe from a recipe that still needs a local installation test. No unverified command should be presented as already successful.

### R10 — Hardware, unloading, runtime, and failure recovery

**Question:** Can the complete single-object route plausibly run on this system, and what must later execution measure?

- [ ] Find exact hardware reports for single-object inference, including checkpoint format, view count, resolution, texture path, offload strategy, software revision, elapsed time, and peak VRAM/RAM.
- [ ] Treat undocumented claims that it runs on 16 GB as unverified. Neither a small adapter download nor a successful run on a larger GPU establishes fit.
- [ ] Construct a stage-by-stage residency table covering optional image generation, mask/camera estimation, encoding, projection/aggregation, structure sampling, shape sampling, decoding, finishing, texturing, and export.
- [ ] Distinguish model storage size, active parameters, runtime tensors, feature/voxel caches, allocator reserve, temporary copies, and system RAM used by offloading.
- [ ] Inspect whether applying LoRAs duplicates base weights and whether native Comfy model management recognizes every large component. Identify caches or graph references that keep memory alive between stages.
- [ ] Determine which views can be encoded in batches and which features must coexist during fusion. Do not serialize joint operations in a way that removes the method's coordination.
- [ ] Specify when models can be unloaded and when reuse is useful. Avoid unloading after every image merely for ceremony; release models at actual stage boundaries and when headroom requires it.
- [ ] Assess supported resolution/view-count/offloading options and any BF16, FP32, or quantization constraints. Identify a supported initial configuration rather than promising an arbitrary low-memory mode.
- [ ] Identify Windows-specific compiler, attention, dtype, device, and GPU finishing issues. Reuse established compatible optimizations; do not turn this into a new kernel project.
- [ ] Define what later measurements must capture: per-stage time and memory peaks, unexpected CPU fallback, cancellation behavior, resource release, and whether repeated runs accumulate memory.
- [ ] Distinguish slow documented work from a stall using observable progress and resource behavior. Plan a specific cancellation/recovery route rather than requiring a reboot as normal operation.

**Output / completion:** A hardware evidence table and a proposed stage residency schedule with confidence labels. If no exact 16 GB proof exists, deliver a plausible supported configuration and the precise local test still required, or explain why no credible configuration was found.

### R11 — GPU finishing, textures, and a useful exported asset

**Question:** What happens after detailed shape generation, and does the complete path deliver the mesh Brian actually needs?

- [ ] Identify the mesh representation produced by decoding and the exact conversion, remeshing, decimation, cleanup, UV, baking, and export steps used by the supplied graph.
- [ ] Trace which finishing operations run on GPU and which run on CPU. Examine supported GPU finishing options already available locally, including the existing project's chosen methods where relevant.
- [ ] Determine whether any proposed finishing change alters geometry materially, requires a different decoder, or creates a costly preprocessing stage. Do not equate switching a label with GPU execution.
- [ ] Establish a geometry-only export route and the optional textured route. Determine whether a trained WorldSculpt texture adaptation exists or texturing uses the base model.
- [ ] Investigate preservation of thin parts, openings, surface detail, separate connected components, winding, normals, and expected topology limitations after simplification.
- [ ] Document supported export formats, material/UV handling, orientation, scale, metadata, and import into Blender. Distinguish an editable starting mesh from a rigged/game-ready or watertight printable asset.
- [ ] Determine how a neutral material and independent viewpoints can expose geometry defects hidden by texture or attractive renders.

**Output / completion:** A complete finishing-to-export path with the device and dependencies for every expensive operation. Identify any unsupported GPU step or remaining mesh-quality limitation explicitly.

### R12 — Licensing, distribution, and local operation

**Question:** What can Brian use locally, what can Mumblebox redistribute, and what must users obtain themselves?

- [ ] Verify licenses separately for official code, LoRAs, aggregators, conditioning projections, Pixal3D code and weights, DINOv3, NAF, decoders, background removal, optional estimators, and custom nodes.
- [ ] Check the community wrapper's actual license at the pinned revision. An official link to a wrapper does not itself grant a redistribution license.
- [ ] Distinguish operation of the models, redistribution of code/weights, distribution of a workflow that downloads weights, and use of generated outputs.
- [ ] Identify attribution, notice, gated access, acceptance, commercial conditions, and any geographic or use restrictions actually present. Link the governing terms rather than inventing a general commercial-use guarantee.
- [ ] Establish whether the chosen path works locally after obtaining dependencies, and whether any auxiliary component requires a hosted service or transmits input images.
- [ ] If a term is ambiguous, record the exact ambiguity and its effect on a private experiment versus a public integration. Do not silently substitute a different encoder or assume a rewrite removes model-license obligations.

**Output / completion:** A component-by-component license and access matrix with a plain-English recommendation for experimentation and later integration. Any unresolved distribution condition remains a named condition, not a hidden assumption.

### R13 — Minimal adaptation, possible training gaps, and Mumblebox fit

**Question:** How much would be needed beyond the supplied graph to serve our actual inputs?

- [ ] Map the proposed data contract to Mumblebox's reference images, image-editing outputs, mask tools, storage, resource handling, and mesh exports through read-only inspection when research is authorized.
- [ ] Classify every required change as existing configuration, existing node connection, small input adapter, wrapper defect repair, substantial model change, or new training.
- [ ] For a necessary custom input adapter, identify its precise input/output and owning layer. Avoid rebuilding existing camera, mask, projection, and aggregation code.
- [ ] Check whether generated references can enter through a supported preparation route without room segmentation or scene-mesh merging. Scene-shaped metadata may be an internal format; it must not change the user task.
- [ ] Explain which camera/mask/preparation work the user would perform, which can be automated reliably, and which remains uncertain. The method's usefulness includes preparation effort, not only the final render.
- [ ] If custom training is genuinely necessary, identify exactly what would be trained, the demonstrated prerequisite, available training code, data/camera/mask labels, losses, hardware, licenses, and evaluation needed.
- [ ] Inspect the supplied training configuration enough to explain how the adapters were made and whether training is reproducible. Do not imply inference fitting 16 GB establishes training feasibility.
- [ ] Estimate training expense only from concrete resource and duration evidence; give assumptions and ranges, or state that a defensible estimate is unavailable. Do not assume weekend training or a small rental budget is sufficient.
- [ ] Classify future integration as a direct optional mesh route, an experimental-only route, or unsuitable for our inputs. Keep GUI, Pinokio, and unrelated features out of the proposal.

**Output / completion:** A minimal change ledger and an honest effort/feasibility assessment. Custom training, if raised, is a separately proposed project and must not silently replace the released-method investigation.

### R14 — Bounded future validation and synthesis

**Question:** What limited experiment could decide whether this is useful, while revealing technical failure rather than hiding it?

- [ ] Define the exact hypothesis, input set, camera provenance, masks, settings, required loaded components, comparison routes, metrics, and export inspection before proposing execution.
- [ ] Include a correct-camera control to distinguish a broken integration from unsuitable generated inputs. A successful control is diagnostic evidence, not completion of the user objective.
- [ ] Include imperfect generated references and explicit desired rear/side details. Investigate geometry in neutral renders and exported mesh data, not texture-only improvement.
- [ ] Preserve the same source material and anchor across comparisons. Record seeds, revisions, framing, masks, cameras, resolution, and finishing so that improvements have an interpretable cause.
- [ ] Avoid a combinatorial sweep of models, view counts, settings, or image seeds. Use the small evaluation envelope in section 7, or justify a revised bound before requesting implementation approval.
- [ ] Specify success, conditional success, rejection, technical failure, and inconclusive outcomes separately. A workflow that queues successfully is not proven useful.
- [ ] Produce one concrete implementation proposal based on the supplied single-object graph. Include exact required deviations, unresolved runtime checks, and a clear point to stop for review.

**Output / completion:** A decision-ready research report and independent-workflow proposal. The report must either support a credible implementation or identify the exact feasibility limit; it must not present an unrun experiment as a working solution.

## 6. Order of investigation and scope controls

This is the proposed order for a later authorized research pass, not work being started by this document:

1. **Establish the reference implementation:** R01, R02, and an initial R07 graph map. Reuse earlier evidence and identify the authoritative single-object path.
2. **Understand the mechanism and its assumptions:** R03–R06. Resolve what the input cameras, masks, static geometry, anchor, and aggregation actually mean before judging usefulness.
3. **Make the path concrete:** complete R07, then R08–R12 for settings, artifacts, installation, memory, finishing, and licensing. Check these against the same pinned graph and versions.
4. **Decide what adaptation is necessary:** R13, followed by R14's bounded experiment and final proposal. Present the results for discussion before implementation.

Work inline without subagents unless Brian separately authorizes delegation. Batch independent document reads when useful, but keep conclusions tied to the chosen implementation.

For each unresolved question, inspect the controlling official source and the relevant implementation first. Then perform a focused search of author answers and credible reproductions. If evidence remains absent, record what is unknown and which later test would answer it. Do not repeatedly search for a convenient positive answer.

Adjacent projects are in scope only when they provide a dependency or resolve a precise gap in this WorldSculpt route. No broad survey of every mesh model, image generator, control adapter, or NVIDIA technology is needed.

Narration during future research should state the overall question, the consequential evidence, how it changes the proposed workflow, and what remains unresolved. A useful update is: "The supplied graph contains both learned fusion stages; the remaining input issue is how our generated pictures get reliable cameras." Avoid reporting minor file reads as progress toward a proven result.

## 7. Proposed future test envelope — design only

No tests, image generation, rendering, model loading, workflow execution, or installation are authorized by this plan. The research report should confirm or revise this envelope for Brian's approval based on the evidence it finds.

### 7.1 Inputs and comparisons

Prefer existing reusable inputs and exports where their provenance and settings are known. Use a small number of views appropriate to the released method; do not assume a particular number is optimal before the research.

The initial proposed envelope is at most **eight planned reconstruction attempts**, plus **two narrowly justified repair/retry attempts**. Any expansion requires a new explicit decision. Optional cases are omitted when they do not answer a remaining question; unused budget is not a reason to generate more assets.

| Case | Purpose | Proposed path |
| --- | --- | --- |
| V1 | Establish that the complete released method works with valid inputs | One object with correct known cameras and masks through full WorldSculpt |
| V2 | Check the relevant documented observation-error tolerance | Same control with one documented, bounded camera or mask perturbation |
| V3 | Establish the practical starting result for a hard-surface subject | Single best image through the existing Pixal3D route |
| V4 | Answer the main user question on that subject | Same anchor plus a few intended generated views through full WorldSculpt |
| V5 | Attribute any gain to the learned method where comparison is valid | Same V4 inputs/cameras through the matching supported ordinary multiview baseline |
| V6 | Establish a second, different subject's starting result | Single best image of an organic or character-like subject through existing Pixal3D |
| V7 | Check whether the approach is useful beyond one hard-surface example | Same V6 anchor plus a few generated views through full WorldSculpt, with fixed pose |
| V8, optional | Resolve the most consequential remaining view-trust question | One predeclared observation change, exclusion, or repeat, justified before execution |

The research must not manufacture an unsupported baseline or silently bypass required trained components just to fill V5. If the comparison is not technically valid, omit it and explain the attribution limit. Reuse a baseline result only when its provenance is adequate.

Before later execution, choose expected details and a simple evaluation rubric. Assess silhouette/proportions, intended rear/side geometry, duplicated or misplaced features, holes/collapse, thin structures, and editable exported output. Use a neutral material as well as textured inspection. Inspect geometric detail from more than the original reference angle.

Report both results and costs: preparation effort, requested versus accepted input views, camera reliability, stage timings, peak VRAM/RAM, finishing device, cleanup needs, and export validity. A prettier texture must not compensate for worse geometry in the scoring.

### 7.2 Success, rejection, and stopping

**Technical path success:** the selected single-object workflow uses the verified matching adapters and aggregators, consumes the intended references with valid associations, completes on the target machine, uses the accepted GPU finishing route, releases resources appropriately, and exports an inspectable mesh. This alone establishes operation, not superiority.

**Evidence of practical improvement:** on the agreed generated-input examples, extra references provide intended geometry or better proportions than the single-image starting result without severe new contradictions. The reference preparation and runtime must be practical. State which asset types and error conditions the evidence covers; do not generalize a tiny trial to arbitrary objects.

**Conditional usefulness:** the route works for calibrated renders or coherent photographs but not for generated views, works on only one subject, or requires substantial manual camera correction. Report that narrower scope explicitly and let Brian decide whether it is valuable.

**Method rejection for our target:** the complete correctly wired method repeatedly deforms the generated-input examples, fails to preserve deliberate additional geometry, or requires input accuracy/preparation that our intended workflow cannot supply. A calibration-only success cannot be used to relabel the target experiment successful.

**Technical limit or inconclusive outcome:** an unavailable component, incompatible implementation, unresolved camera setup, or unsupported memory requirement prevents evaluating the hypothesis. Identify the exact stopping stage and whether there is a credible repair. Do not call an installation failure proof that learned fusion cannot work.

**Resource stopping rule:** abort a later test at the predetermined resource or stall threshold if it threatens system responsiveness, exhausts available memory, or enters an unacceptable CPU finishing path. The research report must propose observable thresholds from the relevant hardware evidence; it must not invent performance guarantees now.

**Overall stopping rule:** after the approved cases and permitted focused retries, show the actual exports, provenance, and results, then stop for review. No unbounded prompt rerolls, unannounced image regeneration, expanded subject suite, or extra parameter search to obtain a favorable showcase.

## 8. Required deliverables from the later research pass

Create a comprehensive report in plain English, with technical appendices that let a later implementer act without rediscovering the research. Keep related evidence in one place rather than duplicating it across many handoffs.

The report should contain:

1. A concise decision: proceed with a defined independent workflow, proceed conditionally, or do not implement yet because of a named feasibility limit.
2. A source-backed explanation of the method, each adapter/aggregator/projection, and the boundary between demonstrated robustness and our generated-view hypothesis.
3. The official-guidance/skill search result and recommended image-source finding, including a clear "none found" when appropriate.
4. The pinned version table and complete required/optional component inventory.
5. The camera/mask/crop/scale input contract, including what happens with unknown cameras and inconsistent views.
6. A node-by-node annotated copy or diagram of the supplied single-object workflow, with only necessary proposed modifications clearly marked.
7. The complete settings dictionary and proposed initial settings with evidence and uncertainty.
8. An unexecuted installation recipe for the existing Comfy Desktop, with compatible versions, exact file destinations, access requirements, and rollback boundaries.
9. The 16 GB / 64 GB feasibility assessment, stage unloading schedule, GPU finishing route, and remaining runtime measurements.
10. A component-specific license/access table and implications for local experimentation and later distribution.
11. A minimal implementation change ledger, explanation of anything custom, and whether additional training is actually justified.
12. The finalized bounded evaluation table, expected outputs, success/rejection/technical-limit criteria, and stopping point.
13. Important discoveries, rejected assumptions or approaches with reasons, and remaining uncertainties mapped to a focused source check or later validation case.
14. A short next-step proposal for Brian's approval. Research completion must not automatically initiate implementation.

Proposed future report location: `docs/research/2026-10-23-worldsculpt-single-object/REPORT.md`. Adjust the execution-date prefix if research happens later. Store downloaded documentation snippets or metadata only when useful, with source provenance; do not download model tensors during a research-only authorization.

## 9. Completion conditions

### This planning goal

Mark the current goal complete only when:

- The plan is saved in the authorized E: project and can be opened by Brian.
- It covers the agreed single-object scope, supplied-workflow starting point, mechanism, official skills/guidance, upstream image-engine recommendations, components, settings, installation, input preparation, hardware, GPU finishing, licensing, integration boundaries, and future validation.
- Every research package has an answerable question, evidence route, and explicit output or honest-gap condition.
- Planning, research, and implementation permissions are clearly separate.
- The document has been checked for contradictory instructions, missing accepted requirements, invented findings, and implied permission to begin research.
- Brian receives the plan location and confirmation that research has not been started under this goal.

Then stop for review. Do not install, browse the project sources, download models, run generation, change Comfy, or resume the parked integration work.

### A later research goal, if authorized

That separate goal can be complete when the deliverables in section 8 are produced and the evidence supports either a concrete implementation proposal or a specific feasibility limit with a clearly described narrower usable path, if one exists. Every important unresolved claim must be labeled and mapped to the decision it affects. A runtime-unverified proposal may be a completed research result, but it must never be called a working workflow.

## 10. Requirement coverage and planning review

| Accepted requirement | Plan location |
| --- | --- |
| Several pictures of the same object to one mesh | Sections 1–3; R03–R07; R14 |
| Start from the supplied single-object workflow and its adapter wiring | Section 2; R07; R14 |
| Completely separate ordinary-node workflow; no GUI | Section 2; R09; R13 |
| Explain what every adapter is made of and what it does | R03; R04; R07 |
| Investigate official skill, docs, papers, supplements, settings | R01; R03; R04; R08 |
| Determine any preferred image-creation engine and camera support | R02; R05 |
| Verify learned weighting versus discarding bad views | R03; R04; V8 |
| Distinguish occlusion/error tolerance from conflicting AI geometry | R04; R05; R14; section 7 |
| Background removal, masks, camera mismatch, crop and scale lessons | R05; R06 |
| Complete released artifact and installation requirements | R07; R09 |
| 16 GB VRAM / 64 GB RAM, unloading, practical Windows operation | R09; R10 |
| GPU finishing and actual useful export | R11; section 7 |
| Commercial/distribution/access conditions and local privacy | R12 |
| Mumblebox fit without changing its GUI or inventing another task | Section 2; R13 |
| Explain training without promising affordable/easy custom training | R04; R13 |
| Bounded checks, honest outcomes, and a clear stopping point | R14; sections 7–9 |
| Create plan only and wait for Brian | Sections 1; 9 |

Planning review record, 2026-10-23: checked against the accepted decisions and Brian's additions about recommended image engines and supplied workflow wiring. Confirmed all 14 research packages, explicit outputs, the coverage matrix, the separate authorization boundaries, and the bounded future evaluation. A local document check verified section coverage and unchecked research tasks. No WorldSculpt sources were fetched, models installed or loaded, workflows run, or application controls changed for this planning goal. Research checkboxes remain unchecked.

## 11. Local document location and workspace provenance

- Authorized project directory: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI\custom_nodes\comfyui_asset_workshop`
- Plan: `docs\superpowers\plans\2026-10-23-worldsculpt-single-object-research-plan.md`
- Containing Git top-level: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI`
- Git/common directory: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI\.git`
- Observed parent HEAD during planning: detached at `483dae4326356b81de05d27aca3f433dd323cc25`.
- The parent checkout already contained an unrelated untracked `custom_nodes/comfyui-mcp/` entry. This planning task does not alter it.
- This document is a local planning artifact. No branch, repository, worktree, installed package, model file, application state, or workflow is changed by its creation. No commit or push is part of the planning deliverable.


