# SDXL single-image integration

Brian authorized complete design and implementation, GUI updates, and real first-use download/generation checks. Preserve Mumblebox's existing design and all current routes. This adds SDXL; it does not restart multiview reconstruction research.

## Models and sources

- `sdxl_base`: Stability AI SDXL Base 1.0, standalone checkpoint with integrated dual CLIP and VAE. Start at 1024 square, 30 steps, CFG 7, DPM++ 2M / Karras. No refiner is required for this first route.
- `sdxl_juggernaut`: RunDiffusion Juggernaut XL v9 / RunDiffusion Photo v2 checkpoint with baked VAE. Start at 1024 square for this asset workflow, 35 steps, CFG 5, DPM++ 2M / Karras. The publisher recommends 30–40 steps and CFG 3–7. Default negative prompt is empty.
- Multiple reference conditioning: h94 IP-Adapter Plus SDXL ViT-H and its matching CLIP ViT-H encoder, through the already-installed `ComfyUI_IPAdapter_plus` nodes. Default influence 0.8, linear, averaged embeddings. Preserve the entire reference through native `ResizeAndPadImage`; do not stretch or independently crop objects. Ten references is a bounded supported count, not a quality promise.
- Optional sample LoRA: nerijs/pixel-art-xl. Advertise as an optional first-use-download choice only for SDXL. It is not active by default. Existing local SDXL LoRAs remain selectable; architecture/tensor matching still applies.
- Pin sources to the metadata-verified revisions, sizes, and SHA-256 hashes in models.lock.json. Do not fetch weights until actual first-use validation. No model downloads from another application's installation.

Guidance reviewed: [SDXL model card](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), [SDXL license](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md), [Juggernaut XL v9 model card](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9), [IP-Adapter nodes and settings](https://github.com/cubiq/ComfyUI_IPAdapter_plus/blob/main/NODES.md), [IP-Adapter weights](https://huggingface.co/h94/IP-Adapter), [sample LoRA](https://huggingface.co/nerijs/pixel-art-xl). SDXL Base and Juggernaut were public/ungated when inspected. License help must link their actual terms and explain OpenRAIL use conditions; do not imply unrestricted use.

## Complete path

1. User chooses SDXL Base or Juggernaut, describes the asset, optionally selects sources and LoRAs. Enhancement uses SDXL-specific concise visual descriptions and category guidance. Negative prompt is a distinct editable field; it starts empty.
2. Generate checks the exact required dependency list. Missing files produce the existing explicit download/license dialog. Only Download initiates transfers. Access denial uses the repaired repository/token/retry flow. After verified installation, the user retries generation.
3. A checked checkpoint loader loads the UNet, both CLIP encoders, and VAE from this installation. SDXL LoRAs patch the UNet and CLIP when corresponding weights exist, with model and text strengths and an actual matching report. SDXL LoRAs can be declared for either supported SDXL checkpoint; unrelated architectures remain rejected.
4. Text-only generation uses an empty four-channel SDXL latent. Reference mode conditions the model through IP-Adapter, producing one image. Optional image-to-image starts from the first source's encoded image and uses an editable denoise value. Three-quarter/reference tasks use visual conditioning to permit a different composition; these views remain advisory and unmeasured.
5. Every existing image-editor entry point remains available. A masked SDXL edit uses the source image, native inpainting/noise mask, and an editable edit denoise. The existing deterministic compositing step preserves pixels outside the mask exactly. No promised instruction-following parity with Qwen/Klein.
6. User reviews one chosen image. Existing background removal, approval, one-image Pixal3D reconstruction, saved master, GPU PEC finishing, downloads, History, and immutable agent package continue unchanged. Advisory reference generation uses the selected SDXL route.

## GUI and memory

Keep current colors, typography, layout and steps. Add two model choices and SDXL-specific help, negative prompt, sampler/scheduler, reference strength, source mode, image-to-image/edit denoise, and CLIP LoRA strength. Explain each control in ordinary language and provide reset defaults. Store actual settings in History/package provenance. Never silently drop selected references or LoRAs.

Use native Comfy checkpoint/CLIP/VAE loaders and attention/offload behavior, existing extra-headroom and tiled decode, and mandatory stage cleanup. One output image per job. No parallel GPU jobs. No new persistent tensor cache. Primary hardware is 16 GB VRAM / 64 GB RAM; the existing 8 GB preset remains experimental.

## Validation and stopping

Build all wiring and GUI before inference. Add behavior tests for profiles/defaults, dependencies, settings round-trip, both LoRA branches, padded references, img2img/inpaint latents, negative conditioning, sampler selection, first-use actions, and non-SDXL regression. Validate native graphs against the running installation.

For first-use proof, verify and move only the existing selected SDXL Base checkpoint to a recoverable E: backup outside model search paths. Record exact source and backup. Juggernaut is currently absent. Do not delete unrelated files or borrow another model copy. Do not download either checkpoint from a terminal in advance.

Bound live checks to one completed generation per checkpoint via actual first-use download; one LoRA plus multiple-reference job; one source/inpaint job with byte comparison outside its mask; and at most one genuinely necessary mesh/package regression. Reuse existing evidence for unchanged mesh/export paths. Real defects permit focused repair/retest; visual quality is not a reroll criterion.

Complete only when installed functionality, both first-use checkpoint transfers and output images, proportional tests, necessary editor/reference/LoRA checks, and model release are demonstrated. Remove test hooks, leave Comfy ready for Brian, show outputs and limitations, and stop for review. Do not call an unavailable adapter or untested route working.
