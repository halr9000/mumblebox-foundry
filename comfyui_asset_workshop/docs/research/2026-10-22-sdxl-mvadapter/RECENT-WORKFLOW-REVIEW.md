# Recent workflow review: PixelArtistry, Pixaroma, and NVIDIA

Reviewed: 2026-10-22. Research addition for the next Mumblebox discussion; no implementation decision is adopted by this document.

## What Brian is trying to solve

The requirement is a good local mesh with control over its unseen sides, style, and specific details. Multiple images are one possible means of achieving that control, rather than a requirement to maximize view count. A front image must not force the user to accept an arbitrary backpack, shirt back, or rear panel. A texture change and a geometry change are different capabilities.

Current constraints remain a 16 GB GPU, 64 GB RAM, local inference, GPU finishing, and deliberate model unloading between stages. Keep the existing Mumblebox workflow intact. Research should lead to one coherent proposed workflow. Brian has not approved another model comparison, implementation, model download, paid service, or training run during this review.

## Evidence and coverage

This review used video metadata and transcripts, downloadable workflow JSON, repository documentation, model/dataset cards, and research project pages. It is not a claim that the videos were watched frame by frame or that their workflows were run locally.

PixelArtistry coverage was bounded to July 22 through October 22, 2026. Nine relevant videos were reviewed through transcripts and metadata:

