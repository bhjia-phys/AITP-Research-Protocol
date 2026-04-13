# Phase 177.2 Summary: Fresh First-Use Post-Registration Replay Proof

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

## What was done

Phase `177.2` closed milestone `v2.3` with one replayable first-use
post-registration proof package.

### Fixes landed

- the first-run acceptance script now asserts both runtime-state coherence and
  non-stale post-registration route selection
- the runtime-script regression now proves the whole first-use transition on an
  isolated work root
- durable replay receipts now show the updated `topic_state` and the updated
  next-action summary in one packet

## Acceptance criteria

- [x] one runtime-script regression proves the first-use lane reaches the
      post-registration route transition on an isolated work root
- [x] one replay receipt proves `topic_state.source_count = 1` and a non-stale
      post-registration `selected_action_summary`

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-runtime-script.txt` | `phases/177.2-fresh-first-use-post-registration-replay-proof/evidence/` | Runtime-script acceptance receipt |
| `first-use-post-registration-replay.json` | `phases/177.2-fresh-first-use-post-registration-replay-proof/evidence/` | Raw replay packet for the bounded first-use route transition |
| `receipt.md` | `phases/177.2-fresh-first-use-post-registration-replay-proof/evidence/` | Human-readable replay receipt |

## What this phase proved

1. The bounded first-use lane now updates runtime state and next-action
   selection together after first-source registration.
2. The whole `v2.3` post-registration route-coherence slice is mechanically
   replayable.
