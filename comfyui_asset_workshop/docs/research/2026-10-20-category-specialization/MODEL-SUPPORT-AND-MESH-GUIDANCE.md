# Mumblebox: model shortlist, licensing and rough-mesh guidance

Research completed: 20 October 2026. Research only; no implementation or inference performed for this addendum.

This is the latest decision supplement to [REPORT.md](REPORT.md). It supersedes that report's earlier suggestion that the product might become Qwen-only. The broad inventory, category findings, prompt guidance and recent-video research remain useful evidence, rather than requirements to implement every model.

## Accepted direction

- Brian explicitly retained Qwen Image 2.1 with optional AnyAngle, Qwen Image Edit 2511, FLUX.2 Klein 4B and FLUX.2 Klein 9B.
- FLUX 3 Image Klein remains a recommended option for design and editing, following Brian's question about retaining it. Its rough-mesh angle method is not established by this research.
- Keep the experience unified while using model-specific prompts, enhancement instructions, encoders, adapters and settings underneath. Base and distilled variants are separate technical choices, even when grouped under one understandable model family.
- Background removal is an explicit shared stage in every image-to-mesh route, reusing valid alpha and preserving known-camera framing. Native Comfy support is preferred when it satisfies the contract.
- Rough-mesh angle candidates use rendered color/depth/normal/silhouette guides as supported by the selected route, approved appearance references, and model-specific text about the requested view and established visible details. Image models receive rendered images, not a raw mesh through their normal image-reference sockets.
- MoGe FOV estimation is not object-rotation measurement. A requested render camera does not certify the pose of an AI-refined image.
- The next implementation proposal is for the existing Comfy software. Pinokio and standalone application work remain deferred.
- Generation stays local. Restricted models can be offered with accurate terms and links; users obtain any permission needed for their intended use. The app's own integration and distribution obligations remain separate.
- The agreed user-facing labels are **Commercial use allowed — license details** and **Commercial use has conditions — license details**. The details must explain the actual distinction, not merely repeat a badge.
- Each model also needs a short explanation of its supported uses. Do not claim one is best for people, objects or angles without comparative evidence.

## Model roles and caveats

| Model | Proposed role | Rough-mesh guidance evidence | Licensing explanation |
| --- | --- | --- | --- |
| Qwen Image 2.1 + optional AnyAngle | Design, editing and the first direct color-render-guided angle comparison | The adapter author documents original image plus a camera render from a coarse reconstruction. This closely matches our intended method. | Commercial use has conditions. The base model's research license requires separate commercial permission; the Apache adapter does not override it. |
| Qwen Image Edit 2511 | Multi-reference editing and an alternative refinement route | A research implementation demonstrates depth-image-to-RGB conditioning. Our combined identity, front/back and depth method still needs testing. | Commercial use allowed under Apache 2.0, subject to its terms and the licenses of added components. |
| FLUX.2 Klein 4B | Smaller design/editing option; Base variant for the documented RefControl comparison | Community RefControl accepts depth plus appearance, trained on Klein Base 4B. It is a distinct recipe from AnyAngle. | Commercial use allowed under Apache 2.0. Audit the complete example graph: one bundled depth estimator has noncommercial weights. |
| FLUX.2 Klein 9B | Additional design/editing option and a separate RefControl comparison | A 9B-specific RefControl exists. Do not interchange its weights with 4B or assume all variants behave identically. | Commercial use has conditions. Local commercial operation of the weights needs BFL permission; its license separately permits commercial output use. |
| FLUX 3 Image Klein | Initial designs, multiple references, editing and box-guided placement | General reference editing is documented. No equivalent exact-model rough-mesh camera adapter was established in this pass. | Commercial use has conditions. The Kommunity license includes a qualifying-user commercial-output exception; details below. |

