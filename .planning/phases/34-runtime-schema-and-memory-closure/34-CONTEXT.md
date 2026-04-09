# Phase 34: Runtime Schema And Memory Closure - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation from the active worktree after the `v1.33`
closure slice

<domain>
## Phase Boundary

Close the live runtime/schema mismatch around collaborator memory and make the
runtime read path honest again before broader `L2` memory activation work
continues.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- `collaborator_memory` remains noncanonical steering context, not canonical
  `L2` truth.
- The fix must restore schema closure rather than backing out the new runtime
  field.
- Phase `34` is a repair-and-closure slice, not the seeded graph phase.

### Agent discretion

- The exact presentation details in runtime markdown may be tightened if they
  improve readability without changing trust semantics.

</decisions>

<code_context>
## Existing Code Insights

- `research/knowledge-hub/knowledge_hub/aitp_service.py` already derives and
  emits collaborator-memory summaries into the runtime bundle.
- `research/knowledge-hub/runtime/schemas/progressive-disclosure-runtime-bundle.schema.json`
  contains a `$defs.collaborator_memory` block and lists the field in
  `required`, but the top-level `properties` map is not yet wired.
- The failing tests are runtime/schema closure tests, not CLI smoke tests.

</code_context>

<specifics>
## Specific Ideas

- Restore runtime/schema agreement first.
- Keep collaborator memory visible at session start so future decision/routing
  work can build on it.
- Re-run the targeted runtime/schema suite and then the integrated regression
  bundle used at the previous closure point.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `docs/superpowers/specs/2026-04-07-aitp-collaborator-rectification-and-interaction-design.md`
- `docs/superpowers/specs/2026-04-09-aitp-soft-exploration-hard-trust-runtime-design.md`

</canonical_refs>

<deferred>
## Deferred Ideas

- Seeded `L2` graph activation belongs to Phase `35`.
- Human-facing graph maps and `H-plane` timing policy belong to later phases.

</deferred>
