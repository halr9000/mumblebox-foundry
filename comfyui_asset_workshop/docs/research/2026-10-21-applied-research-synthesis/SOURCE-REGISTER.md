# Evidence register for the applied research synthesis

Research date: 2026-10-21/22 UTC. The files under `sources/` are read-only research snapshots, not installed dependencies. No downloaded Python, JavaScript, shell script or workflow was executed.

## Evidence levels

| Level | Meaning | What it does not establish |
|---|---|---|
| Current local source | Existing file read/hash-checked on this machine | Successful runtime, visible UI behavior or quality |
| Historical local result | Earlier saved experiment/review | A repeated current test or general reliability |
| Upstream source/graph | Exact implementation or workflow inspected at a pinned revision | That it works unchanged on Windows/16 GB |
| Author experiment/paper | The author reports a result for a specified setting | Independent reproduction or transfer to our objects |
| Card/documentation/license | Stated capability, usage contract or terms | Measured performance or full dependency clearance |
| Proposed combination | Our reasoned design based on the above | An implemented, novel, or proven system |

The report labels important limitations and avoids promoting source inspection to runtime proof.

## Reused evidence and current local truth

The complete prior [REPORT.md](../2026-10-21-mesh-first-research/REPORT.md) and [SOURCE-REGISTER.md](../2026-10-21-mesh-first-research/SOURCE-REGISTER.md) were read. That prior pass already contains pinned graphs/cards for RefControl, fal Multiple-Angles, AnyAngle, Fun Union, UltraTex, MV-Adapter, OminiControl, PixelArtistry and related methods. Reuse those pins rather than duplicating the entire prior source archive.

`sources/LOCAL-SOURCE-CHECK.json` compares ten prior source hashes with the current files. All ten were unchanged: `recipes.py`, `camera_guides.py`, `pixal_conditioning.py`, `resource_lifecycle.py`, native TRELLIS/Pixal, MoGe, model patches, mesh postprocess, QEM and remesh owners.

Working directory and Git root: `E:\Comfyui-installs\ComfyUI (1)\ComfyUI`; Git common directory `.git`; inspected baseline detached HEAD `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`. Existing `?? comfyui-mcp/` was not modified. The custom extension/research directory is ignored in this parent repository. No branch, commit, push or pull request was created.

The local `comfy_extras/nodes_depth_anything_3.py` had SHA-256 `ADFCE28637B6904A08596AA23E22502D20089BC28FFF6BCDAABE0B3C35FB7F02`, identical to the pinned upstream file fetched in FILES-06. This says that file matches, not that the whole installed Comfy checkout matches upstream or that model weights are installed.

Historical toy-camera evidence: `E:\Comfy-Desktop\ComfyUI-Shared\output\AssetWorkshop\assets\64edac36da7e\drafts\658624c796d94a13\framing-review.md`. No inference was rerun. The recorded change after frame repair supports investigating preprocessing; it does not prove the resulting dimensions correct.

## What the new source inspection established

