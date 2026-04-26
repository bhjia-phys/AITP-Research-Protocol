# Phase 72: Research-Judgment Signals In Decision Surfaces - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Phase 72 after closing `Phase 71`

<domain>
## Phase Boundary

Make runtime decision surfaces expose bounded research judgment instead of only
opaque heuristic selection:

- derive durable momentum / stuckness / surprise signals from existing runtime,
  strategy-memory, and collaborator-memory artifacts
- materialize those signals as a reviewable runtime artifact
- project them into status, synopsis, runtime bundle, and decision-surface
  snapshots
- keep watched hotspot files within maintainability budgets

This phase is about decision-surface explainability and durable judgment
signals.
It is not yet the milestone-close acceptance pass.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Judgment signals must come from durable runtime artifacts, not a new hidden
  heuristic engine.
- `momentum`, `stuckness`, and `surprise` must be visible through production
  status/runtime surfaces, not only internal helper returns.
- A dedicated `research_judgment.active.json/.md` runtime artifact is the
  right durability surface for this phase.

### the agent's Discretion

- Exact signal-status vocabulary for momentum.
- Which durable artifacts should count as supporting refs for each signal.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/research_judgment_support.py`
- `research/knowledge-hub/knowledge_hub/research_judgment_runtime_support.py`
- `research/knowledge-hub/knowledge_hub/topic_status_explainability_support.py`
- `research/knowledge-hub/knowledge_hub/runtime_truth_service.py`
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`
- `research/knowledge-hub/tests/test_runtime_profiles_and_projections.py`
- `research/knowledge-hub/tests/test_schema_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Collaborator-memory rows for `stuckness` and `surprise` already existed, but
  they were not part of runtime decision surfaces.
- Strategy-memory and last-evidence-return surfaces already gave enough durable
  context to derive bounded momentum without inventing a new planner.
- The cleanest way to stay under maintainability budgets was to extract both
  judgment runtime helpers and topic-status explainability helpers out of the
  watched hotspot modules.

</code_context>

<specifics>
## Specific Ideas

- Materialize `runtime/topics/<topic>/research_judgment.active.json/.md`.
- Make `topic_synopsis.runtime_focus` expose `momentum_status`,
  `stuckness_status`, `surprise_status`, and `judgment_summary`.
- Make runtime-bundle `decision_surface` snapshots carry the same judgment
  signals plus the review note path.
- When judgment signals are active, add the research-judgment note to the
  bounded `must_read_now` set.

</specifics>

<deferred>
## Deferred Ideas

- milestone-close docs and acceptance packaging
- final verification-close artifact for the whole `v1.47` milestone

</deferred>

---

*Phase: 72-research-judgment-signals-in-decision-surfaces*
*Context captured on 2026-04-11 after Phase 72 implementation and verification*
