# Mumblebox: mesh components and Pixal3D application research plan

**Date:** 20 October 2026. **Status:** Research complete; product implementation and empirical comparisons remain unperformed.

**Results:** [Completed report](MESH-COMPONENT-RESEARCH-REPORT.md), [46-component inventory](mesh-components.json), and [source register](mesh-sources.json). R01–R11 are answered with source evidence or a specifically bounded unknown. Checked boxes below mean the research question was addressed, not that a proposed future experiment ran.

**Goal:** Determine which mesh-model components and Pixal3D implementation lessons can improve first-pass fidelity, consistent camera guides, resource use and dependable textured exports in the existing Mumblebox Comfy workflow.

**Completion condition:** Every task below has a sourced answer or a precisely bounded unknown after its specified sources have been checked. The completed report contains the component and compatibility inventory, Pixal3D pipeline trace, license review, memory analysis, category/settings conclusions, prioritized recommendations and proposed validation matrix. Sources and exact versions are recorded; documented behavior, local observations and hypotheses are distinguished. Review coverage, citations and internal consistency, deliver the report, then mark the goal complete and say **DING FRIES ARE DONE!** A plan alone, attractive previews, or an unfinished export does not satisfy this condition.

## 1. Agreed scope and working boundaries

Research Pixal3D and the exact TRELLIS generations relevant to our workflow. Treat original TRELLIS, TRELLIS.2 and Pixal3D as distinct systems even where they share ideas or components. Examine the official Pixal3D repository, its installed Pinokio distribution and the native Comfy implementation separately.

The accepted image-model families remain Qwen Image 2.1 with optional AnyAngle, Qwen Edit 2511, FLUX.2 Klein 4B, FLUX.2 Klein 9B and FLUX 3. Preserve variant-specific contracts and the licensing choices in [the current decision supplement](MODEL-SUPPORT-AND-MESH-GUIDANCE.md). This research does not expand or remove support. Consult Hunyuan or another implementation only to answer a concrete shared problem; do not turn this into a survey of unrelated apps.

The intended outputs are useful game assets and printable models, with a high-detail master preserved separately from derivatives. Neither successful GLB export nor a closed-looking preview establishes game-ready topology, animation suitability or printability.

Research execution permits documentation searches, small source/example downloads, read-only inspection of existing code and saved evidence, and writing research artifacts. It does not permit model/node installation, new inference or benchmarks, app restarts, settings changes, workflow rewiring, cache deletion, credential changes, product code changes or Pinokio development. Pixal3D has been stopped with Brian's approval; preserve its saved generation state. Any later empirical tests are proposals until separately authorized.

Work in the existing project, never the legacy OneDrive workspace. Use one research lane; no subagents without Brian's approval. Do not create a second app instance or substitute a browser for a requested desktop app.

## 2. Existing evidence and source locations

- Existing research: [main report](REPORT.md), [current decisions](MODEL-SUPPORT-AND-MESH-GUIDANCE.md), `evidence.json` and `sources.json` in this folder, plus [the image-model guidance report](../2026-10-20-model-guidance/REPORT.md).
- Comfy extension: `E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop`.
- Containing checkout: `E:/Comfyui-installs/ComfyUI (1)/ComfyUI`, common Git directory `.git`; recorded HEAD `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`. Preserve unrelated state.
- Pixal3D launcher: `D:/pinokio/api/Pixal3D-Pinokio.git`; recorded HEAD `2129f16e817dc8f06c8577dcad63581e34d29a5a`.
- Nested Pixal3D source: `D:/pinokio/api/Pixal3D-Pinokio.git/app`; recorded HEAD `f7cf38429b0bd264f1995f0f8743a88b1c728b94`. Local repairs exist; a commit identifier alone does not describe installed behavior.
- Known owning files: `app.py`, `index.html`, `pixal3d/pipelines/`, `pixal3d/utils/render_utils.py`, installed `o_voxel/postprocess.py`, installed `cumesh/bvh.py` and `cumesh/remeshing.py`. Use these as starting points, then follow actual imports and configurations.

