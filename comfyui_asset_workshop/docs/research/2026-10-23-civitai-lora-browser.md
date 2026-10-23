# Civitai LoRA browser: Maestro study and Mumblebox proposal

## Research plan and boundaries

Brian authorized a focused study of Maestro's Civitai browsing, API-key handling, LoRA metadata and downloads, followed by a proposal for Mumblebox. Mumblebox must offer LoRAs only, not Civitai checkpoint/base-model downloads. Do not implement the integration during this pass.

1. Identify the installed Maestro revision and preserve its current state through read-only inspection. Trace the actual frontend, backend and downloader ownership. Use normal source analysis while full source exists; REA is only needed for behavior unavailable in source.
2. Trace key entry, storage, validation, masking, use in requests, disconnection and error recovery without reading or exposing saved credentials.
3. Trace search/filter/pagination, previews, model versions, base-model compatibility, mature-content settings, license/creator guidance, trigger words and recommended settings.
4. Trace file selection, destination, duplicate handling, progress, retry/resume/cancel, concurrent downloads, integrity checks, sidecars and refresh into the installed LoRA list. Identify which pieces are useful and which should not be copied.
5. Cross-check relevant current upstream code, official Civitai API documentation and source, including access restrictions, metadata limits and permissible reuse. Distinguish observed installed source, upstream claims and untested runtime behavior.
6. Map findings to the existing Comfy implementation and propose one bounded LoRA-only flow, backend responsibilities, interface changes, credential privacy and acceptance checks. Reuse existing local LoRA support and download progress conventions; preserve the generation pipeline and owned model folders.

Completion: research questions answered with source pointers and a concrete integration proposal; list any unresolved live API or metadata limitations. Stop before implementation, credential entry or real downloads.

## Operating snapshot

- Research method: local source inspection and primary-source web verification, one lane; no subagents under Brian's operating instructions.
- Installed source: D:/pinokio/api/Maestro.git; Git common directory .git; branch main; HEAD 0678b442723436a467cdda9eaa98eeddc44016d0. Existing modifications: app/models/flux/util.py and tests/test_image_runtime_regressions.py. Leave untouched.
- Maestro root AGENTS.md inspected. Applicable boundaries: preserve existing work, use source analysis for ordinary app understanding, launcher rules apply only to launcher work. No launcher edits, destination creation, app update or runtime lifecycle change is part of this study.
- Mumblebox source: E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop. Keep this report with its existing research notes. No development output in OneDrive or Maestro's checkout.

## Findings

### Recommendation

Add an API-driven **Civitai LoRA browser inside the existing on-canvas Mumblebox controls**. Put its entry beside Style & LoRAs and its credential controls in Settings → Integrations. Search for LoRAs compatible with the selected image model, inspect a particular version, download its weights into this Comfy installation, then explicitly add it to the current image job.

This does not require Pinokio or changes to reconstruction. It is an addition to the existing local-LoRA workflow. Use Maestro as a behavioral reference, not as a source-code dependency. Everything below is a proposal; this research has not implemented it.

### What was actually verified

- Read the installed Maestro frontend, API handlers, downloader, credential persistence, cancellation control, metadata helpers and relevant test source. No Maestro tests or downloads were run.
- Read current Civitai API source. The upstream revision sampled was `29eda63b16e355fe49a29da1861bc6bf4d6674ea`; links below pin that revision where possible. Source describes the repository, not guaranteed parity with production.
- Made public, unauthenticated metadata requests to `/api/v1/models` with `types=LORA`, `nsfw=false`, `limit=1`. SDXL 1.0, Flux.2 Klein 4B, Qwen 2.1 and Flux.3 Klein each returned HTTP 200 and one matching LoRA. No images or weight files were downloaded or displayed. Only structural metadata was inspected.
- Those responses exposed versions, trigger words, descriptions, file sizes, file IDs, hashes including SHA-256, permission fields and preview references. The first SDXL response also contained a next cursor.
- Read the existing Mumblebox LoRA loader, routes, download service and credential-vault implementation. Did not read saved credentials or personal LoRA collections.
- Changed only this research document. No app source, workflows, credentials, runtime settings or model files were changed; no app was launched, stopped or restarted.

### 1. How Maestro handles the browser

