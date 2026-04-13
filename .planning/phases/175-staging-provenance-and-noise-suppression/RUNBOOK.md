# RUNBOOK: Phase 175 Staging Provenance And Noise Suppression

## Purpose

Replay the bounded `L2` fast-path hardening slice that removes obvious staging
noise and preserves the true source provenance per staged entry.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_literature_intake_support.py -q
python -m pytest research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_l2_staging.py -q
```

## Expected success markers

- literature-intake support slice: `11 passed`
- `l2_graph_activation` slice: `8 passed`
- `l2_staging` slice: `2 passed`
- multi-paper staging keeps per-entry `source_id` / `source_slug`
- generic notation tokens and weak `unspecified_method` rows no longer appear
  in the derived staging payload

## Current success boundary

This phase hardens staging hygiene and provenance only. Consultation relevance
ordering is deferred to Phase `175.1`.
