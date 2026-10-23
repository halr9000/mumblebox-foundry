# Mumblebox SDXL / MV-Adapter deep research plan

**Date:** 2026-10-22

**Status: PLAN ONLY. Research has not been executed under this plan.** Brian requested a thorough research plan, followed by a stop. This document authorizes no implementation, installation, generation, training, paid compute, app restart or integration. A short search before Brian's plan-only correction returned possible leads; those are discovery leads, not completed findings from this plan.

**Planning method:** Superpowers brainstorming and writing-plans principles: preserve the accepted brief, divide work into checkable questions, name evidence and decision criteria, review coverage, and define the stopping point. This is a research plan rather than a product implementation plan. Generic implementation, commit, worktree and subagent steps do not apply to this request. Do the eventual research in the current lane unless Brian separately authorizes delegation.

## 1. What Brian wants answered

Can a mature SDXL model, combined with an adapter actually trained for coordinated views, produce better inputs for a useful first mesh than the failed proxy-depth approach? Are there released workflows we can reuse? Can a compatible Juggernaut checkpoint and style LoRAs make this a capable route in its own right? Is another reconstruction engine materially better suited to those images?

The intended experience remains: create or upload an image, produce usable views, inspect/correct the selection, build a mesh, and export it. The goal is a useful game/print asset starting point with little friction. Human review is allowed. Perfect recovery of invisible surfaces is not assumed.

Brian has now allowed SDXL as a serious candidate. Its maturity is an advantage to evaluate, not an automatic quality pass. Qwen or another supported image model may still create the initial design; the multiview generator can be a specialist internal stage. Keeping all previously discussed image families is not required.

**Runtime hypothesis:** approved image plus optional description -> jointly conditioned views -> background/mask and camera preparation -> ONE mesh reconstruction -> geometry review -> optional textures and GPU finishing -> export.

The discarded route is draft mesh -> generated guide pictures -> another reconstruction. Do not reintroduce it through an optional stage, a renamed proxy, or a workflow borrowed for a different purpose. A single-image baseline generated for a controlled comparison is an independent control, not a runtime feedback pass.

The new leads **Preferred Networks / T3lescope**, described by Brian as arbitrary-resolution, high-fidelity generative surface reconstruction from images, and **Gaussian wrapping** are part of this plan. Their exact names, scope, availability and relationship to the task must be verified during research. Their capabilities are not established by this document.

## 2. Boundaries and project ownership

- Target Windows, Brian's 16 GB GPU and 64 GB system RAM. Smaller-card support is future work; ordinary SDXL memory requirements do not establish multiview memory requirements.
- Work in the established E: installation and research tree. No development, caches or generated artifacts in OneDrive; no borrowing models or outputs from other applications.
- Preserve original Mumblebox, its history, masks, user settings and workflows. Preserve the completed independent experiment and its full masters. Abandon its failed route as the next direction, not its evidence or useful repairs.
- No GUI redesign, Pinokio application, integrations, theme system, training wizard or unrelated model survey.
- No model-weight downloads, dependency installation, executable examples, GPU work, Blender rendering or cloud jobs during research execution unless Brian separately expands that authorization. Reading source/workflow JSON and saving attributed research evidence is research; running it is an experiment.
- Keep everything local and free by default. Reading a hosted example does not authorize using a hosted generation service. Price estimates do not authorize spending.
- No license acceptance, credential handling, account changes, vendor outreach or messages to workflow authors.
- Record blockers to a candidate honestly. A negative recommendation is a valid research result. Do not silently adopt excluded or incompatible components to make a candidate look viable.

**Canonical application root:** `E:/Comfyui-installs/ComfyUI (1)/ComfyUI`

**Existing extension:** `custom_nodes/comfyui_asset_workshop`

**Completed experiment:** `custom_nodes/mumblebox_camera_experiment`

**Research outputs after authorization:** `custom_nodes/comfyui_asset_workshop/docs/research/2026-10-22-sdxl-mvadapter/`

The shell currently operates in the E: checkout, whose top-level and Git common directory were resolved. The checkout is detached; existing native fixes and unrelated `comfyui-mcp/` are preserved. This planning task creates only this Markdown file. No branch, worktree, commit or push is required.

## 3. Lessons that constrain the new research

Use `custom_nodes/mumblebox_camera_experiment/RESULTS.md` as the current outcome, and older research as context. Reuse its evidence without relaunching its experiment.

| Observed lesson | Consequence for this investigation |
|---|---|
| True, consistent views with correct cameras improved all six simple controlled fixtures | Investigate a stronger source of multiview evidence; do not conclude that one image is always sufficient. |
| Klein RefControl depth plus estimated cameras failed the improvement gate | Do not revive that exact route or generalize its failure to all adapters. |
| Generated pictures can look good while changing parts or proportions | Score cross-view design preservation and downstream geometry separately from visual appeal. |
| DA3 Small/Base produced substantial pose errors | An angle estimate is not calibration; do not make DA3 a mandatory repair for every new route. |
| Crop, pad and camera conventions can corrupt reconstruction | Trace complete image-to-camera transformations before judging a model. |
| The tested QEM reduction damaged otherwise intact surfaces | Evaluate full geometry first. Preserve the master and use only proven finishing paths; pretty/damaged derivatives cannot establish reconstruction quality. |
| BF16 conversions and saved-state device placement caused real defects | Preserve owning repairs and test the actual installed precision/device path before attributing defects to model quality. |
| Staging and releasing live tensors avoided excessive memory use | Analyze custom-loader ownership as well as Comfy's managed models. Cache retention and CPU copies matter. |
| A median surface-distance score could favor a visibly holed mesh | Require essential-feature and topology review alongside geometry metrics. |
| Technical reruns expanded the previous run substantially | Separate defects from quality failures, cap both explicitly, and keep a visible count. |
| Synthetic simple fixtures do not prove production anatomy or ship quality | Include asymmetric spaceship parts, thin features and a meaningful character/organic case in future validation. |
| Reopened GLB and UV validity did not establish game or print readiness | Report asset-use boundaries, cleanup work and print diagnostics explicitly. |

