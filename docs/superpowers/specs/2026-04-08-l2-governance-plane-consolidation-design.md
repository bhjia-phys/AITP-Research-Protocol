# AITP L2 Governance Plane Consolidation Design

Status: working design

Date: 2026-04-08

## Goal

Consolidate the current scattered `L2` doctrine into one design-level target for
the AITP `L2` governance plane.

This document is meant to update and sharpen the existing `L2` direction rather
than replace it with an unrelated memory product pattern.

The target outcome is:

- an `L2` that compounds reusable physics knowledge over time;
- an `L2` that stays protocol-first, schema-first, and auditable;
- an `L2` that supports progressive retrieval and graph traversal without
  confusing retrieval convenience with scientific trust;
- an `L2` that can serve all three current primary AITP lanes through one shared
  core plus lane-specific extension points;
- an `L2` that can later feed both human-readable and typed downstream knowledge
  realizations, including a future Lean-facing export path.

This is a design document.
It does not define implementation tasks yet.

## Scope

This document defines only the AITP-governed `L2` plane.

It does define:

- reusable identity and provenance doctrine,
- canonical-versus-compiled-versus-staging separation,
- shared object and edge structure,
- lane-aware retrieval and packetization rules,
- human-facing and AI-facing derived output contracts,
- backend bridge expectations,
- and a Lean-ready typed projection contract.

It does not define:

- the complete human-readable downstream knowledge backend,
- the complete machine-primary typed knowledge-network backend,
- concrete Lean object families,
- a full `theory_synthesis` lane implementation,
- or implementation tasks and file-by-file code changes.

## Existing Material Being Consolidated

This design consolidates and sharpens material currently spread across:

- `docs/superpowers/specs/2026-04-07-aitp-collaborator-rectification-and-interaction-design.md`
  - especially `R5. Layer 2 Knowledge-Network MVP`
- `docs/AITP_UNIFIED_RESEARCH_ARCHITECTURE.md`
  - especially `Plane B: L2 governance plane`
- `research/knowledge-hub/canonical/CANONICAL_UNIT.md`
- `research/knowledge-hub/canonical/LAYER2_OBJECT_FAMILIES.md`
- `research/knowledge-hub/canonical/L2_COMPILER_PROTOCOL.md`
- `research/knowledge-hub/canonical/L2_STAGING_PROTOCOL.md`
- `research/knowledge-hub/canonical/L2_BACKEND_BRIDGE.md`
- `research/knowledge-hub/canonical/L2_BACKEND_INTEGRATION_PROTOCOL.md`
- `research/knowledge-hub/schemas/edge.schema.json`
- `research/knowledge-hub/canonical/retrieval_profiles.json`
- `schemas/knowledge-packet.schema.json`
- `docs/AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md`

The practical issue today is not that `L2` has no doctrine.
It is that the doctrine is distributed across several files and is still missing
one clear consolidation target.

## Design Judgment

The right next step is not:

- a search shell first,
- a personal-memory app first,
- or a paired-backend rollout first.

The right next step is:

- consolidate `L2` as a governance plane first,
- preserve a small shared semantic core,
- define progressive retrieval on top of that core,
- and let later human-readable and typed downstream backends realize the same
  promoted identity without silently becoming the source of truth.

Short form:

- `L2` should not become a generic memory shell,
- but it should learn from modern memory systems.

## Lessons From External Systems

Recent knowledge and memory systems are useful here, but only selectively.

### What to borrow

From search-centric systems:

- progressive retrieval rather than full-memory loading,
- cheap index-first narrowing,
- optional deeper packet expansion only when needed,
- and bounded consultation shaped around the current question.

From memory-shell systems:

- separation between raw conversational or source traces and distilled reusable
  memory,
- dual output surfaces for human and agent use,
- and graph-assisted neighborhood traversal for later recall.

From graph-memory systems:

- explicit edge-centric navigation,
- relation-aware retrieval,
- and the idea that derived summaries should remain reconstructible from smaller
  underlying units.

### What not to borrow

AITP should not equate:

- search score with trust,
- graph centrality with importance,
- frequency of reuse with scientific correctness,
- or automatic clustering with canonical identity.

AITP `L2` is a governed scientific memory plane, not a convenience layer that
silently promotes whatever is easy to retrieve.

## Core Doctrine

### 1. `L2` is a governance plane, not the whole downstream knowledge world

