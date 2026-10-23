# Mumblebox: practical local workflow recommendation

Research and synthesis completed October 22, 2026. Proposal for discussion, not an approved implementation. Target: Brian's 16 GB GPU and 64 GB RAM Windows machine.

**The recommendation**

Keep a good first mesh and make deliberate, localized changes to it. Use the existing staged Pixal3D path to make that first mesh. For an absent physical part, generate or supply the part separately, then place it on the preserved base. For a logo, color, or surface pattern, change the texture on the preserved geometry. Use targeted Blender editing as the single fallback when a change requires cutting, seamless reshaping, or topology repair.

This is the strongest practical proposal supported by the evidence we have. It is also a narrower promise than automatic neural editing of any hidden surface. The new part-placement and texture-projection connections still require development and validation. This report does **not** establish a finished Comfy-only replacement for a 3D artist.

The research did find genuine neural geometry editors. None of the inspected releases established the complete combination we need: arbitrary rear-side editing, preservation of an imported Pixal3D mesh, practical 16 GB Windows operation, suitable distribution terms, and a working Comfy integration. That is a feasibility limit, not proof that the problem is impossible.

Do not make a second whole-object reconstruction the default. Do not require six, eight, or ten generated views. Do not retain five image-model workflows just because they were previously built. Preserve the existing Mumblebox implementation and research assets; removal or replacement would be a separate implementation decision.

**What this would let a person do**

Start with a picture of an explorer. Create a useful mesh. If the backpack is missing, use a backpack reference to create that part and attach it to the back without asking an image model to redraw the explorer's face, limbs, or proportions. If the shirt needs a symbol on its back, put that symbol on the actual shirt surface. Inspect the resulting object from any angle and export it.

The backpack has real volume. The shirt symbol does not. A picture showing a backpack is not evidence that the exported mesh contains one.

The tradeoff is explicit placement and review. A single backpack image still leaves its unseen shape uncertain; dimensions and placement require a human decision or a measurable specification. Joining separate parts does not automatically produce one printable solid or an animation-ready character. Seamless anatomy changes remain outside the first proposed Comfy implementation.

**What was actually checked**

This pass read the earlier experiment results, current native Comfy source, the existing model lock, author repositories, inference entry points, checkpoint listings, licenses, papers, and the recent workflow review. Small source files and documentation were saved as research evidence. No model weights were installed, no generation was run, no compute was purchased, and no Comfy workflow, setting, or runtime was changed.

Evidence labels in this report mean:

| Label | Meaning |
|---|---|
| Earlier local proof | Recorded results from the completed experiment, reread during this pass; not a new run |
| Source verified | Behavior or interface visible in the inspected source; not runtime proof |
| Author reported | A requirement or result published by the authors |
| Proposed | Work to build and test after approval |
| Not established | The evidence does not support a promise |

