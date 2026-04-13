# Context: Phase 176 New-Topic Session-Start Routing Hardening

## Why this phase exists

After `v2.1` closed the bounded fresh-topic `L2` hardening slice, the same
measurement-induced / observer-algebra real-topic run still exposed a public
front-door regression: a long natural-language request that clearly asked to
start a new research program from scratch was routed back onto durable
current-topic memory and reopened `fresh-jones-finite-dimensional-factor-closure`.

This is dangerous because it silently contaminates a fresh topic request with
stale runtime state and makes later AITP artifacts appear valid even though the
initial route choice was wrong.

## Root cause

- `route_codex_chat_request()` already checks new-topic routing before
  current-topic fallback.
- The failure was narrower: `_extract_new_topic_title()` did not recognize
  "start a new research program from scratch on ..." as a fresh-topic request.
- Once that extraction failed, the later `current topic` wording in the same
  request matched the current-topic reference rule and won the route.

## Files in scope

- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_service.py`

## Boundaries

- Do not redesign the full front-door routing stack.
- Do not touch source registration or Windows path handling yet; that is
  deferred to Phase `176.1`.
- Keep the fix bounded to fresh-topic intent recognition and the durable
  `session-start` route it feeds.