`L2` should remain the AITP-governed contract and indexing plane for reusable
knowledge.

Its job is to:

- assign reusable identity,
- preserve provenance,
- record promotion route and trust posture,
- expose retrieval profiles,
- materialize derived helper surfaces,
- maintain staging and hygiene separation,
- and register backend bridge intent.

It is not itself the entire human-readable brain or the entire typed downstream
knowledge network.

### 2. `L2` remains schema-first

The center of gravity remains:

- `CanonicalUnit`,
- explicit edge rows,
- explicit retrieval policy,
- explicit promotion records,
- and explicit backend cards.

Folders remain useful for browsing and storage, but folder shape does not define
meaning by itself.

### 3. `L2` learns through governed distillation

AITP should become wiser over time by promoting reusable distilled objects out of
`L1` or `L3/L4`, not by treating all durable text as equally reusable memory.

That means:

- raw sources stay in `L0`,
- provisional understanding stays in `L1`,
- exploratory work stays in `L3`,
- adjudication stays in `L4`,
- and only reusable, scoped, provenance-backed objects land in canonical `L2`.

## Shared `L2` Core

### 1. Canonical surfaces

The shared core should treat the following as primary canonical surfaces:

- typed unit files governed by `CanonicalUnit`,
- `canonical/index.jsonl`,
- `canonical/edges.jsonl`,
- `canonical/retrieval_profiles.json`,
- promotion and provenance records,
- backend bridge metadata.

The following are important but non-authoritative relative to canonical units:

- `compiled/` outputs,
- `staging/` entries,
- `hygiene/` reports.

### 2. Shared semantic contract

Every canonical object should keep the existing minimum contract:

- stable `id`,
- explicit `unit_type`,
- reusable `summary`,
- assumptions,
- regime,
- scope,
- provenance,
- promotion,
- dependencies,
- related units,
- payload.

This remains the cross-lane invariant.

No lane should be allowed to bypass:

- explicit scope,
- explicit assumptions,
- explicit provenance,
- or explicit promotion route.

### 3. Shared family structure

AITP already has a richer object-family set than the earlier `R5` MVP list.
That is a feature, not a problem.

The consolidation rule should be:

- keep one shared canonical family space,
- avoid splitting `L2` into lane-specific incompatible ontologies,
- and allow each lane to emphasize different subsets of that shared family space.

The shared cross-lane reusable families should be treated as the stable common
backbone:

- `concept`
- `claim_card`
- `assumption_card`
- `regime_card`
- `method`
- `workflow`
- `validation_pattern`
- `warning_note`
- `bridge`
- `example_card`
- `topic_skill_projection`

The richer formal-theory families remain first-class canonical families, but
they should be understood as lane-rich extensions inside the same shared family
space rather than a separate `L2`:

- `definition_card`
- `notation_card`
- `equation_card`
- `theorem_card`
- `proof_fragment`
- `derivation_step`
- `equivalence_map`
- `symbol_binding`
- `caveat_card`
- `derivation_object`

The earlier `R5` items that do not yet fully exist as canonical families should
be treated as explicit extension targets rather than silently forgotten:

- `physical_picture`
  - planned shared-core extension family
- `negative_result`
  - immediate next extension family

Until those families exist, they should not quietly pretend to be canonical by
default.
They may live in `staging/` or topic-local `L3` when that is the honest state.

## Edge Vocabulary Consolidation

### 1. Canonical edge vocabulary

The canonical edge vocabulary should follow the schema-backed terms already in
`research/knowledge-hub/schemas/edge.schema.json`:

- `depends_on`
- `supports`
- `contradicts`
- `specializes`
- `generalizes`
- `uses_method`
- `validated_by`
- `warned_by`
- `bridged_to`
- `derived_from`
- `applies_in_regime`

These should be treated as the authoritative graph layer for canonical `L2`.

### 2. Retrieval or narrative aliases

Earlier design language introduced several useful but not fully schema-aligned
labels:

- `valid_under`
- `warns_about`
- `analogy_to`
- `derived_from_source`

The consolidation rule should be:

- `valid_under` is a human-facing alias for `applies_in_regime`;
- `warns_about` is a human-facing rendering derived from `warned_by` plus
  object direction;
- `derived_from_source` belongs primarily in provenance, not as the default
  canonical unit-to-unit edge;
- `analogy_to` should not become canonical edge vocabulary until AITP can state
  analogy semantics sharply enough to distinguish it from a real `bridge`.

