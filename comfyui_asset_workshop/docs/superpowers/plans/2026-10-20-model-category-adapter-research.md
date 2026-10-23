# Mumblebox: model, asset-category, and official-adapter research plan

> **Status: PLAN ONLY — research has not started.**
> Written 20 October 2026. Incorporates Brian's discussion through the request to inventory all official adapters and improve first-pass results without chasing perfection.
>
> **For the future researcher:** Use Superpowers executing-plans to track the research tasks after Brian explicitly authorizes this plan. Work directly in this session; no subagents without Brian's permission. Checkboxes below are future research steps, not completed work. Finishing the research does not authorize product implementation.

**Goal:** Determine, with traceable evidence, how each supported image-model variant should handle different game-asset subjects and tasks, and which official publisher components can improve first-pass consistency, correction effort, memory use, and the images supplied to mesh generation.

**Approach:** Reuse the completed model-guidance research. Inventory the publishers' complete relevant component offerings before selecting candidates. Compare category-specific prompting, reference strategies, adapters, and workflow changes, then recommend the smallest understandable set of user choices and the internal specialization needed to support them.

**Research tools:** Existing local reports and source snapshots; official documentation, skills, model cards, release records, repositories, native Comfy workflows, and author-published examples; focused searches of relevant forums and video transcripts. Source inspection and literature review only. No inference, application modifications, new helper programs, or product installation.

**Specification:** The accepted requirements in this document consolidate Brian's conversation. The [earlier research report](../../research/2026-10-20-model-guidance/REPORT.md) supplies the baseline evidence, not authority to override later decisions.

## 1. Intended outcome in plain English

Someone chooses the kind of game asset they want, chooses an image model, supplies a description and/or references, and gets that model's most appropriate supported treatment behind one understandable interface.

The program should use the model's documented terminology internally. People should see familiar asset terminology, helpful examples, and clear next steps. They should not need to learn prompt dialects, adapter formats, or Comfy wiring.

The desired improvement is a more coherent first set of images and an easier path through reviewing, editing, regenerating, and choosing useful views. Ten images are candidates, not a mandatory input quota. Human review remains part of the process.

Brian accepts imperfect AI results and useful correction time. Fifteen minutes was an illustration of an acceptable hands-on process, not a performance promise, benchmark, or required timeout. Do not promise perfect angles, guaranteed anatomy, universal game-ready topology, or print-ready output.

The current workflow has produced useful textured meshes. Preserve that working baseline. This research is intended to make justified improvements, not declare the entire existing system broken.

## 2. Authorization and boundaries

### What is authorized now

- Write and review this research plan.
- Read existing project guidance and the prior research needed to make the plan accurate.
- Save this one plan in the existing project documentation location.
- Stop and let Brian review it.

### What executing this plan would authorize later

Only after Brian approves execution:

- Read official and relevant community sources, including actual examples and failure reports.
- Inspect relevant existing implementation read-only when needed to answer a named question.
- Retrieve small documentation, workflow examples, prompt rules, and evidence snapshots into the research folder.
- Analyze published artifacts without executing downloaded code or workflows.
- Write the research report, source records, inventory, recommendations, and proposed later tests.

### What this plan does not authorize

- Product changes, Comfy workflow rewiring, generation, mesh export tests, benchmarks, or model comparisons run locally.
- Installing skills, models, adapters, nodes, dependencies, services, or browsers. An official skill may be read or archived as evidence without activating it.
- Launching, restarting, closing, or controlling Comfy Desktop or another creative application.
- Changes to configuration, credentials, Hugging Face access conditions, user history, assets, or caches.
- Pinokio development, integrations, monetization, tutorial production, or a new interface redesign.
- Training adapters, curating a community style collection, or expanding the supported image-model menu.
- Commits, pushes, worktrees, or creation of a persistent goal unless separately requested.
- Reopening settled repair work or silently resuming an old goal.

For any later asset work, Brian's existing-instance and visible-work requirements remain binding. This document does not grant a background-generation exception.

## 3. Workspace and baseline

Plan location:

- docs/superpowers/plans/2026-10-20-model-category-adapter-research.md

Existing extension:

- E:/Comfyui-installs/ComfyUI (1)/ComfyUI/custom_nodes/comfyui_asset_workshop

Containing Git checkout:

- E:/Comfyui-installs/ComfyUI (1)/ComfyUI
- Common Git directory: E:/Comfyui-installs/ComfyUI (1)/ComfyUI/.git
- Planning-time HEAD: 63be2f9b82ad0dac88a7ceaa28a9cf3154125a18, detached.
- Planning-time Git status includes unrelated untracked comfyui-mcp/. Preserve it.
- The extension's documentation may be ignored by the containing repository. Saving a file is not a Git commit or publication.

Resolve the safe existing E: paths explicitly. Do not create active state under the legacy OneDrive workspace. Do not relocate the project as part of research.

Read these existing research artifacts once, then refer back only to relevant sections:

