# Phase 181.1 Summary: Selected Candidate Route Advancement

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)

## What was done

Phase `181.1` advanced public route materialization from generic consultation
to one candidate-specific follow-up.

### Fixes landed

- queue materialization now switches from `consultation_followup` to
  `selected_consultation_candidate_followup` once the selection artifact is
  present
- runtime-state pointers now expose the selection artifact directly
- `must_read_now` now foregrounds the selection note when that candidate route
  is active

## Acceptance criteria

- [x] queue materialization advances to the selected consultation candidate
- [x] public surfaces can foreground the same candidate-specific route

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-queue-selected-candidate.txt` | `phases/181.1-selected-candidate-route-advancement/evidence/` | queue-materialization regression receipt |
| `receipt.md` | `phases/181.1-selected-candidate-route-advancement/evidence/` | human-readable summary of the candidate-route shift |

## What this phase proved

1. A successful consultation-followup no longer leaves the route on a generic
   consult instruction.
2. The runtime can now advance onto one selected staged candidate honestly.