The recorded five-of-six usefulness result concerns simple editable bases. Do not rewrite it as proof of high-fidelity arbitrary-image reconstruction. Failed guide trials superseded by technical repairs remain superseded.

## 4. Hypotheses and alternatives

### H1 — Coordinated views can improve the first mesh

MV-Adapter's learned cross-view/reference connections may produce more compatible evidence than independent image editing did. Research must identify the actual released image-conditioned variant, its training assumptions and its reconstruction use. A grid assembled by prompting is not equivalent to learned cross-view coordination.

### H2 — A strong SDXL derivative may help without losing consistency

An appropriate Juggernaut SDXL checkpoint may improve fidelity/style, but a model that makes attractive single pictures can still interact poorly with the adapter. Compare a documented baseline before claiming the derivative is better.

### H3 — Camera compatibility may decide the outcome

Even consistent pictures can be poor inputs to a reconstruction model that assumes different projection, pose, normalization or view order. Research must settle the orthographic/perspective bridge or identify a better matched reconstruction route. Do not force convenient labels onto incompatible evidence.

### H4 — Reconstruction-side improvements may be more useful than additional image work

T3lescope, Gaussian wrapping and other directly relevant released approaches may address first-surface quality. Assess them as reconstruction candidates, without assuming they require or justify another image/mesh feedback pass.

### H5 — A useful SDXL route can become a reference for future training

If the existing mechanism proves valuable, an equivalent for a newer backbone may be worth developing. Reusing an architecture, fine-tuning existing weights and training a port are different projects. No automatic custom-training commitment follows from finding training code.

**Acceptable research recommendations:** proceed with a specific bounded SDXL route; proceed only with a named reconstruction substitution; request one narrowly defined compatibility probe before choosing; or reject the route with concrete reasons. Supporting evidence, not the desired conclusion, determines the recommendation.

## 5. Research method and evidence rules

1. Read the existing reports and actual local owners needed for the selected question. Do not restart the prior broad image-model survey.
2. Start with original papers, author repositories, model cards, released example graphs and source code. Trace important claims to the owning implementation and exact variant.
3. Use author issue discussions, firsthand reproduction logs, community workflow JSON and original tutorial artifacts to identify operational problems. Distinguish author demonstration, user report and locally verified behavior.
4. Search recent activity and tutorials, prioritizing **2026-09-22 through 2026-10-22** for new workflows, fixes and compatibility changes. Older official model releases remain necessary evidence; a last-month filter must not exclude them.
5. YouTube transcripts are allowed. Record transcript versus graph versus visual inspection; do not claim to have watched a video from a transcript. Trace useful recipes to downloadable graphs and source. Popularity and thumbnails do not establish quality.
6. Inspect the JSON connections, not only screenshots. Verify that an alleged image-to-mesh workflow uses the images in reconstruction rather than only repainting an existing mesh.
7. Record commit/revision, URL, retrieval date, exact file/section, component version, evidence type and applicability to our machine. Preserve brief attributed excerpts or source snapshots where needed; avoid copying entire publications.
8. Mark each answer **documented**, **source-confirmed**, **author-reported**, **community-reported**, **locally demonstrated previously**, **inference**, **unknown**, or **requires runtime validation**. Local source inspection is not a runtime pass.
9. When a lead fails, inspect the owning source, make one focused follow-up, then record the limitation or use the named fallback. Do not keep searching broadly without a decision it could change.
10. Keep one question register and one final recommendation. Update a fact once in its canonical table rather than duplicating conclusions across handoffs and plans.

## 6. Research work packages

Each package below is future research, not a task to execute while writing this plan. Complete its evidence and decision output before advancing. A runtime-only unknown is an answer category; it must receive a small proposed test rather than an invented factual conclusion.

### R00 — Establish the comparison and retire misleading assumptions

**Questions**

- Which previous failures came from input/software defects, and which survived their correction?
- Which native graph, image preparation, camera bridge, saved-state, resource and finishing pieces can be reused unchanged?
- What is already built versus merely researched? Which original Mumblebox features remain preserved but outside the experiment?
- Are we seeking a useful editable base, a finished static game asset, a deformable character or a printable object? What proof differs between those outcomes?

**Actions and output**

- [ ] Reconcile the accepted decisions against the final experiment report, not historical progress notes.
- [ ] Produce a short **keep / retire / candidate / unknown** table, with evidence links.
- [ ] Record the new one-reconstruction rule and the reference baseline protocol.