Recorded observations to investigate, not universal conclusions:

1. The installed app builds a textured 3D representation before rendering eight 1024-pixel views. Its renderer rotates one object with consistent camera parameters. This is not eight independently generated reference images.
2. GLB extraction is a separate operation using saved shape/texture state. It remeshes before final simplification, then unwraps UVs and bakes material attributes.
3. The last observed decimation target was 1M. It does not cap earlier geometry processing. Confirm the actual count semantics in the implementation rather than trusting an ambiguous label or docstring.
4. During the stalled export, the page said Building BVH while the log had reached Cleaning mesh. The progress interceptor updates the displayed stage on progress increments, not every description change. An unchanged page label did not locate the exact native operation.
5. Before stopping, GPU memory was nearly full and the Pixal3D process had about 41 GiB resident RAM. CPU time and GPU utilization were still increasing; these observations do not establish useful progress, an out-of-memory exception, or the cause of the stall. No final GLB was verified.
6. The process ended when stopped; GPU usage fell to 902 MiB and the saved state file remained present. Do not restart it for this research.

## 3. Evidence method and efficient tool use

Use official papers, supplementary material, source, model cards, configuration files, releases and maintainers' explanations first. Pin repository revisions and exact weight/variant identities. Use examples and issues to discover limitations, then trace technical claims to their owning implementation.

Search recent YouTube workflows within the preceding 30 days, recording the search cutoff and publication dates. Use transcripts and linked workflow files, not titles or polished demos as proof. Older primary documentation remains valid when it is authoritative for the pinned release. Community posts are leads and experience reports; label them accordingly.

Apply the research skill's source discipline. Use ordinary source analysis for complete Python/JavaScript repositories. The reverse-engineer-anything skill explicitly recommends this; use its package/runtime tools only if a specific unanswered question depends on shipped artifacts or behavior absent from source. Do not perform REA setup or an unrelated tool inventory. Use Pinokio guidance for launcher-managed behavior; do not execute its internal Python as a hidden substitute for a running app.

For each conclusion record: question ID, source URL/path, publisher, revision/date, relevant location, observed fact, inference, limitation and consequence for Mumblebox. Label evidence as **official documentation**, **source inspection**, **existing runtime observation**, **community claim**, **proposed experiment** or **unknown**. No claim of local performance or visual quality may be manufactured from source inspection.

Search every relevant official repository/model collection/release/configuration location before concluding that an official adapter was not found. Report where and when searched; do not claim absence everywhere. Do not label a community LoRA official because it works with an official model. Do not treat an encoder, renderer, decoder or accelerator as a LoRA.

## 4. Research tasks

### R01 — Exact model and component inventory

- [x] Identify current selected mesh checkpoints, variants, native node classes and wrapper versions. Distinguish image-to-3D, text-to-3D and text-to-image-to-3D routes.
- [x] Inventory all relevant official offerings: base and single/multiview weights; sparse-structure, shape and material generators; image encoders and feature refinement; autoencoders/decoders; camera estimators; foreground removal; refiners; supported adapters/LoRAs; geometry and texture tools; renderers and runtime libraries.
- [x] Determine which are required and already active, optional and compatible, trained into the architecture, training-only, or unsupported substitutions. Inspect official skills if present; lack of a SKILL.md does not imply lack of guidance.
- [x] Identify direct native Comfy equivalents and genuine gaps. Separate a configuration option from a different checkpoint or a new node.

**Deliver:** one inventory with exact identity, owner/provenance, role, input/output contract, compatibility, current integration, availability, license, resource implications, evidence and apply/test/skip disposition. Explicitly distinguish TRELLIS versions. No assumed plug-and-play VAE/encoder swaps.

### R02 — Foreground and background removal

