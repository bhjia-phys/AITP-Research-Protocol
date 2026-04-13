# Receipt: Phase 177.2 Fresh First-Use Post-Registration Replay Proof

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

## Observed results

- `pytest-runtime-script.txt`: `1 passed, 81 deselected in 4.42s`
- `first-use-post-registration-replay.json`:
  - `topic_state.source_count = 1`
  - `topic_state.layer_status.L0.status = "present"`
  - `selected_action_summary = "Stage bounded literature-intake units from the current L1 vault into L2 staging."`

## Raw artifacts

- `.planning/phases/177.2-fresh-first-use-post-registration-replay-proof/evidence/pytest-runtime-script.txt`
- `.planning/phases/177.2-fresh-first-use-post-registration-replay-proof/evidence/first-use-post-registration-replay.json`