If a relation is still too vague for canonical graph use, keep it in notes,
payload, or staging instead of inventing a weak edge that later undermines graph
quality.

### 3. Evidence rule for edges

Every canonical edge should keep:

- explicit `from_id`,
- explicit `to_id`,
- explicit `relation`,
- and `evidence_refs`.

Edge existence should remain evidence-backed.
No derived graph builder should be allowed to silently add canonical edges based
only on embedding proximity or text similarity.

## Progressive Retrieval

### 1. Retrieval should start narrow

`L2` consultation should prefer:

1. query classification,
2. index-level narrowing,
3. profile-guided edge expansion,
4. bounded packet materialization,
5. human or AI render.

The default should not be to load all matching unit bodies into context.

### 2. Retrieval should be lane-aware

Retrieval should use the current lane as a shaping signal, not as the sole truth
of unit identity.

The lane tells consultation:

- which unit families to prefer first,
- which relations to expand,
- what warnings to foreground,
- and what kind of output packet to produce.

It should not create separate incompatible ontologies for each lane.

### 3. Retrieval should be mode-aware

`discussion`, `explore`, `verify`, and `promote` should retrieve different
shapes of `L2` support even for the same lane.

Examples:

- `discussion` should bias toward concepts, assumptions, regimes, bridge notes,
  and warnings;
- `explore` should bias toward methods, derivation objects, equivalence maps,
  and route-shaping workflows;
- `verify` should bias toward validation patterns, assumptions, equations,
  contradictions, and regime limits;
- `promote` should bias toward provenance, prior related units, conflicts,
  duplication risk, and backend writeback consequences.

### 4. Retrieval should be packetized

The existing `KnowledgePacket` idea should evolve into a small family of
derived consultation packets rather than a one-size-fits-all summary blob.

The important rule is:

- packets are derived retrieval surfaces,
- packets are not canonical unit replacements,
- and packets must keep exact pointers back to the underlying units and
  evidence-bearing artifacts.

## Human-Facing And AI-Facing Output Surfaces

### 1. Human-facing outputs

Human-facing `L2` outputs should be operator-readable derived surfaces such as:

- workspace memory maps,
- lane-specific consultation summaries,
- review packets for promotion,
- bridge snapshots,
- backend drift notes,
- and hygiene summaries.

These should read like compact research aids rather than raw JSON dumps.

But they must still preserve:

- canonical unit ids,
- assumptions,
- regime and scope limits,
- provenance pointers,
- and warning surfaces.

### 2. AI-facing outputs

AI-facing `L2` outputs should be machine-primary consultation packets that are:

- compact,
- relation-aware,
- lane-aware,
- and explicit about trust posture.

An AI-facing packet should generally surface:

- the selected canonical unit ids,
- why they were selected,
- the edge neighborhood used,
- warnings,
- assumptions and regime limits,
- unresolved conflicts if any,
- and exact pointers for deeper follow-up.

### 3. Symmetry rule

The human-facing and AI-facing surfaces may differ in rendering, but they should
be derived from the same promoted identity and should not silently disagree about
scope, assumptions, or trust status.

## Lane Extension Points

The current three primary lanes are:

- `formal_theory`
- `toy_numeric`
- `code_method`

The consolidation rule is:

- one shared `L2` core,
- lane-specific retrieval and compiled views,
- lane-specific richer family usage,
- but no lane-specific fork of canonical identity rules.

### 1. `formal_theory`

`formal_theory` should be the richest current lane in terms of canonical family
resolution.

It should preferentially use:

- `definition_card`
- `notation_card`
- `equation_card`
- `assumption_card`
- `regime_card`
- `theorem_card`
- `proof_fragment`
- `derivation_step`
- `equivalence_map`
- `symbol_binding`
- `caveat_card`
- `derivation_object`
- plus cross-lane families such as `concept`, `bridge`, `warning_note`, and
  `validation_pattern`.

Its compiled packets should foreground:

- dependency chains,
- proof status,
- missing obligations,
- equivalence structure,
- scope limits,
- and export readiness for later formal translation.

### 2. `toy_numeric`

`toy_numeric` should use the shared core without requiring a separate object
universe.

It should preferentially use:

- `concept`
- `assumption_card`
- `regime_card`
- `claim_card`
- `method`
- `workflow`
- `validation_pattern`
- `warning_note`
- `example_card`
- `bridge`

