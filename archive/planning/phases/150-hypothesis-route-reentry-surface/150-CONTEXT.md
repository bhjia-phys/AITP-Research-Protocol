# Phase 150: Hypothesis Route Re-entry Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.75` research-control slice.

The phase should:

- derive a bounded route re-entry summary from parked hypothesis routes
- keep deferred reactivation conditions and follow-up return readiness visible
- coexist with the current route activation, deferred, and follow-up
  mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing parked-route metadata, deferred buffer
  reactivation conditions, and follow-up return contracts instead of inventing
  a disconnected re-entry ledger.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  re-entry conditions and readiness, do not auto-reactivate candidates or patch
  parent topics.
- **D-03:** Preserve current deferred-reactivation helpers and follow-up
  reintegration as the execution-level mechanisms.
- **D-04:** Add one isolated acceptance lane so the route re-entry path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/GAP_RECOVERY_PROTOCOL.md`
- `research/knowledge-hub/runtime/DEFERRED_RUNTIME_CONTRACTS.md`
- `research/knowledge-hub/knowledge_hub/followup_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `.planning/phases/150-hypothesis-route-reentry-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic candidate reactivation from the new re-entry summary
- automatic parent-topic mutation from follow-up child return packets
- broader branch spawning, multi-branch scheduling, and route adjudication

</deferred>

---

*Phase: 150-hypothesis-route-reentry-surface*
*Context gathered: 2026-04-12*
