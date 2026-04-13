# Phase 177.1 Summary: Post-Registration Next-Action Reselection

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human experience)

## What was done

Phase `177.1` repaired the stale first-use route transition after registration.

### Fixes landed

- stale bootstrap `l0_source_expansion` actions are now pruned once a first
  source already exists
- source registration now triggers a queue/decision refresh so the next-action
  surface is rematerialized from current state instead of staying frozen
- when no better action exists yet, the queue falls back to
  `Inspect the compiled L1 vault before continuing.`

## Acceptance criteria

- [x] post-registration `selected_action_summary` no longer points at the raw
      L0 handoff entry surfaces
- [x] the new post-registration action is derived mechanically from the
      refreshed runtime state and queue pipeline

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-cli-e2e.txt` | `phases/177.1-post-registration-next-action-reselection/evidence/` | First-use CLI E2E receipt for the post-registration route change |
| `receipt.md` | `phases/177.1-post-registration-next-action-reselection/evidence/` | Human-readable replay receipt |

## What this phase proved

1. The first post-registration step is no longer stuck on the bootstrap L0
   source-handoff wording.
2. The route change is driven by queue regeneration rather than an operator-only
   workaround.
