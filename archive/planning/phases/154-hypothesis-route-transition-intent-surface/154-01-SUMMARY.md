# Phase 154 Summary

Status: implemented in working tree

## Goal

Close the next post-`v1.79` gap by turning route-transition eligibility into an
operator-visible transition-intent surface instead of leaving the
source-to-target handoff implied after the gate becomes available.

## What Landed

- route transition-intent payload construction and runtime/read-path rendering
  in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- runtime protocol and research-question rendering for the new
  transition-intent section in:
  - `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- replay support for proposed versus ready versus checkpoint-held route
  transition intent in:
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- public runtime-bundle schema coverage for `route_transition_intent` in:
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_intent_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_hypothesis_route_transition_intent_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `154` now closes the first bounded route transition-intent slice:

- `status --json`, `research_question.contract.md`, and the runtime protocol
  note now surface one `route_transition_intent` summary with `proposed`,
  `ready`, and `checkpoint_held` states
- `replay-topic --json` exposes the same transition-intent payload plus the
  route-transition-intent status on both current-position and conclusions lanes
- the new isolated acceptance proves AITP can distinguish proposed,
  directly-ready, and checkpoint-held source-to-target handoff intent without
  automatic route mutation