- [x] Trace the precise remover, weights, mask convention, image crop/padding/resize and alpha handling in Pixal3D, TRELLIS and our current Comfy branches.
- [x] Determine when existing alpha is reused, when segmentation is repeated, and whether a supplied mask can bypass automatic removal. Check premultiplied versus straight alpha, background fill colors and whether compositing changes what the model sees.
- [x] Assess documented limits for fingers, antennae, thin fins, spokes, hair/fur, open holes, disconnected parts, shadows and reflective/transparent materials. Distinguish retaining a silhouette from inferring transparent geometry.
- [x] Inventory official relevant alternatives and compatible existing mask tools. Compare license, local availability, memory, edge behavior and integration burden; do not assume a new remover is automatically better.
- [x] Specify what would let a user inspect/correct a cutout, retain the original, reset the mask and download the result using our existing editing experience. Examine mask consistency across approved views.

**Deliver:** a foreground-preparation recommendation, failure checklist and input contract. Background removal is an explicit workflow element, not an implicit optional extra. Keep object cutout alpha separate from a generated asset's material transparency.

### R03 — Camera estimation and multiview conditioning

- [x] Trace MoGe/FOV estimation, manual override, camera distance, crop-dependent intrinsics and coordinate conventions. Establish whether estimates are per-image, what is assumed and which values enter the model versus only the renderer.
- [x] Verify actual multiview checkpoint requirements, image limits/recommendations, order, image weights if supported, camera metadata, pose assumptions and treatment of inconsistent images. A batch of images is not proof of multiview conditioning.
- [x] Determine which routes accept unposed images or estimate/refine poses, versus requiring supplied transforms. Separate imperfect generated angles from known render-camera metadata.
- [x] Investigate front/back agreement, asymmetric details, consistent scale/framing and source images that are already three-quarter views. Do not call the source camera Front without establishing orientation.
- [x] Compare evidence for one image, an approved front/back pair, a coherent smaller subset and ten reviewed candidates. Treat view count as an evidence question rather than a quality slider.

**Deliver:** camera/input contracts per mesh model, sources for each limit, and a clear strategy for carrying camera metadata through image refinement without pretending the refined image obeyed it exactly.

### R04 — Pixal3D generation pipeline and actual quality mechanisms

- [x] Trace upload through preprocessing, feature extraction, camera handling, structure sampling, shape sampling, cascaded refinement, material sampling and decoding. Explain pixel alignment and feature refinement using the actual paper and code.
- [x] Establish the roles of DINO-family features, NAF and other named modules for the inspected release. Identify learned weights versus ordinary processing code and where independent optional helpers could be inserted legitimately.
- [x] Trace every exposed and hidden sampler setting: steps, guidance, guidance rescale, schedules, seed scope, resolution, token limits and precision. Identify which settings are read and which stages they affect.
- [x] Examine whether direct text influences mesh generation in each route or only an upstream image model. Do not recommend a mesh prompt box without a supported conditioning path.
- [x] Analyze known strengths and failure modes: smooth manufactured panels, sharp edges, anatomy, appendages, small components, underside inference, surfaces with reflections, repeated structures and self-occlusion.

**Deliver:** a plain-English stage diagram plus a source-linked technical trace. Explain quality mechanisms and limits without attributing all improvement to one module or to higher settings.

### R05 — Why previews look good, and what they prove

- [x] Trace the precise representation rendered before export, its material channels, geometry simplification and available render modes.
- [x] Inspect camera rotation, FOV, distance, projection, clipping, frame count and render resolution. Distinguish camera alignment from exact pixel reconstruction.
- [x] Inspect albedo/base color, clay, normals, environment maps, metallic/roughness, shadows, exposure and color management. Identify which apparent detail exists in geometry versus texture or lighting.
- [x] Determine whether color, depth, normal, silhouette and camera metadata can be obtained directly from intermediate geometry without GLB extraction. Identify supported interfaces and any missing native Comfy feature; do not implement it.
- [x] Compare the pre-export preview representation with the exported textured mesh and its viewer settings. Explain where remeshing, UV baking, normals, texture resolution or lighting can change the result.

