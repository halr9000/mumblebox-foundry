# Mumblebox: mesh components and lessons for the next Comfy iteration

Research completed: 20 October 2026 (America/New_York). Research only. Product implementation and new inference tests were not performed.

This report answers [R01–R11 in the accepted research plan](MESH-COMPONENT-RESEARCH-PLAN.md). Read it alongside [the accepted five-model decisions](MODEL-SUPPORT-AND-MESH-GUIDANCE.md). The searchable [component inventory](mesh-components.json) and [source register](mesh-sources.json) record exact versions, compatibility, provenance and evidence limits.

## What the research establishes

**There is a credible next step: improve foreground preparation and camera contracts, then compare mesh-render-guided images against the mesh we already get directly.** Much of the necessary machinery already exists in native Comfy. The research does not establish that a refinement loop will always beat direct reconstruction.

The strongest findings are:

1. **Background removal belongs in every image-to-mesh route.** Our workflow already uses native removal with original BiRefNet weights. Make the cutout inspectable and correctable, preserve usable input alpha, and avoid changing the framing of images whose camera is already known. The Pixal3D paper explicitly identifies imperfect segmentation edges as a source of geometry artifacts. [S03] [S09] [S10] [S12]
2. **The impressive Pixal3D previews are renders of one generated 3D object.** They are not independently invented views. That explains their consistency and makes intermediate geometry a useful starting point for angle guides. [S20] [S21]
3. **Native Comfy can render color, depth, normals and a silhouette mask from a mesh.** Geometry-only guides can avoid UV unwrapping and a final textured GLB, although rendering still builds a BVH and has a memory cost. Color guides need suitable vertex colors or texture data. [S24]
4. **The image model receives a rendered guide, approved appearance references and model-specific text.** Qwen/Klein/FLUX do not receive the raw mesh through their ordinary image-reference inputs. A render fixes the camera of the guide; it does not prove that the generated image obeys that camera. [S33] [S34] [S37]
5. **MoGe estimates perspective/FOV, not the object's turnaround angle.** It does not certify that an AI-generated view is 45 degrees. Reliable image-to-mesh camera fitting remains an unverified capability for our route. [S17] [S18]
6. **Memory use is not just model weights.** The inspected native Pixal conditioning retains large per-view feature maps. More views can consume substantial system RAM even when processing each image sequentially. Export has a separate peak, and a final triangle target does not cap earlier processing. [S07] [S22] [S28]
7. **There are no official Pixal3D/TRELLIS category, style or angle LoRAs in the checked inventories.** The useful supporting components are mostly built-in encoders, decoders, camera tools, segmentation, rendering and mesh processing. Exact search boundaries are recorded below; this is not a claim that no future or unpublished adapter exists. [S41]
8. **Licensing must follow the entire execution path.** Original BiRefNet and BRIA's BiRefNet-based RMBG-2.0 have different terms. The standalone renderer/export dependencies also include NVIDIA research-use restrictions. Prefer the existing native Comfy path and verify its selected dependency closure, rather than copying the standalone stack wholesale. [S12] [S13] [S38] [S39]

Brian's latest decisions remain controlling: build the next iteration in **Comfy**, keep one understandable experience, preserve the five accepted image families, and defer Pinokio development. Native capabilities are preferred when they solve the actual problem. Background removal is required across mesh routes. Color/depth/normal/silhouette guides are explicit research candidates. The later implementation proposal must be discussed separately.

## 1. Evidence, versions and official inventory — R01

Evidence labels used here:

- **Source:** behavior found in inspected code/configuration; not a successful local execution.
- **Observed earlier:** the stopped Pixal3D session and already-recorded results; not a new test.
- **Author claim:** published by a component/workflow author; not independently measured here.
- **Candidate:** a justified later comparison, not installed or proven behavior.
- **Unknown:** the exact missing evidence is stated.

| System | Inspected identity | Consequence |
| --- | --- | --- |
| Installed Comfy | 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18 | Native node contracts in this report apply to this revision. |
| Mumblebox extension | Existing local custom_nodes/comfyui_asset_workshop; inspected files hashed in source register | Local behavior is established from files, not inferred from the containing Git commit. |
| Pixal3D Pinokio launcher | 2129f16e817dc8f06c8577dcad63581e34d29a5a | Launcher, official app and local repairs are separate owners. |
| Installed Pixal3D / official master | f7cf38429b0bd264f1995f0f8743a88b1c728b94 plus pre-existing local changes | Current master uses the TRELLIS.2/DINOv3 route. |
| Microsoft TRELLIS.2 | 75fbf0183001ed9876c8dbb35de6b68552ee08bd | Includes image-to-3D and a distinct texturing-existing-mesh pipeline. |
| Original TRELLIS | 442aa1e1afb9014e80681d3bf604e8d728a86ee7 | Different architecture, image/text checkpoints and output representations. |
| Pixal3D paper / Pixal3D-D | Paper branch and TencentARC/Pixal3D-D | Direct3D-S2/DINOv2 route; not a distilled upgrade for current master. |

The official repository trees, READMEs, pipeline configurations, model-author listings, available branches/releases and relevant collections were checked. TencentARC's model listing returned Pixal3D and Pixal3D-D; Microsoft's returned TRELLIS.2-4B and the original image/text families. No relevant official LoRA, category adapter, style adapter or SKILL.md was located in those checked trees/listings. The collections queries returned 22 TencentARC collections and 39 Microsoft collections, with no Pixal/TRELLIS match in the returned titles/descriptions/item identifiers; the Comfy-Org query returned none. Guidance lives in papers, model cards, code and examples rather than an official agent skill. [S01] [S04] [S06] [S41]

The current Pixal model repository contains separate single-view and multiview flow weights for sparse structure, 512/1024 shape and 1024 material generation, plus shared decoders. The Comfy repack offers BF16 and int8_convrot variants and the DINOv3-plus-NAF encoder. TRELLIS.2 has separate shape/material encoders/decoders and texturing configuration. These are matched parts; an arbitrary VAE, encoder or adapter is not a safe replacement. [S02] [S05] [S50] [S51]

