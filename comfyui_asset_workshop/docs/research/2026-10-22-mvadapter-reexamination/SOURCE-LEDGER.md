# Focused MV-Adapter research: source ledger

Checked 2026-10-22. This is source research, not an installation or generation log. Local source inspection, authors' demonstrations, forum reports, and proposed engineering are different evidence classes. The report makes the recommendation; this ledger makes it traceable.

## Saved work reviewed first

The adjacent [previous research collection](../2026-10-22-sdxl-mvadapter/REPORT.md), its source/question registers, workflow inventory, follow-up, validation proposal and recent-workflow review were read. Relevant passages in the October 20 model-guidance and October 21 mesh-first/applied-synthesis reports were checked. Their saved source files remain the primary local code archive. The later assembly recommendation is superseded by Brian's explicit direction.

The existing [camera experiment results](../../../../mumblebox_camera_experiment/RESULTS.md) establish earlier tests of Pixal and Klein/RefControl, not a successful SDXL/MV-Adapter reconstruction. Its matched-camera controls and failures with generated views inform the new camera and quality gates. Counts and hardware readings in that file belong to those earlier experiments only.

## Release pins

These revisions were returned by public GitHub/Hugging Face metadata during this research. Model weights were not downloaded.

| Component | Revision | What was inspected |
|---|---|---|
| huanngzh/MV-Adapter | 4277e0018232bac82bb2c103caf0893cedb711be | README, inference script, image pipeline, attention implementation, requirements, license |
| huanngzh/ComfyUI-MVAdapter | 9d6d8afeff135d81a31f16dde5291d8b40dbb0a4 | Nodes, utilities, camera helper, example graphs, requirements, README |
| huanngzh/mv-adapter weights | 6de4033df6b53366f3c009d22f5ec434bb55e59f | Card, file inventory, task-specific weight names, license metadata |
| stabilityai/stable-diffusion-xl-base-1.0 | 462165984030d82259a11f4367a4eed129e94a7b | Card, license, release metadata |
| madebyollin/sdxl-vae-fp16-fix | 207b116dae70ace3637169f1ddd2434b91b3a8cd | Card/license metadata and use by the adapter examples |
| ZhengPeng7/BiRefNet | e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4 | Card/license metadata and explicit author-graph selection |
| Stable-X/StableNormal | 594b934630ab3bc71f35c77d14ec7feb98480cd0 | Hub loader, pipeline, normal conventions, dependencies, license |
| Stable-X/stable-normal-v0-1 | 4362d11c636ef42ed117dd76984c7f2d83e6abd9 | Card, metadata, model index |
| Stable-X/yoso-normal-v0-3 | 2202fcb69960d94b437e06c19c556a12ceeb57c0 | Card and metadata |
| facebookresearch/dinov2 | 7764ea0f912e53c92e82eb78a2a1631e92725fc8 | License and hub backbone loader; StableNormal uses dinov2_vitl14 |
| pengHTYX/Era3D | a2ce68da53c0dc4df403112c53692b9ba893a4f0 | Orthographic loader, rays, normal conversions, NeuS model/system, config, export, requirements, LICENCE |
| tatsy/torchmcubes | a9ac95aa329957ba646e7bb057f825f5dfa77f38 | Current main, CUDA dispatch, build configuration, README, MPL-2.0 license |
| SuhZhang/CorrAdapter | a269d224f89aa7ae2bed1b4c61b2613352e8a1d2 | Released MVAdapter subproject, inference, attention, pipeline, repository license |
| SuhZhang/CorrAdapter-Model-on-MVAdapter | ea63a23219be214675b0f11ffda99b60e0e21b08 | Card, four-shard artifact inventory; license field absent |
| zhihao0512/EDN | b177aa858b8287480e11e345cfa8db618cf04347 | README, tree, inference and pipeline; checkpoint entries present, no root license found |
| SarahWeiii/diso | 9792ad928ccb09bdec938779651ee03e395758a6 | README, setup, license; noncommercial restriction excludes it from the proposed commercial-use stack |

## Evidence by question

### S01 — The published method and actual reconstruction result

