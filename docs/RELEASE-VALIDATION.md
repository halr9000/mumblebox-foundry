# Preview 0.1.0-preview.7 validation

Preview.7 adds the categorized Roadmap tab, repairs text clipboard handling and keeps Pinokio Update accessible while running. Targeted checks cover clipboard ownership/native editing, running-menu visibility, the idle guard, update stop/install/restart ordering and fresh manual release checks. The source and installed ComfyUI clipboard path were exercised with Ctrl+C/Ctrl+V. No new asset generation or category-quality qualification is claimed for this release. Earlier pipeline evidence below remains from prior previews.

Validated on 2026-11-02 on Windows/NVIDIA. This release adds the Pinokio installer and embedded Foundry interface, and repairs first-use model preparation and isolated texture-worker dependencies. The checks below distinguish actual generation from automated contract checks.

## Model acquisition and installation

- Downloaded all three required DINOv3 files without authentication from the public distribution already used by the pinned upstream TRELLIS wrapper. Their SHA-256 hashes matched the existing model manifest, including the 1,212,559,808-byte weights. The model and its license are unchanged; this acquisition path does not require the original repository's approval queue.
- The complete selected-workflow resource set is prepared before generation, including downstream texture resources and back-view resources for image pairs. Print-only selection does not acquire unnecessary texture models. Files are prepared on disk; model loading/offloading remains stage-specific.
- The installed texture-worker entry-point probe passed in both the native ComfyUI configuration and Pinokio's isolated worker environment. Its ComfyUI utility imports are now declared worker dependencies instead of relying on the host environment.
- Focused automated checks passed: seven workflow/Rocket checks, ten readiness checks, seven bootstrap checks, six release/installer checks and two quad-diagonal checks. Release packaging rejects invalid UTF-8 and known corrupted-punctuation sequences.

## Saved asset and geometry

The Pinokio Ranger test used saved checkpoints to resume the failed workflow rather than regenerate successful stages. Turnaround, initial mesh, Hi3D, cleanup, texture, compact export preparation and optional quad preparation completed in the managed installation.

- Hi3D used CUDA: recorded allocated/reserved GPU memory was 8,565/9,232 MB. The texture worker recorded 3.503/3.691 GB allocated/reserved.
- The cleaned master had 359,200 vertices and 718,356 triangles. It had zero boundary edges, non-manifold edges and degenerate faces, with consistent winding and a watertight result.
- Texturing retained 718,356 triangles; UV seams increased the vertex count to 422,768. The measured maximum positional difference was approximately 1.64e-8.
- The compact version reached 100,000 triangles and passed the same boundary, non-manifold, degenerate-face, winding and watertight checks.
- The optional authoring version contained 24,399 quads and eight small triangular caps, with no n-gons. Its triangulated export had 48,806 triangles and was watertight. All 17 disconnected components were retained. A deterministic 10,000-point comparison measured mean/p95 surface deviation of 0.000156/0.000538 of the source bounding-box diagonal; this does not establish animation-ready edge flow.
- Quad corrections preserve the detailed master. They resolve triangulation conflicts and bounded small boundary loops; they do not merge all components or globally weld the source. Temporary NumPy mesh archives are closed before Windows scratch cleanup.

The saved test asset's final packaging retry and archive review were deferred by user instruction; they are not claimed as preview.6 validation. These measurements describe this asset, not a guarantee for arbitrary generated subjects. Category generation and physical webcam checks remain user testing.

## Release boundary

The portable package includes the launcher, app entry point, dependency manifest and update/repair paths. Model weights, generated test assets, credentials and private runtime records are excluded. Models download on workflow first use, not when installing or opening Foundry. A Windows/NVIDIA managed-install run is not a claim of Linux/macOS or 8 GB compatibility.

---

# Retained preview.5 evidence

Validated on 2026-11-01. This release adds the independent image creator, paired editing, Image Gallery and image-to-3D handoff. The existing four-view mesh, refinement, cleanup and export stages retain their owners and settings. Test images and private runtime records are not distributed.

## Real generation and installed controls

Checks operated the actual Foundry interface in the existing Alt-Tab-accessible Comfy Desktop window through its supported integration, without moving or focusing the operating-system window.

