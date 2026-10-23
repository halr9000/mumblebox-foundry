# Mumblebox applied research: governing plan

Started 2026-10-21 America/New_York; research may continue into 2026-10-22 UTC. This plan governs the new research goal. It supplements, critically reviews, and may supersede recommendations in `../2026-10-21-mesh-first-research/`; it does not change product code.

## Intended result

Find the strongest practical, evidence-backed route to an accurate game or print mesh directly from Mumblebox, before Blender correction. Produce a comprehensive but understandable report and an actionable next-iteration recommendation, including serious custom engineering/training options when existing tools leave a measurable gap.

## Accepted scope and constraints

- Windows, 16 GB VRAM, 64 GB RAM. Start with Brian's machine; portability and honest model-specific support remain requirements.
- Spending target is $0. Longer local work is acceptable. Research paid alternatives only as bounded, priced contingencies; do not buy or launch anything.
- Research and read-only source inspection only. No product changes, installs, model/dataset downloads, image/mesh generation, training, paid jobs, or Pinokio development.
- Save research on E:. No SwarmUI or D: access, OneDrive output, or unsolicited subagents.
- Relevant current families: Qwen Edit 2511, Qwen 2.1, Klein 4B and 9B, FLUX 3, Pixal3D, TRELLIS and justified alternatives. SDXL/SD2.1 are excluded deployment choices; their research can inform architecture.
- Brian's ideas are candidates, not mandatory architecture: no imposed number of views, contact sheet, two-pass scheme, shared-frame attention, custom training, or VLM planning.
- Preserve useful existing work. Distinguish what is already wired from what is tested, broken, inferred, proposed, or obsolete.
- Trace important claims to papers, author code, actual graphs, cards, licenses and training configurations. Practitioner posts and recent videos are leads, not proof of performance.
- Account for compatible projection, framing, cameras, conditioning formats, model variants, all component licenses, GPU/RAM lifetime and GPU finishing.
- Include Brian's added NVIDIA DLSS question: distinguish super resolution, ray reconstruction, frame generation and DLSS 5 neural rendering; investigate their actual inputs, current authorized SDK availability, GPU support, licensing, geometry versus appearance effects, and whether they help previews, guide renders or mesh accuracy. Also compare relevant deterministic rendering/denoising alternatives. Do not confuse a sharper rendering with a more accurate mesh.
- Include Brian's added independent-reimplementation option. Use Reverse Engineer Anything guidance when needed for read-only architecture analysis. Distinguish implementing a published method from copying restricted code, using restricted weights/data or bypassing SDK restrictions. For a unique useful component, assess a genuinely independent implementation and any retraining required; compare maintenance, performance, licensing and evaluation costs against permitted existing options. No reverse-engineering circumvention, binaries or product implementation is authorized in this research phase.
- Include Brian's added broader NVIDIA/library request: assess practical camera, rendering, geometric optimization, synthetic-data and acceleration building blocks, and explain how they could work together within Comfy. Keep custom adapters open as evidence-backed options; distinguish ordinary integration, training and new architecture. Do not add technologies solely because they are available.
- Communicate overall progress, concrete findings, limitations and next questions. Avoid repeated reorientation and unrelated redesign.

## Decision questions and work packages

