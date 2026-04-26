# Phase 66: Global Source Catalog And Cross-Topic Dedup - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** New milestone opener after closing `v1.45`

<domain>
## Phase Boundary

Add the first real global Layer 0 compilation surface:

- compile a deduplicated source catalog across topic-local `source_index.jsonl`
- surface cross-topic source reuse as a durable artifact
- make that catalog reachable through production service and CLI entrypoints

This phase is about global source identity visibility.
It is not yet about bounded citation traversal or fidelity ranking.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Keep the new source catalog under `source-layer/compiled/`.
- Derive the catalog from topic-local `source_index.jsonl` files rather than
  trying to treat `global_index.jsonl` as the richer source-of-truth.
- Expose the new behavior through an extracted command-family handler instead
  of adding another inline branch to `aitp_cli.py`.

### the agent's Discretion

- Exact source-catalog summary fields and markdown layout.
- How much linked-reference information to surface in the first catalog slice.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/source-layer/README.md`
- `research/knowledge-hub/L0_SOURCE_LAYER.md`
- `research/knowledge-hub/knowledge_hub/source_intelligence.py`
- `research/knowledge-hub/tests/test_source_catalog.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Topic-local source intelligence already exposes `canonical_source_id`,
  references, and cross-topic neighbor signals, but there was no durable global
  catalog view across topics.
- `source-layer/global_index.jsonl` exists, but it is too thin to serve as the
  richer compiled source catalog on its own.
- The right first step was therefore a compiled catalog over topic-local source
  indexes, not another runtime note.

</code_context>

<specifics>
## Specific Ideas

- Materialize `source-layer/compiled/source_catalog.json|md`.
- Group topic-local source rows by `canonical_source_id`.
- Surface cross-topic reuse counts and linked references between cataloged
  sources.

</specifics>

<deferred>
## Deferred Ideas

- bounded citation traversal commands
- source-family reuse navigation
- fidelity-aware ranking in runtime status/read surfaces

</deferred>

---

*Phase: 66-global-source-catalog-and-cross-topic-dedup*
*Context captured on 2026-04-11 after Phase 66 implementation and verification*
