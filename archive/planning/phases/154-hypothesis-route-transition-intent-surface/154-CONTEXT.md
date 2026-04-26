# Phase 154: Hypothesis Route Transition Intent Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.79` research-control slice.

The phase should:

- derive a bounded route transition-intent summary from route choice plus
  route-transition-gate state
- keep source-to-target transition intent visible without mutating runtime state
- coexist with current route transition-gate and helper mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing route choice, route-transition-gate, and
  helper surfaces instead of inventing a disconnected transition subsystem.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  transition intent, do not auto-mutate runtime state.
- **D-03:** Preserve the current action queue, route gate, and helper
  mechanisms as the execution-level machinery.
- **D-04:** Add one isolated acceptance lane so the transition-intent path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/154-hypothesis-route-transition-intent-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic route mutation after the transition intent becomes explicit
- route-transition receipts or automatic commit ledgers
- multi-branch scheduling and arbitration across many candidates

</deferred>

---

*Phase: 154-hypothesis-route-transition-intent-surface*
*Context gathered: 2026-04-12*
