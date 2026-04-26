# Phase 73: Docs, Acceptance, And Regression Closure - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Final closure phase for `v1.47`

<domain>
## Phase Boundary

Close `v1.47` with:

- docs parity for the new analytical-review and research-judgment surfaces
- one non-mocked acceptance path proving analytical validation plus judgment
  surfaces together through production CLI
- final regression and maintainability confirmation

This phase is milestone-close packaging, not a new feature family.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- The final non-mocked proof should use production CLI entrypoints end to end.
- The acceptance path should stay isolated on a temporary kernel root rather
  than mutating repo runtime state.
- Runtime README and the runtime test runbook must both mention the new
  `research_judgment.active.json|md` surface and its acceptance script.

### the agent's Discretion

- Which minimal temp-kernel fixtures are enough to prove the combined surface.
- Whether kernel docs should mention the new acceptance path in addition to the
  runtime docs.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py`
- `research/knowledge-hub/runtime/README.md`
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`
- `research/knowledge-hub/README.md`
- `research/knowledge-hub/tests/test_research_judgment_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- The isolated acceptance-script pattern already existed for source catalog and
  `L2` MVP closure, so `v1.47` could reuse that style instead of inventing a
  new harness.
- Phase 72 had already landed the real runtime surfaces, so closure work could
  focus on discoverability and one combined proof path.

</code_context>

<specifics>
## Specific Ideas

- Add `run_analytical_judgment_surface_acceptance.py`.
- Make it run production `analytical-review`, `verify --mode analytical`, and
  `status --json` in one isolated flow.
- Document the new runtime judgment surface and acceptance entrypoint in both
  runtime README and test runbook.

</specifics>

<deferred>
## Deferred Ideas

- next-milestone selection after `v1.47`

</deferred>

---

*Phase: 73-docs-acceptance-and-regression-closure*
*Context captured on 2026-04-11 after Phase 73 implementation and verification*
