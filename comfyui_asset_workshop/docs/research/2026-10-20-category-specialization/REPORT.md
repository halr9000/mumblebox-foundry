# Mumblebox: model, category and official-component research

Research date: 20 October 2026. Status: complete; research only. Source and application-preservation audit recorded at the end.

**Mesh follow-up research complete:** [Read the mesh-component and Pixal3D findings](MESH-COMPONENT-RESEARCH-REPORT.md), with the [component inventory](mesh-components.json), [source register](mesh-sources.json) and [completed research plan](MESH-COMPONENT-RESEARCH-PLAN.md). This covers background removal, native camera/render tools, the standalone app's preview/export behavior, memory and licensing. It is research for the next Comfy iteration; product implementation and Pinokio development remain separate decisions.

**Latest decision supplement:** read [Model support, licensing and rough-mesh guidance](MODEL-SUPPORT-AND-MESH-GUIDANCE.md) first. Brian retained Qwen 2.1/AnyAngle, Edit 2511, Klein 4B and Klein 9B with clear license information; FLUX 3 remains recommended for design/editing. This supersedes the earlier Qwen-only possibility below. The supplement distinguishes documented camera routes from untested extensions and records native Comfy rendering constraints. No implementation followed the research.

This report answers the approved [research plan](../../superpowers/plans/2026-10-20-model-category-adapter-research.md), with Brian's added Krea 2 investigation and requirement for local generation. It reuses the [previous model-guidance research](../2026-10-20-model-guidance/REPORT.md). The detailed findings, complete component inventory, fifty model/category records and proposed comparisons live in [evidence.json](evidence.json). Exact source URLs, revisions, retrieval dates and snapshot hashes live in [sources.json](sources.json).

## 1. What I recommend, in plain English

**Make Qwen Image 2.1 plus AnyAngle and rough 3D camera guides the first method to evaluate.** Brian's latest direction is to support Qwen alone if it solves the problem well; a large image-model menu is no longer a requirement. Keep the broader research below as evidence and fallback options, not a mandate to implement every family. Nothing has been removed or changed during this research.

