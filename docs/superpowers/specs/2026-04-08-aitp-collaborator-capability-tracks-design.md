# AITP Collaborator Capability Tracks Design

Status: working design

Date: 2026-04-08

## Goal

Add a companion design layer on top of the existing `M1-M5` milestone sequence
so AITP can be evaluated and extended as a real theoretical-physics
collaborator rather than only as a protocol-strong research control plane.

This document does not replace the current milestone sequence.
It adds collaborator-facing capability tracks, milestone exit gates, and
acceptance targets that keep the implementation aligned with real research use.

Short form:

- keep `M1-M5`,
- do not add a second main roadmap,
- attach collaborator capability requirements directly to the current roadmap,
- and judge progress by real theoretical-physics workflows rather than by
  control-plane growth alone.

## Why This Companion Design Exists

The current design stack is already strong on:

- `L0-L4` epistemic discipline,
- mode and backedge doctrine,
- runtime state materialization,
- promotion and consultation visibility,
- and the emerging `L2` governance plane.

But that alone does not guarantee that AITP behaves like a useful research
partner.

The remaining risk is clear:

- AITP may become increasingly good at explaining its own protocol state,
- while still underperforming at literature-based idea development,
- source-faithful technical reading,
- theory-grade validation,
- and long-horizon reusable scientific memory.

This companion design therefore introduces one additional question for every
major implementation step:

- does this change make AITP more capable as a theoretical-physics
  collaborator?

## Relationship To Existing Designs

This document is a companion to, not a replacement for:

- `docs/superpowers/specs/2026-04-07-aitp-collaborator-rectification-and-interaction-design.md`
- `docs/superpowers/plans/2026-04-07-m1-semantic-closure-and-interaction-contract.md`
- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `docs/AITP_UNIFIED_RESEARCH_ARCHITECTURE.md`
- `docs/AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md`
- `docs/AITP_MODE_ENVELOPE_PROTOCOL.md`

The division of labor is:

- the existing rectification design defines the main research-system direction,
- the `L2` governance design sharpens the reusable-memory plane,
- and this companion design states what additional capability tracks are needed
  so the same roadmap yields a real collaborator rather than a well-instrumented
  shell.

## Two Primary Research Scenarios

This design treats two concrete research scenarios as first-class acceptance
targets.

### Scenario A: Idea-Driven Open Research

The user gives AITP a concrete but unresolved idea, for example:

- whether measurement-induced phase transitions might connect structurally to
  background-independent algebraic formulations of quantum gravity.

AITP should then be able to:

1. start from `L0`,
2. use available agent tools to gather and register literature and other source
   material,
3. build a source-faithful comparative technical understanding in `L1`,
4. form candidate bridges, route comparisons, and synthesis attempts in `L3`,
5. consult `L2` as reusable memory without letting `L2` replace the new work,
6. perform theory-side or numerical checks in `L4`,
7. return to `L0/L1/L3` whenever the honest blocker lives there,
8. and only promote reusable conclusions into `L2` when the evidence bar and
   validation posture justify it.

### Scenario B: Canonical Literature Learning

The user gives AITP a direction, a canonical paper set, or a reading precision
target.

AITP should then be able to:

1. gather and register the relevant source basis in `L0`,
2. read the material in a physicist-grade way in `L1`,
3. reconstruct the technical core of the work rather than only summarize it,
4. treat the result as a candidate research object until it has survived `L4`
   checking,
5. and only then store reusable outputs in `L2`.

The key rule is:

- even classical or standard literature should not bypass `L4`,
- because AITP should learn the paper the way a researcher learns it:
  by reconstructing and checking important details, not by only restating prose.

## Collaborator Capability Tracks

This companion design adds five collaborator capability tracks.
They are not new layers, not new top-level modes, and not a second milestone
sequence.

They are continuous capability requirements that must be attached to the current
`M1-M5` roadmap.

### `R-Collab-1` Idea-To-Research Loop

AITP must support open-ended, idea-driven research in a disciplined way.

Required behavior:

- start from `L0` rather than from unsupported intuition,
- separate literature gathering from interpretation,
- compare several possible routes instead of hardening the first plausible
  bridge,
- let user ideas interact with source-derived structures in `L3`,
- and push candidate bridges into real `L4` checks before they are treated as
  reusable scientific memory.

This track exists because many valuable research questions begin as incomplete
bridges, analogies, or structural suspicions rather than as already-bounded
theorems or implementation tasks.

### `R-Collab-2` Canonical Literature Learning Loop

