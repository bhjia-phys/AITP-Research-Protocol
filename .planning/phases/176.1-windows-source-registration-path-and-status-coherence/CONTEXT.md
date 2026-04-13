# Context: Phase 176.1 Windows Source Registration Path And Status Coherence

## Why this phase exists

The same real-topic run that exposed the fresh-topic `session-start` misrouting
 also showed a first-use Layer 0 problem on Windows:

- long topic slug + long paper-title slug could overflow Windows path limits
  during source registration
- first-use registration needed an honest immediate status refresh so the
  operator could see that at least one source had landed

Phase `176` already fixed front-door topic routing. The next bounded step is
therefore the Layer 0 source-registration path and immediate status coherence.

## Root causes

- `register_arxiv_source.py` used
  `paper-<full-title-slug>-<arxiv-id>` as the source directory name, which is
  unnecessarily long on Windows.
- the registration path wrote Layer 0 / Layer 1 source artifacts but did not
  explicitly refresh runtime-facing status surfaces when an existing topic
  runtime was already present.

## Files in scope

- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`
- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py`
- `research/knowledge-hub/tests/test_source_discovery_contracts.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

## Boundaries

- Do not redesign the full source catalog or discovery ranking stack.
- Do not claim that post-registration action-queue semantics are fully
  rerouted yet; this phase is about path safety plus honest immediate source
  visibility.
- Keep the bounded first-run proof on the existing first-run acceptance lane.
