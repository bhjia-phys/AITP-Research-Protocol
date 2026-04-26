# Phase 138: Knowledge Compilation Contract - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase defines the first bounded production contract for backlog `999.37`
inside `v1.68`.

The phase owns:

- locking one explicit compiled-knowledge contract that goes beyond the already
  shipped `compile-l2-map` and `compile-l2-graph-report` helper surfaces
- defining what counts as "added", "updated", "contradicted", and
  "still-provisional" knowledge in a bounded workspace compilation
- preserving the existing `L4` and canonical-promotion boundary so the new
  compilation surface does not masquerade as authoritative `L2`

This phase does **not** yet need to implement the full runtime materialization
surface. It should first lock the contract and regression expectations.

</domain>

<decisions>
## Implementation Decisions

### Scope
- **D-01:** Build on the existing `l2_compiler.py` surfaces instead of creating
  a disconnected knowledge-memory subsystem.
- **D-02:** Treat the new compilation surface as non-authoritative and
  explicitly mixed-provenance: canonical, staged, and provisional inputs may
  appear together, but their provenance must stay visible.
- **D-03:** Keep the first slice workspace-wide and bounded; do not require a
  cross-user or cross-machine sync layer.

### Contract Shape
- **D-04:** The contract should include:
  - compiled summary
  - new-or-updated knowledge rows
  - contradiction/provisional rows
  - linked navigation entrypoints
  - provenance tier per compiled row
- **D-05:** The contract should capture change-over-time via a bounded update
  summary rather than trying to solve full historical versioning in the first
  slice.
- **D-06:** The contract should be test-first and operator-visible before the
  runtime CLI surface is broadened.

### the agent's Discretion
- Exact artifact names and JSON field names may evolve if they stay explicit,
  non-authoritative, and easy to inspect.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/MILESTONE-CONTEXT.md`
- `.planning/BACKLOG.md` (`999.37`)
- `research/knowledge-hub/knowledge_hub/l2_compiler.py`
- `research/knowledge-hub/knowledge_hub/cli_l2_compiler_handler.py`
- `research/knowledge-hub/tests/test_l2_backend_contracts.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`
- `research/knowledge-hub/canonical/L2_COMPILER_PROTOCOL.md`
- `research/knowledge-hub/canonical/L2_STAGING_PROTOCOL.md`

</canonical_refs>

<code_context>
## Existing Code Insights

- `compile-l2-map` already materializes a workspace memory map over canonical
  units and relation summaries.
- `compile-l2-graph-report` already materializes a human-facing graph report
  and derived navigation pages.
- The obvious missing surface is a compiled-knowledge report that answers:
  what changed, what remains provisional, and where contradictions or
  unresolved updates still sit.
- Existing tests already protect the map/report CLI entrypoints, so the new
  contract should integrate with that same compiler family.

</code_context>

<specifics>
## Specific Ideas

- Use existing canonical + staging + provisional workspace artifacts as the
  first input family instead of inventing a new ingestion source.
- Keep "what changed" bounded to the current and previous compiled snapshot for
  the first slice.
- Make provenance and authority level explicit per row.

</specifics>

<deferred>
## Deferred Ideas

- full historical diff/version tracking
- automatic background rebuild hooks
- multi-user compiled-knowledge sync

</deferred>

---

*Phase: 138-knowledge-compilation-contract*
*Context gathered: 2026-04-11*
