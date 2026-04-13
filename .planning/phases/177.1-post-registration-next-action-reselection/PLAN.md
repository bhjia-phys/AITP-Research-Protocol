# Plan: 177.1-01 - Reselect bounded next actions after first-source registration

**Phase:** 177.1
**Axis:** Axis 2 (inter-layer connection) + Axis 4 (human experience)
**Requirements:** PRC-03, PRC-04

## Goal

Replace the stale post-registration L0 source-handoff action with the next
bounded research action once the first source has landed.

## Planned Route

### Step 1: Add a failing first-use replay regression

**File:**
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

Require post-registration `selected_action_summary` to stop mentioning
`discover_and_register.py` and `register_arxiv_source.py`.

### Step 2: Rebuild the queue after registration

**Files:**
- `research/knowledge-hub/runtime/scripts/orchestrate_topic.py`
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`

Prune the generic bootstrap `l0_source_expansion` row once a first source is
already present, add a bounded fallback inspection step if no better action
exists, and re-run queue materialization after registration.

### Step 3: Preserve receipts

**Command to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q`

## Acceptance Criteria

- [x] post-registration `selected_action_summary` no longer points at the raw
      L0 handoff entry surfaces
- [x] the new post-registration action is derived mechanically from the
      refreshed runtime state and queue pipeline
