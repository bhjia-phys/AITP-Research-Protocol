# Plan: 173-01 — Choose one bounded `LibRPA QSGW` positive target and close its codebase/workflow trust contract

**Phase:** 173
**Axis:** Axis 1 (layer capability) + Axis 2 (inter-layer connection)
**Requirements:** REQ-QSGW-01, REQ-QSGW-02

## Goal

Turn the deferred `LibRPA QSGW` widening work into one honest bounded positive
code-method / first-principles target that is already backed by real code
anchors and validator evidence, instead of pretending the whole QSGW stack is
already positive-L2-ready.

## Chosen bounded route

### Preferred target

Use the strongest existing positive evidence chain first:

- **bounded target family:** `LibRPA QSGW deterministic reduction consistency core`
- **workflow anchor:** `H2O/really_tight` QSGW `iter=10`
- **positive claim shape:** with the bounded deterministic-reduction guard in
  place, `OMP_NUM_THREADS=1` and `OMP_NUM_THREADS=32` produce the same
  `homo_lumo_vs_iterations.dat` trajectory on the reference case
- **code anchors:**
  - `D:\BaiduSyncdisk\Theoretical-Physics\LibRPA-develop\driver\task_qsgw.cpp`
  - `D:\BaiduSyncdisk\Theoretical-Physics\LibRPA-develop\src\params.h`
  - LibRI deterministic-reduction merge guard described in the existing
    engineering report
- **validator / evidence anchors:**
  - `D:\BaiduSyncdisk\Theoretical-Physics\automation\validators\qsgw_validator.py`
  - `D:\BaiduSyncdisk\Theoretical-Physics\obsidian-markdown\04 平时的记录\LibRPA\2026-02-27 LibRPA QSGW 单线程-多线程不一致定位与修复测试报告.md`
  - `D:\BaiduSyncdisk\Theoretical-Physics\obsidian-markdown\04 平时的记录\LibRPA\2026-02-27 QSGW OMP线程数一致性（LibRI确定性归约）.md`

### Explicit non-claims

This phase must **not** claim:

- full `1e-3 eV` QSGW convergence on the general workflow
- broad multi-system `LibRPA QSGW` closure
- that mixing-only scans already solved convergence
- that the whole codebase has already been ingested into authoritative `L2`

## Planned Route

### Step 1: Write failing target-contract acceptance coverage first

**Files:**
- `research/knowledge-hub/tests/test_runtime_scripts.py`

Add a test that requires a new isolated acceptance script to:

- bootstrap a fresh `first_principles` topic from natural language
- register the bounded `LibRPA QSGW` codebase/workflow evidence chain
- materialize a durable target-contract artifact for the deterministic
  reduction consistency core
- fail if the target drifts into unsupported full-convergence or whole-stack
  claims

### Step 2: Add one bounded QSGW target-contract acceptance script

**File:**
- `research/knowledge-hub/runtime/scripts/run_librpa_qsgw_target_contract_acceptance.py`

The script should:

- open a fresh `first_principles` topic through the public front door
- treat `D:\BaiduSyncdisk\Theoretical-Physics\LibRPA-develop` as the code
  source of truth and `D:\BaiduSyncdisk\repos\oh-my-LibRPA` as workflow wrapper
  context
- write one runtime-local target contract for the deterministic-reduction
  consistency core
- scaffold baseline / atomic-understanding / operation-trust artifacts around
  the real validator and real engineering evidence
- explicitly preserve the known non-claims about broader convergence

### Step 3: Keep the target as first-class codebase knowledge, not only prose

**Likely files touched if needed:**
- `research/knowledge-hub/runtime/scripts/run_librpa_qsgw_target_contract_acceptance.py`
- small helper modules only if a real gap appears

Prefer the smallest route that already matches the `aitp-codebase-learning`
discipline:

- codebase root and key files are named explicitly
- bounded workflow / algorithmic claim is explicit
- validator/evidence paths are durable
- the target is shaped so Phase `173.1` can later promote one bounded unit into
  authoritative `L2`

### Step 4: Leave durable evidence for phase closure

**Artifacts to write during execution:**
- `.planning/phases/173-librpa-qsgw-bounded-target-and-trust-contract/TARGET.md`
- `.planning/phases/173-librpa-qsgw-bounded-target-and-trust-contract/RUNBOOK.md`
- `.planning/phases/173-librpa-qsgw-bounded-target-and-trust-contract/SUMMARY.md`
- `.planning/phases/173-librpa-qsgw-bounded-target-and-trust-contract/evidence/`

## Acceptance Criteria

- [ ] one fresh `first_principles` topic is bootstrapped for the bounded `LibRPA QSGW` lane
- [ ] one bounded positive `LibRPA QSGW` target is chosen with explicit codebase and workflow anchors
- [ ] one benchmark, validator, or trust contract makes that target honest enough for later promotion
- [ ] explicit non-claims prevent the target from drifting into unsupported full-convergence or whole-stack closure
- [ ] one isolated acceptance lane proves the target-contract surface mechanically

## Must Not Do

- do not treat failed mixing-only convergence scans as positive closure evidence
- do not claim that `LibRPA QSGW` is globally converged or globally understood
- do not widen into authoritative-L2 promotion in this phase
- do not reopen the already-closed formal or bounded HS toy-model baselines
