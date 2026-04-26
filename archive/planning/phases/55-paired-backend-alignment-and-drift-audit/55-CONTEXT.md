# Phase 55: Paired-Backend Alignment And Drift Audit - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `54`

<domain>
## Phase Boundary

Add an explicit paired-backend alignment and drift-audit surface so AITP can
inspect the theoretical-physics paired backend as a governed production
operation rather than leaving it only in docs and backend cards.

This phase is about inspection and semantics:

- pairing status
- role separation
- drift/debt status
- maintenance protocol visibility
- distinction between consultation, promotion, and sync semantics

This phase is not yet an automatic resynchronization workflow.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Start with audit/read surfaces first: service payload, CLI entrypoint,
  capability audit, and runtime bundle exposure where appropriate.
- Do not implement silent sync or rebuild in this phase.
- Treat paired-backend governance as separate from:
  - `L2 consultation`
  - promotion gates
  - actual writeback
- Use the existing theoretical-physics pair as the first bounded production
  target:
  - `backend:theoretical-physics-brain`
  - `backend:theoretical-physics-knowledge-network`
- Prefer explicit backend-debt / drift-status reporting over fake "aligned"
  claims.

### the agent's Discretion

- Whether paired-backend audit lives in a dedicated helper module or within an
  existing extracted support area, as long as `aitp_service.py` remains thin.
- Whether runtime exposure lands as enriched `backend_bridges` rows or as a
  sibling surface, as long as the semantics stay explicit and inspectable.

</decisions>

<canonical_refs>
## Canonical References

### Backend pairing and maintenance
- `research/knowledge-hub/canonical/backends/THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md`
  - role separation and no-silent-hierarchy rule.
- `research/knowledge-hub/canonical/L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md`
  - drift audit, backend debt, rebuild, and post-rebuild verification doctrine.
- `research/knowledge-hub/canonical/backends/THEORETICAL_PHYSICS_BACKEND_PAIRING.md`
  - supported paired-backend configuration and downstream-L2 framing.
- `research/knowledge-hub/canonical/backends/theoretical-physics-brain.json`
  - operator-primary backend card.
- `research/knowledge-hub/canonical/backends/theoretical-physics-knowledge-network.json`
  - machine-primary backend card.

### Existing runtime and audit surfaces
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
  - existing backend-bridge exposure in the runtime bundle.
- `research/knowledge-hub/knowledge_hub/capability_audit_support.py`
  - doctor/capability audit surface.
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
  - existing backend-card loading and promotion/consultation entrypoints.
- `research/knowledge-hub/runtime/README.md`
  - runtime shell contract and current `backend_bridges` placement.

</canonical_refs>

<code_context>
## Existing Code Insights

- Runtime already carries `backend_bridges`, but only as a shallow bridge
  snapshot without paired-backend role/debt/drift semantics.
- Promotion and consultation already record backend ids and paths, but no
  explicit paired-backend audit surface exists.
- The docs already define backend debt and drift audit, so the main gap is a
  production read path and operator entrypoint.

</code_context>

<specifics>
## Specific Ideas

- Add a `paired_backend_audit` production entrypoint on the service.
- Add a CLI command for paired-backend audit.
- Enrich runtime/backend audit surfaces with:
  - pair members
  - pairing role (`operator_primary` / `machine_primary`)
  - pairing status
  - drift status
  - backend debt status
  - maintenance protocol path
  - explicit `consultation != promotion != sync` semantics

</specifics>

<deferred>
## Deferred Ideas

- automatic paired-backend rebuild or sync commands
- per-unit cross-backend semantic diffing beyond the first bounded audit slice
- phase-wide docs and doctor parity closeout

</deferred>

---

*Phase: 55-paired-backend-alignment-and-drift-audit*
*Context gathered: 2026-04-11 via milestone synthesis and paired-backend docs*
