# Indexing rules

This file defines how the kernel indexes material so AI can retrieve the right objects during thinking, not only store them after the fact.

The indexing design is hybrid:
- typed object store,
- explicit per-layer indexes,
- lightweight relation edges,
- retrieval profiles by stage,
- optional semantic ranking later.

## 1. Core principle

Indexing exists for **active retrieval during reasoning**.

That means:
- `L1` must be able to look up relevant `L2` concepts, claim cards, warnings, and workflows during source understanding,
- `L3` must be able to look up methods, derivation objects, bridges, workflows, and warnings during candidate formation,
- `L4` must be able to look up validation patterns, prior claim cards, warnings, concepts, and derivation objects during adjudication.

So the indexing layer is part of the research loop, not an afterthought.

## 2. Identifier namespaces

Use stable ids with typed prefixes.

### Source-level ids
- `source_id`
  - format: `paper:ryu-takayanagi-2006`
  - format: `url:example-article`
  - format: `video:lecture-foo`

### Layer 1 ids
- `claim_id`
  - format: `claim:rt-leading-entropy-minimal-saddle`
- `candidate_seed_id`
  - format: `candidate_seed:rt-leading-order-entropy`

### Layer 3 ids
- `candidate_id`
  - format: `candidate:rt-leading-order-entropy`
- `run_id`
  - format: `2026-03-12-rt-saddle-check`

### Layer 4 ids
- `validation_id`
  - format: `validation:rt-saddle-dominance`
- `task_id`
  - format: `rt-saddle-scope-check`
- `decision_id`
  - format: `decision:rt-saddle-dominance-accept`

### Consultation protocol ids
- `consultation_id`
  - format: `consult:l1-rt-provisional-normalization`
  - format: `consult:l3-rt-candidate-shaping`
  - format: `consult:l4-rt-validation-routing`

### Layer 2 ids
- `unit_id`
  - format: `concept:rt-minimal-saddle`
  - format: `claim_card:rt-leading-order-entropy`
  - format: `validation_pattern:rt-saddle-competition-check`

## 3. Per-layer index surfaces

### Layer 0 / Layer 1

Use:
- `intake/topics/<topic_slug>/source_index.jsonl`
- `intake/topics/<topic_slug>/provisional_claims.jsonl`
- `intake/topics/<topic_slug>/promotion_candidates.jsonl`
- optional `intake/topics/<topic_slug>/l2_consultation_log.jsonl`

### Layer 2

Use:
- `canonical/index.jsonl`
- `canonical/edges.jsonl`
- `canonical/retrieval_profiles.json`

### Layer 3

Use:
- `feedback/topics/<topic_slug>/runs/<run_id>/candidate_ledger.jsonl`
- `feedback/topics/<topic_slug>/runs/<run_id>/decision_ledger.jsonl`
- optional `feedback/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`

### Layer 4

Use:
- `validation/topics/<topic_slug>/runs/<run_id>/promotion_decisions.jsonl`
- `validation/topics/<topic_slug>/runs/<run_id>/execution-tasks/<task_id>.json`
- optional `validation/topics/<topic_slug>/runs/<run_id>/l2_consultation_log.jsonl`

### Cross-layer consultation protocol

Use:
- `consultation/topics/<topic_slug>/consultation_index.jsonl`
- `consultation/topics/<topic_slug>/calls/<consultation_slug>/request.json`
- `consultation/topics/<topic_slug>/calls/<consultation_slug>/result.json`
- `consultation/topics/<topic_slug>/calls/<consultation_slug>/application.json`

The stage-local `l2_consultation_log.jsonl` files are now projections for local readability.
The consultation protocol surface is the source-of-truth for non-trivial `L2` consultation.
If that consultation materially changes a durable stage artifact, emitting the protocol bundle there is mandatory.

## 4. Minimal cross-layer reference rule

Across layers, pass:
- `id`
- `path`
- `title`
- `summary`
- `layer`
- `object_type`

Do not copy full bodies by default.

The base reusable object for this is `object_ref`.

See:
- `schemas/object-ref.schema.json`

## 5. Layer 2 index entry requirements

Each Layer 2 index entry should include:
- `unit_id`
- `unit_type`
- `title`
- `summary`
- `tags`
- `domain`
- `assumptions`
- `regime`
- `scope`
- `related_units`
- `dependencies`
- `warning_tags`
- `validation_tags`
- `path`
- `maturity`

These fields are not just descriptive.
They are the fields later-stage retrieval should filter on.

## 6. Relation edges

The lightweight graph layer lives in:
- `canonical/edges.jsonl`

Typical edge types:
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

The graph does not replace the typed object store.
It augments retrieval.

See:
- `schemas/edge.schema.json`

## 7. Retrieval profiles

Use stage-aware retrieval profiles stored in:
- `canonical/retrieval_profiles.json`

Profiles should tell the system:
- which unit types to prefer,
- which metadata fields matter most,
- which edges to expand first,
- how many primary results to inspect before broadening.

This is more reliable than “semantic similarity only.”

## 8. Recommended retrieval order

### Layer 1 retrieval

Default unit priority:
- `concept`
- `claim_card`
- `warning_note`
- `workflow`

Why:
- terminology normalization,
- scope checking,
- early contradiction spotting,
- intake routine reuse.

### Layer 3 retrieval

Default unit priority:
- `method`
- `derivation_object`
- `workflow`
- `bridge`
- `warning_note`

Why:
- avoid rebuilding known derivational or research routes,
- surface cross-topic structure,
- avoid known traps.

### Layer 4 retrieval

Default unit priority:
- `validation_pattern`
- `claim_card`
- `warning_note`
- `concept`
- `derivation_object`

Why:
- choose the right checks,
- compare against prior accepted claims,
- surface prior failure modes,
- test regime consistency.

## 9. Query strategy

The recommended retrieval order is:

1. schema filter
   - `unit_type`
   - `domain`
   - `tags`
   - `assumptions`
   - `regime`
   - `scope`

2. graph expansion
   - follow relevant edges from the primary hits

3. optional semantic ranking
   - embedding or full-text ranking can refine results later

Do not invert this order by making semantic similarity the only gate.

## 10. Why this is not just ordinary RAG

Ordinary RAG tends to retrieve similar text.

This kernel needs to retrieve:
- the right typed object,
- in the right stage,
- with the right assumptions and regime,
- plus adjacent warnings, methods, and validation patterns.

So the design target is:

**typed object store + edge layer + retrieval profiles + optional semantic ranking**

not “vector search alone.”

In this architecture, `L2 consultation` is the protocol that turns that retrieval design into an auditable working-memory action.
