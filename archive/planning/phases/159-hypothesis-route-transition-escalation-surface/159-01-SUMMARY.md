# Phase 159 Summary

Status: implemented in working tree

## Goal

Close the next post-`v1.84` gap by turning transition repair into an
operator-visible transition-escalation surface instead of leaving operators to
infer when repair should become a human checkpoint.

## What Landed

- route transition-escalation payload construction and runtime/read-path
  rendering in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- runtime protocol rendering for the new transition-escalation section in:
  - `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- replay support for `none`, `checkpoint_recommended`, and
  `checkpoint_active` transition-escalation visibility in:
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- public runtime-bundle schema coverage for `route_transition_escalation` in:
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_hypothesis_route_transition_escalation_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_hypothesis_route_transition_escalation_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `159` now closes the first bounded route transition-escalation slice:

- `status --json` and the runtime protocol note now surface one
  `route_transition_escalation` summary with `none`,
  `checkpoint_recommended`, and `checkpoint_active` states
- `replay-topic --json` exposes the same transition-escalation payload plus the
  escalation status on the replay surface
- the new isolated acceptance proves AITP can make transition-escalation
  operator-visible without widening into fresh runtime mutation