The component inventory distinguishes required/current parts, optional compatible paths, training or alternate-pipeline components, community candidates and unsupported swaps. It includes official helpers first; community candidates are included only where they address an identified gap.

## 2. Shared foreground preparation — R02

### What exists today

Our AW_PrepareView uses native RemoveBackground with the Comfy-Org repack of original ZhengPeng7/BiRefNet, then crops/composites for the selected mesh model. It reuses an incoming mask only when enough pixels are nearly fully transparent, checks for an empty foreground and flags foreground touching the image border. The Comfy LoadImage mask convention is one minus alpha; the remover's object mask uses white for foreground. Explicit conversion matters. Prepared RGB and crop metadata are saved, but the inspected path does not preserve a separate editable cutout-alpha asset. The existing image editor's edit-region mask is a different concept. [S09] [S10] [S46]

Standalone Pixal and official TRELLIS.2 name their remover class BiRefNet, but their configuration selects **briaai/RMBG-2.0**. The original TRELLIS image pipeline instead uses rembg/U2Net. Architecture name alone does not identify the weights or their license. [S02] [S04] [S06] [S13]

Both standalone Pixal and TRELLIS.2 reuse RGBA with nontrivial alpha, otherwise segment, find a foreground bounding box, crop and multiply RGB by alpha against black. Pixal adds 1.1 padding; TRELLIS.2 uses 1.0. These operations assume ordinary straight-alpha image content. Already-premultiplied input can be darkened twice; do not silently reinterpret arbitrary input alpha. [S01] [S04]

Native ImageCropToMask has its own mask-orientation heuristic and uses a high alpha threshold to find the crop. That can exclude low-opacity wisps or thin uncertain features from the framing. The custom empty-mask guard is valuable. A good mask still cannot recover a clipped antenna or a surface invisible in the source. [S09] [S11]

### Recommendation for every mesh route

Use one foreground-preparation service with model-specific final formatting:

1. Preserve the original image and approved design revision.
2. Reuse valid supplied alpha or a user-corrected foreground mask; run the configured remover when needed.
3. Show the cutout against checkerboard and light/dark backgrounds. Let the user correct keep/remove regions, undo/reset and download RGBA or the mask.
4. Check clipping, empty masks, stray disconnected pixels, holes, fine parts and consistency between selected views.
5. Composite/pad/resize according to the mesh backend's contract.
6. Save the source-to-prepared transform and invalidate derived cameras/features/meshes when the cutout or framing changes.

This is a proposed extension of existing editing tools, not a second mask-editor redesign. Keep the foreground-alpha asset separate from a region-to-edit mask and from material transparency in the eventual GLB.

**Known render cameras require special handling.** Official Pixal multiview inference preserves image framing while segmenting/resizing; it does not independently recenter every object. For our future render-guided route, preserve that frame or correctly transform the camera intrinsics and principal point. Applying the existing independent bounding-box crop without adjusting camera data would undermine geometric alignment. [S19]

Original BiRefNet provides standard, lightweight, portrait, matting and high-resolution variants. Use the existing compatible weights as the baseline. A portrait/matting/HR alternative deserves a focused thin-edge comparison, not an automatic category swap. Comfy's available Lucida repack is a community BiRefNet derivative, not an official Pixal or Microsoft helper; exact checkpoint/configuration correspondence must be resolved before adoption. Its broader design pipeline includes policies and helper models unrelated to 3D cutouts. [S12] [S14] [S46]

Foreground review should explicitly cover fingers, antennae, fins, wheel spokes, hair/fur, intentional openings, separate accessories, cast shadows and bright reflections. A transparent glass surface can be segmented successfully while still failing to reconstruct as physically transparent geometry. Model-card segmentation quality claims do not establish our mesh quality.

## 3. Camera and multiview contracts — R03

| Route | Inputs actually consumed | Camera behavior and limits |
| --- | --- | --- |
| Standalone Pixal single view | One prepared image | MoGe-2 estimates horizontal FOV; manual override is available. Camera distance is fitted to normalized geometry. |
| Native Pixal single view in our recipe | First selected image | Current recipe hardcodes camera_angle_x=49.13 degrees. Available native MoGe nodes are not wired into this recipe. |
| Native Pixal multiview template | Up to four named input sockets | A predefined front/left/back/right rig. Four sockets are a UI contract, not a universal model ceiling. |
| Our AW_PixalViews | Selected images and per-view azimuth/elevation/FOV metadata | Custom implementation supports 1–100 inputs, but this cap does not prove training support or practical memory. |
| Our native TRELLIS.2 recipe | First selected image | It is not a multiview route just because several images were prepared or a log reports their count. |
| Original TRELLIS | Different image/text APIs and conditioning | Its behavior cannot be assigned to TRELLIS.2 or Pixal checkpoints. |

These are source findings from the current recipe and native/custom nodes. A later UI/integration audit should make input-count messaging backend-accurate. [S07] [S08] [S09]

MoGe estimates source-camera perspective from image content. It does not estimate “front-right at 37 degrees” relative to the object's design, nor certify an AI-generated angle. Native LoadMoGeModel → MoGeInference → MoGeGeometryToFOV already exists. The FOV conversion node defaults to vertical; Pixal expects horizontal, so the axis/unit must be set deliberately. Do not replace known render FOV with a new estimate. MoGe's current upstream main has advanced beyond the pinned MoGe-2 used here; switching versions is not a research-only repair. [S17] [S18] [S47]

