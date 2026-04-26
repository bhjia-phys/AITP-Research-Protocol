# Phase 147: Research Question Competing Hypotheses Surface - Context

**Gathered:** 2026-04-12
**Status:** Ready for execution

<domain>
## Phase Boundary

This phase owns the next research-question control slice.

The phase should:

- record multiple live hypotheses explicitly at the question layer
- keep their bounded status and evidence summaries visible
- coexist with deferred candidates and follow-up subtopics

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Extend the research-question contract and runtime/replay surfaces
  instead of inventing a disconnected hypothesis registry.
- **D-02:** Keep the first slice bounded to explicit hypothesis visibility, not
  full multi-branch execution automation.
- **D-03:** Preserve compatibility with deferred candidates and follow-up
  subtopics as execution-level mechanisms.
- **D-04:** Add one isolated acceptance lane so the question-level
  multi-hypothesis path can close independently.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/knowledge_hub/topic_replay.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- `.planning/phases/147-research-question-competing-hypotheses-surface/PHASE.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- full branch scheduling/automation per competing hypothesis
- broader evaluator analytics across hypothesis competition
- automatic promotion/demotion across many hypotheses without explicit bounded review

</deferred>

---

*Phase: 147-research-question-competing-hypotheses-surface*
*Context gathered: 2026-04-12*
