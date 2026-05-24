# Validation Contract

## Purpose

Define how a candidate is supposed to be checked before acceptance.

## Minimum fields

- `validation_id`
- `topic_slug`
- `target_claim_ids`
- `status`
- `validation_mode`
- `acceptance_rule`
- `rejection_rule`
- `artifacts`

## High-rigor fields for non-trivial validation

When validation is more than a lightweight smoke check, it should also declare:

- `required_checks`
- `oracle_artifacts`
- `executed_evidence`
- `confidence_cap`
- `gap_followups`
- `failure_modes`

## v5 validation result statuses

- Canonical result statuses are `passed`, `partial`, `failed`, and
  `inconclusive`.
- Natural aliases are accepted at the tool boundary: for example `pass` becomes
  `passed`, and `partial_pass` becomes `partial`.
- Use `partial` when a broad validation contract has only been partly checked.
  Record the inspected outputs and, when applicable, the exact contract
  `covered_failure_modes` that were closed.
- Only full `passed` results with no missing outputs and no observed failure
  modes can support trust promotion. Partial results are durable progress
  records, not promotion evidence.

## Why it matters

Validation should be declared before the result is interpreted.
Validation should also say what does not count as success, what evidence is
still missing, and how confidence is capped when execution evidence is absent.
