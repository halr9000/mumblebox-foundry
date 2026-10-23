# Mumblebox: the strongest practical route to a better first mesh

Research completed 2026-10-21/22 UTC. Target: Windows, 16 GB GPU memory, 64 GB system RAM. This is a research deliverable and recommendation for discussion, not an implemented or benchmarked new workflow.

Companion documents: [evidence and exact versions](SOURCE-REGISTER.md), [finite validation plan](VALIDATION-PLAN.md), [remaining questions and how to settle them](FOLLOW-UP-RESEARCH.md), [completion audit](COMPLETION-AUDIT.md).

## 1. The answer in plain English

There is a credible way forward. It does not require throwing away Mumblebox, and it does not depend on discovering a perfect prompt. The strongest next iteration is a **camera-aware reconstruction workflow with optional guided improvement**, built on the useful pieces already present.

The critical change is to stop treating an attractive set of generated pictures as if it were a calibrated photograph set. Each picture has a frame, a lens or projection, an apparent object size, and a viewpoint. Some of those facts are known; others are estimates. The reconstruction must receive the actual information available, rather than confidently receiving a nominal angle that the image did not follow.

My recommendation is:

1. Preserve the working interface, editing, history, existing model recipes for comparison, mesh engines and GPU export. Prove their camera and image-preparation contract with known rendered test objects.
2. Establish a strong single-image mesh as a baseline. Add approved views when they contribute consistent evidence. Estimate uncertain cameras and check the estimates; do not equate a requested angle with a measured angle.
3. Use trained structure-plus-reference conditioning for additional images. Start the permissive structural-control comparison with Klein 4B RefControl depth; evaluate Qwen Edit 2511, Qwen 2.1/AnyAngle, Klein 9B and FLUX 3 only in their documented roles and with their own license information. Continued support depends on useful results.
4. Treat a rough mesh as a hypothesis. Its depth, normals and silhouette can guide a new view, but they also carry its shape mistakes. Permit selective correction, compare against the baseline, and retain the earlier mesh if a second pass makes it worse.
5. If this leaves a measurable, repeatable gap, first build a small camera/geometry fitting component. Only then consider a focused trained adapter, using the existing training implementations and licensed synthetic data described below.

This is not a promise that every object will work. It is a way to make progress measurable, avoid spending days on unproductive prompt variations, and reach a useful stopping point. The immediate next phase should be a bounded comparison of complete routes—not another open-ended research project or an attempt to make every possible combination work.

### The main discoveries

**Latest accepted support decision:** Brian is willing to abandon any image model that cannot deliver the required behavior through a practical, evidence-backed route. The five researched families are evaluation candidates, not a requirement to ship five working angle generators. A model may qualify for initial design or local editing while failing angle generation; those roles must be explicit. If it has no useful supported role, drop it from the supported set while preserving existing user files and provenance. The recommended set may shrink to one model. A custom adapter is justified by a specific measurable gap and a decisive pilot, not by a commitment to rescue a favorite base model. Failure in a bounded test means unsuitable for this release and setup, not proof that improvement is theoretically impossible.

