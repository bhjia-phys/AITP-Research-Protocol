# Phase 43 Summary

Status: implemented on `codex/aitp-v137-v142-remediation`

## Goal

Strengthen `L1` intake so source-backed assumptions, regimes, and reading-depth
structure survive source distillation, contract materialization, and runtime
projection.

## What Landed

- source distillation now extracts durable `l1_source_intake` structure with
  source-backed assumption, regime, and reading-depth rows
- topic shell materialization persists the stronger `L1` intake into the active
  research contract and human-readable contract note
- topic synopsis and runtime protocol bundle now carry the same intake structure
  so later layers can reuse it without re-parsing source prose
- mirrored schema contracts and focused regressions were updated to lock the new
  `L1` intake contract in place

## Verification

- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - result: `119 passed`
- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py research/knowledge-hub/tests/test_aitp_cli.py research/knowledge-hub/tests/test_aitp_cli_e2e.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_topic_start_regressions.py -q`
  - result: `144 passed`

## Outcome

Phase `43` is complete on this branch.
The next active milestone step is Phase `44` `contradiction-and-notation-alignment`.
