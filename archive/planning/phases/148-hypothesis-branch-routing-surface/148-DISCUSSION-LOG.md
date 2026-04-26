# Phase 148: Hypothesis Branch Routing Surface - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 148-hypothesis-branch-routing-surface
**Areas discussed:** branch intent visibility, relation to deferred/follow-up lanes, bounded scope

---

## Surface Placement

| Option | Description | Selected |
|--------|-------------|----------|
| extend `competing_hypotheses` rows | preserves one visible question-level truth path | ✓ |
| invent a separate branch ledger | would fragment the operator model | |

## Relation To Existing Mechanisms

| Option | Description | Selected |
|--------|-------------|----------|
| coexist with steering, deferred, and follow-up mechanisms | keeps current execution surfaces intact | ✓ |
| replace deferred/follow-up/steering surfaces | widens scope too far | |

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| declarative hypothesis routing visibility | closes the immediate gap cleanly | ✓ |
| automatic branch spawning/scheduling | too wide for the immediate next milestone | |
