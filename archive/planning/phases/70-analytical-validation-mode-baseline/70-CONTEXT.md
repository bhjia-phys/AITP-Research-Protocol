# Phase 70: Analytical Validation Mode Baseline - Context

**Gathered:** 2026-04-11
**Status:** Implemented and verified
**Mode:** New milestone opener after closing `v1.46`

<domain>
## Phase Boundary

Make analytical validation a real production mode:

- `verify --mode analytical`
- service-side preparation for analytical validation
- theory-synthesis topics defaulting to `analytical` instead of generic
  `hybrid`

This phase is about validation-mode legitimacy.
It is not yet about durable analytical review artifacts.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Analytical validation must go through the existing `prepare_verification`
  service and `verify` CLI entrypoint.
- `theory_synthesis` should map to `analytical` validation by default.
- Keep the phase focused on mode semantics, not on adding new review artifact
  families yet.

### the agent's Discretion

- Exact analytical required-check wording.
- Whether analytical mode should appear only for theory-synthesis or remain
  manually available for any topic.

</decisions>

<canonical_refs>
## Canonical References

- `research/knowledge-hub/knowledge_hub/semantic_routing.py`
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/knowledge_hub/topic_shell_support.py`
- `research/knowledge-hub/knowledge_hub/aitp_cli.py`
- `research/knowledge-hub/tests/test_semantic_routing.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli.py`

</canonical_refs>

<code_context>
## Existing Code Insights

- Verification modes already existed for `proof`, `comparison`, `numeric`, and
  `topic-completion`, so the cleanest first step was to add `analytical`
  through the same production path.
- `theory_synthesis` still defaulted to `hybrid`, which blurred analytical
  theory work with generic mixed review.

</code_context>

<specifics>
## Specific Ideas

- Extend `verify --mode` choices with `analytical`.
- Add analytical required checks around limiting cases, dimensional
  consistency, symmetry, and source-backed consistency.
- Route `theory_synthesis` to `analytical` in semantic validation defaults.

</specifics>

<deferred>
## Deferred Ideas

- analytical review artifact family
- research-judgment decision signals
- milestone-close acceptance packaging

</deferred>

---

*Phase: 70-analytical-validation-mode-baseline*
*Context captured on 2026-04-11 after Phase 70 implementation and verification*
