# Phase 6 Plan 02 Summary

Date: 2026-04-01
Status: Complete

## One-line outcome

`AITPService.project_topic_skill()` now supports a bounded `formal_theory` lane
and fails honestly unless theorem-facing trust artifacts, topic-completion
state, and strategy memory are all ready.

## What changed

- Added a theorem-facing candidate selection helper inside `AITPService`.
- Extended `_derive_topic_skill_projection()` so `formal_theory` can become
  `available` only when:
  - the active run exists,
  - a ready `formal_theory_review.json` exists,
  - `topic_completion.json` is `promotion-ready` or `promoted`,
  - strategy memory has at least one row.
- Kept non-ready formal-theory topics on `blocked` or `not_applicable` and
  suppressed false projection candidate rows.
- Added positive and negative service tests for the new gate.

## Verification

- `python -m pytest research/knowledge-hub/tests/test_aitp_service.py -q`
  - `62 passed`
- `python -m pytest research/knowledge-hub/tests/test_schema_contracts.py research/knowledge-hub/tests/test_runtime_profiles_and_projections.py research/knowledge-hub/tests/test_aitp_service.py -q`
  - `77 passed`

## Notes

- The existing `code_method` projection flow remained green.
- This plan enabled the later Jones seed acceptance work by making
  formal-theory projections materializable from real theorem-facing packets.