- **Camera mistakes can overpower good images.** A generated rear three-quarter image wired into a cardinal rear slot is false information, even if the picture is excellent. Cropping and resizing can also change the effective camera.
- **A suitable camera estimator is already in current Comfy source.** Depth Anything 3 Small/Base can process images together and output intrinsics and extrinsics. Their cards specify Apache 2.0. This is a candidate to test, not a guarantee that contradictory AI images become valid measurements. [DA3 Small](https://huggingface.co/depth-anything/DA3-SMALL), [DA3 Base](https://huggingface.co/depth-anything/DA3-BASE), [native node](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_depth_anything_3.py).
- **Another practical workflow hit a problem very similar to ours.** AnyAngle Studio reports a controlled comparison in which reversing original/rough-reference order weakened camera adherence even after the text's image numbers were swapped. Its repaired graph uses original image 1, rough guide image 2, and the author's particular trigger. This is one author's experiment, not independent proof across objects. [Actual comparison](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/main/docs/validation-v164.md).
- **Mesh adapters are real, not a hypothetical category.** WorldSculpt contains actual PEFT LoRA wrapping for Pixal3D denoisers and released scene-reconstruction adapters. Its calibrated, masked scene inputs differ from our generated object views, so it establishes a practical mechanism rather than an immediate solution. [WorldSculpt](https://github.com/AlayaLab/WorldSculpt).
- **Some useful NVIDIA components are now permissively licensed, while others are not.** Current Kaolin and its current FlexiCubes implementation are Apache 2.0; the inspected nvdiffrast license still restricts use to noncommercial research/evaluation. Selecting a renderer therefore matters to the commercial-use path. [Kaolin](https://github.com/NVIDIAGameWorks/kaolin), [nvdiffrast license](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt).
- **Good-looking renders are an unreliable score for geometry.** DLSS, textures, normal smoothing and attractive lighting can improve appearance without fixing proportions, holes or topology. The decision test must include untextured geometry and held-out views.

## 2. What the existing work actually established

The complete previous [mesh-first report](../2026-10-21-mesh-first-research/REPORT.md) and [source register](../2026-10-21-mesh-first-research/SOURCE-REGISTER.md) were reviewed. Ten relevant local source hashes were rechecked and unchanged. Current source inspection is not a new execution test.

| Item | Evidence now | What it means |
|---|---|---|
| Frame-preserving Pixal3D preparation | Present in the inspected custom recipes | The earlier independent-crop defect is not simply still waiting to be fixed. Do not reimplement the same repair. |
| Toy-camera rerun with the same images | Historical saved review; depth/width ratio changed from about 0.92 to 0.72 after the framing repair | Preprocessing mattered. No ground-truth mesh proves that 0.72 was correct; rear viewfinder/grip problems remained. |
| TRELLIS route | The inspected recipe passes `images[0]` | Selecting multiple images in the UI does not make this particular route jointly multiview. Explain that accurately. |
| Pixal3D single-image route | MoGe/FOV assistance already wired | FOV assistance is not complete pose estimation. It does not determine all camera rotations and translations. |
| Draft mesh guide rendering | Depth, normal and mask rendering already present | “Add a renderer” is not the missing innovation. Check map conventions and how the chosen model consumes them. |
| RefControl and family-specific branches | Already present in source | The next step is compatibility proof and comparative results, not pretending these have never been built. |
| Native Pixal3D multiview node | Cardinal-view/shared-camera conventions in the inspected implementation | Arbitrary generated angles need the separate custom-camera route or a validated conversion. |
| GPU decimation and PEC export | Present | Keep Brian's GPU-finishing decision. Verify actual device and failure handling instead of silently returning to a very slow CPU path. |
| Model lifecycle cleanup | Existing owner already handles unloading | Extend or repair that owner only if a measured lifetime problem remains. Do not add competing cleanup systems. |

The historical toy-camera review is at `E:\Comfy-Desktop\ComfyUI-Shared\output\AssetWorkshop\assets\64edac36da7e\drafts\658624c796d94a13\framing-review.md`. It is an observation from the earlier run, not a current benchmark or a universal conclusion about contact sheets.

The research session did not launch Comfy, change a graph, load weights, generate pictures or meshes, or test a new component on the GPU. Existing runtime results remain historical evidence. Source snapshots and reports were the only new project artifacts.

## 3. Why consistency has been difficult

### There are several different problems hiding inside the word “consistent”

| Problem | Example | Appropriate kind of solution |
|---|---|---|
| Identity and design | The camera gains a second handle or loses its round window | Appearance references, approved design facts, selective editing, trained reference conditioning |
| Viewpoint | “Rear three-quarter” comes out almost directly rear | Camera-conditioned generation and camera estimation/checking |
| Projection and framing | The side image is independently zoomed to fill its panel | Preserved frames, explicit pixel transforms and updated intrinsics |
| Shape compatibility | Front and side imply different body thickness | Cross-view geometry checks, joint reconstruction, geometric constraints or rejection of a bad view |
| Surface detail | The main volume is right but edges are bumpy | Resolution/decoder/refinement settings, geometry refinement, appropriate regularization |
| Materials | Painted highlights become bumps or textures disagree across seams | Separate geometry/material evaluation, surface-aware texture generation and baking |

More references primarily address the first row. They do not automatically solve the others. A model can preserve the red handle in every image while making incompatible widths, lens sizes and camera perspectives.

### A contact sheet helps design agreement but does not calibrate its panels

Generating four views together can encourage shared appearance. Splitting exact rectangular panels is deterministic and should be automatic. However, the generator can still zoom one panel, use a different lens, crop a corner, or miss the requested azimuth. A contact sheet is a useful option, not proof of four mutually valid cameras.

Never stretch panels separately to force equal bounding boxes. A long object naturally looks narrower from the front than from the side. Equal box width is not equal physical scale. Preserve each original panel and record every crop, resize and pad. If a transform maps old image pixels to new pixels with matrix `A`, the corresponding intrinsic matrix changes as `K_new = A × K_old`. Perspective, orthographic and nearly orthographic images also require different assumptions.

### A rough mesh cannot be “only orientation” without carrying shape

Depth is the distance to the surface. Silhouette is the outline of the surface. Normals describe the direction the surface faces. All three therefore describe the rough mesh's geometry, including wrong geometry. Removing color prevents invented paint and material details from being copied as appearance; it does not erase a wrong roof pitch, swollen body or misplaced limb.

The practical response is to use the draft as a constrained suggestion: control strength and schedule, trusted-region masks, less restrictive control where the draft is wrong, and a comparison with approved images. If the shape is badly wrong, regenerating a beautiful set of views from it can consistently preserve the mistake. A second pass must earn its place by improving the final mesh.

### More images are not automatically better

An additional view helps when it reveals useful, compatible information. A contradictory image can hurt more than a missing image. Four excellent views do not guarantee a good reconstruction; eight attractive but contradictory views do not guarantee better coverage. Keep the number adjustable and evaluate marginal benefit. There is no basis here for enforcing ten images, a fixed “five good” rule, or exactly two mesh passes for every subject.

## 4. Camera estimation and deterministic geometry tools

### What the camera record needs

Each approved image should travel with its original dimensions; crop/resize/pad transform; projection type; focal lengths and principal point where known; camera rotation and translation where known; coordinate convention; mask; object-relative view label; confidence; and the source of each value. Label values as **known**, **estimated**, or **requested but unverified**.

Known renderer matrices are stronger evidence than a text label. Camera estimation is a guess informed by pixels. Object symmetry can make several answers equally plausible. “Unknown” must be a valid outcome rather than silently substituting zero degrees or a default FOV.

### Depth Anything 3 is the first estimator to evaluate

The inspected native Comfy node supports joint multiview processing for Small/Base and returns camera matrices with depth and optional confidence. The local node file was hash-identical to the fetched upstream file during this research. This proves source availability, not that weights are installed or that the current process has loaded the node.

The two permissive variants are especially relevant to a local commercial-friendly lane. Larger DA3 variants have different terms; do not apply the Small/Base license to the whole family. Mono/Metric variants also do not become multiview pose estimators merely because their depth is good. [Official family](https://github.com/ByteDance-Seed/Depth-Anything-3), [paper](https://arxiv.org/abs/2511.10647).

A required integration test is to check the pixel coordinate system of returned intrinsics against the model's resized input and the node's restored output size. The node has fallback matrices for missing outputs; those must not be accepted as successful calibration. This is an identified test requirement, not a declared bug without executing the corresponding path.

### Other camera candidates

| Candidate | What it actually estimates or requires | Decision |
|---|---|---|
| MoGe-2 | Single-view geometry/intrinsics; already used for FOV | Keep for its established role; do not rename it full multiview calibration. |
| Orient Anything V2 | Absolute/relative orientation and symmetry-related outputs; not complete K/FOV/translation | Useful comparison for object orientation; checkpoint lineage/rights and local memory still need clarification. |
| VGGT / Pi3 | Joint geometric/camera predictions from images | Relevant, especially inside newer reconstruction systems. Check the exact checkpoint and inherited license; inspect failure behavior on AI contradictions. |
| COLMAP | Feature matching, geometric verification, pose optimization from overlapping views | Useful independent check when texture/overlap supports it. Sparse smooth toys and nonoverlapping generated views can fail even when reasonable. |
| OpenCV PnP | Known 3D points, corresponding 2D landmarks and camera intrinsics | Strong deterministic building block when those prerequisites exist. Not a universal angle recognizer. |
| Cuboid/primitive fitting | Edges, landmarks, vanishing directions and explicit shape assumptions | Promising for rigid props/buildings; unsuitable as the only shape model for a dinosaur. |

Orient Anything V2's actual source predicts orientation distributions and handles pairs; a roughly 5 GB checkpoint file is not its total VRAM requirement. The README's two checkpoint identifiers differ, and full training-pipeline availability was incomplete in the inspected release. Record that uncertainty before relying on it. [Repository](https://github.com/SpatialVision/Orient-Anything-V2), [paper](https://arxiv.org/abs/2601.05573).

Brian's “break it into boxes” idea has concrete precedents. CubeSLAM forms and scores cuboid proposals from image detections and edges. CenterPose uses predicted object-box landmarks with PnP, but its released classes and licensing do not provide a general commercial-ready detector for all our assets. These methods justify a category-limited fitting experiment; they do not establish a general single-image solution. [CubeSLAM](https://github.com/shichaoy/cube_slam), [CenterPose](https://github.com/NVlabs/CenterPose), [OpenCV PnP](https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html).

### A custom fitter could be ordinary software, without training

Given an approximate mesh and reliable image masks/landmarks, optimize camera parameters and a small set of shape parameters to reduce rendered mismatch. Start with camera-only fitting so the solver cannot hide a bad camera by deforming the object. Use multiple starting angles, symmetry-aware alternatives and held-out views. Add limited shape adjustment only after camera behavior is established.

PyTorch3D publishes a camera-position optimization tutorial using differentiable rendering. Kaolin publishes differentiable camera examples, although the particular example inspected optimizes against a target camera matrix rather than proving image-based recovery. These are reusable mechanisms with clear prerequisites. A good fit to silhouettes alone cannot recover invisible concavities or guarantee a correct back. [PyTorch3D example](https://pytorch3d.org/tutorials/camera_position_optimization_with_differentiable_rendering), [Kaolin camera example](https://github.com/NVIDIAGameWorks/kaolin/blob/master/examples/recipes/camera/cameras_differentiable.py).

## 5. Image models: separate recipes behind one understandable interface

Keep a common user experience and a common camera/reference record. Keep **learned adapters, encoders, reference order, samplers and prompt assembly specific to the model and checkpoint**. A shared Comfy node interface is possible; universal compatible adapter weights are not established.

| Family | Useful role | Actual control evidence | Caveat and recommendation |
|---|---|---|---|
| Klein 4B | Practical permissive design/edit/structure lane | RefControl depth adapter combines structure and appearance references | First structural-control candidate to compare locally. Domain coverage and generated-view camera accuracy remain unproven. |
| Qwen Edit 2511 | Image editing and reference-conditioned angle variation | fal Multiple-Angles LoRA; concrete Edit/Lightning graph | Good alternate editing/view lane. A learned angle vocabulary is not exact numeric calibration. Camera LoRA remains optional. |
| Qwen 2.1 | Detailed image/reference work; AnyAngle and Fun controls | AnyAngle rough-RGB-plus-original; Fun Union structural network | Keep optional with commercial-use conditions. Test each route separately before stacking adapters. |
| Klein 9B | Higher-capacity edit/control option | RefControl normal and pose routes; UltraTex texture research | Keep with explicit model-operation/output license distinction and measured memory. Do not substitute 9B adapters into 4B. |
| FLUX 3 | Initial design and multi-reference editing | Released image/reference family and official Comfy recipe | Keep for its strengths; no verified exact-camera structural adapter in this research justifies making it the default guided-view engine. |

The prior register contains the exact graphs/cards and pins. Settings below are observations from those sources, not a claim that they are optimal on Brian's GPU.

- Klein 4B RefControl depth's inspected example uses the base model, separate depth/reference latents, 1024-square images, 20 steps and CFG 5. General card guidance differs. Preserve the chosen complete recipe instead of borrowing a sampler from another model.
- Klein 9B normal's preparation uses DSINE-style normals; the pose example uses DWPose. Renderer normals need matching axes, channel ranges and background conventions. A skeleton map is articulation control, not object camera calibration.
- The inspected Qwen Edit 2511 Multiple-Angles graph uses Edit-specific encoding with Lightning, four steps, CFG 1 and additional sampling/normalization nodes. Those are not generic settings for Qwen 2.1.
- AnyAngle's documented setup uses its specific two-image roles, approximately strength 1, CFG 3 and 20 or more steps. The T8 graph/source audit adds a valuable warning: original image first, coarse image second, with the author's counterintuitive trigger wording. Do not silently swap these roles because the text sounds more natural.
- Qwen 2.1 Fun Union is a substantial structural-control network, not a tiny interchangeable LoRA. Its inspected example uses CFG 1 and 40 steps. Combining its map control with AnyAngle/reference conditioning is a hypothesis requiring a bounded comparison, not a documented guaranteed stack.
- FLUX 3 base/distilled settings and guidance differ. The official card and a Comfy template also differ slightly in example step count. Surface model-aware defaults and actual saved parameters rather than a single “Flux CFG” rule.

Sources: [RefControl](https://github.com/thedeoxen/refcontrol), [fal camera LoRA](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA), [AnyAngle](https://huggingface.co/lilylilith/QI_2.1_AnyAngle), [Fun Union](https://huggingface.co/alibaba-pai/Qwen-Image-2.1-Fun-Controlnet-Union), [T8 actual graph](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/main/workflows/AnyAngle-Studio-Qwen21.json), [FLUX 3](https://huggingface.co/black-forest-labs/flux-3-image-klein).

### What prompt enhancement should do

Maintain one approved design description and compile it for the selected model and task. The enhancer must preserve requested parts and distinguish visible evidence from invented hidden details. It should not casually change proportions, add a pedestal, or substitute a more cinematic composition for an asset reference. A model-specific recipe then adds its supported reference syntax, view request, background/lighting instructions and protected design facts.

CFG and steps can change adherence and artifacts, but they cannot supply missing calibration or turn an ordinary image reference into a trained depth input. Seed controls reproducibility, not cross-view geometric identity. Store the actual seed for each result; do not claim that reusing the initial seed locks the same object across poses.

### A small asset-category menu is justified, with limited claims

Recommended user-facing categories are **Props & parts**, **Characters & creatures**, **Vehicles**, and **Buildings & structures**, plus **Automatic**. These are product recommendations, not official universal model categories.

Categories should select relevant constraints and tests: articulated pose preservation for characters; wheel/axle count and bilateral features for vehicles; planes, corners and door/window placement for buildings; handles, holes and thin parts for props. They should not automatically load a supposed “official buildings LoRA” that has not been found. Only create a separate learned branch when actual evidence justifies one. More prompt templates do not necessarily require more duplicated graphs.

## 6. Reconstruction systems that change the picture

There is active research on exactly this problem: combining reconstruction, camera estimation and generative completion instead of independently generating attractive images and hoping they agree. The important distinction is between **a convincing research direction** and **a released, licensed, Windows-compatible system that fits 16 GB**.

| Method | Contribution and inspected evidence | Why it is not automatically our new default |
|---|---|---|
| ReconViaGen v0.5 | Hybrid pipeline combines a VGGT-related coarse reconstruction stage with TRELLIS.2 and adaptive feature fusion. Actual pipeline and app loader inspected. | Published earlier-version memory figures are above 16 GB; v0.5 app initialization places several components on GPU. Exact derived checkpoint rights and peak memory need checking. |
| Mix3R | Joint reconstruction/generation with camera-related geometric information and transformer fusion. Released V2 uses more varied camera/render data than V1. Actual V2 loader inspected. | Example moves the pipeline to CUDA; no demonstrated 16 GB offload route found. No root license was found in the inspected tree, so reuse permission remains an open question. |
| RecGen3D, formerly UniRecGen | Geometric anchors plus generative mesh completion and a trained adapter/point encoder. Released code/config and license inspected. | Author tests use a 24 GB GPU/Linux. The released stack has restrictive upstream terms; reported full training uses multi-H800 compute over days. |
| UniForge3D | Geometry-guided TRELLIS.2 reconstruction, view selection and staging ideas | Useful architecture; derived weights/licensing and local hardware fit limit an immediate permissive deployment. |
| WorldSculpt | Pixal3D LoRA fine-tuning for occluded objects in multiview scenes; actual LoRA helper and scene launcher inspected | Requires calibrated scene transforms, instance masks and object boxes. It is not a universal camera estimator for our generated four-panel sheets. |
| UltraShape | Refines an initial mesh using image conditioning and a geometry representation | Promising direct geometry comparison. Conditional license, startup GPU peak and texture invalidation must be handled. |
| PartCrafter | Compositional generation of multiple mesh parts from an image and part count | Useful for modular parts, not a guarantee of correct joints/rigging. Inspected example includes a background-removal dependency and optional hosted Gemini helpers. |
| SPAR3D | Point-aware single-image reconstruction with an editable intermediate representation | Interesting comparison for local structured editing; full exact-stack/Windows proof was not completed here. Not enough evidence to replace the baseline. |

Primary sources: [ReconViaGen](https://github.com/GAP-LAB-CUHK-SZ/ReconViaGen), [Mix3R](https://github.com/jsnln/mix3r), [RecGen3D](https://github.com/zsh523/RecGen3D), [UniForge3D](https://github.com/xibushu/UniForge3D), [WorldSculpt](https://github.com/AlayaLab/WorldSculpt), [UltraShape](https://github.com/PKU-YuanGroup/UltraShape-1.0), [PartCrafter](https://github.com/wgsxm/PartCrafter), [SPAR3D](https://github.com/Stability-AI/stable-point-aware-3d).

### What we can learn without transplanting entire systems

**ReconViaGen:** reconstruction-derived structure and generation can complement each other. But the inspected adaptive fusion is an algorithmic selection/weighting mechanism, not proof that the model has perfect visibility knowledge. A pipeline's low-memory flag does not by itself fix a demo that initially loads all major stages onto GPU.

**Mix3R:** the authors distinguish a V1 trained on about 400,000 fixed-look-at TRELLIS renders from a recommended V2 using about 200,000 Blender/PBR renders with more varied camera orientation. This directly supports testing realistic camera variation rather than training only eight clean captions around perfect objects. It does not establish that our small adapter can reproduce their results.

**WorldSculpt:** the saved helper loads a base denoiser, wraps target modules through PEFT, freezes base parameters and exposes LoRA parameters to the optimizer. This is a real way to adapt a mesh generator. Its scene script explicitly checks for transforms, masks and fine-tuned checkpoint files. `SS_STEP=15000` and `SHAPE_STEP=15000` select checkpoint iterations; they are not instructions to sample for 15,000 steps. The method's success depends on its inputs and training distribution. [Published paper](https://arxiv.org/abs/2609.05416).

**ComfyColab's experimental Pixal3D/VGGT bridge:** actual source uses depth/confidence information and camera-center alignment to canonical cameras. The inspected path still projects using specified canonical camera labels. It does not magically replace wrong view labels with recovered true poses. It is a useful experimental fusion example with a limited author result, not proof that our camera mismatch is solved. [Inspected adapter](https://github.com/DragonLord1998/ComfyColab/blob/main/worker/pixal3d/vggt_omega_adapter.py).

### Joint image generation and 3D feedback

MV-Adapter, OminiControl, and 3D-Adapter/MVEdit demonstrate mechanisms worth understanding: shared reference information, geometry-conditioned views, and 3D feedback during generation. Their released weights are not interchangeable with Klein/Qwen/FLUX 3. The inspected MV-Adapter deployment examples depend on SDXL/SD2.1, which Brian excluded. The faster reconstruction branch described by 3D-Adapter was not available as a ready local release in the inspected route; available examples also exceed our comfortable resource target.

Use these as architecture precedents, not excuses to introduce an unwanted image family. A future Klein-specific joint-view module would require compatible training and evaluation. A contact sheet assembled by ordinary prompting is not equivalent to a network trained with cross-view geometry. [MV-Adapter](https://github.com/huanngzh/MV-Adapter), [OminiControl](https://github.com/Yuanshi9815/OminiControl), [MVEdit](https://github.com/Lakonik/MVEdit).

## 7. Improvements after the first reconstruction

### Background removal belongs in every path, with review

Provide a mask for every image passed to reconstruction, including uploads, generated images and contact-sheet panels. Preserve the source RGB and original frame; background removal should not secretly recenter or zoom different views. If valid alpha already exists, use it. Show the cutout so a user can catch a missing handle, transparent region, hair strand or hole.

BiRefNet is a practical permissive candidate already familiar to these ecosystems. BRIA model versions have separate terms and should not be silently treated as MIT just because a wrapper is open source. A segmentation model's failure can remove the very geometric evidence we are trying to preserve. Keep the existing mask editor as the correction path. [BiRefNet](https://github.com/ZhengPeng7/BiRefNet), [BRIA RMBG 2.0 card](https://huggingface.co/briaai/RMBG-2.0).

### Separate shape refinement from cosmetic improvement

| Control or operation | What it can change | What it cannot promise |
|---|---|---|
| Sparse-structure resolution/steps/guidance | Coarse occupied volume and the sampling process | Correct missing surfaces from contradictory evidence |
| Shape resolution/steps/guidance | Surface-detail capacity and conditioning behavior | Monotonically better geometry when increased |
| Decoder chunking/token budget | Peak memory and computational workload; sometimes quality trade-offs | A physical measurement or simple universal quality percentage |
| Geometry refinement | Actual vertex/surface shape | Recovery of unsupported details without inference |
| Normal smoothing | Shading normals | Removing bumps from the actual vertex positions |
| Decimation/face budget | Complexity and export/runtime cost | Preservation of arbitrarily thin structures at any budget |
| Remeshing | Tessellation, sometimes topology and surface regularity | Automatically suitable animation topology or printability |
| Texture generation/baking | Appearance on the current surface | Correcting wrong dimensions or joints |

Expose useful advanced controls with model-specific explanations, recommended defaults and reset buttons. Keep a high-detail master and derived game/print versions. Do not present “1M polygons” as a quality requirement for every prop or use a high resolution as compensation for incorrect cameras.

### UltraShape is a worthwhile conditional comparison

The actual inference code accepts an initial mesh, samples its surface, normalizes it, and refines geometry with image conditioning. The official low-memory path reduces latent count and decoder chunk size. However, the inspected startup constructs/moves major modules to GPU before later staging, so source claims of low memory require a startup-peak test on Brian's hardware.

The community Comfy example is a real graph: native Hunyuan generation feeds an UltraShape refinement node and mesh export. It is not demonstrated Pixal3D integration, nor proof that a community node cooperates with Comfy's model offloading. A Pixal-compatible comparison therefore needs an explicit mesh-coordinate/scale bridge and the same input image. Geometry changes invalidate old UV correspondence; retexture or rebake afterward. [Official refinement code](https://github.com/PKU-YuanGroup/UltraShape-1.0/blob/main/scripts/infer_dit_refine.py), [community integration](https://github.com/Hahihula/comfyui-ultrashape).

For ordinary props, camera correction and modest geometry fitting may be cheaper and easier to license. UltraShape is an optional experiment, not a prerequisite for the next usable Mumblebox iteration.

### Texturing is a separate improvement lane

UltraTex is relevant because it generates surface-consistent PBR appearance using geometric buffers and specialized multiview conditioning. The actual published route uses Klein 9B and trained components; a generic 4B code branch is not proof of a released equivalent 4B adapter. It can improve material coherence on a mesh. It cannot correct a wrong mesh silhouette. Keep texturing after geometry selection and test it separately from reconstruction. [UltraTex](https://github.com/yiboz2001/UltraTex), [Comfy integration](https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes).

### Game and print exports need different checks

For a game asset, evaluate silhouette at its expected screen size, triangle budget, material count, texture resolution, UV validity, scale/orientation and import behavior. A textured GLB is not automatically a production-ready animated character.

For a print asset, evaluate physical dimensions, connected components, watertightness where required, self-intersection, wall thickness and unsupported thin pieces. Filling every hole can destroy intended handles or vents. Texture quality does not make a surface printable. These checks can be automated in part, but the UI should report what was measured and what still needs review.

## 8. NVIDIA technologies and other libraries worth combining

Brian's idea is sound: Comfy can orchestrate several specialized tools while presenting one simple experience. The contribution should be precise. A renderer produces structural evidence; a camera solver fits projection; a trained image model supplies appearance/completion; a mesh generator reconstructs; an export stage prepares deliverables. They must agree on coordinates, masks, dimensions and memory ownership.

| Technology | Practical contribution to this project | Recommended treatment |
|---|---|---|
| NVIDIA Kaolin | Camera representations, geometry operations, differentiable rendering interfaces and surface extraction | Serious building-block candidate for a custom fitting/refinement experiment. Current default library is Apache 2.0; inspect optional backends separately. |
| Kaolin FlexiCubes | Differentiable extraction of a mesh from a scalar field | Useful if optimizing an SDF/volume. Not a filter that automatically fixes any existing triangle mesh; conversion and objective are required. Current inspected implementation is Apache 2.0. |
| NVIDIA Warp | Python-authored GPU kernels, spatial queries and differentiable computation | Possible way to accelerate a demonstrated geometry bottleneck. Avoid inventing kernels before profiling existing implementations. |
| NVIDIA nvdiffrast / nvdiffrec | Efficient differentiable rasterization; inverse-rendering research | Strong methodological precedent, but inspected nvdiffrast terms are noncommercial research/evaluation. Do not put it on a blanket permissive list. |
| Omniverse Replicator | Labeled synthetic data and controlled cameras/materials | Relevant if training requires large varied renders. Blender/procedural rendering may be simpler for the first owned-data pilot. Asset and platform rights still matter. |
| TensorRT / related inference tooling | Optimized supported inference graphs | Later targeted optimization after identifying a stable expensive component. Engine building, dynamic shapes, changing LoRAs and version compatibility add costs. |
| FoundationPose / CenterPose | Pose-estimation research and implementations | Useful for their prerequisites and supported domains; not a drop-in arbitrary AI-image camera solution. |
| DLSS family | Real-time image reconstruction/rendering appearance | Potential preview research, not the primary route to accurate exported geometry. See below. |
| OpenCV / SciPy | PnP, robust fitting, least-squares optimization and deterministic geometry calculations | Prefer established functions for small custom camera/primitive tools. |
| PyTorch3D / Open3D / trimesh | Differentiable-rendering examples, mesh analysis and geometric data handling | Evaluate the particular function/license and Windows build. Do not install three competing geometry stacks without need. |

Primary references: [Kaolin](https://github.com/NVIDIAGameWorks/kaolin), [FlexiCubes source](https://github.com/NVIDIAGameWorks/kaolin/blob/master/kaolin/ops/conversions/flexicubes/flexicubes.py), [Warp](https://github.com/NVIDIA/warp), [nvdiffrast](https://github.com/NVlabs/nvdiffrast), [nvdiffrec](https://github.com/NVlabs/nvdiffrec), [Replicator](https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html), [TensorRT](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/quick-start-guide.html), [FoundationPose](https://github.com/NVlabs/FoundationPose), [OpenCV](https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html), [PyTorch3D](https://pytorch3d.org/), [Open3D](https://www.open3d.org/), [trimesh](https://trimesh.org/).

The live NVIDIA skill catalog was checked. It contains Warp-specific optimization/gradient tools, but no exact skill was needed to replace the direct camera/rendering source inspection. No skills or SDKs were installed during this research.

### DLSS: useful distinction, limited direct benefit here

**Super Resolution / DLAA** reconstruct or antialias displayed images using renderer-supplied information and temporal state. **Ray Reconstruction** addresses noisy ray-traced imagery using material/geometry-related inputs. **Frame Generation** generates intermediate display frames. None of those outputs supplies additional measured viewpoints of the object. Generated display frames should not be fed to reconstruction as new geometric evidence. [Official DLSS overview](https://developer.nvidia.com/rtx/dlss), [Streamline programming guides](https://github.com/NVIDIA-RTX/Streamline/tree/main/docs).

**DLSS 5 Neural Rendering** is closer to Brian's idea conceptually: NVIDIA describes geometry-aware, temporally coherent neural appearance enhancement. Its public description uses rendered frames, motion information and controls. That demonstrates the value of grounding image generation in a renderer, but does not establish a general Python image-to-mesh adapter or a way to recover unseen topology. The full paper was not successfully retrieved in this pass; claims here are limited to the official page and inspected sample. [NVIDIA research description](https://research.nvidia.com/labs/adlr/DLSS5/).

The current `vk_gltf_renderer` source includes a Neural Rendering branch that requires a beta NGX SDK. Its documentation expects clean rendered inputs and renderer buffers; this is not a generic “send any PNG to DLSS” interface. A public sample does not prove unrestricted SDK access or compatibility with every 16 GB GPU. DLSS binaries have their own license even when surrounding integration code is open. [Renderer source](https://github.com/nvpro-samples/vk_gltf_renderer/blob/main/src/dlss.hpp), [denoising documentation](https://github.com/nvpro-samples/vk_gltf_renderer/blob/main/docs/denoising.md), [DLSS license](https://github.com/NVIDIA/DLSS/blob/main/LICENSE.txt).

For our structural guide images, ordinary GPU rasterization with exact matrices is the simpler first choice. Do not run depth, normal, position or mask measurements through a beauty enhancer. For a later attractive preview, rendering/denoising technologies can be evaluated independently. They must not obscure the untextured mesh review.

### Python versus Rust/C++/CUDA

Comfy orchestration and PyTorch adapters naturally fit Python. The heavy computation already runs in compiled GPU kernels. Rewriting the surrounding code in Rust does not automatically accelerate diffusion or sparse mesh inference. Use Rust/C++ for a measured CPU-bound service or packaging need; use CUDA/Warp/Triton only when a relevant kernel is actually missing or slow. A small Python node calling an established accelerated library is often the most maintainable result.

## 9. Custom work: what is practical, what needs training, and what is genuinely experimental

There is no reason to rule out custom work. There is also no reason to begin by training a large new model when a camera contract or a small solver could solve the actual failure. The following proposals are ranked by what we can learn for the least cost.

### Proposal A — Camera and framing reconciliation

**Gap:** generated images do not obey their nominal camera labels, and preprocessing can change apparent framing.

**Mechanism:** preserve image transforms; obtain candidate intrinsics/extrinsics from an estimator; fit a camera to reliable draft-mesh landmarks or silhouettes; reject or flag ambiguous fits. Return a camera record and a diagnostic overlay, rather than silently rewriting the image.

**Reusable pieces:** native DA3, existing Comfy rendering, OpenCV PnP/robust fitting, established optimizers, optional Kaolin/PyTorch3D components where compatible. No model training is required to attempt the fitting stage.

**Limits:** a wrong draft can bias the fit. Symmetry, sparse overlap, textureless objects and missing geometry can make pose unidentifiable. Optimizing camera and arbitrary shape together can explain away errors. Start camera-only, preserve alternatives, and compare known-camera renders.

**Smallest decisive experiment:** render several owned asymmetric objects with known cameras, alter framing and camera labels deliberately, and ask the candidate to recover usable cameras. Then test actual generated views separately. Pass only if reconstruction improves and the estimator does not confidently bless known contradictory images. See validation stages V1–V3.

### Proposal B — Structure-plus-identity adapter for Klein 4B

**Gap:** an existing model changes the angle but distorts proportions or copies defects from a proxy.

**Mechanism:** fine-tune a small LoRA against paired examples: clean appearance reference(s), a target-camera structure map from a rough proxy, and the correct target render from the original mesh. Vary proxy defects and control strength so training does not merely teach “copy the imperfect render.” A silhouette/depth map carries camera-relative structure; image references carry appearance. They remain correlated, not mathematically independent channels.

**Precedent and reusable pieces:** RefControl demonstrates structure/reference conditioning. Musubi's actual Klein training forward path packs multiple control-image latents alongside the noisy target, calls the transformer, and trains the target-token prediction. It is not merely an inference demo. The code already has compatible LoRA/training machinery; adding a dataset/config is a smaller first experiment than inventing a new transformer. [Musubi Klein training](https://github.com/kohya-ss/musubi-tuner/blob/main/src/musubi_tuner/flux_2_train_network.py), [training guidance](https://github.com/kohya-ss/musubi-tuner/blob/main/docs/flux_2.md), [AI Toolkit](https://github.com/ostris/ai-toolkit).

**What must be built:** licensed render-pair preparation, explicit reference ordering, matched control formats, proxy perturbations, object-disjoint splits and evaluation. A numeric camera embedding or new cross-view loss is additional model code; ordinary angle captions do not automatically implement those mechanisms.

**Feasibility:** plausible enough for a bounded local memory pilot, not proven to fit 16 GB at useful resolution. Freeze the base, cache text/latents, use a supported quantized base and offload/checkpointing options. Test quality against the existing adapter. Small trainable weights do not mean small activations or a free text encoder.

**Smallest decisive experiment:** one restricted domain, such as asymmetric rigid props; approximately 100 owned/procedural base shapes divided by object family into training/validation/test; an initial 512-resolution, two-reference, batch-one configuration; a short stability/memory run before a capped pilot. Those numbers are proposed starting bounds, not a research finding or a promise of sufficient data. Promote only for held-out camera/proportion improvement that survives reconstruction.

### Proposal C — Pixal3D geometry adapter

**Gap:** even with trustworthy image/camera inputs, the mesh generator systematically rounds hard surfaces, loses thin structures or struggles with a repeatable category.

**Mechanism:** adapt selected sparse-structure/shape denoiser modules on licensed multiview renders with ground-truth geometry. Preserve the base's useful general knowledge while teaching a narrow class of geometric failures. Appearance-only training would not directly supervise the desired mesh change.

**Precedent:** WorldSculpt actually applies PEFT LoRA to Pixal3D denoisers. RecGen3D shows a different reconstruction-conditioned adaptation strategy. These establish that mesh-model adaptation is practical engineering, not proof that a small home-trained adapter will generalize to everything.

**Requirements:** compatible base/adapter terms; geometry latent preparation and camera conventions; a reproducible trainer/config; quality tests on unseen geometry; measured activation and feature-encoder memory. The WorldSculpt single-image helper file and calibrated-scene launcher serve different paths—do not mistake an easy single-image CLI for its complete multiview fine-tuned system.

**Smallest decisive experiment:** one geometric failure class with a fixed, correct camera set; compare base and adapter on unseen meshes using geometry metrics. Defer this until image/camera plumbing passes, otherwise training may compensate for a software error. Exact 16 GB training feasibility remains an explicit follow-up question.

### Proposal D — Joint views or a persistent 3D representation during image generation

**Gap:** independently generated views still disagree even with structure guidance.

**Possible mechanism:** a trainable camera embedding, cross-view attention or a shared 3D/surface-feature representation lets target views consult common geometry. Project visible surface features into each camera, mask occluded regions and separate observed appearance from generated completion. The intended advantage is agreement through a shared object representation, not a long textual instruction to “be consistent.”

**Precedent:** MV-Adapter, OminiControl, Mix3R, reconstruction-guided methods and NVIDIA's geometry-grounded rendering research support parts of this idea. Their specific models and weights do not establish this combined Klein/Qwen design.

**Evidence status:** a proposed combination, with potentially original engineering and training work. This report does not claim novelty relative to all literature or patent clearance.

**Smallest decisive experiment:** first prove that an existing shared geometric representation improves two held-out views over independent reference conditioning. If it cannot, do not scale to eight views, more categories or a larger GPU budget. This is a later research prototype, not a required feature for the next working iteration.

**A particularly relevant camera-token precedent:** *Camera Control for Text-to-Image Generation via Learning Viewpoint Tokens* (CVPR 2026) trains a small camera-parameter encoder alongside an image generator. It explicitly targets the weakness of natural-language angles. Its fixed-focal-length, zero-roll setup is narrower than a universal camera model, and its text-to-image task does not establish identity-preserving novel views of an uploaded object. [Paper](https://arxiv.org/html/2604.19954v1).

The released code includes an MLP with sinusoidal parameter encoding, several camera parameterizations, and SD3 training code using PEFT. Its available backbones are Harmon, SD2.1 and SD3.5—not a ready Klein/Qwen adapter. The inspected Harmon config also illustrates why executable values matter more than comments: comments describe frozen components while current learning-rate/freeze values differ. A port must train the compatible embedding interface and image-model response; copying the small MLP alone would not confer camera understanding. The repository license is CC BY 4.0, with separate backbone and augmented-data rights to check. This makes explicit camera-token conditioning a concrete later alternative to map-only guidance, without adopting an excluded backbone. [Code and configurations](https://github.com/Randdl/viewtoken_control).

### Proposal E — Independent replacement of a restrictive component

For a uniquely useful component, write an input/output specification from public papers and permitted documentation, choose allowed dependencies, implement independently, and compare against a lawful reference or published benchmark. REA can help where permitted binary/runtime analysis is genuinely needed; complete source analysis is usually better served by normal code tools. No binary reverse engineering was necessary in this research.

An independent implementation can replace code. It does not relicense someone else's weights, dataset, SDK or restricted teacher outputs. A learned replacement may require training again on permitted data. Review the applicable agreement before choosing a reverse-engineering method; some inspected components expressly prohibit it. The distinction between an algorithm and protected implementation is real, but not blanket clearance of contracts or patents. [US Copyright Office explanation of computer programs](https://www.copyright.gov/circs/circ61.pdf).

Prefer an existing permissive component whenever it meets the need. A custom replacement is justified by a measurable missing capability, not simply because a library's marketing sounds important.

## 10. Data and training without a data center

### Brian's angle-labeled dataset idea

Yes, renders with accurate camera labels are relevant. A caption saying “rear-left, 45 degrees” can help a model learn the vocabulary. But captions alone do not guarantee accurate camera response, preserve an object's dimensions, or separate pose from identity. The strongest training data also contains the actual camera matrices, reference/target pairing, masks and geometric control maps.

If a camera adapter is the goal, randomize objects, textures and lighting so that angle is not accidentally associated with one appearance. Include nearby continuous angles, elevations, focal lengths and framing—not only eight fixed captions. For people, separate camera movement from joint articulation, and include a canonical pose task before asking the model to change both simultaneously.

Useful public leads include Objaverse-derived multiview sets, GObjaverse and TexVerse. TexVerse's pipeline records PBR/geometry buffers and camera information; its large corpus is not a reason to download everything. Dataset-level code or metadata licensing does not override the source assets' individual rights. [GObjaverse](https://github.com/modelscope/richdreamer/blob/main/dataset/gobjaverse/README.md), [TexVerse](https://huggingface.co/datasets/YiboZhang2001/G-buffer-TexVerse), [Objaverse](https://objaverse.allenai.org/).

The lowest-friction starting data is owned procedural geometry and clearly licensed assets. Render in Blender or another permitted engine. Keep scale, camera matrices, normal convention, masks, object IDs and provenance. Split by object and near-duplicate family, not by image: putting different angles of the same model in train and test would inflate the result.

### Rough-guide training must resemble the real problem

A perfect target depth render paired with a perfect target image only teaches the easy case. Include plausible proxy errors: coarse tessellation, softened edges, missing small parts, mild camera error, partial geometry and incomplete appearance. Use the correct target from the clean mesh. Also test a deliberately too-wrong proxy to establish when guidance should be refused or weakened.

Do not train the model to ignore all geometry to avoid proxy defects; that would throw away the desired camera control. Evaluate both adherence and correction. Hold out entire shapes and styles to distinguish useful learning from memorization.

### Local training is plausible, not yet demonstrated

Musubi documents Klein-specific text encoders, caching, quantization and block-swapping options. The inspected training code supports multiple control references. AI Toolkit also contains a Klein-specific implementation. These are evidence that a compatible trainer exists; they are not evidence that a useful multi-reference configuration has already run on this Windows machine.

A 4-billion-parameter backbone at two bytes per parameter is about 8 billion bytes of weights before activations, the encoder, optimizer state, caches and temporary buffers. Freezing most weights substantially reduces trainable-state costs, but does not remove forward/backward activation memory. Quantization and offloading can trade speed for memory. A small measured pilot must settle the actual feasible resolution/reference count.

A published Klein multiview-completion example fine-tunes the full model for a robot wrist-camera task, using tens of thousands of training pairs and eight H200 GPUs for roughly ten hours. It demonstrates task-specific learning, not that a few hundred dollars or a tiny LoRA reproduces the result. Its target domain also differs from a free orbit around arbitrary game assets. [Released training card](https://huggingface.co/tennyyyin/flux2-klein-multiview-completion).

### Optional compute budget, only if local evidence justifies it

The target remains $0. No paid job was launched or authorized. At the checked Hugging Face Jobs rates, one L4 is $0.80/hour, one L40S $1.80/hour, and one 80 GB A100 $2.50/hour. Four hours of A100 runtime would therefore be $10 in listed compute; eight hours would be $20. That excludes any separately billed storage, services, taxes or extra retries. Prices and availability can change. [Current official pricing](https://huggingface.co/docs/hub/jobs-pricing).

Before suggesting rental: show the exact local memory/throughput limit, validate the dataset and loss on a tiny run, estimate required steps from measured throughput, and define a timeout and spending cap. A possible later $25–$50 pilot is a bounded experiment, not a promise of a finished general-purpose adapter. Data quality and objective design may matter more than a larger card.

## 11. A visual model can help plan, but it cannot see the unseen

A local VLM can produce an **asset description record** with three distinct sections:

- Visible facts: “one round lens protrudes from the front; yellow handle above the body.”
- Proposed hidden design: “the back has a flat battery door; the left side continues the blue casing.”
- Uncertainty: “the image does not show whether there is a second side grip.”

Brian approves the proposed design. Every later image recipe receives the same approved facts and object-relative side definitions. This is useful for a beacon, creature or building because the record is not limited to one object class. It cannot establish the true unseen backside of an existing real object. References or human decisions remain necessary where exact hidden features matter.

Qwen3-VL 4B is a plausible staged local analysis/enhancement candidate with Apache licensing, separate from the image model family. It must unload before the image model/mesh stage. The enhancer should compile model-specific text from the approved record, not continually redesign the asset. [Official model](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct).

Recent evaluation cautions against treating a VLM's fluent explanation as geometric verification. A 2026 study of six VLMs on synthetic scenes found weaknesses around occlusion and other 3D reasoning; its particular models/scenes do not directly benchmark our proposed 4B helper. Similarly, 3D-consistency research shows learned reconstruction models can assign plausible geometry even to inconsistent inputs. Neither a VLM verdict nor a high reconstruction confidence is enough by itself. [VLM evaluation](https://arxiv.org/html/2605.20448v1), [3D-consistency study](https://arxiv.org/html/2605.18754v1).

Use helpers to identify likely problems and explain them. Test them against deliberately duplicated, mirrored, wrongly labeled and structurally contradictory views. For real users, an inconclusive result should invite review, not lock the workflow behind an unreliable automatic judge.

## 12. Memory and speed are part of correctness

On this machine, every major stage must have a clearly owned lifetime. “Unload” must release the actual model references and live tensors; emptying an allocator cache cannot free objects that another owner still holds. Use the existing lifecycle owner instead of adding parallel cleanup helpers.

| Stage | Resident work | What should leave before the next expensive stage |
|---|---|---|
| Describe/enhance | VLM/text components and small images | VLM weights and temporary attention/cache state |
| Generate/edit images | Selected image model, required encoder/VAE and compatible adapters | Encoder after cached encoding where supported; then image model and adapter tensors before mesh generation |
| Mask / estimate cameras | Segmentation or geometry estimator, one bounded batch | Helper weights, features and intermediate images once records are saved |
| Reconstruct geometry | Current sparse/shape stage and necessary feature extractor | Previous stage weights and features not needed later |
| Refine geometry | Only the chosen refiner/fitter and required image/mesh data | Refiner before texturing/export |
| Texture / bake / finish | Current texture model or GPU mesh-finishing stage | All diffusion models when only geometric export remains |
| Idle / cancelled / failed | User files and small UI state | GPU models, large tensor caches and abandoned temporary state |

Measure startup peaks as well as sampling peaks. ReconViaGen and UltraShape source show why a nominal low-memory option is not enough: a loader can exceed the budget before its offload logic becomes useful. View count, image size, feature tokens, sparse occupied volume and UV/texture size all affect memory differently.

Make the 16 GB profile adaptive to actual free memory, with a user-set reserve and truthful trade-offs. A reserve is not a hard sandbox: an external app can consume VRAM later. Keep a conservative default, allow adjustment, and report the selected effective settings. Do not claim an untested 8 GB profile from a 16 GB card with an arbitrary numeric limit.

For system RAM, retain only the active stage's necessary CPU copies, avoid duplicating model caches across apps, bound reference-image/feature caches, and delete temporary intermediates according to a scoped manifest. Never clear arbitrary shared cache directories or delete user history to reclaim memory.

Keep GPU finishing mandatory for the selected path. Record device, elapsed time, peak allocated/reserved VRAM, process RAM and stage transitions. If a GPU exporter fails, show the error and preserve the mesh/state; do not silently launch the extremely slow CPU route Brian rejected.

## 13. Licensing and independent implementation

This is an engineering selection summary, not blanket clearance for every commercial situation. Pin the exact versions and show the underlying terms. The app being free does not by itself make all its model uses noncommercial. An intermediate image being turned into a mesh does not remove upstream conditions.

| Component | Finding at the checked version | Practical UI/deployment treatment |
|---|---|---|
| Qwen Edit 2511 | Apache 2.0 | Commercial use allowed under its terms; still retain notices and audit other components. |
| Klein 4B | Apache 2.0 | Preferred permissive image/control baseline. Check each adapter's own terms. |
| Qwen 2.1 and dependent AnyAngle/Fun routes | Research license; commercial model use requires separate permission from Qwen | Optional lane: “Commercial use has conditions,” link terms and the official request route. |
| Klein 9B | Noncommercial/nonproduction model-use terms; outputs are separately addressed and may be used commercially subject to the license | Explain model operation versus output rights. Do not label all outputs forbidden or the model universally free for commercial operation. |
| FLUX 3 image Klein | Kommunity terms, including eligibility/revenue conditions | Conditional commercial lane; show exact eligibility, not a generic Apache badge. |
| Pixal3D | Current inspected GitHub and HF license files are MIT | Correct stale earlier search results suggesting the current core is research-only. Still audit DINOv3/NAF/renderers and other dependencies. |
| TRELLIS.2 | MIT core | Same dependency distinction; no promise that every optional renderer/weight is MIT. |
| DA3 Small/Base | Apache 2.0 cards | Favor these for the first camera-helper comparison; larger family members differ. |
| DINOv3 | Custom license with redistribution/use conditions, including reverse-engineering restrictions | Preserve terms and gating; do not describe it as MIT or rewrite it as a way around its agreement. |
| VGGT | Original and commercial checkpoints have different terms | A separate commercial checkpoint does not automatically relicense a derived model trained from another checkpoint. Trace lineage. |
| UltraShape | Tencent Hunyuan 2.1 terms | Conditional option with territorial/scale/use obligations, not a universal permissive dependency. |
| Kaolin current default library / current FlexiCubes / Warp | Apache 2.0 at inspected paths | Useful building blocks; legacy noncommercial modules and optional dependencies remain distinct. |
| nvdiffrast | Inspected NVIDIA Source Code License limits use to noncommercial research/evaluation | Do not silently include in a commercial-friendly default; choose a permitted renderer or obtain suitable rights. |
| DLSS | Separate proprietary SDK/binary terms | Optional future rendering integration only after authorized access and compatibility are established. |

Primary terms: [Qwen Edit 2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), [Klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B), [Qwen 2.1](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE), [Klein 9B](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B/blob/main/LICENSE.md), [FLUX 3](https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md), [Pixal3D](https://huggingface.co/TencentARC/Pixal3D/blob/main/LICENSE), [TRELLIS.2](https://github.com/microsoft/TRELLIS.2), [DINOv3](https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m/blob/main/LICENSE.md), [VGGT commercial checkpoint](https://huggingface.co/facebook/VGGT-1B-Commercial/blob/main/LICENSE), [UltraShape license](https://github.com/PKU-YuanGroup/UltraShape-1.0/blob/main/LICENSE).

For Qwen 2.1, the checked license names `model-business@notice.qwencloud.com` for commercial licensing. FLUX 3's checked eligibility includes an annualized gross-revenue threshold of US$5 million with affiliate considerations; the full terms govern. UltraShape's checked Hunyuan 2.1 terms include excluded territories, a large-user-scale threshold and restrictions involving training other AI models from outputs. Those are meaningful product choices, not details to hide behind a download button.

Licenses can change. Record code, weights, adapters, encoders, renderer and data separately. A quantized checkpoint or a community wrapper does not automatically replace the base model's license. Likewise, a permissive new adapter cannot cleanse a restrictive base checkpoint or prohibited training data.

## 14. The complete next-iteration proposal

### Keep

Keep the current understandable UI, manual approval, mask editing on initial and angle images, per-image download/history, model-aware parameters, GPU export, local storage and resource controls. Keep the existing camera-guide and model-recipe owners. Preserve original images and the best mesh from each attempt.

### Repair or prove

Prove the complete image-to-camera contract, including panel extraction, crop/pad transforms, reference ordering, FOV units, axis conventions, native cardinal slots versus custom matrices, and object-relative left/right. Prove that switching design/history resets stale dependent views and that failed or cancelled stages release resources. These are proportional checks of an established implementation, not permission for an unrelated interface redesign.

### Add only where the comparison earns it

First add a trustworthy camera-estimation/diagnostic bridge if DA3 Small/Base passes the known-camera and contradiction tests. Add model-specific structural guidance only through the already identified trained recipes. Then evaluate one selected geometry-improvement route: a small deterministic fitter first, or a conditional direct refiner if evidence justifies it. A trained adapter is a later response to a measured persistent gap.

### Recommended user flow

1. Describe/upload the object; optionally add reference images with clear purposes. Choose an image model, with plain-language strengths and license information.
2. Approve a useful initial image. A three-quarter view often exposes more shape than head-on, but it is not mandatory or guaranteed; retain user uploads and evaluate the subject.
3. If additional evidence is useful, generate/approve the opposite view or other chosen views. Preserve their frames and estimate/check cameras. Explain contradictions in plain language.
4. Make the baseline mesh from the cleanest supported evidence. Review its untextured shape as well as its appearance.
5. Offer optional guided improvement only when the baseline has a specific correctable weakness. Render compatible depth/normal/silhouette guides from a shared rig, preserve appearance references, and regenerate selected views. Compare the new reconstruction with the retained baseline.
6. Select geometry, texture if desired, and export a master plus the requested game/print derivative. Keep images, cameras, parameters and versions with history.

The user should not have to understand matrix algebra. The software must keep that information correct behind the scenes. A concise warning such as “These two views disagree about the handle position” is more useful than a mysterious confidence score.

### Fallback

If generated multiview cameras remain unreliable, keep the best single-image reconstruction or a smaller clearly consistent subset. Do not force a complicated two-pass loop. Offer precise local editing or a category-limited geometric adjustment where supported. Preserve the result for Blender rather than repeatedly degrading it in pursuit of more images.

### What “done” should mean for the next implementation

The next implementation is ready for Brian to use when the fixed validation set has completed, camera plumbing passes, at least one clearly described route produces useful meshes across varied subjects, the optional improvement path is promoted or explicitly rejected by its measured result, and save/reload/export/cancellation/resource behavior passes. It does not require every model to produce every view perfectly.

The companion validation plan defines numeric gates, run caps, category failures and stop conditions. Those thresholds are proposed engineering acceptance criteria, not accuracy levels promised by a paper. Stop for review after that finite comparison instead of adding another adapter whenever a difficult object fails.

## 15. What remains uncertain

The largest unanswered questions now require **experiments**, not another general web search:

- Does native DA3 Small/Base produce useful camera estimates for our generated, segmented object views, and are resized intrinsics carried correctly into Pixal3D?
- Does correcting the exact AnyAngle reference ordering materially improve our objects, or only the author's demonstration?
- Does Klein 4B depth guidance improve reconstructed geometry after accounting for draft-mesh errors?
- Does a deterministic camera/limited-shape fitter or a direct learned refiner improve the same baseline mesh without destroying small features?
- Which exact configurations fit 16 GB at startup, inference and export, and release memory after failure?
- If the existing approaches plateau, can a small owned-data adapter beat them on unseen objects at acceptable local cost?

Licensing lineage, Windows packaging and unavailable checkpoints still have reading/clarification tasks, but they should not block evaluation of the already permissible candidates. The [follow-up plan](FOLLOW-UP-RESEARCH.md) gives each uncertainty a decision, method, evidence requirement and stopping rule.

Recent YouTube/workflow discovery was treated as a lead-finding route, with a requested last-month window. This pass did not watch videos or obtain a verified comprehensive set of last-month transcripts. It did inspect actual code/graphs for relevant recent workflows, including the October AnyAngle order comparison and released WorldSculpt integration lead. No conclusion rests on a video title, search recency label or unverified showcase.

## 16. Short glossary

| Term | Meaning here |
|---|---|
| Intrinsics / K | The lens and pixel-projection information: focal lengths and image center, among other camera details. |
| Extrinsics | Where the camera is and how it is rotated relative to the object/world. |
| Calibration | Determining those camera quantities; a label such as “front-right” is not calibration. |
| Conditioning | Information a model uses while generating, such as text, references, depth or pose. |
| LoRA | A compact trainable change to particular neural-network weights. It is tied to compatible architecture and training. |
| Control network / adapter | A learned mechanism for supplying additional guidance. Not every adapter is a LoRA. |
| VAE | Converts between image/shape data and a model's compressed representation; not a camera-control plugin. |
| Differentiable rendering | Rendering in a way that allows an optimizer to calculate how camera/shape/material changes affect image error. |
| SDF / scalar field | A spatial field from which a surface can be extracted; FlexiCubes operates in this kind of setting. |
| Ablation | A comparison that changes one complete factor so the source of improvement is identifiable. |
| Held-out object/view | An object or camera not used to train or fit the result; useful for detecting overfitting. |
| Source-inspected | The code was read. It was not necessarily executed successfully on this machine. |