The proposed sequence is: approve front and back → generate adequate coarse geometry → render the required camera views → use those guides with the approved design references → review improved images → generate the final detailed mesh. The documented AnyAngle baseline uses original image 1 and guide image 2. Our approved-back addition is a separate test, not an established guarantee. [B37](https://huggingface.co/lilylilith/QI_2.1_AnyAngle) [B59](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/workflows/AnyAngle-Studio-Qwen21.json)

There is a release constraint: Qwen 2.1's current license restricts use to research/evaluation and requires separate permission for commercial use. A successful technical comparison would not resolve that permission. The adapter's license does not replace the base model's terms. See section 9 before deciding on a public commercial game-asset workflow.

1. **Make Enhance and actual generation model-aware and task-aware.** Creating an object, rotating an approved object and changing a selected part need different instructions. The final angle-generation request must use the same care as the Enhance button.
2. **Offer five understandable asset types:** Characters, Creatures, Vehicles, Props and Environment Pieces. Use these to preserve the right facts and guide review. Research supports that practical distinction; it does not establish a different sampler or official category adapter for every selection.
3. **Keep front/back approval and evaluate geometry-guided angles next.** Use both approved images to build a coarse model only if the chosen reconstruction route supports them correctly. Start image refinement with the documented original-plus-guide ordering, then compare adding the approved back as a third reference. Do not automatically accumulate generated views.
4. **Treat AnyAngle as a named, model-specific route.** It is a community LoRA for Qwen 2.1, not a standalone app or a ControlNet. A render supplies deterministic camera placement; the generative result still needs review. Existing plain-text and other camera options need not survive into the product if the preferred route demonstrably makes them unnecessary.
5. **Evaluate the small FLUX.2 decoder and the official prompt helpers separately.** These address different problems: decoding cost versus understanding and expanding the request. Their presence does not guarantee better meshes.
6. **Evaluate Krea 2 Turbo for the starting design and optional official styles.** Krea has nine official style LoRAs. Its local angle and masked-edit routes need separate scrutiny; those capabilities must not be inferred from its attractive text-to-image results.
7. **Choose coherent mesh inputs.** Ten candidate images are a review opportunity, not a quota. An incorrect view can contradict useful evidence. Match selected images to the mesh model's actual camera and input contract.
8. **Keep generation local and permissions transparent.** No hosted inference or paid generation API is recommended. Local availability, commercial rights, redistribution rights and sufficient memory are separate questions.

The strongest next comparison is now geometry-guided Qwen, with exact task contracts, reference ordering and memory management preserved. FLUX/Krea changes below are conditional alternatives, not automatic next implementation steps. This research establishes a credible method to test, not a measured quality winner.

## 2. Scope, exact models and evidence strength

The original eight selected profiles were confirmed in the existing extension. Krea 2 Turbo and RAW are research candidates, not installed additions or new menu entries. Settings below describe the inspected selections; they are not a claim that every value is optimal.

| ID | Selected model | Exact diffusion file | File size, decimal | Current steps / Comfy CFG |
| --- | --- | --- | --- | --- |
| M01 | Qwen Image 2.1 7B | qwen_image_2.1_int8_convrot.safetensors | 7.26 GB | 25 / 1 |
| M02 | Qwen Image Edit 2511 | qwen_image_edit_2511_fp8mixed.safetensors | 20.53 GB | 40 / 4 |
| M03 | FLUX.2 Klein 9B base | flux-2-klein-base-9b-fp8.safetensors | 9.57 GB | 20 / 5 |
| M04 | FLUX.2 Klein 9B distilled | flux-2-klein-9b-fp8.safetensors | 9.43 GB | 4 / 1 |
| M05 | FLUX.2 Klein 9B KV | flux-2-klein-9b-kv-fp8.safetensors | 9.82 GB | 4 / 1 |
| M06 | FLUX.2 Klein 4B | flux-2-klein-4b-fp8.safetensors | 4.07 GB | 4 / 1 |
| M07 | FLUX 3 Image Klein base | flux3-image-klein-base-int8-convrot.safetensors | 5.81 GB | 50 / 3.5 |
| M08 | FLUX 3 Image Klein distilled | flux3-image-klein-int8-convrot.safetensors | 5.83 GB | 16 / 1 |

Base, distilled, KV and quantized variants remain distinct. Klein's current 100-reference socket ceiling is an implementation limit, not evidence that feeding 100 images is useful. Qwen 2.1 and FLUX 3 document up to ten references; Edit 2511's inspected native node has three image inputs. These limits concern one image-generation request, not the number of candidate angles or the number a mesh backend consumes. [B47](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_2_1_image_edit.json) [B49](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_edit_2511.json) [B38](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_9b_kv_image_edit.json) [B43](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux3_klein_distilled_image_edit.json)

The supporting components are also different:

| Image route | Encoder contract | VAE contract |
| --- | --- | --- |
| Qwen 2.1 | Qwen3-VL 8B, selected INT8 ConvRot conversion | Qwen 2.1 64-channel RGBA VAE |
| Edit 2511 | Qwen2.5-VL 7B, selected FP8 scaled conversion | Qwen Image VAE |
| Klein 9B variants | Qwen3 8B text encoder, FP8 mixed | FLUX.2 VAE |
| Klein 4B | Qwen3 4B text encoder, FP4 | FLUX.2 VAE |
| FLUX 3 variants | Qwen3-VL 4B, INT8 ConvRot | FLUX.2 VAE |
| Krea 2 candidate | Qwen3-VL 4B with Krea-specific hidden-state selection | Qwen Image VAE; not Qwen 2.1's VAE |

An encoder with a similar name is not interchangeable without its model-specific conditioning. Exact existing download pins and hashes are preserved in the inventory. Krea's INT8 encoder and VAE can potentially reuse byte-identical files already owned by this Comfy installation; its encoder configuration must still be Krea-specific. [KR22](https://huggingface.co/api/models/Comfy-Org/Krea-2/tree/1171f4dc7e325bf3734586942e737872506c73e1?recursive=true&expand=false) [KR25](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/text_encoders/krea2.py)

**Evidence labels:** publisher documentation states intended behavior; source inspection establishes code/configuration; author examples demonstrate particular runs; community reports identify possible failures; recommendations are reasoned proposals. None of those is a new local benchmark.

No inference, mesh generation, mechanical UI test, model installation, credential action, restart or product-code change was performed in this research pass. Earlier observed successes and failures motivated questions but were not reclassified as new proof. The eleven application-file hashes provide the preservation baseline.

The source inventory covers current public material retrieved on this date, plus pinned earlier evidence. Unknown publication dates remain unknown. Failed URLs and inaccessible surfaces are recorded, including corrected default-branch paths. A public-inventory search cannot establish that no private or future component exists.

## 3. A small, useful asset-type menu

These five categories balance familiar game-asset terminology with a manageable choice. Marketplace and engine taxonomies support the broad distinctions; the exact five-item menu is a product recommendation, not a publisher-mandated taxonomy. [S16](https://assetstore.unity.com/3d) [W01](https://www.fab.com/) [W05](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-assets-in-unreal-engine) [W06](https://dev.epicgames.com/documentation/unreal-engine/static-meshes)

| User choice | Meaning | Examples | Facts to preserve |
| --- | --- | --- | --- |
| Characters | People and humanoid characters, including human-shaped robots. | astronaut; humanoid service robot | identity; pose; limb and digit count specified by the user; outfit; equipment side and attachment |
| Creatures | Animals, monsters and non-humanoid living characters. | six-legged reptile; dinosaur; bird | requested anatomy; head and tail direction; marking placement; limb pose; appendage counts |
| Vehicles | Whole vehicles and major vehicle assemblies. | rover; spaceship; motorcycle | front and travel direction; wheel/engine/fin counts; side-specific details; openings; rigid proportions |
| Props | Individual objects used, carried or placed in a game world. | radio; chair; tool; backpack; shell; statue | silhouette; part counts; material boundaries; markings; functional openings; natural irregularities when present |
| Environment Pieces | Individual buildings, structural modules and natural pieces used to assemble a scene. | doorway; watchtower; wall segment; tree; rock formation | structural silhouette; openings; repeated element counts; roof/base treatment; connection faces if specified; branching form for vegetation |

Boundary rules keep the menu simple:

- A human-shaped robot can be a Character. A nonhuman monster should not inherit human finger or stance instructions.
- A decorative statue can be a Prop; a statue intended as a character may use Characters. The user's intention and description take priority.
- A shell is a Prop even though it is organic. A tree used to construct a level is an Environment Piece.
- A spaceship habitat module can be an Environment Piece when connection faces and rooms matter; the whole spaceship is a Vehicle.
- A backpack reference attached to a character is a design ingredient, not a second asset to generate.
- “Set piece” is too ambiguous as the catch-all menu label. “Low poly” is an aesthetic request and does not establish the resulting mesh's polygon budget.
- Buildings, vegetation and rocks share Environment Pieces in the small menu, while their internal descriptions remain distinct. Do not tell a tree to preserve panel seams.

Selecting a category should visibly explain which details receive attention. It must not silently apply a style or invent mandatory parts. If later comparisons show a category adds no useful instruction for a route, retain only the helpful review guidance.

## 4. Complete model-by-category treatment matrix

Each cell below maps to a detailed record in evidence.json, including tasks, invariants, references, component IDs, confidence and a later test. Every cell has a recommendation; none implies measured category superiority.

Codes:

- **Q:** Qwen 2.1 creation/edit contract plus the category facts.
- **E:** Edit 2511 image-led contract plus category facts; an initial image is required.
- **K:** Klein natural-language task contract plus category facts; keep the row's exact variant settings.
- **F:** FLUX 3 creation/edit/box contract plus category facts.
- **D:** Krea Turbo design-generation candidate only. Angle/edit parity is unproven.
- **R:** Krea RAW research/training candidate; not recommended as a production default.

| Exact model | Characters | Creatures | Vehicles | Props | Environment Pieces |
| --- | --- | --- | --- | --- | --- |
| M01 Qwen 2.1 | Q | Q | Q | Q | Q |
| M02 Edit 2511 | E | E | E | E | E |
| M03 Klein 9B base | K | K | K | K | K |
| M04 Klein 9B distilled | K | K | K | K | K |
| M05 Klein 9B KV | K | K | K | K | K |
| M06 Klein 4B | K | K | K | K | K |
| M07 FLUX 3 base | F | F | F | F | F |
| M08 FLUX 3 distilled | F | F | F | F | F |
| M09 Krea 2 Turbo | D | D | D | D | D |
| M10 Krea 2 RAW | R | R | R | R | R |

The repeated letters are deliberate. Research supports **different facts and task instructions**, not a category-specific checkpoint or sampler for every cell. A vehicle's wheel count and a creature's limb count differ; both can use the appropriate model's existing edit graph. Whole-image and workflow-level masked correction are different capabilities: a mask UI plus compositing does not prove native inpainting support.

Confidence is high about documented model/task distinctions and medium about useful category rules. The magnitude of category benefit, best model per category and best reference arrangement remain untested. T01–T04 below are designed to answer those questions without testing every possible combination.


## 5. Model-specific instructions, enhancement and reference handling

### The shared information, before model-specific wording

Keep three things separate: what the user requires, what approved pictures visibly establish, and what remains unknown. A backpack requested in text is a requirement even if the front conceals it. An unseen clasp invented by the helper is a proposal, not an observed fact. Auto Describe should report visible features and uncertainty; Enhance may clarify a design but must preserve its intent.

Store side-specific facts in object coordinates: “emblem on the character's left sleeve,” “exhaust on the vehicle's right rear,” “underside has three feet.” A camera's left is different from the object's left. The instruction for an angle should mention the surfaces that should be visible and preserve the rest without demanding that hidden features become visible through the object.

This fact representation can be shared. Its final wording, image numbering, length, helper and special control syntax must follow the selected model and task. Preserve the original description alongside any enhanced version.

### Qwen Image 2.1

Official PE-T2I and PE-I2I are separate fine-tuned 9B prompt-enhancement models. They are not interchangeable with a generic LLM that has been given similar system instructions. The former prepares creation prompts; the latter interprets changes in the context of supplied images. Their structured output includes a rewritten prompt and aspect-ratio information. Validate that output and retain the raw request on failure. [H46](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-T2I/resolve/f3ed7985c788ad75b3ab7223e0c4c51e2a43545b/README.md) [H53](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I/resolve/72927bc08afc99b7888ceb7d7d51a12db3700bbd/README.md) [B06](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/ab96caa944157ca28a4f36b695c3047549f48f98/prompt_rewrite/pe_core.py)

The official editing rules favor precise changes and distinguish changed from retained content. Single-image references use natural wording; multiple images use the documented numbered-image convention. Put the approved pair first and identify what each contributes. Do not append every previous view simply because the model accepts several references. [B04](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/ab96caa944157ca28a4f36b695c3047549f48f98/prompt_rewrite/prompts/system_prompt_edit.txt) [S26](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I/resolve/main/system_prompt.txt)

Illustrative project prompt, not a publisher quote: “Use <image1> as the approved front and <image2> as the approved back of the same animal. Show its left-rear three-quarter view, including the left flank and rear of the tail. Preserve the six-leg body plan and the approved markings.” Subject facts vary; the numbered references and change-focused structure follow this family's guidance. This is a test candidate, not a guaranteed angle command.

Official native RGBA and annotation capabilities deserve a small comparison for isolation/edit localization. They should not replace mask compositing when the UI promises unchanged outside pixels. Recent firsthand PE reports include both successful use and runaway or empty output: inspect parsing, reasoning modes and generation limits instead of declaring the helper universally good or bad. [H44](https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/d26bb61231c349cf6b7896fa83353113880e1ba3/README.md) [W04](https://www.reddit.com/r/comfyui/comments/1x9irmw/qwen_image_21_default_workflows_prompt_enhancer/)

### Qwen Image Edit 2511

Use image-led instructions. Its publisher describes character consistency, industrial-design and viewpoint/lighting-related improvements; some useful community-adapter effects were integrated into the model itself. This does not establish exact camera control, and a separate angle LoRA is optional. No official 2511-specific prompt-helper checkpoint was found in the inspected inventory. [H45](https://huggingface.co/Qwen/Qwen-Image-Edit-2511/resolve/6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9/README.md)

The native three-image node can accommodate the approved front, approved back and one particularly relevant detail. More visible upload slots must not silently discard references or imply the encoder used them. Keep full-quality and Lightning presets separate: a four-step camera example is not evidence that the existing forty-step profile should be replaced. [B49](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_qwen_image_edit_2511.json) [B51](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA/resolve/e3066224ab74263f4a5b6179cd1a3b0a15577e44/comfyui-workflow-multiple-angles.json)

An illustrative edit request can describe the desired view, identify the two references and specify critical unchanged details. Do not copy Qwen 2.1 PE output conventions into this older route without checking its actual node/helper contract. A category adds facts such as anatomy or rigid part counts; it does not make Edit 2511 a text-only generator.

### FLUX.2 Klein: base, distilled, KV and 4B

Use clear natural prose, an explicit operation and meaningful reference roles. A recommendation such as a roughly forty-to-seventy-word focused prompt is a heuristic, not a hard token limit. Avoid padding an angle request with a long scene description that competes with the transformation. No official Klein-specific enhancement checkpoint was found. [B17](https://raw.githubusercontent.com/black-forest-labs/skills/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/SKILL.md) [B20](https://raw.githubusercontent.com/black-forest-labs/skills/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/t2i-prompting.md) [B21](https://raw.githubusercontent.com/black-forest-labs/skills/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/i2i-prompting.md) [B22](https://raw.githubusercontent.com/black-forest-labs/skills/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/rules/multi-reference-editing.md)

Illustrative project request: “Show the same rover from its right-rear corner. Use the first image for the front design and the second for the approved rear. Keep its six wheels, cabin proportions and left-side ladder. Show the right-side charging hatch and rear towing hook.” This preserves explicit roles without pretending that a shared seed encodes identity.

Base, distilled and KV retain their own steps, guidance and conditioning. KV optimization is not a new artistic capability, and its reference caching must not be described as a persistent cache shared across unrelated jobs. The 4B route is the leading small-model candidate already present, but reliable 8 GB support still needs a real hardware test. [H09](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-fp8/resolve/902d9d510b51533e07729f19211414a3648b77d2/README.md) [H24](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-kv/resolve/a6dfb36eca3a3906eb2fd460795adfb844e5fcce/README.md) [B38](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_9b_kv_image_edit.json) [B39](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux2_klein_image_edit_4b_distilled.json)

### FLUX 3 Image Klein

BFL publishes an official 9B PUP helper and separate task contracts for creation, editing and bounding-box variants. Its documented external-VLM instructions are a different integration option from running the specialized PUP weights. Use the exact mode; do not assume one verbose enhancer instruction is equivalent. [H05](https://huggingface.co/black-forest-labs/flux-3-image-klein-pup/resolve/3f3edb52b2c55de0d49feab28598b68f7f8e4830/README.md) [B15](https://raw.githubusercontent.com/black-forest-labs/flux-3-image-klein/bfc8889a4497f846416f253a3972a1941ac698b9/src/flux3/pup_prompts.json) [B16](https://raw.githubusercontent.com/black-forest-labs/flux-3-image-klein/bfc8889a4497f846416f253a3972a1941ac698b9/src/flux3/pup_prompts_external_vlm.json) [S27](https://raw.githubusercontent.com/black-forest-labs/flux-3-image-klein/main/src/flux3/pup_prompts_external_vlm.json)

Multi-image references use the family's own ordinal wording, such as first and second image. Bounding-box tasks have their own structured location information. A user-drawn polygon is not merely a box, and a box instruction alone does not preserve every surrounding pixel. The current angle text should be evaluated against this task guidance rather than accepted because the native FLUX 3 graph is correct. [S10](https://docs.bfl.ai/flux_3/flux3_image_bounding_boxes.md) [S11](https://docs.bfl.ai/flux_3/flux3_image_layout.md) [S14](https://docs.bfl.ai/guides/prompting_editing_multi_reference.md)

For the community camera-LoRA route, the author requests raw angle syntax without PUP. Do not let Enhance rewrite away the control tokens. BFL states that base-trained FLUX 3 LoRAs can load into distilled; that establishes intended weight compatibility, not tested quality of this particular camera adapter on M08. [B35](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora/resolve/41425f3e32cc0509293e9aa8d04c0c89f9a90190/README.md) [S05](https://docs.bfl.ai/release-notes.md)

### Krea 2 Turbo and RAW

Local Krea 2 is distinct from older FLUX.1 Krea and from hosted Krea Medium/Large offerings. The publisher recommends Turbo for inference and RAW primarily for training/research. Turbo's local starting point is eight steps. Its command-line guidance value of zero and native Comfy CFG of one both mean unguided sampling. Copying the same numeric value across these implementations would be incorrect. [KH01](https://huggingface.co/krea/Krea-2-Turbo/resolve/98e0fe118d17c9e3547fbb2e25acdbae2cadf7c7/README.md) [KH02](https://huggingface.co/krea/Krea-2-Raw/resolve/6b0ece7fffb640c5e3bcbe0a7f10f66b8e60a603/README.md) [KR03](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/README.md) [KR08](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/sampling.py) [KR23](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_krea2_turbo_t2i.json)

RAW's published 52-step/guidance-3.5 command uses a different guidance equation from standard Comfy CFG. Algebraically it corresponds to CFG 4.5 without custom hooks; that observation is not a validated full RAW Comfy recipe. More steps alone do not prove better production results. [KR08](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/sampling.py) [KR35](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/samplers.py)

Krea publishes natural-language prompting guidance and an expansion system prompt for an LLM of the integrator's choice. The native Comfy template uses TextGenerate with its existing encoder. Evaluate that route before introducing another large helper. The expansion should preserve medium, explicit details and intended content; it must not embellish a single asset into an unrelated scene. A simple prompt remains valid. [KR04](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/docs/prompting.md) [KR05](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/docs/expansion.txt) [KR23](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_krea2_turbo_t2i.json) [KR34](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_krea2_turbo_t2i_int8.json)

An official Krea skills repository exists, but its hosted-service controls—moodboards, style references, sliders and API operations—are not automatically features of the local weights. The local inference repository and native templates govern what can be reproduced here. Downloaded skills were inspected as evidence, not executed as instructions. [KR17](https://raw.githubusercontent.com/krea-ai/skills/ea45cca6b347cfa175b3a83a4b9abbf072e0af3f/krea-generate/SKILL.md) [KR18](https://raw.githubusercontent.com/krea-ai/skills/ea45cca6b347cfa175b3a83a4b9abbf072e0af3f/krea-generate/references/models/krea-2.md) [KR19](https://raw.githubusercontent.com/krea-ai/skills/ea45cca6b347cfa175b3a83a4b9abbf072e0af3f/krea-generate/workflows/lora-train-and-use.md)

**Candidate decision:** Turbo is worth testing for initial-design quality and optional official styles. The current public official local release does not establish the full same-object angle/correction experience we require. It should not appear as a fully equivalent choice until those tasks pass separately.

### Enhancer lifecycle and failure handling

Changing the model, task, category, relevant reference or control adapter can invalidate a prepared prompt. Record which exact contract produced it. An “enhanced” badge must not survive a switch to an incompatible contract. Preserve seed and actual final prompt in history, and show when a later choice changes recommended defaults.

Constrain helper output to useful content; detect empty responses, truncated instructions, leaked reasoning and malformed fields. An understandable fallback is the user's original description with a clear explanation. Silently sending malformed helper output into expensive generation is unacceptable. The amount of text and failure policy should be appropriate to each helper rather than a universal 100–220-word target.

## 6. Official components: what exists and what is useful

An adapter is a broad term for a component that changes or adds model behavior. A LoRA is one particular compact weight adaptation. A VAE encodes/decodes image representations; a text/vision encoder conditions generation; a prompt helper rewrites instructions. They are different parts with different compatibility requirements.

| Component type | Practical role | Relevant example |
| --- | --- | --- |
| LoRA | Adjust learned behavior or style | Krea's official styles; community camera weights |
| Conditioning adapter | Teach use of extra inputs | A reference-image or geometry-guidance route |
| VAE / decoder | Convert pixels and latent representations | FLUX.2 small decoder |
| Text/vision encoder | Turn words/images into the features the model expects | Exact Qwen3-VL configuration per family |
| Prompt helper | Prepare a model/task-specific instruction | Qwen PE-T2I/PE-I2I, FLUX 3 PUP |
| Native feature | Capability already in the selected model/runtime | RGBA output, box prompts, KV/prefix caching |
| Workflow or skill | Instructions and wiring, not necessarily model weights | Native Comfy templates, publisher prompting guides |

### Inventory coverage and dispositions

The inventory contains **95 records**: 53 BFL/Qwen model artifacts, 22 additional supporting features/guides/services, 15 Krea model artifacts and five Krea supporting records. Conversions and alternate checkpoints are counted as artifacts, not falsely advertised as 95 useful new adapters.

| Inventory range | Coverage | Decision |
| --- | --- | --- |
| O01–O42 | All 42 public BFL HF model artifacts: FLUX 3, FLUX.2/Klein variants, decoder, FLUX.1 tools/Krea, Action and conversions | Keep exact selected variants; evaluate small decoder and PUP; exclude wrong-architecture, unrelated and hosted-only routes |
| O43–O53 | Eleven Qwen image-family artifacts including 2.1, Turbo, both PEs, Edit variants, Layered and benchmark material | Evaluate exact-task PEs; retain selected 2511/2.1 routes; other checkpoints are distinct alternatives |
| P01–P12 | Required VAEs/encoders and native conditioning/caching features | Preserve correct matching; evaluate optional features individually |
| P13–P22 | Training example, hosted tools/finetunes, SDK/API/MCP, Self-Flow and official guidance | Reuse relevant guidance; do not add hosted inference or unrelated training |
| KO01–KO15 | Two Krea 2 models, nine official styles and four other/legacy artifacts | Evaluate Turbo/styles; RAW research-only; other artifacts excluded or unresolved |
| KP01–KP05 | Expansion guidance, encoder, VAE, hosted features and unexplained rank-64 LoRA | Reuse correct local components; exclude hosted dependency; do not auto-load unexplained file |

Every artifact has its own record with source, compatibility, disposition and reason. Catalogs, collections and relevant repository/documentation surfaces were cross-checked; collection summaries were expanded because their previews omit items. BFL's ten public repositories, Qwen's sixty and Krea's twenty-three were cataloged, with relevant image/code/skill material inspected. The coverage ledger discloses mirrors/private offerings not exhaustively enumerated. [C01](https://huggingface.co/api/models?author=black-forest-labs&limit=1000&full=true) [C02](https://huggingface.co/api/models?author=Qwen&search=Image&limit=1000&full=true) [C03](https://huggingface.co/api/models?author=Qwen&limit=1000&full=true) [C09](https://huggingface.co/api/collections/black-forest-labs/flux-3-image-klein-6ace04e2205b06c61bc9cbc5) [C10](https://huggingface.co/api/collections/black-forest-labs/flux2-6925d174bb065267b255dadc) [C15](https://huggingface.co/api/collections/Qwen/qwen-image-68be4d76468f322e121dc533) [KR01](https://huggingface.co/api/models?author=krea&limit=1000&full=true) [KR15](https://api.github.com/orgs/krea-ai/repos?per_page=100) [KR20](https://huggingface.co/api/collections/krea/krea-2-loras-6a353dbb18519c78e28b8ee3)

**Negative finding, carefully scoped:** no compatible public original-lab category, style or camera LoRA collection was found for the selected BFL/Qwen profiles. Krea is an exception for styles, with nine verified official releases. No compatible official category/camera Krea 2 adapter was found in the inspected public catalog. Community components remain explicitly labeled.

BFL has official FLUX.1 Depth/Canny LoRAs and Redux, but they are not drop-ins for Klein, FLUX 3 or Qwen. Its Graphic Impressions tutorial teaches training a style LoRA; a downloadable official finished weight was not established. Self-Flow training research and FLUX Action robotics do not solve this asset-image task. [H21](https://huggingface.co/black-forest-labs/FLUX.1-Depth-dev-lora/resolve/dc70845a5f24455b6262f92d5e732bc072417539/README.md) [H23](https://huggingface.co/black-forest-labs/FLUX.1-Redux-dev/resolve/c95859fbf7703ca4d6824b4da4407d7cd0434f81/README.md) [H29](https://huggingface.co/black-forest-labs/FLUX.1-Canny-dev-lora/resolve/35c8cb10238d8391b405c300090339f9704df3f2/README.md) [S01](https://docs.bfl.ai/flux_2/flux2_klein_training_example.md) [S23](https://raw.githubusercontent.com/black-forest-labs/Self-Flow/main/README.md) [H13](https://huggingface.co/black-forest-labs/flux-3-action-base/resolve/99bc185b6ea58c496ffae14c0fce9cc29be1a045/README.md)

The BFL image skill is relevant guidance. The inspected newer FLUX 3 video skills remain video-specific. No official Qwen image SKILL.md was found in the inspected trees, but Qwen's model cards, source, official rules and examples provide substantive guidance. Absence of that filename is not absence of official instructions. [S33b](https://api.github.com/repos/black-forest-labs/skills/git/trees/8907d515b0ac270a988ec7a239add81ee13d6cba?recursive=1) [S34](https://api.github.com/repos/QwenLM/Qwen-Image-2.1/git/trees/main?recursive=1) [S35](https://api.github.com/repos/QwenLM/Qwen-Image/git/trees/main?recursive=1) [B17](https://raw.githubusercontent.com/black-forest-labs/skills/8907d515b0ac270a988ec7a239add81ee13d6cba/skills/flux-image-best-practices/SKILL.md)

### Components worth evaluating first

**FLUX.2 small decoder:** the publisher describes compatibility with open FLUX.2 models and a decode-stage speed/memory improvement. The full encoder plus reduced decoder is about 249.5 MB; decoder-only about 111.8 MB. The advertised roughly 1.4× improvements concern decoding, not the entire workflow. Native Comfy loader source can recognize the configuration, but no local comparison was run. Test fine edges and texture quality; FLUX 3 compatibility remains a separate unknown even though it uses the standard FLUX.2 VAE. [H17](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/a3efc24f613ef42d9428af62fdbd6f5fd8856c4a/README.md) [S37](https://huggingface.co/api/models/black-forest-labs/FLUX.2-small-decoder/tree/main?recursive=true) [S44](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/sd.py)

**Qwen PEs and FLUX 3 PUP:** these are genuine task helpers worth comparison, but approximately 9B-class extra models are not free in RAM or loading time. FLUX 3's current native templates select the official w4a8 helper: 6.724 GB on disk versus 9.748 GB INT8 and 18.820 GB BF16. Evaluate that smaller helper first if FLUX 3 stays in scope; those sizes are not peak VRAM measurements. [Y08](https://huggingface.co/api/models/black-forest-labs/flux-3-image-klein-comfy/tree/main/text_encoders) [B43](https://github.com/Comfy-Org/workflow_templates/blob/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_flux3_klein_distilled_image_edit.json) Evaluate faithful output and cost, keep exact license distinctions, then unload before image inference. Their checkpoints should not be replaced rhetorically with “we installed the official skill.” [S25](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-T2I/resolve/main/system_prompt.txt) [S26](https://huggingface.co/Qwen/Qwen-Image-2.1-PE-I2I/resolve/main/system_prompt.txt) [H05](https://huggingface.co/black-forest-labs/flux-3-image-klein-pup/resolve/3f3edb52b2c55de0d49feab28598b68f7f8e4830/README.md) [S38](https://huggingface.co/api/models/Qwen/Qwen-Image-2.1-PE-I2I/tree/main?recursive=true)

**Native reference/caching/annotation features:** use existing runtime facilities when the selected route supports them. Publisher-linked vLLM-Omni, SGLang, LightX2V, OpenVINO and DiffSynth are ecosystem alternatives, not a reason to migrate the working Comfy installation or label third-party weights as official adapters. [S24](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/README.md)

### Krea's local components and community editing gap

The selected native Turbo candidate file is approximately 13.14 GB FP8; its INT8 ConvRot alternative is 13.49 GB and BF16 approximately 26.28 GB. The FP8 encoder adds about 5.24 GB of stored weights. These are storage figures, not simultaneous VRAM requirements or proof of 16 GB feasibility. Krea's specific twelve-layer hidden-state conditioning matters. [KR22](https://huggingface.co/api/models/Comfy-Org/Krea-2/tree/1171f4dc7e325bf3734586942e737872506c73e1?recursive=true&expand=false) [KR25](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/text_encoders/krea2.py)

The official Comfy style-reference template uses **Ostris's community adapter**, trained with one or two style references and no trigger. Three visible input sockets do not prove three-reference quality. Its latent-reference conditioning is more than a caption, but transferring style is not proof of preserving a particular object from two anchors. [KR24](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_krea2_turbo_int8_image_style_reference.json) [KR28](https://huggingface.co/ostris/krea2_turbo_style_reference/resolve/269e1e4266b89bbabdc64a4f8cebfa0b7254078a/README.md)

Community Krea editing candidates illustrate why ordinary LoRA loading is insufficient. Conradlocke's Identity/General Edit V2 routes require custom dual-conditioning behavior; their tasks and licensing differ. The author notes camera limitations in the identity route and problems from full-strength stacking. Yijunwang2's Outpaint and AnyPaint specify different reference-conditioning, cache and mask conventions. AnyPaint preserves known latent regions but still needs source compositing for strict outside-pixel preservation. These are research candidates, not installed or official Krea features. [KR29](https://huggingface.co/conradlocke/krea2-identity-edit/resolve/f33b26291c640e8ec50b0da420bfee3c9a660daa/README.md) [KR30](https://huggingface.co/yijunwang2/krea2-outpaint/resolve/89693244a3d284d98083bd03c648e7b141298a65/README.md) [KR31](https://huggingface.co/yijunwang2/krea2-anypaint/resolve/1a9fb37a304c27523939c44fc2b770c11472451b/README.md)

The extra rank-64 Turbo LoRA file in the Comfy package lacks enough provenance/purpose in the inspected material to recommend automatic use. Two legacy Krea repositories have no README. Both gaps are recorded rather than guessed away.


## 7. Automatic choices, official styles and optional camera controls

### Automatic selection needs a verified reason

Selecting a category can automatically supply relevant invariants and review hints. It should select an adapter only if an exact-model component has a demonstrated purpose, compatible runtime, acceptable terms and later validation. This pass did not establish an official category adapter that should automatically load.

Style is an explicit user choice. A creature need not be cartoonish; an environment need not be photorealistic. Preserve deliberate LoRA strengths and explain incompatible model changes. Do not silently carry a style or camera adapter into another architecture, or turn a quality route into a Lightning route to make an example work.

### Nine official Krea styles

The public collection and individual author cards identify these nine original-lab styles. They were trained on RAW and demonstrated with Turbo, eight steps, publisher guidance zero and strength one. The quoted short strings below are trigger tokens from the cards, not proposed general prose. [KR20](https://huggingface.co/api/collections/krea/krea-2-loras-6a353dbb18519c78e28b8ee3)

| Style | Published trigger | Card |
| --- | --- | --- |
| vintagetarot | vintage tarot style | [KH04](https://huggingface.co/krea/Krea-2-LoRA-vintagetarot/resolve/5fb7c2f1d6b7a8a35aca940dbe8c5c02ba85fb3f/README.md) |
| retroanime | Purple retro anime style | [KH06](https://huggingface.co/krea/Krea-2-LoRA-retroanime/resolve/23336fcff3bac43028918a2df795fbb63fdc1ff3/README.md) |
| rainywindow | rainy window style | [KH07](https://huggingface.co/krea/Krea-2-LoRA-rainywindow/resolve/b071a8c4201655dcf175e9b5f8ab66db93525747/README.md) |
| softwatercolor | Art Deco watercolor style | [KH08](https://huggingface.co/krea/Krea-2-LoRA-softwatercolor/resolve/12ff680b14a869b0e72f225bbdb237ad244b6a94/README.md) |
| sunsetblur | ethereal motion blur style | [KH11](https://huggingface.co/krea/Krea-2-LoRA-sunsetblur/resolve/bbc39e05cb5b59f60b00d9cca027495d91f2e10a/README.md) |
| kidsdrawing | naive expressive sketch style | [KH12](https://huggingface.co/krea/Krea-2-LoRA-kidsdrawing/resolve/0103d1c5f33d5b6d1c7226c879d5debc6d136121/README.md) |
| darkbrush | monochrome ink wash style | [KH13](https://huggingface.co/krea/Krea-2-LoRA-darkbrush/resolve/af7645f3502694cfc9fd69b9c2dca113344df33d/README.md) |
| dotmatrix | Monochrome stippling style | [KH14](https://huggingface.co/krea/Krea-2-LoRA-dotmatrix/resolve/47f962a5690534f99a8341d37f10ea6322a0c34a/README.md) |
| neondrip | Textured abstract style | [KH15](https://huggingface.co/krea/Krea-2-LoRA-neondrip/resolve/27b1c13a6feb68fe9abc71dc3dbc813fe6af408c/README.md) |

Use them only when the user wants the aesthetic. Rain, motion blur, stippling and abstract brushwork can conceal edges or add texture that resembles geometry. Those styles may produce appealing concepts without improving mesh fidelity.

A concrete documentation mismatch exists: the native style-reference template's stored Darkbrush example uses different wording/strength from the canonical style card. Prefer the exact card when defining a reproducible style recipe, then test the native template; do not call this a runtime defect without running it. Several style cards also point their license metadata at an unestablished “impressionist” path. The common Krea model license was inspected separately. [KR24](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/d0e41fe5423f93db5b5872cf273d7b1af8aa68bc/templates/image_krea2_turbo_int8_image_style_reference.json) [KH13](https://huggingface.co/krea/Krea-2-LoRA-darkbrush/resolve/af7645f3502694cfc9fd69b9c2dca113344df33d/README.md) [KR09](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/docs/KREA-2-COMMUNITY-LICENSE)

### Camera route comparison

| Model route | Available investigated method | Important constraint |
| --- | --- | --- |
| Qwen 2.1 | akhaliq multiple-angles v2 | Community; 30° azimuth spacing and documented elevations 0/30/60/90; no documented underside control |
| Edit 2511 | fal Multiple Angles | Community; its own trigger and eight azimuths, elevations −30/0/30/60; example uses Lightning settings |
| Klein 9B KV | Alexali / Abocg example | Community, one-reference example; other variants and approved-pair behavior not established |
| FLUX 3 base | akhaliq angle LoRA | Community; raw camera grammar, base sampling, no PUP in the author's route |
| Other selected variants | Plain-language route; exact adapter compatibility assessed separately | Do not reuse another row's camera preset by family-name resemblance |
| Krea 2 | No original-lab camera component established | Optional style references are not calibrated viewpoints |

Sources: [B32](https://huggingface.co/akhaliq/Qwen-Image-2.1-Multiple-Angles-LoRA/resolve/175b29b6eb41307473eebc363fca8fc198216b60/README.md) [B33](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA/resolve/e3066224ab74263f4a5b6179cd1a3b0a15577e44/README.md) [B34](https://huggingface.co/Alexali/multiple-angles-flux2K/resolve/32bf2cdbebb47e7c88b929c7b0e9698ce61b2cd7/README.md) [B35](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora/resolve/41425f3e32cc0509293e9aa8d04c0c89f9a90190/README.md) [B51](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA/resolve/e3066224ab74263f4a5b6179cd1a3b0a15577e44/comfyui-workflow-multiple-angles.json) [B54](https://raw.githubusercontent.com/Abocg/Workflows/b8a5dcdac5c4920babd419f8ae22be390187063f/klein_9b_kv_Multiangle.json)

Camera help should say: “Optional. This adds a model-specific angle control that may help the viewpoint. It can also change details or miss the requested angle. Check the result before including it in the mesh.”

Preserve explicit conversion between UI azimuths and each native convention. The existing wrapper's reversal, (360 − azimuth) modulo 360, is a source-level convention to verify with asymmetric subjects. A front-right label is not evidence that the image shows that view. An input already at three-quarter angle must not be treated as a calibrated front simply because it occupies the first slot.

A recent Qwen/fal camera study found under-executed rotations in its own scene/board experiment. It suggests a useful failure mode, not a universal correction factor for all objects. Do not multiply every angle by a constant based on that one result. [S15](https://arxiv.org/html/2609.37732v1)

Geometry guidance is now the priority comparison; contact sheets remain a separate alternative. AnyAngle requires correct guide geometry and reference ordering; a wrong guide can reinforce the wrong object. The contact-sheet author's workflow uses a layout template first and assigns image roles explicitly. Another firsthand character study reports framing failures despite identity consistency. None establishes that a contact sheet is universally better than separate pictures. [B57](https://raw.githubusercontent.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/d5565f8413cdf0378f041b2047fc019be6183609/README_EN.md) [B59](https://raw.githubusercontent.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/d5565f8413cdf0378f041b2047fc019be6183609/workflows/AnyAngle-Studio-Qwen21.json) [S39](https://raw.githubusercontent.com/Pyrolistical/qwen-image-2.1-workflows/f9e4ede87c8485156e24206f2e2edcd7d2387a25/character-turnaround-sheet/process.md) [W02](https://www.reddit.com/r/StableDiffusion/comments/1wmgbx9/can_qwen_image_21_replace_multistage_turnaround/)

### Priority candidate: use rough 3D to guide Qwen's camera

The coarse model is a guide, not the final export. Its render fixes a camera viewpoint while original design images supply appearance. The AnyAngle author permits splats or polygon models, explicitly including TRELLIS/Pixal3D. Start with strength 1, at least 20 steps and CFG 3, respecting the author's original-first, guide-second input order and exact trigger. This is a separate recipe from plain Qwen 2.1 at CFG 1. [B37](https://huggingface.co/lilylilith/QI_2.1_AnyAngle)

The T8 integration records a controlled case where reversing the images weakened angle following even after swapping the text indices. It also reports reference-budget loss carrying coarse face errors into output. Its example graph uses 20 steps, CFG 3, Euler/simple; preserve source detail and verify actual encoded dimensions. The October 3 tutorial demonstrates the simpler original-plus-3D-view connection inside Comfy. These are author demonstrations, not tests on Brian's machine. [B59](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/workflows/AnyAngle-Studio-Qwen21.json) [B60](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/docs/validation-v164.md) [YT01C](https://www.youtube.com/watch?v=_Kfe7QHG1ec)

T8 also documents additional role-labeled references after original 1 and guide 2. That makes our approved-back extension technically plausible, but does not prove that it improves reconstruction across characters, creatures and objects. Keep the object pose, camera convention, projection and framing consistent across guide renders. Validate actual final-view alignment before reusing guide camera matrices for mesh conditioning. [B57](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/README_EN.md)

Do not assume the cheapest possible mesh is sufficient: missing limbs or distorted proportions may be reinforced. Stop at one bounded coarse-to-refined comparison initially rather than repeatedly feeding increasingly invented geometry through a loop. A correct render provides exact guide angles, not a promise that Qwen's result obeys them. The later test must score final meshes as well as pictures.

A separate Qwen **Consistency** LoRA is not a substitute for AnyAngle. Its author reports that keeping edits fixed can suppress wanted movement or head turns. Do not automatically load it for rotation just because its name sounds useful. [Y15](https://huggingface.co/ausboss/Qwen-Image-2.1-Consistency-LoRA/resolve/1b58c4406925d6ec5fa9abd2d080531030f7cc0d/README.md)

### Combination conflicts to preserve

| Combination | Rule |
| --- | --- |
| Style plus camera LoRA | Exact-model test required; combined success is not implied by each loading alone |
| FLUX 3 camera plus PUP | Preserve the author's raw camera syntax; do not automatically enhance it |
| Klein base versus distilled versus KV | Keep separate sampling/reference contracts and verify the exact adapter |
| Hosted Klein API LoRA limit versus local Comfy | A service's one-LoRA limit is not a local architecture limit |
| Krea style-reference plus identity/geometry expectation | Style conditioning must not be represented as guaranteed identity conditioning |
| Krea Identity/General Edit V2 stacked strongly | Author reports broken outputs; separate task routes before experimental blending |
| Masked local repair versus design change | A local fix can preserve other views; a new structural feature may invalidate them |

The managed Klein service documentation and FLUX 3 release notes are useful evidence about those specific products. They do not authorize adding a hosted dependency or prove every local adapter combination. [S45](https://docs.bfl.ai/flux_2/flux2_lora_inference.md) [S05](https://docs.bfl.ai/release-notes.md) [KR29](https://huggingface.co/conradlocke/krea2-identity-edit/resolve/f33b26291c640e8ec50b0da420bfee3c9a660daa/README.md)

## 8. The human sequence, correction loop and mesh selection

Keep the agreed sequence:

1. Upload or generate the initial design. Let the user correct it with the existing editor.
2. Establish which view it actually depicts. Generate a back using that image and intended hidden-side facts.
3. Approve the front/back pair. If the back invents contradictory equipment, correct it before using it as evidence.
4. Generate the remaining candidate angles with model-specific instructions and relevant approved references.
5. Let the user inspect, regenerate, edit or exclude each candidate.
6. Generate a mesh from the selected compatible images, then inspect and export.

Extra references should answer a concrete question: a face close-up, required emblem, backpack or a side detail. Each needs a role. Respect the exact model's capacity and measured memory cost. A failed generated image should never become authoritative simply because it was produced earlier.

There is no evidence that passing the initial seed to every view guarantees identity. Save per-view seeds for reproducibility. Use matched seeds for comparisons, and new seeds for Generate again. The images and their roles carry the object's visual identity.

Masked editing should be available on initial and angle images. Describe the requested end state and preserve enough surrounding context for a plausible repair. Keep/reject, undo, download and clear operations remain part of the user flow. Verify outside-mask equality only where the implementation actually composites source pixels; a feather band is intentionally allowed to change. Native bounding-box or latent-mask control is not the same guarantee.

If a correction changes the object's design—adding a fin, removing a backpack, moving a door—mark dependent views stale. If it merely repairs a local rendering error to match approved facts, record that distinction. Never count an old view as completed for a new design just because the image slot is nonempty.

For Pixal3D, the multiview path requires camera information matching each image's actual framing. Its example orbit is four views at 90° intervals; the first is canonical front. The custom variable-input wrapper can supply more, but socket capacity does not establish best quality. Current single-image mesh routes consume one image. Keep candidate count, image-model reference count and selected mesh-view count separate. [S29b](https://raw.githubusercontent.com/TencentARC/Pixal3D/f7cf38429b0bd264f1995f0f8743a88b1c728b94/README.md) [S42](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_trellis2.py)

User-facing mesh advice: “Choose images that show the same object consistently. You do not need all ten. Exclude views with missing parts, changed proportions or the wrong angle; regenerate them if you need that coverage.”

Game readiness still needs appropriate topology, material/UV quality, scale and potentially LODs, collisions or rigging. Print readiness needs watertightness, suitable thickness, scale and connected geometry. A successful textured GLB export is useful proof of that export, not proof of either downstream readiness. [W05](https://dev.epicgames.com/documentation/en-us/unreal-engine/skeletal-mesh-assets-in-unreal-engine) [W06](https://dev.epicgames.com/documentation/unreal-engine/static-meshes) [W07](https://extensions.blender.org/add-ons/print3d-toolbox/) [W09](https://docs.blender.org/manual/en/3.6/addons/mesh/3d_print_toolbox.html)

TripoSplat, separately checked at Brian's request, produces local Gaussian splats in PLY/SPLAT form. It is not a direct replacement for the textured polygon-mesh output sought here. It now has a concrete intermediate role to consider: rendering coarse camera guides for Qwen/AnyAngle. That does not require choosing it over our existing mesh generator or installing another Pinokio wrapper. No head-to-head quality benchmark was performed. [W13](https://github.com/VAST-AI-Research/TripoSplat)

## 9. Memory, local portability and model terms

### Stage resources deliberately

Target machine: RTX 4080 SUPER, 16 GB VRAM, 64 GB system RAM. Intended minimum: 8 GB **VRAM**. Reliable minimum system RAM has not been measured.

| Stage | Load/reuse | Release or invalidate |
| --- | --- | --- |
| Describe/enhance | Selected helper, or a proven reusable encoder route | Helper residency before heavy image inference; stale enhanced prompts |
| Generate design/angles | Exact image model, encoder, VAE, compatible selected adapters | Irrelevant adapters and changed reference caches |
| Correct a view | Reuse compatible image components and relevant context | Temporary mask/crop tensors and rejected candidate buffers |
| Make mesh | Selected mesh route and approved input files/cameras | Image model residency before mesh peaks |
| Export | Required texture/geometry buffers only | Owned temporary export buffers after save/cancel |

The inspected Comfy code already provides VRAM reservation/headroom, asynchronous offload and RAM-pressure cache controls. In that version, --lowvram explicitly has no effect with Dynamic VRAM enabled. Cache-none or disable-smart-memory may increase offloading/recomputation and reduce speed. Do not advertise a custom budget number as a hard cap or force every “memory saving” flag at once. [S32](https://raw.githubusercontent.com/Comfy-Org/ComfyUI/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy/cli_args.py)

The user control should explain the tradeoff: retaining more on the GPU can reduce transfers but leaves less room for generation; reserving more GPU memory may slow work and move pressure to RAM. “Free resources” should release this workflow's owned model/cache allocations, not terminate unrelated applications or indiscriminately purge user files.

Native KV/prefix caching may operate across denoising steps. That is not a promise that changing a prompt, reference or adapter can reuse a previous job's conditioned cache. Cache identity must include the inputs and settings that affect it. [H24](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-kv/resolve/a6dfb36eca3a3906eb2fd460795adfb844e5fcce/README.md) [S24](https://raw.githubusercontent.com/QwenLM/Qwen-Image-2.1/main/README.md)

File size is not peak VRAM. Quantization can reduce model storage without proportionately reducing activation or export peaks. Do not assume a newer low-bit format accelerates this Ada GPU. Evaluate exact kernels and quality. A 16 GB card with artificial reservations is not equivalent to testing a real 8 GB card.

Use paths relative to the target Comfy installation, pinned downloads and exact checksums. Prefer reuse of identical files already owned by that installation, while avoiding dependencies on another app's private models. Remove only owned temporary files under known paths; keep selected outputs, accepted references, history records and installed model files. Cancellation and restart need bounded recovery.

### Free local execution does not mean identical model permissions

These are summaries of the inspected terms, not a determination of the future product's legal status. A free interface and per-user downloading do not erase underlying model conditions.

| Family/component | Inspected terms and consequence |
| --- | --- |
| Qwen 2.1 and its PEs | Qwen Research License limits the granted use to noncommercial research/evaluation; commercial use needs a separate grant |
| Qwen Edit 2511 | Apache 2.0 model-card license; supporting artifacts retain their own notices |
| Klein 4B | Apache 2.0 |
| Klein 9B variants | FLUX noncommercial model terms; output-use provisions do not imply unrestricted commercial inference |
| FLUX 3 Image Klein | Kommunity terms with qualifying revenue threshold and additional conditions |
| FLUX 3 PUP / small FLUX.2 decoder | Apache 2.0; does not change the image model's separate license |
| Krea 2 and official styles | Community terms permit conditional commercial use below the stated revenue threshold; code is separately Apache 2.0 |
| Community adapters | Check exact revision and its own terms; an older permissive release does not license a restrictive successor |

Primary license/card sources: [S18](https://huggingface.co/Qwen/Qwen-Image-2.1/resolve/main/LICENSE) [H45](https://huggingface.co/Qwen/Qwen-Image-Edit-2511/resolve/6f3ccc0b56e431dc6a0c2b2039706d7d26f22cb9/README.md) [H12](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/resolve/e7b7dc27f91deacad38e78976d1f2b499d76a294/README.md) [S19b](https://huggingface.co/black-forest-labs/FLUX.2-klein-9b-kv-fp8/resolve/main/LICENSE) [S20](https://huggingface.co/black-forest-labs/flux-3-image-klein/resolve/main/LICENSE.md) [H05](https://huggingface.co/black-forest-labs/flux-3-image-klein-pup/resolve/3f3edb52b2c55de0d49feab28598b68f7f8e4830/README.md) [H17](https://huggingface.co/black-forest-labs/FLUX.2-small-decoder/resolve/a3efc24f613ef42d9428af62fdbd6f5fd8856c4a/README.md) [KR09](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/docs/KREA-2-COMMUNITY-LICENSE) [KR10](https://raw.githubusercontent.com/krea-ai/krea-2/db3984fbc6e13b34c0064990fc2d95ac64d00058/LICENSE.md)

FLUX 3's inspected threshold concerns annualized gross revenue below US$5 million, including affiliates, with further obligations. Krea's is below US$1 million over the preceding twelve months, including affiliates, with distribution/notice and other conditions. Do not present either as unrestricted Apache-style permission. Converted encoders and all bundled dependencies also need a checked licensing chain before release.

Local-only means inference on the user's machine with no paid generation API required. Download hosts, optional authentication and model access terms are separate. No terms were accepted and no weights were downloaded during this research.


## 10. Plain-English help and internal translation

Keep the familiar experience. Suggested copy below is a research deliverable, not an implemented redesign.

**Asset type help:** “Choose the kind of asset you are making. This helps preserve important details across pictures. It does not choose an art style.” Use the category definitions in section 3, with Props as the understandable fallback.

**Which model should I use?** Explain documented strengths and limits without an unsupported winner badge:

| Choice | Useful short explanation |
| --- | --- |
| Qwen 2.1 | Creation and editing with several references; has dedicated prompt helpers. Check its research-use terms. |
| Qwen Edit 2511 | Start with an image and describe changes. Useful documented identity/design editing features; three native references. |
| Klein 4B | Smaller image model and a candidate for lower-memory machines. Exact supported settings still need hardware validation. |
| Klein 9B distilled | Fast four-step route. Compare details and consistency with the other variants. |
| Klein 9B base | Separate guided route for more sampling control; slower does not guarantee better. |
| Klein 9B KV | Reference-caching variant; use its own compatible workflow. |
| FLUX 3 base / distilled | Creation and editing with separate settings; model-specific prompt preparation and layout controls. |
| Krea 2 Turbo, if adopted | Candidate for the initial concept and official artistic styles. Angle/edit support needs separate proof. |

The menu should not say “best for people” or “best for objects” until representative comparisons support those claims. A guide should identify local availability, required references, likely resource tradeoffs and license conditions without forcing beginners to read implementation details.

**Reference help:** “Add an image that shows a detail you want to preserve. Explain its job—for example, the face, backpack, emblem or material. It does not need to show the whole asset.”

**Angle review help:** “Check that the parts, proportions and markings match your approved design. Include this image only if it shows the correct side of the same object.”

**Seed help:** “Random makes a new attempt. A fixed seed helps repeat the same settings; it does not lock the object's identity across different angles.” Record the resolved seed, not merely the random sentinel.

### Translation examples

The following are proposed internal facts, not claimed official magic phrases. The selected family's task formatter then expresses them using its documented reference/prompt contract.

| User category and request | Internal emphasis | What must not be invented |
| --- | --- | --- |
| Character: astronaut with backpack | Humanoid identity, unchanged outfit, backpack attachment, sleeve side | Unrequested weapons, extra fingers, new rear equipment |
| Creature: six-legged reptile | Nonhuman anatomy, six legs, tail orientation, marking continuity | Human hands or a forced human T-pose |
| Vehicle: four-wheel rover | Rigid cabin proportions, four wheels, front/travel direction, side-specific ports | A fifth wheel or a mirrored hatch |
| Prop: curved shell | Organic silhouette, spiral direction, opening and natural irregularity | Mechanical seams or unnecessary symmetry |
| Environment Piece: doorway | Architectural opening, wall thickness intent, connection faces, repeated parts | An entire room or exact engine-ready dimensions |

For Qwen 2.1, reference roles can become its numbered-image wording. For Klein, use focused natural prose referring to the first/second reference. FLUX 3 selects its creation/edit/box preparation. Krea creation can use its faithful expansion instructions; its unproven angle route should not inherit the same promises. This is shared product meaning with model-specific expression.

## 11. Smallest justified changes to the existing implementation

**Priority update from Brian:** evaluate Qwen 2.1 + AnyAngle with coarse 3D guides first. If it meets the actual asset, memory and permission requirements, simplifying to Qwen alone is acceptable. The broader changes listed here are conditional options for the later implementation discussion; do not execute them all as a checklist of mandatory model support.

This is a change-impact map for the next discussion, not an authorized implementation plan.

| Priority | Proposed change | Existing owner | Expected benefit / principal uncertainty | Later proof |
| --- | --- | --- | --- | --- |
| 1 | Exact model/task prompt preparation for Enhance and actual generation | profiles.py, description_helper.py, routes.py | Consistent guidance reaches the model; helper benefit and memory cost need comparison | T00, T02 |
| 1 | Five categories supplying invariants and review hints | profiles.py, description_helper.py, web/creator.js, store.py | Better preservation instructions without copied graphs; magnitude untested | T01 |
| 1 | Approved reference roles, exact input limits and camera conventions | recipes.py, nodes.py, routes.py, store.py | Avoid silent omissions and false angle assumptions | T03, T04, T07 |
| 2 | Optional exact-variant camera routes and combination checks | profiles.py, recipes.py, web/creator.js | Potential angle improvement; identity may regress | T04 |
| 3, conditional | Evaluate small decoder and native memory settings | models.lock.json, recipes.py, memory_policy.py | Potentially cheaper decoding and clearer budgets; hardware/quality proof needed | T05 |
| 3, conditional | Evaluate Krea Turbo design generation and opt-in official styles | Existing profile, lock, recipe and helper owners | Additional design option; angle/edit parity remains a separate gate | T08 |
| 1 | Accurate help, provenance/history and stale-state invalidation | web/creator.js, web/image-editor.js, store.py | Prevent old images/prompts being reused as current design evidence | T00, T06 |
| 1 | Qwen 2.1 + AnyAngle with rough 3D camera guides | Existing recipe/node owners if approved later | First comparison; consider Qwen-only support if quality, memory and permissions allow | T04, T07 |

Preserve the UI and working graph ownership. Add separate recipes when inputs, conditioning or sampling actually differ; category text alone belongs in a small policy/formatting layer. Automatic loading must remain traceable and reversible. User settings and explicit overrides must not disappear under “smart” presets.

The raw description, enhanced text, exact model/helper IDs, prompt-contract version, reference roles/hashes, adapter strengths and resolved seeds should be sufficient to understand a saved job. Changes affecting output must invalidate the right dependent state. This prevents the previous stale-image failure without inventing another interface.

## 12. Bounded later comparisons, uncertainties and stopping point

The latest direction changes the order: after deterministic contract checks, run the Qwen geometry-guided comparison first. T04 is now 18 outputs across a character, creature and mechanical object, three difficult views each, comparing current reference-only generation with the documented original-plus-guide recipe. Allow up to six further outputs to isolate the extra approved-back reference. Reuse the selected images for final-mesh comparisons under T07. Other families are conditional follow-ups only if this leaves a concrete gap. No tests in this section were executed during the research.

**These tests are designed, not executed.** There is no new local quality score or mechanical proof in this report.

| Test | Maximum initial scope | What it answers |
| --- | --- | --- |
| T00 Contracts/UI | Eight current profiles; candidates only if adopted; each changed control exercised visibly | Correct variants, local routes, approval, history, clearing, cancellation, saving and errors |
| T01 Categories | 40 paired-condition outputs; up to eight confirmation outputs | Whether category clauses help without changing the underlying model-aware recipe |
| T02 Enhancement | Two prompts per helper/task; at most twelve informative image comparisons | Faithfulness, valid formatting, useful detail, correct model/task selection |
| T03 References | 24 outputs | Front alone versus approved pair versus pair plus one relevant detail |
| T04 Camera | 18 Qwen comparison outputs; up to six approved-back extension outputs | Whether rough 3D guides improve difficult angles across three asset types |
| T05 Resources/decoder | Cold/warm promoted routes; six paired decodes; real hardware tiers | Peak memory, offload behavior, quality, cancellation and 8 GB feasibility |
| T06 Masks | Twelve edits across initial and angle images | Selection behavior, intended correction, preservation, keep/reject/undo/download |
| T07 Mesh subsets | Eight supported mesh runs from two distinct subjects and reused approved views | Single/four/six/all coherent inputs, correct cameras, textured export/re-import |
| T08 Krea | Six design outputs, then six style/reference comparisons; up to twelve edits only if earlier gates justify them | Local initial-design value and separately verified optional editing |

Use varied subjects: a humanoid with asymmetric equipment, a nonhumanoid creature, a vehicle with side-specific fittings, a curved or organic prop and a structural/natural environment piece. Do not spend the entire comparison tuning one crate or beacon.

Record exact files/revisions, quantization, actual final prompt, reference order/roles/hashes, adapters, sampler/scheduler, CFG semantics, steps, seed, resolution, camera convention, time, peak GPU/RAM usage and human correction effort. Review angle accuracy, silhouette, part counts, side-specific facts, pose, crop and usable edges separately. A VLM can assist; it cannot be the sole judge.

Keep first results and failures. Permit at most two user-like corrections per rejected view in a comparison, recording them separately. Stop rerolling when the contract itself fails; diagnose it. Promote a change only if it preserves hard requirements and improves the relevant paired comparison. Agree numerical release targets during the implementation-plan review rather than inventing a success percentage here.

Remaining questions are explicit in evidence.json: category benefit; best affordable faithful helper; exact-route benefit of front/back anchors; useful camera methods; small-decoder fidelity and FLUX 3 compatibility; real 8 GB feasibility; coherent mesh subset choice; Krea reference/edit reliability; incomplete component/license provenance; and uninspected private/mirror offerings. None requires pretending a literature review is an inference test.

### Requested Pinokio detour and current decision

Brian supplied screenshots and asked which existing programs could help solve this workflow's present problems. The first feature-oriented shortlist was too broad and is superseded.

Brian's final installation choice is **hoodtronik/Pixal3D-Pinokio** and **pinokiofactory/Hunyuan3d-2-lowvram**, which he intends to install himself: direct same-model comparison and an alternative text/image/multiview pipeline. TRELLIS remains source background, not a third install recommendation. Maestro remains relevant to the upstream image-generation/reference stage. Study how each actually prepares inputs, conditions generation and handles failures; do not add a feature merely because another app has it. [PA04](https://github.com/hoodtronik/Pixal3D-Pinokio) [PA01](https://github.com/pinokiofactory/Hunyuan3d-2-lowvram) [PA02](https://raw.githubusercontent.com/deepbeepmeep/Hunyuan3D-2GP/main/README.md) [PA07](https://github.com/Deathdadev/TRELLIS.2-Pinokio)

Pixal3D's current launcher exposes low-VRAM mode, while its start source says the demo enables public Gradio sharing; local-only use should disable that before launch. The TRELLIS launcher is labeled contributor alpha and upstream lists 24 GB, so source/workflow review should precede an installation recommendation on this 16 GB machine. Hunyuan's model terms have territorial restrictions, relevant before any globally distributed integration. These are source findings, not installed behavior. [PA05](https://raw.githubusercontent.com/hoodtronik/Pixal3D-Pinokio/main/start.js) [PA06](https://raw.githubusercontent.com/hoodtronik/Pixal3D-Pinokio/main/pinokio.js) [PA17](https://raw.githubusercontent.com/microsoft/TRELLIS.2/main/README.md) [PA14](https://raw.githubusercontent.com/Tencent/Hunyuan3D-2/main/LICENSE)

Texturizer, SAM 3D Body and the two TripoSplat wrappers were inspected for the earlier question but are not current install recommendations. BRIA's listed launcher targets RMBG 1.4, a background-removal model with noncommercial free terms. No app was installed or tested during the detour. [PA03](https://raw.githubusercontent.com/cocktailpeanut/texturizer/main/README.md) [PA08](https://raw.githubusercontent.com/facebookresearch/sam-3d-body/main/README.md) [PA10](https://github.com/cocktailpeanut/triposplat.pinokio) [PA11](https://github.com/hoodtronik/TripoSplat-pinokio) [PA12](https://raw.githubusercontent.com/cocktailpeanutlabs/bria-rmbg/main/install.js) [PA13](https://huggingface.co/briaai/RMBG-1.4/raw/main/README.md)

### YouTube pass: September 20–October 20, 2026

Six relevant uploads were date-verified with public YouTube metadata. English automatic captions were downloaded and relevant passages read; this was not full video-frame inspection. Translated-caption requests initially returned HTTP 429; original-English captions worked on the bounded retry. Linked public workflow JSON and owning model instructions were inspected where available. No paid/member-only template was accessed.

| Verified upload | Creator / video | Relevant finding and limit |
| --- | --- | --- |
| September 28 | AmberNova Studio, [AI Film Creator](https://www.youtube.com/watch?v=rMR7VFXL8WY) — YT03M/C | Krea character-sheet generation precedes Qwen composition. Useful separation of design and references; film composition is not calibrated mesh evidence. |
| September 30 | Pixaroma, [Qwen 2.1 Ep36](https://www.youtube.com/watch?v=OBZDYDFay9o) — YT06M/C | Separate creation, enhancement, crop/stitch, sketch and multi-reference recipes. Creator distinguishes drawn hints from strict masks and warns that consistency adapters resist motion. The actual adapter card confirms that limitation. |
| October 3 | Tutorials View+, [Qwen AnyAngle](https://www.youtube.com/watch?v=_Kfe7QHG1ec) — YT01M/C | Rough 3D/splat view becomes Qwen's second reference beside the original. Strongest directly relevant angle-control lead; a demo is not our own cross-category validation. |
| October 11 | Stable Yogi, [H3 location sheet](https://www.youtube.com/watch?v=c-pVUJfwQcU) — YT05M/C | Krea anchor plus Klein views and explicit picture roles. Supports testing reference coverage; the published six-shot result concerns H3 rooms, not exact object rotation. Reported 96 GB timings do not establish 16 GB performance. |
| October 17 | Vantage with AI, [FLUX 3 unified workflow](https://www.youtube.com/watch?v=-8mKHVCsoBU) — YT02M/C | Model-dependent presets, reference order and boxes. Author explicitly labels base 25 steps a shortened alternative to official 50; distilled uses 16. Boxes guide, rather than strictly mask, the edit. |
| October 20 | Pixaroma, [FLUX 3 Ep39](https://www.youtube.com/watch?v=ntxxhO9H3bY) — YT04M/C | Nineteen downloadable examples include a character sheet, local crop/stitch and PUP. Three relevant JSON graphs were inspected. This proves example availability, not exact multiview geometry. |

The Vantage graph confirms its model-dependent switches and separate reference path. Pixaroma's box example uses a crop/stitch route, which must not be conflated with BFL's native bounding-box conditioning. Its PUP graph selects the same official w4a8 file found in current native templates. Saved widget defaults can be overridden by connected controls, so an implementation pass must trace links before copying settings. [Y04](https://vantagewithai.com/wp-content/uploads/2026/10/Vantage-Flux3-klein-Unified-workflow.json) [Y12](https://workflows.pixaroma.com/workflows/Ep39%20Workflows.zip) [Y13](https://workflows.pixaroma.com/workflows/Ep39%20Workflows.zip) [Y14](https://workflows.pixaroma.com/workflows/Ep39%20Workflows.zip)

A related September 29 source repository, PixelArtistry's Qwen-to-Pixal workflow, generates a four-view sheet, crops/recenters it, then uses the official mesh stages. Its author reports extra views, drifting crops and misleading three-quarter profiles, and disables prompt refinement because it softened strict profile wording. Treat its sample crop coordinates as example-specific, and its fixed-90-degree requirement as the selected conditioning contract—not a universal prohibition on other Pixal camera inputs. Its README still has a video-link placeholder, so it is recorded as source research, not a watched video. [Y07](https://api.github.com/repos/pixelartistry/PixelArtistry-Pixal3D-Multiview/commits/main) [Y09](https://github.com/pixelartistry/PixelArtistry-Pixal3D-Multiview/blob/7cbc1269705d8ba508f6e7a44ffdee44d0ab8f0c/README.md) [Y10](https://github.com/pixelartistry/PixelArtistry-Pixal3D-Multiview/blob/7cbc1269705d8ba508f6e7a44ffdee44d0ab8f0c/workflows/PixelArtistry_Qwen2.1_Turnaround_to_Pixal3D_Multiview.json)

Older January/July tutorials and Pixaroma's September 17 Pixal episode were excluded from the recent-upload count. Search-engine recency sometimes returned irrelevant or old pages; only verified upload dates qualified. This is a focused recent pass, not a claim to have watched every relevant video.

### Source index and completion audit

Read this report for decisions; use evidence.json for all findings, fifty matrix cells, ninety-five component records and finite tests; use sources.json for the complete source ledger and local snapshots. Original BFL/Qwen sources are indexed as B/C/H/S/K/W, Krea as KR/KH, the requested app detour as PA, and recent video/source checks as Y/YT. A web-read record without a saved file is not a hashed snapshot.

The public-catalog search stopped after the owning inventories, relevant exact-model guidance, native workflows and focused author failure reports stopped changing the recommendations. This is exhaustive within the declared public surfaces, not a claim to have read every web page, private repository or unpublished adapter.

The research is ready for Brian's review. The next stage is to discuss the findings and agree an implementation plan. No automatic installation, product edit, inference batch or overnight test follows this report.


Final audit: 297 unique source records; 257 saved source snapshots hash-checked; 95 official-component inventory records; 50 distinct model/category cells; 33 findings; six recent video metadata/caption pairs; all twelve report sections present. Failed fetches remain labeled as failures. All eleven application baseline hashes are unchanged. Git remains at detached HEAD 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18 with the pre-existing untracked comfyui-mcp/ preserved. No product code, models, runtime, app state or generated assets were changed. No push or commit was made.
