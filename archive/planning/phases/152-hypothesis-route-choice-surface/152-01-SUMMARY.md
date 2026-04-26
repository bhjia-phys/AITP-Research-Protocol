# Phase 152 Summary

Status: implemented in working tree

## Goal

Close the next post-`v1.77` gap by turning the current local route plus the
primary handoff candidate into one hypothesis-aware route choice surface.

## What Landed

- route choice payload construction and runtime/read-path rendering in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- runtime protocol and research-question rendering for the new route choice
  section in:
  - `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- replay support for stay-local versus yield-to-handoff choice in:
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- public runtime-bundle schema coverage for `route_choice` and
  `route_choice_option` in:
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_hypothesis_route_choice_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_hypothesis_route_choice_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `152` now closes the first bounded route choice slice:

- `status --json`, `research_question.contract.md`, and the runtime protocol
  note now surface one stay-local versus yield-to-handoff summary
- `replay-topic --json` exposes the same `route_choice` payload plus the route
  choice status and both bounded options
- the new isolated acceptance proves the local route can stay active while the
  primary handoff candidate remains visible as the yield option, without
  runtime mutation
