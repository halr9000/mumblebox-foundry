# Civitai integration — installed verification

## Delivery boundary

Brian's latest instruction is to finish everything except the final account step. The local implementation is finished and installed in the existing Comfy Desktop. Civitai app registration, actual OAuth authorization, and the authenticated internet-download check dependent on that connection remain unverified. The overall goal must not be represented as fully complete while those remain.

No account registration was submitted. No private key was obtained or copied from another application. The browser-control refusal for the Civitai authentication site was not bypassed.

## Installed behavior

| Behavior | Evidence |
| --- | --- |
| On-canvas browser | Integrations renders inside the existing Mumblebox controls, beside the processing graph. No replacement popup or second app. |
| Model/LoRA shortcuts | Browse more models opens checkpoints for the current profile. Browse more LoRAs opens LoRAs. Both were operated in the installed interface. |
| Supported families | All eleven profile filters returned HTTP 200 and results from the live Civitai API. Download eligibility additionally checks exact variant, resource type, file ownership, SafeTensor format and SHA-256. |
| Search, pagination and detail | SDXL LoRA results loaded 12, then 24 after Load more. Version selection, file identity, previews, creator notes, usage flags and destination were inspected in the live interface. A pasted SD XL version URL selected version 126601/file 91488. |
| Mature-content switch | Default off. An on/off sequence immediately cleared results and selected detail, then returned twelve results with no mature preview records. Stale replies cannot restore the previous result set. Only the switch preference is stored in localStorage. |
| Connection recovery | A real unauthenticated download returned HTTP 401. Its persistent progress panel retained the error through tab navigation; Open Civitai Settings focused the exact key field. Existing Hugging Face connection remained connected. |
| Download engine | Stream, hash rejection, HTML rejection, range mismatch, pause/resume, cancel/retry, unknown length, shared writer lock, redirect credential isolation, existing-file collision and complete-partial recovery pass deterministic tests. These are fixture tests, not proof of a live authenticated transfer. |
| Explicit use | Add LoRA selected/enabled the verified file, refreshed the existing selector and switched to its clearly named model when needed. Use checkpoint selected verified SDXL weights; the selection reached the native loader. |
| Credential lifecycle | OS-vault storage, failed replacement preserving the old connection, no plaintext fallback, public-only client configuration, device polling/backoff/denial, refresh rotation and revoke/disconnect pass fixtures. No actual OAuth connection is claimed. |
| Local API limits | Unsupported profile, unrelated pasted URL and oversized JSON body returned 400. A foreign-origin credential operation was denied with 403. Stale apply requests preserve the project and now return 409. Successful selections use the existing bounded public-project response. |
| Existing workflow | Image preparation/editing/foreground/mesh/export regressions passed. GPU finishing remains PEC; release_between_stages remains enabled. No new mesh or quality comparison was required for this integration. |

## Weights and actual generation

The existing owned SDXL Base and Pixel Art XL files exactly matched Civitai's SHA-256 identities. Owned hard links under this installation's Mumblebox folders reused those bytes without changing the originals or downloading duplicate copies. This is verified local reuse, not a successful internet transfer.

- Checkpoint: SD XL model 101055, version 126601, file 91488; SHA-256 `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b`.
- LoRA: Pixel Art XL model 120096, version 130580, file 94718; SHA-256 `4234637cb80c998f41e348e6a6cb6bc20d8d038b2b0f256b6129b3b5e353eef7`.
- Actual project: `7ad618002d9a`, “Civitai wiring check — coolant pump”.
- First attempt was rejected before sampling because Windows combo values use native path separators. The recipe boundary now converts portable nested paths for both LoRA loaders and the native modern-model loader. Regression tests reproduced and then passed the fault.
- Job `a55d2d5fa26e493589724202fc575bb0` completed with the imported checkpoint and LoRA. Native validation reported **722 matched and applied patches**, including zero CLIP patches where the LoRA has none. This proves application of weights, not aesthetic fidelity.
- The final metadata check found checkpoint provenance was appended after the Save Image node had serialized its recipe. It now enters both SDXL and modern recipes before serialization and survives agent-package filtering. Job `37e8b8c4dfbb435aa9b19330b7195698` completed with the same prompt/settings and reused seed 3502514300, verifying the repaired saved record. No image-quality tuning occurred; the two successful checks produced identical image pixels.
- Final image: `E:/Comfy-Desktop/ComfyUI-Shared/output/AssetWorkshop/assets/7ad618002d9a/images/design/19d37c2505a04285.png`. It is unapproved for mesh use, ready for Brian's review.
- Both selected resources' sources, identifiers, checksums and creator permissions are retained in the saved recipe. Agent-export serialization preserves them in the affected tests; no new 3D mesh/package was generated for this browser check. Checkpoint 91488 is explicitly present in the final image recipe.
- Successful stage cleanup reported **zero loaded models**, with VRAM returning to approximately **1.4 GiB**. Browsing and verification did not load a generation model. System RAM figures include other applications; this is not a claim that all system memory was freed.

## Checks

- Full existing/new Python regression suite: **224 passed**. After the metadata correction, all four affected imported-workflow and ten agent-package checks passed again.
- All **14 Node interface check files** passed. The Civitai check additionally covers determinate/indeterminate progress and paused-status visibility.
- New/modified Python modules compile. Both actual owned SDXL checkpoint bundles passed header-only native architecture validation.
- Changes are in `E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop`. Git top-level is the containing Comfy installation, detached HEAD; unrelated untracked `comfyui-mcp/` was preserved. No commit, push, branch/worktree, Swarm change, OneDrive write, purchase or hosted generation occurred.

## Final manual account step — prepared, not performed

In Civitai account settings, the documented route is Security & Apps → OAuth Applications. Register a **public** Mumblebox app with **UserRead, ModelsRead and MediaRead** permissions (scope bitmask 37) and device authorization. No client secret should be pasted into Mumblebox. If the site's registration form does not offer public/device authorization, inspect the actual requirement before choosing a redirect; do not invent a callback URL.

Paste the public Client ID into Mumblebox **Settings → Civitai connection → Connected-app setup**, save it, then use **Connect with Civitai**. The app displays Civitai's authorization link/code. A personal Civitai API key is the implemented alternative and uses the same OS-vault policy.

After that account action, the bounded remaining verification is: authorize; verify the returned account; retry the small 12 MB file already identified as model 229213/version 383563/file 307897; confirm streaming, final hash/header validation, selector refresh and disconnect/reconnect. Refresh/revoke are currently fixture-verified only. No further model-quality rerolls or mesh comparisons are part of this delivery.

Relevant official account-flow documentation: [Civitai OAuth developer documentation](https://github.com/civitai/civitai/blob/main/docs/auth/oauth-developer-docs.md). The actual account form was not inspected beyond the rejected browser navigation; registration is deliberately left to the final assisted step.

## Screenshots

- [Browser and persistent progress](civitai-browser-installed.webp)
- [Live result cards](civitai-browser-cards.webp)
- [Final account setup fields](civitai-settings-ready.webp)