The inspected multiview source projects image features using supplied cameras and combines views. It does not automatically fit arbitrary unposed images or reject inconsistent images with a confidence score. Our wrapper negates the UI azimuth into the native convention and derives camera distance from FOV and a 1.1 framing assumption. It does not carry arbitrary camera matrices, principal-point offsets or orthographic projection. The first selected view is treated as the canonical frame; deselecting the nominal front without rebasing is a source-level risk requiring a test, not a demonstrated runtime failure. [S07] [S09] [S19]

The paper's multiview training uses 2–6 views and reports comparisons at 2/4/6, but that paper uses the Direct3D-S2/DINOv2 branch. It neither establishes ten as the current master's limit nor proves ten improves it. Current inference loads a supplied list of cameras/images without a hard four/ten limit found in the inspected path. [S03] [S19]

Recommendation: offer ten **reviewable candidates**, preserve approved front/back identity, and reconstruct from a coherent selected subset with useful coverage. Keep apparent scale, pose, handedness and side-specific details consistent. More images are helpful when they add correct evidence; duplicated or contradictory surfaces can bias conditioning. A generated back is still a design decision, not a discovery of factual hidden geometry.

A render-guide record should include mesh revision, camera matrix or equivalent calibrated parameters, axes, projection, horizontal/vertical FOV, aspect ratio, camera target/distance, framing transform, guide type and depth/normal convention. After generative refinement, retain these as the **requested** camera metadata until correspondence is established. Reliable camera fitting of the refined image remains unknown for our native route.

## 4. What generates quality — R04

The current standalone path is:

**Prepare foreground → estimate camera → extract DINO features → refine local features with NAF → sample sparse structure → sample/refine shape → sample material → decode geometry/material → save reusable state.**

Pixel-aligned conditioning projects candidate 3D locations back into the source images. This offers more spatial information than a global image summary, but it depends on useful masks and sufficiently accurate cameras. NAF upsamples/refines image features used by the trained model; it is not an optional style LoRA. Current Pixal uses DINOv3 and NAF together; its feature-channel contract expects them. The paper reports useful ablations for its earlier branch, not a benchmark of our installed Comfy route. [S01] [S03] [S07] [S16]

Official current pipeline defaults inspected:

| Stage | Steps | Guidance | Guidance rescale | Guidance interval | Time rescale |
| --- | --- | --- | --- | --- | --- |
| Sparse structure | 12 | 7.5 | 0.7 | 0.6–1.0 | 5 |
| Shape | 12 | 7.5 | 0.5 | 0.6–1.0 | 3 |
| Material | 12 | 1.0 | 0 | 0.6–0.9 | 3 |

These are checkpoint configuration defaults, not evidence that maximum guidance or more steps gives the best object. Current native Comfy sampling is expressed through different stage nodes/scheduler transforms. Our recipe uses structure 12 steps, low shape 20, high shape 12, material 12, with guidance 7.5/7.5/7.5/1 and seed offsets. Do not mechanically replace that graph with standalone settings without mapping the scheduler semantics. [S02] [S08]

The standalone cascaded path uses an intermediate coarse shape, then higher resolution subject to its sparse-token budget. Requested resolution is not necessarily the final achieved resolution if the adaptive path reduces it to fit the budget. Report actual resolution/token count when available. Higher resolution raises potential detail and cost, but cannot repair contradictory references or guarantee smooth manufactured surfaces. [S01]

Neither current Pixal nor native TRELLIS.2 in our recipe has a direct ordinary text-prompt mesh-conditioning input. Text influences the upstream design/angle images. Original TRELLIS has separate text-model checkpoints, which are a different support choice; they are not a prompt box to bolt onto Pixal. [S02] [S06] [S08]

## 5. Why the previews were consistent — R05

The installed app decodes one geometry/material result, saves its latent state, applies a very high preview-renderer mesh-count safeguard, and renders eight rotations at 45-degree intervals. It produces 1024-pixel JPEG previews with several HDRI environments plus normal/clay/base-color modes. The camera follows the same object and FOV throughout. Thus its images agree because they are views of the same 3D representation. [S20] [S21]

Environment illumination, reflections and smooth shading can make surfaces look more convincing than the bare geometry. A clay/normal comparison is necessary when judging bumps, seams, sharp edges and thin pieces. The GLB viewer uses different exposure/shadow/environment settings; a preview-versus-export comparison must match lighting before attributing all appearance differences to geometry or texture damage. HDRI assets inspected here are CC0, but the PBR renderer code has separate terms. [S20] [S21] [S39] [S43]

Native Comfy's RenderMesh supplies:

| Output | Useful role | Important limit |
| --- | --- | --- |
| Texture or vertex-color render | Appearance guide for a compatible editing route | Requires actual texture/UVs or vertex colors; raw mesh alone may produce clay. |
| Depth | Structure guide for a compatible depth-conditioned route | Per-view normalization, near white; not metric depth. Background and polarity must match the model. |
| Normals | Surface orientation and geometry review; possible future control input | Encoding/coordinate basis must match a trained consumer. No accepted model is automatically proven to consume this map. |
| Foreground mask | Silhouette review, compositing and preparation | Object-white hit mask, unlike LoadImage's transparency-mask convention. |

RenderMesh currently uses the first mesh in a batch, constructs a roll-free perspective camera and builds a triangle BVH. Wider camera-node fields do not establish renderer support for arbitrary roll or orthographic projection. Start later verification with square images, explicit perspective cameras and zero roll; test top/bottom pole behavior. Native PaintMesh can produce vertex colors from the generated material field without a full UV bake, but this is an approximate appearance guide, not identical to the standalone HDRI/PBR render. [S24] [S25]

A rough guide should come from a completed coarse geometry stage, not from interrupting a sampler midway. Geometry-only depth/normal/mask guides can avoid material generation, UV work and final GLB export. Color-guide routes have additional appearance costs. Reuse a good existing intermediate rather than always regenerate a “cheap” one.

## 6. Export, the stalled run and native alternatives — R06

### Standalone export order

