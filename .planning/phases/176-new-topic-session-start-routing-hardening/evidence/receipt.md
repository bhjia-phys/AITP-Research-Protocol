# Receipt: Phase 176 New-Topic Session-Start Routing Hardening

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "detects_new_topic_from_natural_language or detects_brand_new_research_topic_named_in_english or prefers_current_topic_reference or from_scratch_new_research_program_outranks_current_topic_memory or projection_hint_does_not_override_current_topic or start_chat_session_materializes_current_topic_route or start_chat_session_allocates_fresh_slug_for_explicit_new_topic_collision or start_chat_session_from_scratch_request_allocates_new_topic_even_with_current_topic_memory" -q
```

## Observed results

- `pytest-session-start-routing.txt`: `8 passed, 147 deselected in 1.90s`

## Key facts

- the long "start a new research program from scratch on ..." request now
  routes as `request_new_topic`
- extracted title:
  `measurement-induced algebraic transition and observer algebras`
- `start_chat_session()` now allocates
  `measurement-induced-algebraic-transition-and-observer-algebras`
  even when durable current-topic memory exists
- the durable `session_start_contract` records the same
  `request_new_topic` route

## Raw artifacts

- `.planning/phases/176-new-topic-session-start-routing-hardening/evidence/pytest-session-start-routing.txt`
