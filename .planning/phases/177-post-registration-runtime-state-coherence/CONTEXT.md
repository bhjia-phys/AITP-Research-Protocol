# Context: Phase 177 Post-Registration Runtime State Coherence

## Why this phase exists

After `v2.2`, first-source registration refreshed status surfaces well enough
to expose `source_count >= 1`, but durable runtime state still kept stale zero
source counters and `layer_status.L0 = missing` in the first-use replay.

That meant the runtime truth surface and the operator-facing status surface were
not yet saying the same thing about whether Layer 0 had been entered
successfully.

## Root cause

- source registration refreshed runtime bundles, but `topic_state.json` itself
  was not updated from the refreshed source-intelligence view
- later surfaces could therefore read a mixture of fresh derived payloads and
  stale persisted topic-state counters

## Files in scope

- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`
- `research/knowledge-hub/tests/test_source_discovery_contracts.py`

## Boundaries

- keep the fix bounded to persisted runtime-state and projection coherence
- do not solve next-action reselection here; that is Phase `177.1`
