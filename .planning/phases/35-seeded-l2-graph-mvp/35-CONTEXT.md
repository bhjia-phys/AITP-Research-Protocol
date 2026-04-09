# Phase 35: Seeded L2 Graph MVP - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning
**Mode:** Brownfield continuation after Phase `34` runtime/schema closure

<domain>
## Phase Boundary

Turn the existing seeded `L2` graph code from a partly hidden demo surface into
an honest runtime-visible memory substrate that AITP can actually build on.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Do not pretend Phase `35` is “seed the first graph from scratch” because the
  TFIM seed, graph files, and consultation code already exist in the repo.
- Treat the real gap as activation honesty: runtime and operator surfaces still
  do not clearly say whether canonical `L2` has any substantive graph content.
- Keep collaborator memory separate from canonical graph state.

### Agent discretion

- The first bounded Phase `35` slice may focus on graph activation status and
  counts rather than on richer retrieval semantics if that gives AITP a more
  honest read path immediately.

</decisions>

<code_context>
## Existing Code Insights

- `research/knowledge-hub/knowledge_hub/l2_graph.py` already contains:
  - `seed_l2_demo_direction`
  - `consult_canonical_l2`
  - `stage_l2_insight`
- `research/knowledge-hub/canonical/index.jsonl` and `edges.jsonl` are already
  populated with the TFIM benchmark-first seed.
- `research/knowledge-hub/knowledge_hub/aitp_service.py` already surfaces
  consultation and writeback counts in `l2_memory`, but not graph activation
  status.
- `research/knowledge-hub/tests/test_l2_graph_activation.py` already locks the
  TFIM seed behavior.

</code_context>

<specifics>
## Specific Ideas

- Add a canonical graph activation surface to runtime `l2_memory`.
- Surface at least:
  - index path
  - edge path
  - unit count
  - edge count
  - available unit types
  - activation status/summary
- Keep the operator-readable `l2_memory.md` honest about whether AITP is
  consulting a real graph or mostly an empty shell.

</specifics>

<canonical_refs>
## Canonical References

- `docs/superpowers/specs/2026-04-08-l2-governance-plane-consolidation-design.md`
- `docs/superpowers/specs/2026-04-07-aitp-collaborator-rectification-and-interaction-design.md`
- `research/knowledge-hub/tests/test_l2_graph_activation.py`

</canonical_refs>

<deferred>
## Deferred Ideas

- Richer consultation expansion and human-facing memory-map pages belong to
  Phase `36`.
- Soft exploration and `H-plane` continue/update/stop policy belong to Phase
  `37`.

</deferred>
