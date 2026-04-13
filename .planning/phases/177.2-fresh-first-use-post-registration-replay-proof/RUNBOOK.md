# RUNBOOK: Phase 177.2 Fresh First-Use Post-Registration Replay Proof

## Purpose

Replay the bounded first-use lane through registration and prove both runtime
state and selected next action are updated.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

## Expected success markers

- runtime-script slice: `1 passed`
- replay JSON reports `topic_state.source_count = 1`
- replay JSON reports `topic_state.layer_status.L0.status = present`
- replay JSON reports post-registration selected action:
  `Stage bounded literature-intake units from the current L1 vault into L2 staging.`

## Current success boundary

This phase proves the bounded first-use post-registration route transition
only. It does not yet claim full downstream research closure after that step.
