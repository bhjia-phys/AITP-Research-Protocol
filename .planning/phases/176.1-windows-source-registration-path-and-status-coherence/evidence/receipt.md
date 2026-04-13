# Receipt: Phase 176.1 Windows Source Registration Path And Status Coherence

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -q
python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

## Observed results

- `pytest-source-discovery-contracts.txt`: `15 passed in 1.37s`
- `pytest-first-run-cli-e2e.txt`: `1 passed, 25 deselected in 3.52s`
- `run-first-run-after-registration.json`:
  - `registration.runtime_status_sync.status = "refreshed"`
  - `registration.runtime_status_sync.source_count = 1`
  - `status_after_registration.active_research_contract.l1_source_intake.source_count = 1`

## Key facts

- the long-title registration path now compiles to a short stable source slug
  matching `paper-2401-00001-<8hex>`
- runtime/status refresh is performed automatically when `topic_state.json`
  already exists for the topic
- the first-run acceptance lane now proves immediate post-registration source
  visibility on the status surface

## Raw artifacts

- `.planning/phases/176.1-windows-source-registration-path-and-status-coherence/evidence/pytest-source-discovery-contracts.txt`
- `.planning/phases/176.1-windows-source-registration-path-and-status-coherence/evidence/pytest-first-run-cli-e2e.txt`
- `.planning/phases/176.1-windows-source-registration-path-and-status-coherence/evidence/run-first-run-after-registration.json`
