# Phase 58: MVP Node-Family Activation And `physical_picture` Closure - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing `v1.43`

<domain>
## Phase Boundary

Turn the declared `L2` MVP family surface into a real production contract by
activating `physical_picture` across schema/docs/seed/retrieval paths and
making the MVP subset explicit in the places the code already uses.

This phase is about vocabulary activation and bounded seed-path closure.

It is not yet about full graph retrieval maturity, multi-backend federation,
or broad ontology expansion.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- `physical_picture` must stop being reserved-only design language and become a
  real `CanonicalUnit` / backend-target / seedable family.
- The MVP subset must stay bounded:
  - `concept`
  - `theorem_card`
  - `method`
  - `assumption_card`
  - `physical_picture`
  - `warning_note`
- The first implementation slice should prefer the already-existing
  `l2_graph.py` and canonical schema/docs instead of inventing a parallel
  graph subsystem.
- Trust boundaries stay explicit: staging and seeding are not promotion.

### the agent's Discretion

- The exact seeded `physical_picture` example for the first direction, as long
  as it is real `L2` data and retrieval can surface it.
- Whether the phase updates only the graph helper path or also a small number
  of service/bridge mappings when required by the new family.

</decisions>

<canonical_refs>
## Canonical References

### MVP contract
- `research/knowledge-hub/canonical/L2_MVP_CONTRACT.md` - current MVP surface
  and the current reserved-only status of `physical_picture`
- `research/knowledge-hub/canonical/LAYER2_OBJECT_FAMILIES.md` - typed family
  contract that needs a real `physical_picture` family
- `research/knowledge-hub/canonical/canonical-unit.schema.json` - canonical
  unit activation boundary
- `research/knowledge-hub/schemas/l2-backend.schema.json` - backend-target
  activation boundary

### Existing production helpers
- `research/knowledge-hub/knowledge_hub/l2_graph.py` - current seeded graph,
  staging-aware consult path, and demo direction helper
- `research/knowledge-hub/knowledge_hub/l2_staging.py` - lightweight staging
  production surface
- `research/knowledge-hub/knowledge_hub/tpkn_bridge.py` - backend type mapping
  that may need the new family

### Existing regression anchors
- `research/knowledge-hub/tests/test_schema_contracts.py`
- `research/knowledge-hub/tests/test_l2_graph_activation.py`
- `research/knowledge-hub/tests/test_l2_backend_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- `L2_MVP_CONTRACT.md` already names `physical_picture`, but only as a reserved
  family and explicitly says schema/object-family support is not active yet.
- `l2_graph.py` already seeds one small direction and supports consultation plus
  staging-aware retrieval, so the code path exists but the MVP vocabulary is
  not yet fully aligned with the contract.
- Backend schemas and bridge mappings currently do not include
  `physical_picture`, so the MVP surface is still inconsistent across docs,
  schema, and writeback.

</code_context>

<specifics>
## Specific Ideas

- Add `physical_picture` to:
  - `canonical-unit.schema.json`
  - `l2-backend.schema.json`
  - backend cards where canonical targets are enumerated
  - `tpkn_bridge.py`
  - `l2_graph.py` family directory mapping
- Seed one TFIM-facing `physical_picture` unit into the MVP demo direction
- Update MVP docs so `physical_picture` is active rather than reserved

</specifics>

<deferred>
## Deferred Ideas

- broader graph traversal and consultation ranking policy
- CLI/service command family for L2 seeding and consult
- larger real-topic graph seeding beyond the first bounded direction

</deferred>

---

*Phase: 58-mvp-node-family-activation-and-physical-picture-closure*
*Context gathered: 2026-04-11 via backlog promotion and current L2 helper inspection*
