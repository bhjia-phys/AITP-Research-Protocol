# Phase 127: Doctor And Front-Door Verification Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 127-doctor-and-front-door-verification-hardening
**Areas discussed:** front-door scope, doctor contract shape, human-readable doctor output

---

## Front-Door Runtime Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Codex + Claude Code + OpenCode | Adoption-facing front-door parity target set | ✓ |
| Include OpenClaw parity | Expand scope into specialized autonomous lane | |
| Only baseline Codex | Delay parity work for Claude/OpenCode | |

**User's choice:** Prioritize Codex, Claude Code, and OpenCode together.
**Notes:** OpenClaw stays visible but is not part of the front-door parity
target for this milestone.

---

## Doctor Contract Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Per-runtime remediation contract + top-level convergence | Machine-readable and user-facing install truth | ✓ |
| Raw issue codes only | Keep diagnosis low-level and docs-heavy | |
| Top-level only | Hide per-runtime detail behind one aggregate result | |

**User's choice:** Expose both per-runtime remediation and top-level
convergence.
**Notes:** The doctor surface must be usable both by humans and CI.

---

## Human-Readable Output

| Option | Description | Selected |
|--------|-------------|----------|
| Front-door summary first | Show readiness, repair command, and docs per runtime | ✓ |
| Full nested payload dump | Preserve the raw JSON structure in text form | |
| Per-runtime only with no aggregate view | Force users to infer convergence manually | |

**User's choice:** Human-readable doctor output should lead with front-door
summary information.
**Notes:** The user should not need to parse the entire nested payload to find
the next repair command.

---

## the agent's Discretion

- Exact JSON field names may shift as long as readiness, remediation, and
  convergence semantics remain stable and test-covered.

## Deferred Ideas

- Quickstart walkthrough details and first-run proof belong to Phase `128`.
- Broader Windows-native bootstrap cleanup belongs to Phase `129`.

