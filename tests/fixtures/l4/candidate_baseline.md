---
artifact_kind: candidate
stage: L3
candidate_id: cand-qho-energy-spectrum
candidate_type: result
title: Quantum Harmonic Oscillator Energy Spectrum
claim: >-
  The energy eigenvalues of the 1D quantum harmonic oscillator with
  Hamiltonian H = p^2/(2m) + (1/2) m omega^2 x^2 are
  E_n = (n + 1/2) hbar omega, for n = 0, 1, 2, ...
evidence: >-
  Derived using ladder operator method. Define a, a^† from x and p.
  Show [a, a^†] = 1, H = hbar omega (a^† a + 1/2). From number operator
  N = a^† a with eigenvalues n ∈ ℕ_0, the spectrum follows.
regime_of_validity: Non-relativistic QM, 1D, harmonic potential only
status: validated
validated_at: 2026-04-20T12:00:00Z
sources:
  - griffiths-qm-ch2
---

# Candidate: Quantum Harmonic Oscillator Energy Spectrum

## Claim
The energy eigenvalues of the 1D quantum harmonic oscillator with
Hamiltonian H = p^2/(2m) + (1/2) m omega^2 x^2 are
E_n = (n + 1/2) hbar omega, for n = 0, 1, 2, ...

## Derivation Summary
Using ladder operator method:
1. Define dimensionless operators from x and p
2. Construct a = sqrt(m omega/(2 hbar)) x + i sqrt(1/(2m hbar omega)) p
3. Show [a, a^†] = 1
4. Express H = hbar omega (a^† a + 1/2) = hbar omega (N + 1/2)
5. From N |n⟩ = n |n⟩ with n ∈ ℕ₀, spectrum follows

## Regime of Validity
- Non-relativistic quantum mechanics
- One spatial dimension
- Strictly harmonic potential (no anharmonic corrections)
- Single particle
