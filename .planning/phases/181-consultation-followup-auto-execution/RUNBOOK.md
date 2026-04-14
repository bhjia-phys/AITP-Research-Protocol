# Phase 181 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "consultation_followup or continue_recorded_as_steady" -q
```