| ID | Question to resolve | Required evidence/deliverable | Status |
|---|---|---|---|
| R1 | What did the existing implementation and experiments actually establish? | Complete prior report/register review; narrow current-source checks; superseded assumptions identified. | Answered; synthesis saved |
| R2 | Can camera and framing errors be measured or reduced reliably? | Calibration conventions, pose/camera estimators, deterministic fitting, limitations with generated views; include cuboids, landmarks, skeleton/body fitting. | Answered; synthesis saved |
| R3 | Which current image routes provide useful structure and identity conditioning? | Model-specific actual graphs/code, control and reference roles, expected map conventions, supported variants; optional camera LoRAs. | Answered; synthesis saved |
| R4 | Is there a better integrated reconstruction or joint-view route? | Current released methods, code/weights availability, fit for hardware/licensing; compare against clean single-image reconstruction. | Answered; synthesis saved |
| R5 | Can a visual-language model plan hidden surfaces or check consistency usefully? | Empirical limitations, feasible local model, visible facts versus designed inventions, concrete precedent and testable role. | Answered; synthesis saved |
| R6 | What custom components are worth building, and what would each actually require? | Gap, precedent, mechanism, reusable implementation, engineering versus training, evidence status and smallest decisive experiment. | Answered; synthesis saved |
| R7 | Can useful adapters be trained locally for $0? | Compatible trainers/configs, memory methods, data/rights, camera/pose encodings, training objectives, validation splits, realistic feasibility and paid fallback boundaries. | Answered; synthesis saved |
| R8 | What improves mesh quality after reconstruction without concealing bad geometry? | Segmentation, normal/silhouette refinement, topology, thin parts, materials, game/print export and GPU finishing. | Answered; synthesis saved |
| R9 | What can safely coexist on this machine and in a shareable product? | Stage lifetimes/offload/cache plan, Windows/kernel risks, licensing matrix, source/weight/output distinctions, compilation only for evidenced bottlenecks. | Answered; synthesis saved |
| R10 | Which complete route should the next iteration follow? | One coherent recommendation and fallback, keep/repair/replace/add decisions, rationale and category-specific exceptions. | Answered; synthesis saved |
| R11 | What finite experiment would settle whether it works? | Varied subjects, baselines, fixed variables, geometry/usability/resource measures; explicit promotion, rejection and stopping rules. | Answered; synthesis saved |
| R12 | What remains uncertain, and is it worth another pass? | Prioritized follow-up research with question, affected decision, known evidence, method, dependencies, sufficient evidence and stop rule; distinguish reading/runtime and prerequisite/later. | Answered; synthesis saved |

## Method and anti-churn rules

1. Reuse pinned prior evidence unless a new question requires deeper inspection or a newer release could change the decision.
2. Search in focused groups. Trace promising claims to exact code, graphs, checkpoints, training configuration and license. Do not run downloaded code.
3. Record a lead as supported, partially supported, contradicted, inaccessible, or unverified. A missing public implementation is itself a decision-relevant limitation, not a reason for endless searching.
4. Prefer a complete compatible route over assembling unrelated promising parts. Distinguish shared infrastructure from model-specific learned weights.
5. Follow an additional lead only if it can change the recommendation, reduce an important uncertainty, or establish an experiment. Stop a literature branch when further reading repeats known constraints.
6. No runtime superiority or hardware-fit claims without measured evidence. Separate author measurements, historical local observations, source inspection and proposed tests.

## Deliverables

- `REPORT.md`: comprehensive plain-English synthesis, terminology, examples, findings, alternatives, recommended route and fallback, custom proposals, feasibility, resources and licensing.
- `SOURCE-REGISTER.md` and source snapshots/manifest: primary sources, versions, inspected paths/graphs, findings and evidence limits; reuse prior register by reference.
- `VALIDATION-PLAN.md`: bounded implementation-validation experiment, not executed in this research phase.
- `FOLLOW-UP-RESEARCH.md`: actionable prioritized uncertainties, including which require experiments rather than more reading.
- `COMPLETION-AUDIT.md`: requirement-by-requirement check against saved artifacts and inspected evidence.

## Completion condition

Mark the research goal complete only when all twelve work packages have sourced answers or explicitly actionable gaps; promising accessible implementations/graphs are examined; all deliverables are saved and checked; and the recommendation distinguishes demonstrated behavior from hypotheses and later experiments. Then explain the findings and limitations, say `DING FRIES ARE DONE!`, and stop for discussion. Completion does not mean the proposed next iteration has been implemented or proven.