**Stop:** a single current-truth table is sufficient. No retesting the old route or rediscovering its complete history.

### R01 — Audit MV-Adapter's actual capabilities and releases

**Questions**

- What do the camera encoder, cross-view attention and image-reference connections do? Which weights are trained, frozen or copied from the base?
- How do text-to-view, image-to-view, geometry-conditioned, texture-only, fixed-view and beta view-selection releases differ?
- Which variants actually generate several views jointly? Is batch order semantically significant? What does selecting fewer views change?
- What is the documented default camera set, elevation, distance, projection and canonical object orientation for each relevant release?
- Which source-image pose/framing range was represented during training? Can an arbitrary three-quarter upload be used without pretending it is a front orthographic photograph?
- Does the image-conditioned route accept one reference or several? Does a node silently take only the first? What happens to alpha, text, masks and resolution?
- Which claims concern generated pictures, and which include actual reconstruction evaluation? What failure cases do the paper and issues report?

**Inspect:** author paper and appendix; released weight cards; pipeline, condition-encoder and attention code; training configuration; camera embedding and preprocessing utilities; example graphs.

**Output:** a variant matrix, a plain-English mechanism explanation, and one exact documented baseline recipe. Include unsupported combinations explicitly.

**Stop:** select the smallest image-to-multiview baseline that addresses the task. Geometry-dependent/texturing releases do not become mandatory dependencies.

### R02 — Find and dissect existing reusable workflows

**Questions**

- Is there a released, locally runnable uploaded-image -> MV-Adapter -> mesh graph? Which reconstruction engine does it use?
- Can we reuse a complete matched pipeline or only its view-generation section?
- Are examples current with the author nodes? Are they real JSON graphs, screenshots, gated downloads, hosted-only demos or descriptions?
- Do they apply background removal, consistent framing, correct view ordering and appropriate camera conditioning?
- Do they require an initial mesh, use multiple pictures only for textures, or run a second reconstruction? Those do not meet the new core route.
- Are there recent working fixes for Windows, Diffusers, model loading, VAE precision or memory ownership?
- Is there firsthand evidence of cleaner game meshes, including unsuccessful examples, rather than only attractive turntables?

**Search targets:** author Comfy workflow directory; source-linked community workflows; relevant original ComfyUI-3D-Pack examples; author/user reproducibility issues; recent GitHub, YouTube and forum leads. Use community aggregators only to locate primary artifacts.

**Actions and output**

- [ ] Shortlist at most five materially different candidates; inspect the strongest three in depth.
- [ ] For each, map actual inputs -> conditioning -> generated outputs -> reconstruction -> finishing.
- [ ] Record graph URL/hash, node owners/versions, weight list, camera assumptions, hardware evidence, terms, defects and reuse cost.
- [ ] Recommend a primary reusable graph and at most one fallback, or state that no end-to-end match was found.

**Stop:** enough inspected source exists to specify a reproducible experiment or identify the exact missing bridge. Do not collect dozens of near-identical workflows.

### R03 — Choose a baseline and investigate Juggernaut compatibility

**Questions**

- Which official SDXL model and adapter recipe form the reproducible control?
- Which exact Juggernaut release is SDXL-based, available from its actual publisher, and suitable for isolated objects rather than photographic scenes?
- Is the relevant support demonstrated for **image-to-multiview**, not merely text-to-multiview?
- Does the graph use Diffusers directories, a single checkpoint, an extracted UNet or baked VAE/text encoders? Are conversion/loading paths supported?
- Do scheduler, prediction type, distilled/Lightning variants, VAE scaling and precision match the adapter's assumptions?
- Do community derivatives preserve image-reference response and cross-view agreement? Could added visual detail undermine geometric agreement?
- Is there a documented reason to choose a different SDXL derivative for anime or stylized assets? Do not expand to many checkpoints without evidence.

**Output:** an exact component bill for the baseline and one preferred Juggernaut SDXL candidate, plus a compatibility checklist and a reasoned selection. A familiar model name alone is insufficient.

**Stop:** one baseline and one derivative in the core comparison. One named replacement is permitted only if the preferred derivative has a specific disqualifying incompatibility; record that choice before testing.

### R04 — Camera, projection and image-frame contract

This is a **P0 gate**. It cannot be deferred to “the mesh model will compensate.”

**Questions**

- What matrices and ray embeddings condition each MV-Adapter output? What physical/canonical cameras do those encode?
- Which outputs are orthographic? How are orthographic extent, object normalization and camera distance defined?
- Does the existing Pixal3D multiview model and its feature projector support that projection, or only perspective intrinsics? Inspect the model/conditioning implementation and training assumptions.
- Can a mathematically justified, finite perspective approximation preserve the relevant pixel projections? If so, what measured error and depth-range bounds would be required? Do not silently substitute a large focal length.
- How do axes, handedness, camera-to-world/world-to-camera, row/column ordering, image Y direction, front convention and mesh coordinates map?
- How are camera records updated after background removal, cropping, resizing and padding? Which operations change scale/center independently across images?
- How do we distinguish **conditioning camera**, **requested angle**, **observed pose estimate** and **verified geometric agreement**? A trained camera input still does not guarantee perfect generated geometry.
- Can a non-generative fitting/checking method expose wrong poses or incompatible proportions without requiring the discarded rough-mesh feedback route?
- What ambiguities arise with symmetric objects, textureless sides, little overlap, articulation or invented hidden details? How are inconclusive cases treated?

