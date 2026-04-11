# Phase 54: Control-Plane Ontology Freeze And Runtime Contracts - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing `v1.42`

<domain>
## Phase Boundary

Freeze the first explicit control-plane contract for AITP by making
`task_type`, `lane`, `layer`, `mode`, and `H-plane` distinct, inspectable, and
runtime-visible through production surfaces.

This phase is about the control-plane truth model and its runtime/service/CLI
projection.
It is not yet the paired-backend drift audit itself, and it is not a broad
docs-only architecture rewrite.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- Treat `task_type`, `lane`, `layer`, `mode`, and `H-plane` as orthogonal axes.
  Do not collapse them into one mixed routing blob.
- Start from read/audit surfaces first:
  runtime bundle, topic status, doctor/capability audit, and CLI-visible
  summaries.
- Prefer adding one explicit production `control_plane` payload over scattering
  more semantics across markdown prose.
- Keep paired-backend alignment and drift semantics for Phase `55`; this phase
  only needs the control-plane contract to expose where backend-governance
  hooks belong.
- Preserve the current runtime shell and progressive-disclosure model; extend
  it rather than replacing it.

### the agent's Discretion

- Whether the control-plane builder lives in a new helper module or in an
  existing extracted helper, as long as `aitp_service.py` remains thin.
- Exact field names inside the `control_plane` payload, provided they remain
  explicit and testable.
- Whether CLI exposure lands as JSON-only for this phase or also gets a
  human-readable render, as long as the runtime and audit surfaces are honest.

</decisions>

<canonical_refs>
## Canonical References

**Downstream planning and implementation must read these first.**

### Architecture and ontology
- `docs/V142_ARCHITECTURE_VISION.md` - target architecture after the archived
  `v1.42` chain; names the `H-plane` and control-plane responsibilities.
- `docs/AITP_UNIFIED_RESEARCH_ARCHITECTURE.md` - defines the six orthogonal
  axes and the separation between research plane, `L2` governance plane, and
  downstream realizations.
- `docs/AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md` - keeps lane/layer/mode
  semantics distinct.

### Backend governance
- `research/knowledge-hub/canonical/backends/THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md`
  - paired-backend role separation and drift doctrine.
- `research/knowledge-hub/canonical/backends/theoretical-physics-knowledge-network.json`
  - existing backend card and retrieval/promotion hints.

### Current runtime and audit surfaces
- `research/knowledge-hub/runtime/README.md` - current runtime shell contract.
- `research/knowledge-hub/knowledge_hub/runtime_bundle_support.py` - current
  progressive-disclosure bundle assembly.
- `research/knowledge-hub/knowledge_hub/capability_audit_support.py` - current
  doctor/capability audit surface.
- `research/knowledge-hub/knowledge_hub/aitp_service.py` - service facade and
  status/capability entrypoints.
- `research/knowledge-hub/knowledge_hub/aitp_cli.py` - CLI command exposure.

</canonical_refs>

<code_context>
## Existing Code Insights

- Runtime already exposes many control-adjacent fragments:
  `runtime_mode`, `transition_posture`, operator checkpoints, promotion gates,
  and lane-specific projections.
- Capability audit currently reports runtime/layer/integration sections, but it
  does not yet surface one first-class control-plane section.
- The architecture docs now over-specify the intended control plane relative to
  what runtime/service/CLI surfaces make directly inspectable.

</code_context>

<specifics>
## Specific Ideas

- Add one production `control_plane` payload to the runtime bundle and re-use
  that payload in status and capability-audit surfaces.
- The payload should at minimum answer:
  - current `task_type`
  - current `lane`
  - current epistemic `layer` / resume stage
  - current `mode`
  - current transition posture / backedge posture
  - current `H-plane` state:
    checkpoint, approval, pause, redirect, or override posture
- Capability audit should gain a `control_plane` section so doctor-like
  inspection can tell whether the runtime shell is control-plane-complete.

</specifics>

<deferred>
## Deferred Ideas

- Explicit paired-backend alignment and drift ledgers
- One-shot sync/repair command families for paired backends
- Full docs/doctor parity closeout and broader regression closure

</deferred>

---

*Phase: 54-control-plane-ontology-freeze-and-runtime-contracts*
*Context gathered: 2026-04-11 via milestone synthesis and architecture docs*
