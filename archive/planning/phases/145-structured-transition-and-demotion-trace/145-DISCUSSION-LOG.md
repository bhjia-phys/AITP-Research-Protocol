# Phase 145: Structured Transition And Demotion Trace - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 145-structured-transition-and-demotion-trace
**Areas discussed:** runtime history, demotion honesty, replay surfaces

---

## History Surface

| Option | Description | Selected |
|--------|-------------|----------|
| extend runtime replay + promotion trace | preserves continuity with the existing runtime shell | ✓ |
| invent a standalone history subsystem | would fragment runtime truth surfaces | |

## Backward Moves

| Option | Description | Selected |
|--------|-------------|----------|
| treat demotions as first-class history | keeps overturned conclusions operator-visible | ✓ |
| silently overwrite current stage only | hides the real research path | |

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| bounded transition/demotion trace | closes the immediate runtime-history gap | ✓ |
| full competing-hypothesis / evaluator-modification stack | too wide for the immediate next milestone | |