- [REPORT.md](../../research/2026-10-20-model-guidance/REPORT.md): previous findings, known limitations, implementation owners, and source links.
- [inventory.json](../../research/2026-10-20-model-guidance/inventory.json): eight exact model profiles and weight identity evidence.
- [sources.json](../../research/2026-10-20-model-guidance/sources.json): pinned source records and existing downloads.
- [implementation-baseline.json](../../research/2026-10-20-model-guidance/implementation-baseline.json): earlier application-file hashes.

Do not rehash large weights or reread every downloaded file merely to begin another research pass. Revalidate a fact if it affects a new recommendation or there is evidence it has changed.

### Supported variants to cover separately

| ID | Current selected variant | Research distinction to preserve |
|---|---|---|
| M01 | Qwen Image 2.1 7B, INT8 convrot | Separate creation/edit guidance and enhancer contracts |
| M02 | Qwen Image Edit 2511, FP8 mixed | Edit-oriented model; full-quality versus Lightning recipes |
| M03 | FLUX.2 Klein 9B base, FP8 | Base-model conditioning and settings |
| M04 | FLUX.2 Klein 9B distilled, FP8 | Distilled model and compatible components |
| M05 | FLUX.2 Klein 9B KV, FP8 | Distinct KV model, reference cache behavior, compatibility |
| M06 | FLUX.2 Klein 4B distilled, FP8 | Separate size/encoder/adapter compatibility and memory tier |
| M07 | FLUX 3 Image Klein base, INT8 convrot | Normal prompt expansion, task contracts, base compatibility |
| M08 | FLUX 3 Image Klein distilled, INT8 convrot | Distilled settings, task contracts, component compatibility |

This table is inherited from the dated baseline, not a new claim of runtime verification. Confirm any changed menu/profile before future recommendations. Do not silently add Turbo, another base size, or a different family.

## 4. Accepted decisions and research questions

The following are requirements, not assumptions that research may quietly replace:

- One simple user experience may select many different internal workflows.
- Every supported exact model variant gets appropriate treatment; changing a filename is insufficient.
- Enhancement and the final generation prompt must agree with the selected model and task.
- Asset categories are candidates for specialization, not proof that separate graphs are needed.
- Familiar gaming terminology belongs in the interface; model-appropriate wording belongs inside the workflow.
- A small category list must be researched, recommended, and explained.
- Category help must be easy to find beside the selector, analogous to model-selection help.
- Front → back → user approval of the pair → remaining angles remains the accepted starting approach.
- Extra references may describe identity, anatomy, equipment, materials, symbols, or specific parts.
- Human review, per-image corrections, selective inclusion, and regeneration remain essential.
- Camera-control LoRAs remain optional, with understandable limitations.
- Suitable official category components should be selected automatically in a future preset after compatibility and benefit are established.
- Optional style choices may include publisher-released styles only if suitable official offerings exist.
- Inventory all official adapters and relevant supporting components for the selected models, including angle/consistency helpers. Do not start with a shortlist that filters out unfamiliar capabilities.
- Community examples may inform methods and the existing optional camera routes. They must not be relabeled official or used to fill an empty official category/style catalog.
- Memory, loading/unloading, and time matter alongside image quality.
- The intended hardware is RTX 4080 SUPER 16 GB VRAM with 64 GB RAM; the proposed minimum tier is 8 GB VRAM. System RAM requirements for that tier still need evidence.
- Outputs serve game assets and potentially printing; these uses have distinct downstream requirements.
- Preserve the working baseline. Avoid unrelated redesign, indiscriminate duplication, and endless experimentation.

The earlier report's proposed three subject labels are provisional. This plan supersedes that tentative menu with a researched taxonomy. It also adds the complete official-component inventory and official-style investigation.

## 5. Evidence method and source coverage

### 5.1 Source order

1. Original publisher's official documentation, model cards, skills, technical reports, release announcements, and maintained repositories.
2. Actual publisher example code/graphs and supported integration documentation, including native Comfy examples.
3. Component authors' own documentation, workflows, demonstrations, and issue responses.
4. Firsthand user reports, reproducible forum discussions, and creator videos/transcripts, used as observations or leads with attribution.
5. Secondary summaries only to locate the owning source; do not let a recap replace the source for a technical recommendation.

For taxonomy, consult established game-engine documentation and asset-library category systems directly. Examine at least two independent ecosystems, such as Epic/Fab and Unity, and relevant professional environment/character workflow documentation. Their labels are evidence of familiarity, not proof a generation category is technically useful.

### 5.2 Publisher inventory coverage

For both Qwen and Black Forest Labs:

- Traverse the official model/adapter collections, model repositories, documentation indexes, supported-tools catalogs, skills repositories, release notes, and linked official projects.
- Resolve publisher aliases and official hosting accounts using links from the publisher's own sites/repositories.
- Include current and relevant legacy offerings needed to disambiguate the user's recollection of official building/person/style tools.
- Record every potentially applicable offering before deciding whether to use it.
- Record older-family or API-only items in an exclusion table when their names could otherwise be mistaken for local support.
- Follow pagination and repository links to closure within these declared official surfaces. Record inaccessible/private/deleted pages and gaps.
- A popular community LoRA, publisher retweet, model-hub search result, or Comfy-Org conversion does not by itself prove original-lab authorship.
- An inventory can be comprehensive as of its recorded date and searched surfaces; it cannot guarantee discovery of unpublished or inaccessible releases.

