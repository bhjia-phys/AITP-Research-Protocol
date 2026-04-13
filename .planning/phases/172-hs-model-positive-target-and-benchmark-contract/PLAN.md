# Plan: 172-01 — Choose one bounded positive HS-model target and close its benchmark or convergence contract

**Phase:** 172
**Axis:** Axis 1 (layer capability) + Axis 2 (inter-layer connection)
**Requirements:** REQ-HS-01, REQ-HS-02

## Goal

Turn the deferred HS toy-model widening work into one honest bounded target:
the benchmark-backed HS-like finite-size chaos-window core, with explicit
separation from the exact-HS negative OTOC route.

## Planned Route

### Step 1: Write failing acceptance coverage first

**Files:**
- `research/knowledge-hub/tests/test_runtime_scripts.py`

Add one test that requires a new isolated acceptance script to:

- bootstrap a fresh `toy_model` topic
- clone the `haldane-shastry-chaos-transition` source rows
- materialize a durable positive-target contract
- prove that the target is the robust finite-size core and not the exact-HS
  OTOC claim

### Step 2: Add one bounded target-contract acceptance script

**File:**
- `research/knowledge-hub/runtime/scripts/run_hs_toy_model_target_contract_acceptance.py`

The script should:

- start a fresh `toy_model` topic from natural language
- clone the source rows from `haldane-shastry-chaos-transition`
- load `candidate:hs-chaos-window-finite-size-core` from the existing candidate
  ledger as the chosen positive target
- write runtime-local baseline / operation / trust artifacts that make the
  benchmark contract explicit
- fail if the target drifts into the weak shoulder, thermodynamic closure, or
  exact-HS chaos claim

### Step 3: Leave durable evidence

**Artifacts to write during execution:**
- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/TARGET.md`
- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/RUNBOOK.md`
- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/SUMMARY.md`
- `.planning/phases/172-hs-model-positive-target-and-benchmark-contract/evidence/`

## Acceptance Criteria

- [ ] one fresh `toy_model` topic is bootstrapped for the HS widening lane
- [ ] the positive target is explicitly narrowed to the robust HS-like finite-size core
- [ ] the exact-HS OTOC mismatch route stays explicit as a separate negative comparator
- [ ] one benchmark or trust contract artifact makes the target honest enough for later promotion
- [ ] one isolated acceptance lane proves the target-contract surface mechanically
