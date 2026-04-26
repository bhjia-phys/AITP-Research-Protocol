# Phase 148: Hypothesis Branch Routing Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.73` research-control slice.

The phase should:

- record explicit branch-routing intent on each active competing hypothesis
- keep route kind and target summary visible through runtime and replay
- coexist with existing steering, deferred, and follow-up mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Extend existing `competing_hypotheses` rows instead of inventing a
  disconnected branch ledger.
- **D-02:** Keep the first slice declarative: visible route intent, not
  automatic branch spawning or scheduling.
- **D-03:** Preserve innovation-direction steering, deferred candidates, and
  follow-up subtopics as downstream execution mechanisms.
- **D-04:** Add one isolated acceptance lane so the hypothesis-routing path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `.planning/phases/148-hypothesis-branch-routing-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic hypothesis-to-branch spawning
- multi-branch scheduling and arbitration across many hypotheses
- implicit adjudication heuristics that choose branch destinations without a
  durable declared route

</deferred>

---

*Phase: 148-hypothesis-branch-routing-surface*
*Context gathered: 2026-04-12*
