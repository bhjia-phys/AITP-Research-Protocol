# RUNBOOK: Phase 176 New-Topic Session-Start Routing Hardening

## Purpose

Replay the bounded front-door routing fix that makes explicit fresh-topic
"from scratch" requests allocate a new topic instead of falling back to stale
current-topic memory.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "detects_new_topic_from_natural_language or detects_brand_new_research_topic_named_in_english or prefers_current_topic_reference or from_scratch_new_research_program_outranks_current_topic_memory or projection_hint_does_not_override_current_topic or start_chat_session_materializes_current_topic_route or start_chat_session_allocates_fresh_slug_for_explicit_new_topic_collision or start_chat_session_from_scratch_request_allocates_new_topic_even_with_current_topic_memory" -q
```

## Expected success markers

- regression slice: `8 passed`
- the long "start a new research program from scratch on ..." request routes as
  `request_new_topic`
- the extracted topic title is
  `measurement-induced algebraic transition and observer algebras`
- `start_chat_session()` persists the same `request_new_topic` route into the
  session-start contract

## Current success boundary

This phase only hardens fresh-topic intent recognition at the public front
door. It does not yet solve Windows first-source registration or status-sync
coherence after registration.
