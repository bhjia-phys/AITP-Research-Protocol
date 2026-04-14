# Phase 181.2 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "consultation_followup_selection_acceptance or staged_l2_advancement_acceptance_script_runs_on_isolated_work_root or staged_l2_reentry_acceptance_script_runs_on_isolated_work_root or first_source_followthrough_acceptance_script_runs_on_isolated_work_root" -q
python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "continue_recorded_h_plane_as_steady" -q
```