Maestro's React components render search cards, detail pages, version/file selectors, preview galleries and download rows. Its browser calls its own local Python API; that backend talks to Civitai. It does not need to frame the Civitai website. Its API-key banner links to Civitai account settings and to Maestro's integrations settings. Public browsing is still attempted without a key. [M1–M3]

Search supports text, sort, time period, base-model filters, mature-content preference and cursor pagination. The installed backend uses a bounded in-memory cache: 15 minutes and at most 200 entries. Its cache identity includes the search filters/cursor but not the credential identity. For Mumblebox, changing/removing a key must invalidate any account-dependent cache and clear relevant browser state. [M3–M4]

Maestro now also has checkpoint and character modes. **Neither belongs in the requested Mumblebox integration.** Its generic download handler accepts checkpoint imports; hiding that frontend mode would therefore be insufficient. Its pasted-URL LoRA importer, however, already rejects a parent resource whose type is not `LORA`. Apply that invariant consistently in Mumblebox's search, detail resolution and final download authorization. [M1, M5]

Current Civitai search source supports type/base-model filters and cursor pagination. Text search rejects a `page` parameter; cursors should be treated as opaque. It also distinguishes temporary overload and region/content restrictions. Use bounded pages and honor retry instructions rather than fetching a whole catalog. [C1–C2]

### 2. API keys: what to retain and what to improve

Maestro uses a password input for entry, clears the temporary input after save, and returns a mask plus an `is_set` flag to its normal settings UI. A real key stays in the backend for outgoing API requests. Saving is atomic and persistence failure restores the previous state. **Saving is not proof that Civitai accepted the key.** No dedicated Civitai validation action was found in the examined key-save path. [M6–M7]

The installed Maestro configuration stores the key in plain JSON. This is screen masking, not encryption. Its download worker can append `token` to a download URL and logs that URL on an HTTP error; that path can therefore disclose a credential. It should not be reproduced. No real configuration file was opened to establish this: the behavior is visible in the source. [M7–M8]

Mumblebox already uses an operating-system credential vault for Hugging Face, scoped to the Comfy installation. Use the same storage policy with a **separate Civitai credential**. A Hugging Face token is not a Civitai key. Do not store either key in a workflow, browser localStorage, exported agent package, metadata sidecar or log. [W1]

Proposed controls: **Get a Civitai key**, **Save key**, **Test connection**, **Disconnect**. Return only saved/verified/error status. Distinguish “key saved” from “connection verified.” An authentication-required metadata read, such as the current search endpoint's `favorites=true` path, can establish that the server recognized a key; discard returned favorites and do not present a successful public search as authentication proof. Verify the chosen endpoint with the supported key scope during implementation. A connection test still cannot promise access to every LoRA. [C1]

Civitai's current download source resolves an account, enforces resource access, handles unauthorized/no-access/early-access/archived outcomes and redirects successful requests to a file URL. A key identifies the user's permitted access; it does not purchase access or accept conditions automatically. Use the documented API authentication mechanism, redact credentials and signed URLs, and never forward the user's key to an unrelated redirect host. No browser-session or password extraction is needed. [C3–C4]

### 3. Compatibility: selected version, not a generic family guess

Maestro maps Civitai `baseModel` labels to its own LoRA directories. It correctly prefers the selected version's identity over an old search-filter selection; an explicit directory override is still possible. Mumblebox should use its supported profile IDs and exact variant mappings, not Maestro's unrelated video architectures. [M2, M5]

One concrete discrepancy: installed Maestro maps the new Qwen architecture from `Qwen 2`, while the live public query returned **`Qwen 2.1`**. Blindly copying that map would miss current resources. The API/source also distinguishes Klein 4B, Klein 9B, base/distilled labels and FLUX 3 Klein. Maintain a small explicit mapping with tested aliases. [M9, C5, live metadata checks]

