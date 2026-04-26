# Phase 128: Shared Quickstart And First-Run Acceptance - Context

**Recorded:** 2026-04-11
**Status:** Retrospectively documented after implementation

<domain>
## Phase Boundary

This phase owns the first successful user path after installation is verified.

The scope is the shared, runtime-neutral path from a good install to one real
bounded topic run:

- `bootstrap`
- `loop`
- `status`

The phase does not redefine per-runtime native entry surfaces. It documents the
shared first-run proof that all three front-door runtimes can fall back to.

</domain>

<decisions>
## Implementation Decisions

### Shared Proof Shape
- **D-01:** Use one real topic instead of a synthetic `demo-topic`.
- **D-02:** Keep the proof bounded to `bootstrap -> loop -> status`.
- **D-03:** Treat the direct CLI flow as the canonical verification path, even
  when native runtime entry surfaces differ.

### Acceptance Contract
- **D-04:** Back the quickstart with one isolated acceptance script that runs
  the production CLI on a temp kernel root.
- **D-05:** Lock the quickstart contract in docs and regression tests so the
  first-run path cannot silently drift per runtime.

</decisions>

<canonical_refs>
## Canonical References

- `docs/QUICKSTART.md`
- `docs/INSTALL.md`
- `README.md`
- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py`
- `research/knowledge-hub/tests/test_quickstart_contracts.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<deferred>
## Deferred Ideas

- Native front-door polish for each runtime stays in their install docs.
- PyPI packaging remains outside `v1.65`.

</deferred>

---

*Phase: 128-shared-quickstart-and-first-run-acceptance*
