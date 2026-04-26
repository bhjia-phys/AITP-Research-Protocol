# Phase 133 Summary

Status: implemented on `main`

## Goal

Close the public-package milestone with one honest clean-install proof and
aligned planning state.

## What Landed

- the publishable package identity is now consistently documented as
  `aitp-kernel` while preserving the `aitp` CLI
- a new `run_public_install_smoke.py` acceptance script builds a wheel,
  installs it into a clean virtualenv, and proves the installed runtime can run
  the first-run path on isolated roots
- milestone planning, traceability, and archived closure records are now
  aligned with the shipped public-package state

## Outcome

Phase `133` is complete.
`v1.66` is ready to stand as the closed PyPI/package milestone.
