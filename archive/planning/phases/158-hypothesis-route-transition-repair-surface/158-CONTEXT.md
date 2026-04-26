# Phase 158: Hypothesis Route Transition Repair Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.83` research-control slice.

The phase should:

- derive a bounded route transition-repair summary from route transition
  discrepancy plus current route artifacts
- keep bounded repair guidance visible without widening into fresh runtime
  mutation
- coexist with current route transition-discrepancy and helper mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing route transition-discrepancy and helper
  surfaces instead of inventing a disconnected transition subsystem.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  transition repair, do not widen into fresh runtime mutation.
- **D-03:** Preserve the current action queue, transition discrepancy, and
  helper mechanisms as the execution-level machinery.
- **D-04:** Add one isolated acceptance lane so the transition-repair path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/158-hypothesis-route-transition-repair-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- fresh runtime mutation after the repair plan becomes explicit
- multi-branch scheduling and arbitration across many candidates
- helper-driven transition repair without an explicit repair surface

</deferred>

---

*Phase: 158-hypothesis-route-transition-repair-surface*
*Context gathered: 2026-04-12*
