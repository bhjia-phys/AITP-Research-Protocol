# Phase 78: Quick Exploration Entrypoint And Lightweight Session - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** First implementation phase for `v1.49`

<domain>
## Phase Boundary

Open `v1.49` by making lightweight speculative work a first-class AITP path.

This phase must:

- add a first-class `aitp explore` entrypoint
- materialize a lightweight exploration session under `runtime/explorations/`
- skip full topic bootstrap while still reusing current-topic context when it exists

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- quick exploration must not silently call the normal topic bootstrap path
- quick exploration should reuse current-topic context only if it is already durable
- the artifact footprint for this phase should stay at a tiny two-file session carrier

### the agent's Discretion

- exact session payload fields and promotion-path wording
- whether to add an exploration index now or defer it until artifact-footprint work

</decisions>

<canonical_refs>
## Canonical References

- `.planning/BACKLOG.md`
- `research/knowledge-hub/knowledge_hub/exploration_session_support.py`
- `research/knowledge-hub/knowledge_hub/cli_frontdoor_handler.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`

</canonical_refs>

---

*Phase: 78-quick-exploration-entrypoint-and-lightweight-session*
*Context captured on 2026-04-11 after Phase 78 implementation and verification*