**Output:** coordinate/projection diagram, explicit mapping table, image-transform record schema and a proposed deterministic test using landmarks on asymmetric known geometry. Identify an exact-camera control and a deliberately wrong-order/incorrect-crop negative control.

**Decision:** either document a justified Pixal bridge, recommend an already matched reconstruction method, or mark the combination unsuitable until a bounded bridge probe passes. Do not compensate for a projection mismatch by adding prompts, CFG or more views.

### R05 — Reconstruction engine selection, including new named leads

**Questions common to candidates**

- Does it reconstruct a polygon surface, a neural field, a point cloud or Gaussian splats? Which output actually becomes an editable GLB/OBJ/STL?
- Does it accept one image, multiple images, camera records, normal/depth maps or another representation? Are multiview images genuinely fused?
- Is it a complete released inference path with available weights, or a paper/demo/announced release?
- Does it support the selected generated-view camera set and projection? Would swapping engines discard most of the extra evidence?
- What is the representation's actual resolution/detail limit, and where does inference cost scale? “Arbitrary resolution” must not be interpreted as unlimited detail or memory independence.
- What happens to thin parts, cavities, sharp edges, planes, disconnected components and symmetry? Are geometric improvements measured, not only shaded appearance?
- Can it run staged on Windows with 16 GB VRAM/64 GB RAM? Identify peak/startup versus steady-state claims, precision and compiled dependencies.
- What are the exact weight/code/dependency terms and commercialization/release conditions?

**Primary reference:** Pixal3D multiview remains the comparison engine if its input contract is valid. Its single-image baseline remains a control, not the sole proposed product direction.

**Named lead A: Preferred Networks / T3lescope**

- [ ] Verify spelling, publisher/authors, paper title/version and authoritative project URL for Brian's description, “arbitrary-resolution, high-fidelity generative surface reconstruction from images.”
- [ ] Determine whether it improves first reconstruction directly, predicts/refines surfaces from another representation, or requires an initial mesh.
- [ ] Audit released code, weights, training dependence, exact inputs, camera assumptions, normals/material outputs, memory/time measurements, Windows support and Comfy integration.
- [ ] Compare claimed sharp/thin-feature quality to Pixal on actual source evidence; record whether comparisons use matching inputs and resources.
- [ ] Decide whether it is an immediate candidate, a bounded compatibility probe, or a watchlist item with the exact missing prerequisite.

**Named lead B: Gaussian wrapping**

- [ ] Identify the exact named method or likely intended term using primary sources. Do not silently replace it with Gaussian splatting or assume a particular paper.
- [ ] Separate Gaussian-based reconstruction, wrapping/surface extraction, splat rendering and mesh texturing.
- [ ] Determine whether a usable surface is obtained directly or through an additional extraction/optimization stage; inspect holes, normals, thin features, texture baking and export requirements.
- [ ] Establish image/camera inputs, released implementation/weights, dependencies, license and measured local hardware plausibility.
- [ ] Classify its role: reconstruction alternative, mesh conversion, finishing, or irrelevant to the first-mesh problem. If it depends on prohibited feedback, explain that and exclude it from the core route.

**Matched alternatives:** inspect a reconstruction method used by the author or a verified workflow only if it resolves an identified camera/representation mismatch. Do not begin a general survey of every 3D model.

**Output:** one primary reconstruction choice, one fallback at most, exact bridges and an evidence-based disposition for both named leads. A method may be promising without being ready to install.

### R06 — Input preparation, design preservation and useful view selection

**Questions**

- What source angle, object occupancy, background, lighting and alpha does the selected adapter expect? Which documented preprocessing operations are essential?
- Can the workflow begin with an uploaded image, text-created image, image plus description, or a prepared design from another model? Preserve the true role of each input.
- How do we avoid changing design facts when SDXL reinterprets a Qwen-generated source?
- Which prompts/negative prompts/reference-strength settings are specific to the image-conditioned release? Do not borrow text-only CFG, generic seed advice or another adapter's trigger.
- Are all requested body parts/features present? Are backs and sides distinct? How are occluded/unseen features labeled as proposed rather than observed?
- Can BiRefNet reuse existing valid alpha? Does removal retain holes, handles, hair and thin appendages? Are masks and RGB saved separately with source identity?
- Does the author-trained six-view set make sense for first tests? Which four-view or subset weights actually exist? Are top/bottom/elevated outputs supported by the selected image-to-view weights?
- Can a user exclude a bad view without breaking the trained sampler or reconstruction? Distinguish selecting output views jointly from deleting an image after generation.
- If a single view is regenerated independently, can it remain compatible with the set? Identify safe batch-regeneration/local-edit behavior without promising it before proof.

**Output:** a documented input-to-view recipe, per-view review checklist and supported camera/view-count table. No mandate to make ten images. No elevation or underside promises based solely on another model variant.

### R07 — Style LoRAs, anime models and mature SDXL ecosystem

**Questions**