| Path | Observed result |
|---|---|
| Front/back creation | FLUX.2 Klein 4B generated a clockwork courier front and an image-conditioned back at 512 pixels, four steps, CFG 1, seeds 42/43. Both previews loaded. |
| Selected-area edit | A vest color edit completed through the installed editor. Comparison against the actual source-resolution selection found 19,500 changed pixels inside and **zero outside**. Accepting the edit retained the original and left the rear revision unchanged. |
| Single image and LoRA | General Image generated a 512-pixel paper observatory using the installed Paper Diorama Klein 4B LoRA. The result and resource hash/source appeared in its record. General Image offered no 3D handoff. |
| Gallery | Saving produced one grouped pair entry and one single-image entry with loaded thumbnails. Saved files and entry removal have separate confirmation controls. |
| 3D handoff | Save & Create a 3D Mesh opened page 1 with accepted front/back copies, roles, descriptions and a server-validated provenance receipt. No additional mesh generation was required. |
| Reload recovery | A restored Comfy property proxy initially broke creator initialization. The installed repair restored the saved draft and both previews after reload. |
| Separate graph | The creator materialized its own colored node group on the same graph. The existing 94-node 3D workflow and its completed alien output records were preserved. |

These are representative checks, not qualification of every model, LoRA or category. The accepted edit can make the two views inconsistent; the UI asks users to review both. Physical webcam capture remains deferred because no camera is connected.

## Automated and protocol checks

- Foundry Python suite: **83 passed**, including 20 image-creation tests. Coverage includes input contracts, pair preservation/recovery, revisions, selection compositing, package privacy, bounded Gallery queries, deletion ownership and handoff validation, alongside the existing 3D contracts.
- Portable installer: **5 passed**. Reinstallation preserves settings/models, backs up changed files and rejects unsafe runtime configuration before writes.
- Existing JavaScript wizard-session regression passed. Changed image UI modules passed syntax checks.
- Real MCP stdio against installed services discovered **23 tools**. Image capabilities, create/update/status, idle cancellation, save, Gallery, handoff and invalid operation rejection passed. Existing 3D status/package/create/update/cancel operations also passed. This protocol check did not start a GPU run.

## Output documentation

The actual accepted pair ZIP contained `Images/front.png`, `Images/back.png`, `README.md` and `Metadata/creation.json`. The single-image ZIP contained `Images/single.png` and the same two documentation files. ZIP integrity and member checksums passed. README dimensions, roles, model terms and the single image's LoRA source matched the records. Embedded private recipe metadata was excluded.

The mesh README renderer was exercised with originating-image provenance and produced its model/license section. The handoff's copied input hashes and provenance were verified independently. This is not a claim that a fresh complete image-to-mesh generation/export was run during preview.5; the existing mesh run and export contract tests were retained.

## Release boundary

The explicit archive inventory includes the new image backend, editor/Gallery assets, MCP adapter and documentation. It excludes generated assets, model weights, credentials, local runtime records and obsolete logo drafts. The public workflow has empty user inputs and no saved outputs. The independent image graph is populated when image creation runs.

The release uses the existing portable installer and dependency setup. Relocation/package checks are not a fresh-machine installation test. Windows/NVIDIA is the tested platform: RTX 4080 SUPER, 16 GB VRAM and 64 GB system RAM. Additional memory profiles do not establish 8 GB compatibility.

Optional quads do not imply automatic rigging or animation-ready deformation. Strand Groom/Alembic, deferred workflow cards and Pinokio packaging remain future work. Third-party licenses remain separate from Foundry's Apache-2.0 license. GitHub records the release commit and attached archive digest; the archive also contains per-file `SHA256SUMS.json`.

---

# Retained preview.4 evidence

Validated on 2026-11-01. Preview.4 corrects an archive inventory omission of the retained Materials Lab HTML entry point; the main wizard and mesh pipeline are unchanged. A regression check now requires that entry point in the archive. Public preview.3 was downloaded without authentication, its digest matched, and the installed update control successfully read its GitHub release. Evidence below separates installed control actions, automated tests and exported-asset checks. Generated test assets and local diagnostic receipts are not distributed.

## Installed interface checks

The existing Comfy Desktop window remained available through Alt-Tab. Checks used its supported integration without bringing the operating-system window forward. The main graph retained 94 nodes, 20 groups, 137 links and 31 output records.

