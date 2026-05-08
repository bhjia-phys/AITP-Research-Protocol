---
artifact_kind: l4_validation_contract
stage: L4
topic_slug: demo-topic
lane: formal_theory
candidate_ids:
  - cand-qho-energy-spectrum
mandatory_checks:
  - dimensional_consistency
  - symmetry_compatibility
  - limiting_case_check
  - correspondence_check
optional_checks:
  - conservation_check
  - unitarity_check
  - causality_check
  - approximation_validity_check
trust_audit_required: true
created_at: 2026-04-20T11:00:00Z
---

# L4 Validation Contract

## Scope

This contract governs the validation of candidates produced by
the quantum harmonic oscillator derivation topic.

## Mandatory Checks

| Check | Description | Applies To |
|-------|-------------|------------|
| dimensional_consistency | All equations have consistent physical dimensions | All candidates |
| symmetry_compatibility | Results respect declared symmetries of the system | All candidates |
| limiting_case_check | Known limits (classical, free, non-interacting) are recovered | All candidates |
| correspondence_check | Results agree with established results from trusted sources | All candidates |

## Optional Checks (Lane-Specific)

| Check | Condition |
|-------|-----------|
| conservation_check | Required when conserved quantities are claimed |
| unitarity_check | Required for scattering/S-matrix candidates |
| approximation_validity_check | Required when perturbative expansions are used |

## Trust Audit Requirements

Every L4 review must record:
- What was checked and how
- What passed, failed, or was inconclusive
- Trust boundary: what is locally closed vs still open
- Devil's advocate: one specific way the claim could still be wrong
