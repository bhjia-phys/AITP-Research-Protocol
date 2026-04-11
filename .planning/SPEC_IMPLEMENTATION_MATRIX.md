# Spec And Plan Implementation Matrix

## Status

The current 2026-04-07 to 2026-04-10 design chain has been translated into
closed milestones through `v1.42`:

- `v1.34` closed
- `v1.35` closed
- `v1.36` closed
- `v1.37` closed
- `v1.38` closed
- `v1.39` closed
- `v1.40` closed
- `v1.41` closed
- `v1.42` closed

Additional post-remediation audit milestones are also closed:

- `v1.62` closed
- `v1.63` closed
- `v1.60` closed
- `v1.61` closed
- `v1.50` closed
- `v1.51` closed
- `v1.52` closed
- `v1.53` closed
- `v1.54` closed
- `v1.55` closed
- `v1.56` closed
- `v1.57` closed
- `v1.58` closed
- `v1.59` closed

- `docs/superpowers/specs/2026-04-07-aitp-collaborator-rectification-and-interaction-design.md`
  - status: implemented through the bounded remediation chain
  - completed promoted slices: `34` through `53`, `115`, `116`, `118`, `119`
  - active promoted remainder: none
  - later remainder beyond `v1.42`: any further collaborator-core expansion
    must be scoped as a fresh milestone
- `docs/superpowers/specs/2026-04-08-aitp-research-scenario-and-layer-responsibility-freeze-design.md`
  - status: implemented through the bounded remediation chain
  - completed promoted slices: `37` through `53`, `112`, `113`
  - active promoted remainder: none
  - later remainder beyond `v1.42`: the first post-remediation `L3-A/L3-R/L3-D`
    layer-graph slice is now implemented in `v1.60`; any deeper orchestration
    maturity beyond that must still be reopened explicitly
- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
  - status: bounded implementation promoted through `v1.42`
  - completed promoted slices: `34`, `35`, `36`, `46`, `49`, `50`, `52`, `53`
  - active promoted remainder: none
  - later remainder: richer multi-backend governance or larger graph policy
    work must be reopened explicitly
- `docs/superpowers/specs/2026-04-09-aitp-soft-exploration-hard-trust-runtime-design.md`
  - status: promoted through the remediation chain
  - completed promoted slices: `37`, `39`, `41`, `47`, `48`, `50`, `51`, `53`
  - active promoted remainder: none
  - later remainder: deeper stop/notify/report timing and stronger event-shaped
    human-facing surfaces, if still needed, should be scoped in a fresh
    milestone

- `docs/superpowers/plans/2026-04-10-aitp-v137-v142-remediation.md`
  - status: implemented and archived on `main`
  - completed promoted slices: `46`, `47`, `48`, `49`, `50`, `51`, `52`, `53`
  - active promoted remainder: none
  - verification anchor:
    `docs/superpowers/plans/2026-04-10-aitp-v137-v142-remediation-review.md`

## Immediate Reopen Reason

Open reopen reason: backlog `999.27` still lacked real method-specificity
surfaces even after the archived remediation chain and the later
post-remediation milestones through `v1.63`.

That gap is now closed for its first production slice in `v1.64`.

The next milestone should be opened only after identifying a new blocker that
is not already covered by the archived remediation phases, the closed
follow-up audit milestones, the `v1.60` layer-graph surface, the `v1.61`
research-taste surface, the `v1.62` scratchpad surface, the `v1.63`
BibTeX source surface, or the `v1.64` method-specificity surface.
