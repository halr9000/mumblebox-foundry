# Gated model download recovery

**Goal:** A new user can identify a missing or access-restricted model, open its actual Hugging Face repository, connect a read token, and retry the same download.

**Accepted design:** Brian approved implementing the model-specific access instructions, clickable repository link, token setup, and retry path discussed in this conversation. Keep the existing interface and model pipeline. Do not generate assets or perform quality comparisons.

**Architecture:** The shared downloader owns source/error metadata and the pinned download batch. The current single-image controls display that state and recovery actions. The existing credential vault continues to own tokens. All network transfers require a user action. Approval on Hugging Face remains the user's action.

## Constraints

- Work in the existing E: installation and existing visible Comfy Desktop.
- Preserve projects, installed models, tokens, and unrelated changes.
- Do not identify all HTTP errors as gated access. Explain 401/403 as denied access that can require repository approval or token permissions.
- Cover image models, their encoders/VAEs/adapters, mesh/background/camera models, and description-assistant weights through the shared downloader.
- No tokens in URLs, status output, exports, or tests using real credentials.
- Retry keeps the original pinned model selection and resumes existing partial downloads.
- No new dependency, worktree, subagent, commit, publish, image generation, or mesh generation.

## Task 1: Downloader recovery contract

Owner: models.py; routes.py; tests/test_model_download_recovery.py.

- [x] Add failing tests for denied access with exact repository context, generic HTTP failure, preserved pinned retry selection, completed-file reuse, and cancellation.
- [x] Attach safe source metadata and actionable access errors at download_one, shared by normal models and the description assistant.
- [x] Preserve a retry descriptor for model batches and validate it at the existing download route.
- [x] Run the targeted Python tests.

## Task 2: Visible first-use and recovery controls

Owner: web/single-image.js; description_helper.py; tests/download-recovery.mjs.

- [x] Add failing behavior checks for missing-model setup and retry payload ownership.
- [x] Show repository and license links before a user starts a missing-model download.
- [x] Add read-token instructions and links next to the existing secure token field.
- [x] Show a persistent, actionable access panel on the current page with repository link, connection shortcut, and retry.
- [x] Check required models before starting generation; open setup instead of submitting a job guaranteed to fail.
- [x] Preserve description-assistant recovery information and explain retry without automatically generating anything.

## Task 3: Verify installed behavior

- [x] Run the scoped existing Python suite and relevant JS tests/syntax checks.
- [x] Activate the change in the existing Desktop, only restarting the idle backend if necessary under Brian's existing restart authorization.
- [x] Mechanically click the actual new controls against controlled missing/denied/success responses; clearly distinguish controlled coverage from real account approval.
- [x] Confirm credentials and installed models are untouched, no generation queued, and leave the interface ready for Brian.

**Stop:** All above checks pass and Brian can use the repaired controls. Report what was actually tested. Do not claim a brand-new machine or a different person's Hugging Face approval was tested.

## Progress

- Live Desktop connection verified; actual Settings button clicked. Queue idle.
- Root cause confirmed: denied download errors discard source context and no first-use recovery controls exist.


## Completion evidence

- Implemented in the existing E: Comfy installation and activated by restarting its idle backend, then reloading the existing Desktop page. No second instance or browser replacement.
- Python: 173 scoped tests passed (7.165 seconds). The new tests first reproduced missing repository recovery, incorrect server-error guidance, missing retry context, and unavailable retry handling, then passed with the repair.
- JavaScript: download-recovery.mjs passed; node --check passed. Existing progress-events, resource-recovery, status-recovery, and selection-persistence checks passed.
- Mechanical Desktop proof: filled a temporary description and clicked Generate image with a controlled missing-model response. The actual setup dialog opened; zero app jobs and zero native prompts were submitted.
- Clicked the actual model-page link, Download these files, Connect Hugging Face, and Retry download. Controlled denied/success responses exercised the installed UI without changing credentials or downloading model weights. The token shortcut retained focus; completion removed the alert and displayed a ready message.
- Corrected two observed presentation defects: the shortcut rerender discarded focus, and the recovery panel could be outside the viewport or hidden under the sticky header. Final measured heading top 140.26 px, header bottom 125.23 px; both recovery buttons visible at 1280x863.
- Real installed HTTP route rejected retry without an owned failed/paused batch with HTTP 400 and the intended explanation, before any download.
- Final Desktop: clean project a2a2149c5cf7, empty prompt/sources, zero jobs, download idle, helper stopped, native queue empty, account still connected. Existing project 30923e8fea2c and exported fish project 37928d815954 remain accessible.
- Test response hooks and transient UI fixtures were removed; polling restored. Original model files and credential storage were not changed. No image or mesh inference, model installation, commit, or push.
- Existing Comfy startup console noise remains: absent optional user.css/subgraphs paths, third-party/internal-module deprecations, registry fallbacks, and unrecognized assets.seed events. No download-control runtime exception or framework error overlay was observed.
- Limits: controlled first-use/access-denied UI coverage plus real downloader unit tests; not a clean-machine install, new-account approval, full gated-weight transfer, or mobile validation.

**Status: complete.** The accepted recovery path is installed and ready for Brian's hands-on use.
