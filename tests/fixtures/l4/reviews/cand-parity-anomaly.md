---
artifact_kind: l4_review
stage: L4
candidate_id: cand-parity-anomaly
outcome: contradiction
l4_cycle: 2
reviewed_at: 2026-04-20T13:30:00Z
check_results:
  correspondence_check: 'contradiction: candidate claims parity is conserved, but Redlich (1984) §4.2 proves parity anomaly in 2+1D with massless fermions'
  symmetry_compatibility: 'contradiction: parity transformation of effective action produces non-invariant term proportional to CS level k'
devils_advocate: >-
  The candidate may have implicitly assumed a Pauli-Villars regulator that
  preserves parity, which is known to be impossible in odd dimensions. The
  contradiction is real and points to a fundamental physics issue, not a
  computational error.
---

# Review: cand-parity-anomaly

## Outcome
contradiction

## Notes
The candidate claims parity conservation in 2+1D Chern-Simons theory coupled
to massless Dirac fermions. This directly contradicts:
1. Redlich (1984) — parity anomaly proof in odd dimensions
2. The explicit computation showing d_eff = k ± N/2 for the CS level
The contradiction is fundamental and cannot be resolved by parameter tuning.

## Devil's Advocate
The candidate may have implicitly assumed a Pauli-Villars regulator that
preserves parity, which is known to be impossible in odd dimensions. The
contradiction is real and points to a fundamental physics issue, not a
computational error.

## Check Results
- correspondence_check: contradiction: candidate claims parity is conserved, but Redlich (1984) §4.2 proves parity anomaly in 2+1D with massless fermions
- symmetry_compatibility: contradiction: parity transformation of effective action produces non-invariant term proportional to CS level k