### 5.3 Search process

For each model family and exact variant, use the official inventories first, then targeted searches for:

- asset type, person/character/humanoid, creature/animal, vehicle, architecture/building, prop, organic object;
- reference consistency, identity preservation, rotation, viewpoint, camera, multiview, underside, pose preservation;
- official adapters, LoRA, control, edit/inpaint, structure/depth/edges, reference/identity, prompt enhancement, style, acceleration/distillation, cache and memory;
- known failures, compatibility issues, unsupported modes, and combinations with quantized weights.

These are search terms, not assertions that a component exists for every capability.

Use the previous report's links as starting points. Inspect newer official releases and relevant recent discussions first, then older foundational guidance where necessary. No arbitrary requirement to find a fixed number of videos or sources per model. Use video transcripts for searchable instructions and inspect the actual published workflow or relevant frames when a claim depends on visual evidence.

For each important recommendation, seek the strongest owning-source support and check for contradictory guidance or reported failures. Do not manufacture disagreement where only one primary source exists.

### 5.4 Evidence labels

Keep two separate fields:

- **Origin:** original publisher; integration maintainer; community component author; firsthand user; researcher inference.
- **Proof:** documented claim; source-inspected behavior; published demonstration; earlier local observation; untested proposal.

Add high/medium/low confidence with a short reason. Confidence in a documented API or wiring contract does not establish image quality. A successfully loaded LoRA does not prove benefit. A visually attractive example does not establish angle accuracy.

Record URLs, source owner, publication/update date if known, retrieval date, exact model and component revisions, and the claim supported. Cite short relevant passages or paraphrases rather than reproducing entire copyrighted guides.

### 5.5 Negative findings and search stopping rule

For each question, report one of:

- Supported recommendation.
- Relevant documented method with benefit needing local validation.
- No meaningful distinction supported by the searched evidence.
- No official compatible component found in the declared surfaces.
- Conflicting, inaccessible, or insufficient evidence, with a specific later check.

After checking the owning documentation, official inventory, exact-variant examples, and targeted firsthand reports, stop when additional results repeat known claims or no longer change the decision. Reopen a question only when a new primary source or a concrete contradiction could alter the recommendation.

There is no shortlist cap on the official inventory. Depth is bounded by completing the declared official surfaces, not by endlessly searching the entire internet.

## 6. Research outputs and record ownership

Create these only when research execution is authorized:

- docs/research/2026-10-20-category-specialization/REPORT.md — the one human-readable report and implementation recommendation.
- docs/research/2026-10-20-category-specialization/evidence.json — structured model/category findings, complete official-component inventory, exclusions, coverage, and unresolved questions.
- docs/research/2026-10-20-category-specialization/sources.json — source URLs, ownership, revisions, dates, and paths/hashes for any downloaded evidence.
- docs/research/2026-10-20-category-specialization/sources/ — only useful small snapshots, examples, or diagrams that add evidence beyond an accessible link.

The directory date ties this work to the plan. Record actual future retrieval dates; never backdate research.

Do not create one document per category, model, or source. Maintain evidence once and summarize it in the report with stable IDs. Do not download model weights, giant repository archives, or whole video libraries for a literature review.

### Required evidence fields

**Finding:** ID, research question/task, exact model IDs, task, category/subtype, claim, recommendation, origin, proof, confidence/reason, source IDs, contradictory evidence, limitations, later test.

**Official component:** ID, publisher/author verification, name, kind, current/legacy status, version, model compatibility, task/category applicability, purpose, local/API availability, required encoders/nodes/dependencies, trigger/prompt format, settings/strength, reference roles, enhancer interaction, composition order/conflicts, file size, resource evidence, license/gating, proposed loading lifetime, recommendation, source IDs.

**Inventory coverage:** publisher, surface URL, sections/pages/collections inspected, date, discovered component IDs, excluded IDs and reasons, unresolved access gaps. Distinguish offering-level families from per-version artifacts and conversions without hiding compatibility differences.

**Category:** proposed UI label, definition, examples, boundary cases, internal subtypes, useful behavior differences, evidence, help copy, model-specific mapping, and rationale for merge/separation.

**Model/category cell:** model ID, category, supported task, treatment level, relevant components, confidence, evidence IDs, unresolved test. Empty cells are not acceptable; use an explicit evidence status.

## 7. Review focus

These risks must be answered in the named tasks:

