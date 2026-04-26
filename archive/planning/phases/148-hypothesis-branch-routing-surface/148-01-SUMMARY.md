# Phase 148 Summary

Status: implemented in working tree

## Goal

Close the next post-`v1.73` gap by making branch intent explicit per competing
hypothesis on the active topic surface.

## What Landed

- normalized hypothesis branch-routing support on the runtime/read-path layer
  in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- question-contract persistence for per-hypothesis route metadata in:
  - `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- runtime protocol / replay visibility for active versus parked hypothesis
  routes in:
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- schema updates for the public research-question and runtime-bundle contracts:
  - `schemas/research-question.schema.json`
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_hypothesis_branch_routing_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_hypothesis_branch_routing_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `148` now closes the first bounded hypothesis-routing slice:

- each `competing_hypotheses` row can declare whether it stays on the current
  topic, parks in deferred storage, routes to a follow-up subtopic, or remains
  excluded
- `status --json` and the runtime protocol note surface the active branch
  hypothesis plus parked branch ids directly
- `replay-topic --json` exposes active branch routing and parked-route counts
  without replacing steering, deferred, or follow-up runtime surfaces