**Deliver:** preview-to-export fidelity checklist and the cheapest technically supported route for producing accurate camera guides. An attractive preview is not an export-success test.

### R06 — Geometry cleanup, BVH, UVs, materials and export

- [x] Follow saved-state decoding through hole filling, BVH creation, remeshing, simplification, connected-component handling, surface normals, UV charts, material baking, seam filling and GLB writing.
- [x] Establish operation ordering, raw versus final element counts and actual decimation units. Determine whether simplification can safely occur earlier, whether alternative supported export paths exist and their geometry/texture tradeoffs.
- [x] Inspect remesh resolution, band width and projection controls; explain effects on thin parts, intentional openings, sharp surfaces, disconnected components and topology. Keep sampling resolution, render size, texture size and final mesh density distinct.
- [x] Trace BVH and mesh dependencies to exact versions and source. Investigate relevant Windows/CUDA failure reports and any bounded native operations. Do not infer a deadlock merely from a frozen UI or infer progress from GPU utilization.
- [x] Explain texture channels, UV size/density, normal conventions, alpha, embedded versus external images, supported GLB extensions, axes and physical-scale assumptions.
- [x] Assess reuse of saved state for retrying export without resampling and preservation of a high-detail master. Define what still needs a real export/reimport test.

**Deliver:** export call graph, cost/risk points, evidence-backed alternatives and requirements for preserving detail in game and print derivatives. Retopology, rigging, collision and printable wall thickness remain separate needs where the generator does not provide them.

### R07 — Rough-mesh guidance for the accepted image models

- [x] Compare direct Pixal3D output against the proposed loop: approved front/back when supported → intermediate geometry → controlled renders → model-specific image refinement → reviewed mesh inputs → final reconstruction.
- [x] Determine whether a useful guide requires a cheap coarse pass, an existing full-quality intermediate, or no refinement at all. Avoid adding a second generation loop when the first mesh already meets the need.
- [x] Preserve AnyAngle's exact appearance/color-guide contract, Klein 4B/9B RefControl's exact depth/appearance and base-model contracts, Edit 2511's documented route, and FLUX 3's proven capabilities. General image reference support does not establish geometric control.
- [x] Verify depth polarity, normalization, background, camera basis, projection, framing, reference order, model-specific prompts, matching adapter versions and strength. Determine whether direct mesh depth avoids an unnecessary estimator and its license/memory costs.
- [x] Examine how an approved back can preserve hidden details and how contradictory backs or flawed proxy geometry can propagate errors. Keep original/approved references as anchors; do not indiscriminately accumulate generated views.
- [x] Specify when human review should reject a guide or view, when to retry, and how to prevent endless self-reinforcing refinement. Ten views are optional candidates, not mandatory mesh inputs.

**Deliver:** compatibility table and ranked future comparisons, with clear documented support versus proposed combinations. Camera-control LoRAs remain optional and explained; no promise of exact generative angles.

### R08 — Category-based recommendations and understandable controls

- [x] Use the established user-facing categories: Characters, Creatures, Vehicles, Props and Environment Pieces. Map to model terminology internally; do not create categories simply because a model card uses different vocabulary.
- [x] Research whether official guidance or credible comparative evidence justifies different mesh/image settings, components or preservation rules by category. If none exists, retain shared numerical defaults and explain the category-specific review criteria.
- [x] Cover resolution, each sampler's steps/guidance, FOV/camera handling, mask treatment, material/texture resolution, remeshing and simplification. Distinguish rough-guide versus final-master versus game/print derivative settings.
- [x] Require that each proposed setting has its actual effect, units, supported range, default source, time/memory/detail tradeoff and failure symptoms documented. Do not equate maximum settings with best results.
- [x] Carry Brian's requirement that recommendations stay exposed and adjustable, with Reset to recommended settings. Explain automatic hardware defaults and what changes do. Do not redesign the UI during research.

