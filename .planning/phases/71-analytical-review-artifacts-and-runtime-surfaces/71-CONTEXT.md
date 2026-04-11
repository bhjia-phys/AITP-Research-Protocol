# Phase 71: Analytical Review Artifacts And Runtime Surfaces - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** Phase 71 after closing `Phase 70`

<domain>
## Phase Boundary

Make analytical validation leave durable and reviewable evidence:

- add a production `analytical-review` audit entrypoint
- materialize `analytical_review.json` inside theory packets
- surface analytical review artifacts through runtime review bundles
- keep service and CLI hotspot growth bounded through extracted helpers

This phase is about durable analytical review evidence.
It is not yet about research-judgment signals.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- The new analytical review flow must go through production service and CLI
  entrypoints, not only tests or docs.
- Durable analytical review artifacts must live in theory-packet storage
  beside other candidate review artifacts.
- Runtime-facing read surfaces should come through the active validation review
  bundle instead of inventing a second parallel dashboard family.

### the agent's Discretion

- Exact analytical check payload shape.
- Whether analytical review should become the primary review kind only in
  analytical mode or also whenever the artifact exists.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/analytical_review_support.py`
- `research/knowledge-hub/knowledge_hub/validation_review_service.py`
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/aitp_cli.py`
- `research/knowledge-hub/knowledge_hub/cli_review_handler.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- `formal-theory-audit` already proved the right pattern: helper-owned durable
  artifact creation with thin service and CLI dispatch.
- `validation_review_bundle.active.json/.md` was already the right runtime read
  surface, so Phase 71 only needed to teach that bundle about
  `analytical_review`.
- Maintainability budgets were tight enough that the review command family had
  to be extracted out of `aitp_cli.py`.

</code_context>

<specifics>
## Specific Ideas

- Add `analytical_review` to theory-packet path generation.
- Record source anchors, assumption/regime context, reading depth, and named
  analytical checks in `analytical_review.json`.
- Make analytical mode prefer `analytical_review` as the primary review bundle
  kind when present.
- Prove the flow through a real CLI e2e test that writes the artifact and then
  re-materializes the runtime bundle.

</specifics>

<deferred>
## Deferred Ideas

- momentum / stuckness / surprise decision signals
- judgment-signal durability ledgers
- milestone-close docs and acceptance packaging

</deferred>

---

*Phase: 71-analytical-review-artifacts-and-runtime-surfaces*
*Context captured on 2026-04-11 after Phase 71 implementation and verification*