| Published | Video | Relevant subject |
|---|---|---|
| July 26 | [P3EqzErB4l4](https://www.youtube.com/watch?v=P3EqzErB4l4) | Local 3D studio |
| August 9 | [RguOAJgJTwE](https://www.youtube.com/watch?v=RguOAJgJTwE) | NVIDIA and Hunyuan3D Buffalo research |
| August 24 | [Ff_tdMsndzQ](https://www.youtube.com/watch?v=Ff_tdMsndzQ) | Local 3D workflow |
| August 26 | [o7VJnIN31Ds](https://www.youtube.com/watch?v=o7VJnIN31Ds) | Native Comfy 3D pipeline |
| September 18 | [_lgyED4IkJg](https://www.youtube.com/watch?v=_lgyED4IkJg) | Multiview Pixal3D |
| September 30 | [dmDrktqyT5o](https://www.youtube.com/watch?v=dmDrktqyT5o) | Watertight finishing |
| October 7 | [PpuNKVoSYB4](https://www.youtube.com/watch?v=PpuNKVoSYB4) | Qwen turnaround to Pixal3D |
| October 12 | [CSiNa_ZCwwA](https://www.youtube.com/watch?v=CSiNa_ZCwwA) | Image to printable mesh |
| October 18 | [4QAgeKYfBnU](https://www.youtube.com/watch?v=4QAgeKYfBnU) | UltraTex texturing |

Four PixelArtistry graphs were inspected: Qwen turnaround to multiview Pixal3D, the multiview print workflow, the game-ready finishing workflow, and UltraTex Standard 6 Views PBR. Additional animation and hosted-service video titles were screened but are not counted as full reviews.

Brian then supplied two QR codes. They were decoded locally without uploading the attachments. Both link to Pixaroma, a different channel:

| Published | Video | Materials examined |
|---|---|---|
| September 9 | [Image to 3D Made Easy: Trellis 2 + Pixal3D, Ep33](https://www.youtube.com/watch?v=BVpE-g39SZU) | Full transcript; seven graphs inventoried; relevant model, camera, finishing, and sampler settings inspected |
| September 17 | [Pixal3D Multiview / Load & Save 3D, Ep34](https://www.youtube.com/watch?v=LSDLengs4hY) | Full transcript; downloaded seven-workflow archive; detailed wiring inspection of geometry-only, PBR HQ, and Klein Keep the Angle graphs |

Snapshots are retained under `sources/pixelartistry/`, including the two Pixaroma caption files and `Pixaroma-Ep33-Workflows.zip` / `Pixaroma-Ep34-Workflows.zip`. Archives were read as data; no bundled code or Blender add-on was installed or executed.

## Findings that affect the next workflow

### 1. A useful new Klein adapter exists, but it solves texturing

[UltraTex](https://github.com/yiboz2001/UltraTex) releases code, training scripts, and checkpoints for multiview texture synthesis. Its Klein route uses **FLUX.2-Klein-base-9B**, dedicated albedo and metallic/roughness LoRAs, and a foreground-aware VAE decoder. Geometry-derived normal maps constrain six jointly generated views. This is concrete evidence that a modern image model can be trained for coordinated multiview work.

Its input is an existing mesh. It improves the surface appearance; it does not establish a method for repairing the first mesh's proportions, adding an absent backpack, or generating accurate geometry from inconsistent references. The released 9B LoRAs do not fit Klein 4B. Training code being available also does not establish a weekend training budget on Brian's GPU. [Official project and paper](https://yiboz2001.github.io/UltraTex/).

The [ComfyUI wrapper](https://github.com/visualbruno/ComfyUI-UltraTex) provides preparation, specialized LoRA loading, sampling, and baking nodes. It renders front/left/back/right/top/bottom normal maps and masks, and supports GPU UV preparation. It requires the base Klein checkpoint, not the ordinary distilled 9B checkpoint. Its specialized loader handles checkpoint keys the stock LoRA loader cannot necessarily consume. Published 16 GB measurements are encouraging author evidence, not local proof.

The wrapper's documented positional-encoding requirements are another concrete lesson: the model learns a particular spatial arrangement of reference and guide information. Camera/image contracts are part of the method; a stronger generic prompt does not replace them. A second rotated texture rig improves coverage of the same mesh, not the accuracy of a regenerated second mesh.

The [PixelArtistry UltraTex workflow](https://github.com/pixelartistry/PixelArtistry-UltraTex) supplies an inspectable six-view PBR graph. Treat it as a serious candidate for the texture stage. Its front appearance reference does not, by itself, demonstrate independent user control of a specific rear logo or unseen material. Code licensing and base-model/weight licensing must be evaluated separately before distribution.

### 2. PixelArtistry's turnaround workflow still has the failure we encountered

The [Qwen/Pixal3D workflow](https://github.com/pixelartistry/PixelArtistry-Pixal3D-Multiview) uses Qwen to produce a four-view strip, splits and crops it, removes backgrounds, and passes the results to native Pixal3D multiview conditioning. The inspected graph uses separate per-view cropping and a fixed FOV of 20. It contains neither an MV-Adapter nor an explicit crop-transform-to-camera calibration bridge.

The author discusses correcting crops and view assignments. Turning prompt refinement off prevents a helper from rewriting the requested camera instructions. These are useful safeguards, but the graph does not demonstrate that four independent generated views have metrically compatible proportions and cameras.

The [October 12 print tutorial, around 13:30](https://www.youtube.com/watch?v=CSiNa_ZCwwA&t=810s) reports a distorted mesh from mismatched views. Its [released graph](https://github.com/pixelartistry/PixelArtistry-Image-to-3D-Print) is therefore evidence of useful construction and finishing steps, alongside an unresolved input-consistency limitation. A tutorial's successful example is not proof that the upstream problem is solved generally.

### 3. Pixaroma provides useful reference wiring, not a hidden angle-control model

The [Ep34 download](https://workflows.pixaroma.com/ep/34/) contains separate geometry-only, vertex-color, textured-mesh, and Klein image-rendering workflows. In the inspected multiview graphs:

- Each reference has an explicitly named front, left, back, or right input.
- BiRefNet masks feed a per-view `ImageCropToMask` at 1024 square with padding 1.1.
- `Pixal3DMultiViewConditioning` uses a fixed FOV of 20 and the multiview-specific Pixal3D checkpoint.
- Native structure, shape, and upsample stages build the mesh.
- The HQ branch includes UDF remeshing, decimation, PEC UV unwrapping, texture baking, normal/AO baking, and a VRAM-release node.

There is no joint image-generation model or learned camera-control adapter in that graph. At [3:13 in the video](https://www.youtube.com/watch?v=LSDLengs4hY&t=193s), the author lists local image models as possibilities but says he usually creates views with ChatGPT or Nano Banana. That distinction matters for our all-local requirement.

At approximately 4:18-6:40 and 11:13, he reports holes, seed sensitivity, and unsuccessful repair attempts. Simplifying small grille features in the reference helped his example. This is an observation from his examples, not a universal instruction to remove the user's desired details. His 24 GB timings are not a performance promise for Brian's 16 GB GPU.

The [Ep33 archive](https://workflows.pixaroma.com/ep/33/) separates TRELLIS.2 and Pixal3D routes. The Pixal3D graphs use `LoadMoGeModel`, `MoGeInference`, and `MoGeGeometryToFOV`. That is an FOV-estimation path; the graph does not demonstrate recovery of arbitrary multiview azimuth and elevation from inconsistent generated images. It also includes low/high resolution choices and PEC finishing. Those are reusable implementation references, not grounds for an unrelated model contest.

### 4. The impressive Klein render is an image, not repaired geometry

Both Pixaroma episodes include a "Keep the Angle" workflow. Detailed Ep34 inspection shows this route:

`Load 3D rendered image -> VAE encoding -> initial sampler latent + reference conditioning -> Klein -> decoded image`

The example uses the ordinary Klein 9B route with four sampling steps, CFG 1, and denoise 0.7. No ControlNet or camera LoRA is present in this graph. The rendered color image supplies both the visual reference and the starting image that the sampler can partially redraw.

This explains the author's reported tradeoff: lower denoise keeps the view and composition more closely, but can also retain mistakes. Higher denoise offers more freedom and can change the view or details. The graph ends at image output and comparison, not a revised mesh. [Ep34 explanation at 13:32-14:53](https://www.youtube.com/watch?v=LSDLengs4hY&t=812s); [Ep33 explanation at 15:30](https://www.youtube.com/watch?v=BVpE-g39SZU&t=930s).

For Mumblebox, these graphs are useful examples of mesh-guided picture generation. They do not prove that feeding those pictures back into reconstruction produces a better mesh. Brian's concern about copying an incorrect rough shape remains valid.

### 5. Watertight finishing and shape fidelity must remain separate

The [PixelArtistry finishing graphs](https://github.com/pixelartistry/PixelArtistry-Watertight-Meshes) combine remeshing, [WTiVo](https://github.com/Mstafa-awad/WTiVo-WatertightVoxel-ComfyuiNode), Blender-based reduction, UVs, and baking. These offer concrete postprocessing ideas. They cannot reconstruct a missing intentional feature solely by closing holes.

Important implementation checks remain: preserving thin parts and intentional openings; avoiding loss of intended disconnected pieces when keeping only the largest component; Python/CUDA wheel compatibility; temporary peak memory; and stage-by-stage GPU versus CPU behavior. WTiVo's documented prebuilt Python version differs from this installation's previously observed Python version. Its GPL licensing also needs consideration before bundling.

A watertight mesh can still be the wrong shape. A visually attractive textured mesh can still have broken geometry. Print readiness additionally depends on meaningful scale, wall thickness, and connected/supportable structure.

### 6. NVIDIA Axolotl3D directly addresses the editing requirement, but is not released for this workflow

[Axolotl3D](https://research.nvidia.com/labs/sil/projects/axolotl3d/) combines images, visibility masks, cameras, and partial 3D points. It fine-tunes Hunyuan3D-DiT for completion and editing, with existing points helping preserve unchanged geometry. This closely matches Brian's request to fix an unseen region using an edited reference.

On October 22, the official page's HTML still contained disabled **Code (Coming Soon)** and **Model (Coming Soon)** links. No official downloadable checkpoint or local setup route was verified. The Kaolin UI shown in the demonstration is not a release of the trained model. There is also no verified 16 GB inference result for Mumblebox. Treat the [paper](https://arxiv.org/abs/2607.20660) as relevant method evidence, not an available dependency or a ready-made adapter for stock Hunyuan3D.

### 7. There is practical training data if a targeted adapter later becomes justified

[G-buffer TexVerse](https://huggingface.co/datasets/YiboZhang2001/G-buffer-TexVerse) publishes aligned renders, camera metadata, normals, position maps, albedo, and material channels from the same objects. It lists 351,847 released assets and a 268,365-asset filtered UltraTex training subset. Six canonical views and a larger spherical-view collection provide useful distinctions between texture training and angle coverage.

The dataset card declares CC0. Its approximately 25.3 TB total size makes an indiscriminate download inappropriate. No dataset download or training was performed. Any future proposal needs a small justified subset, provenance checks, a concrete conditioning target, and measured training-memory requirements. It is evidence that suitable structured data exists; it is not evidence that a general camera adapter is inexpensive or already solved.

## What this changes in the research direction

1. **Retain the hidden-detail requirement.** Reducing input count is acceptable only if the workflow still gives the user meaningful design control over unseen regions.
2. **Distinguish three problems:** generating the right geometry, repairing its surface/topology, and producing consistent textures. A strong result in one is not proof of the others.
3. **Prioritize the released UltraTex route for texture-stage evaluation in the next proposal.** It is the clearest new, concrete example here of a modern model plus purpose-trained multiview components.
4. **Use the Pixaroma and PixelArtistry files as source references for preprocessing, stage controls, memory release, and GPU finishing.** Their published failures and camera assumptions belong in the proposal too.
5. **Keep Axolotl-style geometry-preserving editing as a research target.** Do not make an unreleased checkpoint the foundation of the next runnable workflow.
6. **Do not restart the two-mesh loop simply because mesh-guided images look attractive.** The evidence reviewed here does not show that it reliably improves geometry.

## Questions still requiring resolution before an implementation recommendation

- Which released, locally runnable method can change a user-selected geometric region while adequately retaining the rest? A backpack requires geometry; a shirt emblem may require only texture editing.
- If generated multiview references remain part of the route, what method actually enforces or estimates their compatible cameras and proportions? Fixed labels/FOV and separate tight crops are assumptions, not calibration evidence.
- Can a selected texturing route honor an additional rear reference or masked rear edit, rather than only a front appearance image?
- Which finishing operations preserve the user's small parts and openings on the actual supported versions and 16 GB GPU?
- What are the licensing and distribution conditions of the exact chosen code, base weights, adapters, and data? A repository's code license alone does not answer all of them.

These questions define what the next synthesis must resolve or explicitly limit. They do not authorize another implementation, training run, broad benchmark, or paid service.

## Scope of changes made during this review

Saved research sources and this addendum only. No Comfy workflow, UI, model settings, checkpoints, application process, or existing generation was changed. No runtime performance or mesh-quality success is claimed.
