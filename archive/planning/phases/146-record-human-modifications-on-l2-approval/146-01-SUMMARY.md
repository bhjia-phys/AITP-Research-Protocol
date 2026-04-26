# Phase 146 Summary

Status: implemented in working tree

## Goal

Close the promotion-gate evaluator-divergence gap by recording what a human
changed when approving an `L2` promotion, not just that they approved it.

## What Landed

- structured modification capture on the approval path in:
  - `research/knowledge-hub/knowledge_hub/promotion_gate_support.py`
  - `research/knowledge-hub/knowledge_hub/aitp_service.py`
  - `research/knowledge-hub/knowledge_hub/aitp_cli.py`
- replay visibility for modified approvals in:
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_human_modification_record_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_human_modification_record_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_aitp_cli.py`
  - `research/knowledge-hub/tests/test_aitp_service.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
- documentation updates across:
  - `README.md`
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `146` now closes the bounded human-override slice on the approval gate:

- approvals can be recorded as submitted or with explicit human modifications
- `promotion_gate.json|md` stores what changed and why
- replay surfaces expose modified approval as a distinct evaluator-divergence
  signal instead of flattening it into generic approval
