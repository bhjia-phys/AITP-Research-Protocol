# Receipt: Phase 172 HS Toy-Model Target Contract

## Replay commands

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hs_toy_model_target_contract_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_hs_toy_model_target_contract_acceptance.py --json
```

## Observed results

- `pytest-hs-target-contract.txt`: `1 passed, 72 deselected in 1.19s`
- `hs-toy-model-target-contract-acceptance.json`: `status = success`

## Key facts

- Fresh topic slug: `hs-like-finite-size-chaos-window-core`
- Research mode: `toy_model`
- Chosen candidate: `candidate:hs-chaos-window-finite-size-core`
- Candidate status: `ready_for_validation`
- Trust status: `pass`
- Negative comparator:
  `staging:hs-model-otoc-lyapunov-exponent-regime-mismatch`

## Raw artifacts

- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/evidence/pytest-hs-target-contract.txt`
- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/evidence/hs-toy-model-target-contract-acceptance.json`
