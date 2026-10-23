# Qwen 2.1 toy camera contact-sheet prompt

Status: prompt prepared and checked; no contact-sheet generation performed.

## Guidance consulted

- [Official Qwen 2.1 T2I prompt-rewriter instructions](https://github.com/QwenLM/Qwen-Image-2.1/blob/main/prompt_rewrite/prompts/system_prompt_t2i.txt), checked 2026-10-21. Descriptive English describing the finished image; explicit counts, materials, colors and spatial relationships; walk divided layouts in order; separate output ratio from prompt text. This is the model author's prompt guidance, not an official SKILL.md claim.
- [Official model card](https://huggingface.co/Qwen/Qwen-Image-2.1), checked 2026-10-21. The example specifies 2048x2048 and 40 steps. The current local native profile's 25-step setting is a separate Comfy workflow default; this note does not change runtime settings.

## Proposed settings and review

Text-only Qwen Image 2.1 base, output 2048x2048 (square), no initial/reference image and no AnyAngle adapter for this first sheet. AnyAngle belongs to the later mesh-guided stage. Resolution is a generation setting, not wording inside the prompt. Four equal crops would be 1024x1024. These settings have not been run for this sheet on the local machine.

Panel order: upper-left front/grip-side quarter; upper-right opposite rear/plain-side quarter; lower-left front; lower-right back. The grip is on the operator's right when holding the camera: viewer-left from front and viewer-right from back. First four views use level elevation to simplify scale comparison. Review actual viewpoints before assigning camera metadata; requested poses are not measured AI output poses. Confirm complete objects, matching body/lens proportions, same grip side, sensible occlusion, and no labels/borders/extra objects. Crop panels directly; do not independently stretch objects to equal widths. Contact-sheet consistency is a hypothesis to test, not yet a demonstrated result.

## Candidate prompt

The image is a square studio product-reference sheet showing four views of the same chunky, colorful retro plastic toy camera against a uniform pale-gray background. The sheet has exactly two equal rows and two equal columns, with invisible divisions through its center and one complete camera centered within each equal square region. Clear background surrounds every camera on all sides, including its shutter button, grip, and projecting lens, and the four silhouettes remain separated from one another.

The camera has a broad cherry-red body shaped like a thick horizontal rectangle with generously rounded corners and smooth molded-plastic surfaces. One oversized sunshine-yellow cylindrical lens barrel projects a short distance from the center of its front face, surrounding a single dark circular lens. A thick royal-blue grip forms the camera's right end as seen by someone standing behind the camera and holding it to take a photograph. One large grass-green shutter button sits on top directly above that blue grip, and one small square blue-framed dark viewfinder window occupies the upper center of the rear face. These five defining parts have identical shapes, dimensions, colors, and attachment points in every view, with the remaining body surfaces plain and unmarked.

In the upper-left region, the camera appears from its front and grip-side corner, halfway between a straight front view and a side view. The broad red front, yellow lens opening, short projecting side of the lens barrel, and substantial blue grip are clearly visible together, with the blue grip toward the left of this panel and the rear viewfinder hidden behind the body. The visible front and grip-side surfaces establish the camera's solid thickness and rounded shape.

In the upper-right region, the identical camera appears from the diagonally opposite rear corner, showing its back and the plain red side opposite the blue grip. The square rear viewfinder is clearly visible, while the front lens opening is hidden and the blue grip lies on the far side of the body. The green shutter remains attached above that far-side grip.

In the lower-left region, a straight front view shows the yellow lens as a centered circle, with the blue grip on the viewer's left and the green shutter above it. The front is square to the viewing direction, and the rear viewfinder is concealed by the body.

In the lower-right region, a straight back view shows the square rear viewfinder, the blue grip on the viewer's right, and the green shutter above that grip. The rear face is square to the viewing direction, and the front lens is concealed by the body.

All four views share a level viewing height at the middle of the red body, the same long-lens perspective and camera distance, and matching apparent body height; their widths differ naturally with rotation. Soft, even studio lighting reveals the rounded plastic surfaces with restrained highlights and minimal shadows. The overall composition is a clean, balanced four-view reference sheet containing only the four camera views and their plain background.

