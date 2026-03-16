# Layer map

This file defines the standalone source-of-truth mapping for the public AITP
kernel.

All normative paths below are repository-relative. A fresh clone should already
contain these fixed surfaces.

## 1. Formal layer roots

### Layer 0 — Source substrate

Source-of-truth:
- `research/knowledge-hub/source-layer/`

Primary topic surface:
- `source-layer/topics/<topic_slug>/source_index.jsonl`
- `source-layer/topics/<topic_slug>/sources/<source_slug>/`
- `source-layer/global_index.jsonl`

### Layer 1 — Intake / provisional understanding

Source-of-truth:
- `research/knowledge-hub/intake/`

Primary topic surface:
- `intake/topics/<topic_slug>/`

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

### Layer 3 — Research notebook / candidate formation

Source-of-truth:
- `research/knowledge-hub/feedback/`

Primary topic surface:
- `feedback/topics/<topic_slug>/runs/<run_id>/`

### Layer 4 — Validation / adjudication

Source-of-truth:
- `research/knowledge-hub/validation/`

Primary topic surface:
- `validation/topics/<topic_slug>/runs/<run_id>/`

## 2. Cross-layer protocol surfaces

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
- not a formal L0-L4 layer

Rule:
- do not treat `data/` as the default durable home for new protocol-governed work

## 3. External surfaces

External note vaults, software repositories, or result stores may exist outside
this repository, but they are not live AITP layer roots by path alone.

They must enter through:
- `canonical/backends/` for backend registration
- `source-layer/` for concrete artifact registration

An external human control plane may exist for convenience, but the public
standalone kernel remains self-contained even without it.

## 4. Required read order

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

## 5. Working rule

The public repository now claims the following explicitly:

- `L0-L4` each have deterministic filesystem roots.
- `consultation/`, `runtime/`, and `schemas/` are first-class support surfaces.
- external knowledge stores are optional backends, not hidden canonical stores.
- a run is not AITP-conformant if it bypasses these surfaces and lives only in chat.
