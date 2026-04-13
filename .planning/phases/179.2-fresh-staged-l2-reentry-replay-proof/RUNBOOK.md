# Phase 179.2 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "staged_l2_reentry_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_staged_l2_reentry_acceptance.py --json
```
