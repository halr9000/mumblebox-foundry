# WorldSculpt for Mumblebox: single-object research and proposal

Research date: 23 October 2026. Target: Brian's RTX 4080 SUPER, 16 GB VRAM, 64 GB system RAM, existing Comfy Desktop on E:. Status: **research result and unexecuted proposal**. No WorldSculpt generation, installation, workflow change, or hardware qualification was performed.

## 1. Recommendation in plain English

**Proceed conditionally with a separate experiment built from the supplied single-object Comfy workflow.** WorldSculpt contains the kind of trained multiview fusion that Mumblebox was missing. The released code and weights provide a concrete way to try it; training a new adapter is not the starting requirement.

The experiment remains: **three or four pictures of the same object, with their masks and camera information, go through both WorldSculpt geometry adaptations and both learned aggregators to produce ONE mesh.** It does not reconstruct separate parts and glue them together. It does not require the room/scene-separation application. Internally, the input can describe a “scene” containing exactly one object.

Three limits must be clear before approval:

1. **The evidence supports imperfect observations, especially occlusion. It does not establish that WorldSculpt fixes contradictory AI-generated objects.** Changing a person's anatomy or moving a door between images is different from hiding part of an otherwise consistent object.
2. **Camera preparation is a real part of the work.** A prompt requesting a 45-degree view is not measured camera calibration. The supplied graph does not turn four arbitrary pictures into verified cameras automatically.
3. **16 GB operation is plausible but unverified.** An author reports H100 inference with the second stage below 30 GB in most cases; the community Comfy examples use an RTX 5090. Neither demonstrates Brian's card. Memory management should be present from the first run, followed by measurement and targeted repair—not an intentional all-models-resident crash test. [Author's hardware reply](https://github.com/AlayaLab/WorldSculpt/issues/4#issuecomment-6139788888), [community implementation](https://github.com/jtydhr88/ComfyUI-WorldSculpt).

The proposed first version keeps the complete released method, uses the authors' documented adapter-validation sampling settings, manages resources between stages, and finishes geometry on the GPU. It starts with simple known-camera inputs, then a more detailed hard-surface subject, then a fixed-pose character if the earlier cases work. It stops after the bounded evaluation in section 12.

Brian's accepted addition during this research: the **native Codex image-generation tool** will supply the generated test references after implementation/test approval. Those will be separate images, one view per image, reviewed before reconstruction. Native generation does not supply guaranteed camera metadata. No images were generated during this research.

The existing single-image Mumblebox workflow remains the practical alternative if WorldSculpt cannot improve the generated-view cases within the hardware and preparation limits. A calibrated-photo-only success will be reported as that narrower capability, not as solving generated references.

## 2. What was examined, and what the evidence means

The research covered the official paper, project page, repository, inference implementation, released checkpoint/configuration metadata, author issue replies, community Comfy source and workflow JSON, and the relevant installed Comfy/Mumblebox code. Source snapshots and hashes are retained beside this report. The earlier Mumblebox research supplied the known crop, camera, multiview, finishing, and resource lessons; this pass did not restart a survey of image or mesh models.

| Source | Version examined | What it establishes |
| --- | --- | --- |
| Official WorldSculpt code | `fac6b83282368063a34e648a07c6cff169e05152` | Released inference method, adaptation loading, projection, preprocessing, sampling options |
| WorldSculpt weights/configurations | `8cb81056d803c61371dd84ef18a14142a738610e` | Two stage adapters, two aggregators, training configuration and artifact identities |
| Community Comfy integration | `4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c` | Actual node implementation and supplied instance/scene/video graphs |
| Paper | arXiv `2609.05416v1`, 4 September 2026 | Reported training, evaluation, ablations, assumptions |
| Installed Comfy parent checkout | `483dae4326356b81de05d27aca3f433dd323cc25` | Local source compatibility and memory/finishing APIs, not runtime validation |
| Comfy-Org Pixal3D files | `f37641be376725d324c56626007cc477f1249a69` | Native weight filenames, sizes and download identities |
| Comfy-Org TRELLIS.2 files | `430a9d09b2416687018c8fe8edced2ad4858a439` | Native shape/texture decoder files |

The official repository links and acknowledges the community Comfy integration. That is stronger provenance than a random workflow repost, but it does not make every community setting identical to the official implementation. [Official README](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/README.md), [author acknowledgment](https://github.com/AlayaLab/WorldSculpt/issues/3).

**Evidence labels used here:** “source verified” means the released code or metadata contains the behavior; “published” means the authors report it; “proposed” means an engineering choice for the future experiment; “unverified” means no corresponding local runtime proof exists. File presence, a matching tensor name, or an imported workflow would not prove reconstruction quality.

### Official skill and preferred image generator

No official `SKILL.md` was found in the complete official repository tree, the community wrapper tree, the checkpoint listing, or the targeted official-guidance searches. No official WorldSculpt skill was installed or invented. The paper, source, configuration files and supplied graphs are the available guidance.

No official preference for Qwen, Klein, SDXL, or another 2D image generator was found. The project demonstrates reconstruction from observed views and from **renders of generated 3D Gaussian-splat scenes**, including Marble. Those renders share an underlying scene and camera information. That is materially different from independently asking an image generator for several sides of an object. [Project page](https://alaya-lab.github.io/WorldSculpt/), [paper](https://arxiv.org/html/2609.05416v1).

The implementation explicitly expects the DINOv3 visual encoder. This is an internal feature extractor, not an instruction to create pictures with a Meta image generator. It runs locally. No drop-in encoder replacement was verified.

## 3. How the complete method works

### The complete path to one exported object

1. **Select the references.** Use three or four separate images of the same object, with one fixed geometry and pose. The user may specify unseen details through these images; text is not a direct WorldSculpt reconstruction input.
2. **Create and inspect masks.** Reuse Mumblebox's background-removal capability. Preserve image/mask alignment and original image dimensions. Fine structures must remain in the masks.
3. **Prepare cameras and an approximate 3D box.** Use exact cameras when available; otherwise estimate and validate them. A single instance record identifies the same object in every image.
4. **Use WorldSculpt's canonicalization and cropping.** The selected anchor and object box establish a common 3D coordinate system. Crops update camera intrinsics rather than silently changing object scale.
5. **Extract image features.** DINOv3 encodes the views. Shape conditioning also uses NAF to produce higher-resolution features.
6. **Generate the coarse occupied volume.** Project each view's features onto candidate 3D locations, combine them through the sparse-structure aggregator, and sample the sparse-structure model with its WorldSculpt LoRA applied.
7. **Generate detailed geometry.** At the occupied positions, gather higher-detail per-view features, combine them through the shape aggregator, and sample the shape model with its matching WorldSculpt LoRA.
8. **Decode and finish.** Decode the shape latent into a mesh, release neural models, remesh on the GPU, and decimate on the GPU. Keep the mesh in canonical coordinates until these operations finish.
9. **Place and export.** Apply the canonical-to-object transform and glTF up-axis convention, then save one GLB. Inspect actual geometry from all sides. Optional texture work is a separate extension of this same object, not evidence that its geometry improved.

This is a single reconstruction pipeline with two learned geometry stages. “Two stages” does not mean making two independent meshes and joining them. [Official multiview inference helpers](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/mv_inference_common.py), [community conditioning implementation](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/nodes_conditioning.py).

### What the adapters contain

The released geometry adaptations are numerical tensor weights, not text prompts or caption files. Both stages use LoRA rank 32 and alpha 32. Each released denoiser checkpoint has 360 tensor keys: 180 A/B matrix pairs across 30 blocks. They cover self-attention, cross-attention, and the per-block conditioning projection.

This pass inspected checkpoint metadata using bounded HTTP range reads and `pickletools`, without executing a pickle or loading model tensors. All 180 target weight names for each stage match the corresponding submodule names in the installed BF16 Pixal3D safetensors header. This is **static name compatibility**, not proof that all patches apply or produce correct results at runtime.

The wrapper maps the official standalone-stage keys into the native combined Pixal3D model: sparse structure goes to `structure_model`, detailed shape goes to `img2shape`. Its log message counts input pairs; it does not prove successful matching. Later validation must inspect actual matched patches and missing-key warnings.

The paper describes trained conditioning projections as well as LoRA and aggregation. The released denoiser files examined here contain LoRA A/B weights, including `cross_attn.proj_linear` targets; the official loader supplies base projection weights from the base checkpoint. **There is no verified missing fifth “projection adapter” download to hunt for.** Use the released loader/configuration as a set rather than assuming the paper's architectural description implies another standalone file. [LoRA loading code](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/pixal3d_multiview/lora.py), [wrapper conversion](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/nodes_weights.py).

### What the learned aggregator actually does

At each candidate 3D location, projection gathers a feature vector from each image. The released IBR-style aggregator calculates the cross-view mean and variance, uses learned small neural networks to calculate feature corrections and view weights, and adds the weighted correction to the mean. Softmax normalizes weights across the views at that location.

The consequence is useful: different observations can contribute differently to different parts of the object. An obscured view need not dominate all the geometry.

However, this is **not a hard bad-image rejection system**. A view with a small residual weight still participated in the mean and variance. The wrapper treats the selected observations as valid; it does not use an independently verified contradiction detector, calibrated uncertainty score, or visibility z-buffer to remove false content. Out-of-frame projection uses border sampling. Correct camera geometry still matters.

Both aggregators are required to test the released learned method. If an aggregator input is omitted, the wrapper falls back to averaging. LoRA strength zero skips the adaptation. Those shortcuts would change the experiment and must not be used silently.

Global image tokens are taken from the anchor view; multiview fusion supplies local projected information. The anchor therefore matters even though the local aggregation is permutation invariant. The wrapper also bypasses its aggregator calculation for a single-view input, unlike the general official IBR forward path. Do not treat a one-view wrapper run as an exact reproduction of the paper's one-view ablation. [Official aggregator](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/pixal3d_multiview/mv_aggregator.py), [wrapper projection/fusion](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/projection.py).

### What controls hidden details

An extra reference can show a rear pocket, backpack, handle, recess, or wall feature that the anchor cannot show. With a valid camera, those pixels provide local evidence where that feature belongs in 3D. Areas unseen in every view still depend on Pixal3D's learned shape prior.

There is no guarantee that requested details will appear. Text describing a backpack cannot by itself force WorldSculpt to add one: the core graph has no text-conditioning input for that instruction. A painted emblem is primarily an appearance requirement; a raised backpack is geometry. Evaluate the latter on an untextured mesh rather than accepting a painted imitation.

## 4. What the published results support

The paper trains with variable view counts and intentionally imperfect observations: simulated occlusion, mask disturbances, resolution loss, and camera perturbations. That is directly relevant to the historical problem of fragile inputs. The geometry comparisons and ablations provide a reason to test this method, rather than just a visually appealing demo.

Selected clean-input Toys4k results reported by the authors:

| Method / observations | Chamfer L2, ×10^-3, lower better | F-score @ 0.02 | F-score @ 0.05 |
| --- | ---: | ---: | ---: |
| Pixal3D, one image | 2.17 | 0.749 | 0.934 |
| WorldSculpt, one view | 2.59 | 0.739 | 0.932 |
| WorldSculpt, two views | 1.54 | 0.790 | 0.954 |
| WorldSculpt, four views | 1.35 | 0.813 | 0.964 |
| WorldSculpt, eight views | 1.23 | 0.822 | 0.965 |
| WorldSculpt, sixteen views | 1.19 | 0.827 | 0.967 |

The table is adapted from Niu et al., *WorldSculpt: Generating Compositional Worlds from Grounded Videos*, v1, distributed under CC BY 4.0. The evaluation uses 500 objects and its own canonical/ICP alignment procedure. These numbers are not predicted scores for Mumblebox. [Paper, experiments and ablations](https://arxiv.org/html/2609.05416v1).

The learned aggregator is beneficial in several occlusion tests, but not uniformly superior on every metric. For example, under 75% occlusion with four views, reported Chamfer improves from 6.10 for averaging to 5.67 for learned aggregation, and F-score @ 0.05 rises from 0.845 to 0.849. With eight views in that condition, averaging has the lower Chamfer value (3.04 versus 3.52), while learned aggregation has the higher F-score (0.902 versus 0.898). This is evidence of useful robustness, not an infallible reconciliation mechanism.

No demonstrated guarantee was found for independently generated views that change limb lengths, clothing construction, proportions, articulation, or accessory location. A static T-pose helps define a consistent input task but does not prevent an image generator from changing the body. Camera perturbation training is not proof that camera calibration can be omitted.

### Training implications

The published method freezes the base Pixal3D parameters while training stage LoRAs and multiview conditioning components. Released configs specify rank/alpha 32, BF16 training, AdamW at 1e-4, no weight decay, EMA 0.9999, and variable sets of 1–20 views. Released checkpoints are at 15,000 iterations; config `max_steps=20000` is a training limit, not a recommended inference step count.

The configurations include non-anchor camera perturbations up to about 5 degrees, translation up to 0.05 canonical units, and a focal/FOV perturbation setting. They also include probabilistic image downscaling, occluders, and rough mask boundaries. These settings describe the training distribution; they do not create a validated “errors below this value are safe” threshold for our inputs.

An author reports approximately 150,000 training assets. The release includes inference code, model/configuration files and supporting training utilities, but the specific multiview dataset/trainer classes named by the released configs are not registered in the supplied generic dataset/trainer modules, and a complete turnkey training entry point was not found. A reproducible home-training recipe remains unverified. There is insufficient evidence to price this as a $50 job or a weekend on 16 GB. Existing weights should be evaluated before considering custom training. [Author's training reply](https://github.com/AlayaLab/WorldSculpt/issues/4), [released configurations](https://huggingface.co/AlayaLab/WorldSculpt/tree/8cb81056d803c61371dd84ef18a14142a738610e).

## 5. Input preparation: images, masks, cameras and scale

### Separate images, not a collage

The supplied single-object workflow reads several image frames with matching camera records and masks. It does not expect a 2×2 contact sheet as its single image. A contact sheet could only be an upstream creation format: it would have to be split, each panel's geometry checked, and crop-adjusted cameras supplied. There is no evidence that this extra step helps WorldSculpt, so the proposed test uses separate references.

All references must describe the same stationary object. For the character test, use full-body images in the same T-pose, including consistent hands, limbs, clothing and accessories. Begin with a three-quarter anchor and complementary views. Requested azimuths are labels describing intent, not validated numerical camera poses.

### Released file contract

`WorldSculpt Load Scene` reads a directory containing `transforms.json`, image frames, and separate object-mask images. A single-object dataset still uses one entry in `instances`. The inspected wrapper expects:

| Field / data | Meaning and important condition |
| --- | --- |
| `w`, `h`, `fl_x`, `fl_y`, `cx`, `cy` | Source frame dimensions and perspective intrinsics in pixels |
| `frames[].file_path` | The exact image associated with a camera |
| `frames[].transform_matrix` | 4×4 camera-to-world transform in the expected Blender/OpenGL convention |
| `frames[].mask_paths` | Object-name-to-mask association; a documented fallback mask directory layout also exists |
| `instances[].pass_index` | Identifies the instance, such as `obj01` |
| `instances[].aabb_world` | Minimum and maximum 3D bounds for that object |
| `world_up` | World axis convention used for later placement/export |
| Optional oriented-box fields | Tighter localization when corresponding object pose/scale metadata exists |

The file loader uses **one top-level intrinsic matrix for all frames**. It does not read arbitrary per-frame intrinsic fields. The in-memory scene representation can carry each frame's own matrix; the estimates bridge uses that. Mixed focal lengths or independently cropped images therefore need normalization or a correctly implemented input bridge, not extra JSON fields the loader ignores. [Scene loader and view preparation](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/nodes_scene.py).

Blender/OpenGL camera coordinates and OpenCV coordinates differ. The wrapper handles their conversion in its defined path; supplying a matrix in the wrong convention can mirror or reverse projections. Preserve camera-to-world versus world-to-camera meaning, handedness, up axis, focal units, image dimensions, and object normalization together.

### Masks and background removal

Use the existing Mumblebox foreground-removal path as the starting capability. It can supply full-frame masks while preserving the source image and its recorded preparation transform. The model used for foreground removal is a preprocessing choice; it is not one of WorldSculpt's geometry adapters.

The released file path loads RGB and reads a separate grayscale mask, thresholded at greater than 127. An image's alpha channel alone is not sufficient for that loader. Convert Comfy mask conventions explicitly: the stored WorldSculpt mask must mark the **object** as foreground, even if an upstream Comfy mask marks the transparent/editable region instead.

Inspect thin handles, hair, fingers, arm gaps, antennae and holes. Do not bake a shadow or pedestal into the object mask unintentionally. If a part is removed from every mask, learned fusion cannot use it as direct image evidence. Repeated masking mistakes are not a multiview-adapter failure.

### Cropping and anchor selection

The wrapper chooses an anchor from usable observations based on mask area, aligns the object cube to that anchor, projects the cube into each image, crops a padded square, and updates the focal lengths and principal point for that crop and resize. This is the relevant correction to Mumblebox's earlier independent-cropping problem.

For an image crop beginning at `(x0,y0)` and resized by a common scale `s`, the camera update includes `fx' = s fx`, `fy' = s fy`, `cx' = s(cx-x0)`, `cy' = s(cy-y0)`. The implementation then normalizes these values for its feature projection. Padding offsets must be included too. Stretching each object to fill its own frame without that update changes the apparent cameras.

The mask-fit option grows the canonical cube so its projections contain the masks. It compensates for an undersized box; it is not a general camera or shape optimizer. An incorrect mask or camera can inflate the box.

The current graph does not expose a manual anchor selector. For the first faithful control, record the actual selected anchor. For the generated-view comparisons, the single-image baseline and WorldSculpt must use the same intended anchor; a small explicit anchor override is a justified bridge change if automatic area selection chooses another view. Do not manipulate crop sizes merely to game anchor selection.

The scene loader's cache fingerprint checks the metadata file's modification time. Editing image or mask pixels in place without changing that fingerprint can reuse stale data. Later experiments should use immutable case directories or an input fingerprint covering the image/mask contents.

### Unknown cameras: what is available and what remains difficult

The community wrapper already provides `WorldSculpt Scene From Estimates`: it takes **Depth Anything 3 multiview geometry** plus SAM3 tracked masks, back-projects masked depth, estimates object bounds, filters inconsistent tracks, and passes a scene to the same reconstruction chain. This is a source-backed preparation route for real footage, not proof that arbitrary synthetic references calibrate correctly. [Estimates bridge](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/nodes_realinput.py).

The installed Comfy source has native `DA3Inference`. For multiview it supports the Small/Base variants; its defaults are resolution 504, upper-bound resize, `saddle_balanced` reference selection and `cam_dec` pose estimation. The wrapper recommends loading DA3 in FP32 because its camera decoder encounters an FP16 dtype problem. The official DA3 Base card identifies camera-pose/depth capabilities and Apache-2.0 licensing. No DA3 model was installed or run here. [DA3 Base](https://huggingface.co/depth-anything/DA3-BASE).

For our isolated object images, requiring a video tracker and room detector would add unnecessary work. The minimal proposed bridge is: **the image batch + its existing masks + exact cameras or DA3 estimates + one object box → one-instance WorldSculpt input**. This is data preparation code, not a new trained adapter. Existing masks should not have to be rediscovered with SAM3. The bridge must preserve per-frame intrinsics and expose validation output.

DA3 can be wrong with little overlapping evidence, repeated/symmetric surfaces, artificial backgrounds, or genuinely different geometry. A rotating object on a fixed turntable needs object-relative camera treatment; background features can mislead a scene-camera estimator. Neither a visual-language guess nor an intended angle label should silently replace calibration.

Brian's more specific question—“can a tool estimate that this person is turned 45 degrees relative to the camera?”—concerns **body orientation**, not merely relative cameras. The official SAM 3D Body estimator exposes `global_rot`, focal length, camera translation and body keypoints, making it a relevant character-specific candidate. Its coordinate conventions and reliability on stylized T-pose images would need validation before conversion to WorldSculpt cameras. It is not currently a verified part of this proposal, and it does not solve arbitrary prop orientation. [Official estimator output](https://github.com/facebookresearch/sam-3d-body/blob/main/sam_3d_body/sam_3d_body_estimator.py), [coordinate-frame discussion](https://github.com/facebookresearch/sam-3d-body/issues/65).

A single orientation number is not a complete camera: perspective, distance/scale, framing and elevation still matter. Orthographic and perspective images are not exactly interchangeable without depth/geometry assumptions. For the control case use known perspective cameras; for generated views explicitly label camera estimates and retain the validation uncertainty.

## 6. Supplied single-object graph: complete wiring audit

The downloaded `worldsculpt_instance.json` contains 26 nodes and 34 links. Both stage LoRAs and both aggregators are connected. There is no `Merge Instances` node in this graph. The raw supplied file is preserved only as a research snapshot and was not loaded into Comfy.

| Node IDs | Supplied nodes / settings | Role |
| --- | --- | --- |
| 1 | `UNETLoader`: Pixal3D BF16 | Native base model |
| 2 → 3 | WorldSculpt LoRA Loader: SS then shape, strengths 1 | Apply both geometry adaptations to the same model |
| 4, 5 | WorldSculpt Aggregator Loader: SS and shape | Load the distinct learned fusion networks |
| 6 | `CLIPVisionLoader`: DINOv3-L + NAF | Required image feature extractor despite the generic loader name |
| 7 | `VAELoader`: TRELLIS.2 shape VAE | Structure/shape decoding used by native nodes |
| 8 → 9 | Load Scene → Instance Views, index 0 | Prepare one object's calibrated observations |
| 10 | `PreviewImage` | Displays the anchor crop; not an audit of all views |
| 11 | WorldSculpt Structure Conditioning | Uses views, DINO and SS aggregator |
| 12 | `EmptyLatentImage`, batch 1 | Initial noise container; not one batch item per view |
| 13 → 14 → 15 | CFG Override, CFG Rescale, SD3 sampling shift | Supplied structure sampler modifiers |
| 16 → 17 | KSampler → `VaeDecodeStructureTrellis2`, resolution 64 | Produce occupied structure |
| 18 | WorldSculpt Shape Stage | Uses structure, conditioning, DINO/NAF and shape aggregator |
| 19 → 20 → 21 | CFG Override → CFG Rescale → KSampler | Supplied shape sampling |
| 22 | `VaeDecodeShapeTrellis` | Detailed geometry decoding |
| 23 → 24 | `RemeshMesh` → `DecimateMesh` | GPU geometry finishing, before placement |
| 25 → 26 | WorldSculpt Place Mesh → `SaveGLB` | Coordinate placement and one-object export |

Important practical corrections are proposed, not performed:

- Replace the author's machine-specific scene path with the experiment's E: input path.
- Keep instance index 0 and cap selected views at four rather than the example's maximum of twenty.
- Add inspection of **every** prepared view, mask, camera and projected box; the anchor-only preview is insufficient.
- Select the adaptation sampling preset explicitly; do not inherit ambiguous model shifts.
- Bound GPU finishing and resource retention for 16 GB, as detailed below.
- Keep the Mumblebox GUI and current workflow untouched.

The full per-node widgets and link records are saved in `graph-audit.json`; all 42 input declarations of the wrapper's nodes are retained in `settings-source-index.json`. [Original instance workflow](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/workflows/worldsculpt_instance.json).

## 7. Components, file destinations, installation and access

### Required model files

All destinations below are relative to `E:\Comfyui-installs\ComfyUI (1)\ComfyUI`. Existing files were inspected for presence/size; they were not loaded or fully rehashed.

| Component | Destination | Bytes | Current state |
| --- | --- | ---: | --- |
| Pixal3D BF16 base | `models/diffusion_models/pixal3d_bf16.safetensors` | 10,999,317,704 | Present |
| DINOv3-L/16 + NAF, FP32 | `models/clip_vision/dino_v3_L_naf_fp32.safetensors` | 1,215,214,176 | Present |
| TRELLIS.2 shape VAE, BF16 | `models/vae/trellis_2_shape_vae_bf16.safetensors` | 1,095,844,024 | Present |
| SS LoRA | `models/worldsculpt/worldsculpt_ss_lora.pt` | 84,673,669 | Not installed |
| SS aggregator | `models/worldsculpt/worldsculpt_ss_aggregator.pt` | 33,579,301 | Not installed |
| Shape LoRA | `models/worldsculpt/worldsculpt_shape_lora.pt` | 88,605,893 | Not installed |
| Shape aggregator | `models/worldsculpt/worldsculpt_shape_aggregator.pt` | 134,263,077 | Not installed |
| Optional texture VAE | `models/vae/trellis_2_texture_vae_bf16.safetensors` | 948,461,364 | Present; not needed for geometry-only test |

The four additional WorldSculpt files total **341,121,940 bytes**, approximately 325.3 MiB. This is download size, not working VRAM. Their official source paths are:

| Destination filename | Official WorldSculpt repository path |
| --- | --- |
| `worldsculpt_ss_lora.pt` | `ss_ft64_mv_lora_ibr_texverse/ckpts/denoiser_step0015000.pt` |
| `worldsculpt_ss_aggregator.pt` | `ss_ft64_mv_lora_ibr_texverse/ckpts/mv_aggregator_step0015000.pt` |
| `worldsculpt_shape_lora.pt` | `shape_ft1024_mv_lora_ibr_texverse_fixedmem05/ckpts/denoiser_step0015000.pt` |
| `worldsculpt_shape_aggregator.pt` | `shape_ft1024_mv_lora_ibr_texverse_fixedmem05/ckpts/mv_aggregator_step0015000.pt` |

The HF metadata snapshots record sizes and LFS SHA-256 identities. The source configs are saved separately. Do not substitute the INT8 Pixal3D model or the separately fine-tuned ordinary multiview Pixal3D model: the wrapper specifically requires the matching BF16 base for these LoRAs. [Official weights](https://huggingface.co/AlayaLab/WorldSculpt/tree/8cb81056d803c61371dd84ef18a14142a738610e), [wrapper model instructions](https://github.com/jtydhr88/ComfyUI-WorldSculpt/blob/4d3306775c9dcbe4ed632ae62e689ee88e1f3c1c/README.md).

### Existing environment and compatibility

Read-only inspection found Python 3.13.12, torch 2.12.1+cu130, torchvision 0.27.1+cu130, frontend 1.55.18, comfy-kitchen 0.2.39, comfy-aimdo 0.5.6, NumPy 2.5.2, OpenCV 5.0.0.93, safetensors 0.8.0, trimesh 5.1.1 and SciPy 1.18.1. The GPU reports RTX 4080 SUPER, 16,376 MiB, driver 617.42; Windows reports 66,192,048,128 bytes physical RAM. Full details are in `local-readonly-inventory.json`.

The wrapper imports native Pixal3D/TRELLIS.2 helpers and uses `comfy_api.latest`. Those source APIs are present in the inspected checkout. Its README states no new Python dependencies. This is a promising Windows path because it reuses native Comfy implementations rather than installing the official CLI environment inside Desktop. No exact minimum Comfy commit or version compatibility matrix is published, and node import/kernel execution has not been tested.

The official CLI instructions use a separate TRELLIS.2 environment, NATTEN 0.21.0, PEFT, transformers 4.57.1 and other packages. Their example CUDA architecture 9.0 is not a 4080-specific instruction. Do not blindly run that installer in the existing Desktop environment, downgrade transformers, or interpret an absent standalone PEFT/NATTEN package as proof that the native Comfy path is unavailable.

### Unexecuted installation recipe

1. After approval, verify the live existing Comfy connection and save the currently open Mumblebox state. Retain the checked parent revision and environment inventory; do not update the whole application speculatively.
2. Resolve the wrapper permission route described in section 10, including any proposed modifications. Obtain the pinned node pack into its own `custom_nodes/ComfyUI-WorldSculpt` folder if that route permits it. Record upstream and local changes separately; do not package it in a public Mumblebox release without a verified redistribution grant.
3. Fetch only the four required WorldSculpt checkpoints at the recorded HF revision into `models/worldsculpt/`, with the filenames above. Validate file size and SHA-256. Reuse the present BF16 base, DINO/NAF and decoder files after identity checks.
4. Do not install an official skill unless an actual official skill becomes available. The checked source trees have none.
5. Use Comfy's normal extension reload/restart only with applicable authorization and while Brian is not using an active job. The current research authorization does not permit a restart.
6. Verify node registration and model patch matching. Load a separate copy of the supplied **instance** graph visibly, retaining all trained components. Replace only the documented path/settings/bridge/resource details in this proposal.
7. Build the complete path through GPU finishing and export before queueing the bounded evaluation. The controlled input validates that complete path; it is not a substitute deliverable or a permanently simplified method.
8. Write inputs, diagnostics and outputs inside a dedicated E: experiment directory. Confirm Comfy's resolved output root at runtime before queueing. Do not use D:, Swarm, OneDrive, or the old author's example path.
9. Rollback consists of closing the experimental graph, disabling only its new node pack if necessary, and reverting its separately recorded changes. Do not delete existing shared models, clean unrelated files, alter Mumblebox, or change global settings without a demonstrated need.

Optional camera estimation should start with the reviewed **DA3 Base** checkpoint and its own identity/access check. Optional video mask tracking needs SAM3 and its separate terms. Neither is required for the known-camera control, and neither should be installed merely because the broad scene demo uses it.

## 8. Settings dictionary and proposed first configuration

### User-facing and inference settings

These are proposed experiment settings, not new Mumblebox GUI controls or universal quality recommendations.

| Setting | Supplied value / allowed behavior | Proposed initial setting and reason |
| --- | --- | --- |
| Base model precision | BF16 required by wrapper | BF16; keep adapter/base compatibility |
| SS LoRA stage / strength | `ss`, 1.0; range -10 to 10 | `ss`, 1.0; no strength search |
| Shape LoRA stage / strength | `shape`, 1.0 | `shape`, 1.0 |
| Aggregators | Distinct SS and shape checkpoints; inputs technically optional | Both required and verified; no averaging fallback |
| Instance index | 0; -1 processes all instances | 0, one object |
| Crop resolution | 1024; 256–2048 in steps of 64 | 1024, retaining camera-correct crop; reducing this alone does not remove internal 1024 feature encoding |
| Max views | 20; 0 means all; upper bound 64 | 4, with exactly the intended 3–4 accepted views recorded |
| View selection | `area` or `fps` | Explicit approved set; when already ≤4, do not rely on selector to reject bad views |
| Minimum mask ratio | 0.001; code also requires at least 500 pixels | Retain; record every skipped frame rather than silently reducing views |
| Maximum crop ratio | 3.0 times source frame size | Retain; investigate any rejection |
| Mask-fit scale / percentile | true / 95 | Retain for real/estimated boxes; document resulting scale and validate projection |
| Anchor | Automatic usable mask-area choice | Keep the approved three-quarter anchor fixed across paired comparisons; if automatic selection differs, validate a minimal explicit-selection override rather than changing image scale to force selection |
| Initial latent batch | 1 | 1 object; views are conditioning, not independent samples |
| Seed behavior | 42, fixed | Fixed within a comparison; no rerolls for appearance |
| SS occupancy decode resolution | 64 | 64; shape wrapper requires the high-resolution path, not grid 32 |
| Shape decode resolution | Grid 64 corresponds to detailed 1024 path | Retain; lowering to an unadapted 512 stage changes the method |
| Aggregator chunk size | 4096 locations in wrapper | Retain initially; 1024 is a focused memory repair option if this stage is measured to fail |
| Active sparse-token cap | Wrapper has no explicit cap | Proposed guard at 49,152 locations, matching official inference limit as a boundary; stop/review rather than silently discard coordinates |
| Up axis | `y_up` or `scene` | `y_up` for GLB; preserve recorded transform and units |
| Output prefix | `3d/worldsculpt` | Unique E: experiment/case prefix under verified output root |
| Text prompt | No core geometry text input | Preserve intended details in case record and images; do not imply direct text-conditioned mesh control |

### Sampling: an important source discrepancy

The supplied Comfy graph uses the original Pixal3D-style preset: both stages 12 Euler steps, CFG 7.5, rescale 0.7/0.5, guidance intervals, SS shift 5 and inherited shape shift 3. The wrapper describes this as WorldSculpt's `SAMPLER=official` preset.

The official multiview helper instead identifies **`train` as its default validated adaptation preset**: sparse structure 50 steps, shape 12 steps, ordinary CFG 3, with Euler sampling and no interval/rescale modifiers. Its comments warn that the base preset can over-guide the adapted model. The sampler's default time rescale is 1. [Official preset definitions](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/mv_inference_common.py#L82), [Euler sampler](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/pixal3d/pipelines/samplers/flow_euler.py).

**Proposal:** keep the supplied complete graph, but explicitly use SS 50 / shape 12 steps, CFG 3, Euler, denoise 1, shift 1 on both sampling branches, and no CFG override or rescale. Record the exact sigma schedule during implementation. Matching the named controls is not a claim of bit-for-bit parity between different sampler implementations.

A second static finding makes explicit settings especially important. In the installed Comfy implementation, `CFGOverride` captures the current model's shifted sigma thresholds when the node executes. The graph's structure override at 0.667 sees base shift 3 before a later shift-5 node, giving a threshold near 0.600. Its shape override at 0.769 also sees base shift 3, giving about **0.474**, whereas the documented official guidance interval starts at 0.6. This is a source-derived compatibility discrepancy against this local revision, not a demonstrated bad mesh. If the base preset is tested later, its actual interval must be corrected/verified rather than copying widget percentages blindly. Arithmetic and source hashes are recorded in `local-source-audit.json`.

The two implementations use the same ordinary CFG scale convention, verified from the official mixin. There is no evidence-based need to add 1 to the suggested CFG value. Higher CFG is not a substitute for calibrated cameras or consistent geometry.

### GPU finishing settings

| Setting | Supplied instance graph | Proposed initial geometry test |
| --- | --- | --- |
| Remesh resolution | 768 | **512**, a deliberate memory/finishing compromise; keep original for later comparison only if warranted |
| Sign mode | UDF | UDF; do not substitute Mumblebox's solid-fill route |
| QEF / inverted / enclosed options | false / false / false | Retain |
| Band width / projection back | 1.0 / 0.0 | Retain |
| Smooth iterations | 20 in supplied widgets | **0 initially**, to avoid smoothing away evidence of small geometric details |
| Small-component removal | 0.01 | **0 initially**, so legitimate thin/disconnected details are not silently removed |
| Maximum remesh faces | 20,000,000 | Retain as a safety limit, not a target or prediction |
| Decimation | 200,000 faces, midpoint | Retain initially; inspect thin structures and openings |
| Texture / UV | Not in instance graph | Geometry-only evaluation first; optional later texture branch |
| Optional UV segmenter | Native PEC or adaptive | PEC for GPU chart segmentation; no slow CPU adaptive fallback |

The native remesher reserves memory using an estimate including `resolution³ × 64`: approximately 27 GiB at 768, versus 8 GiB at 512, before other demands. This is a reservation estimate in source, not a measured peak. It is a specific reason not to queue the supplied 768 finish unchanged on 16 GB. Remesh/decimate must occur before world placement because their canonical bounds assume the unit cube.

PEC is a GPU UV-chart segmentation method. It is not a mesh generator or a universal switch that makes every operation GPU-only. File serialization and small coordinate bookkeeping can still use CPU; heavy finishing should use the CUDA-backed native path.

### Optional estimates/texturing settings

For the released estimates bridge, defaults are minimum 500 mask pixels, minimum 2 frames, box trim 2%, confidence percentile 20, minimum track score 0.6 and duplicate-box IoU 0.5. Its depth preparation erodes a 5×5 mask rim, samples at most 20,000 pixels per observation, trims depth tails, rejects inconsistent point-cloud centers, and checks projected-box coverage. These are practical heuristics, not calibrated probabilities of a correct camera. For one already-isolated object, tracking-score and duplicate-object controls are unnecessary unless the original SAM3 video route is used.

WorldSculpt supplies no trained texture adaptation. The optional wrapper texture stage uses the original Pixal3D texture model; its optional aggregator is not connected in the supplied textured example, so local features use averaging. The example runs texture at 12 steps / CFG 1, then decodes texture features and paints vertices. A UV-baked branch can use native UnwrapMesh + BakeTextureFromVoxel + ApplyTextureToMesh and the texture VAE. Texture sharpness, seam quality and geometry must be evaluated separately. The first experiment should not expand into texture tuning.

The full wrapper declaration index preserves exact defaults, ranges and descriptions without executing the node code. Not all internals are exposed as controls: token count, aggregator chunking, cached GPU tensors and crop-cache invalidation need implementation attention if they affect the experiment.

## 9. Can the complete method fit this machine?

**There is not yet a verified yes. There is a concrete memory-management route worth evaluating.** The author's H100 estimate and the wrapper's 32 GB RTX 5090 demonstrations are not measurements of a four-view object on 16 GB. Targeted searches found no primary-source reproduction establishing that exact configuration. The upstream single-image inference script's low-memory comments cannot be transferred to the adapted multiview route.

The local read-only inventory identifies an RTX 4080 SUPER with 16,376 MiB reported VRAM, driver 617.42, and approximately 64 GB installed system memory. These are machine facts, not a free-memory measurement or a performance result. No models were loaded to obtain them.

### Where memory goes

| Source of memory demand | Source-derived finding | Consequence |
| --- | --- | --- |
| Combined BF16 Pixal3D file | Approximately 10.24 GiB of stored tensors across structure, 1024 shape, 512 shape and texture submodels | File size is not the required live allocation. Do not assume all four branches must remain resident, or assume the loader already excludes unused ones |
| Image encoder and NAF | Views are encoded sequentially; a dense FP32 1024-channel 512×512 feature map alone is about 1 GiB | Keep encoding serial and release temporary maps after projection |
| Projected multiview features | Four views × 32,768 positions × 2,048 channels × BF16 is 512 MiB before additional copies, statistics and conditioning tensors | View count and occupied-token count matter independently of adapter size |
| Learned aggregators | Wrapper moves raw modules to the device; they are not ordinary Comfy ModelPatcher-managed models | Standard unloading does not by itself prove these modules or cached outputs have left VRAM |
| Shape attention | Cost grows with occupied sparse positions and attention implementation | Sparse geometry does not automatically make all attention memory cheap |
| Decode and finishing | Decoder plus remesher can peak after denoising is finished | Neural models and cached GPU conditioning must be released before finishing |

The wrapper uses aggregator chunks of 4,096 positions; the official implementation uses a larger chunk in the inspected route. Reducing the chunk to 1,024 is a credible focused repair because it divides the same computation. It does not reduce the full feature stack or guarantee that a shape-denoising peak will fit.

The installed Comfy source supports partial model loading/unloading and asynchronous offloading. This can trade transfer time and system RAM for GPU capacity. Its current `--lowvram` help explicitly notes that it has no effect when dynamic VRAM is enabled. Therefore, copying a launch flag without checking the active memory backend would be misleading. Preserve the working Desktop environment; inspect and use its existing memory management before changing launch behavior. [Comfy model management](https://github.com/Comfy-Org/ComfyUI/blob/483dae4326356b81de05d27aca3f433dd323cc25/comfy/model_management.py), [patching/offloading](https://github.com/Comfy-Org/ComfyUI/blob/483dae4326356b81de05d27aca3f433dd323cc25/comfy/model_patcher.py), [launch options](https://github.com/Comfy-Org/ComfyUI/blob/483dae4326356b81de05d27aca3f433dd323cc25/comfy/cli_args.py).

Brian's proposed “load and unload chunks” is therefore relevant. It has two separate forms: moving model weights between RAM and VRAM, and processing conditioning data in smaller chunks. Neither can eliminate an indispensable live tensor. The first measured failure stage determines which intervention is relevant.

The installed TRELLIS/Pixal attention path packs active sparse positions and calls Comfy's optimized attention. “Sparse” here describes occupied object data; it is not evidence that an arbitrary new sparse-attention mask can be substituted without changing model behavior. Use the supported exact memory-efficient attention backend first. Do not add FlashAttention, SageAttention, INT8 conversion, a different backbone or a new attention algorithm merely to obtain a successful queue. The WorldSculpt loader expressly excludes the INT8 Pixal3D file.

### Proposed stage ownership and unloading schedule

| Stage | What may need GPU residency | Release or move out before the next heavy stage |
| --- | --- | --- |
| Mask/camera preparation | Only the selected mask or camera model, if needed | Mask/camera model, temporary depth and image tensors; save images, masks and camera metadata |
| Sparse-structure conditioning | DINO feature extractor and SS aggregator | Encoder, aggregator and temporary per-view tensors after retaining only required conditioning |
| Sparse-structure sampling | Adapted SS denoiser and its conditioning | SS sampling tensors and conditioning after the occupied coordinates are retained |
| Shape conditioning | Image encoder/NAF and shape aggregator | Encoder, aggregator and dense intermediate maps; retain shape conditioning and coordinates |
| Shape sampling | Adapted shape denoiser and required conditioning | Denoiser residency and conditioning after shape latent is retained |
| Shape decoding | Shape VAE and shape latent | VAE and latent once the mesh is available |
| GPU finishing/export | Mesh and CUDA finishing buffers | Temporary finishing buffers, then GPU mesh buffers when export/inspection no longer needs them |

Some denoisers share a combined base checkpoint. Comfy can manage their residency without re-downloading or recreating the model for every stage. The implementation must measure what actually remains resident, including cache-held tensors and raw aggregator modules. A node named “unload” or an empty queue is insufficient evidence.

Mumblebox's existing idle-only cleanup code is useful, but the independent graph needs explicit lifecycle handling for resources outside Comfy's normal model registry. Use safe cleanup on completion, exception and cancellation. Do not interrupt another user's running job to enforce this experiment's limits.

### Proposed resource limits for the later test

These are practical evaluation limits for discussion, **not published WorldSculpt requirements or expected timings**:

- Queue one object and one reconstruction at a time, four views at most, batch one. Start with at least 16 GiB available system RAM and after prior model cleanup; check actual GPU headroom before queueing.
- Preserve at least 1.5 GiB GPU headroom as a planning reserve for the desktop and other demand. Record device-wide usage and framework allocated/reserved memory separately; high allocated VRAM alone does not prove a hang.
- Warn below 12 GiB available system RAM. Cancel if availability remains below 8 GiB for 10 seconds, or the machine becomes unresponsive. Avoid substituting Windows shared-GPU-memory paging for deliberate offloading.
- Record peak memory and elapsed time for every stage. Treat five minutes with no progress, low GPU and CPU activity, and no meaningful I/O as a stall requiring diagnosis. Active computation with a quiet log is not a stall.
- Use a 45-minute ceiling per reconstruction, including finishing, for this bounded evaluation. If a one-time compilation step prevents a fair measurement, document it and discuss changing the ceiling before another attempt; do not silently keep running overnight.
- Stop at an out-of-memory error, preserve evidence, and clean up. Allow only the two focused repair/retries described in section 12. Repair the measured cause rather than lowering every setting at once.
- Do not silently lower SS resolution to invoke the unadapted 512 branch, drop an aggregator, switch to INT8, discard input views, or use CPU finishing and count that as a successful full-method run.

The memory intervention order is: correct stage cleanup and active offloading; remove retained GPU caches; reduce fusion chunk size if that stage fails; use the proposed 512 GPU finishing configuration. If the shape model's irreducible working set still exceeds the available memory, report that specific limit. A reboot is a possible recovery action with Brian's involvement, not a memory-management strategy or an action performed during this research.

## 10. Licensing, access and local operation

Licenses apply to individual components. An Apache label on WorldSculpt does not replace the terms of its encoder, backbone, wrapper or dependencies.

| Component | Verified license/access evidence | Practical implication |
| --- | --- | --- |
| WorldSculpt original code, LoRAs and aggregators | Apache 2.0; official LICENSE/NOTICE | Commercial integration is permitted subject to the license and required notices |
| Vendored Pixal3D code and base checkpoints | MIT, identified in official third-party notices and upstream model metadata | Preserve the applicable MIT notices; not relicensed by WorldSculpt's Apache section |
| TRELLIS.2 components/decoders | MIT | Preserve upstream attribution and license |
| DINOv3 | Separate Meta DINOv3 license; official weights gated by acceptance | Runs locally, but keep its terms and access requirements visible; an ungated repack does not remove the underlying terms |
| NAF | Apache 2.0 in the official repository | Keep its notice/license when distributing covered material |
| BiRefNet, if reused for masks | MIT in the official model card | Separate optional preprocessing component; inspect masks rather than assume they are correct |
| Depth Anything 3 **Base**, if selected | Apache 2.0 in that model card | Do not transfer this license conclusion to every DA3 variant |
| SAM3, if using the provided tracking bridge | Separate SAM license | Not needed for a simple isolated-object route with existing masks; assess its own terms before adding it |
| ComfyUI | GPL-3.0-or-later in inspected source | Distribution must account for Comfy's own license and any linked/derived integration code |
| Community WorldSculpt wrapper | No license file found; licensing issue open in inspected repository | A public repository and an official link do not establish a redistribution license. Clarify permission before shipping its code in Mumblebox |

Primary texts: [WorldSculpt LICENSE](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/LICENSE), [third-party inventory](https://github.com/AlayaLab/WorldSculpt/blob/fac6b83282368063a34e648a07c6cff169e05152/THIRD_PARTY_LICENSES.md), [DINOv3 license](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md), [NAF license](https://github.com/valeoai/NAF/blob/main/LICENSE), [BiRefNet model card](https://huggingface.co/ZhengPeng7/BiRefNet), [DA3 Base model card](https://huggingface.co/depth-anything/DA3-BASE), [wrapper license question](https://github.com/jtydhr88/ComfyUI-WorldSculpt/issues/1).

DINOv3 grants royalty-free rights under its agreement, including use and modification; it is not labeled noncommercial-only. Its conditions include distributing the agreement with covered materials, acknowledging research use in publications, compliance with privacy/trade laws and restrictions concerning reverse engineering and certain end uses. The precise text governs. It is inaccurate to describe the whole stack as unrestricted MIT/Apache or to infer that Meta receives user images. The local encoder does not require sending those images to Meta.

The official Python route can fetch code on first use through mechanisms such as `torch.hub` and Hugging Face remote-code loading. The Comfy-native route avoids assuming that the entire official training environment must be installed. Later installation should pin and inspect actual dependencies, retain download provenance, use safe checkpoint loading, and keep tokens out of workflow JSON, exports and logs. No credentials were needed for this source research and no private reference images were uploaded.

The wrapper's missing license is an unresolved **distribution** issue. This report is not a grant of rights to modify or distribute it. Before approving an implementation that requires modifying the wrapper, resolve that permission or implement the required integration from the permissively licensed official method and Comfy APIs. That is a narrow integration contingency, not permission to build another unrelated pipeline.

## 11. What already exists and what would actually change

The complete architecture and learned weights already exist. The remaining development is an input/compatibility/resource integration, not inventing a new multiview model.

| Area | Already available | Minimum proposed work after approval |
| --- | --- | --- |
| Learned reconstruction | Both official LoRAs, both aggregators, feature projection and native Pixal/TRELLIS components | Install the pinned integration/weights through a license-compatible route; verify all stage patches and aggregators are active |
| Workflow | Supplied 26-node instance graph | Make an independent copy, correct paths, apply the explicit sampling/finishing changes in section 8, keep it visible in existing Comfy Desktop |
| Inputs with known cameras | Released scene format and crop canonicalization | Prepare one object, preserve cameras/masks, make the selected views and anchor visible; enforce the same anchor across paired comparisons |
| User/native-generated images | Existing reference handling and background removal; native DA3 camera/depth implementation | A small input bridge to package images, aligned masks, camera estimates and one 3D box; validate coordinate conversion and reject invalid estimates clearly |
| Resource management | Native partial offload, serial feature extraction, chunked aggregation; Mumblebox cleanup patterns | Handle raw aggregators and cache lifetime, record stage peaks, enforce guards, release resources on failure/cancel |
| Geometry export | Native decoder, GPU remeshing/decimation, placement and GLB saving | Confirm canonical bounds, output directory, GPU execution and exported geometry; retain per-case provenance |
| Mumblebox integration | Single-image workflow, GUI and agent package | **None in the first experiment.** Only integrate an additional route after reviewing useful results |

The generated-image input bridge is the principal custom component. It should translate validated data into the released method's contract. It must not invent a 45-degree camera because a filename says “three-quarter,” independently normalize each object's crop, silently exclude most views, or hide an invalid camera estimate behind a successful queue.

For the first known-camera case, use the released input format directly. For later generated cases, prefer the documented DA3-based route where it gives usable camera/depth estimates. Reuse single-object masks instead of requiring scene-wide object tracking. Package per-view intrinsics in the in-memory contract when they differ; the file loader's shared-intrinsics format must not flatten them incorrectly.

Brian's body-angle question is a useful narrower input problem: infer a character's facing direction relative to the camera. A body estimator such as SAM 3D Body exposes global rotation and camera-related outputs, but converting those into WorldSculpt's calibrated coordinate system and validating them on stylized T-pose images remains untested. It is an optional character-specific follow-up, not a verified general camera solution or a new mandatory dependency in the initial experiment. A shoulder/head yaw estimate alone does not establish focal length, elevation, distance or whole-body pose consistency.

### What is intentionally outside this iteration

- No GUI redesign, Civitai browser work, Pinokio packaging or new image-model support.
- No room segmentation, scene composition or separately generated parts joined into an object.
- No new adapter training, encoder replacement or attention redesign before the released adaptation has been evaluated correctly.
- No texture-quality sweep or prompt rerolls used to disguise geometric failure.

The training release is evidence that this kind of adaptation is possible. It is not a verified home-training recipe. The authors' dataset and complete custom training pipeline have not been established as a ready-to-run package here. A credible later training proposal would first need the actual dataset/render contract, missing trainer/data implementations, reproducible losses/configs, a training-memory measurement, dataset rights and a compute quote. This research supports neither a $50 estimate nor a weekend/16 GB training promise. Additional training is not currently justified over trying the released weights.

## 12. Bounded future validation and stopping conditions

**Build the complete independent path before queueing the evaluation.** The early control case tests that complete path; it is not a substitute for building it or a reason to declare the user problem solved. No evaluation has been run during this research.

Maximum: **eight planned reconstruction attempts, plus two focused repair/retry attempts** across the whole evaluation. Count a queued reconstruction attempt even if it fails. Do not use leftover slots for unrelated models, prompt tuning or additional subjects. A new installation check without generation is not a reconstruction attempt.

All cases use fixed recorded seeds, pinned revisions, explicit settings, matching image/mask/camera associations and the same finishing policy where the comparison permits it. Generate and approve practical reference sets once, using Brian's requested native image-generation tool. Keep the same approved anchor in its baseline and multiview comparison. If a prior baseline has adequate provenance, reuse it and omit the redundant run.

Check the actual anchor chosen by the wrapper before queueing. Its automatic largest-mask selection may differ from the preferred three-quarter view. If that happens, a minimal explicit anchor-selection change must preserve the canonicalization and camera transforms and be checked before the paired runs. Do not enlarge/crop one picture independently to manipulate the selector, and do not silently compare two different anchors.

| Case | Question | Fixed input and comparison |
| --- | --- | --- |
| V1 | Does the full method work with valid inputs on this machine? | Simple rigid object, four coherent rendered views, exact perspective cameras and masks, both adaptations and both aggregators |
| V2 | Does a small observation error destroy that valid result? | Same V1 inputs, change one non-anchor camera azimuth by 3 degrees; keep everything else fixed. This is within the training augmentation's stated angular scale, not a guaranteed tolerance |
| V3 | What does the existing practical route achieve? | One best three-quarter image of a hard-surface object through single-image Pixal3D |
| V4 | Do intended extra details improve the same object's actual geometry? | V3 anchor plus three approved views from the native image tool, prepared cameras/masks, full WorldSculpt |
| V5, conditional | Can a valid baseline isolate learned-fusion benefit? | Same V4 material through a matching supported ordinary multiview path **only if its camera/input contract can be matched**. Otherwise omit; do not invent a baseline or remove required WorldSculpt pieces and label it the same method |
| V6 | What is the second subject's practical starting result? | One best three-quarter fixed-T-pose character image through single-image Pixal3D |
| V7 | Does the learned route help a materially different subject? | V6 anchor plus three approved fixed-pose views, full WorldSculpt, only if earlier stages permit a meaningful test |
| V8, optional | Would excluding one identified contradictory view help? | One predeclared omission from V4 or V7, preserving all other settings. Use only if the observed failure makes that question consequential |

Choose subjects with visible, countable geometric requirements. For example, a hard-surface object might have one rear raised housing and a side opening; a character might have a particular backpack and a fixed limb arrangement. Record those requirements before reconstruction. An emblem or color change alone tests appearance, not geometry.

The known-camera control may use a small existing mesh rendered with recorded cameras. That mesh is a calibration input for V1/V2, not a replacement output assembled to fake the experiment. It must include asymmetric features that expose swapped cameras or duplicated fronts. The practical V4/V7 cases remain the central question.

### Inspectable output and scoring

For every completed case, retain the actual GLB, source images/masks, camera/box metadata, active-component record, accepted-view count, settings and stage resource log. Show the exported mesh in the existing visible application with neutral material from front, rear, both sides and elevated viewpoints. Also inspect the file for nonempty finite vertices/faces and successful reload. A rendered preview alone is not proof of a valid export.

Use this small rubric, recorded before comparing results:

| Criterion | Pass condition | Severe failure |
| --- | --- | --- |
| Global proportions | Comparable to or better than the single-image baseline from multiple viewpoints | Collapsed, substantially flattened, twisted or stretched object |
| Added intended geometry | Predesignated hidden/side features appear in the correct region as actual geometry | Missing feature, duplicated front on the back, or a feature moved to the wrong side |
| Existing visible structure | Anchor-visible defining parts remain recognizable | Major damage to the original well-observed shape |
| Thin parts/openings | No important loss caused by masks or finishing; remaining defects disclosed | Required limbs, handles or holes fused away or disconnected beyond practical use |
| Export and cost | One reloadable mesh; measured resources within limits; tolerable reference preparation | Invalid export, unrecovered memory exhaustion, CPU finishing substitution or substantial manual calibration required for every object |

This is a practical visual/structural evaluation, not a statistically powered benchmark. Do not claim general superiority from two subjects. Do not require every small detail to be perfect before stopping.

### Outcome definitions

- **Technical success:** both complete trained stages consume the intended references, fit the managed target system, finish on the GPU, release resources and export an inspectable mesh. This establishes operation only.
- **Promising practical improvement:** V4 and V7 each retain the useful anchor geometry and improve the predeclared additional geometric requirements over their single-image baselines, without a severe new distortion. Preparation and elapsed time must be acceptable to Brian.
- **Conditional usefulness:** the route works only for calibrated renders/photos, only one subject class improves, or acceptable results require substantial manual camera work. State that narrower result and stop for a product decision.
- **Rejection for the generated-view target:** valid, complete runs on the practical cases fail to add the intended geometry or introduce severe distortions, with no specific implementation defect explaining the failure. Do not keep rolling seeds until a showcase appears.
- **Technical limit / inconclusive:** cameras cannot be made credible, the installed implementation cannot apply the required components, or the working set still exceeds resources after the focused repairs. Report the exact failed stage and evidence. This does not prove learned fusion is scientifically ineffective.

A repair/retry must name the observed defect, its owning layer and the smallest evidence-based change. Examples are a camera-axis conversion error, an aggregator retained on GPU, or an incorrect sampler interval. “Try another seed because this looks ugly” is not a repair. At most two such retries are authorized by the proposed envelope; expanding it requires a new decision.

**Stopping point:** after the approved cases are completed, or a demonstrated technical limit prevents completing them within the two retries, present all actual exports and failures with this rubric, then stop for review. No integration into Mumblebox, extra subjects, training project or hidden parameter sweep follows automatically.

## 13. Important discoveries, rejected assumptions and remaining questions

### Discoveries that change the recommendation

1. **This is a real trained extension of the mesh model.** The two LoRAs and two learned aggregators address multiview conditioning inside the geometry pipeline. That is substantially closer to the original requirement than concatenating pictures or combining independent meshes.
2. **The whole mechanism is required.** The LoRAs alone are insufficient; missing aggregators fall back to averaging. Static metadata confirms the released adapter targets correspond to the local BF16 base, but runtime patch matching still needs verification.
3. **The camera problem remains.** Training with small camera errors gives a reason to investigate tolerance; it does not make arbitrary camera labels accurate. Generated views are the unproven practical input class.
4. **The supplied graph is a starting point, not a universally correct preset.** Its guidance differs from the official adapted-model default, and local shifted guidance intervals need care. Explicit sampling is an evidence-based change, not speculative prompt tuning.
5. **16 GB needs deliberate lifecycle handling.** Native offloading helps, but raw aggregators, dense conditioning and finishing can still occupy substantial memory. The graph's 768 finishing reservation is a concrete reason to change the initial finishing configuration.
6. **The method can be tested without commissioning a new adapter.** Custom training should wait for a demonstrated remaining limitation in a correctly integrated released method.

### Assumptions rejected by the evidence

| Assumption | Why it was rejected |
| --- | --- |
| “It knows which entire views to discard” | Learned weights are local to feature locations; mean/variance pathways still include observations. There is no verified whole-image truth detector |
| “Four AI images automatically become four correct camera views” | Camera, mask, scale and fixed-geometry assumptions remain explicit in source |
| “A collage is the expected input” | The released object path takes separate observations with corresponding cameras and masks |
| “A small adapter download proves low VRAM use” | Base networks, conditioning tensors, activations and finishing dominate additional memory |
| “An RTX 5090 demo proves 16 GB support” | It demonstrates a 32 GB card, a different resource envelope |
| “The single-image script's 10–12 GB guidance proves this route fits” | It is not a measured full WorldSculpt multiview configuration |
| “More views must improve the result” | Published gains concern appropriate observations; contradictions or calibration errors can hurt, and learned aggregation is not better on every reported metric |
| “A T-pose makes the cameras known” | It constrains body pose; facing direction and full camera calibration still require estimation or measurement |
| “Texture improvement proves geometry improved” | Optional texture uses the base model and can conceal surface defects |
| “An ungated repack removes DINOv3 terms” | Access mechanism and license obligations are separate |
| “All source-visible code is freely redistributable” | The wrapper's own license grant was not found |

### Remaining uncertainties and their smallest useful resolution

| Question still open | What resolves it | Affected decision |
| --- | --- | --- |
| Full four-view peak VRAM/RAM on 16 GB | V1 with per-stage measurement and the proposed lifecycle handling | Whether the complete method is usable on this hardware |
| Correct Comfy sampler/LoRA conversion behavior | Inspect actual matched patch keys, emitted sigma schedule and active stage modules before V1 | Whether the test represents the released method faithfully |
| DA3 camera/depth estimates for independent generated views | Reprojection/axis/box checks on the approved V4/V7 inputs before queueing | Whether those runs test fusion or merely bad calibration |
| Tolerance of semantic disagreement | V4/V7, plus the single optional V8 exclusion | Whether the optional route helps Mumblebox's intended inputs |
| Body-facing yaw estimate for stylized characters | A separate narrowly scoped SAM 3D Body coordinate/output validation, only if character-camera preparation becomes the limiting issue | Whether to add a character-specific preparation aid; not required for V1 |
| GPU finishing at 512 preserves useful small parts | Compare decoded versus finished geometry within the same case | Whether finishing is erasing the model's useful result |
| Community wrapper redistribution/modification rights | A license or explicit maintainer permission; otherwise a permitted implementation of the official integration contract | Whether and how its code can be shipped/modified |
| Training feasibility and cost | Recovered full training implementation, data rights, a memory profile and actual compute quote | Only a later adaptation project if the released method has a clear unresolved limit |

There is no need for another broad image-model or mesh-model survey to answer these questions. Most remaining uncertainty is about running this specific released method correctly with suitable inputs; more general browsing would not substitute for those measurements.

## 14. Coverage, evidence files and next decision

| Research package | Answer location | Evidence or honest remaining limit |
| --- | --- | --- |
| R01 Guidance/release/lessons | Sections 2, 7, 13 | Pinned releases, previous crop/camera/resource lessons, no official skill found |
| R02 Image source | Sections 2, 5 | No preferred 2D generator; generated 3D-scene renders differ from independent generated views |
| R03 Mechanism | Section 3 | Full projection, LoRA and learned-aggregation source; checkpoint target metadata |
| R04 Training/robustness | Sections 4, 11, 13 | Published tests and augmentation; conflicting AI geometry and home training unverified |
| R05 Cameras/preparation | Section 5 | Camera conventions, intrinsics, cropping and estimates bridge; yaw distinction |
| R06 Masks/view selection | Sections 5, 8 | Foreground contract, anchor selection and filtering, preserved affine transforms |
| R07 Graph/artifacts | Sections 6, 7 | Supplied 26-node/34-link graph and exact required/optional models |
| R08 Settings | Section 8 | 42 input declarations indexed; exact initial proposal and sampler discrepancy |
| R09 Installation/compatibility | Section 7 | Unexecuted install/rollback route, local versions and static API compatibility |
| R10 Hardware/resources | Section 9 | Primary hardware statements, local inventory, unload schedule and proposed guards; no 16 GB runtime proof |
| R11 GPU finishing/export | Sections 8, 12 | Native GPU route, geometry versus texture distinction, export inspection requirements |
| R12 Licenses/local operation | Section 10 | Component texts and gated access; wrapper permission unresolved |
| R13 Minimal adaptation/training | Section 11 | Existing components, input/resource integration changes, no speculative training commitment |
| R14 Validation/synthesis | Sections 1, 12, 13 | Concrete conditional proposal, eight-case ceiling plus two repairs, explicit stopping outcomes |

Evidence files beside this report:

- `source-manifest.json`: URLs, saved filenames, sizes and hashes for collected source material.
- `repository-inventory.json`: pinned official/community trees and release inventory.
- `graph-audit.json`: node IDs, types, widget values and links from the supplied instance graph.
- `checkpoint-metadata-audit.json` and `checkpoint-target-audit.json`: bounded checkpoint metadata and local base-name matching; no model execution.
- `settings-source-index.json`: literal wrapper input declarations extracted without importing the wrapper.
- `local-readonly-inventory.json`: local hardware, dependency metadata and relevant file presence.
- `local-source-audit.json`: local source hashes and the guidance-interval arithmetic.
- `sources/`: source/configuration/model-card/license snapshots, paper/project material and author discussion evidence.

Research completion means these questions have been answered to the limit of available source evidence and a concrete, bounded proposal is ready. It does **not** mean that WorldSculpt has run on this machine or that conflicting views have been solved.

**Next decision for Brian:** approve or revise the independent experiment described here. Its complete path is approved separate views → aligned masks and credible cameras → both WorldSculpt geometry stages with both learned aggregators → GPU finishing → one inspectable GLB. Resolve the wrapper permission route before modifying/distributing its code. Preserve the existing Mumblebox application, do no GUI work, and stop after the bounded results for review.

No implementation, generation, model installation, application restart, workflow alteration, commit or push was performed for this report. The parked Civitai integration was not resumed.

Review record, 23 October 2026: all 14 research packages have a mapped answer or explicit remaining uncertainty. The 26-node/34-link graph audit, 42 declared wrapper inputs and 180 matching adapter targets per geometry stage were checked against the retained evidence. All 55 downloaded source entries passed their recorded size/hash checks. All 16 inspected local Comfy source files still match their read-only audit hashes. Parent Git HEAD and status remain the recorded detached revision with the pre-existing untracked `custom_nodes/comfyui-mcp/` entry. These are research/document integrity checks, not runtime or mesh-quality tests.

