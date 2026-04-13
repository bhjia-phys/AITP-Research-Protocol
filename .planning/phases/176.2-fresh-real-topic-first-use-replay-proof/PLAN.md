# Plan: 176.2-01 - Replay a fresh real-topic first-use proof from session-start through first source registration

**Phase:** 176.2
**Axis:** Axis 4 (human evidence) + Axis 5 (agent-facing steering)
**Requirements:** FTF-05

## Goal

Close milestone `v2.2` with one replayable first-use lane proving that the
public front door can start a topic, continue into first-source registration,
and surface immediate post-registration source visibility.

## Planned Route

### Step 1: Add a runtime-script regression

**File:**
- `research/knowledge-hub/tests/test_runtime_scripts.py`

Run `run_first_run_topic_acceptance.py` with a local tarball-backed metadata
fixture and require the script to complete successfully on an isolated work
root.

### Step 2: Preserve replay receipts

**Commands to preserve as evidence:**
- `python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q`
- `python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>`

### Step 3: Close milestone phase work honestly

Write runbook, summary, and receipt describing what the bounded first-use proof
does and does not establish.

## Acceptance Criteria

- [x] one runtime-script regression proves the first-run acceptance lane can
      continue into registration on an isolated work root
- [x] one replay receipt proves post-registration `status` exposes
      `source_count >= 1`
- [x] the phase closes with durable receipts and explicit non-claims