Primary: [final ICCV 2025 paper](https://openaccess.thecvf.com/content/ICCV2025/papers/Huang_MV-Adapter_Multi-View_Consistent_Image_Generation_Made_Easy_ICCV_2025_paper.pdf), [final supplement](https://openaccess.thecvf.com/content/ICCV2025/supplemental/Huang_MV-Adapter_Multi-View_Consistent_ICCV_2025_supplemental.pdf).

Both PDFs are saved in sources, text extracted, and main-paper page 8 visually inspected. Section 5.4 uses StableNormal and NeuS following Era3D. Table 3 reports SDXL MV-Adapter reconstruction CD 0.0206 and IoU 0.5682, versus Era3D(SD2.1) 0.0329/0.5118, on that study's evaluation. These are author results, not this PC's results. The adjacent memory column is TRAINING memory, not inference VRAM. The supplement documents six orthographic image-conditioned views, evaluated input-angle range, training data and separate arbitrary-view training. It does not establish dependable arbitrary hidden-feature instructions.

### S02 — Exact image recipe and cross-view coupling

Primary: [image inference script](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/scripts/inference_i2mv_sdxl.py), [attention](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/models/attention_processor.py), [pipeline](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/mvadapter/pipelines/pipeline_mvadapter_i2mv_sdxl.py), [weights](https://huggingface.co/huanngzh/mv-adapter).

Source verified: shared row-wise multiview attention plus reference attention; image-conditioned SDXL adapter; six 768-square outputs; script defaults 50 steps, CFG 3, reference-conditioning scale 1; SNR shift scale 8. A function signature accepting a list of prompts does not prove view-specific text semantics. The released ordinary path is not the separately trained arbitrary-view method described later in the paper.

### S03 — Author Comfy graph, preprocessing and dependencies

Primary: [author extension](https://github.com/huanngzh/ComfyUI-MVAdapter), [nodes](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/nodes.py), [Diffusers example](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_diffusers.json), [requirements](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/requirements.txt).

Source verified: the example explicitly selects DDPM and ZhengPeng7/BiRefNet. Background-removal class defaults must not silently substitute BRIA. Source foreground is centered with longest side approximately 90% of the frame. The reference-image batch becomes its first image. README estimates 13–14 GB for image inference; that is not a measured guarantee for this installation. Old pinned Diffusers/Transformers conflict with assumptions about current Desktop compatibility.

### S04 — Cameras are canonical, not offsets from the input photo

Primary author replies: [MV-Adapter issue 42](https://github.com/huanngzh/MV-Adapter/issues/42), [Comfy extension issue 40](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/40). Source: [camera helper](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/mvadapter/utils/camera.py).

The author describes model-predicted canonical front and target sides, not fixed rotations relative to the input image. Back-left/back-right are difficult because the standard model was not trained on them. Source cameras are orthographic, span 1.1, distance 1.8, elevation zero; target azimuth list is 0/45/90/180/270/315 with the implementation's -90-degree adjustment. No pose-estimation guarantee follows from those intended cameras.

### S05 — Reconstruction release gap

Primary: [MV-Adapter issue 13](https://github.com/huanngzh/MV-Adapter/issues/13), [issue 33](https://github.com/huanngzh/MV-Adapter/issues/33), [Era3D source](https://github.com/pengHTYX/Era3D/tree/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl).

The request for the paper's reconstruction code remains unresolved in the inspected issue. The separately released TEXTURING code is not that initial reconstruction script. Public Era3D NeuS supplies the relevant optimizer, but recreating the MV-Adapter evaluation requires connecting and validating conventions. It is a source-backed reproduction proposal, not a complete ready-to-run released graph.

### S06 — Normal and ray conventions

Primary: [StableNormal author convention reply](https://github.com/Stable-X/StableNormal/issues/18), [Era3D loader](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/datasets/ortho.py), [ray utilities](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/ray_utils.py), [normal utilities](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/mvdiffusion/data/normal_utils.py).

Source verified: Era3D's loader assumes front-frame normals; independently predicted StableNormal maps need explicit conversion. StableNormal's author describes a DSINE-like left-handed convention. Era3D applies further OpenGL/OpenCV conversion. Its default orthographic ray plane spans two units; it is not automatically the MV-Adapter span. The report requires a calibrated common transform and preserved framing, not a guessed flip.

### S07 — Actual optimizer and export

Primary: [configuration](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/configs/neuralangelo-ortho-wmask.yaml), [geometry](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/geometry.py), [NeuS](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/models/neus.py), [saver](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/instant-nsr-pl/utils/mixins.py).

Source verified: one per-object SDF/radiance fit to RGB/mask/normal evidence, 3,000-step example, 256 extraction grid. Stock extraction uses CPU PyMCubes; its torch alternative is explicitly disabled for scaling problems. Export supports vertex color, not an automatic PBR material. Coordinate conversion and scale occur in the saver as well as the loader. They must not be applied twice.

### S08 — GPU finishing candidate and rejected candidate

Primary: [current torchmcubes source](https://github.com/tatsy/torchmcubes/tree/a9ac95aa329957ba646e7bb057f825f5dfa77f38), [dispatch](https://github.com/tatsy/torchmcubes/blob/a9ac95aa329957ba646e7bb057f825f5dfa77f38/torchmcubes/__init__.py), [MPL terms](https://github.com/tatsy/torchmcubes/blob/a9ac95aa329957ba646e7bb057f825f5dfa77f38/LICENSE), [Mozilla FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/).

GPU marching cubes is implemented; current build needs CUDA 12+, C++20 and CMake 3.24+. Current main is October 19, 2026, and includes MSVC handling. Crucially, a CPU-only build can accept CUDA tensors, run on CPU, and return CUDA tensors. The proposed integration must require HAS_CUDA and verify the actual kernel. Current license is MPL-2.0, not old third-party claims of MIT. Windows compilation remains untested here.

[DISO license](https://github.com/SarahWeiii/diso/blob/9792ad928ccb09bdec938779651ee03e395758a6/LICENSE) is CC BY-NC 4.0; its setup metadata agrees. It is excluded from the proposed commercial-use stack. Do not silently include it because its CUDA implementation is attractive.

### S09 — New, directly relevant consistency research

Primary: [CorrAdapter paper](https://openaccess.thecvf.com/content/CVPR2026/papers/Zhang_Align_Images_Before_You_Generate_CVPR_2026_paper.pdf), [code](https://github.com/SuhZhang/CorrAdapter), [released subproject](https://github.com/SuhZhang/CorrAdapter/tree/a269d224f89aa7ae2bed1b4c61b2613352e8a1d2/image-conditioned/static/MVAdapter), [trained checkpoint card](https://huggingface.co/SuhZhang/CorrAdapter-Model-on-MVAdapter).

Paper PDF saved; page 8 visually checked. CorrAdapter aligns feature correspondences across views. Training-free and trained paths exist. The paper's Table 4 reports 15.27 GB baseline, 20.86 GB training-free extension, 20.88 GB trained extension in its configuration. Table 1 improves image/consistency metrics, but its 3DGS-based consistency evaluation is not proof of our final NeuS mesh quality. Code is Apache-2.0; the separate trained checkpoint card lacks a license declaration. This is a concrete follow-up, not a verified 16 GB default.

### S10 — Learned initial noise

Primary: [EDN repository](https://github.com/zhihao0512/EDN), [paper](https://arxiv.org/abs/2512.16219).

Source/tree verified: MV-Adapter integration changes initial latent noise with a learned predictor. The repository DOES include roughly 61 MB best.pth checkpoint entries; these were inspected as metadata only, not downloaded. No root license was found in the recursive tree. README cautions about differing seeds/preprocessing in comparisons. Consequently this is not a cleared, demonstrated mesh improvement for the primary route.

### S11 — Deployment and memory observations

Primary author/user issue evidence: [Comfy issue 45: model lifetime](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/45), [issue 18: 16 GB OOM report](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/18), [issue 107: CLIPTextModel compatibility](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/107), [Era3D issues](https://github.com/pengHTYX/Era3D/issues).

Reports are version- and configuration-dependent, not universal failures. They support isolated workers and explicit unloading rather than installing old requirements into Desktop. The apparently updated miias/ComfyUI-MVAdapter_Updated fork was compared with the author's pin through GitHub's compare API: identical, zero commits ahead; its name is not evidence of compatibility fixes. A read-only nvidia-smi query in this pass confirmed RTX 4080 SUPER, 16,376 MiB.

### S12 — Component licensing

Primary: [SDXL license](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/462165984030d82259a11f4367a4eed129e94a7b/LICENSE.md), [MV-Adapter weights](https://huggingface.co/huanngzh/mv-adapter), [BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet), [StableNormal](https://github.com/Stable-X/StableNormal), [normal weights](https://huggingface.co/Stable-X/stable-normal-v0-1), [YOSO weights](https://huggingface.co/Stable-X/yoso-normal-v0-3), [DINOv2](https://github.com/facebookresearch/dinov2), [Era3D LICENCE](https://github.com/pengHTYX/Era3D/blob/a2ce68da53c0dc4df403112c53692b9ba893a4f0/LICENCE), [Era3D author issue 2](https://github.com/pengHTYX/Era3D/issues/2), [tiny-cuda-nn license](https://github.com/NVlabs/tiny-cuda-nn/blob/master/LICENSE.txt), [nvdiffrast license](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt).

The report distinguishes output use from code/weight redistribution. Era3D is AGPL-3.0; older MIT descriptions are not current authority. StableNormal also loads DINOv2 ViT-L/14. Optional mesh-texture refinement imports nvdiffrast, whose inspected license is restrictive; it is not assumed cleared for commercial use. The selected volumetric NeuS path and its saver do not need that optional rasterized texture-refinement stage. A future package still needs an executed-dependency/license manifest, not an inference that every installed package is harmless.

### S13 — Checkpoint and community evidence

Primary checkpoint card: [Juggernaut XL v9](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9). Ordinary SDXL compatibility is plausible; no direct evidence found that this checkpoint improves this reconstruction chain. Its card restricts paid API deployment and has separate commercial-contact language. Its ordinary-image sampler/CFG recommendations are not automatically the MV-Adapter recipe.

Community leads read: [Micmumpitz workflow discussion](https://www.reddit.com/r/comfyui/comments/1jp2ljo/mvadapter_and_micmumpitz_workflow/), [Comfy discussion 1jov2nb](https://www.reddit.com/r/comfyui/comments/1jov2nb), [generation issues 1kq97dd](https://www.reddit.com/r/comfyui/comments/1kq97dd), [request for MV-Adapter to Hunyuan workflow](https://www.reddit.com/r/comfyui/comments/1qet19b/looking_for_a_mv_adapter_to_hyunwan3d_21/), [author-hosted HF image demo discussion](https://huggingface.co/spaces/VAST-AI/MV-Adapter-I2MV-SDXL/discussions/2). They supply installation/quality leads, not proof of a complete mesh route.

The Reddit-linked Civitai workflow could not be opened through the research browser; the linked JSON/ZIP was not inspected. The report does not claim it was. Targeted recent YouTube searches did not yield a verified last-month end-to-end reconstruction recipe for this chain. Older Micmumpitz material is a foundational image-workflow lead, not a newly verified mesh demonstration. No full video watching/transcription is claimed.

### S14 — Existing local Comfy components

Read-only source inspection at E:/Comfyui-installs/ComfyUI (1)/ComfyUI, detached HEAD 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18. Existing modifications to nodes_mesh_postprocess.py, nodes_save_3d.py and nodes_trellis2.py predate this research. This is working-tree source evidence, not a clean-upstream claim or fresh runtime proof.

Inspected comfy_extras/nodes_save_3d.py: pack_variable_mesh_batch, mesh_item_to_glb_bytes and SaveGLB support per-vertex colors. Inspected comfy_extras/nodes_mesh_postprocess.py: GPU mesh simplification and PEC atlas support exist, but the voxel texture baker requires Pixal-style voxel attributes, and a UV raster helper has CPU work. Therefore the report does not equate those nodes with an already-working GPU NeuS texture baker. No file in that implementation was edited.

## Access and verification limits

- CVF's web-reader route returned access errors; direct public PDF retrieval succeeded. The saved PDFs, extracted text and inspected page images supersede the failed reader result.
- Some raw GitHub/HF reader routes failed; public API/raw-file requests supplied the cited source. No credential or private account was used.
- torchmcubes' old master reference failed through the API; the repository's actual main branch was resolved and pinned. The initially empty research snapshots were replaced with the successfully fetched files.
- No package was imported or installed, no model weight downloaded, no app inspected or controlled, no generation or benchmark run in this pass. Public source text and research PDFs are the only downloads.
- Exact Windows build compatibility, peak memory, local time, geometric quality and hidden-detail obedience remain future validation questions. Source availability is not their answer.
