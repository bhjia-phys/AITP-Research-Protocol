# Phase 157: Hypothesis Route Transition Discrepancy Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.82` research-control slice.

The phase should:

- derive a bounded route transition-discrepancy summary from route transition
  resolution plus upstream route artifacts
- keep inconsistent transition state visible without widening into fresh runtime
  mutation
- coexist with current route transition-resolution and helper mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing route transition-resolution and helper
  surfaces instead of inventing a disconnected transition subsystem.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  transition discrepancy, do not widen into fresh runtime mutation.
- **D-03:** Preserve the current action queue, transition resolution, and helper
  mechanisms as the execution-level machinery.
- **D-04:** Add one isolated acceptance lane so the transition-discrepancy path
  can close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/157-hypothesis-route-transition-discrepancy-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- fresh runtime mutation after the discrepancy becomes explicit
- multi-branch scheduling and arbitration across many candidates
- helper-driven transition repair without an explicit discrepancy surface

</deferred>

---

*Phase: 157-hypothesis-route-transition-discrepancy-surface*
*Context gathered: 2026-04-12*
