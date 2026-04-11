# Phase 95 Summary

Status: implemented on `main`

## Goal

Route service and frontdoor subprocess failures through a shared diagnostic
formatter so operators get actionable error messages.

## What Landed

- new helper module:
  `research/knowledge-hub/knowledge_hub/subprocess_error_support.py`
- `AITPService._run()` now raises structured failure messages
- `migrate_local_install()` now raises structured pip-install failure messages

## Outcome

Phase `95` is complete.
`v1.54` now has production subprocess diagnostics.
