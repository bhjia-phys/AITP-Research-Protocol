# Phase 142: Pilot M2F Statement-Compilation Pattern For L2 Automated Formalization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 142-m2f-statement-compilation-pilot
**Areas discussed:** pre-Lean gap, packet shape, runtime integration

---

## Missing Surface

| Option | Description | Selected |
|--------|-------------|----------|
| explicit statement-compilation packet before Lean bridge | exposes Stage 1 and Stage 2 separately | ✓ |
| keep declaration skeletons implicit inside `lean_bridge` | hides the actual missing M2F-style boundary | |

## Runtime Integration

| Option | Description | Selected |
|--------|-------------|----------|
| integrate with existing candidate/theory-packet path | keeps formalization on one chain | ✓ |
| create a separate topic-level formalization subsystem | too much duplication and drift risk | |

## Target Design

| Option | Description | Selected |
|--------|-------------|----------|
| proof-assistant agnostic packet with explicit downstream targets | matches the milestone requirement | ✓ |
| Lean-only skeleton packet | too narrow for the intended contract | |