Sources: [AnyAngle author](https://huggingface.co/lilylilith/QI_2.1_AnyAngle), [Qwen 2.1 license](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE), [Edit 2511 model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511), [RINO depth implementation](https://github.com/yangtiming/RINO/blob/main/demo/generation_depth.py), [Klein Base 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4B), [RefControl 4B](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-4B-reference-depth-lora), [RefControl 9B](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-9B-reference-depth-lora), [Klein 9B license](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B/blob/main/LICENSE.md), [BFL licensing FAQ](https://help.bfl.ai/articles/9272590838-self-serve-dev-license-overview-pricing), [FLUX 3 model card](https://huggingface.co/black-forest-labs/flux-3-image-klein).

## What the camera methods actually require

**AnyAngle / Qwen 2.1:** the author proposes reconstructing an adequate coarse model, rendering it at the desired camera and refining that image against the original. The T8 example graph uses the original as image 1 and the guide as image 2. Its trigger wording is easy to misread; preserve the actual graph and compare ordering, rather than interpreting the indices in isolation. The author's baseline is LoRA strength 1, CFG 3 and at least 20 steps. A poor coarse mesh can propagate anatomy and silhouette errors. Adding the approved back to this baseline is our proposed extension, not author-proven behavior. [Author guidance](https://huggingface.co/lilylilith/QI_2.1_AnyAngle), [pinned T8 graph](https://github.com/T8mars/Comfyui-Qwen-Image-2.1-MultiAngle-T8/blob/d5565f8413cdf0378f041b2047fc019be6183609/workflows/AnyAngle-Studio-Qwen21.json).

**RefControl / Klein:** the documented input roles are depth first and appearance second, with the `refcontrol` trigger. The adapters were trained primarily on human examples; the authors describe wider uses, but our creatures, props and structures require comparison. The 4B example uses Base FP8, 20 steps, CFG 5 and LoRA strength 1; generic Base settings and distilled four-step settings must not be silently substituted. The bundled graph estimates depth with Depth Anything V2 Large, whose weights are CC-BY-NC 4.0. We already have geometry, so directly rendering its depth is a promising replacement that avoids that particular model and its license. Match polarity, framing and normalization before claiming equivalence. [Pinned 4B example](https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-4B-reference-depth-lora/resolve/0ae1ef7f9acc4e55ec2237360943c3c3032d3583/image_flux2_klein_image_edit_4b_refcontrol_depth.json), [adapter implementation](https://github.com/thedeoxen/refcontrol), [depth-model terms](https://huggingface.co/depth-anything/Depth-Anything-V2-Large).

**Edit 2511:** RINO supplies a depth image and descriptive text directly to the editing model. That is useful evidence for conditioning, but it does not prove our proposed source-identity-plus-guide workflow. The separate fal multiple-angle LoRA is a prompt-controlled camera adapter, not the same as render conditioning. Retain that distinction. Edit 2511 is an editing model; a text-only initial design needs a supported creation route, with any stage-specific model change explained to the user. [RINO](https://github.com/yangtiming/RINO), [fal angle adapter](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA).

**FLUX 3:** official guidance documents up to ten references, generation/editing and bounding boxes. Boxes influence placement and scale; they do not enforce a hard pixel mask or a camera pose. Its prompt enhancer should produce the model's full scene-caption format, using BFL's own helper or its supplied instructions for another VLM. The distilled model documents 16 steps without CFG; the model card gives Base 50 steps / 3.5, while the current reference README lists Base CFG 4. Preserve that source discrepancy for the implementation plan and select the exact supported workflow/version. Do not transfer FLUX.2 control adapters into FLUX 3. [Model card](https://huggingface.co/black-forest-labs/flux-3-image-klein), [official inference guidance](https://github.com/black-forest-labs/flux-3-image-klein).

## Native Comfy camera and render feasibility

Read-only inspection of the installed source at Comfy commit `63be2f9b82ad0dac88a7ceaa28a9cf3154125a18` found `CreateCameraInfo` and `RenderMesh`. Together they provide a plausible in-Comfy route to color and depth images from chosen cameras, without requiring the user to manually rotate a model in Blender or add an AI depth estimator. This is source evidence, not successful execution.

Important implementation limits found in that source:

- `RenderMesh` renders only the first mesh in a batch.
- Its explicit camera branch constructs a roll-free perspective look-at basis. The broader camera node offers orthographic/quaternion/roll fields, but this renderer does not establish support for all of them.
- Depth is normalized per view, near white. Set the background explicitly and validate the range expected by the adapter.
- Texture rendering requires texture data; otherwise the implementation can fall back to a solid surface.

Use a perspective, zero-roll baseline for the first future comparison. An exact render camera determines the guide, not the fidelity of the generated image. [Camera source](https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_camera.py), [mesh-render source](https://github.com/Comfy-Org/ComfyUI/blob/63be2f9b82ad0dac88a7ceaa28a9cf3154125a18/comfy_extras/nodes_mesh_postprocess.py).

## License details behind the two labels

**Qwen 2.1:** explain that the standard license is for research/evaluation and point to the official commercial request contact, `model-business@notice.qwencloud.com`. Do not promise approval, a price or a response time. AnyAngle's Apache license covers that adapter, not the underlying Qwen model. [Qwen license](https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE).

**Klein 9B:** distinguish the license for operating model weights from permission to use outputs. Do not tell users either that all outputs are noncommercial or that commercial output permission automatically authorizes commercial operation of the model. Link both the license and BFL's self-hosted commercial explanation. [License](https://huggingface.co/black-forest-labs/FLUX.2-klein-9B/blob/main/LICENSE.md), [BFL explanation](https://help.bfl.ai/articles/9272590838-self-serve-dev-license-overview-pricing).

**FLUX 3:** Kommunity v1.0 defines qualifying users as having gross annualized revenue, including affiliates, below US$5 million. Section 2.a permits those users to operate the model in production solely to generate commercial outputs, subject to the other terms. Other uses require separate permission. Section 2.e requires filtering or review for unlawful/infringing content and applicable AI disclosures; redistribution has its own conditions. This is not blanket authorization for every commercial integration or fine-tuning service. The plain-English notice should describe the exception and link to the complete terms. [Official license](https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md), [publisher's commercial deployment page](https://bfl.ai/models/flux-3-image-klein).

For every route, retain exact component identities and terms. A permissive adapter does not change a restrictive base or preprocessor license. User choice is informed choice; a checkbox does not grant permission. Whether a model can be identified from a finished mesh is not a reliable basis for deciding its licensing obligations.

## What remains for the later implementation plan

The research pass is complete; these are implementation/experimental questions, not claims of completed tests:

1. Compare AnyAngle's original-plus-color-guide baseline with Klein Base 4B RefControl's depth-plus-appearance baseline across different asset types. Include the 9B alternative without assuming parameter count guarantees better results.
2. Measure whether adding the approved back improves unseen details or confuses the existing input contract. Do not automatically accumulate every generated view.
3. Establish the minimum useful coarse geometry and check camera conventions, framing, depth range and persistent side-specific details.
4. Test Edit 2511 and FLUX 3 as their own supported methods where justified. Do not claim that general reference editing is equivalent to a trained camera-control adapter.
5. Measure actual peak memory and speed on Brian's 16 GB GPU with 64 GB RAM. The 8 GB tier requires its own measured profile; weight-file size is not total VRAM. Serialize/offload the prompt helper, image model and mesh model as needed. BFL documents a Comfy INT8 route for FLUX 3 on 8 GB cards, but that does not establish our ten-reference or complete-pipeline peak. [BFL local guidance](https://github.com/black-forest-labs/flux-3-image-klein).
6. Carry the existing category-specific preservation rules, per-image review/editing and coherent mesh-subset tests into the implementation discussion. Ten candidates remain optional evidence, not a quota.
7. **Brian's requested addition (20 October): research and add category-based recommended settings.** Investigate whether characters, creatures, props, vehicles and buildings benefit from different defaults for each supported image and mesh model. Cover generation resolution, sampling steps, guidance, camera/FOV handling, texture resolution and export simplification/detail preservation. Use official guidance and comparative results; do not invent numerical differences solely because the category changed. Keep every setting exposed and adjustable, explain each recommendation and its detail/time/memory tradeoff in plain English, and provide **Reset to recommended settings**. Account for the selected model, hardware and rough-guide versus final-asset stage. This is an accepted research and future implementation item, not implemented behavior.

8. **Mesh follow-up research completed (20 October):** the [mesh-component and Pixal3D report](MESH-COMPONENT-RESEARCH-REPORT.md) answers the [completed plan](MESH-COMPONENT-RESEARCH-PLAN.md). Its [inventory](mesh-components.json) and [source register](mesh-sources.json) cover supporting parts, background removal, native guides, generation/preview/export behavior, category defaults, memory and licenses. The next step is a separately discussed implementation proposal for the existing Comfy software; no product changes or new inference tests followed this research.

No weights were downloaded, applications controlled, workflows modified, assets generated, or product code changed for this addendum. This note and the parent report link the separately authorized research plan. No commit or push was made. Product implementation remains a later decision after the research findings are reviewed.