1. **A broad category silently changes the intended subject.** Robots, statues, modular pieces, or organic props get the wrong anatomy or fabricated details. Address in Tasks 3–5 and 13.
2. **An adapter is official but belongs to a different model or mode.** Similar names conceal size, base/distilled, quantization, API/local, or task differences. Address in Tasks 1, 8, 9, and 11.
3. **Good-looking images disagree geometrically.** Wrong angle, duplicated subjects, mirrored side details, incorrect counts, or changed pose survive because only image beauty was evaluated. Address in Tasks 6, 7, 12, and 15.
4. **Automatic component choices override explicit user controls or exceed resources.** Stacking, strength, model changes, and stage transitions cause surprising behavior. Address in Tasks 8–11 and 14.
5. **Research claims exceed the evidence.** No official resource found becomes “none exists”; an example becomes a reliability claim; 16 GB success becomes 8 GB support. Address through the evidence protocol and Tasks 15–16.

## 8. Work sequence

Execution order: **1 → 2 → 3 → 8 → 4 → 5 → 6 → 7 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16**. Task 8 deliberately comes before specialization recommendations: complete the official inventory before choosing components. The task numbers are stable references for coverage and review. No delegated or parallel agent work is implied. Record each finding once; cross-reference it across tasks.

### Task 1 — Freeze the baseline and unanswered questions

**Inputs:** Previous report, inventory, source index, accepted requirements above.
**Produces:** Dated scope, model table, inherited-versus-new findings, and a question register.

- [ ] Read the baseline report and extract only the established contracts and unresolved issues relevant to specialization.
- [ ] Confirm the eight profile identities and whether the existing inventory still describes the menu using minimal read-only inspection if necessary.
- [ ] Separate earlier local image observations from source research and from hypotheses.
- [ ] Record which previous facts need refreshing and why.
- [ ] Record latest decisions that supersede earlier tentative category names or assumptions.

**Done when:** All eight variants and all new questions have an owner in this plan; no previous result is mislabeled as a fresh test.

### Task 2 — Map official guidance and category-related evidence

**Inputs:** Task 1; existing source collection.
**Produces:** Exact-model guidance map with source gaps and conflicts.

- [ ] Locate the current publisher guidance and official skills for each family/variant; establish actual scope.
- [ ] Extract guidance on subject classes, prompt structure, image editing, reference roles, limitations, and relevant training/evaluation domains.
- [ ] Search for category-specific official examples and firsthand demonstrated workflows.
- [ ] Separate publisher rules from our own proposed asset-preservation requirements.
- [ ] Note when models share guidance and when variant-specific conditions prohibit inheritance.

**Questions:** Does the publisher distinguish people, anatomy, architecture, manufactured objects, or styles? Does the guidance differ by task more than by subject? Are apparent category gains attributable to references, different settings, or an adapter instead?

**Done when:** Each exact model has guidance or an explicit gap; “official skill” is never used as a synonym for any online guide.

### Task 3 — Research gaming terminology and a small category taxonomy

**Inputs:** Task 2, direct engine/library taxonomy sources.
**Produces:** Provisional category cards and boundary-case decisions.

- [ ] Compare real asset-library and engine terms for characters, creatures, vehicles, props, environments, structures, modular kits, and set pieces.
- [ ] Distinguish a subject category from a usage role, scene grouping, visual style, or export target.
- [ ] Test whether “set piece” is understandable and technically meaningful for this single-asset pipeline.
- [ ] Map representative ambiguous examples: robot character, robot statue, dinosaur, tree, chair, weapon, spacecraft, ruined tower, corridor wall, interior set, and large decorative landmark.
- [ ] Recommend the fewest categories that improve instructions or explain a meaningful workflow difference; merge those that do not.
- [ ] Define a clear route for unusual subjects without requiring many submenus.

**Done when:** Every proposed category has examples, exclusions/boundaries, rationale, and an explanation of what choosing it changes. Candidate labels from the conversation are not automatically the final menu.

### Task 4 — Decide the useful depth of model/category specialization

**Inputs:** Tasks 1–3 and the official inventory from Task 8.
**Produces:** Complete model-by-category matrix and illustrative internal prompt mappings.

- [ ] For each exact model and candidate category, identify the important invariants and task-specific treatment.
- [ ] Examine anatomy/pose/identity for characters and creatures; dimensions, openings, counts, symmetry, and side assignments for manufactured assets; natural form for organic props.
- [ ] Compare guidance for text-only creation, image-led creation, angle generation, whole-image correction, and masked edits.
- [ ] Identify whether the evidence supports no change, different instructions, different settings/reference handling, an optional component, or a separate graph.
- [ ] Write illustrative prompt translations only where guidance supports them; label them untested.
- [ ] Inspect whether model terminology and UI labels should differ and whether the description can supply internal subtypes without more visible controls.

**Done when:** Every model/category cell has a treatment recommendation or an honest unknown. No universal final prompt is proposed merely for convenience; no full workflow is duplicated merely because a category exists.

### Task 5 — Model-aware enhancement, auto-description, and design facts

**Inputs:** Tasks 2–4; earlier enhancer research.
**Produces:** Task/variant enhancer recommendations and preservation rules.

