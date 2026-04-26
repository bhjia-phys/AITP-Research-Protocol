# Phase 75: Research Trajectory And Cross-Session Continuity - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Second implementation phase for `v1.48`

<domain>
## Phase Boundary

Continue `v1.48` by turning raw collaborator-memory trajectory rows into a
durable cross-session continuity surface.

This phase must:

- derive `research_trajectory.active.json|md` from trajectory-memory rows
- surface recent trajectory through status, current-topic memory, and
  session-start continuity paths
- keep the runtime-watch hotspots within budget

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse only collaborator-memory rows with `memory_kind="trajectory"`.
- Keep trajectory continuity distinct from `collaborator_profile`; profile is
  stable collaborator shape, trajectory is recent research-arc carryover.
- Surface adjacent-topic continuity through `related_topic_slugs` and
  `recent_related_topic_slugs`.

### the agent's Discretion

- Whether runtime bundle also needs the trajectory surface in this phase.
- How much adjacent-topic detail to surface without bloating the continuity
  note.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `research/knowledge-hub/knowledge_hub/research_trajectory_support.py`
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_schema_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Trajectory rows already lived inside collaborator memory, so the gap was not
  storage but durable read surfaces.
- `current_topic.json|md` and session-start were the most direct continuity
  surfaces to upgrade once trajectory became a standalone artifact.
- Runtime-bundle watch budgets stayed tight, so the phase favored extracted
  helper logic and thin integration.

</code_context>

<specifics>
## Specific Ideas

- Add `research_trajectory.active.json|md`.
- Derive latest run id, related topics, recent related topics, and a continuity
  summary from trajectory rows.
- Project trajectory status, summary, and durable paths into current-topic
  memory and session-start artifacts.

</specifics>

<deferred>
## Deferred Ideas

- learned mode or route guidance from strategy-memory rows
- milestone-close docs and non-mocked continuity acceptance packaging

</deferred>

---

*Phase: 75-research-trajectory-and-cross-session-continuity*
*Context captured on 2026-04-11 after Phase 75 implementation and verification*
