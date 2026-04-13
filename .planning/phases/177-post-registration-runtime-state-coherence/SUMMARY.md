# Phase 177 Summary: Post-Registration Runtime State Coherence

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 1 (layer-internal optimization) + Axis 3 (data recording)

## What was done

Phase `177` repaired the persisted runtime-state side of the post-registration
gap.

### Fixes landed

- refreshed source-count and L0-layer presence are now written back into
  `topic_state.json`
- `l0_source_index_path` is refreshed from the real source index instead of
  remaining stale or empty
- current-topic and active-topic projections now remain aligned with the
  refreshed runtime state when registration lands on an existing topic

## Acceptance criteria

- [x] `topic_state.source_count` reflects first-source presence after registration
- [x] `topic_state.layer_status.L0` flips to `present` with `source_count >= 1`
- [x] current-topic / active-topic projections remain aligned after the refresh

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-runtime-state.txt` | `phases/177-post-registration-runtime-state-coherence/evidence/` | Focused registration regression receipt |
| `receipt.md` | `phases/177-post-registration-runtime-state-coherence/evidence/` | Human-readable replay receipt |

## What this phase proved

1. Persisted runtime state no longer contradicts the refreshed source-aware
   status surface after registration.
2. The first-source landing is now visible both in machine state and in
   operator-facing projections.
