# Phase 71 Summary

Status: implemented on `main`

## Goal

Make analytical validation leave durable review artifacts and expose them
through the active runtime review surfaces.

## What Landed

- `analytical-review` is now a production CLI command
- `AITPService.audit_analytical_review(...)` now writes
  `analytical_review.json` into theory-packet storage with named analytical
  checks, source anchors, regime context, and reading depth
- candidate ledgers now retain analytical review status and theory-packet refs
- `validation_review_bundle.active.json/.md` now includes `analytical_review`
  as a specialist artifact and prefers it as the primary review kind in
  analytical mode
- a non-mocked CLI e2e test now proves the artifact is written and then
  surfaced through runtime bundle materialization

## Outcome

Phase `71` is complete.
The next active milestone step is Phase `72`
`research-judgment-signals-in-decision-surfaces`.