Saved latent state → decode mesh/material → fill small holes → construct BVH over raw geometry → remesh or cleanup path → simplify to target faces → UV unwrap → normals/UV rasterization → project/sample material field → fill texture gaps → create PBR material → write GLB.

The installed CuMesh simplifier's argument is **target number of faces**, despite an upstream postprocess docstring referring to vertices. The 1M slider is therefore a final triangle-face target. It does not limit raw decoded geometry, the earlier BVH, remeshing cells or temporary buffers. [S22] [S23]

Disabling remeshing still leaves raw BVH construction and a cleanup/simplification route. It does not mean zero preprocessing or guarantee low peak memory. Narrow-band dual-contouring resolution, projection toward the original surface, hole thresholds and removal of small components all affect shape preservation. The installed app explicitly uses project-back 0 where the library's default differs; compare rather than assume either is universally correct. [S22]

Observed earlier: the progress JSON remained at Building BVH, but the log reached Cleaning mesh at 2/6. Source inspection explains the stale label: the interceptor published on progress increments, not every description change. That means the last displayed label did not identify the active operation. GPU memory was nearly full, resident process RAM was about 41 GiB and private memory about 66 GiB; CPU time/GPU utilization continued. None of this establishes an OOM exception, deadlock, or exact cause. **No final GLB was verified from that run.** [S20] [S44]

Pixal3D was stopped with Brian's approval. The 2,555,084-byte saved state remains at D:/pinokio/api/Pixal3D-Pinokio.git/app/tmp/state_1792540048759_6989.npz. It permits a later export retry without repeating image/shape sampling. No restart or retry occurred in this pass.

### What our Comfy workflow already does differently

Our recipe preserves the raw native mesh and material voxels with AW_SaveMaster, then loads them separately for export. It uses native RemeshMesh, DecimateMesh, normals, UV unwrap and texture/normal/AO baking. This is not the same CuMesh/o_voxel native-extension export stack as the standalone app. [S08] [S09] [S24] [S48]

Current source settings include optional 768-resolution solid-mode remeshing, zero project-back, QEF enabled, no small-component removal; master/game face and texture targets are separate. Solid-mode filling can change intentional openings or interiors. Aggressive simplification can remove thin appendages, and vertex normals cannot restore lost geometry. Preserve the raw master before any such operation. The existing game derivative remains tied to an approved master.

Separate concepts in the UI: shape-generation detail, mesh-cleanup resolution, target triangles, texture pixels and physical dimensions. The standalone assets are normalized; our AW_ScaleMesh applies an explicit height in meters. Reimport must verify orientation, dimensions, UVs, normals and material channels. Standalone export packs metallic into blue and roughness into green; its material sets OPAQUE even where alpha exists in the color texture. Foreground removal is not a material-transparency implementation. [S22] [S26] [S08]

A successful textured GLB is not automatically riggable or printable. Game derivatives may still need suitable deformation topology, collision/LODs and a target-specific budget. Print derivatives need manifoldness, intersections, thickness and real-world scale checks; filling every hole would destroy intentional openings.

### Additional official route

TRELLIS.2's texturing pipeline accepts an existing mesh plus an image, uses a shape encoder, generates material and bakes it onto that mesh. It can reuse UVs or create new ones. It normalizes coordinates and changes axis representation, and UV seams may split vertices. Therefore it is a useful geometry-preserving texturing candidate, not a claim of bit-identical topology/scale preservation. It is also not an image-angle generator. Its BRIA/NVIDIA dependencies need the same license/dependency review before copying that route. [S26]

## 7. Rough-mesh guidance and model-specific text — R07

The future comparison is:

**Approved design/front/back → supported mesh reconstruction → known-camera render → guide + approved appearance reference(s) + model-specific description → human-reviewed candidate views → supported final reconstruction.**

Keep the original direct mesh as the baseline. If it already meets the need, do not force a second generation loop. A flawed proxy can preserve a wrong silhouette very consistently; more polished images do not prove better geometry.

| Accepted image family | Evidence-backed guide route | What remains unproven |
| --- | --- | --- |
| Qwen Image 2.1 + optional AnyAngle | Author describes original appearance plus rough color render; preserve the checked T8 ordering and trigger. | Front/back as an extra reference, our varied objects, exact-angle adherence, net final-mesh gain. Commercial model permission conditions remain. |
| Klein 4B | Community RefControl for the matching Base variant uses depth first, appearance second and its trigger. | Direct mesh depth must match the example's depth distribution; props/creatures/environment pieces need tests. Distilled 4-step settings are not Base/adapter settings. |
| Klein 9B | Its own matching RefControl/Base route; also a simpler rendered-image editing baseline exists. | Better quality than 4B is not established. Base operating license and output permissions are distinct. |
| Qwen Edit 2511 | RINO demonstrates text-plus-depth image editing; a separate multiple-angle LoRA provides prompt-camera control. | Depth plus identity references plus approved back is a proposed combination, not a proven equivalent to AnyAngle. |
| FLUX 3 | General reference-image editing and model-specific description guidance. | No verified equivalent mesh-guide camera adapter found in this research. Keep design/editing support; do not advertise exact camera control. |

The accepted decision supplement records exact adapters, example parameters and licensing links. Direct mesh depth could avoid an unnecessary depth-estimation model; this also avoids the NC Depth Anything V2 Large weights used in the RefControl example. That substitution still requires an equivalence check for depth polarity, framing, normalization and backgrounds. [S33] [S34] [S35] [S36] [S37]

Text is required context, not an afterthought. Per-model angle instructions should identify each reference's role, requested camera/view, established visible-side features, proportions/materials to preserve and any permitted correction. The model-aware enhancer should retain a structured record of agreed front/back/left/right/top/bottom facts, flag unknowns rather than invent them as facts, and translate those requirements into the selected model's supported prompt style. Do not demand mutually occluded details in one view or transfer one model's trigger/order into another.

