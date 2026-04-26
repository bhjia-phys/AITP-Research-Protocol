# Phase 145: Structured Transition And Demotion Trace - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next runtime-history closure slice.

The phase should:

- record forward and backward layer transitions explicitly
- keep demotion reasons and evidence refs durable
- extend runtime replay/read paths rather than inventing a disconnected
  history subsystem

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Build on the existing `resume_stage`, `last_materialized_stage`,
  `promotion_trace`, and topic replay surfaces.
- **D-02:** Treat backward moves as first-class research progress, not as an
  exceptional hidden state correction.
- **D-03:** Keep the first milestone bounded to transition/demotion visibility,
  not full competing-hypothesis management.
- **D-04:** Add one isolated acceptance lane so runtime-history closure does not
  depend on a broader full-suite replay overhaul.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/runtime_projection_handler.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `research/knowledge-hub/knowledge_hub/promotion_gate_support.py`
- `.planning/phases/145-structured-transition-and-demotion-trace/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- human modification capture inside the L2 approval gate
- full competing-hypothesis question modeling
- broader evaluator-divergence analytics beyond the transition/demotion record

</deferred>

---

*Phase: 145-structured-transition-and-demotion-trace*
*Context gathered: 2026-04-12*