The canonical previous results are [the independent experiment's RESULTS.md](../../../../mumblebox_camera_experiment/RESULTS.md). The existing [research report](REPORT.md), [source register](SOURCE-REGISTER.md), and [recent workflow review](RECENT-WORKFLOW-REVIEW.md) remain historical evidence. This recommendation supersedes their provisional route ranking; it does not erase their findings.

**The lessons that decide the route**

1. **Extra views can help, but their quality as measurements matters.** Six owned fixtures reconstructed from consistent renders with exact cameras improved their median normalized surface error by 17–75% over the single-image baseline. Those were limited fixtures, including abstract organic shapes, not a realistic-character benchmark.
2. **Our generated-view improvement failed its declared gate.** The reconstructed vehicle and creature became approximately 53% and 82% worse on that metric. Other sets failed image or camera review before reconstruction. Attractive pictures did not establish compatible observations of one object.
3. **Camera estimation is not a reliable repair for every image set.** DA3 Small had maximum rotation errors of roughly 6–27 degrees on the controls; Base had several errors of 88–150 degrees. These results apply to the tested setup, not every use of DA3.
4. **The existing first mesh is a useful starting point, not an accurate hidden-side solution.** Five of six fixtures yielded recognizable editable bases. The toy camera retained inappropriate hidden-side lens geometry. Exported explorer and watering-can examples reopened with textures but were neither certified game-ready nor watertight.
5. **Finishing can destroy a good result.** Tested 40k/100k QEM reduction introduced holes. GPU resampling preserved larger features more successfully in a checked case but softened detail. A better average surface score even concealed some holes.
6. **Unloading is a resource decision, not a consistency technique.** Keeping one model loaded across a consecutive batch saves loading time. It does not make separate generated images share an understanding of the object. Release it before the next expensive model stage.

These findings justify retaining the locally demonstrated Pixal3D base path. They do not prove Pixal3D is universally better than every alternative. Switching to another mesh model now would add an unmeasured dependency without resolving the demonstrated hidden-detail control problem.

**What the released geometry editors actually offer**

| Method | Released capability and weights | Camera/native-state requirement | Practical consequence for this proposal |
|---|---|---|---|
| [Nano3D](https://github.com/JAMESYJL/Nano3D) | Actual add/remove/replace geometry editing using TRELLIS 1, flow editing and latent merging; code released; underlying TRELLIS weights listed publicly | Best-supported path keeps native TRELLIS state. Inspected entry point renders a fixed front view; imported-GLB re-encoding has an explicit preservation warning | Strong evidence the idea is real. Arbitrary rear editing and 16 GB editing peak are not established. Not a drop-in Pixal editor |
| [3DMorph](https://github.com/toprei/3dmorph) | Actual local shape editing; TRELLIS weights and inference code | Native SLAT state, source mesh, edited render and camera transforms | Author requires at least 20 GB and tests Linux. License file is internally inconsistent. Not a defensible 16 GB default |
| [VoxHammer](https://github.com/Nelipot-Lee/VoxHammer) | Released TRELLIS geometry editing with preserved regions | 3D edit mask and inversion/attention state | Author minimum is 40 GB, recommending an A100 80 GB. No evidence here of a working 16 GB port |
| [VecSet-Edit](https://github.com/BlueDyee/VecSet-Edit) | Released TripoSG-based shape editing | Mesh, source/edited image, mask and azimuth/elevation; source rotates into an editing frame | Interesting camera-aware route. No verified 16 GB run; repository does not provide a clear root license for its own additions |
| [Prox-E](https://github.com/etaisella/Prox-E) | Released primitive/proxy-guided editing using SuperDec and TRELLIS | Explicit proxy changes followed by reconstruction | Free local VLM option exists, but authors report that it substantially underperformed their preferred proxy-editing models. No verified 16 GB complete path |
| [Instant3dit](https://github.com/amirbarda/Instant3dit) | Released SDXL multiview inpainting code; author checkpoint download link; reconstructs edited views | Fixed documented cameras and rendered 3D masks | Research license excludes commercial product development. Paper used internal Adobe reconstruction models; public replacements are explicitly not on par |
| [ObjFiller-3D](https://github.com/objfiller3d/ObjFiller-3D) | Paper/demo describes reference-guided object completion | Multiview/video inpainting followed by reconstruction | Inspected tree contained presentation assets, not a usable inference/weights release |
| [MaskedLRM](https://chocolatebiscuit.github.io/MaskedLRM/) | Paper describes masked multiview conditioning and actual shape reconstruction | Model-specific masked views and reconstruction training | No usable author code/weights release verified in this bounded search |
| [EditFlow3D](https://arxiv.org/html/2608.03179v1) | Paper describes TRELLIS.2 editing with spatial localization | Native latent editing plus segmentation/localization components | No usable official inference/weights release verified here |
| [Hunyuan3D Buffalo](https://tencent-hunyuan.github.io/Hunyuan3D-Buffalo1.0/) / [NVIDIA Axolotl](https://research.nvidia.com/labs/sil/projects/axolotl3d/) | Relevant research demonstrations | Their own learned editing/reconstruction systems | Project release controls still indicate forthcoming code/model availability; not available dependencies for this implementation |

“Not verified” means the inspected sources do not establish the capability. It does not mean nobody privately possesses it. Merely publishing a repository or paper is not equivalent to releasing runnable inference and the necessary weights.

The inspected editing packages are Python research applications, not verified nodes in Brian's Comfy installation. No end-to-end Comfy integration for these editors was established in this pass. Their native TRELLIS 1, TRELLIS.2 and TripoSG latent formats are not interchangeable. Several specify older Python/PyTorch/CUDA environments; an eventual port must preserve the current Desktop environment rather than downgrade it to satisfy a research requirements file.

Nano3D deserves particular care. Its optional integrated Qwen image editor is documented with a 60 GB requirement; that number must **not** be attributed to the geometry editor alone. Pre-edited images can bypass that image editor. However, the actual entry point still eagerly loads TRELLIS, a sparse encoder and an additional DINOv2 model onto CUDA. A memory-conscious port is credible engineering work, but its fit is unproven. Its fixed-front editing path and weaker mesh-import preservation remain separate problems even if memory is solved. [Pinned inference source](https://github.com/JAMESYJL/Nano3D/blob/7d20eb6887cb73e3bb4ec349ee27e0b670004512/inference2.py).

Rotating a mesh on screen does not automatically rotate all the learned latent features into a supported editing frame. Importing a rotated Pixal mesh and re-encoding it would use precisely the weaker import route that needs preservation testing. I therefore do not recommend presenting “rotate to the back and edit anything” as a current Nano3D feature.

Instant3dit is an important explanation for why a research demonstration can look better than its downloadable implementation: the missing reconstruction model matters. Its public SDXL inpainting checkpoint is linked through Google Drive; this pass could not independently enumerate that folder, so release evidence is the author's link, not a downloaded/checksummed checkpoint. [Author disclosure](https://github.com/amirbarda/Instant3dit#reconstruction-using-lrms-large-reconstruction-models).

**Joint multiview remains eligible, but it is not the selected path**

[MV-Adapter](https://github.com/huanngzh/MV-Adapter) coordinates views using additional attention and camera-related conditioning. It is materially different from sending six independent prompts. The [author's Comfy integration](https://github.com/huanngzh/ComfyUI-MVAdapter) exists. SDXL's age is not a rejection criterion.

The inspected recipe produces six orthographic views at its prescribed camera arrangement. Its geometry-related conditioning uses viewing-ray information; it is not a universal object-depth adapter. The separate geometry-plus-image path has higher documented memory needs than ordinary image-to-multiview inference. An image-only memory claim cannot certify every mode.

Pixal's inspected projection code is perspective-based. Orthographic images cannot be made exactly perspective merely by assigning a different FOV: depth-dependent perspective size changes are missing. Approximation requires assumptions and error measurement; correct conversion needs geometry/depth and reprojection, with disocclusions handled. The paper's reconstruction route uses StableNormal and an Era3D-derived orthographic NeuS process, which avoids pretending that projection mismatch does not exist, but adds another reconstruction implementation, dependencies and an unverified Windows/16 GB finishing path.

That route could test whether coordinated views improve reconstruction. It does not establish how a user specifies a particular rear backpack while preserving the accepted front and all other geometry. It is therefore retained as research evidence, not a second recommended product workflow. References: [MV-Adapter paper](https://arxiv.org/html/2412.03632v1), [Era3D source](https://github.com/pengHTYX/Era3D).

The recent Qwen contact-sheet and Pixaroma workflows were also inspected. They provide practical examples, but cropping panels and assigning camera labels is not measured calibration. The Klein “keep the angle” example edits a rendered picture; it does not propagate that edit into the original mesh. See [the recent review](RECENT-WORKFLOW-REVIEW.md) for exact video and workflow coverage.

**The complete proposed primary path**

| Stage | What happens | Exact component and responsibility | Status |
|---|---|---|---|
| 1. Source image | Upload an existing image. Preserve its original pixels and provenance. Text-to-image is optional upstream work | Existing image loading and image/mask editing | Existing capability; not exercised in this research pass |
| 2. Prepare | Remove background; inspect fine parts; crop/pad with recorded transforms and the existing 10% margin | BiRefNet; existing preparation path | Earlier local proof |
| 3. First geometry | Estimate perspective, extract features, sample structure and shape, refine at the already-tested 1024 stage | MoGe-2 ViT-L; DINOv3-L + NAF; Pixal3D single-image weights; TRELLIS.2 shape decoder | Earlier local proof of useful bases and resource fit |
| 4. Preserve | Save the full mesh and reusable native state before reduction or texture work | Existing experiment state handling and native export | Earlier local proof |
| 5. Specify missing detail | Decide whether the requested change is physical geometry or surface appearance. Record the side, location, size and reference | Proposed edit record plus existing preview and mask tools | New connection; no automatic inference of hidden design truth |
| 6a. Add a physical part | Generate that isolated part from its own image using the same preparation/Pixal path, or use a supplied mesh. Place with explicit transform and dimensions | Existing reconstruction; proposed scene composition using trimesh.Scene | New composition connection; separate-part generation does not solve all part geometry |
| 6b. Change appearance | Render the actual selected surface from a recorded camera. Edit or supply the design. Project only onto visible, selected surface texels | Native RenderMesh; proposed visibility-tested image-to-UV projection and masked blend | New projector; current ApplyTextureToMesh is not this operation |
| 7. Finish | Preserve the full master; create an export derivative. GPU resampling only when needed, GPU PEC unwrap and texture baking when required | Native RemeshMesh, UnwrapMesh with PEC, BakeTextureFromVoxel, ApplyTextureToMesh | Core pieces exist; assembled-object finishing needs validation |
| 8. Export and reopen | Export GLB with every part, transform, UV and material. Geometry-only output skips texturing. Reopen the actual saved file | Proposed scene-preserving GLB export using trimesh; existing native preview | New multi-part export contract; prior single-object reopening was proven |

The authoritative shape after stage 4 is the saved mesh, not a newly generated image. A geometry addition may extend it, but does not require regenerating its existing vertices. A texture patch must leave its geometry unchanged.

The first mesh must still pass inspection. This approach will not cure a compacted vehicle, duplicated lens, or badly shaped body just by attaching a good accessory. Such a base is rejected or requires the stated fallback. The proposal improves control and preservation; it does not claim a newly discovered universally superior first-mesh model.

For the first implementation, parts remain separate named meshes in one GLB. That is a valid scene representation, not a watertight Boolean union. A game import still needs polygon budgets, collisions, pivots, and possibly rigging. A print still needs solid geometry and scale checks. Neither is implied by a successful file save.

The optional image helper should be **Klein 4B**, limited to preparing an isolated part reference or editing a surface picture. It is compact, locally usable and has straightforward Apache 2.0 terms. Use the ordinary distilled model for that role; do not silently carry over the tested Base+RefControl camera recipe. The report does not claim the distilled helper has passed the previous Base-model resource benchmark. Uploading references lets the primary geometry path function without this helper. [Official model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B).

Qwen, Klein 9B, FLUX 3, SDXL and AnyAngle are not dependencies of this proposal. Existing files and workflows remain preserved. No family-wide rejection is implied: they have simply not demonstrated a necessary advantage for the narrowly chosen path.

**How hidden details are controlled**

| Requested detail | Proposed control | What it cannot honestly promise |
|---|---|---|
| A backpack, handle, chimney, antenna or wing | Reference for that part; generate/import it; set physical size, rotation and attachment position; inspect from multiple sides | Automatic seam blending, deformation with a character rig, or exact unseen part shape from one picture |
| A symbol on a shirt back, rear warning stripe or material patch | Select that actual surface, use a known render camera, project the design into its UV map with occlusion checks | Added volume, a hole, or new silhouette |
| A missing wall opening, recessed socket or changed body shape | Targeted Blender fallback on the preserved base | General neural editing inside Comfy in this first version |
| A fully specified unseen side provided as another image | Use it to judge shape, derive individual parts, and guide placement or texture edits | Automatic exact multi-image fusion without verified geometry/cameras |

An edited render may contain a beautifully drawn new protrusion. Texture projection must reject treating that protrusion as completed geometry. Likewise, depth and silhouette guides convey approximate shape as well as orientation; they cannot be made “camera only” simply by prompting the model to ignore their geometry.

A vision-language model could assist with a checklist of visible and unspecified surfaces. It cannot observe an invisible wall or certify that an invented camera angle is physically correct. It is not a prerequisite for this proposal.

**The single fallback**

Use Blender for a targeted edit of the accepted mesh: cut a real opening, reshape a limited region, attach/blend a part, or repair topology. Keep the source images and accepted mesh as references and preserve a pre-edit copy.

This fallback is justified because it changes the actual required geometry directly and operates locally without another large generative model. It is a real reduction in automation, and the amount of manual or agent-guided work depends on the object. It is not a claim that Blender can recover unseen truth from an image.

Blender's Boolean tools have explicit topology and solver limitations; they are not an automatic fix for every generated surface. Its glTF export supports meshes and PBR materials, but exported behavior must be inspected after reopening. [Boolean documentation](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/booleans.html), [glTF documentation](https://docs.blender.org/manual/en/5.3/addons/scene_gltf2.html).

GPU finishing remains the primary policy. Small matrix operations, file serialization and necessary targeted topology edits may run on CPU. That does not justify returning to the stalled CPU UV/finishing path. The first iteration should not depend on an expensive CPU Boolean/remesh of an entire multi-million-triangle asset.

**What exists, and what must actually be developed**

The model lock records the following exact starting components. A lock entry records provenance; it is not a fresh hash verification or a new installation test.

| Component | Existing source/revision |
|---|---|
| Pixal single model; shape/texture VAEs; DINOv3-L+NAF repack | Comfy-Org/Pixal3D at f37641be376725d324c56626007cc477f1249a69 |
| Background remover | Comfy-Org/BiRefNet at 25511f8787e51912e1480706b4e47b8f467fbf72 |
| Perspective estimator | Ruicheng/moge-2-vitl at 39c4d5e957afe587e04eec59dc2bcc3be5ecd968 |
| Optional distilled image helper | black-forest-labs/FLUX.2-klein-4b-fp8 at 5b4408e59397a4a37ccb46afe426d8ed86379441 |
| Its text encoder | Comfy-Org/flux2-klein-4B at 5f526678002e43af5551dadb73ce2e8c91b43afe; qwen_3_4b_fp4_flux2.safetensors |
| Its VAE | Existing flux2-vae.safetensors; preserve and verify its recorded provenance before use |

Relevant existing native nodes include Pixal3DConditioning, Trellis2ShapeStage, Trellis2UpsampleStage, VaeDecodeShapeTrellis, Trellis2TextureStage, VaeDecodeTextureTrellis, RenderMesh, UnwrapMesh and BakeTextureFromVoxel. The existing experiment handles staged saved state and release boundaries.

The new work would be concentrated in four responsibilities:

1. **Scene preservation and placement.** Keep separate meshes/materials and apply recorded transforms to the saved scene. Use the established [trimesh scene API](https://trimesh.org/trimesh.scene.scene.html) and [GLB exporter](https://trimesh.org/trimesh.exchange.gltf.html), rather than inventing a mesh file format.
2. **Surface projection.** Connect the selected mask and known render camera to a visible-surface/UV projection. Respect face visibility, depth, object identity, UV seams and a bounded blend region. A render or generic image-composite node alone does not provide this.
3. **Validation.** Check preservation, actual geometry additions, materials, camera alignment, and exported placement. Retain the original on rejection.
4. **Graph orchestration.** Expose the above as an independent native-node workflow, with stage unloading and saved intermediates. No new GUI is needed for the proof.

The custom projector and scene bridge are deterministic engineering, not new trained adapters. The projector is the largest new technical piece: a painted screen pixel must be associated with the correct visible triangle and UV location, without painting an occluded surface. Its scope and tests should be treated seriously; “a small node” is not proof that implementation is trivial.

Important source findings prevent misleading shortcuts:

- Current MergeMeshes concatenates geometry but retains only the first texture when multiple textured inputs are supplied. It is not a complete multi-material assembly/export operation.
- Save3DAdvanced saves its supplied model file and passes viewer transformation information onward. The inspected save path does not bake those viewer transformations into the mesh. Preview placement alone is insufficient proof of exported placement.
- ApplyTextureToMesh accepts a UV texture; it does not project an edited perspective image onto that UV texture.
- RenderMesh supplies useful GPU-rendered color, normals, depth and silhouette. Its displayed depth is normalized for the image; it must not be treated as metric depth without an explicit conversion or a raw-depth output. Preserve the exact camera and crop for projection.
- Existing reduction and remeshing change geometry. They belong on a disposable derivative, not silently on the accepted master.

These are source-inspection findings, not newly reproduced UI defects or repairs. They are why the proposed connections must be mechanically checked.

**Memory and speed policy**

The previous staged reconstruction sampled up to 14.57 GB whole-GPU usage and 39.05 GB system RAM. Corrected image batches sampled up to 13.12 GB and 24.96 GB. These are one-second samples from previous runs, not exact allocator peaks or universal limits.

1. Run the optional image helper by itself. Encode text, release its text encoder when no longer needed, generate/edit the required images, then release image weights and cached intermediates.
2. Run background removal and camera estimation as bounded stages. Retain the necessary pixels, mask and camera data, not unnecessary model instances.
3. Run the proven Pixal staging sequence. Save reusable state without copying multi-gigabyte tensors unnecessarily. Do not load an image generator alongside mesh generation.
4. Complete geometry and texture inference before GPU unwrap/bake work. Retain only the geometry and texture data the next operation needs.
5. Use GPU PEC, not the CPU adaptive UV path. Keep the native GPU bake and the already evaluated GPU derivative path where appropriate.
6. After completion, cancellation or failure, release owned model references first, then clear unused caches. An empty-cache call cannot free still-owned tensors.

Retain a model during a short consecutive batch if no competing heavy stage needs that memory. Sample actual device and system usage at stage boundaries and during heavy operations. The proposed validation requires no OOM, no sustained paging, and at least 8 GB system RAM available at stage entry. Device headroom must be assessed against actual free memory and allocations, not a misleading fixed “16 GB” counter.

After a job ends, loaded-model count should return to zero and resource use should return near the measured idle baseline after cleanup. If it does not, identify the owner before retrying. A reboot may clear an environmental problem, but is not an acceptable routine between-stage dependency.

**Licensing and release suitability**

Local and free does not automatically mean every dependency can be bundled or used commercially.

- Pixal's release and the selected Comfy repack use MIT labeling. DINOv3 retains Meta's own license; NAF has Apache 2.0 terms. A repack's top-level MIT label must not erase upstream component obligations. [Pixal release](https://github.com/TencentARC/Pixal3D), [DINOv3 license](https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md), [NAF license](https://github.com/valeoai/NAF/blob/main/LICENSE).
- The chosen BiRefNet checkpoint is distinct from BRIA's differently licensed removers. The optional Klein 4B model is Apache 2.0; this does not describe Klein 9B or every FLUX model.
- MV-Adapter is Apache 2.0; SDXL and possible custom base checkpoints retain their own terms. Era3D's AGPL code adds distribution obligations. None of these license labels proves local hardware fit.
- Nano3D's root license is MIT, but its stock rendering/export stack must be reviewed separately. The inspected nvdiffrast license limits non-NVIDIA use to noncommercial research/evaluation despite its confusing “commercial” title. Do not import that dependency into a commercial-friendly path without resolving its terms. [Actual license](https://github.com/NVlabs/nvdiffrast/blob/main/LICENSE.txt).
- 3DMorph's README says MIT, but the actual LICENSE includes unresolved BMW-permission language. Treat that as an author clarification requirement, not a clean distribution grant. VecSet-Edit's bundled TripoSG license does not automatically license the repository's own additions.
- Instant3dit's Adobe Research license is a substantive restriction for this product work. A free app is not automatically noncommercial research.

For a later distributed Mumblebox release, preserve license notices and create a component-specific manifest. This pass does not grant legal clearance or accept any access agreement. Private experimentation and distributing an application have different obligations.

**Other useful discoveries, without adding them to the primary route**

[UltraTex](https://github.com/yiboz2001/UltraTex) is a credible modern multiview texture system: Klein-base-9B plus dedicated albedo and material LoRAs and a specialized VAE, with mesh-derived guides. It improves surface appearance, not missing geometry. Its [Comfy wrapper](https://github.com/visualbruno/ComfyUI-UltraTex) and author 16 GB claims deserve attention if the existing texture stage becomes the demonstrated bottleneck. They are not local proof, and its 9B weights do not transfer to 4B.

NVIDIA rendering and geometry libraries can support rendering, visibility and baking. They do not supply the unreleased Axolotl model. DLSS improves displayed/rendered images; it does not add a missing backpack to exported triangles.

[T3lescope](https://pfnet-research.github.io/t3lescope/) is relevant surface-reconstruction research, but its inspected release/hardware evidence does not supply a ready 16 GB component. [GaussianWrapping](https://github.com/diego1401/GaussianWrapping) addresses surface extraction from posed capture data and has noncommercial restrictions; it is not an unseen-object-design engine for one photograph.

These distinctions are useful precisely because they prevent adding impressive components that solve a different problem.

**Could a custom adapter still be worthwhile?**

Yes, but only after a narrowly defined failure demonstrates why it is needed. The evidence supports several different projects, not one universal adapter:

| Project | Necessary training signal | What success would mean |
|---|---|---|
| Camera-conditioned image LoRA | Paired source/target renders of the same objects, calibrated cameras, unchanged identity and explicit projection/crop information | Better requested viewpoints without identity drift; still not guaranteed cross-view consistency |
| Joint multiview adapter | Sets of the same object, cross-view training, fixed camera representation, held-out objects | Coordinated images as a set, with measurable geometric consistency |
| Native 3D edit adapter/model | Before/after 3D geometry or latent states, localized edit masks, corresponding images/instructions | Requested shape change with quantified preservation outside the edit |

The camera LoRA is the least ambitious. It cannot be assumed to solve native 3D editing. Geometry-only labels also cannot convey identity, scale, and hidden design by themselves. Depth and normals may be useful conditioning, but include shape information; captions naming angles alone do not enforce projective geometry.

Brian's Blender-rendered data idea is practical for producing controlled camera pairs. The hard part is diverse legally usable assets, material/render variation, exact camera contracts, and evaluation on entirely unseen objects. Split train/test by object, not by angle of the same object. Do not train on our mistaken images as if they were correct labels.

There are concrete precedents: [Qwen Edit 2511 multiple-angle weights](https://huggingface.co/fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA), [a released FLUX 3 angle training example](https://huggingface.co/akhaliq/flux-3-image-klein-angles-lora), and [AI Toolkit's Klein support](https://github.com/ostris/ai-toolkit). [BFL's training guidance](https://docs.bfl.ai/flux_2/flux2_klein_training) favors the undistilled Base model. These show a credible path to a pilot, not a guarantee of our desired consistency.

Training feasibility must start with one actual forward/backward memory measurement at the chosen resolution, optimizer, rank and batch size. Checkpoint size and inference VRAM do not determine training VRAM. Full multiview attention training is substantially different from a small LoRA; the published MV-Adapter training configuration uses multiple GPUs.

Priority remains zero spending. A later paid pilot would require fresh approval and a hard cap. For scale only, [Runpod's reviewed prices](https://www.runpod.io/pricing) list A100 80 GB PCIe at $1.79/hour: 10 GPU-hours would be $17.90; 48 would be $85.92; an illustrative eight-GPU 24-hour job would be $343.68 before storage and other charges. These are arithmetic examples, **not estimates of the hours our training needs** or availability guarantees.

Python/PyTorch would orchestrate the model and training; GPU kernels do most numerical work. A Rust wrapper would not repair an inadequate training objective or automatically accelerate diffusion. Use Rust only for a measured systems bottleneck later.

Recommendation: do not train an adapter in the next implementation. None is necessary to test preservation, explicit part placement and actual geometry/texture control.

**Bounded validation proposal — no tests below have been run**

The next approved implementation should produce one independent workflow with the complete path before broad quality tuning. Preserve current Mumblebox. Prove the proposed additions with existing models; no automatic adapter hunt, new model family or GUI.

Use three deliberately different owned subjects: a small building with a specified rear fixture; a stylized explorer with a specified backpack and shirt-back mark; and a creature with a specified rear horn or other clearly attachable feature. These cover hard surfaces, a character-like object and an organic silhouette. They do not certify realistic anatomy or rigging.

Predeclare the essential visible and hidden features before looking at outputs. Where exact reference geometry exists, use its renders and cameras as controls. Where it does not, report qualitative acceptance, not invented accuracy percentages.

| Check | Success | Rejection |
|---|---|---|
| First mesh | Recognizable whole object; required visible parts present; no collapse or duplicated essential feature | A fundamental source-image feature is missing or distorted; do not conceal it with texture |
| Physical addition | Requested real part at approved location/scale; visible in silhouette and solid geometry from several viewpoints | Merely painted appearance, wrong side, floating attachment, or materially incorrect part |
| Preservation | Base vertices/faces unchanged by scene assembly before export; exported base matches within numerical tolerance; no unintended global regeneration | New missing parts, changed face/body, changed proportions, holes or global drift |
| Surface edit | Correct selected face gets the mark/material; unselected texture regions preserved outside the declared blend border; geometry unchanged | Back-to-front bleed, wrong camera, warped registration, or geometry claim based on a picture |
| Export | Actual saved GLB reopened; all parts, transforms and materials survive; dimensions within 1% of intended export dimensions | Preview differs from file, materials lost, dimensions wrong, non-finite coordinates |
| Finishing | GPU PEC/bake; no new essential-feature loss; retain master and report remaining topology issues | CPU finishing stall, silent fallback, or simplification damage |
| Resources | Fit observed machine without OOM/sustained paging; explicit release between stages; return near idle after job and controlled cancellation | Model accumulation, repeated restart/reboot dependency, no resource recovery |
| Printing claim | Separate topology/solid checks establish the specific export is printable at the chosen scale | Any unchecked mesh; a successful STL save alone is a failure to prove print readiness |

Before GPU quality runs, use a deterministic two-part fixture with different materials and known transforms to test assembly, UV projection, and export round-tripping. These checks should not consume image-generation attempts. They validate delivered behavior, not a new research direction.

**Generation limit:** three initial meshes plus three separately reconstructed parts, with at most three additional reconstruction attempts across the entire test. Maximum nine attempts, including cancellations and technical reruns. At most six optional image-helper outputs total. Existing supplied reference images are preferred. No seed sweep.

**Fallback limit:** if one required edit is non-additive or a part cannot be made acceptable within that cap, perform at most one targeted Blender fallback case after approval of this proposal. Report the time and manual/agent effort separately. A fallback success does not count as automatic Comfy success.

**Promotion condition:** all three cases must pass preservation, placement/material export and resource checks. Each case claimed as successful must pass every essential-feature check. Promote a general three-category route only if all three complete without the fallback. If only two succeed, report a limited two-case result and the unsupported category; do not call it a general solution.

**Stopping condition:** stop once the three cases and the declared export/resource checks are complete, or once the attempt cap is reached, or once the architecture fails a required preservation/hardware condition that cannot be repaired within those limits. Present successful files, failed cases, actual time/memory and the exact limits. Do not continue quality tuning until everything looks perfect. Do not integrate or redesign the existing GUI automatically.

Technical coding repairs can continue before this bounded quality run. Once the quality run starts, do not create unlimited “technical rerun” exceptions that erase its cap. A newly discovered need for a different reconstruction architecture goes back to discussion.

**Remaining uncertainty and what would resolve it**

| Uncertainty | Bounded next evidence | Decision consequence |
|---|---|---|
| Can separate-part reconstruction preserve the requested detail well enough? | The three part cases above, within the attempt cap | Determines scope of automatic additions |
| Can surface projection preserve registration and avoid hidden-face bleed? | Known-camera two-material fixture, then the three cases | Required before offering surface-edit export |
| How much manual placement remains? | Record number of adjustments and time per case | Product usability claim must reflect actual effort |
| Can Nano3D edit a rear surface on this GPU without destroying the accepted base? | Only if explicitly chosen later: one editor-only memory run, one native front control, one rotated/imported rear preservation control | Could replace some fallback editing; currently not a promised capability |
| Can MV-Adapter improve the first mesh for our objects? | Only if selected later: orthographic reconstruction with compatible cameras and one matched baseline, not direct forced Pixal FOV substitution | Would justify a new route only if final geometry improves |
| Can UltraTex improve appearance enough to justify its extra model? | One fixed-geometry texture comparison if existing texturing is the observed bottleneck | Cannot justify a geometry improvement claim |
| Can printing be automated reliably? | Solid/topology checks and a specific repair trial on exported shapes | Separate capability; remains unproven |

These are conditional follow-ups, not an automatic additional research program. The present evidence is sufficient to recommend a practical proposal and clearly state the missing general neural-editing capability.

**Rejected assumptions**

- More generated views are always better.
- A model's angle label is a measured camera.
- Orthographic and perspective cameras are interchangeable after relabeling FOV.
- An orientation/depth adapter contains no shape information.
- A texture editor repairs geometry.
- Saving a preview guarantees the preview's transforms/materials were serialized.
- A MIT README licenses all dependencies.
- Released inference proves a 16 GB Windows implementation.
- A low-rank adapter is automatically cheap to train or transfers between model families.
- A successful mesh container is a printable or game-ready asset.

**Evidence provenance**

Small source snapshots are under [sources/geometry-editing](sources/geometry-editing/). Pins inspected in this pass:

| Repository | Inspected commit |
|---|---|
| Nano3D | 7d20eb6887cb73e3bb4ec349ee27e0b670004512 |
| 3DMorph | 752dcd3cb5e78c6e37a5a60d988bb58d16bb292d |
| VecSet-Edit | c01b025c0715abfd08ad88daaddc81d4a7759ccf |
| Prox-E | 1c65d604acd138063b77b3fdadf2f42fdc4af9ec |
| Instant3dit | e74299f98ca7ceb8dabc46be7dcc59ec89b33677 |
| ObjFiller-3D | 2119006d56164d09923cf053cb1719de223bfb49 |
| MV-Adapter | 4277e0018232bac82bb2c103caf0893cedb711be |
| ComfyUI-MVAdapter | 9d6d8afeff135d81a31f16dde5291d8b40dbb0a4 |
| Era3D | a2ce68da53c0dc4df403112c53692b9ba893a4f0 |
| Pixal3D upstream pipeline | f7cf38429b0bd264f1995f0f8743a88b1c728b94 |

The local Comfy checkout is detached at 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18, with earlier scoped changes in nodes_mesh_postprocess.py, nodes_save_3d.py and nodes_trellis2.py, plus pre-existing comfyui-mcp. These were inspected, not changed by this research. No commits or pushes were made.

**Research completion and the approval decision**

The research stopping condition is met when this report covers the requested evidence and gives either a supported implementation proposal or the remaining feasibility limit and closest usable alternative. It does not require demonstrating a capability that cannot be tested under a research-only instruction.

This report recommends the closest supported local path: **Pixal3D base, explicit geometry additions, surface-specific appearance edits, preserved scene export, and targeted Blender as the one fallback.** The integrated additions remain proposed. General arbitrary neural rear-side editing on this machine remains unproven.

The next decision is whether that honest, more controlled workflow is useful enough to implement. If a fully automatic Comfy-only neural editor is mandatory, do not quietly approve this as equivalent: the evidence does not currently establish that product. Stop here for Brian's discussion and approval.
