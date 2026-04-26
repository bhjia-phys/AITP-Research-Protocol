# Phase 149: Hypothesis Route Activation Surface - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 149-hypothesis-route-activation-surface
**Areas discussed:** route activation visibility, coexistence with queue/steering, bounded scope

---

## Surface Placement

| Option | Description | Selected |
|--------|-------------|----------|
| extend existing route metadata into activation summary | preserves one visible runtime truth path | ✓ |
| invent a separate activation subsystem | would fragment the operator model | |

## Relation To Existing Mechanisms

| Option | Description | Selected |
|--------|-------------|----------|
| coexist with queue, steering, deferred, and follow-up surfaces | keeps current execution surfaces intact | ✓ |
| replace queue or branch mechanisms | widens scope too far | |

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| declarative route-activation summary | closes the immediate next gap cleanly | ✓ |
| automatic branch spawning or scheduling | too wide for the immediate next milestone | |
