# Phase 134: Runtime Parity Contract And Shared Acceptance Harness - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase defines the shared contract and baseline acceptance harness for
cross-runtime deep execution parity.

The phase owns:

- distinguishing front-door install readiness from deep-execution readiness
- defining the Codex baseline artifact bar that parity targets must match
- creating one shared parity-harness entrypoint and report shape that later
  Claude Code and OpenCode probes will reuse

This phase does **not** yet own the Claude Code-specific or OpenCode-specific
runtime fixes. Those belong to Phases `135` and `136`.

</domain>

<decisions>
## Implementation Decisions

### Runtime Scope
- **D-01:** Keep Codex as the baseline runtime for deep execution.
- **D-02:** Treat Claude Code and OpenCode as parity targets for this
  milestone.
- **D-03:** Keep OpenClaw visible only as a specialized deferred lane. Do not
  expand this phase into OpenClaw parity.

### Contract Shape
- **D-04:** Do not overload the existing front-door `status` field in
  `runtime_support_matrix` with deep-execution claims. Keep install readiness
  and deep-execution readiness distinct.
- **D-05:** Add a shared deep-execution parity surface that records baseline,
  target runtime, acceptance command, expected artifacts, and parity blockers.
- **D-06:** A green `aitp doctor` row must no longer be interpretable as proof
  of deep-execution parity by itself.

### Acceptance Harness
- **D-07:** Reuse existing bounded real-topic acceptance patterns instead of
  inventing a synthetic parity-only shell.
- **D-08:** The shared harness should verify artifact-level outcomes: topic
  shell continuity, runtime protocol, bounded next action, and any declared
  runtime-specific bootstrap receipts.
- **D-09:** The first runnable proof in this phase should center on the Codex
  baseline and produce a reusable report format for later target-runtime
  probes.

### the agent's Discretion
- The exact command name may evolve, but it must be a dedicated parity-facing
  acceptance/report surface rather than a hidden test helper only.
- The parity report may be nested under `doctor --json` or emitted by a new
  runtime script, as long as the separation between install parity and
  deep-execution parity remains explicit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope
- `.planning/BACKLOG.md` — canonical definition of `999.44` cross-runtime deep
  execution parity.
- `.planning/REQUIREMENTS.md` — active requirement mapping for `v1.67`.
- `.planning/ROADMAP.md` — phase ordering for `v1.67`.
- `.planning/MILESTONE-CONTEXT.md` — why runtime parity was promoted now.

### Existing Runtime Parity Surfaces
- `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py` — current
  Codex baseline vs Claude/OpenCode front-door parity model.
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` — doctor payload
  assembly and top-level runtime convergence summary.
- `research/knowledge-hub/knowledge_hub/cli_compat_handler.py` — human-readable
  doctor output contract.

### Runtime Bootstrap And Acceptance Anchors
- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py` —
  bounded first-run install/use acceptance anchor.
- `research/knowledge-hub/runtime/scripts/run_scrpa_control_plane_acceptance.py`
  — real-topic control-plane acceptance anchor.
- `research/knowledge-hub/runtime/scripts/run_tfim_benchmark_code_method_acceptance.py`
  — code-method acceptance anchor with benchmark-first discipline.
- `research/knowledge-hub/runtime/scripts/run_public_install_smoke.py` —
  isolated installed-runtime smoke harness pattern.

### Adoption-Facing Runtime Docs
- `docs/INSTALL_CODEX.md` — Codex baseline front-door and verify language.
- `docs/INSTALL_CLAUDE_CODE.md` — Claude Code SessionStart bootstrap contract.
- `docs/INSTALL_OPENCODE.md` — OpenCode plugin bootstrap contract.
- `research/knowledge-hub/runtime/README.md` — runtime-side acceptance catalog.
- `research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md` — operator-facing
  acceptance runbook.

### Regression Coverage
- `research/knowledge-hub/tests/test_aitp_service.py` — runtime support matrix
  and doctor payload contracts.
- `research/knowledge-hub/tests/test_aitp_cli.py` — human-readable doctor and
  CLI surface contracts.
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py` — install/doc
  contract coverage across Codex, Claude Code, and OpenCode.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `build_runtime_support_matrix()` already expresses baseline runtime and
  parity targets; extend it rather than creating a second disconnected runtime
  classification tree.
- Existing acceptance scripts already exercise bounded real-topic flows through
  production CLI and temp kernel roots.
- `run_public_install_smoke.py` already proves how to keep an installed runtime
  isolated from the host repo state.

### Established Patterns
- Runtime truth is usually recorded through JSON plus markdown artifact pairs.
- Bounded acceptance scripts live under `research/knowledge-hub/runtime/scripts/`
  and are documented in both the kernel README and the runtime runbook.
- Install-facing docs should remain honest about what is baseline-ready versus
  what is still a parity target.

### Integration Points
- Any new parity surface should align with `runtime_support_matrix` and
  `doctor --json` instead of creating contradictory readiness labels.
- Runtime docs and tests must be updated in the same phase so the parity
  contract is operator-visible immediately.

</code_context>

<specifics>
## Specific Ideas

- The user priority that drove `v1.65` and `v1.66` was consistency across
  Codex, Claude Code, and OpenCode. This phase should continue that line, but
  at the deep-execution layer rather than the install layer.
- The milestone should prefer one shared acceptance harness and one shared
  parity vocabulary before splitting into runtime-specific fixes.

</specifics>

<deferred>
## Deferred Ideas

- Claude Code-specific deep-execution fixes and acceptance hardening belong to
  Phase `135`.
- OpenCode-specific deep-execution fixes and acceptance hardening belong to
  Phase `136`.
- Final parity closure reporting and any reopened backlog promotion belong to
  Phase `137`.
- OpenClaw parity remains out of scope for this milestone.

</deferred>

---

*Phase: 134-runtime-parity-contract-and-shared-acceptance-harness*
*Context gathered: 2026-04-11*