- Where in the actual graph are style weights applied relative to the multiview/reference adapter? Which layers can they alter?
- Are one or several style LoRAs supported in the **image-conditioned** route? What reference/style-strength controls are documented?
- Is style expected to come from the input image, base checkpoint, prompt or LoRA? Could competing sources repaint features differently across views?
- What distinguishes a broadly compatible SDXL LoRA from one that assumes a heavily modified derivative? How would the program avoid presenting mere architecture compatibility as a quality pass?
- Which documented anime/stylized base examples are relevant, and do they preserve silhouettes/parts?
- What is a useful limited validation for a consistent series/house style? Does stylization preserve front/back distinctions, symbols, colors and mechanical features?
- What metadata, base-model tag, hash and license information would later be needed to load a user's style safely and reproducibly?

**Output:** supported combination matrix and one optional style comparison after the core route passes. Keep the future “style LoRA creator” as a feasibility note; do not design/build its UI, browse thousands of LoRAs or train one in this phase.

### R08 — Installed-stack, Windows and resource feasibility

**Questions**

- Which author node pack/workflow requires the fewest changes to the established installation? What versions of Comfy, Python, PyTorch/CUDA, Diffusers, Transformers and compiled libraries does it expect?
- Does its loader cooperate with Comfy's model management, or retain an independent pipeline and live GPU tensors? What explicit cleanup is necessary?
- Does “unload models” actually release custom adapter, condition encoder, VAE, text encoder, reference-feature caches and worker state? Can CPU references keep memory alive?
- What memory is required at startup, six-view attention, reference encoding, sampling and VAE decoding? Is the cited memory for inference or training, and for which variant/resolution?
- Which documented optimizations preserve semantics: VAE slicing/tiling, cached encodings, attention implementation, CPU offload, precision? Can naive view chunking break the very cross-view mechanism we are testing?
- What would a conservative 16 GB profile reserve for Desktop/other GPU use? Use actual bytes and distinguish GiB/GB and dedicated/shared memory.
- What whole-system RAM and pagefile behavior would indicate excessive offload or leakage? Preserve headroom and compare repeated runs, not just one successful completion.
- Which caches can be bounded/reused, and which outputs must persist? The previous experiment retained roughly 179 GB of native checkpoints; do not turn every case into an automatic giant-state dump.
- How do success, cancellation, failure and process recovery release resources? Do not restart someone else's app or use a reboot as routine memory management.
- Can textures/UV/baking stay in a later stage, with a real geometry-only route? Does finishing use the required GPU path for heavy operations?

**Output:** source-backed dependency/resource bill, potential version conflicts, minimal isolation/rollback recommendation, stage load/offload diagram, disk/cache budget proposal and a short runtime proof checklist. Do not install or benchmark during research.

**Planning target for future approval:** maintain approximately 1.5 GiB GPU reserve and at least 8 GiB available system RAM where practical; these are proposed safety margins, not already verified settings. A candidate that exceeds them needs an explicit revised profile or rejection, not silent CPU finishing.

### R09 — Mesh finishing, game use and print boundaries

**Questions**

- Which artifacts originate in source reconstruction versus derivative processing? Can comparison occur before any destructive reduction?
- Which proven BF16/saved-state fixes and native GPU resampling/PEC steps remain applicable without modification?
- How much do resampling, smoothing and reduction change actual geometry versus shading? Check holes, thin parts, poles and nonmanifold edges rather than a triangle count alone.
- Are texture sampling, UV generation and baking tied to a particular shape latent? If a different reconstruction engine is chosen, which textures can be reused and which require a different bridge?
- What will exported assets contain: units, orientation, pivots, materials, textures, UVs and optional geometry-only files? Which proof requires reopening the saved file rather than inspecting a cached preview?
- What remains for game use: sensible topology/triangle and material budgets, collision, attachment surfaces, LODs and animation topology where applicable?
- What remains for print use: scale, wall thickness, connectedness, intended openings, self-intersection and watertightness? No universal automatic “fill holes” treatment.
- Could total cleanup work exceed direct Blender construction for a mechanical part? How should a later comparison measure that without guessing token savings?

**Output:** export and usefulness checklist, known limitations, and an optional later AI-plus-cleanup versus Blender-first benchmark specification for one representative spaceship part. This research does not run that benchmark or claim token savings.

### R10 — Licensing, distribution and portability

**Questions**

- What terms apply separately to author code, adapter weights, base SDXL, exact Juggernaut release, style LoRA, encoder/VAE, remover, reconstruction weights, renderer and training assets?
- What can the free application redistribute, download on demand or merely reference? What conditions affect commercial game assets or prints?
- Are there model-operation conditions distinct from rights in generated outputs? Is a license label inherited incorrectly by a wrapper or derivative?
- Are gating/authentication and first-use downloads avoidable or user-initiated? Where would models/cache reside on another Windows installation?
- Are any workflows coupled to paid endpoints, hidden tokens, someone's private folders or hard-coded drives? What must be parameterized for a portable future implementation?
- Are exact versions, hashes and environment constraints sufficient for others to reproduce results without downloading models from another application?

**Output:** graph-specific license/dependency bill with direct terms links and factual plain-English labels; portable path/download design requirements. Missing or unclear terms remain marked unresolved. Do not accept terms or promise blanket clearance.

### R11 — Practical custom training and Blender-generated data

This package answers Brian's training ideas without turning the core research into a training project.

**Three distinct efforts**