- [ ] Compare the exact publisher enhancer, system prompt, input/output contract, and memory needs with the existing helper.
- [ ] Determine how enhancement should preserve requested counts, side details, identity, intended style, and explicit user wording.
- [ ] Define how visible observations, user-specified requirements, and proposed unseen details remain distinguishable.
- [ ] Investigate how a consistent subject description and side assignments should feed angle-specific prompts without forcing every detail into every image.
- [ ] Check interactions with adapter trigger grammar, prompt expansion exceptions, and image-reference labels.
- [ ] Determine whether category/style/model/reference changes require regenerating prepared instructions; avoid silently reinterpreting an approved design.
- [ ] Specify model-aware enhancement examples for text-only and image-led input, including an edit-only model selected without an initial image.

**Done when:** The recommendation covers both the Enhance button and the later final-prompt construction. Auto-description does not invent unseen facts, and a borrowed system prompt is not represented as an equivalent specialized checkpoint.

### Task 6 — Approved anchors, additional references, and sequence

**Inputs:** Tasks 2, 4, 5.
**Produces:** Per-model reference policy and a clear list of unverified combinations.

- [ ] Assess evidence for front generation, front-to-back generation, approval of both, and two-anchor generation of remaining angles.
- [ ] Address uploaded images that are already three-quarter views, inconsistent front/back pairs, and reference images that depict accessories rather than the entire subject.
- [ ] Record supported versus practical reference counts, ordering, resolution, naming, and roles.
- [ ] Compare using the approved pair alone with adding relevant approved side views; examine cumulative drift from feeding every previous image forward.
- [ ] Investigate how symbols, face references, clothing, backpacks, and part references should affect only their intended features.
- [ ] Record any one-reference component conflict explicitly; never silently discard an approved back or a user reference.
- [ ] Separate reproducible seeds from subject identity. Find whether copying an initial seed has documented benefit for any exact route.

**Done when:** Each variant has an explicit reference strategy with limitations and later comparisons, preserving the accepted human approval sequence.

### Task 7 — Angles, elevations, and optional camera methods

**Inputs:** Tasks 2, 4, 6.
**Produces:** Camera-method comparison tied to exact models and asset types.

- [ ] Define camera-versus-object rotation, viewer-versus-subject left/right, framing, distance, elevation, and projection conventions.
- [ ] Examine how to request visible surfaces and expected occlusions without contradicting a camera adapter's supported angles.
- [ ] Investigate front/back, side, quarter, overhead, underside, and low-rear failures by subject type.
- [ ] Review official viewpoint/consistency components from the inventory, and the already-known optional community camera routes with their provenance intact.
- [ ] Compare text/reference methods, compatible adapters, and relevant visual/geometry guidance only where they address a named failure.
- [ ] Check whether joint multiview or contact-sheet methods offer credible evidence relevant to current models; label another model family as a separate proposal, not an incidental replacement.
- [ ] Record documented coordinate/angle support separately from measured or merely illustrated camera accuracy.

**Done when:** Each route has supported controls, known subject limitations, reference requirements, and a camera-off path. No false guarantee that every named angle is correct.

### Task 8 — Inventory every official adapter and supporting component

**Inputs:** Task 1; publisher coverage protocol.
**Produces:** Complete dated publisher inventory, compatibility table, and exclusions.

This is an inventory-first task. Do not limit discovery to style, category, or camera keywords.

- [ ] Enumerate the official surfaces and collections for Qwen and BFL; record coverage and resolve all relevant linked offerings.
- [ ] Inventory official LoRAs, other adapters, specialized checkpoints, reference/identity conditioning, structure/camera tools, editing/inpainting components, prompt helpers, and performance components wherever offered.
- [ ] Record type accurately: a full model, cached computation, encoder, API feature, and LoRA are not interchangeable kinds of adapter.
- [ ] Verify publisher authorship and original artifacts separately from conversions, mirrors, and community derivatives.
- [ ] Map each offering to all applicable exact selected variants and tasks; retain clear exclusions for other model generations or unsupported local modes.
- [ ] Capture documented purpose, quality claims, settings, prompt rules, dependencies, availability, licensing, resource cost, and demonstrated failures.
- [ ] Classify every item: useful candidate, unnecessary for scope, incompatible, or needs evidence. Record the reason even for exclusions.
- [ ] Identify which components could improve first-pass angle/identity consistency even if their names do not mention cameras.
- [ ] Recommend automatic category use only when exact compatibility and relevant benefit are established; flag local validation required before making it a product default.

**Done when:** The entire declared official inventory is accounted for, every item has a disposition, and inaccessible surfaces are documented. A failure to find a category LoRA is a valid result, not permission to substitute a community one.

### Task 9 — Official styles and component combinations

**Inputs:** Tasks 4, 8.
**Produces:** Optional official-style recommendations and a compatibility/conflict table.

