# Phase 152: Hypothesis Route Choice Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.77` research-control slice.

The phase should:

- derive a bounded route choice summary from the active local route plus the
  primary handoff candidate
- keep stay-local versus yield-to-handoff choice visible
- coexist with the current current-route-choice, route activation, route
  re-entry, and route handoff mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing `current_route_choice`, `route_activation`,
  `route_reentry`, and `route_handoff` surfaces instead of inventing a
  disconnected route-choice ledger.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  stay-local versus yield choice, do not auto-mutate runtime state.
- **D-03:** Preserve the current action queue and helper mechanisms as the
  execution-level machinery.
- **D-04:** Add one isolated acceptance lane so the route-choice path can close
  independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/topic_status_explainability_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/152-hypothesis-route-choice-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic route mutation or handoff execution
- multi-branch scheduling and arbitration across many candidates
- helper-driven current-route replacement without an explicit choice summary

</deferred>

---

*Phase: 152-hypothesis-route-choice-surface*
*Context gathered: 2026-04-12*
