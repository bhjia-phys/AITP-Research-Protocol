# Phase 65: Retrieval Docs, Acceptance, And Regression Closure - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Brownfield continuation after closing Phase `64`

<domain>
## Phase Boundary

Close `v1.45` with:

- docs parity for the matured retrieval and graph-report surfaces
- a non-mocked acceptance path that covers the new graph report
- final regression closure for the milestone

This phase is about milestone closure.
It is not about adding another graph feature.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse `run_l2_mvp_direction_acceptance.py` as the bounded non-mocked
  acceptance path instead of inventing a second acceptance script.
- Docs parity must mention both `compile-l2-graph-report` and
  `derived_navigation/index.md`.
- Close `v1.45` only after the acceptance script and the full suite both pass.

### the agent's Discretion

- Exact wording for the updated milestone and acceptance descriptions.
- How much of the graph-report closure to describe in root versus runtime docs.

</decisions>

<canonical_refs>
## Canonical References

- `README.md`
- `research/knowledge-hub/README.md`
- `research/knowledge-hub/runtime/README.md`
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`
- `research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py`
- `research/knowledge-hub/tests/test_l2_backend_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Phases `62` through `64` already delivered retrieval, consultation artifacts,
  and graph-report navigation through production code.
- The remaining mismatch was public discoverability and acceptance coverage for
  the new graph-report command.
- The isolated MVP acceptance path already used a disposable kernel root, so it
  was the right place to extend non-mocked proof without polluting repo state.

</code_context>

<specifics>
## Specific Ideas

- Update root/kernel/runtime docs to name `aitp compile-l2-graph-report`.
- Upgrade `run_l2_mvp_direction_acceptance.py` to verify graph-report and
  derived-navigation artifacts.
- Close the milestone with final traceability and audit docs under
  `.planning/milestones/`.

</specifics>

<deferred>
## Deferred Ideas

- The next milestone selection after `v1.45` archive.

</deferred>

---

*Phase: 65-retrieval-docs-acceptance-and-regression-closure*
*Context captured on 2026-04-11 after Phase 65 implementation and verification*