| Mumblebox selection | Discovery rule | What must remain explicit |
|---|---|---|
| SDXL Base / Juggernaut XL | Start with `SDXL 1.0` LoRAs | Shared architecture does not make every style equally effective. |
| Klein 4B variants | Exact 4B labels and reviewed aliases | Never substitute 9B or Flux.1 because the name contains Flux. |
| Klein 9B variants | Exact 9B labels and reviewed aliases | Do not assert base/distilled/KV compatibility merely from a similar name or tensor width. |
| Qwen Image 2.1 | Current `Qwen 2.1` label; handle older aliases deliberately | Keep it separate from older Qwen Image/Edit weights. |
| Qwen Edit 2511 | Broad `Qwen` metadata may need creator/version evidence | A generic Qwen tag cannot prove exact edit-version compatibility. Show “Compatibility needs confirmation” when unresolved. |
| FLUX 3 Klein variants | Exact FLUX 3 Klein labels | Do not accept a Flux.1/Flux.2 adapter by family-name guessing. |

The table is a discovery policy, not a claim that arbitrary community LoRAs have been tested. Metadata supplies a compatibility hint. Mumblebox's existing native loading checks remain the final runtime check that recognized patches actually apply; even that does not prove a good visual effect. [W2–W3]

**Important API distinction:** the four live sample LoRAs had parent `type=LORA` but weight-file `type=Model`. That nested file category does not mean a full checkpoint. Decide LoRA-only eligibility from the parent resource and verified version/file ownership, not by rejecting every file whose category says Model.

### 4. Download behavior and reliability lessons

The installed Maestro worker:

1. Resolves a target directory and starts a server-owned download job.
2. Streams bytes to an attempt-specific `.part` file; reports received/total bytes.
3. Reserves the final target against simultaneous writers.
4. Checks that the stream is complete and applies minimum-size/header-length checks for SafeTensor files.
5. Atomically publishes the received file, saves a `.civitai.json` sidecar and a creator guide, then marks the download complete.
6. Supports cooperative cancellation; cleans that attempt's partial files and releases reservations. [M5, M8, M10]

Useful limits to understand:

- The examined Civitai worker starts a fresh partial file and removes it on failure; **it does not implement resumable Civitai transfers**. Do not confuse Hugging Face resume support elsewhere in Maestro with Civitai resume support. [M8, M10]
- Target reservations stop simultaneous writers, but the worker publishes with `os.replace`, so a later download can replace an existing file of the same name. Mumblebox should preserve an existing different file and use a version/file-qualified name. [M8, M10]
- The installed LoRA path does not compare a downloaded SHA-256 against the selected Civitai file hash. Its SafeTensor check inspects size/header length, not the complete tensor payload. Use Civitai's file hash plus the installed SafeTensor parser, without executing arbitrary serialized objects. [M8, M10, C6]
- Maestro accepts ZIPs and other imports. That adds extraction and collision complexity unnecessary for the first Mumblebox feature. Start with individual `.safetensors` LoRA files; give a clear unsupported-format message for archives, pickle weights and unrelated files. This does not require removing existing local-file support. [M10]
- A URL's filename and a browser-supplied base model are not authority. The backend must resolve the chosen model/version/file IDs afresh, confirm the parent is LORA, select that exact file, and enforce the owned destination. Civitai's current download source supports a specific `fileId`; preserve that selection rather than letting a generic version URL choose another file. [C3, C6]

For Mumblebox, extend the existing owned-download approach: one active transfer initially, disk-space check, streamed writes, bytes/total, pause/cancel, controlled retry, SHA-256 verification and publish only after validation. Resume only when the refreshed URL still identifies the same version/file/hash and the server confirms the exact byte range. Otherwise restart that partial safely and explain it. Never append a full response to an old partial. Unknown total size should show received bytes without inventing a percentage. [W4]

Use a distinct Civitai download descriptor; do not insert arbitrary community files into the pinned official-model catalog or loosen the existing official-model hash checks. Prefer one download coordinator for resource contention, with each provider retaining its own authentication and source-resolution rules.

### 5. Metadata and creator guidance are worth retaining

Maestro preserves model/version identity, base model, trigger words, descriptions, example prompts, tags, dates and a few preview references. Its creator guide is generated deterministically from bounded source excerpts. The automatic LoRA import explicitly uses `source_only=True`, so it does **not** load an LLM or compete for VRAM. AI refinement is a separate manual path. [M8, M11]

Mumblebox should retain:

- model/version/file IDs, SHA-256, creator/source page, exact base-model label, original filename and installation date;
- creator trigger words and version-specific usage notes;
- declared permissions/license links, captured as source metadata with a retrieval date;
- any user-edited label, trigger selection and strength separately from publisher metadata.

