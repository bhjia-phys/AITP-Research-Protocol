# Phase 59: Lightweight L2 Entry And Seed Command Family - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `58`

<domain>
## Phase Boundary

Expose the bounded MVP `L2` graph and consult capabilities through real service
and CLI entrypoints instead of leaving them as helper-only code.

This phase is about production reachability:

- bounded graph seeding
- bounded `L2` consultation/retrieval
- reuse of the already-existing lightweight staging surface

This phase is not about broad graph maturity or ranking sophistication.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse the already-existing helper implementations in `l2_graph.py` instead of
  creating a second graph API path.
- Keep command names explicit and bounded rather than overloading generic
  topic/runtime commands.
- Treat `stage-l2-provisional` as the existing lightweight staging surface;
  this phase mainly needs service/CLI surfaces for seeding and consultation.
- Close only with at least one subprocess/CLI-backed proof, not only mocked
  dispatch tests.

### the agent's Discretion

- Exact CLI flag names for query text and limits, as long as the surface is
  explicit and testable.
- Whether to expose the new capability through direct service wrappers only or
  with a small extracted command helper if needed.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/l2_graph.py` - current bounded seed and
  consult implementation
- `research/knowledge-hub/knowledge_hub/l2_staging.py` - existing lightweight
  staging production surface
- `research/knowledge-hub/knowledge_hub/aitp_service.py` - public service facade
- `research/knowledge-hub/knowledge_hub/aitp_cli.py` - public CLI surface
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- `stage-l2-provisional` is already a production CLI entrypoint
- `seed_l2_demo_direction(...)` and `consult_canonical_l2(...)` exist only in
  `l2_graph.py`
- there is currently no public service wrapper or CLI command for bounded MVP
  graph seeding or consultation

</code_context>

<specifics>
## Specific Ideas

- Add `AITPService.seed_l2_direction(...)`
- Add `AITPService.consult_l2(...)`
- Add CLI commands:
  - `aitp seed-l2-direction`
  - `aitp consult-l2`
- Add one CLI E2E proof that seeds the TFIM MVP direction and retrieves the new
  `physical_picture` through the CLI path

</specifics>

<deferred>
## Deferred Ideas

- richer ranking/reranking policy
- topic-aware `L2` consultation receipts
- graph rebuild / cache invalidation automation

</deferred>

---

*Phase: 59-lightweight-l2-entry-and-seed-command-family*
*Context gathered: 2026-04-11 after Phase 58 MVP-family activation*
