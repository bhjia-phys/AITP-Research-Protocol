# Phase 141: Adopt LLM-Wiki-Skill Three-Layer Vault And Flowback Into L1 Knowledge Compilation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 141-l1-three-layer-vault-and-flowback
**Areas discussed:** vault scope, entrypoint choice, flowback contract

---

## Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| extend `ensure_topic_shell_surfaces()` | reuse the existing L1 topic-shell and runtime status path | ✓ |
| open a brand-new dedicated CLI compiler first | adds a parallel surface before the main path is stable | |

## Raw Layer Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| anchor raw inputs to `source-layer` through manifests and refs | keeps one immutable truth source | ✓ |
| duplicate source files into `intake/topics/<slug>/vault/raw` | risks second-truth drift and writable copies | |

## Flowback Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| output digest plus explicit flowback ledger | makes query→wiki sync inspectable | ✓ |
| silently rewrite wiki pages without receipts | too opaque for protocol-first AITP | |