| Source | Specific inspected material | Result and limit |
|---|---|---|
| ReconViaGen | Hybrid pipeline, v0.5 app and license | Reconstruction/generation staging is real; app startup placement and inherited checkpoint terms need separate attention. Earlier memory claims cannot be relabeled a 16 GB v0.5 result. |
| Musubi | Klein/Qwen training docs, dataset config, actual Klein training forward | Multiple control-image latents enter training, with target prediction/loss. No local training run. |
| AI Toolkit | Klein model class and base FLUX2 implementation | Compatible family-specific implementation exists; not a proof of our Windows multi-reference training setup. |
| CubeSLAM | Detection readme, cuboid proposal implementation, license | Concrete geometric fitting precedent. Old ROS dependencies and category assumptions limit direct adoption. |
| ComfyColab | `worker/pixal3d/vggt_omega_adapter.py` | Confidence/depth fusion and alignment exist; canonical input labels still drive the inspected projection path. |
| UltraShape | Inference script, inference config, license/notice | Rough-mesh refinement and reduced-memory options exist; startup can still allocate all principal modules. |
| Hahihula UltraShape | Actual nodes, patch file and Hunyuan example JSON | Real Comfy integration, not merely a submodule. Example is Hunyuan-oriented and does not prove Pixal compatibility/offload. |
| Orient Anything V2 | Vision tower, application utility, README and license | Orientation/relative-angle estimates and symmetry handling; not full camera calibration. Checkpoint naming/lineage remains unresolved. |
| RecGen3D | Inference/config/license | Geometry-conditioned generation and trained adaptation; 24 GB/Linux author setup, restrictive stack. |
| PartCrafter | Inference script | Part-count reconstruction path; loads background helper and includes optional hosted helpers. Not an unconditional free/local turnkey path. |
| Img2CAD | Inference source/README | Structured CAD prediction precedent with limited domains; no general arbitrary-asset deployment claim. |
| Mix3R | README, V2 entry and pipeline | Released joint method and V1/V2 distinction; `.cuda()` path and no root license in inspected tree prevent a default-local/commercial claim. |
| 3DConsistency metrics | COLMAP README and metrics implementation | Geometry-checking precedents and learned-confidence caveats. Docker/COLMAP example is not a native Windows drop-in. |
| WorldSculpt | README/license, LoRA helper, single-image inference and scene launcher | Actual Pixal denoiser PEFT LoRA mechanism. Scene path requires transforms/masks/boxes and specific checkpoints; single-image helper is not the complete multiview path. |
| Native DA3 | Complete node source, Small/Base cards | Native joint camera/depth route and permissive variants. Resizing/camera output contract remains a runtime validation item. |
| AnyAngle Studio T8 | README, basic workflow JSON, October 9 order-comparison record | Original-first/coarse-second graph and author-reported controlled comparison. No independent local reproduction. |
| Kaolin | README/license, differentiable camera recipe, FlexiCubes implementation header/class | Current Apache library/FlexiCubes and differentiable camera mechanism. Camera recipe's loss is against a target matrix, not direct evidence of image recovery. |
| Warp | README/license | Python-authored accelerated spatial-computing framework under Apache at pin. No custom kernel benchmark. |
| nvdiffrast | License plus official documentation | GPU differentiable rasterization with inspected noncommercial terms. Not on the blanket permissive list. |
| Streamline / DLSS | SR/RR/FG programming guides; DLSS license | Distinct renderer inputs and purposes; SDK terms separate from integration code. |
| vk_gltf_renderer | `src/dlss.hpp`, `docs/denoising.md` | Neural-rendering path requires beta NGX SDK; not a general image-to-mesh API or proof of user access. |
| Pixal3D / NAF | Current READMEs and license files; HF Pixal license | Current Pixal core MIT and NAF repository Apache. Do not project these onto every helper weight or renderer. |
| Viewpoint Tokens | README/license, Harmon config, camera MLP and SD3 trainer | Concrete camera-token learning and PEFT precedent. Released backbones differ from our selected models; config values must be read rather than trusted from comments. |

## Important primary papers and documentation

