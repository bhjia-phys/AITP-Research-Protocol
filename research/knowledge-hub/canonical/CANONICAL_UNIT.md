# CanonicalUnit

`CanonicalUnit` is the minimal shared contract for every Layer 2 object.

The purpose of this contract is to make Layer 2:
- auditable,
- machine-readable,
- cross-run reusable,
- explicit about scope, assumptions, and provenance.

This is a schema-first design.
Folders may remain useful for storage and browsing, but folders do not define meaning by themselves.

## Required fields

Every Layer 2 object must provide:
- `id`: stable identifier such as `concept:rt-minimal-saddle`
- `unit_type`: one of the explicit Layer 2 object families
- `title`
- `summary`
- `maturity`
- `created_at`
- `updated_at`
- `tags`
- `assumptions`
- `regime`
- `scope`
- `provenance`
- `promotion`
- `dependencies`
- `related_units`
- `payload`

## Semantic rules

### 1. Stable identity
`id` should stay stable across edits.
Rename titles when needed, but avoid changing ids unless the underlying object was actually misidentified.

### 2. Explicit type
`unit_type` is mandatory.
Do not infer the type from the folder path or filename.

### 3. Regime and scope are first-class
Layer 2 objects must state where they apply and where they do not apply.
If this is not known well enough, the item is usually still Layer 3 material.

### 4. Provenance is structural
Each object must point back to the evidence path that made promotion legitimate:
- source ids,
- backend refs when an external backend materially seeded the object,
- Layer 1 artifacts,
- Layer 3 runs,
- Layer 4 checks,
- citations if relevant.

For non-trivial numerical or derivation-heavy units, those `L3` and `L4` paths
should include the relevant baseline-reproduction or atomic-understanding
artifacts that justified trust in the method.

`backend_refs` is optional.
Use it when a registered external backend materially shaped the reusable object.

### 5. Promotion path is explicit
The object must say whether it entered Layer 2 via:
- `L1->L2`
- `L3->L4->L2`

Direct `L1->L4->L2` is not allowed.

### 6. Payload holds type-specific content
The common contract stays small.
Type-specific structure lives inside `payload`.

## Maturity states

Use these states consistently:
- `draft`: newly created canonical unit that still needs local cleanup
- `candidate`: shaped enough to discuss, but not yet validated enough to rely on broadly
- `validated`: passed the intended promotion gate and has explicit supporting checks
- `stable`: reliable default reusable object
- `deprecated`: kept for history, but no longer recommended for active reuse

The existence of `draft` or `candidate` in Layer 2 should be exceptional, not the dominant pattern.

## Directory mapping

Default storage projection:
- `atomic_note` -> `canonical/atomic-notes/`
- `concept` -> `canonical/concepts/`
- `claim_card` -> `canonical/claim-cards/`
- `derivation_object` -> `canonical/derivation-objects/`
- `method` -> `canonical/methods/`
- `workflow` -> `canonical/workflows/`
- `bridge` -> `canonical/bridges/`
- `validation_pattern` -> `canonical/validation-patterns/`
- `warning_note` -> `canonical/warning-notes/`

This mapping is operational convenience, not ontology.

## Minimal example

```json
{
  "id": "concept:rt-minimal-saddle",
  "unit_type": "concept",
  "title": "Ryu-Takayanagi minimal saddle dominance",
  "summary": "In the large-c semiclassical regime, the leading entanglement entropy is controlled by the minimal bulk saddle subject to the relevant boundary conditions.",
  "maturity": "validated",
  "created_at": "2026-03-11T12:00:00+08:00",
  "updated_at": "2026-03-11T12:00:00+08:00",
  "tags": ["ads-cft", "entanglement", "holography"],
  "assumptions": [
    "Semiclassical bulk description is valid",
    "Large-c expansion suppresses non-minimal saddles at leading order"
  ],
  "regime": {
    "domain": "AdS/CFT",
    "approximations": ["large-c", "semiclassical bulk"],
    "scale": "leading order",
    "boundary_conditions": ["fixed interval on the boundary"],
    "exclusions": ["phase-transition points between competing saddles"]
  },
  "scope": {
    "applies_to": ["leading-order interval entanglement entropy"],
    "out_of_scope": ["finite-c corrections", "non-semiclassical saddles"]
  },
  "provenance": {
    "source_ids": ["paper:rt-2006"],
    "backend_refs": ["backend:example-human-note-library"],
    "l1_artifacts": ["intake/topics/holographic-entanglement/promotion_candidates.md#L12"],
    "l3_runs": ["feedback/topics/holographic-entanglement/runs/2026-03-11-rt-saddles"],
    "l4_checks": ["validation/topics/holographic-entanglement/runs/2026-03-11-rt-saddles"],
    "citations": ["Ryu and Takayanagi (2006)"]
  },
  "promotion": {
    "route": "L3->L4->L2",
    "promoted_by": "codex",
    "promoted_at": "2026-03-11T12:00:00+08:00",
    "review_status": "accepted",
    "rationale": "Promoted after explicit derivation cross-check and boundary-regime clarification."
  },
  "dependencies": ["concept:semiclassical-bulk-limit"],
  "related_units": ["derivation_object:rt-leading-order-interval-entropy"],
  "payload": {
    "definition": "Minimal bulk extremal surface controls the leading entropy term in the stated regime.",
    "key_distinctions": ["leading-order vs finite-c", "single-saddle regime vs competing saddles"]
  }
}
```

## Machine-readable schema

The JSON Schema companion for this contract lives at:

`canonical/canonical-unit.schema.json`
