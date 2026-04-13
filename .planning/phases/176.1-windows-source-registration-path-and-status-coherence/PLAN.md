# Plan: 176.1-01 - Shorten Windows source paths and synchronize status after registration

**Phase:** 176.1
**Axis:** Axis 1 (layer-internal optimization) + Axis 4 (human experience)
**Requirements:** FTF-03, FTF-04

## Goal

Make first-source registration robust against Windows path overflow and ensure
runtime-facing status surfaces immediately show that the source landed.

## Planned Route

### Step 1: Add failing regressions

**Files:**
- `research/knowledge-hub/tests/test_source_discovery_contracts.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

Add one registration-unit regression for long-title short source slugs, one
registration-unit regression for immediate runtime status refresh, and extend
the first-run acceptance proof so it re-runs `status` after registration.

### Step 2: Fix the bounded registration path

**File:**
- `research/knowledge-hub/source-layer/scripts/register_arxiv_source.py`

Replace long human-title directory names with a short stable source slug and
refresh runtime/status surfaces when a runtime topic already exists.

### Step 3: Preserve replay receipts

**Commands to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -q`
- `python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q`
- `python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>`

## Acceptance Criteria

- [x] source registration uses a short stable directory slug instead of a long
      paper-title path segment
- [x] when the runtime topic already exists, registration refreshes
      runtime/status surfaces immediately
- [x] the first-run acceptance lane proves post-registration `status` exposes
      `source_count >= 1`