Color, depth, normals and silhouette are candidates with different jobs, not four arbitrary image attachments. Normals/masks help inspection even when no compatible image-control consumer has been established. Cross-check the resulting image against the guide and design; actual-pose recovery is not yet provided. Limit iterations to an agreed comparison and retain the direct-output baseline to prevent self-reinforcing drift.

The creator's downloadable Pixaroma Episode 34 graphs provide a useful independent baseline: rendered-image reference conditioning with distilled Klein 9B, and a variant using the rendered image as the starting latent with denoise 0.7. The graph uses 4 steps/CFG 1, not RefControl's Base recipe; it is not a guarantee of exact geometry. Seven JSON graphs were read from the ZIP in memory without installation. ZIP timestamps are 14–17 September, and the page does not establish a publication date within the requested last-month window. No claim of watching or transcribing the video is made. [S40]

## 8. Categories and exposed settings — R08

Use the established **Characters, Creatures, Vehicles, Props and Environment Pieces** categories. The sources support different preservation/review needs, but no official category-specific Pixal/TRELLIS numerical sampler preset was found. Do not invent a “person CFG” or “building steps” difference.

| Category | What the preset/help should protect | Numerical settings |
| --- | --- | --- |
| Characters | Hands/fingers, face, pose, back accessories, separate limbs, deformation needs | Shared validated baseline until a comparison justifies a difference. |
| Creatures | Tail, ears/horns, claws, thin appendages, fur silhouette, anatomy | Same; more triangles alone cannot repair fused limbs. |
| Vehicles | Wheels, openings, symmetry/asymmetry, underside and separate moving parts | Same; test solid remeshing before adopting it. |
| Props | Handles, holes, flat panels, small controls, sharp edges | Same; simplification can suit solid forms but must preserve defining details. |
| Environment Pieces | Scale, planar surfaces, openings/interiors, repeated elements, modular boundaries | Same; segmentation and framing of a large structure need special review. |

Expose meaningful controls and Reset to recommended settings. The recommendations should depend on exact model, stage and measured hardware profile, not silently turn on lower fidelity:

| Control | Verified starting point / range | Explain to the user |
| --- | --- | --- |
| Shape resolution | Standalone UI 1024 or 1536; default selected by its low_vram configuration. Native graph has its own stage/token contract. | Potential geometric detail and memory cost; separate from texture size. Report actual achieved resolution. |
| Structure steps/guidance | Official config 12 / 7.5; app sliders 1–50 / 1–10 | Coarse occupied shape. More is not a guaranteed improvement. |
| Shape steps/guidance | Official config 12 / 7.5; app exposes guidance 1–10, hides some other stage settings | Fine geometry and adherence. Keep scheduler-specific settings together. |
| Material steps/guidance | Official config 12 / 1; app does not expose the complete set | Surface color/material generation, not extra geometry. |
| Seed | Record the actual integer for each stage and randomize intent separately | Reproducibility aid, not a camera/identity lock or cross-version bitwise guarantee. |
| FOV | App manual bounds approximately 1–170 degrees, default 0.2 rad; native conversion must specify axis/unit | Perspective. Auto estimate for unknown source cameras, preserve exact known render cameras. |
| Target faces | Standalone 100k–1M slider; native derivative targets separate | Final triangle budget, not peak memory or guaranteed game readiness. |
| Texture size | Standalone export request uses 4096; our master/game targets are separate | Surface pixel detail and storage/baking cost, not silhouette detail. |
| Remesh/fill/project/smooth | Exact native node contract, currently 768 solid/QEF/project 0 in our recipe | Can alter openings, corners and small parts. Review against raw master. |
| Memory reserve/offload/precision | Existing native management plus workflow headroom settings | Reserve is a scheduling hint, not a strict GPU-memory ceiling. Precision/resolution changes may affect output. |

Known UI defaults are recorded as observed source, not endorsed universal recommendations. Preserve current quality settings until authorized comparisons establish a better baseline. [S02] [S08] [S20] [S24] [S30]

## 9. Resource use, reliability and portability — R09

### Stage resource map

| Stage | What lives in memory | Useful existing support / future question |
| --- | --- | --- |
| Image preparation | Input RGB/alpha, remover weights and activations | Native patcher/offload; process sequentially and retain corrected alpha. |
| Image feature conditioning | DINO tokens, NAF weights and large per-view maps | Native NAF already chunks attention. Retained full maps are a separate RAM issue. |
| Structure/shape/material | Flow weights, sparse tokens, decoder activations/latents | Stage offloading and matched precision; preserve state after successful generation. |
| Guide rendering | Geometry, attributes, BVH, rays and output images | Render one selected mesh/camera at a time; investigate BVH reuse without stale geometry. |
| Cleanup/remesh | Raw and derived meshes, grids, adjacency/BVH scratch | Separate peak from generation. Chunking/lifetime management before reducing detail. |
| UV/baking/export | Charts, UV images, normals, PBR buffers, reference geometry | Reuse saved master; bound resolution, release completed stages and retry export separately. |

Native Pixal conditioning computes and retains three NAF maps per view: 1024 channels at 512², 512² and 1024². The arrays alone contain 1,610,612,736 elements: **3 GiB per view at 16-bit, 6 GiB at 32-bit**. Ten views imply 30 or 60 GiB for these maps alone; eight imply 24 or 48 GiB. This is arithmetic from the inspected shapes, **not a measured process peak**. Runtime dtype/device depend on Comfy's selected model/intermediate policy; an fp32 weight filename does not prove all runtime maps are fp32. Other tensors/weights increase the total. [S07] [S28] [S29]

Native NAF already uses approximately bounded attention chunks and can write into a preallocated output on the intermediate device. Reimplementing “tiled NAF” without understanding that would duplicate existing work. Investigate stage-specific material-feature creation, lifetime/reuse and measured dtype first. Offloading to RAM can protect VRAM while exhausting 64 GB system memory. [S28]