1. Use or fine-tune an existing SDXL multiview adapter.
2. Train an ordinary style LoRA for the proven SDXL route.
3. Implement/train a compatible multiview/reference mechanism for a newer backbone such as Klein or Qwen.

Do not quote the easiest task's memory/cost as if it proved the hardest one feasible.

**Questions**

- Which complete trainers/configurations exist, and what exact layers, camera encoder and reference/cross-view modules do they train? What changes for a transformer-based backbone?
- What can be reused as data format, evaluation or architecture? Which weights are incompatible and require training again?
- Does the existing trained route prove enough value to justify a port? What narrow measurable gap would additional training address?
- How do existing dataset licenses apply to individual underlying objects? What owned/procedural alternative avoids that uncertainty?
- How can Blender generate many matched examples automatically: object identity, source/target images, camera matrices, masks, scale and optional depth/normals? Do not rely only on angle captions.
- Start with boxes/primitive combinations for calibration and pipeline checks; include varied asymmetric geometry, holes, thin parts and distinct front/back features for meaningful learning. How much shape and appearance diversity is needed for the proposed pilot?
- How are texture, lighting and camera randomized independently so that an angle does not become associated with one color or category?
- How do we separate camera movement from character articulation? A skeleton/pose map is not object-camera calibration.
- How are whole objects and near-duplicate families held out? Different angles of one object must not leak across training/test splits.
- Which target camera sets, resolution and reference count match intended inference? Training arbitrary view synthesis and training a fixed six-view set are different tasks.
- Does an exact trainer expose checkpointing, cached encodings, frozen base weights, supported quantization and offload? What activation memory remains despite small adapter files?
- What minimum local forward/backward and short-learning pilot would establish actual memory, speed and held-out progress? A low training loss on memorized objects is not sufficient.
- What would renting a 48/80 GB or larger GPU buy, given measured steps/second and required iterations? Original multi-A100 training is context, not a universal minimum or a known elapsed-time quote.
- Can costs be bounded with a timeout and checkpoint recovery? Include data preparation, storage, failed attempts and evaluation; separate a $25–$50 pilot budget from any promise of a working adapter.

**Output:** optional training feasibility brief with architecture/data requirements, a $0-first local pilot proposal, explicit unknowns, and conditional rental estimates. No paid job, dataset archive, rendered training images, trainer installation or training run is authorized by this research plan.

### R12 — Compare routes and synthesize a decision

- [ ] Compare complete usable stacks, not isolated model names or showcase pictures.
- [ ] Recommend one primary first-mesh route and one fallback at most; explain why each part is needed.
- [ ] Identify exactly what already exists, what can be reused unchanged, what must be connected, and what genuinely requires new code or training.
- [ ] State whether the SDXL baseline, Juggernaut derivative, style support, T3lescope and Gaussian wrapping are ready, conditional, rejected, or future-only, with reasons.
- [ ] Rank remaining uncertainty by its ability to change the decision. Give every important unknown a finite follow-up, expected evidence and stop rule.
- [ ] Explain the complete proposed image-to-export sequence in plain English, then supply technical detail separately.
- [ ] Produce a bounded runtime experiment proposal. Do not execute it or implement Mumblebox automatically.

## 7. Source leads to validate during research

These are starting points, not research findings or a guarantee that each artifact remains available/compatible. Verify revision and the actual matching file during execution.

| Lead | Why inspect it |
|---|---|
| `https://github.com/huanngzh/MV-Adapter` | Author paper, release matrix, pipelines, cameras, training and limitations. |
| `https://github.com/huanngzh/ComfyUI-MVAdapter` | Actual nodes and downloadable image-conditioned workflow graphs. |
| `workflows/i2mv_sdxl_diffusers.json` and `workflows/i2mv_sdxl_ldm.json` in that repository | Baseline image-to-view routes and supported checkpoint loading. |
| `workflows/i2mv_sdxl_ldm_lora.json` | Actual image-conditioned LoRA combination rather than inference from text-only support. |
| `workflows/i2mv_sdxl_ldm_view_selector.json` | Subset camera behavior and its separate beta weight requirement. |
| `https://arxiv.org/abs/2412.03632` | Training/evaluation details, view/camera assumptions and backbone limitations. |
| `https://huggingface.co/huanngzh/mv-adapter` | Exact released weights, filenames, terms and revision. |
| `https://github.com/MrForExample/ComfyUI-3D-Pack` | Inspect relevant example graphs carefully; geometry-conditioned/texturing paths may fail the no-draft requirement. |
| Actual Juggernaut publisher/release, verified during research | Avoid choosing a different architecture or an unverified mirror by name alone. |
| Preferred Networks / T3lescope | Verify exact identity and primary project/paper before evaluating. |
| Gaussian wrapping | Resolve exact method, then inspect actual surface/conversion implementation. |
| Existing local mesh-first/applied-synthesis reports | Reuse prior primary-source pointers and unresolved questions only when relevant to this route. |

## 8. Proposed later runtime validation — NOT authorized now

Research must refine and justify this proposal, identify the exact artifacts, and present it for approval. Source inspection cannot complete these rows.

### Stage V0 — Validate the image/camera/reconstruction contract

