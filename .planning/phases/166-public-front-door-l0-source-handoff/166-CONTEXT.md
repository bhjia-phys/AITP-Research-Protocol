# Phase 166: Public Front Door L0 Source Handoff - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase makes the honest post-bootstrap `return_to_L0` outcome point to one
concrete source-acquisition path. It does not auto-run source
discovery/registration, does not widen beyond the already shipped arXiv-first
entry surfaces, and does not absorb the contentful-registration-default work
reserved for Phase `166.1`.

</domain>

<decisions>
## Implementation Decisions

### Primary handoff lane
- **D-01:** The handoff should expose one primary "start here" lane:
  `research/knowledge-hub/source-layer/scripts/discover_and_register.py` when
  the operator has a natural-language topic statement or query rather than a
  fixed arXiv id.
- **D-02:** The same handoff block should list two secondary direct-entry
  surfaces beside the primary lane:
  `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py` for
  known arXiv ids and `research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md`
  as the operator runbook.
- **D-03:** The wording should stay plain and action-oriented: tell the
  operator what to open or run next, not just that "source and candidate
  artifacts" are missing.

### Surface parity
- **D-04:** `topic_dashboard.md`, `runtime_protocol.generated.md`, and
  `topic_replay_bundle.md` must all surface the same handoff facts from one
  shared runtime payload or source of truth, not three separately maintained
  prose strings.
- **D-05:** Existing selected-action summary and `return_to_L0` truth must stay
  visible; the new handoff augments that surface instead of replacing the
  bounded-action record.

### Honesty boundary
- **D-06:** The handoff remains advisory and explicit only when the chosen
  action is an actual `l0_source_expansion` / `return_to_L0` situation. Do not
  auto-discover, auto-register, or pretend the topic already has sources.
- **D-07:** If the operator already knows an arXiv id, the handoff may point
  directly to registration; otherwise discovery-first remains the recommended
  default.

### Verification boundary
- **D-08:** Phase `166` should add bounded regression coverage for the handoff
  copy and cross-surface parity. The end-to-end proof that continues through
  actual registration belongs to Phase `166.1`.

### the agent's Discretion
- exact field names or helper-object shape for the shared handoff payload
- final markdown formatting of the handoff block on each surface
- whether dashboard/protocol/replay show inline command examples or only path
  references, as long as the primary lane and honesty boundary remain intact

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope and routing
- `.planning/ROADMAP.md` — Phase `166` goal, requirements, and honesty boundary
- `.planning/REQUIREMENTS.md` — `REQ-L0HAND-01` and `REQ-L0HAND-02` define the
  cross-surface handoff contract
- `.planning/BACKLOG.md` — item `999.86` captures the original public-entry
  friction being promoted here

### Prior evidence that triggered this phase
- `.planning/phases/165.6/165.6-01-SUMMARY.md` — proves the public front door
  now works and names `999.86` as the remaining follow-up
- `.planning/phases/165.6/165.6-ISSUE-LEDGER.md` — records the exact generic
  `L0` next-action wording that should now become concrete
- `.planning/phases/165.6/evidence/jones-von-neumann-algebras-public-entry/POSTMORTEM.md`
  — durable evidence for the honest `return_to_L0 source expansion` outcome

### Layer-0 entry surfaces and operator docs
- `research/knowledge-hub/L0_SOURCE_LAYER.md` — defines the current
  discovery-before-registration path and shipped `L0` entrypoints
- `research/knowledge-hub/README.md` — documents the bounded pre-registration
  discovery entrypoint and current acceptance expectations
- `research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md` — operator-facing
  runbook for direct arXiv registration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`: derives
  open-gap summary and dashboard text from `selected_pending_action`; already
  classifies `l0_source_expansion` as a real `return_to_L0`.
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`: composes
  runtime protocol, topic synopsis, minimal execution brief, and truth-source
  pointers; best place to add a shared handoff payload consumed by multiple
  surfaces.
- `research/knowledge-hub/knowledge_hub/topic_replay.py`: materializes replay
  bundle and already exposes `current_position.next_action_summary`.
- `research/knowledge-hub/knowledge_hub/topic_dashboard_surface_support.py`:
  central dashboard write path, so dashboard changes should stay routed through
  this support layer.
- `research/knowledge-hub/source-layer/scripts/discover_and_register.py`,
  `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`, and
  `research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md`: already-shipped
  `L0` entry surfaces that this phase should point at instead of re-implement.

### Established Patterns
- Durable next-step truth comes from `next_action_decision.json|md`,
  `topic_synopsis.runtime_focus`, and related runtime-bundle fields, not from
  ad hoc UI-only strings.
- Dashboard, runtime protocol, and replay already reuse shared runtime
  artifacts; preferred changes should extend shared payload builders rather than
  patch each surface independently.
- Existing tests already assert parity between
  `minimal_execution_brief.selected_action_summary` and
  `topic_synopsis.runtime_focus.next_action_summary`, so new handoff data should
  follow the same parity discipline.

### Integration Points
- `research/knowledge-hub/runtime/scripts/decide_next_action.py` if the
  selected `l0_source_expansion` copy itself needs to become concrete
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py` for gap /
  `return_to_L0` classification and dashboard-facing explainability
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` for
  runtime-protocol and synopsis-level parity
- `research/knowledge-hub/knowledge_hub/topic_replay.py` for replay visibility
- `research/knowledge-hub/tests/test_aitp_mcp_server.py`,
  `research/knowledge-hub/tests/test_aitp_service.py`, and replay/runtime tests
  for regression coverage

</code_context>

<specifics>
## Specific Ideas

- Preferred operator-facing phrasing pattern: "Start with
  `discover_and_register.py` when you have a topic query; if you already know
  the arXiv id, use `register_arxiv_source.py`; use
  `ARXIV_FIRST_SOURCE_INTAKE.md` for the exact command forms."
- Keep the handoff anchored to the honest gap state: surfaces should still say
  the topic is returning to `L0 source expansion`, then immediately name the
  concrete next source-acquisition path.

</specifics>

<deferred>
## Deferred Ideas

- Change `register_arxiv_source.py` default behavior to contentful download;
  that is Phase `166.1`.
- Broaden the handoff to non-arXiv provider families or automatic provider
  selection.
- Auto-trigger discovery or registration directly from the runtime queue.

</deferred>

---

*Phase: 166-public-front-door-l0-source-handoff*
*Context gathered: 2026-04-13*
