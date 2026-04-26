# Phase 136: OpenCode Deep-Execution Probe - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 136-opencode-deep-execution-probe
**Areas discussed:** bootstrap entry surface, plugin proof shape, parity-gap reporting

---

## Bootstrap Entry Surface

| Option | Description | Selected |
|--------|-------------|----------|
| real plugin-module hook execution | covers the supported OpenCode bootstrap surface | ✓ |
| file presence only | too weak to count as a deep-execution probe | |

**User's choice:** Auto-selected recommended bootstrap path.

---

## Probe Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| temp `.opencode` install plus real plugin hooks and isolated runtime artifacts | honest bounded deep-execution proof | ✓ |
| claim full OpenCode parity without hook/runtime evidence | overclaims what is actually measured | |

**User's choice:** Auto-selected recommended bounded probe.

---

## Honesty Policy

| Option | Description | Selected |
|--------|-------------|----------|
| land the probe and report remaining live-OpenCode gap explicitly | matches milestone requirement | ✓ |
| mark OpenCode parity as closed once the plugin hook test exists | false closure | |

**User's choice:** Auto-selected recommended reporting policy.

---

## the agent's Discretion

- exact deep-execution status label once the probe lands
- exact comparison field names in the parity report

## Deferred Ideas

- full OpenCode parity closure
- cross-runtime closure report
- OpenClaw deep parity
