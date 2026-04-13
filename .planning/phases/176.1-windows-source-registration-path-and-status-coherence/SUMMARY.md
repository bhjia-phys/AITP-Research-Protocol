# Phase 176.1 Summary: Windows Source Registration Path And Status Coherence

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 1 (layer-internal optimization) + Axis 4 (human experience)

## What was done

Phase `176.1` closed the bounded first-use Layer 0 reliability slice of
milestone `v2.2`.

### Fixes landed

- arXiv source registration now uses a short stable source directory slug based
  on the arXiv id plus a digest, instead of concatenating the full paper title
- when a runtime topic already exists, registration now refreshes runtime
  status surfaces immediately and syncs current-topic / active-topic metadata
  instead of leaving the operator to infer that a source landed
- the first-run acceptance lane now re-runs `status` after registration and
  proves that `source_count` is immediately visible

## Acceptance criteria

- [x] source registration uses a short stable directory slug instead of a long
      paper-title path segment
- [x] when the runtime topic already exists, registration refreshes
      runtime/status surfaces immediately
- [x] the first-run acceptance lane proves post-registration `status` exposes
      `source_count >= 1`

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-source-discovery-contracts.txt` | `phases/176.1-windows-source-registration-path-and-status-coherence/evidence/` | Full source-discovery and registration contract receipt |
| `pytest-first-run-cli-e2e.txt` | `phases/176.1-windows-source-registration-path-and-status-coherence/evidence/` | CLI E2E receipt for first-run continuation into registration |
| `run-first-run-after-registration.json` | `phases/176.1-windows-source-registration-path-and-status-coherence/evidence/` | Raw first-run acceptance replay showing runtime status refresh and post-registration `source_count` |
| `receipt.md` | `phases/176.1-windows-source-registration-path-and-status-coherence/evidence/` | Human-readable replay receipt |

## What this phase proved

1. Layer 0 source registration no longer needs long human-title directory names
   to preserve human-readable metadata.
2. First-source registration can now refresh runtime/status surfaces
   immediately when the topic runtime already exists.
3. The bounded first-run lane now proves post-registration source visibility
   mechanically instead of relying on operator memory.

## Explicit non-claims

- This phase does not yet prove that post-registration action selection is
  rerouted away from the pre-registration L0 handoff prompt.
- This phase does not redesign discovery ranking, source intelligence
  semantics, or broader topic-loop planning.