Show creator recommendations as recommendations. Strength/CFG/step hints in descriptions or sample prompts are not a universal machine-readable contract. Do not silently rewrite the user's subject, override model defaults or copy an example's whole scene. Optional prompt-enhancer context should be bounded and treated as untrusted quoted source information. Trigger insertion should be explicit and deduplicated. [M11, C6]

Maestro sanitizes remote HTML before rendering its description. For Mumblebox, plain text with preserved paragraphs and explicit source links is sufficient and easier to keep readable. Do not render creator HTML directly or allow embedded scripts. Fetch thumbnails lazily, use bounded sizes/results, and do not autoplay an entire gallery. Browsing does not need to load generation weights.

Civitai exposes permission fields and descriptions; those are useful for display but do not justify a blanket “all LoRAs are commercially unrestricted” claim. Display **Creator's usage conditions** with the actual source and keep the selected base model's license information separate. Do not automatically purchase paid/early-access resources or claim a paid resource became free because a key is present. [C2–C3, C6]

### 6. Proposed user experience

Keep everything inside the existing on-canvas controls. No modal replacement for Mumblebox and no need to move to Pinokio.

1. In **Create → Style & LoRAs**, provide **Browse Civitai LoRAs** beside the existing local LoRA controls. Expand an inline browser there.
2. Explain: “Download optional LoRAs to change the style or details of your images. Results are filtered for your selected image model.” Keep the selected model visible.
3. Show search, sort and a compact “Compatible with …” filter, then preview cards with creator and base-model labels. Use explicit **Load more** cursor pagination for the first version; retain position/results when returning from details.
4. Show selected version, compatible variant, trigger words, creator notes, usage conditions, file size and destination before **Download LoRA**. Public browsing can continue without a key; restricted downloads get a direct Settings shortcut.
5. Show **Downloaded X of Y**, phase, pause/cancel/retry and a useful error. A completed transfer refreshes the local list automatically. Navigating to another section does not start a second transfer or lose its status.
6. Show **Add to this image** after installation. This fills the existing LoRA row with the correct local file and selected triggers; it does not silently enable a style just because it downloaded. Keep current strength/enabled controls and their model-aware help.
7. Allow **Paste a Civitai link** as an alternate discovery path, through exactly the same type, compatibility, permission and file-validation checks. Reject checkpoint links clearly.

Suggested destination: `models/loras/Mumblebox/<compatible-family>/` under this Comfy installation, with deterministic names including version/file identity to avoid collisions. Keep the selected original filename in metadata. Existing installed LoRAs stay where they are. Display the resolved folder and offer Open folder; do not save to another application's model directory. [W2, W4]

### 7. What already exists and what requires development

| Responsibility | Existing Mumblebox owner | Proposed change |
|---|---|---|
| Local LoRA selection, strength, enabled state and trigger text | `web/single-image.js`, `profiles.py`, `recipes.py` | Add discovery/metadata affordances; retain the current image pipeline. |
| List owned local LoRA files | `single_image_routes.py:165–172` | Refresh on completed import; optionally return source/compatibility metadata alongside names. |
| Contain local LoRA paths | `recipes.py:17–24` | Retain containment and owned-installation rule. |
| Verify native patch application | `lora_compatibility.py` | Retain existing loader verification; do not promise visual correctness. |
| Private HF credentials | `hf_auth.py` | Reuse the OS-vault policy with a separate Civitai account; no shared token or plaintext fallback. |
| Model downloads and progress/recovery conventions | `models.py`, existing frontend progress UI | Reuse the streaming/progress conventions without treating community files as pinned official models. |
| Civitai API, metadata normalization and selected-file resolution | Does not exist | Add one small provider service and local routes; no Maestro backend dependency. |
| Civitai browser and credential settings | Does not exist | Add inline browser near LoRAs and settings controls in Integrations. |
| LoRA source/license/guide sidecars | No complete Civitai import path exists | Save bounded, credential-free metadata; preserve user overrides and include provenance in agent exports when that LoRA was used. |

