# Phase 134: Runtime Parity Contract And Shared Acceptance Harness - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 134-runtime-parity-contract-and-shared-acceptance-harness
**Areas discussed:** runtime scope, contract shape, acceptance harness

---

## Runtime Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Codex baseline + Claude/OpenCode parity targets | stays aligned with current user priority | ✓ |
| include OpenClaw in the same parity pass | widens scope too early | |

**User's choice:** Auto-selected recommended scope.

---

## Contract Shape

| Option | Description | Selected |
|--------|-------------|----------|
| keep install readiness and deep-execution readiness separate | preserves honesty | ✓ |
| overload current doctor readiness rows with execution claims | risks false parity green checks | |

**User's choice:** Auto-selected recommended contract split.

---

## Acceptance Harness

| Option | Description | Selected |
|--------|-------------|----------|
| reuse bounded real-topic acceptance anchors | gives honest artifact-level evidence | ✓ |
| invent a synthetic parity-only mock shell | too detached from real runtime behavior | |

**User's choice:** Auto-selected recommended harness style.

---

## the agent's Discretion

- exact parity report field names
- exact acceptance script naming, as long as it stays parity-facing and
  operator-visible

## Deferred Ideas

- runtime-specific Claude Code fixes
- runtime-specific OpenCode fixes
- OpenClaw deep parity
