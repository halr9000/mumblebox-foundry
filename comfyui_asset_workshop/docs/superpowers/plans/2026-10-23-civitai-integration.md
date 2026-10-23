# Civitai browser and connected account implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. Brian prohibits subagents, extra worktrees, repeated approval loops and unrelated changes.

**Goal:** Browse compatible Civitai LoRAs/checkpoints inside Mumblebox, connect an account securely, download verified files and use them in existing image workflows.

**Architecture:** Extend the existing Python/aiohttp extension and vanilla JavaScript canvas controls. A provider service owns discovery and normalization; authentication owns the OS-vault connection; a download owner publishes verified artifacts and an installed catalog. No core Comfy internet code, new framework or generation-model changes.

**Tech stack:** Existing Python, requests/urllib, aiohttp, keyring, safetensors, Comfy native loaders and DOM/CSS. Existing Python unittest and Node UI checks; live installed proof in Comfy Desktop.

**Spec:** Accepted decisions below plus `docs/research/2026-10-23-civitai-lora-browser.md`. Later conversation overrides that report's original LoRA-only scope.

## Accepted decisions and global constraints

- Integrations is the actual Civitai browser inside the existing canvas controls. Credentials belong in Settings. No replacement popup.
- Browse more beside image-model and LoRA selection opens Integrations with matching resource type/model filters.
- Only existing workflow architectures qualify. SDXL checkpoints include model/CLIP/VAE; modern families require their existing component loader format. Metadata alone never establishes load compatibility.
- Show NSFW content toggle at the top, default off, remembered. Changing it clears prior results/detail/previews and reruns the current search. Respect server restrictions.
- Search/sort, versions, file size/format, creator, triggers, readable notes, license/source and destination. Bounded cursor pagination and stale-response protection.
- Manual API key plus registered-app connection, test/disconnect/refresh/revoke; credentials in the existing installation-scoped OS-vault policy. No secrets in URLs, workflows, logs, localStorage, sidecars or agent exports.
- Proper recovery distinguishes authentication, resource access, limits, outage and integrity failures. Deep links open the exact service settings or resource page while preserving search/job state.
- Progress bar with bytes/total and phase, visible across navigation. Pause/cancel/retry and verified range resume; immutable file/version/hash identity; no replacement of existing different files. Explicit Add/Use after installation.
- Everything stays in this Comfy installation's owned model tree on E:. Preserve Mumblebox, existing data, HF connection and existing downloads. No Swarm or OneDrive writes.
- Browsing/download work uses no GPU model. Keep stage unloading and GPU finishing unchanged.
- User authorized one plan followed by implementation, app registration and bounded functional proof. No new design approval required. Existing Comfy live controls were verified and Settings was visibly selected through its live controller before edits.

## Current truth and access limitation

2026-10-23: root `E:/Comfyui-installs/ComfyUI (1)/ComfyUI`, detached HEAD; common directory `.git`; unrelated untracked `comfyui-mcp/`. Extension changes remain in its existing installed location. No new branch/worktree or broad Git staging.

Comfy Desktop page 5 is the existing Mumblebox Single Image workflow at port 8188. `app.mumbleboxSingle` is connected and can visibly render its Settings page. The native workflow stays next to the controls.

Chrome/CDP could not connect to port 9223. The existing Chrome extension browser connection was available, but its safety gate **denied access to auth.civitai.com** when opening Civitai account settings. Its instruction prohibits alternate browser/raw-CDP workarounds. No registration/account mutation happened. Brian has been asked for manual public-app registration/client ID; never ask for a client secret. Continue local implementation and record this external requirement honestly. App registration/connection cannot be counted complete from documentation or an unconfigured button.

## Approach

Chosen: existing extension plus a self-contained Civitai provider and inline browser, retaining existing controls/styles. A hosted integration or embedded external website would introduce unnecessary account/session dependency; copying Maestro code introduces licensing and unrelated architecture. Use its behavior as reference only.

Use registered public-client device authorization where available so a local/portable Comfy installation does not require a hosted callback. If registration mandates a redirect, settle the exact registered loopback/HTTPS requirement before submitting; never guess a production callback. Manual key entry remains usable independently.

## File ownership

- `civitai_catalog.py`: HTTP errors, API client, supported-family mapping, safe model/version/file normalization, eligibility and URLs; no credentials at rest or GPU imports.
- `civitai_auth.py`: separate vault account, verified identity, public client ID configuration, device connection/refresh/revoke, safe public status. Reuse the existing vault policy without changing HF token behavior.
- `civitai_downloads.py`: one explicit transfer, shared download arbitration, persisted source identity, partials, resume/hash/header validation, installed metadata, pause/cancel/retry; no generation.
- `civitai_routes.py`: local routes adapting those owners, bounded request validation and service errors. Register through the existing extension route path.
- `web/civitai-browser.js` and `web/civitai-browser.css`: browser state/controller and UI, bound to existing Mumblebox controls; input/search/detail/download/settings recovery, no top-level modal or independent app.
- `web/single-image.js`, relevant stylesheet: new tab/shortcuts, status integration and Settings connection section; reuse current visual tokens and controls.
- `store.py`, `recipes.py`, `single_image_routes.py`, `package_export.py` only where installed resource selection/provenance requires it. No changes to reconstruction/finishing algorithms.
- Focused new Python and Node checks under `tests/`; concise installed evidence beside this plan.

