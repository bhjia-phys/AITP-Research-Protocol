# Phase 149: Hypothesis Route Activation Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next post-`v1.74` research-control slice.

The phase should:

- derive a bounded route-activation summary from explicit hypothesis routes
- keep local-route action versus parked-route obligations visible
- coexist with the current queue, steering, deferred, and follow-up mechanisms

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing `competing_hypotheses` route metadata instead
  of inventing a disconnected activation ledger.
- **D-02:** Keep the first slice declarative and operator-visible: summarize
  route activation, do not auto-spawn or schedule branches.
- **D-03:** Preserve the current action queue and existing steering/deferred/
  follow-up surfaces as the execution-level mechanisms.
- **D-04:** Add one isolated acceptance lane so the route-activation path can
  close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `.planning/phases/149-hypothesis-route-activation-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- automatic branch spawning from route activation
- multi-branch scheduling and arbitration
- automatic route adjudication beyond explicit activation summaries

</deferred>

---

*Phase: 149-hypothesis-route-activation-surface*
*Context gathered: 2026-04-12*
