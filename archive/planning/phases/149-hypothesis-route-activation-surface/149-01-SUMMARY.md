# Phase 149 Summary

Status: implemented in working tree

## Goal

Close the next post-`v1.74` gap by turning explicit hypothesis route metadata
into one operator-visible route-activation surface.

## What Landed

- route-activation payload construction and runtime/read-path rendering in:
  - `research/knowledge-hub/knowledge_hub/runtime_read_path_support.py`
- runtime protocol bundle rendering for the new route-activation section in:
  - `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py`
  - `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py`
- replay support for active-local action and parked-route obligations in:
  - `research/knowledge-hub/knowledge_hub/topic_replay.py`
- public runtime-bundle schema coverage for `route_activation` and
  `route_obligation` in:
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- one new isolated acceptance lane:
  - `research/knowledge-hub/runtime/scripts/run_hypothesis_route_activation_acceptance.py`
- new contract/runtime coverage in:
  - `research/knowledge-hub/tests/test_hypothesis_route_activation_contracts.py`
  - `research/knowledge-hub/tests/test_runtime_scripts.py`
  - `research/knowledge-hub/tests/test_topic_replay.py`
  - `research/knowledge-hub/tests/test_schema_contracts.py`
- documentation and runbook updates across:
  - `research/knowledge-hub/README.md`
  - `research/knowledge-hub/runtime/README.md`
  - `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`

## Outcome

Phase `149` now closes the first bounded route-activation slice:

- `status --json` and the runtime protocol note surface the active local
  hypothesis, its immediate bounded action, and the parked-route obligation
  lanes directly
- `replay-topic --json` exposes the same `route_activation` payload plus the
  parked-route count without replacing the action queue, deferred buffer, or
  follow-up subtopic surfaces
- the new isolated acceptance proves the activation surface stays declarative
  and does not auto-spawn a follow-up topic directory