Our extension already serializes stages, unloads managed models at stage boundaries, supplies model-budget headroom and owns bounded temporary cleanup. It retains history and raw masters. The image VAE tiling setting does not prove that a 3D shape decoder is tiled. Do not delete HF/model caches or other app data to solve stage memory pressure. [S30] [S31] [S32]

The relevant community project Espalier targets the same inspected Pixal/TRELLIS/CuMesh revisions. It changes weight streaming, feature/decoder tiling, occupied-voxel projection, geometry scratch-buffer lifetime and chunking, and separates generation/export processes. Its author reports 16 GB Linux success and describes numerical differences for some tiling changes. This is strong source material for memory engineering, **not a Windows/Comfy drop-in fix or our benchmark**. Native Comfy already addresses some of these issues through a different implementation. [S27]

The installed standalone environment uses Python 3.12, Torch 2.8/CUDA 12.8 and community native wheels tagged for that Torch/CUDA combination, plus triton-windows. Earlier repairs pinned MoGe-2 and adjusted compiler selection. Mutable “latest” wheel URLs are not a reproducible dependency lock; future packaging should pin exact artifacts/hashes and validate imports/ABI. First-run compilation and a long geometry operation are distinct costs. A successful compiler repair did not verify export. [S49]

**16 GB/64 GB:** there is existing successful generation/preview evidence and a failed/stopped export; this is not whole-pipeline certification. **8 GB:** remains unproven. Official TRELLIS.2's documented Linux/24 GB baseline and another author's 16 GB result do not certify our 8 GB profile. No low-memory setting was changed during research. [S04] [S27] [S44]

Progress should follow real stage starts/completions, with elapsed time and counts where available. Do not invent a percentage for an opaque native call. Native Comfy code has interruption checks in some loops; native extensions may not return promptly to Python. A cancellation/recovery test is still needed. Restarting the whole app should not be the ordinary export-retry path.

Cache keys should include source/mask hashes, approved revision, exact model/adapter/precision/settings, preparation transform and camera/guide type. Changing an image or mask must invalidate downstream derived data. Keep original images, history and accepted masters outside disposable job work; existing owned-path cleanup is the starting point.

## 10. Licensing and acquisition — R10

These are engineering interpretations of the inspected terms, not a blanket legal clearance for every derivative or third-party asset. Operating weights, using outputs, modifying/distributing code and redistributing weights are separate permissions.

| Component | Checked terms | Recommendation consequence |
| --- | --- | --- |
| Pixal3D / TRELLIS.2 core and published weights | MIT for those releases; third-party terms remain | Commercial core permission does not clear every helper. |
| Original BiRefNet / Comfy repack | MIT | Best existing default to retain for broad local use, with notices/provenance. |
| Original TRELLIS remover: rembg / U2Net | MIT code / Apache-2.0 repository terms | Record exact downloaded weight provenance if selected; no reason found to replace our current baseline. [S55] [S56] |
| BRIA RMBG-2.0 | Noncommercial weight license; commercial self-hosting agreement path | Do not silently inherit it from the standalone default. |
| DINOv3 | Meta DINOv3 license, with its own use/redistribution terms | Record separately; a repack label or Pixal MIT notice does not override it. |
| NAF | Apache-2.0 | Retain license/notice obligations; matched architecture required. |
| MoGe-2 | MIT with identified third-party Apache portions; inspected model card MIT | Pin the correct v2 code/weights; not the same as all newer MoGe variants. |
| CuMesh / FlexGEMM / cuBVH | MIT in checked upstream licenses | Useful source candidates; packaged dependency versions still matter. |
| nvdiffrast | NVIDIA Source Code License, research/evaluation restriction for non-NVIDIA use | Avoid carrying it into an unrestricted commercial route without permission or a suitable replacement. |
| nvdiffrec-derived renderer | NVIDIA research/evaluation restriction; installed render files retain restrictive header | Do not treat the PBR renderer as MIT because its caller is MIT. |
| Native Comfy core / comfy-kitchen | GPL-3.0 core / Apache-2.0 kitchen | Distribution/code obligations need to be honored; generated assets are not automatically GPL simply because the tool is. |
| Pixal HDRIs | CC0 in the installed asset notice | These specific maps can be reused under their terms; not every sample asset is cleared. |
| Lucida | Community card states MIT; training-data provenance has caveats | Optional comparison only; resolve exact revision/config and provenance before shipping. |

The nvdiffrast license was checked both in current official source and the installed wheel. Its name includes “1-Way Commercial,” but the actual use clause restricts non-NVIDIA use to research/evaluation. The official README provides a commercial inquiry route. This is a concrete reason to prefer our inspected native Comfy rendering/baking path, which does not import nvdiffrast/nvdiffrec in the traced path. That observation is not a complete legal audit of every transitive package or every optional Comfy backend. [S38] [S39] [S45] [S53]

Keep the five image-family labels already agreed: **Commercial use allowed** or **Commercial use has conditions**, each with exact terms. Qwen 2.1/AnyAngle, Klein 9B and FLUX 3 retain their specific caveats. Apache/MIT adapters do not override base-model terms. Do not change that menu or remove an accepted family during research. [S37]

Download into the chosen Comfy installation with exact identity/revision/hash. Reuse the existing user-supplied HF authentication mechanism without storing tokens in workflows, history, export metadata or shared files. Optional gated downloads need explicit access/license information; after all selected dependencies are present, prove the route can run offline in later testing. Offline operation was not tested here. No credentials were inspected or copied.

## 11. Research recommendations for the next discussion — R11

These are prioritized conclusions for Brian's later implementation proposal, not an executable implementation plan or authorization to change software.