AITP must support reading and internalizing classic or foundational literature
as reusable scientific knowledge.

Required behavior:

- represent reading depth and source fidelity explicitly,
- capture assumptions, regime, notation, and proof posture in `L1`,
- reconstruct key technical content rather than stop at summaries,
- and require an `L4` check path before promotion into `L2`.

This track exists because a collaborator should not merely say what a paper is
about.
It should become able to use what the paper established.

### `R-Collab-3` Physicist-Grade Validation

AITP must validate like a theoretical physicist, not only like a workflow
system.

Required validation families include:

- limiting-case checks,
- dimensional checks,
- symmetry checks,
- notation and definition consistency checks,
- source-consistency checks,
- symbolic sanity checks,
- and when appropriate, toy-model or numerical confirmation.

Required output posture includes:

- `pass`,
- `partial`,
- `blocked`,
- `interesting_failure`,
- `regime_mismatch`,
- and `needs_source_recovery`.

This track exists because a research collaborator must be able to say not only
what a candidate means, but also what kind of check it survived and what still
remains open.

### `R-Collab-4` `L2` As Active Research Brain

`L2` should function as active reusable research memory, but not as a shortcut
that bypasses new work.

Required behavior:

- `L1/L3/L4` can consult `L2` through explicit consultation artifacts,
- retrieved memory objects carry scope, assumptions, provenance, and trust
  posture,
- consultation results may change route choice, warning posture, or concept
  alignment,
- but consultation does not replace source reading, candidate formation, or
  validation.

This track exists because a real collaborator gets smarter through accumulated
knowledge while still doing fresh work honestly.

### `R-Collab-5` Backedge And Retry Discipline

AITP must be able to move non-linearly across the layer graph without losing
scientific honesty.

Required behavior:

- classify why a route failed or paused,
- return to the layer that actually owns the blocker,
- keep the return durable and resumable,
- and preserve subroute, parking, and reintegration state.

This track exists because serious research is not a one-pass pipeline.
The system must be able to recover, branch, and retry without turning failure
into vague TODOs.

## Milestone Attachment Matrix

The existing roadmap remains:

- `M1` Semantic Closure And Interaction Contract
- `M2` `L2` Knowledge-Network MVP
- `M3` Physicist-Grade Intake And Validation
- `M4` Collaborator Memory And Low-Bureaucracy Exploration
- `M5` Paired Backend Maturity And Theory-Synthesis Lane

The collaborator tracks attach to the milestones as follows.

### `M1`

Primary attachment:

- `R-Collab-1`
- `R-Collab-4`
- `R-Collab-5`

Required collaborator-facing outcomes:

- topic identity distinguishes idea-driven research from canonical literature
  learning,
- runtime surfaces expose stop reason, resume stage, and backedge meaning,
- `L2` consultation is clearly separated from `L2` promotion,
- lane identities are no longer allowed to drift silently,
- and the runtime can explain why a topic is currently in `L0`, `L1`, `L3`,
  `L4`, or at an `L4 -> L2` boundary.

`M1` does not need to complete deep scientific work yet.
It must make the system honest about what work is being attempted.

### `M2`

Primary attachment:

- `R-Collab-4`
- `R-Collab-1`
- `R-Collab-2`

Required collaborator-facing outcomes:

- `L2` contains a non-empty seeded physics memory direction,
- consultation is no longer rhetorical,
- consultation can actually influence route comparison or warning posture,
- and `L2` retrieval behaves progressively rather than as whole-memory preload.

`M2` is the point where AITP first becomes meaningfully smarter through use.

### `M3`

Primary attachment:

- `R-Collab-1`
- `R-Collab-2`
- `R-Collab-3`

Required collaborator-facing outcomes:

- `L0` behaves more like source intelligence than source storage,
- `L1` becomes assumption-, regime-, and notation-aware,
- `L4` gains real theoretical-physics validation families,
- and canonical-literature learning can produce trustworthy reusable results
  only after actual checking.

`M3` is the point where AITP starts to resemble a careful physicist rather than
an advanced summarizer.

### `M4`

Primary attachment:

- `R-Collab-1`
- `R-Collab-2`
- `R-Collab-5`

Required collaborator-facing outcomes:

- collaborator memory is formalized separately from domain memory,
- failed routes and negative results are retained and reused,
- route-history and preference signals influence future choices,
- and low-bureaucracy exploration can still reintegrate cleanly into the
  protocol-governed topic graph.