Its compiled packets should foreground:

- model definition,
- observable definition,
- benchmark target,
- convergence and reproducibility expectations,
- regime limits,
- and reusable benchmark or validation routes.

If later `toy_numeric` needs narrower canonical families, those should be added
as explicit shared-family extensions rather than hidden inside free-form payloads.

### 3. `code_method`

`code_method` should also stay inside the shared family space.

It should preferentially use:

- `method`
- `workflow`
- `validation_pattern`
- `warning_note`
- `topic_skill_projection`
- `bridge`
- `claim_card`
- `assumption_card`
- `regime_card`

Its compiled packets should foreground:

- prerequisites,
- backend dependencies,
- benchmark-first gates,
- operational failure modes,
- validation route,
- and trusted reusable execution memory.

### 4. Reserved extension lane

AITP should keep the reserved future lane:

- `theory_synthesis`

This document does not define it fully.

But the shared `L2` structure should leave room for it by ensuring that:

- `bridge`,
- `equivalence_map`,
- `concept`,
- `warning_note`,
- and future `physical_picture`

can already support cross-paper and cross-framework retrieval without requiring a
new `L2` plane.

## Canonical, Compiled, Staging, And Backends

### 1. Canonical

Canonical `L2` remains the authoritative reusable-memory surface.

### 2. Compiled

Compiled `L2` remains a derived helper surface for:

- consultation,
- navigation,
- hygiene review,
- and operator-readable reuse.

Compiled outputs may cluster, summarize, rank, or packetize.
They may not silently redefine canonical meaning.

### 3. Staging

Staging remains the quarantine zone for `L2`-adjacent material that is durable
but not yet trusted canonical memory.

This is especially important for:

- candidate reusable insights from discussions,
- provisional warning notes,
- pre-family content such as future `physical_picture`,
- and AI-generated reusable-memory candidates awaiting review.

### 4. Backend bridges

Backends remain explicit support surfaces, not automatic truth imports.

A backend may:

- seed consultation,
- seed staged candidates,
- or materially inform promoted units through `backend_refs`.

A backend may not:

- count as canonical merely because it exists,
- replace `L0` registration when strong reuse depends on a concrete artifact,
- or substitute for explicit promotion records.

## Lean-Ready Export Contract

Lean should remain a downstream export path, not the definition of `L2`
success.

This design should therefore reserve a Lean-ready typed projection contract with
the following rules:

- no new top-level Lean-specific epistemic layer is introduced;
- no canonical unit becomes true merely because it has a typed downstream
  encoding;
- Lean-facing export consumes selected promoted units from canonical `L2` or
  machine-primary downstream typed realizations;
- export readiness is recorded as projection metadata or derived status, not as
  the sole criterion for promotion.

The main export-eligible families should eventually include:

- `definition_card`
- `notation_card`
- `equation_card`
- `assumption_card`
- `regime_card`
- `theorem_card`
- `proof_fragment`
- `derivation_step`
- `equivalence_map`
- `symbol_binding`

But this document only reserves the contract.
It does not yet define the full Lean-side type mapping.

## Update Rule For Existing Specs

Going forward, the existing `R5` L2 MVP language should be interpreted through
this consolidation:

- the earlier MVP node and edge lists remain useful orientation points,
- but they do not override the richer canonical family and edge protocols that
  already exist elsewhere in the repository,
- and they should no longer be read as if `L2` were a single small graph schema
  detached from canonical-versus-compiled-versus-staging separation.

The practical merge target should be:

- keep the shared-core MVP spirit,
- keep the graph traversal and progressive retrieval requirement,
- keep the lightweight staging entry path,
- but anchor all of that inside the already-existing governance-plane doctrine.

## Success Criteria

This consolidation should be considered successful when AITP can honestly say:

- `L2` has one clear governance-plane definition,
- the three primary lanes share one reusable-memory core,
- progressive retrieval is a first-class `L2` behavior,
- human-facing and AI-facing outputs are derived from the same promoted
  identity,
- backend use no longer risks looking like an opaque side channel,
- and future Lean export has a clear reserved attachment point without forcing
  premature formalization.

## One-Line Doctrine

Build `L2` as a schema-first governance plane with shared reusable identity,
lane-aware progressive retrieval, explicit compiled and staging separation, and
future-facing downstream export hooks, rather than as a generic memory shell or
an overgrown ontology.
