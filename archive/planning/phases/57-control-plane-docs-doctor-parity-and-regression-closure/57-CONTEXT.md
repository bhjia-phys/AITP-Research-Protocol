# Phase 57: Control-Plane Docs, Doctor Parity, And Regression Closure - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning
**Mode:** Brownfield continuation after closing Phase `56`

<domain>
## Phase Boundary

Close `v1.43` by making the new control-plane, `H-plane`, and paired-backend
surfaces resumable and auditable from the same places operators already use:

- `aitp doctor --json`
- README / install docs
- one real-topic verification flow

This phase is not about inventing another control-plane helper or adding new
ontology. The contract is already present from Phases `54-56`; this phase
closes parity and proof.

</domain>

<decisions>
## Implementation Decisions

### Locked decisions

- `doctor` must expose the control-plane governance surface explicitly rather
  than forcing operators to infer it from scattered docs and CLI help.
- The public docs must name the new audit entrypoints directly:
  - `aitp capability-audit`
  - `aitp paired-backend-audit`
  - `aitp h-plane-audit`
- Milestone closeout must include at least one non-mocked real-topic
  verification path that exercises control-plane and paired-backend behavior
  through production code.
- Reuse the existing real-topic acceptance anchor style instead of inventing a
  synthetic topic or demo prose.

### the agent's Discretion

- Exact field names under the new doctor section, as long as docs/contracts and
  CLI entrypoints are explicit and testable.
- Which public docs are updated, as long as root usage docs and kernel-facing
  docs both reflect the new governance surfaces.
- Whether the real-topic acceptance script calls service methods directly,
  CLI entrypoints directly, or both, as long as the proof is non-mocked and
  durable.

</decisions>

<canonical_refs>
## Canonical References

### Milestone contract
- `.planning/ROADMAP.md` - defines Phase `57` as docs + doctor parity +
  regression closure.
- `.planning/REQUIREMENTS.md` - active requirements for `REQ-CTRL-01`,
  `REQ-CTRL-02`, `REQ-BACKEND-01`, `REQ-BACKEND-02`, `REQ-HPLANE-02`, and
  `REQ-VERIFY-01`.

### Production surfaces
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` - `doctor`
  payload assembly.
- `research/knowledge-hub/knowledge_hub/aitp_service.py` - service facade for
  `ensure_cli_installed`, `topic_status`, `capability_audit`,
  `paired_backend_audit`, and `h_plane_audit`.
- `research/knowledge-hub/knowledge_hub/aitp_cli.py` - public CLI command
  exposure and dispatch.

### Architecture and governance docs
- `docs/AITP_UNIFIED_RESEARCH_ARCHITECTURE.md` - unified architecture contract.
- `docs/V142_ARCHITECTURE_VISION.md` - control-plane / `H-plane` reference
  vision.
- `research/knowledge-hub/canonical/backends/THEORETICAL_PHYSICS_PAIRED_BACKEND_CONTRACT.md`
  - paired-backend contract anchor.
- `research/knowledge-hub/README.md` - kernel-facing public command and
  maintainability docs.
- `README.md` - top-level public usage and support matrix.
- `docs/INSTALL_CODEX.md`, `docs/INSTALL_CLAUDE_CODE.md`,
  `docs/INSTALL_OPENCODE.md` - runtime-install and doctor-facing docs.

### Existing acceptance anchors
- `research/knowledge-hub/runtime/scripts/run_scrpa_thesis_topic_acceptance.py`
  - real-topic formal-theory acceptance anchor.
- `research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py`
  - real-topic code-method acceptance pattern.

</canonical_refs>

<code_context>
## Existing Code Insights

- `doctor` already reports layer roots, protocol contracts, and runtime support
  matrix, but it does not yet expose the newly landed control-plane governance
  docs or audit commands as one bounded operator surface.
- Root and kernel READMEs mention `aitp doctor --json`, but they do not yet
  enumerate the paired-backend or `H-plane` audit commands in the main command
  path.
- The repo already has real-topic acceptance patterns that discover real
  sources or workspaces and then verify durable artifacts, so Phase `57`
  should extend that style instead of inventing mock-only tests.

</code_context>

<specifics>
## Specific Ideas

- Add a `control_plane_contracts` and/or `control_plane_surfaces` section to
  the `doctor` JSON payload.
- Update README and kernel README command lists to include the new audit
  entrypoints and note that `doctor --json` exposes control-plane governance.
- Add one real-topic acceptance script using the scRPA thesis anchor to
  materialize steering plus paired-backend audit artifacts and prove the CLI
  entrypoints on a non-mocked topic.

</specifics>

<deferred>
## Deferred Ideas

- automatic paired-backend rebuild or repair
- cross-runtime auto-replay of control-plane audits
- new human-interaction mechanisms beyond the current `H-plane` surfaces

</deferred>

---

*Phase: 57-control-plane-docs-doctor-parity-and-regression-closure*
*Context gathered: 2026-04-11 via Phase 54-56 follow-through and current public docs*
