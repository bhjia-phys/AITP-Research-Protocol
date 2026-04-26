# Phase 151: Hypothesis Route Handoff Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.76` research-control slice.

The phase should:

- derive a bounded route handoff summary from the current route plus parked
  route readiness
- keep ready parked-route candidates and keep-parked decisions visible
- coexist with the current route activation, route re-entry, and helper
  mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing `route_activation`, `route_reentry`,
  deferred-reactivation, and follow-up return contracts instead of inventing a
  disconnected handoff ledger.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  handoff candidates and deferrals, do not auto-reactivate or auto-reintegrate
  routes.
- **D-03:** Preserve the current action queue and helper actions as the
  execution-level mechanisms.
- **D-04:** Add one isolated acceptance lane so the route handoff path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `research/knowledge-hub/runtime/DEFERRED_RUNTIME_CONTRACTS.md`
- `research/knowledge-hub/GAP_RECOVERY_PROTOCOL.md`
- `.planning/phases/151-hypothesis-route-handoff-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic route reactivation or automatic parent-topic reintegration
- multi-branch scheduling and arbitration across many ready parked routes
- route adjudication heuristics that mutate runtime state without a durable
  handoff summary

</deferred>

---

*Phase: 151-hypothesis-route-handoff-surface*
*Context gathered: 2026-04-12*
