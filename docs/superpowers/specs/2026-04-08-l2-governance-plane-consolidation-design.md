# AITP L2 Governance Plane Consolidation Design

Status: working design

Date: 2026-04-08

## Goal

Consolidate the current scattered `L2` doctrine into one design-level target for
the AITP `L2` governance plane.

The target outcome is:

- an `L2` that compounds reusable physics knowledge over time;
- an `L2` that stays protocol-first, schema-first, and auditable;
- an `L2` that supports progressive retrieval and graph traversal without
  confusing retrieval convenience with scientific trust;
- an `L2` that can serve the current primary lanes through one shared semantic
  core plus lane-specific extension points;
- an `L2` that can later feed both human-readable and typed downstream
  knowledge realizations, including a future Lean-facing export path.

This is a design document.
It defines the consolidation target, not the full implementation.

## Scope

This document defines only the AITP-governed `L2` plane.

It does define:

- reusable identity and provenance doctrine,
- canonical versus compiled versus staging separation,
- shared object and edge structure,
- lane-aware retrieval and packetization rules,
- human-facing and AI-facing derived output contracts,
- backend bridge expectations,
- and a Lean-ready typed projection reserve.

It does not define:

- a complete human-readable downstream knowledge backend,
- a complete machine-primary typed knowledge-network backend,
- concrete Lean object families,
- a full `theory_synthesis` lane implementation,
- or seeded graph data and populated retrieval.

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

## Core Doctrine

### 1. `L2` is a governance plane

`L2` remains the AITP-governed contract and indexing plane for reusable
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

Folders remain useful for browsing and storage, but folder shape does not
define meaning by itself.

### 3. `L2` learns through governed distillation

AITP becomes wiser by promoting reusable distilled objects out of `L1` or
`L3/L4`, not by treating every durable text artifact as equally reusable
memory.

That means:

- raw sources stay in `L0`,
- provisional understanding stays in `L1`,
- exploratory work stays in `L3`,
- adjudication stays in `L4`,
- and only reusable, scoped, provenance-backed objects land in canonical `L2`.

## Shared `L2` Core

### 1. Canonical surfaces

Primary canonical surfaces are:

- typed unit files governed by `CanonicalUnit`,
- `canonical/index.jsonl`,
- `canonical/edges.jsonl`,
- `canonical/retrieval_profiles.json`,
- promotion and provenance records,
- backend bridge metadata.

Compiled outputs, staging entries, and hygiene reports remain important but
non-authoritative relative to canonical units.

### 2. Shared semantic contract

Every canonical object keeps the shared minimum contract:

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

No lane may bypass:

- explicit scope,
- explicit assumptions,
- explicit provenance,
- or explicit promotion route.

### 3. Shared family structure

AITP keeps one shared canonical family space.
It should not split `L2` into lane-specific incompatible ontologies.

Stable cross-lane reusable families include:

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

Lane-rich formal families remain first-class inside the same family space:

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

The immediate extension targets that remain reserved rather than active are:

- `physical_picture`
- `negative_result`

## Edge Vocabulary Consolidation

### 1. Canonical edge vocabulary

Canonical `L2` edges follow the schema-backed relations:

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

### 2. Retrieval or narrative aliases

Useful narrative aliases remain allowed, but they do not replace canonical edge
semantics:

- `valid_under` is a human-facing alias for `applies_in_regime`;
- `warns_about` is a human-facing rendering derived from `warned_by`;
- `derived_from_source` belongs primarily in provenance;
- `analogy_to` remains non-canonical until its semantics become sharper.

### 3. Evidence rule

Every canonical edge keeps:

- explicit `from_id`,
- explicit `to_id`,
- explicit `relation`,
- and `evidence_refs`.

Embedding proximity or text similarity may help retrieval, but they may not
silently add canonical edges.

## Progressive Retrieval

Retrieval should prefer:

1. query classification,
2. index-level narrowing,
3. profile-guided edge expansion,
4. bounded packet materialization,
5. human or AI render.

It should start narrow rather than loading all matching unit bodies into
context.

Retrieval is lane-aware and mode-aware:

- `discussion` favors concepts, assumptions, regimes, warnings, and bridges;
- `explore` favors methods, derivations, route-shaping workflows, and
  equivalence structure;
- `verify` favors validation patterns, assumptions, contradictions, equations,
  and regime limits;
- `promote` favors provenance, duplication risk, conflicts, and downstream
  writeback consequences.

## Human-Facing And AI-Facing Output Surfaces

Human-facing `L2` outputs are operator-readable derived surfaces such as:

- workspace memory maps,
- lane-specific consultation summaries,
- promotion review packets,
- bridge snapshots,
- backend drift notes,
- and hygiene summaries.

AI-facing `L2` outputs are compact machine-primary consultation packets that
surface:

- selected canonical unit ids,
- why they were selected,
- the edge neighborhood or retrieval profile used,
- warnings,
- assumptions and regime limits,
- unresolved conflicts,
- and exact pointers for deeper follow-up.

These two surfaces are derived from the same promoted identity.
They may differ in rendering, but they may not silently disagree about scope,
assumptions, trust status, or unresolved boundaries.

## Lane Extension Points

The current primary lanes are:

- `formal_theory`
- `toy_numeric`
- `code_method`

The shared rule is:

- one shared `L2` core,
- lane-specific retrieval and compiled views,
- lane-specific richer family usage,
- but no lane-specific fork of canonical identity rules.

The reserved future lane remains:

- `theory_synthesis`

## Canonical, Compiled, Staging, And Backends

Canonical `L2` remains the authoritative reusable-memory surface.

Compiled `L2` remains a derived helper surface for consultation, navigation,
hygiene review, and operator-readable reuse.

Staging remains the quarantine zone for durable but not-yet-trusted `L2`
adjacent material, including future `physical_picture` or other pre-family
content.

Backends remain explicit support surfaces, not automatic truth imports.
They may seed consultation or staging, but they do not count as canonical
solely because they exist.

## Lean-Ready Export Contract

Lean should remain a downstream export path, not the definition of `L2`
success.

Therefore:

- no new Lean-specific epistemic layer is introduced;
- no canonical unit becomes true merely because it has a typed downstream
  encoding;
- Lean-facing export consumes selected promoted units from canonical `L2` or
  machine-primary downstream typed realizations;
- export readiness is recorded as metadata or derived status, not as the sole
  criterion for promotion.

## Success Criteria

This consolidation succeeds when AITP can honestly say:

- `L2` has one clear governance-plane definition;
- the primary lanes share one reusable-memory core;
- progressive retrieval is a first-class `L2` behavior;
- human-facing and AI-facing outputs are derived from the same promoted
  identity;
- backend use no longer risks looking like an opaque side channel;
- and future Lean export has a clear reserved attachment point without forcing
  premature formalization.

## One-Line Doctrine

Build `L2` as a schema-first governance plane with shared reusable identity,
lane-aware progressive retrieval, explicit compiled and staging separation, and
future-facing downstream export hooks, rather than as a generic memory shell or
an overgrown ontology.
