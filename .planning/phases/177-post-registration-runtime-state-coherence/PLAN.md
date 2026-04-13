# Plan: 177-01 - Refresh runtime state and topic projections after first-source registration

**Phase:** 177
**Axis:** Axis 1 (layer-internal optimization) + Axis 3 (data recording)
**Requirements:** PRC-01, PRC-02

## Goal

Make post-registration runtime state persist the same first-source truth that
runtime/status surfaces already derive.

## Planned Route

### Step 1: Add a failing registration regression

**File:**
- `research/knowledge-hub/tests/test_source_discovery_contracts.py`

Extend the registration regression so it requires `topic_state.source_count >= 1`,
`layer_status.L0.status = present`, and aligned current-topic / active-topic
projection files after registration.

### Step 2: Fix the persisted runtime-state writeback

**Files:**
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`

After runtime refresh, write the refreshed source-count and L0 layer-status
facts back into `topic_state.json`, then sync the current-topic / active-topic
projections.

### Step 3: Preserve receipts

**Command to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -k "refreshes_runtime_status_surfaces_when_topic_runtime_exists" -q`

## Acceptance Criteria

- [x] `topic_state.source_count` reflects first-source presence after registration
- [x] `topic_state.layer_status.L0` flips to `present` with `source_count >= 1`
- [x] current-topic / active-topic projections remain aligned after the refresh
