# RUNBOOK: Phase 177.1 Post-Registration Next-Action Reselection

## Purpose

Replay the bounded first-use route and prove that the selected next action
after registration no longer points back to the stale L0 source handoff.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q
```

## Expected success markers

- CLI E2E slice: `1 passed`
- post-registration `selected_action_summary` does not contain
  `discover_and_register.py`
- post-registration `selected_action_summary` does not contain
  `register_arxiv_source.py`

## Current success boundary

This phase only proves that the first post-registration action is no longer the
stale bootstrap handoff. It does not yet claim that the whole downstream
research loop is closed.
