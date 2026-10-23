# Mumblebox: coordinated views, camera compatibility, and a better first mesh

Research completed: 2026-10-22. Target: Windows, 16 GB GPU memory, 64 GB system RAM.

**This is a research result and a proposal for discussion. No new workflow has been implemented or tested during this research.** Comfy, its models, existing Mumblebox, and the completed experiment were not changed. Source files and these research documents were saved in the established E: research directory. No weights, installations, generation, training, or paid services were used.

## The recommendation in plain English

Try a specialist that makes the views **together**, rather than asking a general image editor to invent each view separately. Start from the user's approved image; use SDXL plus the released image-conditioned MV-Adapter to generate its trained set of six views; preserve their framing and camera information; reconstruct **one** mesh; inspect it; then finish and export it on the GPU.

My primary recommendation is **conditional MV-Adapter → Pixal3D** because it can reuse the locally exercised reconstruction, memory handling, and textured-export machinery. It is not a plug-and-play recommendation. First prove a correct orthographic projection bridge with known geometry. If that bridge cannot preserve useful reconstruction, reject the combination before an image-generation campaign. The one fallback is the paper's better-matched family of reconstruction: **MV-Adapter → StableNormal → orthographic NeuS**, using the released Era3D reconstruction implementation as the engineering reference. Its Windows, memory, normal-coordinate, and export integration must pass a separate early gate.

This ordering is my practical engineering judgment, not a published claim that MV-Adapter works with Pixal3D. The scientific advantage of the fallback is its matching camera model; the practical advantage of the primary is reuse of the working local mesh/export machinery. Neither is a locally proven solution yet.

**Do not train a new adapter first.** The released coordinated-view adapter can test the central hypothesis without a training project. Brian's lighter Klein/Qwen suggestion is credible and remains a targeted follow-up: a small camera LoRA may be sufficient. The evidence does not establish that a larger adapter is inherently necessary, or that any particular LoRA already produces reconstruction-grade camera accuracy.

The practical standard is a useful mesh with manageable corrections. Human review and a few targeted image edits are allowed. Ten perfect images, zero manual intervention, photorealism, or watertight output on every object are not the success criteria. All corrections must be counted so they cannot hide a weak automatic result.

## What changed in our understanding

Three findings materially affect the next experiment:

