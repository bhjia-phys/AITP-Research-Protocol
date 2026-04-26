# Phase 63: Consultation Context And Artifact Maturity - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Brownfield continuation after closing Phase `62`

<domain>
## Phase Boundary

Turn bounded `consult-l2` retrieval into a real consultation protocol surface:

- durable request/result/application artifacts
- stage-aware consultation projection logs
- CLI/runtime inputs that preserve consultation context instead of dropping it

This phase is about reviewable consultation context.
It is not about adding new graph-report UIs yet.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse the existing `_record_l2_consultation(...)` protocol writer instead of
  inventing a second artifact format.
- Extend the public `consult-l2` CLI to accept topic/stage/run context and an
  explicit `--record-consultation` switch.
- Keep `aitp_service.py` within watch budget by extracting consultation-record
  assembly into a dedicated support module.

### the agent's Discretion

- Exact result-summary wording inside consultation artifacts.
- Whether recorded consultation defaults should narrow the primary-hit window to
  keep traversal context reviewable.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/cli_l2_graph_handler.py`
- `research/knowledge-hub/knowledge_hub/l2_consultation_support.py`
- `research/knowledge-hub/consultation/schemas/consult-request.schema.json`
- `research/knowledge-hub/consultation/schemas/consult-result.schema.json`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`
- `research/knowledge-hub/tests/test_schema_contracts.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Phase `62` already exposed bounded traversal metadata in in-memory consult
  results, but that context was not written into durable consultation protocol
  artifacts.
- The service already had `_record_l2_consultation(...)`, so the missing work
  was call-site maturity, not schema invention.
- The maintainability watch budget on `aitp_service.py` remained a hard guard,
  so new assembly logic had to move into a helper module.

</code_context>

<specifics>
## Specific Ideas

- Add red tests for schema, service, CLI, and CLI E2E artifact recording.
- Extend `consult-result.schema.json` with traversal and retrieval-summary
  fields and align consult-request unit enums with `physical_picture`.
- Record consultation artifacts from `AITPService.consult_l2(...)` when the
  caller opts in with explicit topic/stage/run context.

</specifics>

<deferred>
## Deferred Ideas

- Human-facing graph reports and derived navigation surfaces.
- Broader consultation docs parity and milestone-close acceptance packaging.

</deferred>

---

*Phase: 63-consultation-context-and-artifact-maturity*
*Context captured on 2026-04-11 after Phase 63 implementation and verification*