- Reuse owned known geometry where suitable, including an asymmetric prop with a hole/thin part, a spaceship/mechanical component, and a character/organic subject with distinct rear features.
- Preserve one source view per object and a declared ground-truth view set. Use source angles within the documented image-conditioned range.
- Prove coordinate/projection and crop mapping with known landmark renders to approximately one-pixel tolerance. Include wrong view order, mirrored convention and independent crop negative controls.
- If orthographic MV-Adapter output cannot be consumed with a defensible bridge, stop this engine combination before expensive image trials. Consider only the named matched fallback.

### Stage V1 — Documented baseline, then one derivative

- Run the author's exact image-conditioned baseline on the first subject and inspect all intended outputs before scaling.
- After technical integration passes, compare baseline SDXL and the one chosen Juggernaut derivative on the same three source objects and declared camera set.
- Use one predeclared seed per object, with paired controls where meaningful. Shared seeds provide reproducibility, not a guarantee of identity.
- Start with the release's trained default view set; do not invent camera/elevation changes to make it resemble the previous workflow.
- Keep all generated outputs and their rejection reasons. No VLM-only approval, cherry-picked seed sweep or silent mirrored-view substitution.

### Stage V2 — Compare geometry, then a held-out case

- Reconstruct only coherent accepted sets. Preserve exact image frames and record camera provenance.
- Compare each candidate to the same source's single-image baseline and, for known geometry, the true-view control. Reuse existing controls only if inputs/preprocessing/preset match.
- Evaluate full masters before reduction/textures. Use geometry distance plus silhouettes, proportions and essential-feature checks. Use one shared similarity alignment, never independent per-axis stretching to hide errors.
- Use a fourth held-out fresh design for the winning route. It has no ground-truth accuracy percentage unless a true reference mesh exists.
- If the baseline works and the derivative fails, keep the baseline. If both fail the quality gate, stop and report that result.

### Stage V3 — One style compatibility check and exports

- Only after the core route passes, optionally apply one compatible existing style LoRA on one primary object. Compare preservation and cross-view agreement to its no-style control.
- Finish up to two representative chosen meshes using the proven GPU route; keep masters. Reopen actual saved files in existing Desktop and inspect geometry, UVs and textures.
- Prove a geometry-only output bypasses texturing/UV work; report print diagnostics separately.
- Record success, controlled cancellation and a focused failure cleanup. Do not deliberately exhaust RAM to prove recovery.

### Suggested hard limits for the future experiment

| Item | Proposed cap and interpretation |
|---|---|
| Core checkpoint choices | Author baseline plus one Juggernaut SDXL candidate. |
| Primary subjects | Three known-truth, varied objects, including a spaceship-relevant component and organic/character case. |
| Held-out fresh case | One. |
| Core generated views | Six batches of six across the three paired subjects, plus one held-out batch: 42 images if the selected release uses six views. |
| Optional style test | One batch of six after a core pass: total 48 images. |
| Logical reconstructions | Up to 15: three single controls, three true-view controls, six generated-view comparisons, held-out single/MV pair, one optional style comparison. Reuse valid saved controls where possible. |
| Technical reruns | At most two focused reruns, each one image batch or reconstruction. At most 12 additional generated images and two additional reconstructions. Record the defect before using an exception. |
| Absolute totals | 60 generated views and 17 logical reconstructions including those exceptions; no quality sweeps. A recipe with a different trained view count needs a revised budget before running. |
| Texture/export comparisons | At most two chosen geometries; no image or shape regeneration merely to test export. |

These are maximums, not a requirement to spend the budget. A failed prerequisite stops downstream work. Technical exception limits prevent a repeat of an open-ended invalidation/replay loop; exceeding them requires a new decision from Brian.

### Proposed success and rejection criteria

Research should justify final thresholds rather than pretend the following proposal is already approved or measured:

- Camera/frame tests pass, with the relevant projection supported or a validated bridge.
- At least two of the three controlled objects improve normalized median geometry error by at least 10% over their source-image baselines, with no increase in catastrophic essential-feature failures; report all three individually and the paired aggregate.
- The organic/character result remains a recognizable useful base. Simple primitive success alone cannot certify complex character quality.
- The held-out design preserves essential parts/proportions across usable views and yields a useful mesh. No ground-truth percentage is invented.
- The Juggernaut/style options earn support only if they retain consistency and do not materially degrade geometry. A more attractive picture is insufficient.
- Heavy stages complete on the chosen 16 GB / 64 GB profile; resources release after success/cancel/failure; no silent heavy CPU finishing or reliance on shared-memory spill.
- Saved geometry and textured exports reopen; tested finishing does not introduce the previous surface damage. Game/print readiness limitations remain explicit.

Reject or narrow the route for recurring wrong-side features, duplicated/lost parts, projection incompatibility, unusable camera assumptions, no geometry benefit, unacceptable memory/runtime, absent release artifacts or incompatible terms. The cause may remain uncertain; uncertainty is not permission for endless tuning.

## 9. Research deliverables and acceptance

Create these only when research execution is authorized:

