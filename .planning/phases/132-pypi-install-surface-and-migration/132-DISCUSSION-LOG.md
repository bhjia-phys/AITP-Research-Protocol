# Phase 132: PyPI Install Surface And Migration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-11
**Phase:** 132-pypi-install-surface-and-migration
**Areas discussed:** public install defaults, honest runtime-specific migration language, release workflow docs

---

## Public Install Default

| Option | Description | Selected |
|--------|-------------|----------|
| `pip install aitp-kernel` by default | newcomer-facing install surface | ✓ |
| keep editable install first | preserve old repo-first entry | |

---

## Editable Install Position

| Option | Description | Selected |
|--------|-------------|----------|
| contributor / local-dev lane | honest but no longer default | ✓ |
| hide editable install entirely | too aggressive for maintainers | |

---

## Migration Contract

| Option | Description | Selected |
|--------|-------------|----------|
| separate public-package migration from repo-backed convergence | keeps command semantics honest | ✓ |
| treat `migrate-local-install` as universal | overclaims what the command does today | |

---

## Deferred Ideas

- clean-environment smoke still belongs to Phase `133`
