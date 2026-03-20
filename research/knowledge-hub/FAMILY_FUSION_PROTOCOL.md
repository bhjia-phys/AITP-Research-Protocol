# Family Fusion Protocol

This file defines the public AITP contract for multi-source fusion of
definitions, theorems, notation, and derivation families.

Fusion is allowed because reusable theory knowledge must eventually cross paper
boundaries.
Fusion is dangerous because papers often present similar claims with different
assumptions, notation, or proof routes.

This protocol exists to keep that fusion honest.

## 1. Why this exists

If AITP treats every paper-local phrasing as a separate object forever, the
knowledge base never becomes reusable.

If AITP merges them too aggressively, it invents a false consensus.

The correct middle path is family-level fusion with explicit source-local
projections and explicit conflict records.

## 2. Core family surfaces

AITP family-aware backends should expose, or be mappable to:

- `theorem_family`
- `definition_family`
- `notation_family`
- `source_fusion_record`
- `conflict_record`

These objects let the system say:

- which source-local units belong to the same reusable family,
- which assumptions were preserved,
- which notation was normalized,
- which differences remain unresolved.

## 3. Fusion admission rule

Two source-local objects should be placed in the same family only when:

- the core claim or definition is substantively the same,
- regime and scope are compatible or explicitly parameterized,
- notation differences are recoverable,
- the merged object does not erase a real disagreement.

Do not fuse merely because titles sound similar.

## 4. Conflict preservation rule

When two nearby sources disagree about:

- assumptions,
- domain of validity,
- normalization,
- proof route,
- or even the exact statement,

the disagreement must survive as a durable conflict surface.

Family fusion should reduce redundancy, not erase scientific structure.

## 5. Source fusion record

A durable source-fusion record should explain:

- why the objects were grouped,
- what the canonical family boundary is,
- which source-local details remain attached to each member,
- which unresolved tensions still block stronger fusion.

This record is the audit trail for later retrieval and regression.

## 6. Runtime trigger handshake

The runtime bundle should treat family fusion as a deeper read when:

- `contradiction_detected` fires,
- a proof-completion review reveals source-local proof divergence,
- or promotion would otherwise conflate distinct source statements.

When triggered, the next agent must open:

- `FAMILY_FUSION_PROTOCOL.md`,
- the active source-fusion or conflict artifacts,
- the affected consultation and validation records,
- the candidate or backend objects under possible fusion.

## 7. Script boundary

Scripts may:

- aggregate candidate members into a family view,
- render comparison tables,
- validate family metadata and member references.

Scripts may not decide:

- that two theorem statements are truly equivalent,
- that a normalization change is only cosmetic,
- or that a contradiction can be ignored.

Those are substantive theoretical judgments.
