# Phase 139: Compiled Knowledge Surface And Acceptance - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase turns the new compiled-knowledge contract from Phase `138` into a
more operator-visible and acceptance-backed surface.

The phase owns:

- integrating the compiled-knowledge report into the user/runtime-facing docs
- adding one dedicated bounded acceptance script for the compiled-knowledge
  surface rather than relying only on CLI E2E coverage
- tightening the report wording and navigation so operators can inspect what
  changed without reading raw JSON only

This phase does **not** close the entire milestone. The final closure and
regression audit still belongs to Phase `140`.

</domain>

<decisions>
## Implementation Decisions

- **D-01:** Reuse the new `compile-l2-knowledge-report` command from Phase
  `138`; do not create a second overlapping compiled-knowledge entrypoint.
- **D-02:** Add one isolated acceptance script under
  `research/knowledge-hub/runtime/scripts/` so the surface has a dedicated
  bounded proof path.
- **D-03:** Operator-facing docs should keep the compiled surface explicitly
  non-authoritative and staging-aware.

</decisions>

<canonical_refs>
## Canonical References

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/phases/138-knowledge-compilation-contract/138-CONTEXT.md`
- `.planning/phases/138-knowledge-compilation-contract/138-01-SUMMARY.md`
- `research/knowledge-hub/knowledge_hub/l2_compiler.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`
- `research/knowledge-hub/runtime/README.md`
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md`
- `research/knowledge-hub/README.md`

</canonical_refs>

<code_context>
## Existing Code Insights

- The production compiler command and payload now exist.
- The missing closure slice is dedicated acceptance visibility plus more direct
  operator discoverability.
- Existing L2 docs already mention map/report/hygiene surfaces, so this phase
  should extend that same cluster rather than creating a separate docs section.

</code_context>

<deferred>
## Deferred Ideas

- closure audit and milestone completion
- background rebuild hooks
- multi-user compiled-memory sync

</deferred>

---

*Phase: 139-compiled-knowledge-surface-and-acceptance*
*Context gathered: 2026-04-11*