Keep provider requests in the extension, not core Comfy. Do not introduce global request monkey-patches, another framework, a second app instance or GPU services for browsing. Use existing lifecycle/unloading behavior when generation actually loads a selected LoRA. Downloading, hashing and reading notes need CPU/disk/network, not another resident GPU model.

### 8. Implementation sequence, if approved later

1. Add separate vault-backed Civitai credentials and a narrow provider client. Prove status/error redaction and an authenticated metadata test.
2. Add server-owned LoRA-only discovery and detail resolution, exact version/file identity and explicit compatibility states. Cap page sizes/timeouts/cache and prevent older searches overwriting newer filters.
3. Add the owned-file download job, integrity checks, cancellation/resume semantics and metadata persistence. Existing different files must survive retries and naming collisions.
4. Add the inline browser and integrations controls, automatic local-list refresh, and explicit Add to this image. Keep source notes and license information readable.
5. Perform the finite functional checks below, then stop for Brian's hands-on review. No image-quality re-rolling or mesh comparisons are part of integration acceptance.

### 9. Bounded acceptance checks

These are proposed implementation checks, not tests performed during this research.

| Check | Required result |
|---|---|
| Public search and pagination | One supported-model search, next page, filter change and return from details work; stale results cannot overwrite newer search state. |
| Credential lifecycle | Save, authenticated test, restart persistence and disconnect work. Wrong key and unavailable vault are actionable. Inspect workflow/export/log/request responses for secrets. No real keys in fixtures. |
| LoRA-only enforcement | Search hides checkpoints. A pasted checkpoint link and forged download request are rejected by the backend. A real LoRA weight with file category Model remains eligible. |
| Compatibility | One SDXL entry and one supported modern-family entry map correctly. Known wrong-family entries cannot be auto-added; ambiguous labels remain explicitly unverified. |
| Successful import | One selected small compatible SafeTensor LoRA is downloaded, its exact hash verified, metadata saved, list refreshed and Add to this image populated correctly. |
| Interrupted transfer | One pause/resume and one cancel/retry check; same bytes/hash or safe restart. No partial file enters the selectable list. |
| Failure handling | Deterministic fixtures cover bad hash, HTML/error body, missing total, 401/403/404/410/429/503, expired redirect, path escape, duplicate click and existing-name collision. No repeated live failure downloads are needed. |
| Use in generation | One image generation with the imported LoRA verifies wiring and loader application. No aesthetic competition, repeated seed search or mesh-quality test. |
| Canvas and memory | Controls stay embedded; navigation keeps transfer status; browsing/download do not load an LLM or image model. Existing stage-unload policy remains intact. |

**Stopping condition:** the agreed supported-file flow passes these checks, failure paths preserve data and privacy, and Brian can browse → download → select a LoRA → generate using it. If Civitai denies a particular resource, report that specific access limitation rather than claiming the entire integration is broken or attempting to evade it. Additional asset types and formats require separate scope.

### 10. Remaining uncertainties and explicit limits

- No authenticated key test, restricted-resource download, actual installation or rendered browser interaction was performed. Those belong to implementation validation, with Brian's own key entered through the secure UI.
- Current live metadata succeeded for four named families; that is not proof of every supported variant or of community LoRA compatibility. The exact Qwen Edit 2511 identity needs careful handling because broad Qwen labels are ambiguous.
- Byte-range behavior and redirect hosts must be checked on the selected production file during implementation. Do not assume a fixed old CDN hostname or that every server supports resume. Re-resolve expired links through Civitai; do not persist signed URLs as durable identity.
- Creator license text/permissions and API scan fields can be incomplete or change. Preserve provenance and show unknown states. A hash proves the received file matches the announced bytes, not that the creator's claims are correct.
- The official old API wiki now points to `developer.civitai.com/site/reference`. That site could not be retrieved through the research browser. Current official repository source and successful public API responses supplied the needed endpoint evidence; no repeated browser workaround was attempted.
- Maestro's root license contains noncommercial/evaluation restrictions and separate component notices. The practical recommendation is an independently written client against the public API, with no copied Maestro code. This study is not a license clearance for redistribution of Maestro or third-party LoRAs. [M12]

## Source index

Local line numbers refer to the installed snapshot recorded above. Mumblebox pointers describe current source, not new behavior.