`M4` is the point where AITP starts to resemble a long-horizon collaborator for
one researcher rather than a stateless protocol executor.

### `M5`

Primary attachment:

- `R-Collab-1`
- `R-Collab-4`
- `R-Collab-5`

Required collaborator-facing outcomes:

- `theory_synthesis` becomes a first-class lane,
- cross-paper assumption, regime, and notation reconciliation are explicit,
- paired backend alignment is operationally governed,
- and cross-framework bridge work becomes auditable rather than narrative-only.

`M5` is the point where AITP becomes capable of higher-level synthesis rather
than only bounded reading, bounded validation, and bounded promotion.

## Required Deliverables By Capability Track

These deliverables are requirement classes, not yet implementation tasks.
Whenever possible they should attach to existing surfaces before new surfaces
are introduced.

### `R-Collab-1` Deliverables

Required deliverable classes:

- idea-to-research packet,
- comparative literature map,
- route comparison artifact,
- idea synthesis note,
- `L4` check plan,
- final result brief for the current iteration.

Preferred attachment to existing surfaces:

- extend `idea_packet`,
- extend `L3` research-run artifacts,
- extend `validation_contract.active`,
- and add a light result-brief render if the current runtime shell cannot carry
  the research-facing summary cleanly.

### `R-Collab-2` Deliverables

Required deliverable classes:

- source reading packet,
- claim extraction packet,
- assumption and notation table,
- derivation reconstruction note,
- claim audit summary.

Preferred attachment to existing surfaces:

- strengthen `L1` intake artifacts,
- strengthen `validation_review_bundle.active`,
- and preserve source-fidelity links back to `L0`.

### `R-Collab-3` Deliverables

Required deliverable classes:

- validation-family selection artifact,
- symbolic sanity report,
- limiting-case report,
- notation consistency report,
- source-consistency report,
- optional numerical or toy-model check note when relevant.

Preferred attachment to existing surfaces:

- extend `validation_contract.active`,
- extend `validation_review_bundle.active`,
- and keep specialist reports as supporting artifacts rather than replacing the
  main review bundle.

### `R-Collab-4` Deliverables

Required deliverable classes:

- strengthened consultation request/result/application chain,
- memory influence log,
- promotion-ready knowledge packet,
- scoped synthesis packet for `L2`-assisted research.

Preferred attachment to existing surfaces:

- `consultation/`,
- `topic_synopsis`,
- `validation_review_bundle.active`,
- `topic_skill_projection.active`,
- and canonical promotion records.

### `R-Collab-5` Deliverables

Required deliverable classes:

- backedge packet,
- gap classification artifact,
- return contract,
- route reactivation note,
- reintegration log for resumed subroutes.

Preferred attachment to existing surfaces:

- runtime decision artifacts,
- unfinished-work queue surfaces,
- follow-up and reintegration logs,
- and explicit runtime synopsis fields rather than free-form TODO lists.

## Surface Strategy

The system should resist the temptation to create a parallel surface family for
every new collaborator-facing requirement.

The default strategy should be:

1. extend `idea_packet` when the new requirement is topic-intent or novelty-bar
   related,
2. extend `research_question.contract` when it is about the bounded question or
   declared research target,
3. extend `validation_contract.active` when it is about selected checks or
   adjudication posture,
4. extend `validation_review_bundle.active` when it is about primary review
   truth,
5. extend `topic_synopsis` when it is about current runtime truth,
6. use `consultation/` when `L2` materially changes the work,
7. use `topic_skill_projection.active` for mature reusable route memory,
8. add a new surface only when the existing ones cannot express the semantics
   without distortion.

This rule keeps the collaborator upgrade natural rather than proliferating a
second runtime tree.

## Milestone Exit Gates

The current milestones should gain collaborator-facing exit gates in addition to
their protocol-facing ones.

### `M1` Exit Gates

- topic type is explicit enough to distinguish at least:
  - `idea_driven_research`
  - `canonical_literature_learning`
- runtime exposes:
  - `stop_reason`
  - `resume_stage`
  - `backedge_reason`
- `L2` consultation and `L2` promotion are separate in both doctrine and
  runtime surfaces,
- `first_principles` is not silently collapsed into `toy_numeric`,
- and `theory_synthesis` has an explicit reserved lane identity.

### `M2` Exit Gates

- at least one seeded physics memory direction exists in canonical or staging
  form,
- consultation results can alter a downstream route in a visible way,
- staged review and canonicalization are non-empty and inspectable,
- and retrieval is progressive rather than full-memory loading.

