# Layer 2 — Canonical Reusable Knowledge Base

This is the reusable center of OMTP.

Layer 2 is defined first by the `CanonicalUnit` contract, not by folder names alone.
The directory layout is a storage projection of typed objects, not the ontology itself.

Core docs:
- `CANONICAL_UNIT.md`
- `canonical-unit.schema.json`
- `LAYER2_OBJECT_FAMILIES.md`
- `L2_MVP_CONTRACT.md`
- `L2_BACKEND_BRIDGE.md`
- `L2_BACKEND_INTEGRATION_PROTOCOL.md`
- `L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md`
- `PROMOTION_POLICY.md`
- `L3_L4_LOOP.md`
- `examples/paper-result-decomposition.md`
- `../../docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `../INDEXING_RULES.md`
- `edges.jsonl`
- `retrieval_profiles.json`
- `backends/`

Store only material that is worth reusing across topics or runs:
- atomic notes as a transitional fallback for sharply scoped reusable units,
- concept notes,
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
Use `L2_BACKEND_INTEGRATION_PROTOCOL.md` as the unified rule for adding future backends.
Use `L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md` as the explicit drift-audit,
backend-debt, and rebuild rule for paired downstream realizations.
Promotion into this layer should usually come through explicit Layer 4 validation, not by default.
Keep promotion queues, unresolved prerequisites, research blockers, and run-local TODOs in Layer 3 rather than here.

Current `v1.28` scope stops at governance-plane closure and paired-backend
maintenance semantics.
Graph activation, traversal, and populated retrieval remain later work.
