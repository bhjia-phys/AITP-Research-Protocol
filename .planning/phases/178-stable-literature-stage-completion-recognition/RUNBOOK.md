# Phase 178 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "literature_intake_stage" -q
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "materialize_action_queue_appends_literature_intake_stage_in_literature_submode or advances_to_staging_review_after_matching_literature_stage" -q
```
