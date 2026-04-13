# Context: Phase 177.1 Post-Registration Next-Action Reselection

## Why this phase exists

Once Phase `177` made `topic_state` honest, the remaining first-use gap became
even clearer: post-registration `selected_action_summary` still pointed to the
old L0 source handoff even though a source already existed.

## Root cause

- the original bootstrap queue kept the generic `l0_source_expansion` action
  after registration
- no post-registration queue regeneration was triggered to prune that stale
  handoff and select the next bounded action

## Files in scope

- `research/knowledge-hub/runtime/scripts/orchestrate_topic.py`
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

## Boundaries

- keep the fix bounded to the first post-registration route transition
- do not redesign broader planner policy or multi-source sequencing
