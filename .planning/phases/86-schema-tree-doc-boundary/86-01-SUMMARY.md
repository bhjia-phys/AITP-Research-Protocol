# Phase 86 Summary

Status: implemented on `main`

## Goal

Document the public-versus-runtime schema-tree boundary in durable docs and
guard that boundary with tests.

## What Landed

- `schemas/README.md` now defines the public schema authority and mirror rule
- `research/knowledge-hub/schemas/README.md` now defines package-local schemas
  versus root mirrors
- `docs/architecture.md` now explains where public schemas live and why the
  installable runtime keeps shared copies

## Outcome

Phase `86` is complete.
`v1.51` now has explicit schema-tree boundary docs.
