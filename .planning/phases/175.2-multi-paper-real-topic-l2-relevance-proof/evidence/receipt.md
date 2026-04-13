# Receipt: Phase 175.2 Multi-Paper Real-Topic L2 Relevance Proof

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "multi_paper_l2_relevance_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_multi_paper_l2_relevance_acceptance.py --json
python -m pytest research/knowledge-hub/tests/test_literature_intake_support.py research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_l2_staging.py research/knowledge-hub/tests/test_aitp_service.py -k "consult_l2 or test_topic_local_staged_hit_can_win_primary_surface_when_staging_is_included" -q
```

## Observed results

- `pytest-runtime-script.txt`: `1 passed, 80 deselected in 0.36s`
- `run-multi-paper-l2-relevance.json`: `status = "success"`
- `pytest-v2.1-regression-slice.txt`: `3 passed, 172 deselected in 0.43s`

## Key facts

- staged entry count: `2`
- staged source ids:
  `source:factor-type-warning-paper`,
  `source:measurement-induced-bridge-paper`
- primary hit id:
  `staging:measurement-induced-observer-algebra-bridge-note`
- primary hit trust surface: `staging`
- unrelated canonical carryover remains visible as
  `concept:observer-algebra-carryover` without outranking the local staged hit

## Raw artifacts

- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/pytest-runtime-script.txt`
- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/run-multi-paper-l2-relevance.json`
- `.planning/phases/175.2-multi-paper-real-topic-l2-relevance-proof/evidence/pytest-v2.1-regression-slice.txt`