- [ ] Identify publisher-released style offerings, if any, and verify exact model compatibility and rights.
- [ ] Distinguish artistic style from subject specialization, quality enhancement, prompt guidance, and architectural/rendering terminology.
- [ ] Evaluate whether a small style selection adds useful capability to asset creation without impairing consistency.
- [ ] Research composition of category, style, camera, acceleration, and user-selected LoRAs: supported order, strengths, cumulative effects, and documented conflicts.
- [ ] Specify how explicit user choices should be preserved when an automatic category preset selects a component.
- [ ] Recommend what to display, what to disable only for real incompatibility, and what needs a clear caveat.
- [ ] If no suitable official style offering exists, recommend no bundled style LoRA; do not invent a catalog.

**Done when:** Any proposed style selection is sourced, optional, and separate from asset type. Unknown stacking behavior remains unverified rather than assumed safe.

### Task 10 — Editing and masks as part of the human correction path

**Inputs:** Tasks 4–9; existing editing mechanisms in the prior report.
**Produces:** Model/task editing guidance and practical limitations.

- [ ] Compare methods for recoloring, replacing a part, correcting a count, repairing anatomy, and preserving angle/pose.
- [ ] Examine small selections, soft edges, selected-area versus whole-object context, and reference roles during an edit.
- [ ] Cover both uploaded/generated initial images and every generated angle.
- [ ] Determine how an approved design change should affect other views and invalidate obsolete instructions; separate a local image correction from an intentional whole-design change.
- [ ] Identify official editing/structure helpers that could improve the selected area while preserving the existing outside-selection behavior.
- [ ] State limitations clearly: unchanged outside pixels do not establish a geometrically correct edit, and one corrected view does not automatically repair other views.

**Done when:** Recommendations support a useful iterative correction process without adding an unrelated editor redesign.

### Task 11 — Memory, automatic loading, portability, and licensing

**Inputs:** Tasks 5–10; existing memory findings.
**Produces:** Component lifetime and hardware feasibility recommendations.

- [ ] For each recommended component, record download size separately from peak runtime VRAM/RAM evidence.
- [ ] Map when to load, reuse, offload, release, or replace enhancement, image, reference-cache, adapter, and mesh-stage resources.
- [ ] Investigate supported native Comfy memory controls before recommending a new helper layer.
- [ ] Check 4080 SUPER/Ada compatibility, selected quantizations, low-memory reference handling, and sensible quality/speed choices.
- [ ] Assess the proposed 8 GB VRAM tier, including system RAM/offload requirements and what remains unmeasured.
- [ ] Clarify adjustable memory settings: planning headroom or offloading preferences are not automatically hard process-wide limits.
- [ ] Record model/adapter/node versions, local installation paths, first-use download requirements, gates, access conditions, and offline reuse implications.
- [ ] Check official license text for local use, commercial use, generated outputs, distribution/download arrangements, and required notices; flag ambiguity for review rather than giving an unsupported legal conclusion.
- [ ] Recommend cache ownership and cleanup that releases temporary resources while preserving user assets, references, selected downloads, and reproducibility.

**Done when:** Recommendations explain what a user gains and gives up. No 8 GB claim is based solely on weight size or artificially reserving memory on a 16 GB card. Research does not accept terms or download weights.

### Task 12 — Human selection, mesh inputs, games, and prints

**Inputs:** Tasks 4, 6, 7, 10; existing mesh routes.
**Produces:** Input-quality/review guidance and model-specific mesh constraints.

- [ ] Verify relevant view-count, camera, image-format, segmentation, framing, and reference requirements of the currently used Pixal3D/Trellis routes where they affect the new recommendations.
- [ ] Distinguish ten candidate output views from the number of references passed into an image model.
- [ ] Assess evidence for coherent subsets versus adding conflicting images; avoid declaring a universal best count.
- [ ] Define useful checks: same subject/pose/proportions, correct parts and markings, distinct useful coverage, side assignment, duplicates, crop/background problems, and symmetry that legitimately makes views similar.
- [ ] Draft clear advice on keeping, editing, regenerating, or excluding a view.
- [ ] Explain that attractive shading or sharper textures do not guarantee cleaner geometry or topological suitability.
- [ ] Identify preparation differences relevant to games and prints, while distinguishing downstream rigging/LODs/UVs/collision and watertightness/wall thickness/scale from image-generation quality.

**Done when:** The report explains the human's role and limitations without requiring all ten images or promising a finished game/print asset from a successful run.

### Task 13 — User terminology, category help, and internal translation

**Inputs:** Tasks 3–12.
**Produces:** A small recommended menu, help content, and per-model translation examples.

- [ ] Select final proposed game-facing labels based on familiarity and useful distinctions; include merge/reject rationales.
- [ ] Write each category card: plain definition, familiar examples, ambiguous cases, and what selection changes.
- [ ] Draft the nearby “Help me choose” explanation for Asset type, using the existing model-help interaction as the reference.
- [ ] Map user labels to internal subject descriptions and model-specific instructions without exposing model jargon.
- [ ] Address “Which model should I use?” recommendations by category only when supported by comparative evidence.
- [ ] Describe automatically selected official components in plain language, including why they were selected and how the user can override them.
- [ ] Keep style optional and separate. Avoid extra dropdowns for distinctions that can be inferred reliably from an explicit description.
- [ ] Recommend what should happen when category and description conflict; preserve user intent rather than silently changing the subject.