| Priority / disposition | Recommendation | Evidence and smallest later check |
| --- | --- | --- |
| 1 — Keep and extend existing support | Shared background removal, reusable alpha and visible cutout correction for every mesh route | Native remover exists. Check fine parts/holes and known-camera framing before comparing model quality. |
| 2 — Apply existing support carefully | Correct camera metadata; evaluate native MoGe only for unknown source FOV | Confirm horizontal units and round-trip framing. Do not label requested AI angle as measured pose. |
| 3 — Evaluate | Render rough-mesh color/depth/normal/mask guides with native nodes | Verify orientation, front/back identity, depth polarity, silhouette and top/bottom behavior. |
| 4 — Evaluate | Model-specific guide + approved reference(s) + text; compare AnyAngle and Klein RefControl first | Use their exact variant/order/trigger contracts; compare final mesh with direct output. |
| 5 — Keep, verify and improve | Preserve raw masters and make export independent/retryable; improve progress truth | Reuse one saved state, compare native cleanup/export variants and reimport final GLB. |
| 6 — Evaluate resource improvements | Measure retained features and stage peaks; adapt relevant streaming/lifetime ideas | Start with no-quality-change resource lifetime fixes; label precision/tile/resolution differences. |
| 7 — Apply help, test numerical changes | Category preservation advice and fully exposed settings | No invented category CFG/step presets; confirm setting changes affect the intended stage. |
| Conditional | Existing-mesh TRELLIS.2 texturing, matting/HR remover, community guide baselines | Adopt only for a measured gap, matching input/output and licensing requirements. |
| Do not adopt by assumption | Arbitrary VAEs/encoders, nonexistent official category LoRAs, unbounded ten-view accumulation, wholesale standalone renderer stack | Incompatible/unproven or unnecessary cost/terms. |

Keep the working interface, history/reuse, per-image editing, review/inclusion controls and master/game separation. No unrelated redesign, new Pinokio app, hosted service or automatic support expansion follows this report.

## 12. Bounded later validation and remaining unknowns

Before later testing, agree what improvement is sufficient. Use an asymmetric prop, a character with hands/back detail, a creature with thin appendages, a vehicle with openings and an environment piece. Do not judge all routes from crates or beacons. Use ground-truth multiview geometry where possible; unseen surfaces invented from a single image cannot be scored as recovered truth.

1. Verify native cutout and camera/render contracts without generative angle refinement.
2. Produce/reuse one supported direct reconstruction and preserve its source state.
3. Compare direct output with one exact AnyAngle color-guide recipe and one exact Klein Base RefControl depth recipe; keep corresponding inputs/settings recorded.
4. Compare adding an approved back only after the documented two-input baseline works.
5. Compare a coherent small mesh-input subset with additional reviewed views.
6. Retry export from the same state, measuring generation/render/export peaks separately; compare one cleanup/resource change at a time.
7. Reimport master/game/print derivatives and review shape, UV/material fidelity, scale and use-specific requirements. Expand to varied asset categories only after basic contracts pass.

Record exact model hashes, reference order, prompt, seeds, cameras, masks/crops, runtime precision, actual resolution/tokens, raw/final counts, time and peak VRAM/RAM. Judge under matched neutral/clay lighting as well as beauty renders. Never call a file existing on disk an export/reimport pass.

| Remaining unknown | Why research alone cannot settle it | Smallest later evidence |
| --- | --- | --- |
| Whether refinement improves the final mesh | Author examples and source contracts are not our controlled comparison | Direct mesh versus guide-refined reconstruction on matched assets. |
| Actual camera angle of an AI-refined image | MoGe FOV is not object-pose fitting; no reliable native fitting route verified | Geometry/image correspondence evaluation with known cameras; reject rather than silently certify mismatches. |
| Best coherent view count | Paper branch and current implementation differ; more views add memory/conflicts | Same asset, coherent subsets and measured output/peak memory. |
| Best category numerical defaults | No official per-category presets found | Controlled preservation/quality comparison, shared baseline otherwise. |
| Exact cause of stopped native export | No OOM/crash or finished native-stage trace establishes it | Instrumented later retry from preserved state, no resampling. |
| 8 GB support | No execution at that budget in this pass | Complete generation/render/export at the target budget with quality review. |
| RefControl depth equivalence / AnyAngle third reference | Proposed substitutions/extensions of author contracts | Inspect depth distributions; compare exact documented baseline first. |
| Top/bottom, normal encoding and broader camera fields | Node schema is broader than verified renderer behavior | Render known geometry at those cameras and compare expected maps. |
| Full packaged commercial dependency clearance | Component review is not a complete distribution SBOM or permission grant | Pin actual runtime package closure, carry notices and resolve restricted optional components. |
| Current-month YouTube coverage | Date-filtered discovery produced no verifiable eligible additional video; Episode 34 date is unconfirmed | Do not label an undated/older graph a new October release. Follow up only if a specific relevant source appears. |

The recent-workflow search window was 20 September–20 October 2026. Primary code/examples were used even when older; they are authoritative for their versions. No current-week/latest claim is based on a title, search ranking or ZIP timestamp. Community workflows were inspected as sources, not installed or executed.

## 13. Coverage and research-only audit

| Task | Answer location | Research disposition |
| --- | --- | --- |
| R01 | Section 1 and component/source inventories | Official inventory and native equivalence covered; no matching official LoRA/skill found in checked sources. |
| R02 | Section 2 | Shared remover and alpha/crop/correction contract covered. |
| R03 | Section 3 | Single/multiview/FOV/pose limits covered; generated-pose fitting remains explicitly unknown. |
| R04 | Section 4 | Generation/NAF/sampler/text roles traced; paper/current distinction maintained. |
| R05 | Section 5 | Preview consistency explained; native guide modes and limits established from source. |
| R06 | Section 6 | Export order, triangle target and failure evidence separated; final export remains unproven. |
| R07 | Section 7 | Five-family guide/text compatibility and proposed substitutions recorded. |
| R08 | Section 8 | Categories, exposed controls and absent numerical evidence documented. |
| R09 | Section 9 | Feature/RAM/export peaks, existing management and Windows dependency risks covered. |
| R10 | Section 10 | Major code/weight/helper/render terms distinguished; package-level audit bounded. |
| R11 | Sections 11–12 | Prioritized recommendations, keep/test/skip decisions and minimal later comparisons supplied. |

