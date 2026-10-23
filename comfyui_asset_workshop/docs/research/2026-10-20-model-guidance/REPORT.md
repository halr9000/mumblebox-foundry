# Mumblebox Creator — model-specific image workflow research

Research completed against sources retrieved on 20 October 2026. This is a research package for Brian's review, not an implemented change or a new image-quality test.

## What we should do

**Keep one simple user experience and give each model an explicit, appropriate workflow behind it.** The strongest opportunity is to improve the actual instructions and reference handling, while preserving the native sampling paths that already follow published examples.

The important findings are:

1. **The same wording is not appropriate everywhere.** Qwen 2.1 publishes separate rules for creating an image and editing an existing image. Klein's official skill favors focused natural-language descriptions. FLUX 3 expects a specific prompt-expansion stage. Its camera LoRA is an explicit exception: the author says to bypass that expansion.
2. **Enhance description and final generation must agree.** Our Enhance button uses a shared system prompt. Afterward, the generation path extracts a compact object description and constructs another prompt. Fixing the button alone would leave that second stage largely unchanged.
3. **Most current sampler defaults have a sound source.** Qwen 2.1's 25/1, Qwen Edit 2511's 40/4, Klein base's 20/5, Klein distilled/KV/4B's 4/1, and FLUX 3's 50/3.5 or 16/1 match the relevant native Comfy examples or their exposed settings. They were not all arbitrary numbers.
4. **Front and back remain useful anchors, but are not a mathematical identity lock.** Multi-reference support does not prove that a camera LoRA trained or demonstrated with one input behaves equally well with two. Preserve Brian's approved pair; validate that combination explicitly.
5. **Camera LoRAs remain optional.** They can improve the angle and worsen details. Some cannot express an underside at all. They must not be treated as mandatory or universally better.
6. **Subject type should affect the instructions.** A person, a creature and a mechanical object need different invariants. Those requirements should be expressed through each model's own prompt format.

These are evidence-backed reasons for a focused improvement pass. They do not establish that the revised approach will produce ten correct views every time.

## Decisions accepted during this research

- One visible experience; multiple internal workflows are welcome. No requirement to expose their wiring to the user.
- Model-specific handling applies to the exact variant, task, reference images and compatible adapters, rather than merely changing the model filename.
- Include a proposed Asset type choice: **Person or humanoid / Creature / Object**. The user can correct the choice. It must not silently rewrite the user's intended subject.
- Add nearby model-selection help labeled **“Which model should I use?”**. Recommended presentation: a short panel beside the selector, without navigating away. Explain strengths, speed/memory tradeoffs, reference/edit support and optional camera control. Include subject-specific recommendations or “most consistent angles” only where comparative evidence supports them. Keep the exact visual treatment for implementation review.
- Camera control is optional and clearly explained. Suggested wording: **“Use camera control LoRA (optional). May help the model follow the requested viewing angle. It can also change details or produce inconsistent results. You can generate angles without it. Review each image before using it for the mesh.”** Default-off is the recommendation for review, not a change made here.
- Retain the front → back → approve pair → remaining angles sequence, selected-model editing, quality controls, history and explicit image review.
- Do not remove or replace supported models without Brian's decision.

## What was actually inspected and downloaded

The extension is at `E:\Comfyui-installs\ComfyUI (1)\ComfyUI\custom_nodes\comfyui_asset_workshop`. Its containing Git checkout is detached at `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18`; the common Git directory resolves to `E:\Comfyui-installs\ComfyUI (1)\ComfyUI\.git`. The unrelated untracked `comfyui-mcp` directory was preserved.

