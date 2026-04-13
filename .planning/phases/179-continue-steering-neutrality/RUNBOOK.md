# Phase 179 Runbook

## Verification

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_service.py -k "continue_recorded_as_steady" -q
python -m pytest research/knowledge-hub/tests/test_runtime_profiles_and_projections.py -k "continue_recorded_h_plane_as_steady" -q
```
