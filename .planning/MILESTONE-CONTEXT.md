# Milestone Context

Current milestone: `v1.65` `Installation And Adoption Readiness`

## Latest Closed Milestone

`v1.64` `L1 Method Specificity Surface`

## Why It Was Next

The backlog now explicitly overrides the old ordering for user-facing
installation and first-use work.

Current priority is to improve installation and first-use surfaces before
promoting deeper collaborator-core backlog.

That means the next bounded milestone should focus on:

- `999.49` installation verification and smoke-test hardening
- `999.50` 5-minute quickstart and first-run proof
- `999.51` Windows path and symlink robustness

while leaving `999.48` PyPI publication for a later dedicated milestone.

## What This Closure Protects

- Do not reopen old install/use entry items like `999.3`, `999.4`, or `999.5`
  as separate milestones.
- Keep the install/adoption work centered on the canonical cluster
  `999.49` through `999.51`.
- Keep OpenClaw as a specialized lane rather than a front-door parity target
  for this milestone.

## Current Status

`v1.65` is active.

Immediate next repository task:

- discuss and plan Phase `127`
- do not reopen `v1.64` unless a fresh regression appears
