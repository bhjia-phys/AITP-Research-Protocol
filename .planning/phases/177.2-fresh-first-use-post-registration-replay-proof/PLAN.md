# Plan: 177.2-01 - Replay a fresh first-use lane through post-registration route transition

**Phase:** 177.2
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)
**Requirements:** PRC-05

## Goal

Close milestone `v2.3` with one replayable first-use proof that registration
updates both runtime state and the selected next action.

## Planned Route

### Step 1: Tighten the runtime acceptance script

**File:**
- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py`

Make the script assert that post-registration `selected_action_summary` is no
longer the stale L0 source-handoff wording.

### Step 2: Preserve replay receipts

**Commands to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q`
- `python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>`

## Acceptance Criteria

- [x] one runtime-script regression proves the first-use lane reaches the
      post-registration route transition on an isolated work root
- [x] one replay receipt proves `topic_state.source_count = 1` and a non-stale
      post-registration `selected_action_summary`
