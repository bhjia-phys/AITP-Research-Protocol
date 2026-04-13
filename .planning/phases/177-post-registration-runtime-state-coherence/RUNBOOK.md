# RUNBOOK: Phase 177 Post-Registration Runtime State Coherence

## Purpose

Replay the bounded registration path and prove that persisted runtime state now
records first-source presence honestly.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -k "refreshes_runtime_status_surfaces_when_topic_runtime_exists" -q
```

## Expected success markers

- regression slice: `1 passed`
- `topic_state.source_count >= 1`
- `topic_state.layer_status.L0.status = present`
- `active_topics.json` focuses the refreshed topic

## Current success boundary

This phase only fixes persisted runtime-state and projection coherence after
registration. It does not yet change the selected next action.
