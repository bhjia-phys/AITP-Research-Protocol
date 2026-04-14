# Phase 182.2 Runbook

## Planned Verification

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "selected_candidate_route_choice_acceptance or consultation_followup_selection_acceptance or staged_l2_advancement_acceptance_script_runs_on_isolated_work_root or staged_l2_reentry_acceptance_script_runs_on_isolated_work_root or first_source_followthrough_acceptance_script_runs_on_isolated_work_root" -q
```
