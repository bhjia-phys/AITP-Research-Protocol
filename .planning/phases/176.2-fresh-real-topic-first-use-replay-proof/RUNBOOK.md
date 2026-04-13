# RUNBOOK: Phase 176.2 Fresh Real-Topic First-Use Replay Proof

## Purpose

Replay the bounded first-use lane from fresh topic bootstrap through first
source registration and immediate post-registration status readback.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "first_run_acceptance_script_runs_registration_and_refreshes_status" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

`<temp-metadata.json>` should point to a local tarball-backed metadata override
fixture, as in the CLI E2E and runtime-script regressions.

## Expected success markers

- runtime-script slice: `1 passed`
- replay JSON contains `registration.runtime_status_sync.status = "refreshed"`
- replay JSON contains
  `status_after_registration.active_research_contract.l1_source_intake.source_count >= 1`

## Current success boundary

This phase proves only the bounded first-use operator path through bootstrap,
registration, and immediate status readback. It does not prove broader
post-registration planning or scientific closure.
