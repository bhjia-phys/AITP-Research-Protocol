# Milestone Context

Current milestone: none selected

## Latest Closed Milestone

`v1.66` `PyPI Publishable Package`

## Why It Was Next

The backlog promotion override explicitly put `999.48` before the just-closed
install/adoption hardening cluster.

`v1.65` shipped the doctor, quickstart, and Windows-native first-use surfaces.
The remaining adjacent adoption blocker is that the public install still starts
with a repo clone plus editable install.

That means the next bounded milestone should focus on:

- `999.48` PyPI publishable package
- public versioned installation and release workflow
- migration away from editable-install-first newcomer docs

## What This Closure Protects

- Do not reopen `999.49` through `999.51` as substitute work for package
  publication.
- Keep OpenClaw as a specialized lane rather than expanding this milestone into
  broader runtime parity.
- Avoid broad repository restructuring unless it is directly required to ship a
  public `aitp-kernel` package while preserving the `aitp` CLI.

## Current Status

`v1.66` is complete.

Immediate next repository task:

- select the next bounded milestone from backlog
- keep `v1.65` and `v1.66` closed unless a fresh install/adoption or packaging
  regression appears
