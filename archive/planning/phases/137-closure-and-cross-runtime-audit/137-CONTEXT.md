# Phase 137: Closure And Cross-Runtime Audit - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase closes `v1.67` with one shared parity audit/report surface and the
targeted verification evidence that ties together the Codex baseline plus the
bounded Claude Code and OpenCode probes.

The phase owns:

- one shared closure report that runs across Codex, Claude Code, and OpenCode
- one explicit summary of equivalent surfaces, degraded surfaces, and still-open
  gaps
- one final verification slice for the milestone requirements
- updating planning state so the milestone can move to milestone-completion
  workflow

This phase does **not** need to turn Claude Code or OpenCode into
`parity_verified`. The milestone can close with open gaps as long as the report
names them honestly.

</domain>

<decisions>
## Implementation Decisions

### Audit Surface
- **D-01:** Add one dedicated cross-runtime audit/report script rather than
  overloading the single-runtime acceptance command with aggregate-only output.
- **D-02:** The audit should reuse the existing bounded runtime probes rather
  than reimplementing their logic.
- **D-03:** The audit must remain operator-readable JSON and should be easy to
  point to from docs and milestone closure notes.

### Closure Semantics
- **D-04:** Treat "closure" here as "bounded parity state is now honestly
  measured and summarized," not as "all runtimes are fully equivalent."
- **D-05:** Keep Codex as the baseline runtime and describe Claude/OpenCode in
  terms of what matches Codex versus what still remains indirect.

### Verification
- **D-06:** Targeted verification should rerun the service/doc slices plus the
  new closure audit/report surface.
- **D-07:** If the closure audit shows remaining live-app gaps for Claude or
  OpenCode, record them as closure findings rather than blocking the audit from
  landing.

### the agent's Discretion
- Exact report field names may evolve if the closure report stays explicit and
  easy to compare.
- The audit may include nested raw runtime reports as supporting evidence.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope
- `.planning/REQUIREMENTS.md` — active requirement mapping for `REQ-VERIFY-01`.
- `.planning/ROADMAP.md` — phase ordering for `v1.67`.
- `.planning/MILESTONE-CONTEXT.md` — why the milestone is closing now.
- `.planning/phases/134-runtime-parity-contract-and-shared-acceptance-harness/134-CONTEXT.md`
  — shared parity contract vocabulary.
- `.planning/phases/135-claude-code-deep-execution-probe/135-CONTEXT.md` —
  Claude-specific parity probe context.
- `.planning/phases/136-opencode-deep-execution-probe/136-CONTEXT.md` —
  OpenCode-specific parity probe context.

### Shared Runtime Probe Surfaces
- `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py` —
  single-runtime parity harness.
- `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py` — doctor
  truth surface for deep-execution parity.
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` — top-level
  doctor parity summary.

### Runtime Docs
- `research/knowledge-hub/runtime/README.md` — runtime acceptance catalog.
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md` — operator-facing
  acceptance runbook.
- `README.md` — public runtime support framing.

### Regression Coverage
- `research/knowledge-hub/tests/test_aitp_service.py` — runtime truth surface
  contracts.
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py` — doc contract
  coverage.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_runtime_parity_acceptance.py` already provides three bounded runtime
  evidence payloads: one baseline and two gap-aware probes.
- `deep_execution_parity_summary()` already gives the compact doctor-facing
  top-level status.
- The docs already explain the single-runtime commands; the closure phase only
  needs to add the aggregate audit surface.

### Established Patterns
- Acceptance scripts should emit one JSON payload that can serve as durable
  operator evidence.
- Planning closure should point to real verification commands and should not
  claim more than the evidence supports.

### Integration Points
- The new closure report should consume the existing runtime probes and avoid
  creating contradictory parity vocabulary.
- The final audit should update planning state so the next step becomes
  milestone completion rather than another runtime probe.

</code_context>

<specifics>
## Specific Ideas

- The closure report should say that Claude Code and OpenCode now both match
  Codex on bounded AITP runtime artifacts, while both still fall short on the
  live-app first-turn bootstrap proof.
- That is exactly the kind of honest outcome the user asked for: consistency,
  without pretending the remaining live-runtime gap does not exist.

</specifics>

<deferred>
## Deferred Ideas

- a future milestone that tries to prove live-app parity more directly
- OpenClaw parity

</deferred>

---

*Phase: 137-closure-and-cross-runtime-audit*
*Context gathered: 2026-04-11*