**Done when:** A new user can understand the choices, while experienced asset creators recognize the terminology. Research produces copy recommendations, not UI code or mockup implementation.

### Task 14 — Fit recommendations into the existing workflow

**Inputs:** Tasks 4–13; prior source inspection.
**Produces:** A minimal internal-routing recommendation and change-impact map.

- [ ] Identify what can stay shared and what must vary by exact model, task, category, style, and component.
- [ ] Inspect the existing owning layer only where necessary: profiles/model inventory, recipe assembly, enhancement/final prompt preparation, reference state, memory ownership, and visible help.
- [ ] Distinguish a changed instruction, parameter preset, reference strategy, component selection, and genuinely different graph.
- [ ] Address prepared-prompt/cache invalidation on relevant changes and capture reproducibility needs: final prompt, model/component versions, strengths, seed, references/revisions, settings.
- [ ] Map each recommendation to an existing owner or name the precise missing capability; do not design an abstraction framework or rewrite unrelated code.
- [ ] Explain how automatic category components, optional camera control, official styles, and user-selected LoRAs coexist without silent substitution.
- [ ] Separate high-confidence implementation candidates from experiments and unsupported alternatives.

**Done when:** The report gives a reviewer a concrete route forward while preserving the working UI, supported models, and accepted front/back process. Research does not become an implementation patch.

### Task 15 — Design bounded later comparisons

**Inputs:** Every substantive finding and unresolved question.
**Produces:** A validation protocol only; no test runs in this research.

- [ ] Choose representative subjects spanning proposed categories: clothed humanoid, distinctive creature, asymmetric vehicle, small architectural piece, and a non-crate prop; include an organic and a symmetric control where they answer a question.
- [ ] Define isolated comparisons: category instructions versus baseline; compatible official component on/off; selected style combinations; front/back versus another supported reference arrangement; difficult camera method.
- [ ] Control the exact variant, settings, source pair, resolution, prompts, and recorded seed. State when a comparison is not like-for-like.
- [ ] Track first-pass usable views, correct coverage, identity/geometry consistency, part counts, duplicates, useful edits, user interventions, elapsed generation/loading time, and memory.
- [ ] Separate first-pass quality from quality after human corrections, and hands-on time from unattended compute time.
- [ ] Use a small repeat across recorded seeds where needed to avoid declaring success from one lucky image. Set the question, repeat count, and acceptance criterion before each future run.
- [ ] Propose text/prompt-contract checks before GPU trials and selected end-to-end textured-mesh comparisons only after the input questions are answered.
- [ ] Include mechanical later checks for model/category switching, automatic component visibility, override behavior, memory release, and history provenance.
- [ ] Set stop rules for each experiment: demonstrated useful improvement, a documented limitation, or a named unresolved question requiring a new decision.

**Done when:** Every uncertain product-changing recommendation has a finite test that could support or reject it. The plan does not require all combinations of every category, style, adapter, and seed.

### Task 16 — Synthesize, audit, and stop

**Inputs:** Tasks 1–15.
**Produces:** Complete source-linked report and research records.

- [ ] Write the plain-English recommendation first: what is worth doing, what should remain shared, what is unsupported, and what still needs tests.
- [ ] Complete the category list, model/category matrix, official inventory, exclusions, style recommendations, optional-camera guidance, and hardware table.
- [ ] Include the internal wording mappings, help copy, minimal change map, and validation protocol.
- [ ] Check every accepted requirement and review-focus risk against a specific finding or explicit unknown.
- [ ] Resolve inconsistent names, compatibility statements, dates, provenance labels, source references, and claims of official authorship.
- [ ] Verify that evidence records parse, source links/paths are recorded, and summaries do not imply local tests that did not happen.
- [ ] Confirm the research did not modify application files or user assets; distinguish that file-integrity evidence from runtime proof.
- [ ] Deliver the report and stop for Brian's review. Do not install, implement, generate, or automatically start the later tests.

**Done when:** The completion conditions below are satisfied, including explicit negative findings where the evidence does not support specialization.

## 9. Required final report structure

Keep one readable report with linked detail:

1. Plain-English recommendations and the decisions Brian needs to make.
2. Scope, dates, exact supported variants, reused baseline, and what was not tested.
3. Recommended small category list, definitions, ambiguous examples, and rejected/merged alternatives.
4. Complete model-by-category treatment matrix.
5. Model/task-specific prompting, enhancement, and reference recommendations.
6. Complete official-component inventory summary, applicability, exclusions, and provenance coverage.
7. Automatic category presets, optional official styles, camera choices, and combination conflicts.
8. View-generation sequence, human review, correction, and useful mesh input selection.
9. Resource/loading/portability/licensing implications.
10. User-facing help and internal translation examples.
11. Minimal existing-workflow changes to consider after approval.
12. Bounded validation plan, limitations, unresolved questions, and source index.

Useful table columns:

- **Model/category:** model, category, task, treatment level, component, reference policy, evidence/confidence, later check.
- **Official component:** publisher, item/version, kind, exact compatibility, purpose, availability, disposition/reason, resource/license notes.
- **Category help:** UI label, definition, examples, difficult boundary, effect, internal terminology.
- **Recommendation:** proposed change, expected benefit, evidence, uncertainty, resource cost, owning layer, validation.

Do not label a category “best for people” or “best for buildings” because of one attractive example. Use conditional, evidence-backed descriptions.

## 10. Requirement coverage map

| Requirement | Owning tasks |
|---|---|
| All eight exact supported variants, preserved | 1, 2, 4, 14 |
| Official skills/guidance, community demonstrations, failures | 2; Section 5 |
| Whether category differentiation matters at all | 3, 4, 15 |
| Small gaming-oriented category list, including set-piece question | 3, 13 |
| Familiar UI names mapped to model-appropriate instructions | 4, 13 |
| Easy-to-find category help and model help | 13 |
| Creation/edit/angle task distinctions | 4, 5, 7, 10 |
| Model/category-aware Enhance and Auto describe | 5 |
| Hidden sides, required parts, and design-fact preservation | 4, 5, 6 |
| Approved front/back pair and additional reference roles | 6 |
| Accumulated references and seed question | 6, 15 |
| Exact camera wording, difficult elevations, geometry guidance | 7 |
| Camera control optional with limitations | 7, 9, 13 |
| All official adapters/supporting components inventoried | 8; Section 5.2 |
| Official angle/consistency helpers included | 7, 8 |
| Automatic category component use when justified | 8, 11, 14 |
| Official-only optional style offerings | 9 |
| Category/style/camera/user-LoRA combinations | 9, 14 |
| Mask editing for initial and angle images | 10 |
| Human selection, incomplete sets, ten candidates not a quota | 12, 13 |
| Game and print preparation distinction | 12 |
| Load/offload, adjustable memory, 16 GB and intended 8 GB tier | 11 |
| Portability, licenses, downloads, cache ownership | 11 |
| Shared implementation versus genuine separate workflows | 14 |
| Varied subjects, correction effort, no perfection guarantee | 15 |
| Preserve working baseline; avoid drift and churn | 1, 14, 16; Sections 2 and 11 |
| Research report and clear stopping point before implementation | 16; Section 11 |

## 11. Completion conditions and anti-churn rules

The future research is complete only when:

- All eight exact variants are covered and every recommended category has a disposition for each model.
- Official publisher surfaces have been inventoried to the declared boundaries, with every identified component classified and gaps disclosed.
- Official category, style, angle, identity, editing, structural, prompt-helper, and performance opportunities have been considered where offerings exist.
- A small category menu is recommended or the evidence explains why a distinction should be merged/omitted.
- UI labels, category help, and model-specific internal wording are connected with understandable examples.
- Automatic category use, optional camera control, optional official styles, and user overrides have compatible recommendations.
- Enhancement, references, masks, mesh input selection, and memory implications are addressed.
- Important claims have exact sources and evidence labels; uncertain claims have bounded later tests.
- The report distinguishes expected improvements from demonstrations and earlier/local proof.
- No product implementation or generation was performed under research authorization.
- Brian receives one clear recommendation package for review.

Do not require proof of perfection or a LoRA for every category to finish. “No suitable official component found” and “no evidence justifies a separate graph” are useful completed findings when the search coverage is documented.

Do not restart the plan because a new source appears. Attach it to the existing question and update the affected recommendation. Do not pursue unrelated models, UI redesigns, new integrations, broad training projects, or every interesting video.

When executing later, narrate useful findings approximately every minute during active work: what question is being answered, what evidence changed the recommendation, and what remains uncertain. Answer Brian's questions while preserving the agreed scope. A direct stop instruction takes precedence.

If a source is unavailable, record the exact gap, try the owning repository or published archive, and continue other questions. Do not convert an unavailable page into an unsupported conclusion.

Research completion leads to review. Implementation, installation, benchmarks, visual Comfy tests, and a future goal require a separate explicit instruction.

## 12. Planning review record

This plan was prepared using the Superpowers planning structure, adapted to Brian's explicit research-only request: checkable tasks, named inputs/outputs, evidence checks, requirement coverage, review risks, and a completion boundary.

The existing conversation supplies the design brief. It does not need another round of speculative product design. The standard implementation-plan steps for writing code, running tests, committing, and dispatching workers do not apply to this deliverable.

Planning review checked that:

- Latest additions include the complete official inventory, official angle helpers, automatic useful category components, and official-only styles.
- The user's gaming terminology remains separate from the model's prompting terminology.
- A bounded, imperfect but useful human correction process is included in the success definition.
- The prior research is reused, while tentative older category names do not override current decisions.
- No evidence collection, model installation, inference, product edit, or active-goal creation is authorized by this planning task.

**Next action after delivery:** Brian reviews this document. Do not execute its unchecked research steps until he says to begin.

