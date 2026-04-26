# Phase 153: Hypothesis Route Transition Gate Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.78` research-control slice.

The phase should:

- derive a bounded route transition-gate summary from route choice plus current
  gating state
- keep transition availability versus gating visible
- coexist with current route choice and helper mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing route choice, operator checkpoint, and helper
  surfaces instead of inventing a disconnected transition ledger.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  transition gating, do not auto-mutate runtime state.
- **D-03:** Preserve the current action queue and helper mechanisms as the
  execution-level machinery.
- **D-04:** Add one isolated acceptance lane so the transition-gate path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/topic_status_explainability_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/153-hypothesis-route-transition-gate-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic route mutation after the gate becomes available
- multi-branch scheduling and arbitration across many candidates
- helper-driven route transition without an explicit gate surface

</deferred>

---

*Phase: 153-hypothesis-route-transition-gate-surface*
*Context gathered: 2026-04-12*
