# Phase 176.2 Summary: Fresh Real-Topic First-Use Replay Proof

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

## What was done

Phase `176.2` closed milestone `v2.2` with one replayable bounded first-use
proof package.

### Fixes landed

- `run_first_run_topic_acceptance.py` now replays source registration and
  immediate post-registration `status` verification instead of stopping at the
  pre-registration handoff
- a dedicated runtime-script regression now proves the first-run acceptance
  script succeeds on an isolated work root with local tarball-backed metadata
- durable replay receipts now show runtime-status refresh and immediate
  `source_count >= 1` after registration

## Acceptance criteria

- [x] one runtime-script regression proves the first-run acceptance lane can
      continue into registration on an isolated work root
- [x] one replay receipt proves post-registration `status` exposes
      `source_count >= 1`
- [x] the phase closes with durable receipts and explicit non-claims

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-runtime-script.txt` | `phases/176.2-fresh-real-topic-first-use-replay-proof/evidence/` | Runtime-script acceptance receipt |
| `first-run-replay.json` | `phases/176.2-fresh-real-topic-first-use-replay-proof/evidence/` | Raw first-use replay showing post-registration status coherence |
| `receipt.md` | `phases/176.2-fresh-real-topic-first-use-replay-proof/evidence/` | Human-readable replay receipt |

## What this phase proved

1. The bounded first-run lane can start from fresh bootstrap and continue into
   source registration mechanically.
2. Post-registration status surfaces immediately expose `source_count >= 1`
   on that bounded lane.
3. The whole `v2.2` first-use reliability slice is now replayable end to end.

## Explicit non-claims

- This phase does not prove that post-registration action selection is fully
  rerouted away from the original L0 handoff text.
- This phase does not widen any scientific closure claim in the formal,
  toy-model, or first-principles lanes.
