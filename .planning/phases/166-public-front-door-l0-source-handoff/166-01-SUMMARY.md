# Phase 166-01 Summary

Status: implemented in working tree

## Goal

Turn the honest post-bootstrap `return_to_L0` outcome into one concrete,
shared, operator-facing source-acquisition handoff across bootstrap wording,
dashboard, runtime protocol, and replay without widening into automatic source
recovery or Phase `166.1` registration-default changes.

## What Landed

- the bootstrap-seeded `next_actions.md` handoff is now concrete:
  - `source-layer/scripts/discover_and_register.py`
  - `source-layer/scripts/register_arxiv_source.py`
  - `intake/ARXIV_FIRST_SOURCE_INTAKE.md`
- `runtime_focus` now carries one shared `l0_source_handoff` payload when the
  topic is honestly blocked on `L0 source expansion`
- `topic_dashboard.md`, `runtime_protocol.generated.md`, and
  `topic_replay_bundle.md` now render the same `L0` handoff facts from that
  shared payload instead of drifting prose
- topic synopsis and progressive-disclosure runtime bundle schemas now expose
  the `l0_source_handoff` structure
- the compact MCP-facing fixture was updated to reflect the new concrete
  handoff wording
- `test_runtime_scripts.py` now restores the full acceptance-script loader set
  inside `setUp`, so the targeted full phase sweep is runnable again

## Verification

- `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py -q`
  - result: `157 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_mcp_server.py research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_topic_replay.py research/knowledge-hub/tests/test_runtime_scripts.py -q`
  - result: `223 passed`
- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py -q`
  - result: `11 passed`

## Outcome

`REQ-L0HAND-01` and `REQ-L0HAND-02` are now satisfied:

- a fresh public bootstrap no longer leaves the operator with only generic
  prose at the `L0` boundary
- dashboard, runtime protocol, and replay expose the same concrete handoff
  surface
- the handoff remains advisory and honest about missing sources

## Remaining Open Work After 166

- `166.1-01` still needs to make arXiv registration contentful-by-default
- `REQ-VERIFY-01` remains open until the milestone proves
  `bootstrap -> handoff -> registration` on a fresh topic