No product code, settings, workflows, model installations, credentials or app lifecycle changed for this research. No new generation, benchmark or GPU test ran. The stopped app's saved state was retained. The research does not claim that the stalled standalone export finished, that eight/ten views are optimal, that 8 GB is certified, or that a guide guarantees the generated camera angle.

The next action is to discuss an implementation proposal for **the existing Comfy software**, using these findings. Pinokio and standalone-language choices remain later product work.

## Source links

**Completion audit:** R01–R11 and all 68 research checklist items are addressed. The inventory contains 46 component records and 56 source records. JSON parsing, source cross-references, local artifact/source paths and a credential-pattern check passed. Hashes confirmed that the 20 inspected product/dependency files were unchanged. This validates the research package, not a newly executed workflow. Audit: 2026-10-21T00:52:11.4311550Z.

The JSON source register adds inspected locations, exact revisions, local file hashes and limitations to these links.

[S01]: https://github.com/TencentARC/Pixal3D/tree/f7cf38429b0bd264f1995f0f8743a88b1c728b94
[S02]: https://huggingface.co/TencentARC/Pixal3D/blob/b0cb2e1b794cab9aa0ac38a95d794a4d9337437f/pipeline.json
[S03]: https://arxiv.org/html/2605.10922v1
[S04]: https://github.com/microsoft/TRELLIS.2/tree/75fbf0183001ed9876c8dbb35de6b68552ee08bd
[S05]: https://huggingface.co/microsoft/TRELLIS.2-4B/tree/af44b45f2e35a493886929c6d786e563ec68364d
[S06]: https://github.com/microsoft/TRELLIS/tree/442aa1e1afb9014e80681d3bf604e8d728a86ee7
[S07]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_trellis2.py
[S08]: <E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop/recipes.py>
[S09]: <E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop/nodes.py>
[S10]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_bg_removal.py
[S11]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_images.py
[S12]: https://github.com/ZhengPeng7/BiRefNet
[S13]: https://huggingface.co/briaai/RMBG-2.0
[S14]: https://huggingface.co/egeorcun/lucida
[S15]: https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md
[S16]: https://github.com/valeoai/NAF/tree/37f2dfc180f2de53d98bd601109c0da0dd6b0f43
[S17]: https://github.com/microsoft/MoGe/tree/925b8ed835a7a9cdb7578ba15c658a0afc969030
[S18]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_moge.py
[S19]: https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/inference_mv.py
[S20]: <D:/pinokio/api/Pixal3D-Pinokio.git/app/app.py>
[S21]: https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/pixal3d/utils/render_utils.py
[S22]: <D:/pinokio/api/Pixal3D-Pinokio.git/app/env/Lib/site-packages/o_voxel/postprocess.py>
[S23]: https://github.com/JeffreyXiang/CuMesh/tree/12289e1062f0603f2f0d0771b02e1395d247f26f
[S24]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_mesh_postprocess.py
[S25]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_camera.py
[S26]: https://github.com/microsoft/TRELLIS.2/blob/75fbf0183001ed9876c8dbb35de6b68552ee08bd/trellis2/pipelines/trellis2_texturing.py
[S27]: https://github.com/overyonder/espalier/tree/b51fac8bb18f92f9f29f9aec771d0913b1b9c3c2
[S28]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/image_encoders/naf.py
[S29]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/clip_vision.py
[S30]: <E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop/memory_policy.py>
[S31]: <E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop/routes.py>
[S32]: <E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop/store.py>
[S33]: https://huggingface.co/lilylilith/QI_2.1_AnyAngle
[S34]: https://github.com/thedeoxen/refcontrol
[S35]: https://github.com/yangtiming/RINO
[S36]: https://github.com/black-forest-labs/flux-3-image-klein
[S37]: MODEL-SUPPORT-AND-MESH-GUIDANCE.md
[S38]: https://github.com/NVlabs/nvdiffrast/blob/253ac4fcea7de5f396371124af597e6cc957bfae/LICENSE.txt
[S39]: https://github.com/NVlabs/nvdiffrec/blob/abf3a34b1eb6e782abffefc2462c7e9bcd89f9bb/LICENSE.txt
[S40]: https://workflows.pixaroma.com/ep/34/
[S41]: mesh-sources.json
[S42]: https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/NOTICE
[S43]: <D:/pinokio/api/Pixal3D-Pinokio.git/app/assets/hdri/license.txt>
[S44]: MESH-COMPONENT-RESEARCH-PLAN.md
[S45]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/LICENSE
[S46]: https://huggingface.co/Comfy-Org/BiRefNet/tree/25511f8787e51912e1480706b4e47b8f467fbf72
[S47]: https://huggingface.co/Ruicheng/moge-2-vitl
[S48]: https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/mesh3d/postprocess/remesh.py
[S49]: <D:/pinokio/api/Pixal3D-Pinokio.git/app/requirements.txt>
[S50]: https://huggingface.co/Comfy-Org/Pixal3D/tree/f37641be376725d324c56626007cc477f1249a69
[S51]: https://huggingface.co/Comfy-Org/TRELLIS.2/tree/430a9d09b2416687018c8fe8edced2ad4858a439
[S52]: https://github.com/JeffreyXiang/FlexGEMM/tree/6dd94a859c26ee8246888502eada3dd8ad85532e
[S53]: https://github.com/Comfy-Org/comfy-kitchen/blob/main/LICENSE
[S54]: https://github.com/ashawkey/cubvh/blob/main/LICENSE
[S55]: https://github.com/danielgatis/rembg/blob/main/LICENSE.txt
[S56]: https://github.com/xuebinqin/U-2-Net/blob/master/LICENSE