- Read the current profiles, prompt/helper code, reference wiring, native Comfy nodes and relevant prior repair observations.
- Verified all **eight selected diffusion-model files** against their pinned SHA-256 values. [Inventory and exact revisions](inventory.json). This is file-identity proof, not a generation test or verification of every ancillary encoder.
- Downloaded official model guidance, prompt-enhancer instructions, native workflow JSON and selected author-published community workflows. [Source URLs, revisions and hashes](sources.json).
- Installed BFL's official [flux-image-best-practices skill][bfl-skill] at `C:\Users\brian_ul7h8cx\.codex\skills\flux-image-best-practices`, pinned to `8907d515b0ac270a988ec7a239add81ee13d6cba`. Its declared model scope is FLUX.1/FLUX.2; it does not replace the newer FLUX 3 Image Klein documentation. The separate FLUX 3 skills in that repository concern video and were not installed for this image task.
- **No official local Qwen 2.1/2511 prompting SKILL.md was found** in the checked Qwen model repositories or targeted official-organization searches. Qwen's actual prompt-rewriter instructions and model documentation were downloaded instead. Community Qwen skills were not relabeled or installed as official skills. Qwen's unrelated DashScope/Wanx example skill is not a substitute.
- No application or workflow implementation was edited, no model/node installed, no app restarted, and no image/mesh generated. Public demo images were inspected as research evidence only. No commit or push.

Final package checks: all 63 downloaded source files matched their recorded SHA-256 hashes; downloaded JSON parsed successfully; all eight diffusion-file inventory checks matched their pins; the nine application files in the before/after baseline were unchanged; the installed skill's entrypoint matched the pinned official source; report reference links resolved to defined source entries. These are research-integrity checks, not runtime or visual-generation passes.

Evidence language below: **Published** means a model/node author documents it; **source-verified** means the actual code or downloaded graph supports it; **demonstrated** means someone else's published result, not our reproduction; **proposed** means a recommendation requiring later validation.

## Exact variants and sampling baselines

All eight selected diffusion files are local to this Comfy installation. Model weight size is not peak VRAM consumption.

