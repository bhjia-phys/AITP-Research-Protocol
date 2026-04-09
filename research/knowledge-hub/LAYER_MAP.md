# Layer map

This file defines the standalone source-of-truth mapping for the public AITP
kernel.

All normative paths below are repository-relative.
A fresh clone should already contain these fixed surfaces.

## 1. Task-type framing

The top-level research task types are:

- `open_exploration`
- `conjecture_attempt`
- `target_driven_execution`

These are orchestration classes, not epistemic layers.

They change:

- how broad `L0` should search,
- how `L1` should read,
- how much `L3` should compare routes,
- and how hard `L4` should try to close a target.

## 2. Lane framing

The main lane families are:

- `formal_theory`
- `model_numeric`
- `code_and_materials`

The reserved future lane remains:

- `theory_synthesis`

These lanes are broad research directions, not filesystem roots.

## 3. Human interaction plane

Human interaction is a cross-cutting plane:

- `H-plane`

It can intervene at any layer.
It governs:

- stop,
- update,
- checkpoint,
- route choice,
- and review.

It is not a normal epistemic layer.

## 4. Formal layer roots

Each layer below defines a minimum handoff contract.
The `Primary outputs` list is the smallest durable artifact surface other parts
of AITP are allowed to read instead of relying on chat state alone.

### Layer 0 — Source substrate

Source-of-truth:
- `research/knowledge-hub/source-layer/`

Primary topic surface:
- `source-layer/topics/<topic_slug>/source_index.jsonl`
- `source-layer/topics/<topic_slug>/sources/<source_slug>/`
- `source-layer/global_index.jsonl`

Primary outputs:
- source registry
- source packets
- citation links
- source fidelity metadata

Consumed by:
- `L1`
- `L3-A`
- `L4` when source recovery is needed

### Layer 1 — Technical understanding

Source-of-truth:
- `research/knowledge-hub/intake/`

Primary topic surface:
- `intake/topics/<topic_slug>/`

Primary outputs:
- assumption table
- notation table
- regime table
- claim extraction packet
- reading-depth record
- contradiction candidates

Consumed by:
- `L3-A`
- `L4`
- `L3-D`

### Layer 2 — Canonical reusable knowledge

Source-of-truth:
- `research/knowledge-hub/canonical/`

Primary object families:
- `canonical/concepts/`
- `canonical/claim-cards/`
- `canonical/derivation-objects/`
- `canonical/methods/`
- `canonical/workflows/`
- `canonical/bridges/`
- `canonical/validation-patterns/`
- `canonical/warning-notes/`
- `canonical/atomic-notes/`
- `canonical/staging/`

Primary outputs:
- consultation outputs
- compiled helper views
- staged memory candidates
- canonical reusable units

Consumed by:
- `L3-A`
- `L3-D`
- `H-plane`
- downstream paired realizations

### Layer 3 — Research analysis / result integration / distillation

Source-of-truth:
- `research/knowledge-hub/feedback/`

Primary topic surface:
- `feedback/topics/<topic_slug>/runs/<run_id>/`

This top-level `L3` is frozen as three internal subplanes:

#### `L3-A` Topic Analysis

Primary outputs:
- analysis workspace
- route comparison artifact
- bridge candidate
- candidate packet
- next-step routing choice

Consumed by:
- `L4`
- `L0/L1` through backedge choice
- `H-plane`

#### `L3-R` Result Integration

Primary outputs:
- validation return
- post-check interpretation
- scope update
- failure classification
- route-return recommendation

Consumed by:
- `L3-A`
- `L3-D`
- `H-plane`

#### `L3-D` Distillation

Primary outputs:
- staged insight candidate
- distilled memory packet
- promotion-ready memory candidate
- memory-scope summary

Consumed by:
- `canonical/staging/`
- canonical `L2`
- `H-plane`

### Layer 4 — Validation / adjudication

Source-of-truth:
- `research/knowledge-hub/validation/`

Primary topic surface:
- `validation/topics/<topic_slug>/runs/<run_id>/`

Primary outputs:
- symbolic sanity report
- limit/symmetry/dimensional report
- source-consistency report
- numerical or code/materials validation record
- adjudication outcome

Consumed by:
- `L3-R`
- `H-plane`

Frozen return rule:

- L4 outputs must return to `L3-R` before any L2 writeback decision.

## 5. Mandatory Movement Law

The frozen research flow is:

- `L0 -> L1 -> L3-A`
- `L2 consult -> L3-A`
- `L3-A -> L4 | L0 | L1`
- `L4 -> L3-R`
- `L3-R -> L3-A | L3-D | L0 | L1`
- `L3-D -> staging | L2 | L3-A | L1`

The older shorthand `L0 -> L1 -> L3 -> L4 -> L2` is no longer sufficient as
the architecture target.

## 6. Cross-Layer Protocol Surfaces

These are not new layers, but they are part of the formal public kernel.

### `consultation/`

Role:
- first-class `L2` consultation protocol
- request / result / application audit trail

Source-of-truth:
- `consultation/topics/<topic_slug>/calls/<consultation_slug>/`

### `runtime/`

Role:
- operator-visible state
- resume surface
- loop control materialization
- `H-plane` interaction projection

Source-of-truth:
- `runtime/topics/<topic_slug>/`

### `schemas/`

Role:
- shared machine-readable contracts used across layers

Source-of-truth:
- `schemas/*.json`
- layer-local schema folders such as `validation/schemas/` and `feedback/schemas/`

### `data/`

Role:
- auxiliary local/query storage
- not a formal `L0-L4` layer

Rule:
- do not treat `data/` as the default durable home for protocol-governed work

## 7. Required Read Order

When an agent enters a topic, read in this order:

1. `research/knowledge-hub/LAYER_MAP.md`
2. `research/knowledge-hub/README.md`
3. `research/knowledge-hub/canonical/CANONICAL_UNIT.md`
4. `research/knowledge-hub/canonical/PROMOTION_POLICY.md`
5. `research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md`
6. `research/knowledge-hub/runtime/README.md`
7. `research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md`
8. `research/knowledge-hub/AGENT_CONFORMANCE_PROTOCOL.md`
9. `research/knowledge-hub/validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md`
10. the active topic runtime artifacts under `runtime/topics/<topic_slug>/`

## 8. Working Rule

The public repository now claims the following explicitly:

- `L0-L4` each have deterministic filesystem roots
- `L3` is internally decomposed into analysis, result integration, and distillation
- `consultation/`, `runtime/`, and `schemas/` are first-class support surfaces
- external knowledge stores are optional backends, not hidden canonical stores
- a run is not AITP-conformant if it bypasses these surfaces and lives only in chat
