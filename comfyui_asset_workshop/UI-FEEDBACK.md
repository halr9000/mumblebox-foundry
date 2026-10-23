# Mumblebox Creator UI feedback

## 2026-10-21 — MUST: automatic model-specific four-view contact-sheet instructions

Status: required repair recorded; automatic prompt construction is not implemented. Brian authorized a manual toy-camera test of the composed instructions first.

- The user describes the object. The workflow adds the selected model's own contact-sheet instructions, based on that model's official prompting guidance. Do not require users to write layout, camera, framing, or consistency instructions themselves, and do not reuse one generic prompt unchanged across models.
- Request a 2x2 sheet with one complete object per equal panel: front/grip-side three-quarter, diagonally opposite rear three-quarter, straight front, straight rear. Camera positions must be described independently of an object's particular features so the template generalizes.
- Bind every panel to one object with fixed proportions, materials, colors, feature counts, attachment points, and feature-to-surface assignments. Change viewpoint, not design. State which faces and details should be visible or occluded in each panel; the corner views must show substantial adjoining faces and perspective depth.
- Keep consistent viewing scale and lighting, complete-object margins, and clean backgrounds. Do not stretch different projected widths into matching silhouettes. Generate at sufficient native resolution for four useful crops.
- Preserve the user's original description and the exact composed prompt/settings in History. Inspect actual viewpoints before assigning camera metadata; requested angles are not measured camera poses. Require user approval before the first mesh.
- First toy-camera sheet (asset 64edac36da7e, revision 4caf7634a7f04b7d; Qwen 2.1, 2048 square, 40 steps, CFG 1, seed 3787072834) has insufficiently oblique upper views and a rear viewfinder that shifts position. It is a completed image, not a consistency pass or mesh approval.
- CFG is a model-specific setting to evaluate, not a consistency guarantee. Qwen 2.1's official repository example uses guidance 1: https://github.com/QwenLM/Qwen-Image-2.1#inference-with-sglang . Keep that baseline; any later CFG comparison must hold prompt, seed, resolution, and other settings fixed. No CFG experiment was requested or run when recording this item.

## Current status — repair pass installed on 2026-10-20

Brian subsequently authorized planning and implementing these repairs. That supersedes the older notes-only statuses below. Implementation and readiness evidence are recorded once in [the repair plan](docs/superpowers/plans/2026-10-20-mumblebox-repairs.md).

- Step 1 wording/help, compact random seed, image downloads, History, editable Settings, hardware-aware memory recommendations, and operation-lock repairs are installed.
- Full image-to-textured-mesh testing, assistant inference verification, restore/delete/undo exercises, and overnight testing remain for the next agreed testing pass.
- The visible old object is a turquoise **case**, despite its stored “Starfish Asterias rubens” name. That name is not evidence of a generated starfish. Preserve the case and do not describe it as a starfish.
- Brian rejected the Step 3 tab label “Your 3D asset.” Suggested replacement: **“3 Preview & export.”** Await his naming decision; do not treat the suggestion as accepted.

## 2026-10-20 — Seed controls

Status: recorded for a later pass. Brian explicitly said not to fix this yet.

- Default the user-facing seed field to `-1` for a new random seed.
- Explain beside the field: “Use -1 for a new random seed each time. Enter a specific number to reuse that seed.”
- Resolve the confusing combination of a displayed number such as `42` and a separate “New random seed” selection.
- Show the actual seed used for each generated image so the user can reuse it.
- Keep the agreed behavior that “Generate again” uses a new random seed, and explain that clearly.
- This note authorizes no implementation; wait for Brian to resume changes.

## 2026-10-20 — Initial image drop area

Status: feedback only; the instruction not to implement changes yet remains in effect.

- Replace “Optional. Drop an image here, or choose a file.”
- With “Optional. Drop an image here, choose a file, or simply enter a description below.”
- Keep this instruction inside the drop area so users can immediately see that typing a description is an alternative to uploading an image.

## 2026-10-20 — Enhance description disabled while Comfy is idle

Status: added to the repair list at Brian's request. Do not repair or run verification yet.

- Observed: “Enhance description” is disabled despite a nonempty description. The interface reports an image operation at “Getting ready…”, while Comfy's queue is empty, downloads are idle, and the description assistant is idle.
- Diagnose and repair the stale or stuck busy state so the button is available when idle and the description contains text. Preserve appropriate protection during real active work.
- Make the reason for a disabled control understandable to the user.
- The configured enhancement/auto-description model is Qwen3.5-9B-Heretic, Q8 by default with a Q4 option, downloaded on first use.
- Model download and a successful enhancement/auto-description run have not yet been verified. Include that verification in the authorized future repair pass before claiming the feature works.

## 2026-10-20 — Description wording and disabled reference upload

Status: added to the repair list at Brian's request. No interface changes or repairs yet.

- Replace “Tell us what you want to make. With an initial image, describe any changes you want.”
- With “Describe what the image should look like, or describe the changes you want to make here.”
- Address the user directly with clear instructions; avoid “tell us” wording that implies an unidentified person or team is receiving the description.
- Brian reports that “Add reference images” is greyed out. Diagnose and repair its disabled state so users can add references when idle.
- Check whether reference upload is affected by the same stuck busy state as “Enhance description”; this cause has not been separately verified for the reported button.

## 2026-10-20 — Description actions, advanced controls, and progression

Status: requested revisions recorded only. Do not implement until Brian resumes repairs.

- Rename “Auto describe” to “Auto Describe my image”.
- Give that button its own tooltip explaining that it describes the initial image the user has already uploaded and presents an editable description.
- Give “Enhance description” its own tooltip explaining that it expands the user's written description with useful visual details and presents a suggestion for review before replacing the text.
- Add a right-aligned primary action beside the description actions: “Generate image and go to Step 2”.
- Revised requested flow: clicking that action generates the image, then automatically opens Step 2 with that generated image when generation succeeds. This supersedes the earlier requirement to remain in Step 1 and click a separate acceptance/next-step button for this action. Do not advance before the image is successfully available.
- Beneath the action row, place the image model and sampling controls under “Advanced — Image model and controls”.
- Clearly explain that choosing an image model loads its recommended default settings, which the user can adjust.
- Make the seed field compact and proportionate to a numeric input instead of allowing it to occupy most of the row or screen. Retain the seed behavior and explanation requested above.

## 2026-10-20 — Asset history

Status: requested feature under discussion. No implementation authorized yet.

- Add a History tab for reopening previous assets and deleting saved work.
- Restore the asset's description, actual generation seed, and all generation parameters along with its images and outputs.
- Brian asked about JSON storage. A per-asset JSON record with relative references to image and mesh files was discussed; detailed storage and version-retention behavior remain design proposals.

## 2026-10-20 — Download every displayed image

Status: interface-wide requirement recorded. No interface changes yet.

- Wherever an image is displayed, provide an accessible “Download image” control.
- Apply this to uploaded initial images, additional references, generated designs, generated angles, history entries, and any image previews.
- Download the underlying full-resolution image file, rather than a reduced thumbnail or screenshot of the interface.
- Preserve this control when images are shown outside their original creation step.
