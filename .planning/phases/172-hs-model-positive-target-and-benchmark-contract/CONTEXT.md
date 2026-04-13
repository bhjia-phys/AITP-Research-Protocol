# Phase 172: HS Model Positive Target And Benchmark Contract - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Pick one honest bounded positive toy-model target for the user-requested HS
quantum-chaos lane, then materialize an explicit benchmark or trust contract
for that target before any authoritative-L2 promotion claim.

</domain>

<decisions>
## Implementation Decisions

### Positive target choice
- Do **not** try to force an exact-HS `alpha = 2` positive chaos claim. That
  would directly collide with the already-proven negative OTOC mismatch route.
- Reuse the strongest bounded positive candidate already present in the repo:
  `candidate:hs-chaos-window-finite-size-core` from
  `haldane-shastry-chaos-transition`.
- Frame the target honestly as an **HS-like finite-size chaos-window core**
  claim around the Haldane-Shastry point, not as “the exact HS model is
  chaotic”.

### Benchmark contract
- Reuse the existing benchmark-calibrated Fisher ED evidence chain and make it
  explicit on a fresh `toy_model` topic shell.
- Keep the claim bounded to the robust core window `0.4 <= alpha <= 1.0`.
- Keep the weaker `1.2 <= alpha <= 1.4` shoulder, larger-system continuation,
  operator robustness, and SU(2) multiplet workflow as explicit exclusions or
  follow-up gaps.

### the agent's Discretion
The exact naming of the fresh toy-model topic may change, but it must make the
positive target distinct from the exact-HS negative OTOC route.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `feedback/topics/haldane-shastry-chaos-transition/.../candidate_ledger.jsonl`
  already contains a ready-for-validation positive candidate:
  `candidate:hs-chaos-window-finite-size-core`.
- `source-layer/topics/haldane-shastry-chaos-transition/` already contains the
  local-note evidence chain for that candidate.
- `run_tfim_benchmark_code_method_acceptance.py` shows the existing pattern
  for converting a bounded benchmark-backed route into a fresh topic shell plus
  durable baseline/operation artifacts.

### Established Patterns
- Fresh proof lanes start from `AITPService().new_topic()` and clone only the
  needed source rows.
- Bounded benchmark honesty is already encoded through
  `scaffold_baseline()`, `scaffold_operation()`, and `audit_operation_trust()`.
- Runtime acceptance scripts should run on isolated work roots and emit one
  JSON payload with durable artifact paths.

### Integration Points
- The fresh toy-model target contract should land as a runtime-side acceptance
  script first.
- Later Phase `172.1` can consume that same bounded target when pushing toward
  authoritative canonical `L2`.

</code_context>

<specifics>
## Specific Ideas

- Fresh topic mode should be `toy_model`.
- The target contract should explicitly say:
  - positive target id
  - source topic slug reused
  - benchmark evidence refs
  - excluded claims
  - distinct negative comparison route: exact HS `alpha = 2` OTOC mismatch
- The acceptance should fail if the chosen target still claims the weak
  `1.2 <= alpha <= 1.4` shoulder or thermodynamic closure.

</specifics>

<deferred>
## Deferred Ideas

- Do not promote into authoritative `L2` in this phase.
- Do not reopen the larger-system continuation lane yet.
- Do not widen to `LibRPA QSGW` in this milestone slice.

</deferred>
