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

## Why it matters

Validation should be declared before the result is interpreted.
Validation should also say what does not count as success, what evidence is
still missing, and how confidence is capped when execution evidence is absent.
