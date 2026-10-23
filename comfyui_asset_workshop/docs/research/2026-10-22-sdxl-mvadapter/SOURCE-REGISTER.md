# Source register and evidence limits

Research date: 2026-10-22. All retrievals in this package were read-only public-source inspection. Saved source copies are under `sources/`; they contain code, configuration, model cards, licenses, graphs and metadata, **not model weights**. The generated `sources/SOURCE-MANIFEST.json` supplies file sizes and SHA-256 hashes. Retrieval manifests provide the originating URLs. A pinned revision is reproducibility evidence, not a runtime success certificate.

## How evidence is classified

- **Owner source:** original repository, release configuration, actual graph, model card, paper or license. Establishes what is implemented or claimed.
- **Author benchmark:** published results under the author's setup. Does not establish performance on Brian's machine or our combined pipeline.
- **Firsthand issue:** useful reproduction/compatibility evidence, not a controlled quality benchmark.
- **Prior local runtime:** the existing experiment's recorded outcomes, read here and not rerun.
- **Proposal/inference:** the next integration, bridge, resource policy or test threshold. Explicitly untested.

## Pinned source repositories

| ID | Repository and inspected revision | Used for |
|---|---|---|
| S01 | [huanngzh/MV-Adapter](https://github.com/huanngzh/MV-Adapter/tree/4277e0018232bac82bb2c103caf0893cedb711be), `4277e0018232bac82bb2c103caf0893cedb711be` | Attention, image pipeline, camera conditioning, training owners/configuration, reference preprocessing and resource claims. |
| S02 | [huanngzh/ComfyUI-MVAdapter](https://github.com/huanngzh/ComfyUI-MVAdapter/tree/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4), `9d6d8afeff135d81a31f16dde5291d8b40dbb0a4` | Actual I2MV graphs, LoRA wiring, loader ownership and pinned requirements. |
| S03 | [MrForExample/ComfyUI-3D-Pack](https://github.com/MrForExample/ComfyUI-3D-Pack/tree/9e8096e50c5bcf35e1f3e34c6ae06216101f8a11), `9e8096e50c5bcf35e1f3e34c6ae06216101f8a11` | Geometry-guided/texturing graph inputs; why they do not constitute the selected first-mesh route. |
| S04 | [TencentARC/Pixal3D](https://github.com/TencentARC/Pixal3D/tree/f7cf38429b0bd264f1995f0f8743a88b1c728b94), `f7cf38429b0bd264f1995f0f8743a88b1c728b94` | Conditioning renderer, projected feature training, multiview pipeline, image features, LICENSE and NOTICE. |
| S05 | [pengHTYX/Era3D](https://github.com/pengHTYX/Era3D/tree/a2ce68da53c0dc4df403112c53692b9ba893a4f0), `a2ce68da53c0dc4df403112c53692b9ba893a4f0` | Orthographic dataset/rays, normal coordinate assumptions, NeuS config, extraction/export and stated AGPL terms. |
| S06 | [Stable-X/StableNormal](https://github.com/Stable-X/StableNormal/tree/594b934630ab3bc71f35c77d14ec7feb98480cd0), `594b934630ab3bc71f35c77d14ec7feb98480cd0` | Normal prediction components, optional masking, requirements and license. |
| S07 | [diego1401/GaussianWrapping](https://github.com/diego1401/GaussianWrapping/tree/11e3b6fb5ca6f0a54e2b5587a09693488f3655af), `11e3b6fb5ca6f0a54e2b5587a09693488f3655af` | Actual Gaussian-to-surface task, capture assumptions, dependency and usage restrictions. |
| S08 | [logicalor/comfyui_mv_adapter](https://github.com/logicalor/comfyui_mv_adapter/tree/524caf48bd136296c4cb44d804da74e28c9e3125), `524caf48bd136296c4cb44d804da74e28c9e3125` | Community memory/offload implementation; no verified current-stack solution. |
| S09 | [ostris/ai-toolkit](https://github.com/ostris/ai-toolkit/tree/14f8f95090689b585093e5aaf48bc1e2e0a67ea4), `14f8f95090689b585093e5aaf48bc1e2e0a67ea4` | Klein model classes and paired-reference conditioning; Qwen paired-edit configuration as a training lead, not a 2511 hardware guarantee. |

GitHub trees and revision responses are saved. Code and graph snapshots relevant to the conclusions are saved individually. No repositories were installed into Comfy and no external source code was executed.

## Model cards and metadata

| Artifact | Revision inspected | Purpose and caveat |
|---|---|---|
| [SDXL base 1.0](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) | `462165984030d82259a11f4367a4eed129e94a7b` | Documented image backbone; OpenRAIL++ license text saved. |
| [MV-Adapter](https://huggingface.co/huanngzh/mv-adapter) | `6de4033df6b53366f3c009d22f5ec434bb55e59f` | Separate standard/beta/geometry-conditioned weights; do not interchange their trained tasks. |
| [Juggernaut XL v9](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9) | `cf419233522daa0b9ea36c3aff98fa2cab1fb0fb` | Ordinary SDXL derivative, exact v9 checkpoint; card's paid-API condition matters. |
| [FP16-fix SDXL VAE](https://huggingface.co/madebyollin/sdxl-vae-fp16-fix) | `207b116dae70ace3637169f1ddd2434b91b3a8cd` | Author inference component; preserve base/derivative terms. |
| [BiRefNet](https://huggingface.co/ZhengPeng7/BiRefNet) | `e2bf8e4460fc8fa32bba5ea4d94b3233d367b0e4` | Explicit MIT-labeled remover; not BRIARMBG 2.0. |
| [StableNormal](https://huggingface.co/Stable-X/stable-normal-v0-1) | `4362d11c636ef42ed117dd76984c7f2d83e6abd9` | Normal predictor in the fallback family. |
| [YOSO normal component](https://huggingface.co/Stable-X/yoso-normal-v0-3) | `2202fcb69960d94b437e06c19c556a12ceeb57c0` | Supporting StableNormal component; do not count a downloaded primary model as a complete stack. |
| [Pixal3D weights](https://huggingface.co/TencentARC/Pixal3D) | `b0cb2e1b794cab9aa0ac38a95d794a4d9337437f` | Multiview pipeline metadata/config and license. Regional gate metadata is not ignored. |
| [Klein Base 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4B) | `a3b4f4849157f664bdbc776fd7453c2783562f4d` | Small local training candidate. Not interchangeable with 9B or FLUX 3. |
| [Qwen Edit 2511](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) | `6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9` | Confirms exact Apache-labeled parent of the Qwen camera LoRA. |
| [fal Qwen 2511 angles](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA) | `e3066224ab74263f4a5b6179cd1a3b0a15577e44` | Actual paired-render LoRA and Comfy JSON. Card's pose claims are author claims, not our calibration proof. |
| [FLUX 3 Klein angles](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora) | `41425f3e32cc0509293e9aa8d04c0c89f9a90190` | Recent limited-scope training precedent with explicit author failure cases; conditional BFL terms. |

HF cards are prefixed `hf--` locally to distinguish them from GitHub READMEs. The JSON APIs preserve repository identity, revision, files and card metadata. No access terms were accepted and no gated dataset or model weights were downloaded.

## Papers, official guidance and data

| ID | Primary source | What was actually used |
|---|---|---|
| P01 | [MV-Adapter arXiv 2412.03632v1](https://arxiv.org/html/2412.03632v1) | Architecture/training explanation and published reconstruction evaluation. HTML saved. The ICCV final PDF fetch was not successful; do not claim its full text was reviewed. Later released code was inspected separately. |
| P02 | [T3lescope project](https://pfnet-research.github.io/t3lescope/) and [arXiv 2610.03308v1](https://arxiv.org/html/2610.03308v1) | Exact identity, availability, posed-image cascade and resource appendix. Both HTML sources saved. Project still says code forthcoming. |
| P03 | [Gaussian Wrapping project](https://diego1401.github.io/BlobsToSpokesWebsite/) and [paper 2604.07337](https://arxiv.org/abs/2604.07337) | Identification and task context; source repository/license determine implementation disposition. |
| P04 | [BFL Klein training](https://docs.bfl.ai/flux_2/flux2_klein_training) | Official small-model training feasibility, Base versus distilled, hardware distinction; Markdown snapshot saved. |
| P05 | [BFL style training example](https://docs.bfl.ai/flux_2/flux2_klein_training_example) | A concrete style recipe, explicitly not evidence that its small style dataset teaches general camera geometry. Snapshot saved. |
| P06 | [Objaverse Ortho10View](https://huggingface.co/datasets/huanngzh/Objaverse-Ortho10View), [Rand6View](https://huggingface.co/datasets/huanngzh/Objaverse-Rand6View), [bpy-renderer](https://github.com/huanngzh/bpy-renderer) | Paired rendering-data precedent. Large archives not downloaded. Dataset metadata does not override individual asset licenses. |
| P07 | [Runpod pricing](https://www.runpod.io/pricing) | Public rates checked 2026-10-22, page dated 2026-10-08. Cost examples only; no deployment, account operation or quote. |

## License sources

- [MV-Adapter Apache license](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/LICENSE) and the exact HF model cards above.
- [SDXL license](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/462165984030d82259a11f4367a4eed129e94a7b/LICENSE.md).
- [Pixal LICENSE](https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/LICENSE) and [NOTICE](https://github.com/TencentARC/Pixal3D/blob/f7cf38429b0bd264f1995f0f8743a88b1c728b94/NOTICE).
- [DINOv3 license](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md), [NAF license](https://github.com/valeoai/NAF/blob/main/LICENSE), [TRELLIS.2 model card](https://huggingface.co/microsoft/TRELLIS.2-4B).
- [Era3D stated license](https://github.com/pengHTYX/Era3D/tree/a2ce68da53c0dc4df403112c53692b9ba893a4f0#license), [StableNormal license](https://github.com/Stable-X/StableNormal/blob/594b934630ab3bc71f35c77d14ec7feb98480cd0/LICENSE.txt).
- [nvdiffrast license](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt): read the actual use limitation, not only the title. [tiny-cuda-nn license](https://github.com/NVlabs/tiny-cuda-nn/blob/master/LICENSE.txt).
- [Gaussian Wrapping license](https://github.com/diego1401/GaussianWrapping/blob/11e3b6fb5ca6f0a54e2b5587a09693488f3655af/LICENSE.md).

Moving-branch license pages have local dated/hash snapshots; refresh the selected artifacts' exact terms before public packaging. This report does not transfer one component's permission to the entire pipeline or assert that generated asset rights settle all reference-data rights.

## Issues and discovery evidence

[ComfyUI-MVAdapter issue 107](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/107), including comments, was saved. It reports a loader failure in a modern environment. Its attached graph has setup differences, so it is not a controlled validation of the chosen recipe. [Issue 49](https://github.com/huanngzh/ComfyUI-MVAdapter/issues/49) and [MV-Adapter issue 12](https://github.com/huanngzh/MV-Adapter/issues/12) identify dependency/device pitfalls. [Pixal issue 33](https://github.com/TencentARC/Pixal3D/issues/33) was inspected; an unresolved question is not an author's confirmation of support.

Recent searches prioritized the last month. YouTube [gd6r4DvBQBw](https://www.youtube.com/watch?v=gd6r4DvBQBw) and [aLOSWFG654k](https://www.youtube.com/watch?v=aLOSWFG654k) supplied discovery metadata only; no video-watching or transcript review is claimed. Forum suggestions were used as leads and were not promoted to compatibility or quality facts without owner-source support.

## Local source and previous-runtime provenance

Repository: `E:/Comfyui-installs/ComfyUI (1)/ComfyUI`; Git common directory `.git`; detached HEAD `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`.

Relevant read-only local owners: `comfy/ldm/trellis2/model.py`, `comfy_extras/nodes_trellis2.py`, `comfy_extras/nodes_mesh_postprocess.py`, `comfy_extras/nodes_save_3d.py`, the existing experimental graph/camera/result owners, and selected Mumblebox model metadata. Prior modifications to native nodes already existed; the report uses the installed local source, not an assumption of pristine upstream behavior.

The previous experiment's `RESULTS.md` is the runtime authority for its positive controls and failed route. None of those tests was repeated during this research. The current Python/package inspection was metadata-only; it did not load Torch/CUDA models. A package's absence here says nothing about other application environments.

Observed Git status was preserved: existing modifications in `nodes_mesh_postprocess.py`, `nodes_save_3d.py`, `nodes_trellis2.py`, and existing untracked `comfyui-mcp/`. Research documents live in the existing extension's documentation tree. No commit, reset, worktree, push, app operation or implementation mutation was performed.

## Integrity and limitations

The retrieval manifests were checked against their saved file hashes. `RESEARCH-AUDIT.json` records the final document/link/JSON/coverage checks. These checks validate the research package, not a workflow. No new runtime performance, local training speed, view consistency, geometry quality or export correctness was measured.

Searches cannot prove that no unpublished/better workflow exists. The stopping rule is sufficient evidence to recommend a bounded next decision, with unresolved consequential questions explicitly assigned a finite probe.
