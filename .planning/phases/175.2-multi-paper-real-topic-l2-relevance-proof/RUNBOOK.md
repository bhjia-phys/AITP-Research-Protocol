# RUNBOOK: Phase 175.2 Multi-Paper Real-Topic L2 Relevance Proof

## Purpose

Replay the bounded multi-paper fresh-topic proof showing that hardened `L2`
staging preserves per-entry provenance and that explicit local staged rows can
win the primary consultation surface over unrelated canonical carryover.

## Commands

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "multi_paper_l2_relevance_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_multi_paper_l2_relevance_acceptance.py --json
python -m pytest research/knowledge-hub/tests/test_literature_intake_support.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_l2_staging.py research/knowledge-hub/tests/test_aitp_service.py -k "consult_l2 or test_topic_local_staged_hit_can_win_primary_surface_when_staging_is_included" -q
```

## Expected success markers

- isolated runtime-script acceptance: `1 passed`
- supporting bounded `v2.1` regression slice: `3 passed`
- acceptance JSON reports `status: "success"`
- acceptance JSON reports `primary_hit_id` as
  `staging:measurement-induced-observer-algebra-bridge-note`
- acceptance JSON reports `primary_hit_trust_surface` as `staging`
- acceptance JSON reports two distinct staged source ids:
  `source:measurement-induced-bridge-paper` and
  `source:factor-type-warning-paper`

## Current success boundary

This phase proves only the bounded staging-and-consultation relevance slice for
one fresh multi-paper topic. It does not prove authoritative canonical `L2`
promotion, global retrieval redesign, or that copied package-local staging
noise has been eliminated from every secondary consultation surface.
