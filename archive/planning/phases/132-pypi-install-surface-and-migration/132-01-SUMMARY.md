# Phase 132 Summary

Status: implemented on `main`

## Goal

Shift the newcomer-facing install and migration surface from editable-install
first to public-package first.

## What Landed

- install docs and READMEs now default to `python -m pip install aitp-kernel`
- editable install is now explicitly documented as the contributor / local-dev
  lane rather than the default public path
- a new PyPI release runbook exists in
  `docs/PUBLISH_PYPI.md`

## Outcome

Phase `132` is complete.
`v1.66` now has a public-package-first install surface and an explicit release
workflow doc.