1. **`REPORT.md`:** plain-English answer first, followed by an in-depth account of R00–R12. Explain the proposed path, actual existing components, new work, alternatives, failures, uncertainty and recommendation. Distinguish evidence from inference throughout.
2. **`SOURCE-REGISTER.md`:** primary source/version/claim ledger and provenance. Keep source artifacts under a bounded `sources/` directory if needed; no model-weight caches in research evidence.
3. **`WORKFLOW-INVENTORY.md`:** at most five shortlisted candidates, strongest three examined, graph lineage and exact reuse assessment. Show whether each is no-draft image-to-mesh, image-to-views only, texture-only, or another excluded route.
4. **`QUESTION-AND-DECISION-REGISTER.md`:** every research package and named lead, answer status, evidence, decision and remaining runtime question. This is the single coverage/decision authority for the new research.
5. **`VALIDATION-PROPOSAL.md`:** exact proposed primary/fallback graph components, resource plan, fixtures, controls, caps and go/no-go criteria. It remains a proposal, not runnable authorization or a claim of completion.
6. **`FOLLOW-UP.md`:** only unresolved issues that could change a decision. Give each the smallest source check or runtime probe, priority, dependencies and stop rule. Keep optional custom training, newer-model ports and Blender cost comparisons clearly conditional.

The report must explicitly answer:

- Is there an existing workflow we should reuse? Which exact artifact, and what does it actually do?
- Why is the selected method meaningfully different from the failed route?
- Is Juggernaut genuinely compatible and preferable, merely plausible, or unsuitable?
- What does a style LoRA add, and what combination is actually supported?
- Which views, cameras and input preparation are justified?
- Is Pixal3D the right reconstruction engine for those outputs?
- What did the T3lescope and Gaussian-wrapping investigations establish?
- What fits Brian's hardware on source evidence, and what still needs measurement?
- What can be shipped or downloaded under the exact stack's terms?
- What can be reused now, what needs engineering, and what would need training?
- What would justify a local training pilot, Blender-generated data, or eventual rental?
- What is the finite next experiment and when must it stop?
- Does the likely total correction effort support Mumblebox's intended use, and what remains unknown about Blender-first cost?

## 10. Anti-drift, narration and source-search stopping rules

- Present progress in terms of decisions: what question was answered, what evidence supports it, what remains unresolved and how it affects the route. Explain hypotheses and connections; do not narrate only filenames or tool calls.
- Give a useful update at least every 60 seconds during active work. Number research packages in progress so Brian can place the detail in the whole project.
- Do not repeatedly read settled reports or restart planning. Reopen an accepted decision only for a concrete conflicting finding.
- Do not turn source availability into installed proof, image generation into mesh-quality proof, or a saved model into a usable game asset.
- Search recent sources to resolve a specific gap. After the owner source and two focused discovery passes yield no decisive answer, mark it unknown and specify the bounded runtime check. This does not forbid deeper reading of a directly relevant promising implementation.
- No broad model-family expansion, speculative helper stacks, GUI work or training execution. New promising ideas get a disposition in the research register, not automatic implementation.
- Keep camera fitting, surface refinement and alternate reconstruction roles explicit. Do not smuggle the abandoned second-mesh feedback route back into the design.

## 11. Clear completion and stop statements

### Completion of THIS planning task

This task is complete when this single research plan is saved, self-reviewed for coverage of Brian's current instructions and additions, and linked for review. Then say **“DING FRIES ARE DONE!”** and stop. Do not browse further, execute R00–R12, create an implementation goal or alter the apps.

### Completion of the FUTURE research phase

After separate authorization, research is complete when R00–R12 and both named new leads have an evidence-backed disposition; the source/workflow inventory and exact-stack comparison are recorded; the primary/fallback recommendation or no-go conclusion is explained; licensing/hardware uncertainties are explicit; and every remaining consequential unknown has a finite follow-up with a stop rule. The report and validation proposal must be understandable without reading the chat.

Research completion does not require all candidates to work, every uncertainty to disappear, a GPU test, a paid training run, or an implemented product. Stop for Brian to discuss and approve the next experiment. Do not execute the proposed workflow automatically.

## 12. Planning self-review

- [x] Research-only boundary and stop preserved; no new implementation goal requested.
- [x] Prior failed route retired; useful repairs, original Mumblebox and evidence preserved.
- [x] Uploaded-image starting point, optional description, one reconstruction and GPU finishing retained.
- [x] Actual jointly conditioned views distinguished from ordinary camera LoRAs and prompt grids.
- [x] Existing workflows, recent tutorials, exact source/JSON audit and reproducibility covered.
- [x] SDXL baseline, one Juggernaut candidate, anime/style compatibility and mature ecosystem covered without a checkpoint sweep.
- [x] Orthographic/perspective mismatch, coordinate/crop contracts, source pose and unverified generated cameras made P0 questions.
- [x] Preferred Networks / T3lescope and Gaussian wrapping explicitly included without inventing their capabilities.
- [x] 16 GB VRAM / 64 GB RAM, custom-loader cleanup, startup peaks, precision, disk growth and cancellation covered.
- [x] Full-master geometry, essential features, texture/export proof and game/print boundaries covered.
- [x] Blender-generated paired data, training feasibility, newer-model ports and bounded paid-compute questions covered conditionally.
- [x] AI-plus-cleanup versus Blender-first value and token-cost uncertainty retained.
- [x] Future runtime caps separated from research authorization, with no unbounded technical exceptions.
- [x] Deliverables, unknown-handling, measurable proposed gates, negative-result handling and stopping points stated.