### `M3` Exit Gates

- `L1` captures assumptions, regime, notation, proof posture, and tension,
- `L4` supports several physicist-grade validation families,
- at least one canonical-literature learning flow survives `L4`,
- and promotion remains blocked when the reconstruction or checks remain weak.

### `M4` Exit Gates

- collaborator memory is separated from reusable domain memory,
- route history and negative-result retention influence later routing,
- and exploration can remain lightweight without bypassing trust gates.

### `M5` Exit Gates

- `theory_synthesis` lane is operational,
- paired backend alignment policy is executable rather than purely doctrinal,
- and at least one cross-paper synthesis topic can survive the route honestly.

## Acceptance Matrix

This companion design requires a collaborator-focused acceptance matrix in
addition to module-level and schema-level tests.

### `A1` Open Idea Research

Input:

- a concrete research idea with incomplete initial structure.

Required acceptance behavior:

- `L0` source gathering is real,
- `L1` comparative analysis is source-faithful,
- `L3` route comparison and synthesis are explicit,
- `L4` performs an actual check family,
- and unresolved work exits honestly through backedge or partial result rather
  than fake closure.

### `A2` Canonical Literature Learning

Input:

- a canonical paper set or learning direction,
- plus a requested reading precision.

Required acceptance behavior:

- `L1` stores more than summaries,
- at least part of the technical core is reconstructed,
- `L4` checks whether the reconstruction is trustworthy,
- and `L2` promotion occurs only after that review.

### `A3` Cross-Paper Synthesis

Input:

- several papers or frameworks with possible overlap or tension.

Required acceptance behavior:

- assumptions, regime, and notation mismatches are explicit,
- synthesis does not flatten disagreement,
- and the output distinguishes:
  - validated bridge,
  - scoped analogy,
  - unresolved tension,
  - and speculative possibility.

### `A4` Theory-Plus-Check Workflow

Input:

- a candidate theoretical claim, bridge, or derivation target.

Required acceptance behavior:

- at least one real `L4` check family is applied,
- any required return to `L0/L1/L3` is durable and explicit,
- and the result remains honest about scope and non-conclusions.

## Risk Controls

This companion design is motivated by several concrete failure risks.

### Risk 1: `L2` Becomes Shortcut Memory

Failure mode:

- the system answers from prior memory before new work justifies it.

Control rule:

- `L2` may guide, warn, align, and compare,
- but it does not replace `L0`, `L1`, `L3`, or `L4`.

### Risk 2: `L4` Remains Prose-Only Review

Failure mode:

- the system explains validation posture without performing meaningful checks.

Control rule:

- every strong `L4` conclusion must name actual check artifacts or explicitly
  state why only a partial result exists.

### Risk 3: Control Plane Outruns Research Plane

Failure mode:

- runtime state becomes more elaborate while research artifacts remain too weak.

Control rule:

- milestone closure requires collaborator-facing acceptance, not only new
  control surfaces.

### Risk 4: Classical Learning Bypasses Validation

Failure mode:

- canonical papers are promoted after summary-quality reading alone.

Control rule:

- classical learning still requires `L4`,
- because AITP should learn by reconstruction and checking rather than by prose
  compression alone.

### Risk 5: Collaborator Memory Pollutes Scientific Memory

Failure mode:

- user preference, route history, and reusable physics knowledge become
  inseparable.

Control rule:

- collaborator memory must be durable but separate from canonical scientific
  units and their trust posture.

## Recommended Integration Strategy

This companion design should be integrated through:

1. one companion spec,
2. one companion plan per milestone family when needed,
3. and one collaborator acceptance matrix.

It should not be integrated by:

- renumbering the existing milestones,
- opening a second primary roadmap,
- or rewriting the current milestone sequence into user-story language.

The natural rollout is:

1. freeze this collaborator capability companion design,
2. attach a small `M1` companion plan focused on topic typing, stop and backedge
   explainability, and `L2` consultation boundaries,
3. attach a small `M2` companion plan focused on making `L2` non-empty and
   actually useful,
4. then extend `M3-M5` with the stronger collaborator-facing gates described
   here.

## One-Line Design Doctrine

AITP should keep its current `M1-M5` roadmap, but every milestone should now be
judged not only by whether the protocol kernel becomes cleaner, but also by
whether AITP becomes more capable of acting like a real theoretical-physics
collaborator across idea formation, literature learning, validation, memory,
and honest non-linear research motion.
