# Phase 131: Package Identity And Distribution Asset Contract - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase hardens the package identity, version, and distribution-asset
contract behind the upcoming public PyPI install path.

The phase owns:

- public distribution naming and build metadata
- single-source version exposure
- inclusion of the runtime assets that must survive outside editable install

The phase does **not** own the final newcomer doc rewrite or the end-to-end
clean-install publication audit except where those surfaces need a stable
packaging contract first.

</domain>

<decisions>
## Implementation Decisions

### Distribution Identity
- **D-01:** The public package name should converge on an actually publishable
  PyPI name; the current implementation uses `aitp-kernel` because `aitp` is
  already occupied on PyPI.
- **D-02:** The import package may stay `knowledge_hub` if that keeps the diff
  smaller and does not block the public distribution contract.

### Version Contract
- **D-03:** Version reporting should come from one source of truth rather than
  duplicated literals in both `setup.py` and `knowledge_hub.__init__`.
- **D-04:** `aitp --version`, wheel metadata, and install diagnostics should
  expose the same semver.

### Distribution Assets
- **D-05:** The built wheel/sdist must carry the runtime assets needed by
  `aitp doctor`, `bootstrap`, and the shared first-run path, rather than
  relying on a git checkout plus editable path references.
- **D-06:** Editable install remains supported, but only as a contributor or
  migration lane rather than the default public contract.

### the agent's Discretion
- The build backend may stay setuptools if it can ship the public contract
  cleanly.
- Renaming the import package is not required unless a smaller change cannot
  satisfy the public distribution goal.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backlog And Milestone Scope
- `.planning/BACKLOG.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`

### Current Packaging Surface
- `research/knowledge-hub/setup.py`
- `research/knowledge-hub/knowledge_hub/__init__.py`
- `research/knowledge-hub/knowledge_hub/aitp_cli.py`
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py`

### Existing Verification Surface
- `research/knowledge-hub/runtime/scripts/run_dependency_contract_acceptance.py`
- `research/knowledge-hub/tests/test_dependency_contracts.py`
- `research/knowledge-hub/tests/test_documentation_entrypoints.py`
- `research/knowledge-hub/tests/test_aitp_service.py`

### Public Install Surface
- `docs/INSTALL.md`
- `README.md`
- `research/knowledge-hub/README.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `setup.py` already exposes console scripts for `aitp`, `aitp-mcp`, and
  `aitp-codex`; Phase `131` should extend that packaging contract rather than
  invent a new CLI entry path.
- `run_dependency_contract_acceptance.py` already builds a wheel and inspects
  metadata; extend that verification lineage instead of replacing it.

### Current Gaps
- `setup.py` still publishes `name=\"aitp-kernel\"`.
- `frontdoor_support.py` still queries and repairs the package as
  `aitp-kernel` plus `pip install -e research/knowledge-hub`.
- install docs and documentation entrypoint tests still assume editable install
  as the public default.

### Integration Points
- Any version-source refactor must stay aligned with doctor output and CLI
  tests that currently assert `0.4.0`.
- Any packaging-data change must keep runtime scripts, schemas, and protocol
  markdown available from an installed wheel.

</code_context>

<specifics>
## Specific Ideas

- Treat this as the contract-setting phase for the whole milestone.
- Prefer the smallest viable packaging diff that unlocks real PyPI
  distribution.

</specifics>

<deferred>
## Deferred Ideas

- Public doc migration and newcomer-facing install defaults belong primarily to
  Phase `132`.
- Final clean-install verification and closure evidence belong to Phase `133`.
- OpenClaw packaging parity remains outside this milestone.

</deferred>

---

*Phase: 131-package-identity-and-distribution-asset-contract*
*Context gathered: 2026-04-11*