## Review focus

1. Fast filter/NSFW changes or tab navigation cannot display a previous request's previews or lose an active transfer.
2. Parent type LORA with nested file type Model is legitimate; a forged checkpoint/unsupported architecture cannot bypass backend checks.
3. Redirects, HTML failures and exception strings cannot leak API keys or install error pages as weights.
4. Expired signed URLs/range mismatch/cancel near publication cannot corrupt an existing installed file.
5. Imported selection must reach the actual loader, verification preflight and exported provenance, not merely appear in a dropdown.

## Tasks

### Task 1: Provider and compatibility contract

Consumes supported profile IDs. Produces a bounded `CatalogClient` and `CivitaiError`, normalized resource/version/file records, supported-family options and exact file eligibility.

- [x] Write focused tests for LoRA-parent versus file category, exact family mapping, version/file ownership, unsupported checkpoint/format, credential-free URLs and classified errors.
- [x] Run them and observe the missing provider failure.
- [x] Implement provider with bounded timeouts, read-only discovery, cursor passthrough and no GPU imports. Verify tests.

### Task 2: Credentials and connected app

Consumes provider HTTP/error behavior and existing vault policy. Produces save/test/disconnect status, public client configuration and device authorization/poll/refresh operations.

- [x] Tests cover invalid/revoked key, failed verification preserving old connection, vault failures, no plaintext fallback, token redaction and refresh/revoke outcomes.
- [x] Implement using documented `/api/v1/me` verification and public-client authorization. Keep secrets server-side; never expose raw token responses.
- [ ] Complete registration/connection only when the blocked browser step is resolved manually; record actual evidence and permissions.

### Task 3: Verified download and installed selections

Consumes backend-resolved version/file descriptors and auth headers. Produces status with bytes/total/phase, installed verified records and explicit selected model/LoRA references.

- [x] Deterministic local fixtures cover complete stream, pause/resume, cancel/retry, HTML, wrong hash/range, duplicate writer and different existing file. Observe failures before implementation.
- [x] Re-resolve IDs before transfers and retries. Restrict the destination to owned models directories. Validate source type/format and native architecture before publishing; reserve paths and publish without overwriting unrelated files.
- [x] Persist only credential-free provenance. Hook imported selections into existing loader and preflight, maintaining official-model pins and existing memory boundaries.
- [x] Show unsupported native layouts clearly; do not enable downloads that cannot be consumed by the chosen workflow. No automatic checkpoint conversion.

### Task 4: Local routes and on-canvas browser

Consumes provider/auth/download owners. Produces Integrations UI, Settings connection controls, Browse more shortcuts and persistent download indicator.

- [x] Backend tests verify capped parameters, compatibility/type enforcement and recovery status/error schemas.
- [x] Node checks verify shortcut prefilters, NSFW reset, stale-result ownership, progress with/without total, settings deep link and explicit Add/Use selection.
- [x] Build responsive preview cards and readable inline detail; preserve current theme/type/control tokens. Keep sensitive fields out of persisted browser state.
- [x] Verify each meaningful change visibly in the existing Comfy Desktop; no second app or hidden substitute.

### Task 5: Installed functional proof and stop

- [x] Run relevant existing/new Python and Node checks once; repeat only affected checks after actual repairs.
- [x] In the installed GUI prove search, filter, cursor, details, shortcuts, key recovery and navigation with download progress.
- [ ] Complete authenticated-transfer proof after the deferred account setup. Existing matching local LoRA and checkpoint weights were selected through the browser and used successfully; the live server denied the unauthenticated transfer. Exact evidence is in the verification record.
- [x] Verify no browser/download GPU-model load; use existing release controls after generation. Confirm the existing image preparation/mesh/export path remains wired; no mesh regeneration required solely for this browser feature.
- [x] Present screenshots, installed result paths, tests and truthful external limitations; stop for Brian's review.

## Clear completion condition

All required behavior and installed proof above must work, including actual Civitai app registration and connection. A manual/account security limitation is an unresolved dependency, not a completed integration. Do not mark the goal complete until required behavior/proof is done. Stop after presenting verified results; say **DING FRIES ARE DONE!** only on actual completion.

## Progress

- Brian resumed work with the explicit instruction to finish everything except final manual account registration. All local implementation is complete; registration and the live authorization/download proof dependent on it remain deferred.
- Tasks 1–4 implemented and activated in the existing Desktop. Focused contract checks and existing regressions pass. The final image/metadata check completed successfully; exact results and remaining account action are in `2026-10-23-civitai-verification.md` beside this plan.
- Existing matching local files were SHA-256 verified against Civitai and exposed through owned hard links. This is local reuse, not evidence of an authenticated internet transfer.
- No new branch/worktree, push, model-quality comparisons, Swarm edits, hosted service, purchase or account registration occurred.
