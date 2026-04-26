# Phase 72 Summary

Status: implemented on `main`

## Goal

Expose bounded research-judgment signals through durable runtime and
decision-surface outputs instead of leaving them implicit.

## What Landed

- `research_judgment.active.json/.md` is now materialized under each runtime
  topic as a durable judgment artifact
- judgment signals are derived from existing durable surfaces such as
  collaborator-memory `stuckness` / `surprise`, strategy memory, open-gap
  state, dependency state, and last-evidence-return receipts
- `topic_synopsis.runtime_focus` now exposes `momentum_status`,
  `stuckness_status`, `surprise_status`, and `judgment_summary`
- runtime-bundle `decision_surface` snapshots now expose the same judgment
  signals and the judgment note path
- when judgment signals are active, the runtime bundle adds the judgment note
  to `must_read_now`
- helper extraction kept watched hotspot files inside maintainability budgets

## Outcome

Phase `72` is complete.
The next active milestone step is Phase `73`
`docs-acceptance-and-regression-closure`.
