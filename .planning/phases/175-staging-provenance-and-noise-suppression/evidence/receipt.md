# Receipt: Phase 175 Staging Provenance And Noise Suppression

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_literature_intake_support.py -q
python -m pytest research/knowledge-hub/tests/test_l2_graph_activation.py research/knowledge-hub/tests/test_l2_staging.py -q
```

## Observed results

- `pytest-literature-intake-support.txt`: `11 passed in 0.90s`
- `pytest-l2-graph-and-staging.txt`: `10 passed in 0.90s`

## Key facts

- per-entry staged provenance now preserves `source_id` and `source_slug`
- generic notation bindings such as `classes` are suppressed
- weak `unspecified_method` rows are suppressed
- staging-index rebuilds preserve `trust_surface`, `source_refs`, `tags`, and
  `provenance`

## Raw artifacts

- `.planning/phases/175-staging-provenance-and-noise-suppression/evidence/pytest-literature-intake-support.txt`
- `.planning/phases/175-staging-provenance-and-noise-suppression/evidence/pytest-l2-graph-and-staging.txt`
