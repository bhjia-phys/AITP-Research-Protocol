# Phase 61: L2 MVP Docs, Acceptance, And Regression Closure - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `60`

<domain>
## Phase Boundary

Close `v1.44` by making the new L2 MVP command family and acceptance surface
visible in the public docs and test runbook, then re-run the final regression
gate.

This phase is about public parity and milestone closure:

- README parity
- runtime runbook parity
- final milestone-close verification

This phase is not about adding more `L2` graph features.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Public docs must mention the new bounded `L2` commands directly:
  - `aitp seed-l2-direction`
  - `aitp consult-l2`
  - `aitp compile-l2-map`
  - `aitp audit-l2-hygiene`
- The runtime runbook must include the isolated MVP acceptance script.
- Close `v1.44` only after the full suite and the isolated MVP acceptance pass.

### the agent's Discretion

- Which docs get updated beyond the kernel README and runtime runbook, as long
  as the public command path is clear and tested.

</decisions>

<canonical_refs>
## Canonical References

- `README.md`
- `research/knowledge-hub/README.md`
- `research/knowledge-hub/runtime/README.md`
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`
- `research/knowledge-hub/tests/test_l2_backend_contracts.py`
- `research/knowledge-hub/runtime/scripts/run_l2_mvp_direction_acceptance.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- The new L2 MVP commands and isolated acceptance exist in production code, but
  public docs do not yet point operators at them.
- Kernel README already mentions compiled and hygiene artifacts, so this phase
  mainly needs command/acceptance discoverability, not new protocol invention.

</code_context>

<specifics>
## Specific Ideas

- Add the four L2 MVP commands to root and kernel README command sections
- Add the isolated MVP acceptance command to runtime README and test runbook
- Close the milestone with final audit docs under `.planning/milestones/`

</specifics>

<deferred>
## Deferred Ideas

- future docs for graph maturity beyond the MVP direction
- broader user-facing walkthroughs for multiple seeded directions

</deferred>

---

*Phase: 61-l2-mvp-docs-acceptance-and-regression-closure*
*Context gathered: 2026-04-11 after Phase 60 compiled/hygiene proof closure*
