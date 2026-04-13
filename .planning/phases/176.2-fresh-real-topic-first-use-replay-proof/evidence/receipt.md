# Receipt: Phase 176.2 Fresh Real-Topic First-Use Replay Proof

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

## Observed results

- `pytest-runtime-script.txt`: `1 passed, 81 deselected in 3.76s`
- `first-run-replay.json`:
  - `registration.runtime_status_sync.status = "refreshed"`
  - `registration.runtime_status_sync.source_count = 1`
  - `status_after_registration.active_research_contract.l1_source_intake.source_count = 1`

## Key facts

- the first-run acceptance lane now reaches registration instead of stopping at
  the pre-registration handoff proof
- the replay leaves both the runtime refresh receipt and the post-registration
  status payload visible

## Raw artifacts

- `.planning/phases/176.2-fresh-real-topic-first-use-replay-proof/evidence/pytest-runtime-script.txt`
- `.planning/phases/176.2-fresh-real-topic-first-use-replay-proof/evidence/first-run-replay.json`
