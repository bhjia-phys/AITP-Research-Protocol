# Phase 167-01 Summary

Status: implemented in working tree

## Goal

Upgrade the current `L1` contradiction intake path into richer, source-backed
contradiction rows with explicit comparison basis, while preserving the
existing `contradiction_candidates` chain and keeping the broader runtime
surface cleanup for Phase `167.1`.

## What Landed

- `detect_contradiction_candidates(...)` now emits richer contradiction
  metadata, including comparison basis and side-specific basis summaries
- `derive_l1_conflict_intake(...)` now keeps one bounded contradiction row per
  source pair and contradiction detail, preferring the stronger `regime_rows`
  basis when duplicates compete
- contradiction rows now carry:
  - `comparison_basis`
  - `source_basis_type`
  - `source_basis_summary`
  - `source_evidence_excerpt`
  - `against_basis_type`
  - `against_basis_summary`
  - `against_evidence_excerpt`
- the richer row contract now exists in:
  - `schemas/research-question.schema.json`
  - `schemas/topic-synopsis.schema.json`
  - `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
- the existing contradiction-aware acceptance lane still runs on the upgraded
  row contract

## Verification

- focused service contradiction slice:
  - `2 passed`
- schema contracts:
  - `11 passed`
- contradiction-aware acceptance invocation:
  - `1 passed`
- final phase regression slice:
  - `14 passed`

## Outcome

`REQ-L1CON-01` and `REQ-L1CON-02` are now satisfied:

- `L1` contradiction rows are now explicit, pairwise, and source-backed
- each contradiction row carries the bounded comparison basis needed for later
  human/runtime surfaces

## Next Step

Proceed to Phase `167.1` for runtime/read-path contradiction parity and the
bounded milestone proof lane.