**Deliver:** justified defaults or explicitly unproven candidates, plus plain-English help text requirements. No invented category-specific numbers.

### R09 — Memory, speed, reliability and portable installation

- [x] Map the lifetime of weights, features, latents, raw meshes, render buffers, environment maps, BVHs, UV data and baking buffers across every stage. Separate GPU allocation/reservation, CPU residency, system commit and disk caches.
- [x] Identify reuse, serialization, release and existing native Comfy offloading options. Research whether image and mesh models overlap unnecessarily and whether decoder/export resources outlive their purpose.
- [x] Distinguish offloading and batching from precision, quantization, resolution or algorithm changes that may affect quality. Never quietly reduce fidelity or enable a memory mode.
- [x] Evaluate published and existing observed evidence for the RTX 4080 SUPER 16 GB and 64 GB RAM. The 8 GB VRAM tier needs its own validation; do not derive support from file size or a smaller model's success.
- [x] Trace pinned dependencies, Windows compiler selection, Torch/CUDA/kernel compatibility, first-run compilation versus steady-state cost, and differences among official installation, community wheels and local fixes.
- [x] Examine native progress/cancellation capabilities and honest stage reporting, stale callbacks, export retry and recovery. Propose observable progress even where percentage is unavailable; do not promise immediate cancellation of native GPU work.
- [x] Define cache ownership and invalidation by source image/mask, approved design version, model/adapter/settings and camera data. Preserve user history, source images and masters; cleanup must target owned disposable artifacts only.

**Deliver:** stage resource map, compatibility risks and ranked memory improvements with known quality effects. No benchmark runs or settings changes in this research pass.

### R10 — Licensing and distribution of every relevant component

- [x] Review code, base weights, helper weights, adapters, render assets/environment maps and bundled native libraries separately. Record exact terms and source dates.
- [x] Distinguish local operation, commercial output use, model redistribution, code reuse, attribution, gated access and any commercial agreement requirements. A permissive wrapper or adapter does not override another component's conditions.
- [x] Retain the agreed user-facing labels Commercial use allowed and Commercial use has conditions, with links and the applicable caveat. Identify uncertainty instead of inventing a legal guarantee.
- [x] Assess local model acquisition into the selected Comfy installation, user-supplied Hugging Face authentication, optional gated components and offline operation after setup. Do not inspect or copy credentials.

**Deliver:** per-component license matrix and any restrictions that change a technical recommendation. Free app distribution does not by itself establish permission for every dependency or commercial use.

### R11 — Apply the lessons to our actual Comfy workflow

- [x] Compare native Comfy, our extension, official Pixal3D and the Pinokio distribution at corresponding stages. Identify already-present features before proposing additions.
- [x] Attribute every important behavior to its owner: official model, inherited backbone, renderer/export library, wrapper UI, native Comfy integration or local repair.
- [x] Inventory all relevant official helpers first, then consider narrowly relevant community components separately when official offerings leave a concrete gap. Do not add novelty without a demonstrated problem.
- [x] Produce recommendations as **keep**, **apply using existing support**, **evaluate experimentally**, **do not adopt**, or **unknown**. Each recommendation names the issue, evidence, expected benefit, integration point, dependencies/license, resource cost, risks and smallest later test.
- [x] Prioritize foreground correctness and camera contracts, intermediate renders, dependable export and memory use ahead of additional features. Preserve the existing one-interface experience, history, image editing, review and explicit inclusion choices.

**Deliver:** a small ordered way-forward list, not a product implementation or a promise that all candidate helpers will be added.

## 5. Proposed later validation, not authorized execution

Design a controlled comparison rather than an unbounded matrix of every setting. Use representative existing or later-approved assets: an asymmetric hard-surface prop; a character with hands and a back detail; a creature with thin appendages; a vehicle with openings; and an environment piece with sharp edges. Do not test only crates or beacons. Use known multiview/geometry ground truth where available; inferred unseen surfaces cannot be scored as factual reconstruction without it.

