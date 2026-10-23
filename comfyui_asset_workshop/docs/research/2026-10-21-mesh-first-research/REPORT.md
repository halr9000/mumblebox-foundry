# Mumblebox: better first-export meshes

Research completed 2026-10-21. Target: Windows, 16 GB GPU memory, 64 GB system RAM. This is a research recommendation for discussion, not an implemented product change.

## Answer to Brian

**Yes. There are practical custom improvements with working precedents. The strongest opportunity is to control and verify geometry across the pipeline, rather than keep strengthening the wording of angle prompts.**

Three different things need to work together:

1. The pictures must depict the same object.
2. The reconstruction model must receive camera and framing information that matches those pictures.
3. Finishing must preserve the recovered shape rather than merely make it look smooth.

Our earlier tests exposed problems in all three areas. They were useful experiments. However, continuing to change prompts without separating these causes would waste time. The next iteration should compare a small number of complete, technically compatible routes against a clean baseline.

**Recommended order:** validate the image/camera contract; test existing structural controls with separate appearance references; compare a genuinely joint multiview generator where its projection matches the reconstruction route; consider custom training only for a measured remaining failure. Keep a good first mesh if a second pass makes it worse.

No application was changed, no models or datasets were installed, and no image, mesh, or training jobs were run during this research. Public code, graphs, model cards, and dataset documentation were inspected and small source snapshots saved. Performance and quality claims below are either author reports, earlier local observations, or proposals; none are new runtime proof.

## 1. What the current evidence actually establishes

| Observed condition | Likely owner and consequence | What it does not establish |
|---|---|---|
| Earlier preprocessing enlarged and recentered each toy-camera silhouette without updating its projection. | Image preparation could change the relationship between pixels and rays. This was a real input-contract defect. | It does not prove that cropping is always wrong. |
| The saved rerun preserves all four original panel frames and identity image transforms. | That particular repair already exists. Do not repeat it as a new feature. | The requested view angles are still estimates, not measured camera poses. |
| The rerun changed depth/width from about 0.92 to 0.72, while duplicated rear details and grip problems remained. | Preprocessing contributed; inconsistent pictures and reconstruction ambiguity remain plausible contributors. | A nicer ratio is not a measurement against a true toy-camera mesh. |
| The current TRELLIS.2 recipe conditions on `images[0]`. | Selecting additional images does not make this branch a multiview reconstruction model. | It does not imply that every TRELLIS-derived research system is single-view. |
| Current Pixal single-image auto-FOV already uses MoGe. | Recommending that same connection as missing would be stale advice. | MoGe's FOV estimate is not a complete multi-image camera calibration. |
| RefControl and draft rendering paths already exist in our extension. | The work is now exact input compatibility and comparative validation, not inventing their existence. | Source wiring alone does not prove improved output quality. |

Evidence: the prior [controlled framing record](<E:/Comfy-Desktop/ComfyUI-Shared/output/AssetWorkshop/assets/64edac36da7e/drafts/658624c796d94a13/framing-review.md>) and fresh inspection of `recipes.py`, `pixal_conditioning.py`, `camera_guides.py`, and `resource_lifecycle.py` in this extension. The historical record reports 64 passing targeted tests and cleanup after that run. Those tests were not rerun during this research.

### Camera assumptions matter more than labels

The local native `Pixal3DMultiViewConditioning` offers four named slots: front, left, back, right. Its implementation supplies a horizontal orbit, fixed relative azimuths, a shared perspective FOV, and a framing assumption. Connecting a three-quarter image to its front slot does not cause the node to infer that image's real camera.

