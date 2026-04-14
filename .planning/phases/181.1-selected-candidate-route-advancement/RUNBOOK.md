# Phase 181.1 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "advances_to_selected_consultation_candidate_when_selection_exists or advances_past_staged_l2_review_after_later_continue" -q
```
