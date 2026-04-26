# Phase 60: Seeded Direction And Bounded Retrieval Proof - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `59`

<domain>
## Phase Boundary

Turn the seeded MVP `L2` direction into a reviewable proof surface by exposing
compiled memory-map artifacts, hygiene artifacts, and one non-mocked acceptance
path that exercises the bounded direction end to end.

This phase is about proof and auditability:

- compiled map
- hygiene report
- one bounded MVP acceptance flow

This phase is not yet about public docs closeout or broad graph maturity.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse the existing helpers in `l2_compiler.py` and `l2_hygiene.py` rather
  than creating duplicate proof logic.
- Expose those helpers through production service and CLI entrypoints.
- The acceptance path should operate on an isolated kernel root so it proves
  production code without polluting repo runtime state.
- The acceptance path must seed and consult the bounded TFIM direction before
  compiling and auditing it.

### the agent's Discretion

- Exact CLI names for compiled/hygiene commands, as long as they remain explicit.
- Exact acceptance assertions, as long as they verify:
  - the seeded `physical_picture`
  - consultable retrieval
  - compiled memory map output
  - hygiene output

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/l2_compiler.py`
- `research/knowledge-hub/knowledge_hub/l2_hygiene.py`
- `research/knowledge-hub/runtime/scripts/compile_l2_workspace_map.py`
- `research/knowledge-hub/runtime/scripts/audit_l2_hygiene.py`
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/aitp_cli.py`
- `research/knowledge-hub/tests/test_l2_compiler.py`
- `research/knowledge-hub/tests/test_l2_hygiene.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- `compile_l2_workspace_map.py` and `audit_l2_hygiene.py` already exist as
  standalone scripts, but there is no public `aitp` command family for them
- service currently has seed/consult wrappers, but not compiled/hygiene wrappers
- the seeded TFIM direction is now reachable through CLI, so a bounded
  acceptance script can stay entirely on production surfaces

</code_context>

<specifics>
## Specific Ideas

- Add `AITPService.compile_l2_workspace_map(...)`
- Add `AITPService.audit_l2_hygiene(...)`
- Add CLI commands:
  - `aitp compile-l2-map`
  - `aitp audit-l2-hygiene`
- Add `run_l2_mvp_direction_acceptance.py` to prove:
  - seed
  - consult
  - compile map
  - hygiene report

</specifics>

<deferred>
## Deferred Ideas

- public docs closeout for the new L2 command family
- larger seeded directions beyond TFIM MVP
- stronger contradiction/bridge policy over seeded memory

</deferred>

---

*Phase: 60-seeded-direction-and-bounded-retrieval-proof*
*Context gathered: 2026-04-11 after Phase 59 production command-family closure*