1. **There is a real architectural difference to test.** MV-Adapter adds trained reference and cross-view attention to a frozen diffusion backbone. Six pictures generated in one coordinated batch are different from six independent angle prompts or a contact-sheet instruction. The author provides an actual image-conditioned Comfy graph, not only a text-to-image demo. [Attention implementation](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/models/attention_processor.py), [image-conditioned graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_diffusers.json).
2. **Good-looking views can still enter reconstruction with the wrong camera mathematics.** Released MV-Adapter I2MV uses orthographic target cameras. Inspected Pixal feature projection is perspective. Assigning matching angle names does not resolve that difference. A bridge is possible, but has to be proven. [MV camera construction](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/scripts/inference_i2mv_sdxl.py), [Pixal projection training code](https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/pixal3d/trainers/flow_matching/mixins/image_conditioned_proj.py).
3. **A small custom LoRA is a practical possibility, not wishful thinking.** BFL documents consumer-GPU Klein 4B training, and a released Qwen camera LoRA uses paired synthetic renders. These support a bounded, inexpensive future experiment. They do not prove that angle accuracy, identity preservation, and downstream mesh improvement will all follow. [BFL training guidance](https://docs.bfl.ai/flux_2/flux2_klein_training), [Qwen camera LoRA](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA).

## What the previous experiment actually established

The canonical local evidence is [the completed experiment's results](../../../../mumblebox_camera_experiment/RESULTS.md). Those are earlier runtime results; they were read, not rerun here.

True consistent views with correct cameras improved the six controlled full-master fixtures. In contrast, the draft-mesh/depth/Klein/estimated-camera/second-mesh route did not meet its improvement gate. Recorded generated vehicle and creature reconstructions were substantially worse than their independent controls. Camera estimates sometimes had large errors. Reduction could create holes, while a median distance score concealed visually important damage.

Keep the original pictures, full masters, correct image transformations, device/precision repairs, memory release, and GPU finishing work. Retire the failed runtime feedback route. A single-image control in a future experiment is an independent baseline, not a draft mesh fed back into image generation.

These failures do **not** prove all camera LoRAs are useless, all multiview reconstruction is bad, or one image is always enough. They establish that invented geometry, inconsistent pictures, approximate camera estimates, and damaged derivatives must not be combined and then mistaken for an adapter-quality test.

## The complete proposed primary path

| Stage | What happens | Exact component or responsibility | What exists / what must change |
|---|---|---|---|
| 1. Starting image | Upload an image, or create one with an already supported image model; approve it. | Existing Mumblebox image and mask tools. | Exists. No requirement to use SDXL for the original design. |
| 2. Object isolation | Keep the original; obtain alpha; make a documented square reference frame. | Explicit `ZhengPeng7/BiRefNet`, or the user's accepted alpha. | Model and reference preprocessing recipe exist. Preserve the crop/pad transform; do not install a different default remover silently. |
| 3. Coordinated views | Generate six RGB views in one batch from the approved reference and a concise object description. | `stabilityai/stable-diffusion-xl-base-1.0`, `madebyollin/sdxl-vae-fp16-fix`, `huanngzh/mv-adapter/mvadapter_i2mv_sdxl.safetensors`. | Author pipeline and Comfy graph exist. Current-environment compatibility and explicit model ownership need integration. |
| 4. Review and masks | Inspect the whole set for mismatched parts, sides, size, and clipping. Save masks without recropping each picture. | Existing review capabilities plus a camera-bearing view bundle. | Review UI need not change for this experiment; bundle/provenance must be added to the independent test. |
| 5. Release image stage | Drop live image pipeline, reference features, text encoders, VAE and remover ownership. | Existing Comfy management where supported; explicit cleanup for custom Diffusers objects. | Custom loader does not automatically become Comfy-managed. A free-memory button alone is insufficient. |
| 6. Reconstruct once | Feed RGB, masks, explicit projection, and correctly transformed cameras into the multiview model. | Existing Pixal multiview weights; new, validated orthographic projection support. | Perspective path exists and was exercised. Orthographic consumption is **not implemented or proven**. |
| 7. Inspect full master | Check silhouette, proportions, thin parts, holes and side-specific features before reduction. | Existing mesh inspection/export machinery and declared fixture criteria. | Exists in pieces; acceptance must refer to the full master. |
| 8. Optional texture and finish | Generate texture only for accepted geometry; release heavy models; GPU unwrap/bake; save. | Existing Pixal texture path, native `UnwrapMesh` with PEC, voxel texture bake, GLB export. | Existing path was exercised earlier. Verify the actual final files for the new route. |
| 9. Geometry-only / print | Bypass UV and texture generation when only shape is wanted. | Full geometry export plus print diagnostics. | Do not describe a raw mesh as print-ready without checking closure, thickness, intersections and scale. |

The author graph uses 768 × 768 targets, six views, 50 sampling steps, CFG 3, reference strength 1, and shifted DDPM sampling. Preserve that baseline before changing a model, style, scheduler, or guidance. These are the released inference-example settings, not a claim of optimum settings for every object. Its training validation configuration has different step settings; do not silently mix them. [Diffusers graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_diffusers.json), [training configuration](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/configs/view-guidance/mvadapter_i2mv_sdxl.yaml).

A description is useful for naming the object and visible design. It does not replace the reference image, camera conditioning, or shared attention. Avoid broadcasting a front-only feature as something that must appear in every target image. Do not use one universal enhancement recipe for different model families. No prompt-enhancer or GUI work is proposed in this research phase.

## Camera compatibility: solvable mathematics, unproven model behavior

### Why the distinction matters

Orthographic projection keeps size independent of depth. Perspective projection makes nearer parts larger. A correct camera rotation can therefore still produce incorrect feature-to-surface alignment if the projection is wrong.

The released MV-Adapter inference code requests azimuths `[0, 45, 90, 180, 270, 315]`, all at zero elevation, then subtracts 90 degrees when constructing its world-space camera. Its orthographic frame spans 1.1 units. Its camera-map condition is a **Plücker ray representation**—a description of viewing rays, not a depth image of the object. The model still has to infer object structure. [Inference implementation](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/scripts/inference_i2mv_sdxl.py).

Locally inspected `comfy/ldm/trellis2/model.py` projects using focal length and divides by camera depth. Its coordinate transform and object normalization also matter. Existing `MX_PixalCameras` work supports pinhole intrinsics and image transforms; that does not establish orthographic support. The official Pixal conditioning renderer likewise uses perspective intrinsics. [Official renderer](https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/data_toolkit/blender_script/render_cond.py).

### Three possible bridges, with different guarantees

1. **Direct orthographic projection in the reconstruction integration.** Use the known viewing rays and linear scale instead of a pinhole depth division. This is the preferred proposed primary bridge. All relevant sparse-structure, shape and texture feature projections must agree. Correct mathematics does not prove a perspective-trained model will accept the new conditioning distribution well; ground-truth controls decide that.
2. **Distant perspective approximation.** Move the virtual perspective camera away and increase its focal length to preserve framing. This can approach orthographic projection closely. It is a legitimate candidate, not an impossible conversion. It must be evaluated against a known object-depth range and the model's normalization, precision and camera assumptions—not by typing a guessed FOV into the UI.
3. **Reproject an image using depth.** Accurate depth allows visible pixels to be moved between camera models. It does not reveal hidden surfaces; holes and depth errors need handling. A single RGB image has no universal exact orthographic-to-perspective conversion.

For clarity, the approximation can be described without guessing: for image width `N`, orthographic span `S`, and a reference plane at distance `d`, choose focal length in pixels `f = N*d/S`. At the reference plane the projections match. A point displaced toward the camera by `z` has a relative scale discrepancy `z/(d-z)`. This is a derived pinhole calculation, **not a measured Pixal result**. Increasing `d` reduces the mathematical error, but does not certify model quality.

The future camera gate checks known landmarks to roughly one-pixel tolerance, includes wrong-order/mirror/crop negative controls, and reconstructs true rendered views before any generated batch. Do not call requested camera labels measured camera accuracy. An AI image can disobey its requested pose even when our matrices are correct.

Keep target images in their original generated frames. A foreground mask may change; image coordinates must not change silently. Any intentional resizing/cropping needs its corresponding transform applied to the camera. Preserve projection type, image size, camera-to-world convention, frame transforms, object normalization, mask version, source hash and view order together.

## The one fallback: a reconstructor that already expects orthographic views

The MV-Adapter paper evaluates reconstruction using generated RGB, StableNormal predictions, and a NeuS reconstruction approach based on Era3D. Its reported improvements are evidence for that research configuration, **not** a comparison against this machine's Pixal workflow. [Paper, reviewed arXiv version](https://arxiv.org/html/2412.03632v1).

The fallback would retain the same approved input and six-view generator, then run:

`six RGB views + alpha → StableNormal → correctly transformed normals → Era3D orthographic NeuS → full mesh → GPU finishing/export`.

The released orthographic dataset and reconstruction code are concrete reuse candidates. They are not a ready-made Mumblebox plug-in. Important work remains:

- Map view order and camera conventions explicitly. Convert camera-local predicted normals to the coordinate convention expected by the reconstruction dataset; filenames alone do not perform that conversion.
- Feed accepted RGB-derived masks. Do not independently segment normal-map colors as if they were photographs.
- Validate Windows CUDA dependencies, ray chunking, extraction memory, and the selected surface extractor. The default code offers extraction paths with different CPU/GPU behavior; an available CPU fallback does not satisfy Brian's heavy-stage GPU requirement.
- Expose optimization iterations and extraction resolution honestly. These are per-object surface fitting, not training a general-purpose image adapter.
- Build a valid color-export bridge. A NeuS vertex-colored mesh is **not** Pixal's voxel/latent texture object. Native `BakeTextureFromVoxel` cannot simply be attached to it. A GPU vertex-color/radiance-to-UV bake or another explicit, licensed bridge would be needed for a textured GLB. Do not fabricate metalness and roughness provenance.

Sources: [orthographic dataset](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/datasets/ortho.py), [reconstruction configuration](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/configs/neuralangelo-ortho-wmask.yaml), [surface extraction](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/geometry.py), [StableNormal](https://github.com/Stable-X/StableNormal).

Fallback activation is a review decision within the shared experiment limits, not permission to start a second unlimited project. If neither route has a defensible camera contract and a viable GPU path, stop with a negative result.

## SDXL, Juggernaut and style options

Use official SDXL base as the baseline. The one derivative candidate is **RunDiffusion/Juggernaut-XL-v9**, specifically `Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors`, an ordinary SDXL derivative. Do not substitute Lightning, a FLUX-based Juggernaut, or a newer unrelated architecture because the name matches. Architecture makes it a plausible candidate; no verified author I2MV-to-mesh result for this exact checkpoint was found. [Model card](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9).

The author's image-conditioned LoRA graph really connects the reference image through the multiview pipeline. This is stronger evidence than a text-only style demonstration. However, the example's named style file does not establish that file's provenance or redistribution terms. Use at most one separately licensed, compatible style LoRA after geometry success. Anime examples elsewhere do not certify every anime checkpoint or image-conditioned style combination. [I2MV LoRA graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_ldm_lora.json).

The standard release is six level views. The beta changes supported view counts; that is not proof of unrestricted elevations. Geometry-conditioned variants require geometry and serve another purpose. Their top/bottom demonstrations cannot be transferred to standard first-mesh I2MV by changing a menu label. No arbitrary eight- or ten-view requirement should be imposed on this release.

## Memory, speed and Windows compatibility

The inspected desktop environment reports Python 3.13.12 and Torch 2.12.1+cu130, with Transformers 5.16.1. The author Comfy adapter pins older Diffusers/Transformers dependencies. Diffusers and PEFT were not installed in this inspected environment. A recent issue reports a CLIP loader failure with a similar modern stack; it is a compatibility warning, not a local reproduction or a valid Juggernaut quality test. [Author requirements](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/requirements.txt), [issue 107](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/107).

For a future independent experiment, prefer a version-isolated image-stage environment, controlled visibly from the existing Comfy graph, over downgrading the desktop's working packages. That worker is a proposed compatibility boundary, not something created here. Check the actual GPU architecture against the chosen Torch/CUDA build before pinning a runtime; copying an old requirements file is not sufficient.

The author reports roughly 13–14 GB image inference usage, which makes 16 GB plausible but close. That number is not a verified peak on Brian's card. Startup copies, the reference encoder, background remover, VAE decoding, and retained objects can consume the remaining headroom. [Author resource notes](https://github.com/huanngzh/MV-Adapter).

Ownership policy for the future test:

- Keep the image model loaded through one coordinated batch. Splitting that batch into independent image jobs would defeat the mechanism being tested.
- Cache completed text embeddings when compatible, then release encoders when safe. Do not unload modules mid-forward pass.
- Decode with supported VAE slicing if needed. Do not assume arbitrary sequential offload preserves custom attention; a community wrapper explicitly warns about that interaction.
- Release live pipeline/reference/remover objects between image, reconstruction, and finishing stages. `empty_cache()` cannot free tensors still referenced by a loader or closure.
- Set a proposed reserve of about 1.5 GiB GPU memory and 8 GiB available system RAM. Measure actual peaks; do not fill memory deliberately to test recovery.
- Keep caches, models, intermediates and output under the designated E: installation/project paths. Do not copy the old large checkpoints repeatedly. Keep one recoverable selected master/state and delete only owned disposable intermediates after validation.

These are proposed policies. Memory release and speed must be measured in the later installed workflow, including cancellation and failure cleanup. CPU file I/O is normal; replacing GPU unwrap/bake or inference with a slow CPU fallback is not.

## Mesh quality, finishing and usefulness

The full reconstruction is the quality reference. A reduced mesh that looks smoother but loses a hole or thin handle is not an improvement. Preserve master and game derivative separately with their parameters and source images.

The existing local finish graph uses a GPU resampling path when needed, smooth normals, PEC UV segmentation, voxel texture baking and GLB saving. Earlier tests showed that resampling can soften details and remain high-poly; it is not universal cleanup. Existing QEM reduction damaged some subjects. Therefore no automatic “game-ready” label follows from a polygon-count target.

Expose relevant knobs in an eventual implementation: reconstruction resolution, sparse-structure/shape steps and guidance, geometry seed, texture steps/resolution, finishing method, reduction target, UV settings and geometry-only export. Show the recipe's own defaults and distinguish input camera FOV from shape quality. Do not invent category-specific defaults from intuition. The three varied fixtures can supply initial evidence; category tuning is a later, measured change.

For games, inspect topology, UV validity, materials, silhouette, thin parts, scale and triangle count. For prints, inspect manifoldness, closure, intersections, disconnected pieces, thickness and physical scale. Neither task is certified by a successfully opened GLB alone.

AI plus Blender cleanup versus Blender-first remains asset-dependent. A curved organic shape and a grid-aligned spaceship connector have different costs. No token or time saving can be promised from source research. A later equal-time comparison on one representative mechanical part is more informative than another broad model sweep; it is outside the proposed generation campaign unless separately approved.

## T3lescope and Gaussian Wrapping

**T3lescope is a promising research lead, not an installable solution in this audit.** Preferred Networks and the University of Tokyo describe posed multiview generative surface reconstruction, with coarse-to-fine cells and shared generators. The project page still says code is forthcoming. No usable release/weights/license package was verified. [Official project](https://pfnet-research.github.io/t3lescope/).

Its paper's large-scene hardware examples use substantially more than 16 GB, including H200 runs with 36–79 GiB reported across cascade levels. Those measurements do not establish a minimum for a small object, but they also do not establish a viable six-image 16 GB path. Watch for code, weights, terms and a small-object benchmark; do not block the current experiment waiting for it. [Paper, especially Appendix H](https://arxiv.org/html/2610.03308v1).

**Gaussian Wrapping is a different, released reconstruction approach.** The exact project is *From Blobs to Spokes: High-Fidelity Surface Reconstruction via Oriented Gaussians*. It fits a scene from posed photographs and sparse reconstruction data, then derives/refines a surface. It is not a drop-in LoRA, a single-image completion model, or a generic “wrap this Pixal mesh” button. Its published implementation has noncommercial restrictions and an unverified Windows/16 GB path. Keep it as a real-capture research reference, not the commercial Mumblebox default or another fallback. [Author repository](https://github.com/diego1401/GaussianWrapping), [license](https://github.com/diego1401/GaussianWrapping/blob/11e3b6fb5ca6f0a54e2b5587a09693488f3655af/LICENSE.md).

## What a custom adapter would actually need

Brian's Blender dataset idea has a concrete foundation. The MV-Adapter authors release paired-view dataset descriptions, rendering tools and training configuration. A useful training example associates a source view with target views of the **same** object, known camera transforms/projection, object normalization and captions. Random unrelated silhouettes labeled “left” and “right” teach weaker associations and can confuse orientation with object identity. [Training data implementation](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/data/multiview.py), [renderer](https://github.com/huanngzh/bpy-renderer).

Depth is optional, not an automatic requirement:

| Information | Role | Requirement for the proposed training investigation |
|---|---|---|
| Source RGB and corresponding target RGB | Teaches how this object changes under a camera move. | Essential for paired image-edit training. |
| Source/target cameras, projection, object frame and crop transforms | Makes angle/scale labels meaningful and permits geometric evaluation. | Essential ground truth for a serious camera task, even if a basic LoRA consumes angle words rather than matrices. |
| Foreground alpha | Separates shape from the background and protects framing. | Strongly recommended; cheap to render exactly. |
| Object identity and held-out family split | Prevents apparently good results from memorizing the test objects. | Essential evaluation metadata. |
| Depth and surface normals | Can supervise geometry or provide optional controls. | Save them if cheaply available; do not require them at inference unless the chosen architecture actually consumes them. |
| Visibility / correspondences | Can support a later consistency loss or view selection. | Useful optional research data, not an existing universal adapter input. |
| Caption / requested camera change | Tells the model what to preserve and which movement to perform. | Model-specific grammar; distinguish relative movement from absolute object-facing labels. |

Depth contains **shape**, not just camera orientation. An adapter cannot be promised to extract only camera information while ignoring all geometry encoded in a depth guide. A camera-ray condition is a cleaner way to represent the camera itself; the reference image supplies appearance and the learned prior supplies unobserved structure. Whether a light LoRA learns enough of that separation is a testable hypothesis.

For owned synthetic data, vary shapes, asymmetric features, materials, lighting, backgrounds, starting viewpoints and distances independently. Hold out whole objects and some whole shape families. Include genuine backs and undersides. Boxes are excellent calibration fixtures but inadequate evidence of generalization to people and irregular objects. Existing Objaverse render archives are very large and include asset-specific licensing considerations; do not download hundreds of gigabytes before establishing the training need. [Ortho dataset](https://huggingface.co/datasets/huanngzh/Objaverse-Ortho10View), [random-reference dataset](https://huggingface.co/datasets/huanngzh/Objaverse-Rand6View).

### Lighter Klein/Qwen approaches

BFL's Klein guidance recommends undistilled Base checkpoints for training. Its published requirements make **Klein 4B** a credible local candidate; the 9B recommendation exceeds this card's VRAM. The guide's short LoRA training estimates concern ordinary specialization, not a guarantee of learning calibrated multiview geometry. No controlled Klein-versus-SDXL training-speed comparison for this task was found. [Official training guidance](https://docs.bfl.ai/flux_2/flux2_klein_training).

The audited AI Toolkit source has Klein 4B/9B model classes, reference-image conditioning and model-specific quantization/offload paths. This is more relevant than applying a style-only training example to camera edits. A 16 GB paired-edit training step, checkpoint reload and held-out result remain unmeasured here. [Klein implementation](https://github.com/ostris/ai-toolkit/blob/14f8f95090689b585093e5aaf48bc1e2e0a67ea4/extensions_built_in/diffusion_models/flux2/flux2_klein_model.py), [conditioning implementation](https://github.com/ostris/ai-toolkit/blob/14f8f95090689b585093e5aaf48bc1e2e0a67ea4/extensions_built_in/diffusion_models/flux2/flux2_model.py).

The fal Qwen Edit 2511 angle LoRA is an existing lightweight example: paired rendered data, named viewpoints and a specific trigger grammar. Its released weights do not require a hosted inference service. The card does not provide a local 16 GB training benchmark or establish calibrated multi-image reconstruction. It is a third-party adapter for Qwen, not an official Qwen-lab adapter. [Model card](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA).

A new, narrowly relevant October lead is `akhaliq/flux-3-image-klein-angles-lora`, trained on 4,000 paired renders with a published image-edit training script. Its author explicitly reports uneven generalization and hallucinated replacements for some plain objects. This is evidence that the small-adapter route is buildable and still needs object-level validation; it is not a new supported-model commitment. Do not conflate FLUX 3 Klein with FLUX.2 Klein 4B/9B. [Author card](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora).

### Training escalation, only if justified later

Start with existing weights. If the view generator fails a specific, repeatable requirement, propose the smallest training change addressing that failure. A paired camera-edit LoRA on Klein 4B is a more affordable first custom-training hypothesis than porting an entire joint-attention architecture. Success would still be judged on unseen objects, angle/scale error, feature preservation and mesh quality—not a falling training loss.

The published MV-Adapter training is a much larger undertaking: the paper describes multi-A100 training, and the released configuration trains new attention/conditioning modules rather than merely a tiny low-rank update. It should not be sold as a guaranteed weekend run on this card. [Paper](https://arxiv.org/html/2412.03632v1), [training owner](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/systems/mvadapter_image_sdxl.py).

Suggested later escalation: one local memory/forward-backward probe; one short held-out learning pilot; only then estimate a larger run. Default expenditure remains **$0**. A rental estimate must use measured seconds per step, planned steps, GPU count, evaluation time, storage and setup. Current advertised rates are examples, not a project quote; $50 does not guarantee a useful adapter. [Primary pricing reference](https://www.runpod.io/pricing).

Python is not the bottleneck merely because the training script is Python: tensor operations execute in optimized GPU libraries. Rust/C++ can help measured data or integration bottlenecks. Rewriting orchestration does not create better learned geometry. LoRA weights are model-specific; datasets, camera conventions and evaluation can be reused across backbones, but SDXL adapter tensors cannot simply be loaded into Klein or Qwen.

## Licensing and portability decisions

This is a source-based component audit, not a blanket clearance of every downstream use. A code license, a weight license, and rights to training/reference assets are separate. The exact artifact and its terms must accompany any future download or redistribution.

| Component | Finding | Consequence |
|---|---|---|
| MV-Adapter code/weights | Apache 2.0. | Suitable candidate with notices and conditions preserved. |
| SDXL base | OpenRAIL++ terms. | Commercial use is conditional on those terms; not public domain. |
| Juggernaut XL v9 | Card identifies OpenRAIL-M and separately restricts paid API use without permission. | Explain exact conditions; do not give an unconditional “everything commercial allowed” badge. |
| BiRefNet | Selected ZhengPeng7 checkpoint is MIT. | Explicitly select it; BRIARMBG 2.0 is a different license/model. |
| Pixal3D | Main code/weights MIT, with third-party notices; HF card also has a regional gate flag. | Audit actual dependencies and access rules before redistribution. |
| DINOv3 / NAF feature package | DINOv3 has Meta's own license; NAF has separate terms. | A local combined-file MIT label is not sufficient provenance. Record a future correction; no runtime files edited here. |
| TRELLIS.2 components | Selected upstream weights are labeled MIT. | Preserve their own artifact records; do not transfer that label to DINO. |
| StableNormal | Apache-labeled code/weights; retain underlying component notices. | Candidate, not a reason to skip dependency audit. |
| Era3D reconstruction fork | AGPL-3.0 stated by project. | Commercial use and source-sharing obligations are different questions. Plan compliant integration; do not relabel the fork MIT. |
| nvdiffrast | Inspected license includes noncommercial restrictions. | Do not add it casually. Native primary finishing avoids it; prove whether the isolated NeuS core needs the optional renderer. |
| tiny-cuda-nn | BSD-3-Clause. | Suitable dependency candidate subject to notices. |
| Gaussian Wrapping | Noncommercial implementation terms. | Exclude from commercial default. |
| T3lescope | Code/weight release terms not verified. | Watchlist only. |
| Klein 4B / Qwen Edit 2511 angle LoRA | Apache-labeled selected artifacts. | More straightforward research candidates; still preserve exact upstream terms and data rights. |
| Klein 9B / FLUX 3 Klein | Different, conditional BFL licenses. | Do not inherit 4B's Apache label. No new support decision made here. |

Primary license links and pinned snapshots are in [SOURCE-REGISTER.md](SOURCE-REGISTER.md). Reimplementing a paper's idea can be a legitimate engineering project, but copying restricted code/weights or assuming all legal constraints disappear after a rewrite is not a licensing strategy.

## What is ready, and what is not

**Ready to discuss:** a concrete coordinated-view hypothesis; actual released I2MV graphs and weights; exact baseline and derivative; documented camera mismatch and plausible bridges; one matched fallback; source-based memory/license risks; a finite test proposal; and a credible lighter-adapter training path if evidence later justifies it.

**Not proven:** that MV-Adapter improves Brian's meshes, that its generated cameras are geometrically exact, that Juggernaut is better, that the adapter fits the current desktop stack, that the fallback fits 16 GB on Windows, that any new route exports correct PBR textures, or that a local training weekend solves the task.

The next action after approval should be the bounded camera/runtime gate in [VALIDATION-PROPOSAL.md](VALIDATION-PROPOSAL.md), followed only on success by the declared image/mesh comparisons. Outstanding questions have finite probes and stop rules in [FOLLOW-UP.md](FOLLOW-UP.md). The full coverage and decisions are in [QUESTION-AND-DECISION-REGISTER.md](QUESTION-AND-DECISION-REGISTER.md).

**Research stopping point:** all planned questions have evidence or a bounded unknown; no additional broad search is required to make the next decision. Stop here for Brian's review. Do not start the proposed experiment automatically.
