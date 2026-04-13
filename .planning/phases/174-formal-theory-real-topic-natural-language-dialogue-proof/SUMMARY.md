# Phase 174 Summary: Formal-Theory Real-Topic Natural-Language Dialogue Proof

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 2 (inter-layer connection) + Axis 5 (agent-facing steering)

## What was done

Phase `174` closed the formal-theory leg of the new real-topic natural-language
dialogue milestone.

### Proof route

- started from a fresh natural-language formal request in the Jones / von
  Neumann algebra direction
- kept the route tied to the already-proved bounded formal theorem lane
- proved the natural-language request remains visible on runtime-side steering
  artifacts while the final authoritative-L2 theorem landing stays unchanged

## Acceptance criteria

- [x] One real natural-language dialogue run proves the formal-theory baseline can be entered through the public front door
- [x] Runtime steering artifacts preserve the fresh natural-language request
- [x] The route stays aligned with the bounded positive authoritative-L2 theorem baseline

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-formal-real-topic-dialogue.txt` | `phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/` | Isolated runtime-script receipt for the formal real-topic dialogue proof |
| `formal-real-topic-dialogue-acceptance.json` | `phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/` | Raw replay payload with dialogue inputs, steering artifacts, and repo-local L2 parity |
| `receipt.md` | `phases/174-formal-theory-real-topic-natural-language-dialogue-proof/evidence/` | Human-readable replay receipt |

## What this phase proved

1. The public AITP front door can steer the bounded formal-theory baseline from
   a real natural-language request without hidden seed state.
2. Runtime steering artifacts preserve the real dialogue request instead of
   erasing it behind internal routing.
3. The bounded formal authoritative-L2 landing remains stable under this
   real-dialogue entry path.
