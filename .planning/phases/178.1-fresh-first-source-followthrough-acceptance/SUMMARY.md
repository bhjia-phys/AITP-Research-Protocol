# Phase 178.1 Summary: Fresh First-Source Follow-Through Acceptance

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

## What was done

Phase `178.1` added one isolated fresh-topic acceptance proof for the first
post-registration L1->L2 follow-through.

### Fixes landed

- a new runtime acceptance script now replays
  `bootstrap -> register first source -> literature_intake_stage -> staging review`
- the same script now proves `consult_l2(include_staging=True)` returns at
  least one topic-local staged hit after that first follow-through
- runtime README and runbook now expose the new bounded proof entrypoint

## Acceptance criteria

- [x] one isolated acceptance script proves the fresh first-source
      follow-through lane end to end
- [x] the proof packet includes staged-`L2` visibility and topic-local staged
      consultation retrieval
- [x] runtime-script regression coverage keeps the proof mechanically replayable

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-followthrough-acceptance.txt` | `phases/178.1-fresh-first-source-followthrough-acceptance/evidence/` | runtime-script acceptance regression receipt |
| `first-source-followthrough-acceptance.json` | `phases/178.1-fresh-first-source-followthrough-acceptance/evidence/` | raw isolated replay packet |
| `receipt.md` | `phases/178.1-fresh-first-source-followthrough-acceptance/evidence/` | human-readable proof summary |

## What this phase proved

1. A fresh topic can now continue from first-source registration into one
   bounded staged-`L2` follow-through step without falling back to the earlier
   post-registration loop.
2. The topic-local staged entry becomes retrievable through the bounded
   consultation surface immediately after that first follow-through.