| Area | Observed result |
|---|---|
| Main shell and wizard | Compact grouped navigation, requested removals, combined reference intake and model/licensing section afterward. All five wizard pages inspected. |
| New versus resumed work | Open Wizard opened an empty page 1; Resume previous asset restored the saved asset. No generation was started by either action. |
| Themes and artwork | Real theme controls switched light/dark presentation. The approved shared logo and six workflow illustrations loaded. |
| Settings | Automatic update preference saved off/on and persisted through bootstrap reads. Check for updates reported a real GitHub availability/rate-limit failure before publication instead of claiming success. |
| Resource deletion | An exclusive 50-byte test file appeared in the LoRA list. Cancel preserved it; confirmed deletion removed only that file. Shared-resource Delete controls were disabled. No user model was deleted. |
| Civitai | Family changes requested new results automatically. NSFW filtering sent true/false. API-key help opened the correct Settings field. Download selected Pixel Art XL and verified an existing 162.6 MB file, without another weight download. |
| History | The saved asset displayed its generated front image. The public package-import panel was absent. |
| Rocket confirmation | Opened from the wizard, selected versions/formats, rejected an empty selection, and cancelled without altering saved choices. The same selector serves normal exports. |
| Review workspace | Mesh preview appears beside export choices. Settings and Rocket dialogs fit within the available embedded viewport in both themes. |

The latest checks did not submit a new full GPU generation or execute a real mid-generation cancellation. Rocket orchestration, retry and failure paths have the automated coverage described below; those checks are not presented as manual end-to-end generation proof.

## Automated tests

- Foundry Python suite: **63 passed**. Coverage includes run contracts/recovery, Rocket branch selection and retry idempotency, cancellation/error checkpoint preservation, library paths, resource ownership, MCP boundaries, first-use readiness, missing-only downloads and update checks.
- Release installer: **5 passed**. Installation/reinstallation preserves settings and model sentinels; changed files are backed up; remote Hi3D URLs and OneDrive runtime paths are rejected before installation writes.
- JavaScript activity/viewer/session suite: **6 passed**. Includes activity states, drag-only viewer input and fresh-versus-resumed wizard state and missing-field defaults for older agent-opened runs.
- Ten installed texture snapshot files matched the pinned manifest; verification required **zero model downloads**.
- Original source diff whitespace checks passed; retained upstream license/vendor text was not reformatted.

## MCP runtime

The distributed Foundry MCP ran through the real stdio protocol against installed Foundry HTTP services. Nine tools were discovered. Capabilities, saved-run status/package access, create/update, idle cancellation and invalid-start rejection passed. Test configuration did not start generation. Input restrictions and other adapter contracts have separate automated coverage. The real display action exposed a legacy run missing its turnaround-model field; session restoration now retains the original Qwen default when that field is absent and copies inputs independently. The fix has a regression test and is verified in the installed interface.

## Portable install and export proof

The allowlisted release was installed into a separate local directory and imported using the existing ComfyUI host dependencies without starting a second server. **44 node classes and 141 routes** registered. Python compilation passed. This checks relocation and package completeness; it is not a fresh-machine installation test.

From that relocated package, the exporter used preserved local assets to create only these requested outputs:

- Compact game mesh: GLB and FBX.
- Light quad authoring mesh: OBJ and FBX, with required material companions.

The resulting archive contained 22 files. All four mesh files were re-imported in Blender 5.2.2 LTS; polygon counts, UV layers, bounds and packaged texture paths passed. The root README matched the selected directories, files, measurements and recorded limitations. Source asset hashes were unchanged; ZIP integrity passed.

This direct exporter test intentionally supplied no upstream generation metadata, and the README reported that absence. It is not evidence for complete generation-model provenance by itself; the saved full workflow package and provenance contract checks cover that separate path.

The sanitized public graph has empty inputs and no saved output previews or wizard session. Its 94 nodes, 20 groups and 137 links preserve the working pipeline. Source/archive checks exclude credentials, weights, generated test assets, personal installation paths and local runtime state.

## Preserved pipeline and limits

The retained local reference run completed turnaround, native four-view geometry, Hi3D refinement, cleanup, final mesh texturing and multiple exports. This release preserves those results and stage owners. It does not claim that every future subject will be watertight or that arbitrary topology is animation-ready.

- Windows/NVIDIA preview with manual dependency setup; reference system RTX 4080 SUPER, 16 GB VRAM, 64 GB RAM.
- Alternate model/category generation quality tests remain user testing. Physical webcam capture is deferred because no camera is connected.
- Additional memory profiles are placeholders. No 8 GB compatibility claim.
- Quad retopology is optional; no automatic rigging/deformation qualification.
- FBX material interpretation and Unreal import require destination-specific review. Physical printing is not tested.
- Strand Groom/Alembic, deferred workflow cards and Pinokio packaging remain future work.
- Model licenses remain separate from the original code's Apache-2.0 license.

Public release URLs, commit and final archive digest are recorded by GitHub's release and its attached checksum file. The archive also contains SHA256SUMS.json for individual files.
