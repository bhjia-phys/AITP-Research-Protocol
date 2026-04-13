# RUNBOOK: Phase 172 HS Toy-Model Target Contract

## Purpose

Replay the bounded positive target-selection and benchmark-contract proof for
the HS toy-model widening lane.

## Command

From repo root:

```bash
python -m pytest research/knowledge-hub/tests/test_runtime_scripts.py -k "hs_toy_model_target_contract_acceptance_script_runs_on_isolated_work_root" -q
python research/knowledge-hub/runtime/scripts/run_hs_toy_model_target_contract_acceptance.py --json
```

## Expected success markers

- fresh topic slug: `hs-like-finite-size-chaos-window-core`
- research mode: `toy_model`
- target candidate id: `candidate:hs-chaos-window-finite-size-core`
- target contract exists under the fresh topic shell:
  - `runtime/topics/<slug>/hs_positive_target_contract.json`
  - `runtime/topics/<slug>/hs_positive_target_contract.md`
- trust gate status: `pass`
- negative comparator remains explicit:
  `staging:hs-model-otoc-lyapunov-exponent-regime-mismatch`

## Interpretation

This phase does **not** yet promote the positive target into canonical `L2`.
It only proves that one honest bounded positive HS-family target and its
benchmark/trust contract can be carried onto a fresh `toy_model` topic shell.
