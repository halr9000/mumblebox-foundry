# Mumblebox: focused SDXL + MV-Adapter proposal

Research completed 2026-10-22. **Proposal for discussion; implementation has not begun.** Target: Brian's Windows Comfy Desktop, RTX 4080 SUPER with 16 GB VRAM and 64 GB RAM. The [source ledger](SOURCE-LEDGER.md) records inspected code, release pins, author statements, community leads and access limits. The [research plan](PLAN.md) defines the authorized scope.

## The recommendation

**Build one independent Comfy workflow that takes an image and a short description, generates six coordinated views with SDXL + MV-Adapter, and reconstructs one object from those views using the orthographic NeuS method used in the MV-Adapter paper.** Use StableNormal to estimate surface directions. Finish and extract the mesh on the GPU, then export a colored GLB and a geometry master.

This is the adapter-based route Brian expected. The views exchange information during generation. Reconstruction fits one shared surface to their combined evidence. It does not generate a separate mesh for each image or assemble separately generated parts.

The strongest reason to choose it is a published connection between the adapter and actual mesh reconstruction. The original authors used StableNormal and NeuS following Era3D, and reported better reconstruction scores in their evaluated setting. That justifies a focused reproduction attempt; it does not establish that every object or hidden-detail request will work here. [Final paper, section 5.4 and Table 3](https://openaccess.thecvf.com/content/ICCV2025/papers/Huang_MV-Adapter_Multi-View_Consistent_Image_Generation_Made_Easy_ICCV_2025_paper.pdf)

**Three limitations must be accepted before implementation:**

1. The public release does not contain the exact complete image-to-mesh evaluation script. The components exist, but their camera/normal connection, Windows integration and GPU extraction need engineering and calibration.
2. The standard image-conditioned adapter takes one reference image plus shared text. Reliable use of several user photographs, or guaranteed rear-only instructions, is not established by this release.
3. Image generation is plausibly within 16 GB, but the full chain has not been measured on this PC. Its first complete validation must prove memory fit, useful geometry and tolerable time.

The proposed first export is **one actual mesh with vertex colors**, not a UV/PBR material package or an automatically print-ready model. That distinction is explicit so the proposal cannot win by delivering attractive pictures or a mislabeled asset. UV baking is a separate missing connection described below; it is not silently counted as finished.

No alternative full pipeline is recommended as a fallback at this point. If this route fails its agreed tests, report that result and discuss the evidence. Do not quietly replace it with Pixal, independent view prompting, or mesh assembly.

## What is different from the unsuccessful work

Earlier experiments had two distinct failure sources: images that disagreed about the object, and reconstruction inputs whose cropping/cameras did not match. Correcting one does not fix the other.

MV-Adapter addresses the first by adding trained multiview attention to SDXL. During a joint denoising run, a view can use features from the other views and from the source photograph. This is materially different from requesting six separate pictures with carefully worded prompts. It encourages agreement; it does not enforce a watertight 3D scene or exact feature placement. [Attention source](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/models/attention_processor.py)

The proposed reconstruction addresses the second by using the projection type the adapter was trained to produce. NeuS represents a single surface and adjusts it to explain the six silhouettes, colors and surface-direction estimates. The connection will carry explicit cameras and transforms, rather than infer them from filenames or turn orthographic images into guessed perspective photographs. [Orthographic loader](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/datasets/ortho.py), [ray construction](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/ray_utils.py)

The prior local Klein/RefControl and Pixal tests remain useful lessons about camera matching, thin features and resource recovery. They are not tests of this adapter. The later assembly experiment neither proves nor disproves it. No local success with the complete route was found in the reviewed evidence.

## Complete path from the user's picture to one exported mesh

> Image + brief description → foreground isolation → six jointly generated views → paired masks and surface normals → camera-correct reconstruction of one surface → GPU mesh extraction and color sampling → visible inspection → GLB and geometry export.

### 1. Accept and prepare the source

Start with one complete, unobstructed object, preferably photographed from a front three-quarter angle. Preserve the uploaded original. A cutout with alpha can bypass segmentation; otherwise use ZhengPeng7/BiRefNet, explicitly selected rather than the wrapper's alternative default.

Follow the author's source-framing recipe: isolate the foreground, retain its aspect ratio, center it, and leave roughly 10% total margin along its longest dimension. This prepares the reference for generation. It does **not** authorize independently zooming or cropping the six generated target views. [Author inference/preprocessing](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/scripts/inference_i2mv_sdxl.py)

The first validation targets complete object pictures, not every possible photograph. The paper evaluated limited reference elevations and front-facing azimuths. Severe cropping, extreme overhead views, transparent objects, reflections and heavy occlusion are not silently promised. A failure on those inputs should later become a clear limitation, not an invitation to invent hidden geometry with confidence.

### 2. Generate six views together

Use this reproducible baseline, chosen from the released image-conditioned examples:

| Control | Proposed baseline | Reason |
|---|---|---|
| Base image model | stabilityai/stable-diffusion-xl-base-1.0 | Direct reference model; keeps checkpoint effects out of the first result |
| Adapter | huanngzh/mv-adapter: mvadapter_i2mv_sdxl.safetensors | Released image-conditioned SDXL adapter |
| VAE | madebyollin/sdxl-vae-fp16-fix | Explicit supported component in the examples |
| Views | Six in one joint run | Preserves cross-view attention and trained camera set |
| Size | 768 × 768 each | Released baseline size; no independent upscale/crop |
| Steps / guidance | 50 / CFG 3 | Script defaults |
| Reference-conditioning scale | 1.0 | Script default; distinct from text CFG |
| Scheduler | DDPM, interpolated SNR shift scale 8 | Explicit author Comfy graph plus released scheduler code |
| Precision | FP16; VAE slicing | Documented implementation path |
| Negative text | watermark, ugly, deformed, noisy, blurry, low contrast | Released generic starting point; not a location-aware exclusion mechanism |
| Extra style/checkpoint adapters | None in the first proof | Test MV-Adapter's intended mechanism before changing its input distribution |

[Image inference](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/scripts/inference_i2mv_sdxl.py), [author Comfy graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_diffusers.json).

There is a release-detail discrepancy worth preserving: the standalone script can keep its loaded base scheduler when no scheduler is specified, while the graph explicitly selects DDPM. The proposal fixes the graph choice instead of leaving it implicit. Likewise, the supplement and code express SNR shifting differently; use the released code value rather than mix settings from different descriptions.

The standard six slots are front, front-right, right, back, left and front-left. They are all at the horizon. This first reproduction does not add rear diagonals, overhead or underside pictures, or switch to a beta variant with different view counts. Those changes would change the method being evaluated. The author specifically warns that untrained rear diagonals are difficult. [Author reply](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/40)

The short description identifies the object, its overall style and the requested hidden detail, if any. It does not contain a manually invented prompt for every camera. Keep the full six-view set available for inspection; do not mix individually rerolled images from unrelated runs into a supposedly coherent batch.

### 3. Estimate surface directions and keep the masks aligned

Run the full StableNormal route with stable-normal-v0-1 and yoso-normal-v0-3. Its implementation also loads DINOv2 ViT-L/14 to provide image features; that dependency must be included in the download, license and memory manifest. A normal map describes the direction a visible surface faces. It is not a depth map or proof that hidden geometry is correct. [StableNormal loader](https://github.com/Stable-X/StableNormal/blob/594b934630ab3bc71f35c77d14ec7feb98480cd0/hubconf.py), [pipeline](https://github.com/Stable-X/StableNormal/blob/594b934630ab3bc71f35c77d14ec7feb98480cd0/stablenormal/pipeline_stablenormal.py)

Process the six views sequentially with the normal estimator loaded once. Pair every RGB image with its foreground mask and normal map. Apply the same pixel transform to all three. If resizing is needed for the reconstruction configuration, resize the complete square frame uniformly; vector normals must be renormalized after resampling. Do not independently recenter a normal map or alter an object's apparent scale.

The first reproduction uses the full normal estimator rather than silently substituting its turbo option. Normal prediction can itself be wrong, particularly on thin structures, flat painted graphics and ambiguous shading. The validation therefore inspects normals and the resulting geometry separately.

### 4. Connect the cameras and normals correctly

This is the most consequential missing bridge. It must be implemented before judging artistic results.

**Canonical front:** The adapter predicts what it thinks is the object's front. Its camera zero is not necessarily the uploaded photograph's camera. The author states this directly. The source photo remains the generator's identity reference; it must not be appended as a seventh orthographic reconstruction view. [MV-Adapter issue 42](https://github.com/huanngzh/MV-Adapter/issues/42)

**Projection and size:** The adapter's camera helper uses an orthographic span of 1.1, distance 1.8 and elevation zero, with its particular azimuth offset and world axes. Era3D's default ray plane spans two units. These can be reconciled through an explicit common coordinate/scale mapping; they must not simply be connected unchanged. Save the actual matrices and span, not only a label such as “right.”

**Normal direction:** StableNormal predicts each view in its own camera convention. Era3D's ordinary loader assumes its input normals already share a front-view basis, then applies additional coordinate conversions. Feeding the six independently predicted normal maps straight into that path is incorrect. The bridge must decode vectors, map the documented StableNormal convention, rotate each map into the common frame and preserve a single documented export orientation. The author describes StableNormal's convention as left-handed; a guessed OpenGL sign flip is insufficient. [Normal convention](https://github.com/Stable-X/StableNormal/issues/18), [Era3D normal conversion](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/mvdiffusion/data/normal_utils.py)

**Framing:** Foreground removal only changes alpha. It does not crop each target independently. Every reconstruction pixel must keep the projection that produced it. Correct metadata still cannot make an AI image obey that projection; visual agreement remains a separate gate.

The stage boundary should carry one manifest containing:

- Original image hash, prepared reference, prompt, seed, component revisions and settings.
- Six immutable view identifiers and exact image/mask/normal file pairings.
- Orthographic projection, image size, camera-to-world and world-to-camera matrices, pixel-center convention and world axes.
- Source crop transform separately from target-frame transforms.
- Normal encoding, handedness/basis conversion and object normalization.
- One final object-to-export transform, applied once.

This manifest prevents another camera/crop mistake and lets a failed reconstruction be diagnosed without regenerating images. It is internal data, not extra work the user performs.

### 5. Reconstruct one surface

Use Era3D's released orthographic NeuS implementation, not its separate image generator. NeuS learns a compact surface representation for this one object by rendering it from the six known cameras and comparing those renders with RGB, silhouette and normal evidence. It is per-object optimization, not training a new general-purpose model.

Start from the released neuralangelo-ortho-wmask configuration: 3,000 optimization steps, mixed precision, its RGB/mask/normal losses and its documented six-view weights. Keep the existing 256 extraction resolution initially. Record all deviations needed for memory or coordinate correctness. The optimizer's partial-pixel ranking tolerates some outliers; it cannot reconcile a handle that changes sides or a backpack that disappears from every rear view. [Configuration](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/configs/neuralangelo-ortho-wmask.yaml), [system](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/systems/neus_ortho.py)

The released config asks for 1024-square reconstruction images and comments about export color at lower sizes. If retained, uniformly resample the 768-square frames to 1024, including masks and normalized normal vectors. That adds no information and must not change the camera span. Exact MV-Adapter reconstruction settings were not released, so this is an explicit reproduction choice, not a claim to match every unpublished setting.

No new mesh-generating weights are needed for this NeuS stage. Its small networks and CUDA libraries are fitted to the current object. The implementation must cap ray batches and extraction chunks for this PC rather than assume the largest upstream settings are appropriate.

### 6. Extract, inspect and export on the GPU

The stock Era3D exporter uses CPU PyMCubes; its alternative torch path is explicitly disabled because of scaling issues. Enabling that checkbox is not a solution. The proposal includes a corrected extraction bridge using the CUDA implementation in current torchmcubes. The surface field and its original coordinate bounds remain authoritative. [Era3D geometry source](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/geometry.py)

torchmcubes exposes real CUDA extraction, but its current wrapper can silently perform the computation on CPU if built without CUDA, then return GPU tensors. Require HAS_CUDA, inspect the executed kernel/device and reject the CPU fallback. Its current revision has MSVC support code and requires CUDA 12+, C++20 and CMake 3.24+; compilation on this machine remains a validation task. [CUDA dispatch](https://github.com/tatsy/torchmcubes/blob/a9ac95aa329957ba646e7bb057f825f5dfa77f38/torchmcubes/__init__.py), [build configuration](https://github.com/tatsy/torchmcubes/blob/a9ac95aa329957ba646e7bb057f825f5dfa77f38/CMakeLists.txt)

Preserve the unmodified extracted master. Query the fitted field for vertex colors on GPU in bounded chunks. Convert to Comfy's mesh representation and use the existing SaveGLB path, plus a geometry export suitable for later inspection. Verify face winding, units/orientation, normals, finite vertices and material/vertex-color preservation after reopening the actual file.

The existing Comfy GPU decimation machinery can produce a lighter derivative if needed. It must not be used to hide reconstruction defects, and the full master is retained. No CPU BVH finishing or slow CPU unwrap is part of this initial route. CPU bookkeeping and file serialization are ordinary; heavy extraction/optimization must stay on GPU.

**Color is not a PBR texture.** Era3D's export evaluates its learned appearance at vertices. It does not separate physically meaningful albedo, roughness and metalness, and it may retain lighting from the generated pictures. A colored GLB still answers the mesh experiment, but it is not the final game-material feature.

For UV textures later, the concrete missing piece would be a baker that samples this NeuS appearance field onto a UV atlas. Existing Comfy PEC unwrapping may supply an atlas, but its Pixal voxel-attribute baker cannot accept a NeuS field. That connection must be separately implemented and licensed; the present report does not count it as working or include it in the initial mesh-quality success claim.

## How much control does this provide over unseen details?

There are three different capabilities, and they must receive separate verdicts.

| Capability | Evidence and expectation |
|---|---|
| Preserve the identity and visible features of one reference | This is the released adapter's primary task; performance still needs local validation |
| Make the generated views agree with one another | Joint attention is implemented and evaluated; occasional inconsistencies remain possible |
| Place an arbitrary requested feature only on an unseen side | Shared text can influence generation, but reliable spatially restricted control is not established |

For example, “a compact robot with a single rectangular backpack centered on its back” is a valid request to test. It is not an enforced placement constraint. If the backpack is painted on the chest, mirrored, omitted or only appears as a dark patch, that request failed. A negative prompt saying “no backpack” would also discourage the desired rear backpack; shared negative text is not a per-view mask.

The author Comfy sampler selects the first reference image from an input batch. Its six outputs do not mean it accepts six user references. The paper's arbitrary-view extension and geometry-conditioned variants are different training/tasks; their descriptions do not make multiple-reference control available in this standard checkpoint. [Sampler source](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/nodes.py), [weight inventory](https://huggingface.co/huanngzh/mv-adapter/tree/main)

During validation, the allowed low-effort correction is one short prompt revision or one whole-set seed retry, with the six views regenerated together. Individually editing incompatible views until reconstruction happens to work would conceal a failure of the automatic workflow. User-assisted editing remains a possible later feature, not evidence that this first automatic method worked.

If ordinary object reconstruction passes but the controlled rear-detail test fails, the result is **a useful one-image reconstruction candidate with an unresolved product requirement**. It is not full success for Brian's complete goal. No research claim currently closes that gap with certainty.

## What exists and what must be developed

“Exists” below means released source or a locally inspected component; it does not mean this complete connection has been run here.

| Part | Existing evidence | Required implementation work |
|---|---|---|
| SDXL + image-conditioned MV-Adapter | Released code, weights and author Comfy graphs | Reproduce the pinned image stage; preserve six-way coupling; record settings |
| Background removal | BiRefNet and author integration | Explicit model selection, alpha handling and paired masks without target recropping |
| StableNormal + YOSO + DINOv2 | Released estimators and loader | Controlled local loading, six-image batch ownership, normal convention bridge and unloading |
| Orthographic NeuS | Released Era3D optimizer | Feed the actual cameras, transform normals correctly, isolate dependencies, cap memory |
| GPU surface extraction | torchmcubes CUDA source | Compile verified CUDA path; repair coordinate/sign/winding handling in the bridge; no CPU fallback |
| Colored mesh export | Era3D field-color export and existing Comfy mesh/GLB support | Type conversion, one export transform, visible preview and file reopening checks |
| Complete Comfy chain | Not verified in the reviewed work | One independent graph with visible stages, progress, cancellation and resource recovery |
| Exact multi-reference / rear-only control | Not supplied by the standard released wrapper | An unresolved capability, not a hidden implementation promise |
| UV/PBR baking from NeuS | No complete compatible bridge verified | Later scoped development if the geometry route passes and that work is approved |

This is a meaningful integration project. It is neither a finished one-click graph nor a proposal to invent a new image model. Build the complete path before artistic tuning. Small deterministic camera/conversion checks support that work; they must not become a substitute project.

## Memory, Windows and visible Comfy operation

The author extension estimates 13–14 GB for SDXL image inference. A later CorrAdapter paper measured its MV-Adapter baseline at 15.27 GB under its own settings. User OOM reports also exist. These numbers describe different configurations; none guarantees comfortable headroom on the RTX 4080 SUPER. [Extension README](https://github.com/huanngzh/ComfyUI-MVAdapter), [CorrAdapter Table 4](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_Align_Images_Before_You_Generate_CVPR_2026_paper.pdf)

Use stage-owned worker processes managed by nodes in the existing visible Comfy Desktop. This is an integration proposal, not permission to run a hidden second app. Inputs, six outputs, normals, reconstruction progress, mesh preview and export must appear in that one graph. Cancellation terminates the current worker and reports the actual result.

The stage sequence is:

1. Segment the input, save it, unload segmentation weights.
2. Load SDXL/adapter/text encoders/VAE, generate all six views in one shared pass, save results, end the worker.
3. Create target masks, unload segmentation, then load StableNormal/YOSO/DINO once, process all six views, save and end that worker.
4. Load only NeuS and its CUDA dependencies; fit the object, extract/color it, save the master, release the worker.
5. Run any approved GPU finishing/export step, then release its resources.

Do not unload the adapter between output views: that would misunderstand the joint batch. Do not keep previous image models resident while reconstruction starts. Verify worker termination, GPU allocation and host memory after success, error and cancellation. An empty cache call is insufficient while a graph object still owns model tensors.

The author extension pins Diffusers 0.31.0, Transformers 4.46.3 and related older packages. StableNormal has a different older environment, and Era3D relies on tiny-cuda-nn, nerfacc and PyTorch Lightning. Their complete requirements files are not safe to apply indiscriminately to current Desktop. StableNormal's list also contains Linux-specific packages. Use pinned minimal environments under E:; do not downgrade Desktop globally. [Extension requirements](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/requirements.txt), [StableNormal requirements](https://github.com/Stable-X/StableNormal/blob/594b934630ab3bc71f35c77d14ec7feb98480cd0/requirements.txt), [Era3D setup](https://github.com/pengHTYX/Era3D)

The exact minimal Windows package combination is unresolved. Era3D's original CUDA 11.8 instructions and current torchmcubes' CUDA 12 requirement cannot be silently combined. During implementation, either establish a compatible CUDA 12 reconstruction environment with narrow compatibility changes, or isolate extraction behind a field/mesh file boundary while retaining GPU color evaluation in the reconstruction environment. This is an environment fallback within the same algorithm, not a different mesh method. Record it before quality testing; never conceal a CPU fallback.

For Windows data loading, avoid blindly spawning one CUDA-using worker per CPU core. A controlled zero-worker data loader is a reasonable compatibility starting point, not a claimed upstream speed recommendation. CPU offloading of idle image components may reduce VRAM, but splitting the six images into independent denoising jobs is disallowed.

## Licensing and local operation

The selected source/weight releases are accessible without a paid inference service. Free local inference does not eliminate license obligations. These findings concern the exact inspected releases, not every model with a similar name.

| Component | Inspected terms / consequence |
|---|---|
| SDXL base | CreativeML Open RAIL++-M. Commercial output use is possible subject to use restrictions and upstream terms; not a public-domain declaration |
| MV-Adapter | Apache-2.0 code/weight declaration; preserve notices and dependency terms |
| FP16-fix VAE / BiRefNet | MIT declarations for these releases; retain provenance and upstream obligations |
| StableNormal / YOSO | Apache-2.0 declarations; pin the full normal pipeline rather than treating one card as a license for every dependency |
| DINOv2 ViT-L/14 | Apache-2.0 code; track the selected released backbone and weight provenance |
| Era3D | AGPL-3.0. Commercial activity is not prohibited, but software distribution/network-use obligations need to be respected. It is not automatically a requirement to publish ordinary generated asset files |
| tiny-cuda-nn | BSD-style source terms in the inspected license |
| Current torchmcubes | MPL-2.0, including file-level source obligations when distributing covered code/modifications. Do not repeat obsolete MIT descriptions for this revision |
| DISO | CC BY-NC 4.0; excluded from this proposed commercial-use stack |
| Optional nvdiffrast texture-refinement route | Inspected NVIDIA license has restrictive terms; not assumed commercially cleared and not included in the primary volumetric reconstruction path |

[License sources and exact pins](SOURCE-LEDGER.md#s12--component-licensing), [MPL explanation](https://www.mozilla.org/en-US/MPL/2.0/FAQ/), [DISO license](https://github.com/SarahWeiii/diso/blob/9792ad928ccb09bdec938779651ee03e395758a6/LICENSE).

Era3D's AGPL code and optional renderer licenses are material distribution decisions for a future public Mumblebox package. Internal source-backed experimentation is not the same as product redistribution. A release must carry an actual dependency/notice manifest and resolve any inherited model-weight terms; this report is not blanket legal clearance. Keeping a component in a separate process must not be advertised as automatically avoiding copyleft obligations.

## Promising additions that were actually examined

### CorrAdapter is a real continuation of this exact idea

The 2026 CorrAdapter work adds feature correspondence matching to multiview attention: it tries to align corresponding parts before exchanging information. Its released MV-Adapter subproject contains both a training-free route and a trained variant. This is directly relevant to inconsistent details, rather than another unrelated image generator.

It is not the default for this PC yet. Its paper reports about 20.9 GB for the extension under the evaluated configuration, above this card's capacity. The trained checkpoint exists but its inspected card does not declare a license. Its reported consistency improvements are not a local NeuS-mesh demonstration. After a successful baseline, a separately bounded memory/quality comparison could be justified; adding it now would mix reproduction with unproven memory engineering. [Code](https://github.com/SuhZhang/CorrAdapter), [paper](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_Align_Images_Before_You_Generate_CVPR_2026_paper.pdf), [trained weights card](https://huggingface.co/SuhZhang/CorrAdapter-Model-on-MVAdapter)

### EDN is released code with unresolved usage terms

EDN learns an adjustment to initial diffusion noise. The repository includes a MV-Adapter implementation and checkpoint file entries. It is not correct to dismiss it as weights-unavailable. However, no root license was found, and the available comparisons do not establish an improvement to this complete mesh route. It remains a specific follow-up pending licensing and a matched test, not a component in the baseline. [EDN code](https://github.com/zhihao0512/EDN), [paper](https://arxiv.org/abs/2512.16219)

### Juggernaut and style LoRAs remain conditional

The adapter was designed to retain SDXL ecosystem compatibility, and the authors show selected community models and LoRAs. That does not prove every derivative checkpoint will produce better geometry. Juggernaut XL v9 was specifically checked; its card is oriented toward photographic appearance and has paid-service licensing restrictions. Its ordinary text-to-image guidance should not overwrite the adapter's coordinated-view recipe. [Juggernaut card](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9)

Recommendation: start with the official SDXL base. If the complete geometry path passes and appearance is the demonstrated remaining weakness, discuss one matched checkpoint substitution. No style catalog or checkpoint sweep belongs in this first validation.

## What is deliberately not being proposed

| Approach | Reason it is excluded from this iteration |
|---|---|
| Separate meshes assembled into one result | Changes the user's task and adds manual work |
| Six independently prompted generations | Does not test MV-Adapter's joint generation hypothesis |
| Pixal with guessed perspective cameras for these images | Adds an unvalidated projection bridge when an orthographic method is documented |
| A rough-mesh / second-mesh loop | Not required to test the selected published route; can propagate invented geometry |
| More cameras, contact-sheet splitting or beta arbitrary-view weights | Changes the release and camera contract before the standard method is understood |
| A pose ControlNet by itself | A human pose skeleton does not specify arbitrary object shape or ensure six views agree |
| Texture-only refinement as geometric success | Cannot create a missing backpack, hole or correct object proportions by itself |
| CPU extraction/unwrap as an unnoticed fallback | Violates the GPU finishing requirement and repeats the earlier speed problem |
| Custom training before testing the released adapter | The requested capability already has a relevant released mechanism; unbounded training would defer answering whether it works |

These are decisions for this iteration, not claims that every excluded technique is useless.

## Custom adapter work: a credible path, but only after a diagnosed failure

If a later test shows cross-view identity succeeds but user-specified hidden geometry does not, the research problem becomes narrower: condition joint view generation on explicit side-specific information without overwriting visible identity.

A credible future training proposal would need: licensed 3D assets; known camera renders with consistent masks, scale and coordinate system; paired source/target views; examples of asymmetric hidden features; a conditioning representation that labels which view or region a reference belongs to; and held-out whole-object reconstruction tests. Blender-generated data could supply camera truth. Captioning unrelated single views with angle names alone would not reproduce multiview coupling.

The official training machinery provides a starting point, but the original MV-Adapter training used eight A100s and a substantial object corpus. CorrAdapter's trained path also uses multi-GPU fine-tuning; its training-free path is distinct. Neither source supports promising a complete new adapter on this 16 GB card over a weekend. A LoRA's small file size is not a measurement of activation memory or data cost.

No compute purchase or price estimate is justified before selecting the exact trainable modules, dataset size, resolution, batch arrangement, GPU type, runtime and provider. A future budget would be GPU-hours multiplied by a verified provider rate, plus storage/data preparation. The current recommendation costs no training rental because it first tests released weights.

## Bounded implementation and validation proposal

These are **proposed limits for approval**, not tests performed in this research. Their purpose is to produce an honest answer without another open-ended sequence of tiny artistic tweaks.

### Build once, then evaluate the complete path

Implement the stage wrappers, camera/normal interface, GPU extraction and export as one independent graph. Preserve Mumblebox's current workflow. Perform targeted engineering checks as each connection is written, but do not substitute those checks for the real image-to-mesh test.

There is one early calibration gate because a coordinate bug can invalidate every later quality result. Use a simple asymmetric object with known dimensions and camera renders to verify transforms, normal signs, field extraction and export axes. This fixture is an engineering control; it is not counted as a successful user asset. No manual assembly of generated parts occurs in it.

### Fixed evaluation set

Select and freeze the images and essential features before viewing generated results. Use existing suitable inputs or user-supplied photos; do not generate a more convenient subject after a failure.

| Case | Why it is included | Essential judgment |
|---|---|---|
| A — asymmetric stylized prop | Distinct front, back and one-sided feature; toy camera is suitable if its original single reference is usable | Body proportions, feature count, side placement and identity |
| B — mechanical/game part | A through-hole, thickness and a narrow structural feature | Actual open hole and solid geometry, not painted shading; no destructive smoothing |
| C — character/organic figure | Different geometry from crates and vehicles; separated limbs or appendages | Correct major-part count, readable silhouette, no fused limbs where source separates them |
| C+ — same input as C, one requested rear feature | Directly tests why Brian wanted hidden-side control | Feature added in the correct rear location as geometry while source-facing identity remains intact |

C and C+ use the same fixed seed so the hidden-detail request has a meaningful paired comparison. Predeclare the feature, such as a single centered rectangular backpack, and its spatial relation. It cannot be counted as successful merely because the word influenced a color patch.

### Attempt and resource limits

- Four primary joint-view runs, one per case. At most one quality retry for each case, changing either the concise prompt or the seed, not an unlimited parameter search. Maximum eight complete six-view candidates: 48 generated target images.
- At most one reconstruction for each completed candidate. If a reconstruction plumbing defect corrupts an otherwise valid attempt, allow at most two logged technical reruns across the entire suite, reusing the same images. Maximum ten reconstruction invocations, plus one calibration control and one calibration retry.
- No CorrAdapter, EDN, checkpoint substitution, new camera set, custom training or unrelated model trial inside this suite. Those require a separate decision after the result.
- If the reference configuration exceeds memory, permit one explicitly logged memory-only adjustment for that stage: component offload or bounded ray/extraction chunks. Preserve joint generation, camera set and training resolution. Repeated OOM after that rejects the configuration on this hardware.
- Proposed run caps, excluding first downloads/builds: 10 minutes for six-view generation, 10 minutes for all normal estimation, 30 minutes for reconstruction, 10 minutes for extraction/color/export. These are user-experience rejection limits, not measured speed predictions. A deterministic timeout stops the worker and records the failure.
- A job with no progress and no meaningful GPU work for five minutes is diagnosed once rather than left running indefinitely. Compilation time must be separately identified so it is not mistaken for generation progress.
- Target at least 1 GiB of GPU headroom when practical; record both whole-card usage and process allocations. Keep at least 8 GiB of system RAM available. Stop rather than drive the machine into sustained paging. Capacity and units must be recorded, not inferred from an empty queue.
- After each stage or cancellation, worker allocations must disappear and whole-card memory must return close to that run's measured idle baseline. A discrepancy over roughly 1 GiB requires explanation before the next heavy stage; ordinary display/background usage is not attributed automatically to this workflow.
- At most five minutes of user interaction per case beyond upload and review. No Blender repair, manual target recropping, individually painted view corrections or assembling meshes to obtain a pass.

An integration failure is not evidence against the underlying scientific method. Stop at a failed engineering gate, report the exact missing connection, and do not burn the artistic attempt budget on known-invalid inputs. Ordinary reproducible code defects can be repaired within the proposed graph; each rerun is still recorded and the fixed attempt caps still apply.

### Success criteria

**Engineering gate:** camera/normal calibration is correct; real CUDA extraction executes; actual exported files reopen with matching orientation, geometry and color; cancel/error/success release resources; no Desktop-wide dependency downgrade.

**Image gate:** all six images are complete and retain the object identity and required feature layout. No front/back swap, major mirror, missing essential part or incompatible change of proportions. A technically correct camera manifest does not waive this visual gate.

**Mesh gate:** cases A, B and C each produce a coherent whole object within their allowed attempts. Inspect the actual exported geometry from front, back, both sides, above and below, with a neutral surface display as well as color. Required holes are holes, protrusions are protrusions, and thin parts have usable thickness. No catastrophic flattening, duplicated major forms or large unintended disconnected fragments. Relative landmark ratios should stay within a predeclared 15% tolerance where the input provides a fair comparison; unknown hidden dimensions are not invented as ground truth.

**Hidden-detail gate:** C+ adds the specified rear feature as actual geometry in the correct location, without copying it to the front or sacrificing the source-facing features. This gate must be reported separately even if A/B/C look good.

**Practical gate:** bounded time, memory and interaction limits hold. All attempts and exceptions appear in the result table; successes are not cherry-picked from hidden reruns.

These criteria accept that an AI mesh may need later art cleanup. They do not require flawless topology, perfect fingers or ready-to-print manufacturing tolerances. They do require that the output already represent the intended object well enough to be useful, rather than being attractive only from one camera.

### Rejection and stopping conditions

Stop the suite when its allowed attempts have finished, or earlier when a fundamental gate makes valid continuation impossible. Do not extend the run to chase perfection or silently redefine success.

- **Full experiment success:** engineering, A/B/C geometry, C+ hidden-detail and practical gates pass. Deliver every final exported result and its views/settings, then stop for Brian's review. This is bounded evidence on four cases, not proof of universal reliability.
- **Limited result:** A/B/C work, but the rear-control or practical requirement fails. Deliver the useful meshes and name the failed capability. Do not mark the full product objective achieved; discuss whether the limited route is worth integrating.
- **Rejected local proposal:** after allowed retries, the coordinated views or reconstruction remain unusable, GPU finishing cannot be established, or it cannot operate within this hardware/time budget. Deliver failure evidence and stop. Do not switch methods without discussion.
- **Integration limit:** public components cannot be connected correctly within the approved scope. State the exact source/runtime obstacle and what a separate decision would require. A license problem is not bypassed by copying the code or renaming a wrapper.

Before implementation, agree on these limits and the vertex-color export scope. After that agreement, the implementation goal must adopt them explicitly. No further approval is needed for every small repair inside that accepted scope, but a material method change requires discussion.

## Remaining uncertainties and the precise next evidence needed

| Uncertainty | Why research alone cannot close it | Bounded resolution |
|---|---|---|
| Six-view image stage fits 16 GB reliably | Published numbers differ; custom attention/runtime versions matter | One reference configuration run and one memory-only retry |
| Exact camera/normal mapping | Authors' conventions are documented, but complete MV-Adapter reconstruction glue is absent | One asymmetric calibration control with saved matrices and expected normal directions |
| Native Windows optimizer/extractor compatibility | Separate older CUDA ecosystems and current compiler changes | Isolated build/import proof and CUDA kernel proof before artistic runs |
| Surface fitting is useful and fast enough | Source code and paper averages do not measure these inputs on this PC | Fixed A/B/C cases with time and geometry criteria |
| Text controls the unseen feature | Shared conditioning does not enforce per-side semantics | Paired C/C+ input/seed with explicit rear-feature geometry inspection |
| Multiple reference photographs | Current standard wrapper uses one image | Unresolved product extension; no claim until an actual conditioning/reconstruction design is approved |
| UV/PBR output | Existing voxel baker does not consume a NeuS field | Separate, explicit field-to-atlas bake proposal after geometry validation |
| CorrAdapter's benefit within 16 GB | Published configuration exceeds the card; no matching mesh proof | Later separately approved memory and mesh comparison, not this baseline |
| EDN usage and benefit | Missing clear license and matched mesh evidence | Author clarification/source license plus an agreed matched test, not installation now |

No further broad survey is recommended before the proposed baseline. The consequential unknowns are now specific interfaces and runtime/quality tests. If implementation is approved, the next action is to build this complete adapter-to-mesh chain, not restart from separate meshes or resume generic prompting experiments.

## Research completion record

The plan was written, existing evidence reviewed first, targeted release/paper/source/community research completed, and this proposal saved. R1–R8 have answers with explicit unresolved runtime/product limits. Relevant new code and paper snapshots are in sources; older snapshots are linked through the ledger.

No Comfy code, workflow, runtime, settings or models were changed. No generation, installation, training, benchmark, purchase or app restart occurred. No result in this report is presented as a newly generated local mesh. Research ends here for discussion and approval.
