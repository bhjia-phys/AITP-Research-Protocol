# Phase 178.1 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status or first_source_followthrough_acceptance_script_runs_on_isolated_work_root" -q
python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q
python research/knowledge-hub/runtime/scripts/run_first_source_followthrough_acceptance.py --json
```
