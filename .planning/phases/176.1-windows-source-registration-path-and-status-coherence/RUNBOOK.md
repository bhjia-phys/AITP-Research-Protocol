# RUNBOOK: Phase 176.1 Windows Source Registration Path And Status Coherence

## Purpose

Replay the bounded Layer 0 fix that shortens source-registration directory
paths and refreshes runtime/status surfaces immediately after first-source
registration.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_source_discovery_contracts.py -q
python -m pytest research/knowledge-hub/tests/test_aitp_cli_e2e.py -k "first_run_acceptance_can_continue_into_source_registration" -q
python research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py --json --register-arxiv-id 2401.00001v2 --registration-metadata-json <temp-metadata.json>
```

`<temp-metadata.json>` should point to a metadata override whose `source_url`
references a local tarball fixture, as in the CLI E2E regression.

## Expected success markers

- source-discovery contracts: `15 passed`
- first-run CLI E2E slice: `1 passed`
- registration payload reports `runtime_status_sync.status = "refreshed"`
- registration payload uses a short slug matching
  `paper-2401-00001-<8hex>`
- post-registration status exposes `source_count >= 1`

## Current success boundary

This phase proves Windows-safe source path shortening and immediate source-count
visibility only. It does not yet prove that the post-registration bounded next
action is automatically rerouted away from the original L0 handoff text.
