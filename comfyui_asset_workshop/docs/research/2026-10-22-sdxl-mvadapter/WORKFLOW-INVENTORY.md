# Audited workflow inventory

Date: 2026-10-22. Evidence: downloaded graph JSON and owning source, not installed execution. Five workflow families were shortlisted. Loader variants within one family are not counted as independent solutions. No graph was imported into Comfy during this audit.

## W1 — Author SDXL image-to-multiview baseline: select

- Repository: [huanngzh/ComfyUI-MVAdapter](https://github.com/huanngzh/ComfyUI-MVAdapter/tree/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4).
- [Diffusers graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_diffusers.json).
- [Checkpoint/LDM loader graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_ldm.json).
- Audited owners: `nodes.py`, `utils.py`, `mvadapter/utils/camera.py`, actual image-conditioned pipeline, attention processors, inference script.

**Actual path:** image loader → background removal → reference preparation → image-conditioned MV pipeline → sampler → image preview/save. Diffusers loading selects SDXL base and the FP16-fix VAE; the local-checkpoint alternative does not change the task into independent views.

**Recipe to preserve:** six 768-pixel targets; DDPM with interpolated SNR shift, scale 8; 50 steps; CFG 3; reference scale 1; release-specific negative prompt; seeded CUDA generation. Foreground reference is centered and scaled by the author's preprocessing. The JSON explicitly selects BiRefNet. The node's default may instead name BRIARMBG 2.0, so default substitution is not acceptable.

**Critical limitations:** one reference image is consumed by the wrapper, even if an image batch is supplied; this is not unlimited multi-reference conditioning. Output images do not carry a complete Mumblebox reconstruction-camera bundle. Native Comfy model release is not automatically applied to custom Diffusers pipelines. The UI view-count field is not reliable evidence of arbitrary view support; actual azimuth list and selected weights govern.

**Decision:** primary image recipe. Requires a current-stack compatibility boundary and camera-provenance bridge. Source readiness is not runtime readiness.

## W2 — Author image-conditioned style-LoRA graph: defer until core pass

[Graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_ldm_lora.json).

The reference-image path is connected. `CustomLoraModelLoader` is wired into the MV pipeline, with a sample style filename and strength. This confirms a concrete I2MV LoRA integration, not just a T2MV screenshot. The exact sample file's author/license was not established, so it is not an approved downloadable dependency.

**Decision:** at most one licensed style check after geometry success. Keep exact SDXL architecture and compare the same source, seed and cameras. Support is earned through preserved features and mesh quality. No style-training UI or checkpoint catalog.

## W3 — Author beta/view selector: not baseline

[Graph](https://github.com/huanngzh/ComfyUI-MVAdapter/blob/9d6d8afeff135d81a31f16dde5291d8b40dbb0a4/workflows/i2mv_sdxl_ldm_view_selector.json), [beta training configuration](https://github.com/huanngzh/MV-Adapter/blob/4277e0018232bac82bb2c103caf0893cedb711be/configs/view-guidance/mvadapter_i2mv_sdxl_aug_quantity.yaml).

Uses the beta adapter intended for varying view counts, including 2/3/4/6. It does not establish arbitrary elevation training or unrestricted user-designed cameras. Do not use this beta to silently recreate the old eight-/ten-view goal. First test the documented six-view release. Manual exclusion after generation remains possible, with a coverage minimum in the validation proposal.

## W4 — ComfyUI-3D-Pack geometry-guided/texturing recipes: reject for first mesh

[IG2MV graph](https://github.com/MrForExample/ComfyUI-3D-Pack/blob/9e8096e50c5bcf35e1f3e34c6ae06216101f8a11/example_workflows/MV-Adapter/MV-Adapter-ig2mv.json), [texturing graph](https://github.com/MrForExample/ComfyUI-3D-Pack/blob/9e8096e50c5bcf35e1f3e34c6ae06216101f8a11/example_workflows/MV-Adapter/MV-Adapter-Texturing.json).

These graphs consume existing geometry and render geometric controls. They demonstrate meaningful use of depth/normals/camera-conditioned imagery, but address another task. Their views and conditions are not interchangeable with ordinary image-conditioned MV-Adapter weights.

**Decision:** useful source material for future mesh texturing, not the selected first-mesh recipe. Do not reintroduce draft mesh → generated views → second mesh through these graphs. Package-level MIT metadata does not clear every bundled model, renderer or dependency.

## W5 — logicalor memory-oriented wrapper: study ownership, do not adopt wholesale

[Repository](https://github.com/logicalor/comfyui_mv_adapter/tree/524caf48bd136296c4cb44d804da74e28c9e3125), [sampler](https://github.com/logicalor/comfyui_mv_adapter/blob/524caf48bd136296c4cb44d804da74e28c9e3125/nodes/sampler.py), [pipeline](https://github.com/logicalor/comfyui_mv_adapter/blob/524caf48bd136296c4cb44d804da74e28c9e3125/mvadapter/pipelines.py).

The source includes VAE slicing, memory cleanup, and low-memory handling. It also warns about sequential CPU offload interacting with custom attention. Requirements remain old; no released example workflow JSON or complete current-stack proof was located. README licensing language is not the same as a verified standalone LICENSE file.

**Decision:** reuse the lessons about explicit ownership and attention/offload compatibility, not an unverified new dependency stack. No claim that its low-memory mode is validated on this machine.

## Reconstruction and training evidence, not extra workflow candidates

- Pixal official and local projection code: primary engine bridge must be validated, not inferred from view names.
- StableNormal plus Era3D orthographic reconstruction: the one reconstruction fallback. It needs normal-frame and export integration, not simply graph wiring.
- fal Qwen Edit 2511 angle LoRA: concrete lightweight training precedent; future comparison only. No new primary/fallback added by this finding.
- Klein paired-edit trainer and recent FLUX 3 Klein angle LoRA: targeted training feasibility evidence. Not a commitment to expand model support.
- T3lescope: release watchlist. Gaussian Wrapping: different capture problem and restricted implementation. Neither replaces the current route without new evidence and approval.

## Recent discovery and negative findings

Discovery prioritized 2026-09-22 through 2026-10-22. Queries covered MV-Adapter Comfy image-conditioned workflows, SDXL/Juggernaut compatibility, orthographic reconstruction, recent fixes, and source-linked tutorials. Older author graphs remained the most concrete recipes. A current GitHub issue supplied useful dependency evidence, not a working modern recipe. No verified new last-month complete Mumblebox-equivalent workflow was found; this is a bounded search result, not proof that none exists.

YouTube leads [gd6r4DvBQBw](https://www.youtube.com/watch?v=gd6r4DvBQBw) and [aLOSWFG654k](https://www.youtube.com/watch?v=aLOSWFG654k) were discovery descriptions/chapter metadata, not watched/transcribed videos in this run. No visual-quality claim is based on them. Downloaded author graph JSON, rather than thumbnails or popularity, was used to establish the actual recipe.

Recent discussion of texture tools and old multi-camera demonstrations was not counted as proof of camera-calibrated first-mesh generation. Search stopped when owner source plus focused discovery could not resolve the remaining runtime questions; those questions are in FOLLOW-UP.md.