| ID | Primary evidence |
|---|---|
| M1 | `D:/pinokio/api/Maestro.git/ui/src/components/LoraBrowser/LoraBrowser.tsx`: 17–30, 40–104, 234–321, 543 onward — browser, filters, onboarding, pasted URL. |
| M2 | `D:/pinokio/api/Maestro.git/ui/src/components/LoraBrowser/ModelDetail.tsx`: 40–54, 80–160, 180–208, 260–345 — sanitized descriptions, version/file choice, metadata payload. |
| M3 | `D:/pinokio/api/Maestro.git/ui/src/stores/useStore.ts`: 5202–5245, 5248 onward — search/detail/download actions and polling. `ui/src/components/LoraBrowser/DownloadBar.tsx`: progress/cancel rows. |
| M4 | `D:/pinokio/api/Maestro.git/app/launch.py`: 4268–4413 — cache, search proxy and detail proxy. |
| M5 | Same file: 4437–4588, 4972–5133 — generic downloads versus LoRA-only URL resolution. |
| M6 | `D:/pinokio/api/Maestro.git/ui/src/components/shared/ApiKeyField.tsx`; `ui/src/components/SettingsDrawer/ServicesSettingsPanel.tsx`: 718–722 — key entry/masking/save. |
| M7 | `D:/pinokio/api/Maestro.git/app/launch.py`: 1131–1147, 3899–3904, 7643–7647, 7702–7869 — persistence, bearer auth, masking and service-config updates. `tests/test_services_config_keys.py` supplies supporting test cases, not a test run. |
| M8 | Same file: 4671–4956 — download authentication/logging, streaming, publication, metadata and cleanup. |
| M9 | Same file: 3053–3112 — Civitai base-model mapping. |
| M10 | Same file: 3637–3875 — public progress records, cancellation scope, reservations, SafeTensor length checks and archive handling. `app/services/download_control.py` — cooperative transfer cancellation. |
| M11 | Same file: 5593–5647; `app/services/lora_metadata.py`: 174–222 — deterministic creator guide, optional AI refinement and source context. |
| M12 | [Maestro license](https://raw.githubusercontent.com/Blizaine/Maestro/0678b442723436a467cdda9eaa98eeddc44016d0/LICENSE). Local LICENSE inspected too. |
| C1 | [Official search endpoint](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/pages/api/v1/models/index.ts) — filters, authenticated favorites, cursors, overload and region handling. |
| C2 | [Official model query schema](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/server/schema/model.schema.ts) — type/base-model filters and permission fields. |
| C3 | [Official download endpoint](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/pages/api/download/models/%5BmodelVersionId%5D.ts) — fileId, account/access outcomes and redirects. |
| C4 | [Official endpoint/auth wrappers](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/server/utils/endpoint-helpers.ts) — public versus authenticated requests and credential-aware caching. |
| C5 | [Official model constants](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/server/common/constants.ts) — named variants, file formats and base-license mapping. Exact live labels additionally checked through public search as described above. |
| C6 | [Official version endpoint](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/pages/api/v1/model-versions/%5Bid%5D.ts), [model detail endpoint](https://github.com/civitai/civitai/blob/29eda63b16e355fe49a29da1861bc6bf4d6674ea/src/pages/api/v1/models/%5Bid%5D.ts) — version identity, trigger words, file metadata/hashes/scans and explicit download URLs. |
| W1 | `hf_auth.py`: 16–144 — installation-specific OS-vault credentials and connect/test/disconnect behavior. |
| W2 | `single_image_routes.py`: 165–172; `recipes.py`: 17–24; `profiles.py`: 44 onward — owned local file listing, containment and declared compatibility. |
| W3 | `lora_compatibility.py`: 6–27, 55–81 — checked native weight application and explicit lack of visual verification. |
| W4 | `models.py`: 21–46, 77–149 — owned model roots, redirect credential handling, disk-space checks, range validation, hashing and refusal to overwrite existing different files. `web/single-image.js`: 411–440, 728 onward — local LoRA controls and credential UI. |

## Research completion

The focused research is complete. The result is a concrete, bounded LoRA-only integration proposal with actual source evidence and public-API confirmation. Implementation, authenticated downloads and live UI proof remain deliberately unperformed pending Brian's review.