The upstream general multiview path accepts camera matrices and horizontal FOV. Its conventions include Blender-style camera-to-world transforms and rebasing onto the first view. The custom Mumblebox path can supply explicit metadata, but metadata that repeats the requested angle is still an estimate when an image generator disobeys it. [Pixal3D source and multiview instructions](https://github.com/TencentARC/Pixal3D)

The official Comfy example independently crops to masks with padding before using a presumed cardinal rig. That is a useful example of a particular normalization convention, not proof that arbitrary independent cropping preserves calibrated cameras. A correct pipeline must implement one coherent convention. [Official Comfy multiview graph](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/3d_pixal3d_multi_views.json)

For a calibrated perspective image transformed by an image-space affine matrix A, the corresponding intrinsic matrix changes to K′ = A K. Arbitrarily stretching one view to match another's bounding box changes the evidence. Even with a fixed camera rig, different silhouettes can occupy different widths. Orthographic inputs also require an explicit orthographic-compatible route; a guessed small perspective FOV is not automatically equivalent. [PyTorch3D camera conventions](https://pytorch3d.org/docs/cameras)

## 2. What can be custom-built, with actual precedents

These are engineering recommendations inferred from the cited implementations. They are not claims that the complete proposed Mumblebox combination has already been tested.

| Custom component | Existing precedent | Practical job for Mumblebox | Boundary |
|---|---|---|---|
| **Image and camera validation** | Pixal's explicit camera contract; native Comfy graph; standard camera transforms | Carry projection type, image size, crop/resize transform, camera matrix, FOV/intrinsics, mask, source revision, and confidence together. Reject incompatible combinations. | Checks metadata and transformations; cannot make contradictory artwork true. |
| **Bounded camera fitting** | PyTorch3D's working differentiable-rendering camera optimization tutorial | Adjust a small camera error against a trusted proxy using silhouette and, where available, correspondences. Report ambiguous fits. | Needs a reasonably accurate shape; symmetric objects and wrong geometry can fool it. |
| **Separate structure and appearance inputs** | RefControl's reference-plus-depth/normal routes; MV-Adapter geometry/reference inputs | Render structure from a mesh while retaining approved pictures as appearance references. Use the exact conditioning format expected by each model. | Geometry guides still contain the proxy's shape errors, even when they contain no color. |
| **Joint multiview generation** | MV-Adapter's released code, weights, Comfy graphs, and paper | Generate views that exchange information during sampling, instead of treating every angle as an independent edit. | This is architecture-specific. Its released SDXL/SD2.1 weights do not load into Qwen or Klein. |
| **Controlled reconstruction feedback** | 3D-Adapter/MVEdit's released optimization-based pipeline | Render the draft, apply trained guidance, and keep a second result only when it improves geometry. | The complete released system is heavier than our target; naive feedback can reinforce errors. |
| **Geometry refinement from multiview evidence** | Unique3D's normal-driven reconstruction/refinement implementation | Investigate a matched normal-to-mesh path or carefully bounded surface refinement. | Independent inaccurate normal maps can produce confidently wrong geometry. |
| **Coordinated surface generation** | UltraTex's Klein multiview texturing code and community Comfy port | Improve textures across views after the shape is accepted. | Texturing is not shape correction. A polished bad mesh is still a bad mesh. |

Primary precedents: [camera fitting tutorial](https://pytorch3d.org/tutorials/camera_position_optimization_with_differentiable_rendering), [RefControl](https://github.com/thedeoxen/refcontrol), [MV-Adapter](https://github.com/huanngzh/MV-Adapter), [3D-Adapter](https://arxiv.org/html/2410.18974v2), [MVEdit implementation](https://github.com/Lakonik/MVEdit), [Unique3D implementation](https://github.com/AiuniAI/Unique3D), [UltraTex](https://github.com/yiboz2001/UltraTex).

### Universal interface, model-specific weights

A common Comfy data interface is realistic. A single learned adapter that plugs unchanged into Qwen Edit, Qwen 2.1, Klein 4B, Klein 9B, and FLUX 3 is not supported by the inspected implementations. Their layers, latent formats, encoders, and reference conditioning differ.

The common interface should describe the intended object, approved appearance references, desired camera, structural maps and their conventions, masks, and provenance. Each model route then translates that information into its own graph and prompt. The enhancer should understand the selected route and preserve camera/layout instructions instead of rewriting them into generic prose.

The stored reference collection can be larger than an adapter's actual inputs. A route trained for one control plus one identity image should select an appropriate approved identity reference for that view, not silently append the entire image history. Record the actual images consumed. More references are not automatically supported merely because the base image model can accept them.

A pose skeleton answers a different question from a camera: it describes articulation. For a character turntable, project the **same 3D skeleton and pose** through the same camera rig. Independently guessed 2D poses can silently change the character's stance. Skeleton control alone does not specify clothing volume, facial identity, finger geometry, or a backpack's thickness.

## 3. The strongest reconstruction and multiview candidates

| Route | What is established | Fit for our next comparison |
|---|---|---|
| Clean single-image Pixal | Existing local path; automatic source FOV route present | Essential baseline. Additional generated views must beat it, not merely add work. |
| Camera-conditioned multiview Pixal | Upstream matrices/FOV path; current custom conditioning | Highest priority to validate with known cameras before blaming the image model. |
| Current TRELLIS.2 branch | Single-image conditioning in our recipe | Useful independent baseline; label honestly in the UI. |
| MV-Adapter | Trained cross-view/reference attention; camera and geometry variants | Strong evidence for the joint-view idea. A separate SDXL/SD2.1 experiment, not a plug-in for the five existing families. |
| Era3D | Joint color/normal outputs and source-camera estimation | Relevant matched reconstruction research; outputs are orthographic. Pin the variant because camera estimation behavior differs between releases. |
| Unique3D | Four generated views followed by normal-driven mesh reconstruction/refinement | Worth comparing as an integrated method, not just extracting its images and guessing new cameras. |
| UniForge3D | Recent unposed multi-image reconstruction/generation source | Promising watchlist item. Weight licensing and unverified Windows/16 GB operation prevent a default recommendation. |
| 3D-Adapter/MVEdit | Geometry feedback during generation; optimization-based code released | Important design evidence. Full deployment exceeds the present resource target and scope. |

[Era3D](https://github.com/pengHTYX/Era3D), [Unique3D](https://github.com/AiuniAI/Unique3D), [UniForge3D](https://github.com/xibushu/UniForge3D), [MVEdit](https://github.com/Lakonik/MVEdit).

### AHA: a prompted contact sheet is not the same as a joint multiview model

Putting four pictures in one generation can help visible consistency, but it does not establish exact shared geometry or cameras. MV-Adapter adds learned cross-view and reference communication. Its geometry path uses position and normal maps, not an arbitrary replacement photograph. That difference directly addresses the problem Brian is trying to solve. [MV-Adapter paper](https://arxiv.org/html/2412.03632v1)

The author's Comfy I2MV graph was inspected: it assembles an SDXL pipeline, multiview module, image reference, background preparation, and six-view sampler. The inspected node implementation uses the first supplied reference image. The separate ControlNet example uses a set of scribble controls; it is not proof that the public Comfy nodes expose the upstream mesh-conditioned, reference-preserving geometry pipeline. Porting that specific path would require real engineering. [ComfyUI-MVAdapter](https://github.com/huanngzh/ComfyUI-MVAdapter)

Hardware numbers must stay variant-specific: upstream reports geometry-conditioned SDXL needing more than 16 GB, while its SD2.1 geometry example is reported below 10 GB. Community/offload claims for other variants are not proof that the preferred geometry route fits this PC. [Geometry SDXL script](https://github.com/huanngzh/MV-Adapter/blob/main/scripts/inference_ig2mv_sdxl.py), [geometry SD2.1 script](https://github.com/huanngzh/MV-Adapter/blob/main/scripts/inference_ig2mv_sd.py).

### AHA: front views are not inherently wrong

Unique3D explicitly prefers a front orthographic input and describes failures when shape extent is poorly visible. A three-quarter input can reveal useful depth to another model, but there is no universal best first angle independent of the model's training and camera assumptions. The truck and toy-camera experiments do not justify changing every model to the same input convention. [Unique3D input guidance](https://github.com/AiuniAI/Unique3D)

### AHA: rough-mesh feedback is real, but is not automatically an improvement

3D-Adapter reconstructs and renders guidance during generation; its paper includes comparisons showing that the way feedback is applied matters. Its inspected source uses controlled depth/RGB conditioning schedules. The fast GRM-based adapter is not released in the inspected repository, while the available optimization-oriented WebUI documents a 24 GB-class requirement. This supports the idea, but not a claim that its full pipeline is a ready 16 GB Comfy replacement. [Paper](https://arxiv.org/html/2410.18974v2), [released source](https://github.com/Lakonik/MVEdit)

UniForge3D is another approach to the missing-camera problem: joint reconstruction with geometric features and view selection. Fresh source shows staged model offloading and cached image features. However, its README separates MIT code from VGGT-derived noncommercial weights and additional dependencies. It remains a research comparison, not a commercial-use promise or an installed capability. [UniForge3D source and terms](https://github.com/xibushu/UniForge3D)

## 4. What each supported image family can actually use

The following distinguishes inspected graphs from merely plausible combinations. Camera LoRAs remain optional; their labels are learned guidance, not calibrated camera guarantees.

| Family | Verified relevant route | Recommended research role | Important limitation |
|---|---|---|---|
| **Klein 4B** | RefControl reference-plus-depth LoRA and actual Comfy graph | First structural-control candidate for the permissive, smaller-model route | Community training is human-heavy; object accuracy and our rendered-map convention need proof. |
| **Klein 9B** | RefControl reference-plus-normal and pose graphs | Optional comparison if 4B misses structure or characters need pose guidance | Different weights from 4B; memory and base-model terms differ. |
| **Qwen Edit 2511** | fal Multiple-Angles LoRA and actual Comfy graph; model-specific training script | Existing image-edit/reference route and angle baseline | No verified matching strict depth/normal ControlNet route was established in this pass. |
| **Qwen 2.1** | AnyAngle; Alibaba PAI Fun-Controlnet-Union; current native Comfy patch support | Strong conditional-license experimental lane | AnyAngle expects a rough RGB rendering; Fun controls are a different mechanism and their composition requires testing. |
| **FLUX 3 Klein** | Official local model/reference guidance; separate community angle work | Retain image creation/editing support | No equally verified structural-control or trained joint-view graph found here. Do not imply parity. |

### Klein RefControl: useful separation already exists

The 4B depth workflow places the depth control first and identity reference second using reference latents. The inspected example uses an undistilled base-model route, the adapter's trigger, and its own sampling settings. The 9B pose example uses DWPose; the normal example uses DSINE. These are specific combinations, not evidence that every variant supports every control type. [4B depth card and graph](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-4B-reference-depth-lora), [9B normal](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-9B-reference-normal-lora), [9B pose](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-9B-reference-pose-lora).

When the mesh renderer already provides a map, another AI depth/normal estimator should not be necessary merely to recover that same information. But rendered maps must match the adapter's expected depth direction, range, normal coordinate frame, channels, background, and framing. Replacing the preprocessor is a hypothesis to validate, not a free equivalence.

### Qwen 2.1: AnyAngle and Fun control are different routes

AnyAngle's instructions use a rough rendered image for viewpoint and another image for appearance. It was trained around that input structure. There is no verified basis here for replacing its RGB guide with a depth map and expecting unchanged behavior. Its card also acknowledges sensitivity to bad guide geometry. [AnyAngle](https://huggingface.co/lilylilith/QI_2.1_AnyAngle)

Fun-Controlnet-Union supports several structural conditions including depth, pose, edges, and inpainting. It is an actual control network, with additional memory demand. Fresh inspection found support in the **current local native** `QwenImageDiffsynthControlnet` patch path. A community wrapper's claim that native support is absent is stale relative to this installation. Reference-plus-control behavior still needs a real graph test; native class availability is not the same proof. [Official Alibaba PAI card](https://huggingface.co/alibaba-pai/Qwen-Image-2.1-Fun-Controlnet-Union), [community wrapper examined](https://github.com/b2renger/ComfyUI-QwenImage21-FunControlNet).

### Qwen Edit 2511: do not borrow another version's recipe

The inspected fal workflow combines the Multiple-Angles adapter with a four-step Lightning route and Qwen Edit-specific encoding. Its settings are not the undistilled Qwen 2.1 recipe. The adapter has discrete captioned camera positions, which can guide a turn but do not measure the resulting camera. The available DiffSynth training script also includes version-specific conditioning. [Adapter and graph](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA), [2511 training script](https://github.com/modelscope/DiffSynth-Studio/blob/main/examples/qwen_image/model_training/lora/Qwen-Image-Edit-2511.sh).

### FLUX 3: support the documented capability

The official local card distinguishes base and distilled sampling and documents reference-image behavior. That is useful for design/editing, but bounding-box placement and multiple references do not constitute calibrated 3D camera control. Keep its strengths visible without claiming the same angle-guidance guarantees as a trained structural route. [Official model card](https://huggingface.co/black-forest-labs/flux-3-image-klein)

## 5. New work that addresses the same problems

### Another Pixal turnaround workflow encounters the same issue

PixelArtistry publishes a Qwen 2.1 turnaround-to-Pixal graph. Source inspection shows a prompted four-panel image, deterministic splitting, background preparation, native cardinal-view conditioning, and GPU-oriented export. Its own notes discuss side views drifting toward three-quarter views. It is useful evidence that our problem is shared; it is not a demonstrated cure for exact camera consistency. Its layout instructions should remain protected when the subject prompt is enhanced. [Repository and actual workflow](https://github.com/pixelartistry/PixelArtistry-Pixal3D-Multiview)

### UltraTex: coordinated Klein texturing, not a new shape model

Released code dated October 3 includes Klein-based multiview texturing. It reduces work on background regions and uses a matching foreground-aware decoder. Released Klein LoRAs target 9B; source support for 4B does not mean a compatible 4B checkpoint is supplied. Albedo and metallic/roughness use separate branches. The author's speedups compare against their dense baseline and are not timing predictions for this PC. [Official code and checkpoint layout](https://github.com/yiboz2001/UltraTex), [paper](https://arxiv.org/html/2609.23169v1).

The community Comfy graph was inspected along with its active `core/conditions.py` and `core/sampling.py`: a mesh produces normal-map conditions; foreground normal tokens and reference tokens are kept distinct; sampling uses the trained texture route; a surface baker exports the result. This is a real implementation pattern worth studying. Windows kernel compatibility, peak memory, and texture fidelity remain untested here. [Community Comfy port](https://github.com/Mstafa-awad/UltraTex-ComfyUI-nodes)

**Usefulness:** it may improve material consistency after geometry is accepted. It cannot repair a squeezed body, missing handle, or wrong wall thickness. It should not become an excuse to expand this iteration into another renderer project.

## 6. Training our own: a practical hypothesis, not a promise

Brian's camera-captioned dataset idea has a real foundation. It becomes much stronger when training pairs include **the same object's appearance reference, target image, exact camera, and structural maps**, rather than unrelated silhouettes with angle labels.

| Dataset or trainer | Useful material | What must be checked before use |
|---|---|---|
| Objaverse-Ortho10View | Matched RGB, depth, normals, camera metadata, including top/bottom | Orthographic projection; underlying object licenses; canonical-front quality. |
| Objaverse-Rand6View | Other views of matching object identities | Pair by object ID; do not mix camera conventions. |
| G-buffer Objaverse | Geometry buffers and camera information at scale | Asset rights and exact render conventions, not only repository code license. |
| G-buffer TexVerse | Normals, position maps, alpha, material images, poses/intrinsics, reference views | Dataset card declares CC0; retain source provenance and verify the selected release before a training download. |
| DiffSynth 2511 trainer | Model-specific LoRA training example | Large-base memory needs; no measured 16 GB fit established here. |
| MV-Adapter training | Separate multiview/reference modules with released configuration | Heavier architectural training; not equivalent to a small style LoRA. |
| OminiControl | Released custom conditional training on FLUX.1 | An architecture/trainer precedent, not Klein-compatible weights. |

[Ortho10View](https://huggingface.co/datasets/huanngzh/Objaverse-Ortho10View), [Rand6View](https://huggingface.co/datasets/huanngzh/Objaverse-Rand6View), [G-buffer Objaverse](https://github.com/modelscope/richdreamer/blob/main/dataset/gobjaverse/README.md), [G-buffer TexVerse](https://huggingface.co/datasets/YiboZhang2001/G-buffer-TexVerse), [OminiControl](https://github.com/Yuanshi9815/OminiControl).

TexVerse supplies both canonical and wider spherical camera configurations, plus separate camera-space and world-space normals. Its larger released pool and smaller paper training subset explain the differing asset counts; they are not interchangeable benchmark sizes. No dataset archives were downloaded.

If existing adapters leave a demonstrated gap, the first custom-training candidate should be a **Klein 4B geometry-plus-reference adapter**, with a narrow objective: preserve object identity while obeying a supplied structural view. That choice follows licensing, model size, and the nearby RefControl precedent; it is not a measured claim that Klein will outperform Qwen.

Training requirements:

- Split by object, not by image. Otherwise views of the test object leak into training.
- Include asymmetric props, thin parts, and characters. Camera orientation and body pose need separate labels.
- Keep all views of one example geometrically consistent. Randomize appearance and lighting independently where appropriate.
- Include the kinds of imperfect proxy geometry encountered at inference, while preserving known target truth. This proposed augmentation needs an ablation.
- Track silhouette, proportions, part count, and held-out-view geometry, not just attractive samples.
- Compare with the existing adapter before and after training on the same unseen objects.
- Start with a small memory/step-throughput pilot. Training hours, cloud cost, and local feasibility remain unknown until measured; inference offloading does not prove training will fit.

A larger joint-view adapter could be a later research investment. It should not be the first response to a camera-coordinate or cropping bug. OminiControl's configurable conditional training and MV-Adapter's released training modules show that such customization is real; neither removes the need for a backbone-specific implementation.

## 7. Backgrounds, geometry, finishing, and memory

### Background removal belongs in every applicable route

Preserve the original image and a separately editable alpha mask. If valid transparency already exists, do not unnecessarily estimate it again. For generated or uploaded opaque images, offer automatic segmentation and the existing mask editor. Preview thin legs, handles, holes, hair, antennae, and object shadows before reconstruction. A background mask is not a camera correction.

Pin the **actual weights**, not just a node named BiRefNet. The original ZhengPeng7/BiRefNet card declares MIT, whereas BRIA RMBG-2.0's local weights require a commercial agreement for commercial use. A loader default can change the licensing of a supposedly permissive route. The inspected MV-Adapter example and loader defaults are not identical on this point. [Original BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet), [BRIA terms](https://huggingface.co/briaai/RMBG-2.0).

### Helpful components are not necessarily optional adapters

Pixal's DINOv3/NAF feature processing and MoGe camera estimation perform supporting inference jobs. They should not be swapped as though they were interchangeable style LoRAs. Multiview weights also differ from single-image weights. Features, camera metadata, and stage conditioning must remain paired with the reconstruction model they belong to. The inspected upstream and native conditioning paths establish these roles; they do not establish a category-specific magic LoRA for cleaner geometry. [Pixal3D](https://github.com/TencentARC/Pixal3D)

Expose useful controls with model-aware explanations:

| Control | Plain-English meaning | Recommended treatment |
|---|---|---|
| Reconstruction resolution | How finely the model can represent shape | Start with the documented route default; higher can cost much more memory and cannot recover contradictory evidence. |
| Sparse-structure steps/guidance | How the initial occupied structure is sampled and conditioned | Expose separately from shape sampling; do not copy image-model CFG rules. |
| Shape steps/guidance | How detailed geometry is sampled from the image evidence | Show the checkpoint's recommendation and preserve values in history. More is not guaranteed to be better. |
| FOV / camera source | The perspective assumption used to interpret pixels | Show whether measured, rendered, estimated, or manually entered. Never silently label a requested angle as known. |
| Face target | How much geometry remains after simplification | Preserve a high-detail master; thin parts may require more faces than solid props. |
| Remesh and smoothing | Changes to the actual surface | Optional and measured. Excess smoothing can erase mechanical edges, holes, or small details. |
| UV/texture quality | How the surface appearance is stored | Separate from geometry-only export. Do not force UV work when only a shape is wanted. |
| Seed | Repeatability for a specified model and recipe | Save the actual seed used. Reusing one seed across different views does not impose shared 3D geometry. |

Category presets should be modest, visible defaults derived from evidence. A thin mechanical part and a solid prop may need different preservation settings; a character needs pose and identity checks. This research did not establish authoritative numerical CFG/step presets for every category. Do not invent them under the label of official guidance.

### GPU finishing: retain the requirement, describe it accurately

Fresh local source inspection confirms `UnwrapMesh` selects a GPU device for PEC segmentation and a CPU device for the adaptive alternative. GPU decimation code is also present. Some array handling, packing, serialization, and orchestration still use the CPU. Therefore the promise should be **GPU-intensive finishing with visible resource use**, not literally zero CPU work.

`MeshSmoothNormals` changes surface shading normals, not the underlying vertex positions. It cannot repair a bumpy print. Remeshing, surface smoothing, simplification, UV generation, and texture baking must be evaluated separately. Preserve the raw mesh before these operations; compare silhouettes and thin features after them. A texture normal map can improve game shading but cannot add physical print geometry.

For prints, check watertightness, self-intersections, thickness, disconnected pieces, orientation, and physical scale. For games, check face budget, UVs, materials, normals, and silhouette preservation. One export preset should not pretend these requirements are identical.

Local owners inspected: `comfy_extras/nodes_mesh_postprocess.py` (`UnwrapMesh`, `MeshSmoothNormals`), `comfy_extras/mesh3d/postprocess/qem_decimate.py`, and the extension's finishing recipes. Runtime speed and memory still require measurement; source inspection alone is not a benchmark.

### Memory should be a stage contract

The current lifecycle code already coordinates idle-boundary unloading. Extend and prove that behavior rather than adding a second resource manager. The intended sequence is text conditioning, image generation, segmentation/control preparation, reconstruction, then finishing, with only the required heavyweight models resident at each stage. Save reusable CPU/disk results, release no-longer-needed model and tensor references, and check actual headroom before the next stage.

An empty allocator cache does not free live tensors. CPU offload can also consume substantial system RAM. Record process RAM and GPU allocations, avoid keeping multiple high-resolution feature batches unnecessarily, and bound caches by job ownership. Current Pixal conditioning creates several resolution/stage feature sets, so view count has a real memory cost. Do not present an arbitrary VRAM slider as a hard guarantee unless the owning backend enforces it.

Retain an obvious unload control and resource display. Prevent it from corrupting an active job. If an operation cannot fit on the GPU, reduce the supported workload or show the condition; do not silently substitute a long CPU path after the user selected GPU finishing.

## 8. Licensing conclusions that affect the choice

This is a reading of the linked published terms, not a substitute for checking the exact release and intended business use before distribution. Code, base-model weights, adapter weights, datasets, and generated outputs are separate layers.

| Model/component | Finding as checked on 2026-10-21 | Suitable UI wording |
|---|---|---|
| Qwen Edit 2511 | Apache-2.0 base model | Commercial use allowed under the linked terms. |
| Klein 4B base | Apache-2.0 base model | Commercial use allowed under the linked terms. |
| Qwen 2.1 and inherited routes | Research/evaluation license; commercial model use requires separate authorization | Commercial use requires authorization; show the official request details. |
| Klein 9B base | Noncommercial model-use license; its output clause separately permits commercial output use subject to restrictions | Model use has conditions; explain output rights separately rather than saying every sale is prohibited. |
| FLUX 3 Klein | Kommunity license permits commercial output generation by qualifying users below the stated US$5M gross annualized revenue threshold, including affiliates, subject to terms | Commercial use has conditions; show eligibility and license details. |
| UniForge3D | MIT code does not clear the noncommercial VGGT-derived weights or background-removal dependency | Research option pending full dependency/license review. |
| UltraTex Klein route | MIT code plus separate trained components and conditional-license 9B base | Review the complete selected checkpoint chain; not a blanket permissive route. |

Primary terms: [Qwen Edit 2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), [Klein 4B base](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4B), [Qwen 2.1 license](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE), [Klein 9B license](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B/blob/main/LICENSE.md), [FLUX 3 license summary and link](https://huggingface.co/black-forest-labs/flux-3-image-klein).

The accepted decision to offer conditional-license options can remain. Show the exact model and conditions, link the authoritative terms, and record the selected model revision with the job. An Apache adapter does not remove restrictions from the base it modifies. Likewise, a permissive image-model label is not a commercial clearance for every component of the eventual image-to-mesh pipeline. A distributable release still needs an exact dependency and weight manifest.

## 9. Recommended next iteration

**Keep:** the current human-facing workflow, image editor, approvals, history, parameter controls, background-mask review, and resource management. Research has not justified throwing these away.

**Change first:** the hidden image/camera contract and its proof. Store whether camera information is known or estimated; prevent incompatible projection/framing assumptions; expose which references a mesh branch actually consumes. Use deterministic render-derived maps where they are available and convert them for the selected adapter.

**Compare next:** the existing direct route against a controlled second pass using Klein 4B RefControl depth. Keep Qwen 2.1 AnyAngle as its own optional RGB-guide route, with licensing and guide-shape limitations. Do not silently convert AnyAngle into a different depth-only workflow.

**Investigate as the next architectural alternative if needed:** MV-Adapter's trained joint-view route, including a matched reconstruction method. Its orthographic geometry example must not be fed to a perspective-only path with invented calibration. A small dedicated SD2.1/SDXL comparison may teach more than another large sweep over generic prompts in all five families.

**Do not make mandatory:** four pictures → first mesh → eight pictures → second mesh. The second pass is useful only if it demonstrably improves shape. Eight well-chosen requested views can be offered, but the number of images is not the quality target. Extra contradictory views can hurt, and repeated generations conditioned on the same wrong proxy can repeat its errors.

**Defer pending evidence:** custom training, UltraTex integration, UniForge deployment, paid compute, new UI categories beyond useful defaults, and any Pinokio implementation. These are potential follow-ons, not unfinished repairs disguised as completion.

## 10. A finite validation experiment for the next authorized implementation

This is the proposed proof of the next approach. It has not been run. Numerical thresholds below are proposed engineering acceptance rules, not values established by a paper.

### A. Prove the reconstruction input contract first

Use three licensed ground-truth meshes: an asymmetric toy/house with recognizable side details, a thin mechanical part, and a posed humanoid. Render four exact views with saved cameras, masks, and image transforms. Validate coordinate conversion and reprojection before invoking AI; a suggested implementation tolerance is under one pixel at the chosen test resolution on visible landmarks.

Make at most three oracle-input Pixal reconstructions, one per object. Compare with the known meshes. If exact images and correct cameras still reconstruct badly, identify that model or integration limit before paying for generated-view tests. Do not try to fix an oracle-input failure with better image prompts.

### B. Compare three complete routes, without a parameter fishing expedition

Use the same three objects and two fixed seed sets. Freeze source references, route-specific documented settings, checkpoint revisions, masks, and scoring rules before running:

1. **Single-image baseline:** one informative input, Pixal single-image path.
2. **Four-view baseline:** the current four-view generation strategy with the validated camera/framing path. Retain estimated-camera labels where necessary.
3. **Structural second pass:** use route 2's draft, render eight structural guides from one rig, generate guided images with Klein 4B RefControl and approved appearance references, then reconstruct with the matching metadata. Check output deviations; the guide camera is not automatically the generated image's true camera.

This is at most **18 scored route results**, reusing the route-2 draft for route 3 rather than regenerating it. Together with the three oracle runs, the planned ceiling is 21 mesh reconstructions before finishing. It is a small screening study, not statistical proof of universal superiority.

No automatic angle regeneration loop during the scored comparison. Record failures and view rejections. Use the same acceptance rule for every object; retain counts of requested, accepted, and actually consumed views. Human-assisted recovery can be measured separately, with a fixed allowance, rather than mixed into an allegedly automatic success rate.

### C. Score geometry before textures

- Held-out-view silhouette agreement, including views never supplied to reconstruction.
- Surface distance and normal consistency against ground truth where valid. Alignment may use rigid transform and one uniform scale; independent axis stretching must not conceal bad proportions.
- Width/depth/height ratios, number and location of salient parts, missing holes or thin structures, duplicated details.
- Mesh validity, disconnected pieces, physical scale, and print-specific thickness checks.
- Human review of recognizable identity and usability. Keep these judgments separate from geometric measurements.
- End-to-end time, peak GPU/process RAM, actual offloading, export time, and whether any CPU fallback occurred.

For genuinely invented assets without ground truth, report agreement and human usefulness scores, not fictitious absolute accuracy.

### D. Stop and choose

A proposed promotion threshold is at least a 10% median reduction in the chosen normalized geometry error, improvement in at least two of the three categories, and no new catastrophic failure in the third. The single-image or first-mesh result remains available whenever the extra pass loses. Report confidence limitations from the small sample.

Finish only the three selected representative winners through the GPU-oriented export path. Verify that the exported mesh preserves their shape and can be reopened, and that resources are released. A pretty preview is not export proof.

At the end, deliver the comparison, one recommended default route, its known failure cases, and a clear decision on whether a custom trainer is justified. Do not expand automatically into every model, adapter, step count, or view count. If the screen finds no winner, that is a valid finding and a discussion point—not a reason for endless tiny prompt changes.

## 11. Coverage, unresolved facts, and research stopping point

| Plan item | Answer location | Remaining uncertainty |
|---|---|---|
| R1: current lessons | Section 1 | No ground-truth toy-camera mesh; relative improvement is not absolute accuracy. |
| R2: reconstruction choices | Sections 1 and 3 | Runtime quality of alternatives on this PC remains untested. |
| R3: five-family controls | Section 4 and saved graphs | Qwen reference-plus-Fun composition and FLUX 3 structural parity unproven. |
| R4: joint views/characters | Sections 2–4 | Cross-category quality and normal/pose conventions need the bounded comparison. |
| R5: custom opportunities | Sections 2, 6, and 9 | No custom training or new camera fitting implemented. |
| R6: prep/finishing | Section 7 | Real peak memory and speed, plus print checks, need runtime evidence. |
| R7: data/resources/licenses | Sections 6–8 | Exact training cost and a complete distributable dependency manifest remain unknown. |
| R8: recommendation/proof | Sections 9–10 | The next product implementation requires discussion and authorization. |

Recent discovery searches included the last-month window, September 21–October 21, 2026. UltraTex and UniForge were traced to current papers and source. An official UltraTex YouTube link was found but video access was throttled; no usable transcript was obtained. **No claim here depends on having watched that video.** The PixelArtistry graph was inspected directly rather than inferred from a tutorial. Reddit and video popularity are not treated as quality evidence.

The research goal is complete when this report and its source register are saved and checked. The next action is Brian's discussion of the proposed comparison, not a background installation or another generation run.

## Local evidence and reproducibility

Project root: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI`.

Containing Git checkout inspected at detached commit `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`; an existing untracked `comfyui-mcp/` was present. The extension is ignored by that containing checkout, so the commit alone does not identify its contents. Relevant local source hashes and public source revisions are recorded in `SOURCE-REGISTER.md` and the `sources` manifests beside this report. No commit, push, restart, or product installation was performed for this research.
