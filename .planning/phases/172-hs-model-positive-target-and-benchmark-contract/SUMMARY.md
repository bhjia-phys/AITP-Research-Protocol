# Phase 172 Summary: HS Model Positive Target And Benchmark Contract

**Status:** Done
**Date:** 2026-04-14
**Axis:** Axis 1 (layer capability) + Axis 2 (inter-layer connection)

## What was done

Phase 172 closed the target-selection and benchmark-contract slice for
milestone `v1.98`.

### Chosen positive lane

- fresh topic mode: `toy_model`
- fresh topic slug: `hs-like-finite-size-chaos-window-core`
- chosen target candidate:
  `candidate:hs-chaos-window-finite-size-core`
- chosen target type: `claim_card`

### Honest narrowing decision

The phase explicitly did **not** treat exact HS `alpha = 2` as a positive chaos
target. Instead it chose the already benchmark-backed **HS-like finite-size
chaos-window core** and kept the exact-HS OTOC mismatch route as an explicit
negative comparator.

### Contract surfaces produced

- fresh toy-model topic shell
- cloned source rows from `haldane-shastry-chaos-transition`
- `hs_positive_target_contract.json|md`
- baseline summary for the benchmark gate
- operation manifest + trust audit proving the target contract is
  trust-ready enough for the next promotion phase

## Acceptance criteria

- [x] One fresh `toy_model` topic is bootstrapped for the HS widening lane
- [x] The positive target is explicitly narrowed to the robust HS-like finite-size core
- [x] The exact-HS OTOC mismatch route stays explicit as a separate negative comparator
- [x] One benchmark or trust contract artifact makes the target honest enough for later promotion
- [x] One isolated acceptance lane proves the target-contract surface mechanically

## Evidence

| Artifact | Location | Purpose |
|----------|----------|---------|
| `pytest-hs-target-contract.txt` | `phases/172-hs-model-positive-target-and-benchmark-contract/evidence/` | Isolated runtime-script receipt for the fresh toy-model target-contract lane |
| `hs-toy-model-target-contract-acceptance.json` | `phases/172-hs-model-positive-target-and-benchmark-contract/evidence/` | Raw replay payload with target candidate, trust gate, and negative comparator |
| `receipt.md` | `phases/172-hs-model-positive-target-and-benchmark-contract/evidence/` | Human-readable replay receipt |

## What this phase proved

1. There is now one honest bounded positive HS-family target that does not
   collide with the already-proven exact-HS negative OTOC route.
2. The target is no longer only implicit in prior notes; it now has a fresh
   toy-model topic shell plus explicit benchmark/trust artifacts.
3. Phase `172.1` can now focus on promotion into authoritative `L2` instead of
   re-litigating what the positive target even is.
