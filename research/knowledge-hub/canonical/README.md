# Layer 2 — Canonical Reusable Knowledge Base

This is the reusable center of OMTP.

Layer 2 is defined first by the `CanonicalUnit` contract, not by folder names alone.
The directory layout is a storage projection of typed objects, not the ontology itself.

Core docs:
- `CANONICAL_UNIT.md`
- `canonical-unit.schema.json`
- `LAYER2_OBJECT_FAMILIES.md`
- `L2_COMPILER_PROTOCOL.md`
- `L2_MVP_CONTRACT.md`
- `L2_STAGING_PROTOCOL.md`
- `L2_BACKEND_BRIDGE.md`
- `L2_BACKEND_INTEGRATION_PROTOCOL.md`
- `L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md`
- `PROMOTION_POLICY.md`
- `L3_L4_LOOP.md`
- `examples/paper-result-decomposition.md`
- `../INDEXING_RULES.md`
- `edges.jsonl`
- `retrieval_profiles.json`
- `backends/`

Store only material that is worth reusing across topics or runs:
- atomic notes as a transitional fallback for sharply scoped reusable units,
- concept notes,
- physical-picture notes,
- claim cards,
- derivation objects,
- method notes,
- workflows,
- topic-skill projections,
- bridge notes,
- validation patterns,
- warning notes.

Typed families:
- `atomic_note`
- `concept`
- `physical_picture`
- `claim_card`
- `derivation_object`
- `method`
- `workflow`
- `topic_skill_projection`
- `bridge`
- `validation_pattern`
- `warning_note`

Use `index.jsonl` as the cross-cutting catalog.
Use `edges.jsonl` as the lightweight relation layer.
Use `retrieval_profiles.json` as the stage-aware retrieval policy surface.
Use `backends/` as the internal bridge registry for external human/software knowledge stores.
Use `compiled/` for derived consultation/reuse helper surfaces only.
Use `compiled/obsidian_l2/` for the fixed-folder Obsidian-friendly Markdown mirror over canonical units.
Inside `compiled/obsidian_l2/`, use:
- `families/<family>/index.md` for ontology-family browsing
- `profiles/<retrieval_profile>.md` for stage/read-depth shelves
- `topics/<topic_slug>.md` for topic-linked evidence shelves over global reusable units
  Topic shelves should keep fixed sections such as `Origin`, `Validated`,
  `Reused`, and `Failed Or Limited` so human browsing does not depend on ad hoc
  role strings.
Use `hygiene/` for audit-only workspace reports over canonical `L2`.
Use `staging/` for provisional or scratch `L2`-adjacent material that is not
yet trusted canonical memory.
Keep topic-linked evidence on canonical units visible and honest.
In particular, `reuse_receipts` may be backwritten when a bounded `L3`
iteration plan explicitly cites canonical `L2` units as part of its reuse basis,
and may later accumulate `l3_synthesis` or staging receipts when that reuse was
actually carried through a bounded iteration.
Use `L2_BACKEND_INTEGRATION_PROTOCOL.md` as the unified rule for adding future backends.
Use `L2_COMPILER_PROTOCOL.md` as the contract for canonical-versus-compiled-
versus-staging behavior.
Use `L2_STAGING_PROTOCOL.md` as the contract for provisional staging behavior.
Promotion into this layer should usually come through explicit Layer 4 validation, not by default.
Keep promotion queues, unresolved prerequisites, research blockers, and run-local TODOs in Layer 3 rather than here.
Keep high-level `L2` compiler semantics in protocol docs, schemas, JSON policy,
or templates rather than growing them ad hoc inside giant Python service files.
