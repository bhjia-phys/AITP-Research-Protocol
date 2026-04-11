# Phase 133: Closure And Clean-Install Audit - Context

**Recorded:** 2026-04-11
**Status:** Retrospectively documented after implementation

<domain>
## Phase Boundary

This phase closes `v1.66` after the package identity and install-surface work
from Phases `131` and `132`.

The phase owns:

- correcting the public distribution name to an actually publishable PyPI name
  while preserving the `aitp` CLI
- adding one real clean-install smoke proof on an isolated virtualenv
- closing the milestone with packaging and install verification evidence

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Use `aitp-kernel` as the publishable distribution name because the
  `aitp` package name is already occupied on PyPI, but keep the CLI command as
  `aitp`.
- **D-02:** Keep the clean-install proof centered on a wheel-built isolated
  virtualenv instead of inventing a fake “works because the repo is nearby”
  claim.
- **D-03:** Treat `aitp --version` plus `aitp doctor --json` as the public
  command-entry smoke, then run the isolated first-run path from the installed
  wheel-backed runtime itself.
- **D-04:** Close `v1.66` without reopening `v1.65` install/adoption work or
  widening the milestone into new runtime parity scope.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/runtime/scripts/run_dependency_contract_acceptance.py`
- `research/knowledge-hub/runtime/scripts/run_public_install_smoke.py`
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py`
- `research/knowledge-hub/knowledge_hub/bundle_support.py`
- `research/knowledge-hub/tests/test_public_install_contracts.py`
- `research/knowledge-hub/tests/test_dependency_contracts.py`
- `research/knowledge-hub/tests/test_quickstart_contracts.py`
- `docs/PUBLISH_PYPI.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- selecting and planning the next milestone remains outside `v1.66`

</deferred>

---

*Phase: 133-closure-and-clean-install-audit*
