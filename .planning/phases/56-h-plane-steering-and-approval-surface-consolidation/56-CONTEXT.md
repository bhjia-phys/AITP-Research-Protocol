# Phase 56: H-Plane Steering And Approval Surface Consolidation - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `55`

<domain>
## Phase Boundary

Consolidate the existing human-interaction artifacts into one explicit
production `H-plane` surface so redirect, pause, approve, and override no
longer live as scattered notes and specialized commands only.

This phase is about unification and projection:

- steering note / redirect state
- operator checkpoint state
- pause/focus registry state
- promotion approval state
- one unified service/runtime/CLI entrypoint

This phase is not about inventing new human-interaction mechanisms from
scratch.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Reuse the existing durable artifacts:
  - `control_note.md`
  - `innovation_direction.md`
  - `innovation_decisions.jsonl`
  - `operator_checkpoint.active.{json,md}`
  - `active_topics.json`
  - `promotion_gate.{json,md}`
- Add one explicit `h_plane` production payload instead of asking operators to
  reconstruct state from those files manually.
- Keep the `H-plane` distinct from the general control plane:
  - control plane = task/lane/layer/mode/transition truth
  - `H-plane` = human steering/approval/intervention truth
- Prefer read/audit exposure first. Do not replace the existing write paths in
  this phase.

### the agent's Discretion

- Whether the `H-plane` helper lives in a dedicated module or is composed from
  smaller extracted helpers, as long as the existing facades stay thin.
- Exact field names of the `h_plane` payload, as long as redirect, pause,
  approve, and override semantics remain explicit and testable.

</decisions>

<canonical_refs>
## Canonical References

### Architecture
- `docs/V142_ARCHITECTURE_VISION.md` - names the `H-plane` explicitly as the
  human interaction layer.
- `docs/AITP_UNIFIED_RESEARCH_ARCHITECTURE.md` - defines `H-plane` as distinct
  from layer/lane/mode.

### Existing artifacts and write paths
- `research/knowledge-hub/knowledge_hub/aitp_service.py` - steering,
  checkpoint, pause/resume, and promotion approval entrypoints.
- `research/knowledge-hub/knowledge_hub/kernel_markdown_renderers.py` -
  control-note and operator-checkpoint rendering.
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` - current
  runtime bundle projection.
- `research/knowledge-hub/knowledge_hub/capability_audit_support.py` - current
  audit/doctor surface.

</canonical_refs>

<code_context>
## Existing Code Insights

- redirect steering already writes `control_note.md`, `innovation_direction.md`,
  and `innovation_decisions.jsonl`
- pause/resume/focus already persist through `active_topics.json`
- approval already persists through `promotion_gate.json`
- operator checkpoints already exist, but the operator still has to know which
  artifact to open first

</code_context>

<specifics>
## Specific Ideas

- Add a production `h_plane` payload with bounded sections:
  - `steering`
  - `checkpoint`
  - `registry`
  - `approval`
- Add `AITPService.h_plane_audit(...)`
- Add `aitp h-plane-audit`
- Expose the same `h_plane` payload through runtime bundle and capability audit

</specifics>

<deferred>
## Deferred Ideas

- new interactive steering UX beyond the existing durable artifacts
- cross-runtime H-plane parity and docs closeout

</deferred>

---

*Phase: 56-h-plane-steering-and-approval-surface-consolidation*
*Context gathered: 2026-04-11 via milestone synthesis and current runtime artifacts*
