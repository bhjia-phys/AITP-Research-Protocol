# Phase 168: Analytical Check Rows And Review Contract Expansion - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase upgrades the existing `analytical_review` artifact from a
review-level aggregate with thin check rows into an explicit bounded
check-row contract. It covers CLI/service input shape, review-artifact
normalization, durable theory-packet payloads, and the compatibility
projections needed to keep the current analytical-review path working.

It does not yet widen into runtime/read-path rendering changes or the new
bounded analytical proof lane; those belong to Phase `168.1`.

</domain>

<decisions>
## Implementation Decisions

### Review-contract boundary
- **D-01:** Build on the existing `analytical_review` artifact family and the
  public `analytical-review` CLI/service entrypoint instead of inventing a
  separate analytical cross-check subsystem.
- **D-02:** Keep the durable artifact at `analytical_review.json` inside
  theory-packet storage and keep `validation_review_bundle` as the current
  integration point. Phase `168` enriches the artifact contract itself, not
  the runtime/read-path surfaces that display it.
- **D-03:** Keep this phase bounded to one candidate review at a time. No
  multi-candidate comparison bundle, route mutation, or symbolic/CAS backend
  work belongs here.

### Check-row semantics
- **D-04:** Analytical checks must become first-class self-contained rows
  inside the existing `checks` array. Each row must carry its own `kind`,
  `label`, `status`, `notes`, exact `source_anchors`, bounded assumption or
  regime context, and reading-depth posture instead of relying only on
  top-level review context.
- **D-05:** Expand the check taxonomy to cover `source_cross_reference`
  alongside existing limiting-case, dimensional-consistency, symmetry, and
  self-consistency checks.
- **D-06:** Keep review-level rollups such as `overall_status`, counts,
  `summary`, and compatibility fields, but treat them as projections from the
  richer row set rather than the only durable source of context.

### Compatibility and scope safety
- **D-07:** Preserve the current `analytical-review` CLI/service call pattern
  in this phase. Existing review-level flags may remain as defaults or
  compatibility inputs, but the stored artifact must materialize row-level
  context for every check.
- **D-08:** Do not widen into runtime/read-path presentation redesign in this
  phase. Minimal compatibility adjustments are allowed only if the current
  validation-review bundle or baseline acceptance path would otherwise regress.
- **D-09:** Keep the current primary-review-bundle behavior working:
  analytical mode should still surface `analytical_review` as the primary
  review kind when present.

### Verification boundary
- **D-10:** Phase `168` should land targeted CLI, service, and e2e coverage
  that locks the richer analytical-check row contract and the compatibility
  path.
- **D-11:** The milestone-close proof lane and richer runtime/read-path
  rendering are explicitly deferred to Phase `168.1`.

### the agent's Discretion
- exact row field names for row-level assumption or regime context
- whether top-level compatibility fields are exact rollups or defaults mirrored
  from rows
- whether CLI compatibility is implemented purely by projecting the current
  review-level flags into each row or by adding optional row-specific overrides
  without breaking the current command

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope and prior closure history
- `.planning/ROADMAP.md` — Phase `168` goal, scope split, and dependency on
  `v1.93`
- `.planning/REQUIREMENTS.md` — `REQ-ANX-01` and `REQ-ANX-02`
- `.planning/milestones/v1.47-ROADMAP.md` — original analytical-validation
  milestone that introduced the current production analytical-review lane
- `.planning/milestones/v1.47-REQUIREMENTS.md` — original analytical-review
  and proof-lane requirements
- `.planning/phases/71-analytical-review-artifacts-and-runtime-surfaces/71-CONTEXT.md`
  — prior design decisions for the existing analytical-review artifact family

### Core implementation surfaces
- `research/knowledge-hub/knowledge_hub/analytical_review_support.py` —
  current analytical-review normalization, blocker logic, rollups, and artifact
  writing
- `research/knowledge-hub/knowledge_hub/cli_review_handler.py` — current
  public CLI parser and dispatch for `analytical-review`
- `research/knowledge-hub/knowledge_hub/validation_review_service.py` —
  current validation-bundle selection logic for `analytical_review`
- `research/knowledge-hub/knowledge_hub/aitp_service.py` — current
  theory-packet paths and analytical validation-mode defaults

### Current contract locks and compatibility guards
- `research/knowledge-hub/tests/test_aitp_service.py` — current durable
  analytical-review artifact and validation-bundle tests
- `research/knowledge-hub/tests/test_aitp_cli.py` — current parser and CLI
  dispatch coverage for `analytical-review`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py` — current production-CLI
  e2e flow for analytical review and primary bundle promotion
- `research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py`
  — existing bounded acceptance lane that must remain compatible through this
  phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `analytical_review_support.py` already owns the allowed check kinds and
  statuses, row normalization, blocker computation, summary generation, and
  candidate-ledger compatibility updates.
- `cli_review_handler.py` already exposes `analytical-review` through the
  public CLI and currently passes review-level source or regime context plus
  thin check rows.
- `validation_review_service.py` and `prepare_verification(...)` already make
  `analytical_review` the primary review kind in analytical mode when present.

### Established Patterns
- Review artifacts live in theory-packet storage as durable JSON written by
  helper-owned support modules with thin service and CLI routing.
- Compatibility is usually preserved by enriching an existing artifact family
  first, then widening runtime/read-path rendering in a follow-on phase.
- There is no separate public JSON schema for `analytical_review` today, so the
  contract is currently locked by focused CLI, service, e2e, and acceptance
  coverage rather than by a standalone schema file.

### Integration Points
- `research/knowledge-hub/knowledge_hub/analytical_review_support.py`
- `research/knowledge-hub/knowledge_hub/cli_review_handler.py`
- `research/knowledge-hub/knowledge_hub/aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_service.py`
- `research/knowledge-hub/tests/test_aitp_cli_e2e.py`
- `research/knowledge-hub/runtime/scripts/run_analytical_judgment_surface_acceptance.py`

</code_context>

<specifics>
## Specific Ideas

- The current gap is not lack of an analytical-review artifact. The gap is
  that `checks` rows are still too thin while `source_anchors`,
  `assumption_refs`, `regime_note`, and `reading_depth` live mostly at the
  top level.
- The narrowest useful outcome is to keep `checks` as the public field name and
  enrich each row, then let top-level counts, summaries, and compatibility
  fields roll up from those rows.
- Analytical validation-mode wording should explicitly mention
  source-cross-reference checks once the new kind exists.

</specifics>

<deferred>
## Deferred Ideas

- new runtime/read-path markdown or JSON surfaces beyond current compatibility
- the milestone-close proof lane or a new acceptance harness
- CAS or symbolic backend work, route mutation, or multi-candidate analytical
  comparison

</deferred>

---

*Phase: 168-analytical-check-rows-and-review-contract-expansion*
*Context gathered: 2026-04-13*