| Comparison | Keep fixed | Question it answers |
| --- | --- | --- |
| Current foreground preparation versus one justified alternative | Source, crop/framing and downstream recipe | Are fine structures and openings preserved without harmful background leakage? |
| Direct single-image baseline versus supported front/back | Model/version and comparable geometry settings | Does the back improve hidden surfaces without contradictions? |
| Raw intermediate renders versus refined guide images | Camera, source identity and chosen backend | Does image refinement improve the final mesh over the already-useful first result? |
| Exact model-specific guide recipes | Matched camera guides and asset requirements | Which supported image route preserves geometry and design most reliably? |
| Coherent small subset versus more reviewed views | Backend and input contracts | Does additional evidence help or introduce inconsistent geometry? |
| Export alternatives and one resource change at a time | Saved shape/material state | Can export finish with less peak memory while preserving useful detail? |
| Master versus game and print derivatives | Same accepted source result | What quality is lost, and which additional checks are required? |

For each later test record seed, exact weights/settings/inputs/cameras, cold or warm run, stage times, peak VRAM/RAM, intermediate and final counts, and failure/retry behavior. A seed does not guarantee cross-version or cross-hardware bitwise identity.

Review silhouette, proportions, persistent side-specific details, anatomy, flat-surface bumpiness, sharp edges, disconnected/fused parts, holes, normals, UV seams and PBR channels. Evaluate geometry under matched neutral/clay lighting so an attractive HDRI cannot hide a regression. Validate exported files by reimport, not just file existence. Print checks include manifoldness, intersections, scale and minimum thickness; game checks include density, materials and intended deformation needs. Establish thresholds per intended use before declaring a winner.

Gate later testing: first prove one complete baseline and correct camera/mask contracts; then compare only the strongest candidate per hypothesis; expand to the varied asset set only when initial behavior is correct. Stop tuning when the agreed quality/cost target is met or remaining limits are identified. Do not chase perfection or silently broaden scope.

## 6. Research outputs, coverage and stopping rule

Create in this existing research folder:

1. `MESH-COMPONENT-RESEARCH-REPORT.md`: the single readable report, stage diagram, app comparison, license/settings/resource tables, recommendations and proposed tests. Include a plain-English summary first.
2. `mesh-components.json`: the searchable component and compatibility inventory, including required/current/optional/training-only/unsupported classification and evidence references.
3. `mesh-sources.json`: source URLs/paths, publishers, revisions/dates, inspected locations, claim IDs and limitations. Reuse earlier source records by reference rather than duplicating large snapshots.
4. Minimal links/status updates in this plan, the main report and the current decision supplement. Do not rewrite settled image-model research unless new evidence directly contradicts a recommendation; document that conflict explicitly.

Before completion:

- [x] R01–R11 each have an answer, relevant source coverage and an explicit conclusion.
- [x] Every proposed component has exact compatibility, provenance and licensing information, or a clearly stated unresolved requirement that prevents recommendation.
- [x] Background removal and mask correction are explicitly covered.
- [x] Pixal3D's preview, generation and export paths are explained separately; the stalled run is not reported as an export success or an established root cause.
- [x] Rough-mesh guidance includes the direct-output baseline, known camera contracts and risks of preserving a flawed proxy.
- [x] Category defaults are evidence-backed or marked unproven, with exposed controls and tradeoffs.
- [x] Memory recommendations address generation, rendering and export, and do not claim an untested 8 GB tier works.
- [x] The five accepted image families and current user decisions remain intact.
- [x] Source/claim links, component records and report recommendations agree; no hypothetical benefit is presented as measured.
- [x] Remaining questions have named evidence gaps and the smallest proposed later test. No unresolved required source check is hidden behind a generic further research item.
- [x] Saved artifacts are readable and linked from the existing research. No product change, app restart, installation, credential action or new generation occurred during research.

The goal ends after this evidence-backed research package is delivered. It does not continue automatically into product implementation or testing. On verified research completion: **DING FRIES ARE DONE!**