- [ReconViaGen, arXiv 2510.23306](https://arxiv.org/abs/2510.23306): reconstruction/generation hybrid. Source implementation inspected separately.
- [Orient Anything V2, arXiv 2601.05573](https://arxiv.org/abs/2601.05573): object orientation; not camera intrinsics/translation.
- [RecGen3D, arXiv 2604.01479](https://arxiv.org/html/2604.01479v1): geometry-conditioned mesh generation; distinguish author hardware/training from local feasibility.
- [UltraShape, arXiv 2512.21185](https://arxiv.org/abs/2512.21185): geometry-refinement motivation; actual inference/config inspected.
- [WorldSculpt, arXiv 2609.05416](https://arxiv.org/abs/2609.05416): calibrated-scene object reconstruction; actual LoRA/launcher code inspected.
- [Depth Anything 3, arXiv 2511.10647](https://arxiv.org/abs/2511.10647): joint depth/ray/camera method. Small/Base cards are the relevant license evidence.
- [Camera Control via Viewpoint Tokens, arXiv 2604.19954](https://arxiv.org/html/2604.19954v1): explicit camera embeddings; fixed-FOV/roll assumptions, T2I task and different backbones limit transfer claims.
- [3D consistency evaluation, arXiv 2605.18754](https://arxiv.org/html/2605.18754v1): learned geometry confidence can be misleading; actual metrics source inspected.
- [VLM 3D evaluation, arXiv 2605.20448](https://arxiv.org/html/2605.20448v1): synthetic-scene reasoning evidence, not a direct benchmark of the proposed 4B helper or all our assets.
- [NVIDIA DLSS 5 research page](https://research.nvidia.com/labs/adlr/DLSS5/): official method description. Full paper retrieval did not succeed; no full-paper-reading claim.
- [OpenCV PnP](https://docs.opencv.org/4.x/d5/d1f/calib3d_solvePnP.html): deterministic pose from known correspondences/intrinsics.
- [PyTorch3D camera optimization tutorial](https://pytorch3d.org/tutorials/camera_position_optimization_with_differentiable_rendering): actual image-loss optimization precedent; no local installation/test.
- [TensorRT quick start](https://docs.nvidia.com/deeplearning/tensorrt/latest/getting-started/quick-start-guide.html): graph optimization capabilities, not a speed claim for this workflow.
- [Replicator](https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html): synthetic-data option, not a necessary dependency.
- [HF Jobs pricing](https://huggingface.co/docs/hub/jobs-pricing): checked listed hourly rates. No paid job or credentials used.
- [Copyright Office Circular 61](https://www.copyright.gov/circs/circ61.pdf): implementation-expression versus methods background; not blanket patent/contract permission.

## Model, data and license evidence

The report links exact family terms, including Qwen 2.1 research licensing, Klein 9B output/model distinctions, FLUX 3 Kommunity, DINOv3, VGGT commercial checkpoint, and UltraShape. Treat source/weight/data/output terms separately.

Current Pixal HF license was saved at revision `b0cb2e1b794cab9aa0ac38a95d794a4d9337437f`; current GitHub license at `f7cf38429b0bd264f1995f0f8743a88b1c728b94`. Both inspected texts are MIT. Stale search hits describing a different license do not override these retrieved files.

Training data references: [Objaverse Ortho10View](https://huggingface.co/datasets/huanngzh/Objaverse-Ortho10View), [Rand6View](https://huggingface.co/datasets/huanngzh/Objaverse-Rand6View), [GObjaverse metadata/conventions](https://github.com/modelscope/richdreamer/blob/main/dataset/gobjaverse/README.md), [G-buffer TexVerse](https://huggingface.co/datasets/YiboZhang2001/G-buffer-TexVerse), [TexVerse upstream](https://github.com/yiboz2001/TexVerse). No data archives were downloaded. The proposed owned-data pilot avoids assuming all source assets have identical rights.

The Klein multiview full-fine-tuning comparison is [tennyyyin/flux2-klein-multiview-completion](https://huggingface.co/tennyyyin/flux2-klein-multiview-completion). Its large hardware/domain-specific experiment is not a benchmark of a local LoRA or arbitrary-object orbit consistency.

## Retrieval limits, negative results and corrected assumptions

- No model weights, dataset archives, executable packages or apps were installed. Small source/documentation/JSON snapshots were saved.
- The NVIDIA catalog was read from its public JSON; no `npx` installation or capability change was performed.
- Public raw access to some gated model metadata/licenses was unavailable. Publicly readable license pages were used where available; no credential or access bypass occurred. Unresolved lineage remains unresolved.
- Initial guessed default-branch paths for some repositories returned 404. Repository metadata supplied the actual default branch; successful snapshots are pinned. Failed fetches are not treated as inspected implementations.
- The actual UltraShape community implementation was found inside its repository tree; an early possibility that it was only a submodule was rejected.
- Searching for Mix3R initially surfaced unrelated results; only the author project/repository was used for technical conclusions.
- Recent YouTube/Reddit discovery informed leads, but no video was watched or fully transcribed in this pass. No completeness claim for “all workflows this month.” Technical claims were traced to primary code/cards/papers.
- DLSS 5 sample integration exists, but general SDK availability and compatibility for Brian's exact GPU were not established.
- Kaolin's present Apache FlexiCubes path differs from legacy noncommercial paths. Likewise, a VGGT commercial checkpoint does not retroactively clear all derived models.
- No current end-to-end model quality or 16 GB training superiority is claimed. The validation/follow-up documents identify those experiments explicitly.

## Retrieval manifests

`REPOSITORIES.json`, `REPOSITORIES-02.json` and `REPOSITORIES-03.json` record repository pins. `FILES-01.json` through `FILES-08.json` (including `FILES-03-DLSS.json`) and `HF-LICENSE-01.json` record exact fetched file URLs and SHA-256 values. `NVIDIA-skills-catalog.json` is discovery metadata, not an installed skill.

`SOURCE-FILES.json` at this report root inventories all saved source files and their hashes. `VERIFICATION.json` records the final documentation/provenance checks. These validate the research package, not the proposed workflow.

## Exact new source revisions

The following table is generated from the retrieval records. HF and GitHub revisions for the same named model are separate entries where applicable.

| Repository/provider | Exact revision |
|---|---|
| [AlayaLab/WorldSculpt](https://github.com/AlayaLab/WorldSculpt/tree/fac6b83282368063a34e648a07c6cff169e05152) (GitHub) | fac6b83282368063a34e648a07c6cff169e05152 |
| [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI/tree/46aad33e4d4c0696582611bf450dd93742fa9090) (GitHub) | 46aad33e4d4c0696582611bf450dd93742fa9090 |
| [depth-anything/DA3-BASE](https://huggingface.co/depth-anything/DA3-BASE/tree/f4a6c9b3c95e41c82048423d3493a81ec3fa810e) (Hugging Face) | f4a6c9b3c95e41c82048423d3493a81ec3fa810e |
| [depth-anything/DA3-SMALL](https://huggingface.co/depth-anything/DA3-SMALL/tree/e08cab65ca0ec38e7826075418411ab90cab4da3) (Hugging Face) | e08cab65ca0ec38e7826075418411ab90cab4da3 |
| [DragonLord1998/ComfyColab](https://github.com/DragonLord1998/ComfyColab/tree/adc90335fc697ca2b1c806d88b5502eebf1651c7) (GitHub) | adc90335fc697ca2b1c806d88b5502eebf1651c7 |
| [GAP-LAB-CUHK-SZ/ReconViaGen](https://github.com/GAP-LAB-CUHK-SZ/ReconViaGen/tree/19a902f54edb52194bc78dbea37d60278a2cddbe) (GitHub) | 19a902f54edb52194bc78dbea37d60278a2cddbe |
| [Hahihula/comfyui-ultrashape](https://github.com/Hahihula/comfyui-ultrashape/tree/ff53274ab23e688384147e7881c88fc6ca1a2d8b) (GitHub) | ff53274ab23e688384147e7881c88fc6ca1a2d8b |
| [jsnln/mix3r](https://github.com/jsnln/mix3r/tree/8f7505c03d6a908148cb715df811027a285a2e1c) (GitHub) | 8f7505c03d6a908148cb715df811027a285a2e1c |
| [kohya-ss/musubi-tuner](https://github.com/kohya-ss/musubi-tuner/tree/f8a1b03794a49239a3539015075f5123d6c07d66) (GitHub) | f8a1b03794a49239a3539015075f5123d6c07d66 |
| [mvp18/3DConsistency-metrics](https://github.com/mvp18/3DConsistency-metrics/tree/7d58fada281723ff70ada3fd022ccbd7c8000fa9) (GitHub) | 7d58fada281723ff70ada3fd022ccbd7c8000fa9 |
| [NVIDIA-RTX/Streamline](https://github.com/NVIDIA-RTX/Streamline/tree/625db07d4bca5abc67d781c42af7e7fb0761f1b6) (GitHub) | 625db07d4bca5abc67d781c42af7e7fb0761f1b6 |
| [NVIDIA/DLSS](https://github.com/NVIDIA/DLSS/tree/9981c6350dc58c0ce21f024fd65e31e851c31689) (GitHub) | 9981c6350dc58c0ce21f024fd65e31e851c31689 |
| [NVIDIA/warp](https://github.com/NVIDIA/warp/tree/ae6bef512833f9229f66669d4b5044eaeb64656d) (GitHub) | ae6bef512833f9229f66669d4b5044eaeb64656d |
| [NVIDIAGameWorks/kaolin](https://github.com/NVIDIAGameWorks/kaolin/tree/ee8b7eca1e56b1b9fd1509fc406f8d8ccbc9240b) (GitHub) | ee8b7eca1e56b1b9fd1509fc406f8d8ccbc9240b |
| [NVlabs/nvdiffrast](https://github.com/NVlabs/nvdiffrast/tree/253ac4fcea7de5f396371124af597e6cc957bfae) (GitHub) | 253ac4fcea7de5f396371124af597e6cc957bfae |
| [nvpro-samples/vk_gltf_renderer](https://github.com/nvpro-samples/vk_gltf_renderer/tree/c1059f4ff159aac3c5c92c71575a82746e0f4b4a) (GitHub) | c1059f4ff159aac3c5c92c71575a82746e0f4b4a |
| [ostris/ai-toolkit](https://github.com/ostris/ai-toolkit/tree/b1d5ef8534c80f0e347a59a3ed2c6182af321db8) (GitHub) | b1d5ef8534c80f0e347a59a3ed2c6182af321db8 |
| [PKU-YuanGroup/UltraShape-1.0](https://github.com/PKU-YuanGroup/UltraShape-1.0/tree/5e8dcef05df101ab00ab6cd5fdd0ed0c74fbca66) (GitHub) | 5e8dcef05df101ab00ab6cd5fdd0ed0c74fbca66 |
| [qq456cvb/Img2CAD](https://github.com/qq456cvb/Img2CAD/tree/afe48afa3f66e793ac9b64d3df4aab8c3ef7f7e3) (GitHub) | afe48afa3f66e793ac9b64d3df4aab8c3ef7f7e3 |
| [Randdl/viewtoken_control](https://github.com/Randdl/viewtoken_control/tree/b4d46618255526d922cae1e8367616a7af1e6e4c) (GitHub) | b4d46618255526d922cae1e8367616a7af1e6e4c |
| [shichaoy/cube_slam](https://github.com/shichaoy/cube_slam/tree/c371989bf1448802898bc7f17e99bba4a76167e6) (GitHub) | c371989bf1448802898bc7f17e99bba4a76167e6 |
| [SpatialVision/Orient-Anything-V2](https://github.com/SpatialVision/Orient-Anything-V2/tree/73b11c9dc83e84daeb563d0c766831f2c66b0a18) (GitHub) | 73b11c9dc83e84daeb563d0c766831f2c66b0a18 |
| [T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/tree/d5565f8413cdf0378f041b2047fc019be6183609) (GitHub) | d5565f8413cdf0378f041b2047fc019be6183609 |
| [TencentARC/Pixal3D](https://github.com/TencentARC/Pixal3D/tree/f7cf38429b0bd264f1995f0f8743a88b1c728b94) (GitHub) | f7cf38429b0bd264f1995f0f8743a88b1c728b94 |
| [TencentARC/Pixal3D](https://huggingface.co/TencentARC/Pixal3D/tree/b0cb2e1b794cab9aa0ac38a95d794a4d9337437f) (Hugging Face) | b0cb2e1b794cab9aa0ac38a95d794a4d9337437f |
| [valeoai/NAF](https://github.com/valeoai/NAF/tree/37f2dfc180f2de53d98bd601109c0da0dd6b0f43) (GitHub) | 37f2dfc180f2de53d98bd601109c0da0dd6b0f43 |
| [wgsxm/PartCrafter](https://github.com/wgsxm/PartCrafter/tree/3d773bf02fad51c7ab31a5615573fec93b287b30) (GitHub) | 3d773bf02fad51c7ab31a5615573fec93b287b30 |
| [zsh523/RecGen3D](https://github.com/zsh523/RecGen3D/tree/5a3c473b09eb75eed6e2ea4b625c4155a54d108c) (GitHub) | 5a3c473b09eb75eed6e2ea4b625c4155a54d108c |
