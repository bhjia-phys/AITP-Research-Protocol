# Phase 152: Hypothesis Route Choice Surface - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 152-hypothesis-route-choice-surface
**Areas discussed:** stay-local versus yield choice visibility, relation to current route choice, bounded scope

---

## Surface Placement

| Option | Description | Selected |
|--------|-------------|----------|
| extend current-route-choice with hypothesis-aware choice summary | preserves one visible operator truth path | ✓ |
| invent a separate route-choice subsystem | would fragment the operator model | |

## Relation To Existing Mechanisms

| Option | Description | Selected |
|--------|-------------|----------|
| coexist with current route choice, route handoff, and helper mechanisms | keeps current execution surfaces intact | ✓ |
| auto-trigger mutation from the new summary | widens scope too far | |

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| declarative route-choice visibility | closes the immediate gap cleanly | ✓ |
| automatic route mutation or scheduling | too wide for the immediate next milestone | |
