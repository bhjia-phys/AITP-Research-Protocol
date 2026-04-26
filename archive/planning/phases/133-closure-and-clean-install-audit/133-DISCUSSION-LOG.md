# Phase 133: Closure And Clean-Install Audit - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 133-closure-and-clean-install-audit
**Areas discussed:** real publishable package identity, clean-install proof shape, milestone closure criteria

---

## Public Distribution Identity

| Option | Description | Selected |
|--------|-------------|----------|
| `aitp-kernel` package + `aitp` CLI | publishable and minimally disruptive | ✓ |
| keep `aitp` as the package name | blocked by existing PyPI occupant | |

---

## Clean-Install Evidence

| Option | Description | Selected |
|--------|-------------|----------|
| wheel install into temp venv + isolated smoke path | honest public-package proof | ✓ |
| repo-local editable install only | does not prove the PyPI path | |

---

## Closure Policy

| Option | Description | Selected |
|--------|-------------|----------|
| close `v1.66` after package, docs, and clean-install evidence align | bounded and sufficient | ✓ |
| reopen `v1.65` or expand into new runtime parity scope | scope creep | |

---

## Deferred Ideas

- next-milestone selection remains separate from `v1.66` closure