| Profile | Installed model format | Current steps / CFG | Evidence and recommendation |
|---|---|---:|---|
| Qwen Image 2.1 7B | `qwen_image_2.1_int8_convrot.safetensors` | 25 / 1 | Matches [native T2I][q21-t2i-template] and [edit][q21-edit-template] defaults. Qwen's reference examples use 40 steps; compare later, not an automatic claim that 25 is broken. |
| Qwen Image Edit 2511 | `qwen_image_edit_2511_fp8mixed.safetensors` | 40 / 4 | Matches the full non-Lightning branch of the [native workflow][q2511-template] and [model example][q2511-card]. Keep distinct from Lightning. |
| FLUX.2 Klein 9B base | `flux-2-klein-base-9b-fp8.safetensors` | 20 / 5 | Matches [Comfy's base edit workflow][kbase-template]. BFL's [Diffusers example][kbase-card] uses 50 / 4. These are different published baselines, not grounds to replace working settings blindly. |
| FLUX.2 Klein 9B distilled | `flux-2-klein-9b-fp8.safetensors` | 4 / 1 | Matches [native workflow][kdist-template] and [model card][kdist-card]. Do not assume more steps make this four-step model better. |
| FLUX.2 Klein 9B KV | `flux-2-klein-9b-kv-fp8.safetensors` | 4 / 1 | Matches [native workflow][kkv-template]. The separate [KV model][kkv-card] caches reference attention across denoising steps. It does not guarantee camera/identity consistency. |
| FLUX.2 Klein 4B distilled | `flux-2-klein-4b-fp8.safetensors` | 4 / 1 | Matches [native workflow][k4-template] and [model card][k4-card]. Uses the 4B text encoder; do not attach a 9B-only adapter by assumption. |
| FLUX 3 Image Klein base | `flux3-image-klein-base-int8-convrot.safetensors` | 50 / 3.5 | Matches the exposed [native T2I workflow][f3base-template]. BFL's [reference implementation][f3-repo] uses CFG 4. Preserve the distinction and compare only if useful. |
| FLUX 3 Image Klein distilled | `flux3-image-klein-int8-convrot.safetensors` | 16 / 1 | Matches exposed [native T2I][f3dist-template] and [edit][f3dist-edit] settings; the publisher specifies 16 steps without CFG. |

The workflow files contain subgraphs and linked widgets. Their effective exposed values were traced: reading an inactive inner widget would incorrectly suggest Qwen 2511 CFG 3 or FLUX 3 T2I 15 steps. There is also a real discrepancy in the downloaded FLUX 3 **base edit** template: its note says 50/3.5, but its unlinked sampler widget is CFG 1. That file is not evidence to force our base path to CFG 1. The publisher and exposed base T2I settings provide clearer baselines.

Qwen 2.1 Turbo, Klein 4B base, and BF16 alternatives are not additional selected profiles in the current eight-entry menu. They should not be silently conflated with the installed variants or added as an incidental research change.

## Model-specific findings

### Qwen Image 2.1

**Published:** the unified model supports text-to-image and image editing with up to ten reference images. The local native encoder offers more sockets, but that does not expand the publisher's supported claim. [Model guidance][q21-card]

**Prompt handling:** Qwen publishes two post-trained 9B prompt-enhancer checkpoints, PE-T2I and PE-I2I, with different output contracts. T2I returns a detailed final-image description plus aspect ratio. Editing takes ordered images and returns an editing instruction plus size-following information. These checkpoints and prompts are not interchangeable. [Rewriter documentation][q21-rewriter]

For edits, the official instructions emphasize changing the requested attribute while preserving identity through the image reference. They caution against redescribing untouched appearance in exhaustive detail. With multiple images, use `<image1>`, `<image2>`, etc., and give each an explicit role; with one input, the editing guide uses a natural reference to that image. A viewpoint edit should preserve pose, count and design while changing the view. [Edit instructions][q21-edit-rules]

**Recommended workflow:** use the T2I contract for text-only design, the editing contract for image-led design/back/remaining angles/corrections, and a separate raw camera grammar when its adapter is enabled. Keep both approved anchors in the ordinary multi-reference angle route. Describe only necessary visible details in the final view prompt; retain the full object specification separately.

The official native templates now include quantized PE-T2I/PE-I2I loaders and `TextGenerate`. These are relevant reusable components, not a reason to install a separate vLLM server on this Windows machine. The current Heretic helper is a different model; copying the official system prompt into it would be an adaptation requiring testing, not equivalent to the published fine-tuned enhancer. **Confidence: high on contracts; medium on the recommended adaptation; image-quality improvement unverified here.**

### Qwen Image Edit 2511

**Published/source-verified:** this is the edit-oriented 20B model, using the older Qwen2.5-VL encoder. The current native `TextEncodeQwenImageEditPlus` accepts three images and prefixes them as Picture 1/2/3. Positive and negative reference conditioning use the native timestep-zero method; the full-quality route includes shift 3.1 and CFG normalization. Our branch already follows those connections. [Model card][q2511-card], [native workflow][q2511-template]

**Recommended workflow:** require an input image; do not silently pretend it is the same text-only generator as Qwen 2.1. For remaining angles, the front and back consume two of its three native reference slots, leaving one ingredient reference. Use direct edit instructions and explicit image roles. Do not claim Qwen 2.1's specialized enhancer was trained for 2511. A model-aware general helper is a proposed alternative to validate.

For corrections, the selected angle remains the primary canvas. For a camera change, its optional fal adapter has a separate exact grammar. The adapter's author workflow uses a Lightning LoRA at four steps/CFG 1; our full 40-step path is deliberately different. Borrowing only its step count would be wrong. **Confidence: high on native routing and limits; medium on proposed prose policy; camera quality remains subject-dependent.**

### FLUX.2 Klein 9B base

**Published:** use clear descriptive prose, explicit relationships between references, and a direct statement of what changes in an edit. The official skill suggests moderate rather than exhaustive prompts for Klein; its 40–70-word advice is a writing heuristic, not a tokenizer limit. [Official Klein guidance][klein-rules], [reference guidance][bfl-references]

**Recommended workflow:** build a focused prompt around the requested object and task. Avoid sending the same long six-face description to every view. Preserve the full-capacity base sampler route and compare native 20/5 against the publisher's 50/4 example only in a controlled quality test. The official native base workflow itself demonstrates a camera-perspective change without a camera LoRA. [Base workflow][kbase-template]

There is no separately verified camera adapter in our base profile. Keep plain-text/reference generation usable. An adapter advertised for distilled Klein or a different FLUX model must not be attached just because “Klein” appears in its name. **Confidence: high on documented baseline; medium on camera reliability.**

### FLUX.2 Klein 9B distilled

Use the same documented Klein reference-language conventions, but retain its four-step, CFG-1 route. Its smaller step count is a trained property, not a reduced setting on the base model. [Model card][kdist-card]

The downloaded [Simple Prompt Batcher example][batcher-workflow] provides a concrete native 9B-distilled branch and short camera-edit instructions, alongside a 4B branch. It is an author-published example, not proof of correct geometry or our approved two-anchor sequence.

The [dx8152 consistency adapter][consistency-card] is a possible editing comparison, not an established camera controller. Its author says no trigger is required and publishes single/double-image workflows. Those graphs mix different step counts and additional adapter choices; they are not a clean justification to switch every distilled run to 16 steps or install the adapter universally. **Confidence: high on baseline, medium on reusing demonstrated structure, low on universal benefit from this optional adapter.**

### FLUX.2 Klein 9B KV

The [publisher][kkv-card] describes a distinct distilled model that computes reference attention initially and reuses it during later steps. Our recipe uses `FluxKVCache`, native reference latents and the matching model. Preserve that combination; caching is a performance feature, not a substitute for good reference roles.

The [Abocg workflow][abocg] matches the current camera recipe unusually closely: KV FP8, four steps, CFG 1, Alexali's angle LoRA at 1.3. Its interactive camera node supplies the prompt. However, the [Alexali model card][alexali] contains virtually no instructions. This is community workflow evidence, not an official BFL calibration or proof that every angle is supported. Its example uses one source image; our two-anchor variation still needs deliberate evaluation.

**Recommended workflow:** a normal two-anchor KV edit path plus an optional, separately versioned camera path. Keep its demonstrated settings; do not label all camera limits or compatibility claims “official.” **Confidence: high on graph comparison, medium on camera-route rationale, low on exact-angle guarantees.**

### FLUX.2 Klein 4B distilled

Use the 4B encoder/model combination, four steps and CFG 1. Its [official native workflow][k4-template] demonstrates one- and two-image edits. The same [community batcher example][batcher-workflow] contains a dedicated 4B camera-edit branch.

**Recommended workflow:** focused wording and the approved front/back pair; add ingredient references only within a measured practical budget. It is a useful lighter candidate for the intended 8 GB tier. The publisher's model-card figure of roughly 13 GB does not establish the requirements of this FP8/offloaded Comfy installation, and a four-billion-parameter label is not proof of an 8 GB pass. [Model card][k4-card]

No suitable camera adapter was verified for the current 4B profile in this research. The 9B camera and consistency LoRAs are not automatically compatible. Keep ordinary angle generation available. **Confidence: high on native recipe; 8 GB performance and challenging-angle consistency remain unmeasured.**

### FLUX 3 Image Klein base

The [publisher][f3-repo] explicitly says its normal T2I, edit and layout routes should use prompt expansion. It supplies separate [external-VLM system prompts][f3-pup] for those tasks, so using another helper is supported in principle. The normal edit expansion refers to ordered images naturally in its final prose; layout uses a different structured contract. Do not apply a blanket rule about reference tokens across all these modes.

**Recommended workflow:** explicit text-only, image-edit and bounded-edit expansion routes; preserve exact counts and requested changes, then pass the resulting caption into the correct native reference graph. The current custom FLUX 3 expansion is a useful starting point, but it does not cover corrections and masked edits and does not implement each published task contract.

**Camera exception:** the [angle-LoRA author][f3-camera] specifically removes the prompt upsampler and uses raw `<mva>` camera instructions on the base model at 50 steps. Our code already bypasses FLUX 3 expansion when camera control is on, but appends general side-description text and sometimes multiple reference bindings. That extended combination is not the author's short single-input demonstration. The author also reports plain-object hallucinations; this is a real limitation to explain, not something to promise away. **Confidence: high on the exception; its best settings for our approved pair remain unverified.**

### FLUX 3 Image Klein distilled

Normal T2I/edit expansion and ten-reference support also apply to distilled, but it uses 16 steps without CFG. Keep its separate native profile. [Publisher][f3-repo], [native edit workflow][f3dist-edit]

The researched FLUX 3 camera LoRA was trained on **base**, not distilled. No verified distilled camera adapter was found. Offer its ordinary image-led angle route without silently substituting base. Compare it on preservation, camera coverage and time; do not assume base is better merely because it uses more steps. **Confidence: high on supported route; comparative quality unverified.**

## Camera-control findings and optional alternatives

| Route | Published or demonstrated controls | Important limit |
|---|---|---|
| Qwen 2.1 akhaliq v2 | `<mva>`; 12 azimuth labels at 30-degree intervals; elevations 0/30/60/90; recommended v2 step-1500 checkpoint; strength 0.8–1.0. | No negative elevation in its published dictionary. It cannot honestly be advertised as a calibrated underside route. It does not use the 2511 45-degree dictionary. [Author guidance][q21-camera] |
| Qwen 2511 fal | `<sks>` followed by azimuth, elevation and distance; eight azimuths; elevations -30/0/30/60; strength 0.8–1.0. | Low-angle is not straight underneath; no 90-degree top-down in this dictionary. Example graph also contains Lightning. [Author guidance][q2511-camera] |
| Klein 9B KV Alexali | Current 1.3-strength recipe is demonstrated by Abocg with a camera-prompt node. | Sparse model documentation. One-reference example; two anchors and all controls need validation. [Workflow][abocg] |
| FLUX 3 base akhaliq | Raw `<mva>` grammar; eight azimuths, five named elevations including low-angle/top-down; prompt expansion bypassed. | Base only in the author's recipe; documented hallucinations for ordinary objects. [Author guidance][f3-camera] |

These adapter descriptions are not claims that the generated image has a measured camera pose. Neither a successful tensor load nor a label such as “right 90°” establishes that the pixels actually show that camera.

Two optional research candidates deserve later consideration without replacing current models:

- **Qwen 2.1 AnyAngle:** the author uses an original image plus a coarse render from a chosen 3D camera, then its dedicated LoRA. The published recommendation is strength 1, CFG 3 and at least 20 steps. This adds a visual camera target rather than relying only on a degree in text. A poor initial reconstruction can still impose wrong anatomy or layout. [LoRA author][anyangle]
- **A concrete implementation exists:** [T8 AnyAngle Studio][t8] publishes native Qwen examples, reference ordering and validation notes. Its October 9 comparison reports better camera adherence with original image first/coarse guide second, even after correctly swapping text tags in the reversed case. I inspected its published original/guide/final images: the final broadly follows the changed orientation and retains the outfit, but this single public example does not prove exact identity, dimensional fidelity or ten-view consistency. [Comparison][t8-comparison]

For comparison only, [MV-Adapter][mvadapter] offers actual joint multiview generation and geometry conditioning on SDXL/SD2.1. It is a different model route with its own resolution/memory costs, not a drop-in Klein or Qwen LoRA. Adding it would be Brian's separate decision.

## What should be kept, and what should change later

These are source-inspection findings, not new runtime test results.

| Finding | Existing ownership | Recommended action | Confidence |
|---|---|---|---|
| Eight explicit profiles, native model-specific encoders/samplers, no automatic substitution | `profiles.py`; `recipes.py:223–285` | Keep. Extend the model-specific behavior rather than rebuild the app. | High |
| Approved front/back images actually feed remaining angle recipes | `recipes.py:62–89` | Keep. Preserve exact revisions/order; test extra references and adapter modes separately. | High |
| Enhance description is generic across all profiles | `description_helper.py:65–86,245–275` | Route by selected model, task and subject; use matching enhancer guidance and output format. | High |
| Generated designs and angles pass through another shared specification-to-prompt stage | `routes.py:598–614`; `description_helper.py:278–344,382–422` | Fix the final prompt builder as well as Enhance. Protect user requirements from being lost in compact identity/side fields. | High on route; loss magnitude needs tests |
| Shared side instructions request roughly equal visible face widths even for supported Qwen 30°/60° cameras | `description_helper.py:383–408`; `profiles.py:73–104` | Remove conflicting geometry wording in the model-specific camera path. Check coordinate conventions explicitly. | High on textual conflict; effect unmeasured |
| FLUX 3 has an existing custom expansion branch | `description_helper.py:341–379` | Reuse the idea. It also runs for initial design generation through the preparation route; do not falsely claim it only runs for later angles. Split T2I vs image-led tasks, and cover corrections/masks. | High |
| Camera LoRA prompts append generic side prose and sometimes extra reference bindings | `recipes.py:169–182` | Compare the published short recipe with a deliberately defined two-anchor extension. Keep optional and disclose limits; do not silently discard the approved back. | High on source; best choice unverified |
| Single-image Qwen 2.1 bindings use `<image1>` too | `recipes.py:149–153` | Follow its edit guide's single- vs multi-image distinction in the new task formatter. | High on guidance difference; benefit unmeasured |
| Klein declares 100 references as a graph ceiling | `profiles.py:10–25` | Do not advertise 100 as a validated quality limit. The official skill documents four in its service-oriented guidance; our local graph can wire more. Establish a practical per-model/reference budget. | High |
| Selected-area editing is implemented with a noise mask and saved-image compositing | `recipes.py:155–160,212–220,266–271`; image-edit owner | Preserve the proven outside-selection behavior. Model-specific edit prompts may improve the selected result; a mask does not guarantee exact replacement counts or geometry. | High on mechanism; edit fidelity varies |
| LoRA family labels and actual tensor application are different evidence | `recipes.py:184–205`; extension-owned LoRA loader | Retain compatibility checks and hashes. Distinguish supported model family, successful loading and observed visual improvement. | High |

The prior repair notes document both useful front/back results and failures such as wrong side views, duplicate people and incorrect vent counts. They are historical local evidence, not passes awarded by this research. A completed image and a completed graph execution must remain separate from a usable reference view.

## How Enhance and subject handling should work

Keep the user-facing description editable and preserve the original. Internally, separate **what the asset is** from **how this particular model should draw this particular image**. The common object specification can be shared; the final model prompt should not be universal.

| Decision | Required behavior |
|---|---|
| Selected model and variant | Select the correct prompt rules, native connections, compatible adapters and sampling baseline. Share code only where the behavior really is the same. |
| Text-only design | Apply that model's creation guidance. Keep the complete asset visible with a useful plain background, unless Brian/user explicitly requests otherwise. |
| Image-led design or new angle | Identify the reference roles and preserve their order. Front and back describe the same subject, not two subjects to place together. Request one output view. |
| Correction or mask edit | Use the current image as the canvas, change the requested detail, preserve the camera and untargeted content. Do not reuse a whole-object design prompt automatically. |
| Optional camera adapter | Preserve its trained grammar, supported camera labels, source order and prompt-expansion exception. Do not run a general enhancer over its trigger command. |
| Person or humanoid | Preserve identity, body proportions, limb/finger counts, clothing placement and approved pose. Distinguish rotating the camera from turning the head/body. |
| Creature | Preserve anatomy, count and placement of legs/wings/horns, markings, head/tail directions and pose. Avoid forcing an animal into box-like front/back “panels.” |
| Object | Preserve silhouette, dimensions/proportions, component counts, openings, handles and side assignments. For organic objects, preserve natural form without inventing engineered panels. |

Subject rules are our product constraints, not a claim that every publisher has a separate official “dinosaur prompt.” The model-specific formatter expresses those constraints in the documented language. Hidden surfaces can be proposed during design for user approval; an auto-description must not present unseen details as observed facts.

Store the user description, approved design facts, actual final prompt, model/adapters, settings, reference order/revisions, enhancer identity and guidance revision with the job. Existing history already captures much of the generation recipe; extend it only for the missing provenance. Invalidate prepared instructions when their relevant model, adapter, subject type or reference inputs change.

The number of generated mesh views is separate from the number of reference images supplied to an image model. Ten candidate views do not mean every image generation should receive ten inputs. Keep the approved pair stable; add relevant references deliberately. Reusing a seed helps reproduce a comparison but is not an identity lock across different prompts/models.

## Memory on Brian's machine and the proposed 8 GB tier

For the RTX 4080 SUPER 16 GB and 64 GB system RAM, preserve sequential stages: description/enhancement, image encoding/generation, then mesh. Do not try to keep every large model resident simultaneously. Existing idle-queue checks, helper shutdown, Comfy offloading, optional tiled VAE and headroom controls provide a useful foundation. The headroom setting influences Comfy's memory planning; it is not a hard process-wide VRAM cap. [Local source: `description_helper.py:425–516`, `memory_policy.py`, `nodes.py:51–64`]

Qwen's published BF16 prompt-enhancer setup uses roughly 20 GB for weights before cache and therefore is not a full-GPU fit for this card. The official Comfy workflows already name quantized enhancer files; those are the relevant candidates for a later download/test. They must run as a separate stage with model memory released appropriately. Using a generic Qwen3.5/Heretic helper is not equivalent to the official post-trained checkpoint. [Qwen hardware and contracts][q21-rewriter], [native enhancer integration][q21-edit-template]

Qwen 2.1's native cache supports CPU storage, lossless default storage and lower-precision options. CPU/default is worth retaining with 64 GB RAM before spending quality on cache quantization. Klein KV reduces repeated reference processing within denoising. Neither makes unlimited reference images free. Source-verified: installed `comfy_extras/nodes_qwen.py:185–215`, `nodes_flux.py:265–302`.

For 8 GB VRAM, keep Klein 4B FP8 and FLUX 3 INT8 as candidates. BFL explicitly describes an 8 GB Comfy path for FLUX 3; that is publisher evidence, not a complete Mumblebox workflow pass. Qwen 2511's selected diffusion weights alone are about 20.5 GB on disk and require substantial offloading here. Resolution, reference count, encoder state and cache influence peak memory; increasing steps mostly increases work/time rather than solving fit. [FLUX 3 memory guidance][f3-repo], [Klein 4B card][k4-card]

Start later comparisons at one output image and a controlled reference budget. Measure end-to-end peak VRAM/RAM and time on a real 8 GB GPU before advertising support. Do not infer it from an artificial reserve on the 16 GB card. NVFP4 acceleration documented for Blackwell is not a reason to change this Ada GPU's working INT8/FP8 setup.

## Proposed validation after Brian approves implementation

This is a finite comparison plan, not permission to start generating now.

1. **Verify routing mechanically:** selecting each of the eight profiles selects its native model, final prompt formatter, enhancer task and reference order. Confirm camera-off requires no camera download. Unsupported camera choices explain why without disabling ordinary generation.
2. **Check prompt preservation before expensive runs:** original design facts survive enhancement and final compilation; single vs multiple references are numbered correctly; camera triggers are untouched; edits do not request a different pose. Confirm subject/model changes invalidate prepared instructions appropriately.
3. **Use varied subjects:** an asymmetric mechanical item with distinct side details; a clothed humanoid with a fixed pose; a creature with clear anatomy/markings; an organic item with recognisable asymmetry. Include a symmetric control where a visually similar side is expected rather than automatically wrong.
4. **Bound the first comparison:** for each profile, use the same approved pair and fixed recorded seeds. Compare the existing route to the model-specific route on a quarter view, strict side view and difficult elevated/low view. Record every result, not only attractive successes. Qwen 2511's text-only case should give its clear input requirement.
5. **Camera comparison only where compatible:** compare camera-off and camera-on using the adapter's documented angle set. A one-input author baseline can help diagnose adapter behavior, but must be labeled as such; it must not silently replace the approved two-anchor production requirement. Test whether adapter strength/detail tradeoffs help across subjects.
6. **Judge usable geometry, not merely resemblance:** correct visible/hidden surfaces, one subject, constant pose and scale, matching silhouettes and component counts, no mirrored side assignment, and consistent materials. CLIP similarity alone cannot prove correct camera pose. Preserve failed results as failures and exclude them from a mesh.
7. **Run corrections and memory checks:** one recolor and one counted-detail replacement per model route; inspect the edited area and compare pixels outside the selection. Measure fit/time for the intended reference counts and sequential helper loading.
8. **Only then complete sets and compare meshes:** use the best coherent subset, with honest camera information, against the accepted baseline. Compare texture and shape fidelity rather than assuming all ten images always improve a mesh. Finish with textured export proof in the later implementation/test goal.

Stop expanding a comparison when it has answered its specific question. A supported model can remain available with a clearly stated limitation. Further research is warranted only for a named unresolved failure, not because another workflow exists.

## Remaining questions, explicitly unproven

- Which subject/model combination benefits most from two anchors versus a camera adapter's single-reference training pattern?
- Whether official quantized Qwen enhancers outperform the current helper enough to justify their memory/load cost here.
- Whether Qwen 2.1 at 40 steps improves difficult views materially over the native 25-step baseline on the installed INT8 model.
- Whether optional Klein consistency or geometry-guided AnyAngle routes improve our subjects without introducing new drift.
- Actual camera-coordinate agreement with the mesh model, not merely agreement with a text label.
- End-to-end speed, peak memory and quality on an actual 8 GB machine.

The research is complete enough to make the next implementation pass specific and bounded. It does not establish a universal best model or perfect multiview reconstruction.

## Source index

The linked repositories below are publisher/author sources. Local snapshots and exact revisions are in [sources.json](sources.json); the native Comfy templates were downloaded at `d0e41fe5423f93db5b5872cf273d7b1af8aa68bc`. Community examples were inspected as evidence, not installed or run. The author-linked YouTube tutorials were leads; this report does not claim to have watched them or reproduced their results.

[bfl-skill]: https://github.com/black-forest-labs/skills/tree/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices
[klein-rules]: https://github.com/black-forest-labs/skills/blob/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/flux2-models.md
[bfl-references]: https://github.com/black-forest-labs/skills/blob/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/multi-reference-editing.md
[q21-card]: https://huggingface.co/Qwen/Qwen-Image-2.1
[q21-rewriter]: https://github.com/QwenLM/Qwen-Image-2.1/tree/ab96caa944157ca28a4f36b695c3047549f48f98/prompt_rewrite
[q21-edit-rules]: https://github.com/QwenLM/Qwen-Image-2.1/blob/ab96caa944157ca28a4f36b695c3047549f48f98/prompt_rewrite/prompts/system_prompt_edit.txt
[q21-t2i-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_2_1_t2i.json
[q21-edit-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_2_1_image_edit.json
[q2511-card]: https://huggingface.co/Qwen/Qwen-Image-Edit-2511
[q2511-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_edit_2511.json
[kbase-card]: https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B
[kdist-card]: https://huggingface.co/black-forest-labs/FLUX.2-klein-9B
[kkv-card]: https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-kv
[k4-card]: https://huggingface.co/black-forest-labs/FLUX.2-klein-4B
[kbase-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_image_edit_9b_base.json
[kdist-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_image_edit_9b_distilled.json
[kkv-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_9b_kv_image_edit.json
[k4-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_image_edit_4b_distilled.json
[f3-repo]: https://github.com/black-forest-labs/flux-3-image-klein/tree/bfc8889a4497f846416f253a3972a1941ac698b9
[f3-pup]: https://github.com/black-forest-labs/flux-3-image-klein/blob/bfc8889a4497f846416f253a3972a1941ac698b9/src/flux3/pup_prompts_external_vlm.json
[f3base-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux3_klein_t2i.json
[f3dist-template]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux3_klein_distilled_t2i.json
[f3dist-edit]: https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux3_klein_distilled_image_edit.json
[q21-camera]: https://huggingface.co/akhaliq/Qwen-Image-2.1-Multiple-Angles-LoRA
[q2511-camera]: https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA
[f3-camera]: https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora
[alexali]: https://huggingface.co/Alexali/multiple-angles-flux2K
[abocg]: https://github.com/Abocg/Workflows/blob/b8a5dcdac5c4920babd419f8ae22be390187063f/klein_9b_kv_Multiangle.json
[batcher-workflow]: https://github.com/ai-joe-git/ComfyUI-Simple-Prompt-Batcher/blob/f7f14462ff06a50cac6c14b668b822f6e2640a54/FLUX2-DEV-KLEIN_4_and_9B_1_click_multiple_character_angles-v1.0.json
[consistency-card]: https://huggingface.co/dx8152/Flux2-Klein-9B-Consistency
[anyangle]: https://huggingface.co/lilylilith/QI_2.1_AnyAngle
[t8]: https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/README_EN.md
[t8-comparison]: https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/docs/validation-v164.md
[mvadapter]: https://github.com/huanngzh/MV-Adapter/tree/4277e0018232bac82bb2c103caf0893cedb711be
