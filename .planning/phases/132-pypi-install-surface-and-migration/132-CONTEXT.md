# Phase 132: PyPI Install Surface And Migration - Context

**Recorded:** 2026-04-11
**Status:** Retrospectively documented after implementation

<domain>
## Phase Boundary

This phase owns the newcomer-facing install surface after the package contract
from Phase `131` exists.

The scope is:

- default install docs for `pip install aitp-kernel`
- adapter install docs that no longer assume editable install first
- migration docs that separate repo-backed local convergence from public-package
  migration
- a repeatable release runbook for building and publishing the public package

This phase does not own the final clean-install smoke evidence on a fresh
environment. That remains closure work.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Make `pip install aitp-kernel` the default newcomer path everywhere
  user-facing docs are primarily about installation.
- **D-02:** Keep editable install documented, but explicitly demote it to the
  contributor / local-dev lane.
- **D-03:** Do not invent fake one-click claims for OpenCode or Claude Code;
  keep each runtime doc honest about its real front-door activation path.
- **D-04:** Split public-package migration from repo-backed
  `migrate-local-install` so the command contract is not misrepresented.
- **D-05:** Document the PyPI release workflow explicitly instead of burying it
  in milestone notes.

</decisions>

<canonical_refs>
## Canonical References

- `README.md`
- `docs/INSTALL.md`
- `docs/INSTALL_CODEX.md`
- `docs/INSTALL_CLAUDE_CODE.md`
- `docs/INSTALL_OPENCODE.md`
- `docs/INSTALL_OPENCLAW.md`
- `docs/QUICKSTART.md`
- `docs/MIGRATE_LOCAL_INSTALL.md`
- `docs/UNINSTALL.md`
- `.codex/INSTALL.md`
- `.opencode/INSTALL.md`
- `docs/PUBLISH_PYPI.md`
- `research/knowledge-hub/tests/test_documentation_entrypoints.py`
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py`
- `research/knowledge-hub/tests/test_quickstart_contracts.py`

</canonical_refs>

<deferred>
## Deferred Ideas

- a true clean-environment `pip install aitp-kernel` smoke gate stays in Phase `133`
- final closure evidence and milestone audit remain Phase `133`

</deferred>

---

*Phase: 132-pypi-install-surface-and-migration*
