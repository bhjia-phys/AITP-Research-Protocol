# Phase 138: Knowledge Compilation Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 138-knowledge-compilation-contract
**Areas discussed:** scope, provenance boundary, contract shape

---

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| extend the existing `l2_compiler` family | keeps the new surface bounded and coherent | ✓ |
| create a separate knowledge-memory subsystem | too broad for the first slice | |

---

## Provenance Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| mixed-provenance compiled view with explicit authority levels | matches backlog intent without bypassing `L4` | ✓ |
| treat compiled knowledge as canonical by default | violates the promotion boundary | |

---

## Contract Shape

| Option | Description | Selected |
|--------|-------------|----------|
| added/updated/provisional/contradiction summaries plus navigation | gives one real compiled-knowledge surface | ✓ |
| another raw graph dump with different labels | not enough value beyond current reports | |

---

## Deferred Ideas

- full version history
- background refresh hooks
- multi-user sync
