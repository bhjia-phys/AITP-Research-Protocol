# Phase 145 Summary

Status: implemented in working tree

## Goal

Close the runtime-history gap by making forward/backward layer transitions and
demotion reasons durable, operator-visible, and replayable.

## What Landed

- structured transition-history support in:
  - `research/knowledge-hub/knowledge_hub/runtime_projection_handler.py`
  - `research/knowledge-hub/knowledge_hub/promotion_gate_support.py`
  - `research/knowledge-hub/knowledge_hub/candidate_promotion_support.py`
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_transition_history_acceptance.py`
- one new contract-test slice:
  - `research/knowledge-hub/tests/test_transition_history_contracts.py`
- runtime acceptance coverage in:
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
- projection/replay coverage updates in:
  - `research/knowledge-hub/tests/test_runtime_profiles_and_projections.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
- documentation updates across:
  - `README.md`
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `145` now closes the bounded runtime-history slice through:

- `transition_history.jsonl` as the append-only event log
- `transition_history.json|md` as the operator-facing summary surface
- promotion rejection and promotion completion feeding structured transition
  rows
- topic replay and runtime protocol note exposing the history path instead of
  forcing reconstruction from scattered current-state fields
