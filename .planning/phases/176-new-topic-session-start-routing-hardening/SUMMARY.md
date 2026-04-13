# Phase 176 Summary: New-Topic Session-Start Routing Hardening

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human experience) + Axis 5 (agent-facing steering)

## What was done

Phase `176` closed the first front-door reliability slice of milestone
`v2.2`.

### Fixes landed

- `_extract_new_topic_title()` now recognizes long fresh-topic requests phrased
  as new research programs/projects, including "from scratch" wording
- topic-title trimming now discards follow-up steering clauses such as
  "keep the run bounded..." and "do not continue the current topic"
- route-level and `start_chat_session()` regressions now prove that explicit
  fresh-topic intent outranks durable current-topic memory in the bounded case

## Acceptance criteria

- [x] a long "from scratch" new-topic request outranks durable current-topic
      memory at route time
- [x] `start_chat_session()` records the same new-topic route durably
- [x] existing bounded current-topic and explicit new-topic routing regressions
      remain green

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-session-start-routing.txt` | `phases/176-new-topic-session-start-routing-hardening/evidence/` | Bounded routing regression slice covering old and new front-door cases |
| `receipt.md` | `phases/176-new-topic-session-start-routing-hardening/evidence/` | Human-readable replay receipt |

## What this phase proved

1. Fresh-topic intent can now outrank current-topic fallback even inside a long
   natural-language request that also mentions bounded autonomous continuation.
2. The durable `session-start` contract stays aligned with the corrected route
   instead of recording a stale current-topic continuation.
3. The bounded fix preserves the earlier explicit-new-topic and current-topic
   routing regressions.

## Explicit non-claims

- This phase does not yet solve Windows long-path first-source registration.
- This phase does not yet repair status-facing `L0` coherence after successful
  source registration.
- This phase does not redesign the broader projection-routing or retrieval
  stack beyond the bounded fresh-topic intent case.
