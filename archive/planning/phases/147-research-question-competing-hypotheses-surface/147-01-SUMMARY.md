# Phase 147 Summary

Status: implemented in working tree

## Goal

Close the research-question modeling gap by making multiple plausible bounded
answers first-class on the active topic surface.

## What Landed

- normalized `competing_hypotheses` support on the runtime/read-path layer in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- question-contract persistence plus markdown rendering in:
  - `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
  - `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`
- runtime protocol / replay visibility for the same surface in:
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- schema updates for the public research-question and runtime-bundle contracts:
  - `schemas/research-question.schema.json`
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_competing_hypotheses_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_competing_hypotheses_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `README.md`
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`
  - `.planning/PROJECT.md`

## Outcome

Phase `147` now closes the first bounded multi-hypothesis slice:

- `research_question.contract.json|md` can keep multiple competing hypotheses
  with explicit status, evidence refs, and exclusion notes
- `status --json` and the runtime protocol note surface that question-level
  competition directly through `active_research_contract`
- `replay-topic --json` exposes the leading hypothesis plus count/exclusion
  summary without replacing deferred buffers or follow-up subtopics
