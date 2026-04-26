# Phase 1: Topic-Start Hardening - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning
**Mode:** Brownfield continuation from the active working tree and Share_work handoff notes

<domain>
## Phase Boundary

Sharpen source-heavy topic starts so AITP can produce better `idea_packet`
defaults and truthful runtime status surfaces without hiding uncertainty,
route choice, or active human needs.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Use the current working tree in `research/knowledge-hub/knowledge_hub/aitp_service.py`,
  `research/knowledge-hub/runtime/scripts/sync_topic_state.py`, and
  `research/knowledge-hub/runtime/scripts/orchestrate_topic.py` as the starting
  point instead of rewriting the topic-start path from scratch.
- Prefer source-grounded distillation from registered source artifacts and
  original source text before falling back to generic chat text.
- Keep `status_explainability` machine-readable in `topic_state.json` and render
  it outward into human-facing runtime surfaces.
- Preserve AITP protocol semantics; GSD should organize execution but must not
  replace AITP runtime state as the source of truth.

### the agent's Discretion

Heuristic details for novelty extraction and lane-aware first validation routes
may be tightened during implementation as long as the outputs remain bounded,
honest, and source-grounded.

</decisions>

<code_context>
## Existing Code Insights

- `research/knowledge-hub/knowledge_hub/aitp_service.py` owns topic bootstrap
  and currently coalesces `idea_packet` defaults.
- `research/knowledge-hub/runtime/scripts/sync_topic_state.py` is the right
  place to build machine-readable status summaries.
- `research/knowledge-hub/runtime/scripts/orchestrate_topic.py` should render
  existing state rather than invent new semantics.
- `research/knowledge-hub/tests/test_runtime_scripts.py` already contains
  targeted explainability coverage and should be extended before broader claims.

</code_context>

<specifics>
## Specific Ideas

- Use real source content, not only cached summaries, when source previews are
  empty or dominated by comments.
- Distill lane-aware first validation routes for formal-theory and numerical
  starts instead of relying on a single generic sentence.
- Ensure operator-facing surfaces expose `why_this_topic_is_here`,
  `current_route_choice`, `last_evidence_return`, and `active_human_need`.
- Add regression coverage before claiming the phase is complete.

</specifics>

<canonical_refs>
## Canonical References

- `docs/HUMAN_IDEA_AI_EXECUTION_STEERING_PROTOCOL_VNEXT.md`
- `docs/roadmap.md`
- `research/knowledge-hub/runtime/README.md`
- `D:/BaiduSyncdisk/Theoretical-Physics/obsidian-markdown/07 Share_work/2026-03-29_aitp-current-state-and-next-optimization-directions.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- Strategy-memory write/read integration belongs to the next phase unless a
  small helper naturally falls out of current work.
- AITP x GSD coexistence policy and packaging are milestone-later work, not
  blockers for this phase.

</deferred>
