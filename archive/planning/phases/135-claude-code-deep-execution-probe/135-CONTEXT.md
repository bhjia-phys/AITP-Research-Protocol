# Phase 135: Claude Code Deep-Execution Probe - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase lands the first Claude Code-specific deep-execution probe for
`v1.67`.

The phase owns:

- exercising the supported Claude Code SessionStart bootstrap surface
- proving that the Claude bootstrap path can be checked against real AITP
  runtime artifacts on an isolated kernel root
- recording exactly which bounded deep-execution surfaces match the Codex
  baseline and which still fall short
- promoting Claude Code from `probe_pending` to an honest "probe now exists"
  state in runtime truth surfaces

This phase does **not** yet claim full Claude Code parity with Codex, and it
does **not** yet implement the OpenCode-specific probe. Those belong to later
phases.

</domain>

<decisions>
## Implementation Decisions

### Probe Entry Surface
- **D-01:** The probe must enter through the supported Claude SessionStart
  bootstrap surface, not through a synthetic Claude-only helper.
- **D-02:** On Windows-native, exercise the generated `run-hook.cmd` wrapper so
  the probe covers the actual wrapper path that user installs rely on.
- **D-03:** The probe may use the Python sidecar hook underneath the wrapper,
  but that relationship should stay visible in the report.

### Probe Shape
- **D-04:** Reuse the shared parity harness from Phase `134` rather than
  creating a one-off Claude-only script.
- **D-05:** Keep the probe bounded: install assets into a temp Claude project
  root, verify the SessionStart payload, then route a real natural-language
  request through production `aitp session-start` plus `status` on an isolated
  kernel root.
- **D-06:** Reuse the shared Jones Chapter 4 topic so the Claude probe can be
  compared directly against the Codex baseline artifact bar.

### Honesty Contract
- **D-07:** The probe report must separate "matches Codex on the bounded AITP
  artifact surface" from "still not proven through a live Claude chat turn."
- **D-08:** `aitp doctor` should stop saying Claude deep execution is
  `probe_pending` once the probe lands, but it still must not imply full parity
  unless a later closure phase earns `parity_verified`.

### the agent's Discretion
- Exact status labels may evolve if they stay explicit about "probe exists"
  versus "parity verified."
- The probe report may add helper fields when they improve operator debugging,
  as long as the top-level comparison remains easy to read.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope
- `.planning/REQUIREMENTS.md` — active requirement mapping for `REQ-PARITY-03`.
- `.planning/ROADMAP.md` — phase ordering for `v1.67`.
- `.planning/MILESTONE-CONTEXT.md` — why Claude Code is the next runtime probe.
- `.planning/phases/134-runtime-parity-contract-and-shared-acceptance-harness/134-CONTEXT.md`
  — shared parity contract and baseline vocabulary.

### Shared Parity And Doctor Surfaces
- `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py` —
  shared parity harness to extend.
- `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py` — deep
  execution parity truth surface for doctor.
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` — top-level
  doctor parity summary.
- `research/knowledge-hub/knowledge_hub/cli_compat_handler.py` — human-readable
  doctor output.

### Claude Code Install And Bootstrap Assets
- `docs/INSTALL_CLAUDE_CODE.md` — supported Claude Code install/verify story.
- `research/knowledge-hub/knowledge_hub/agent_install_support.py` — Claude
  asset installer and wrapper generation.
- `hooks/session-start.py` — Python SessionStart sidecar.
- `hooks/run-hook.cmd` — Windows-native wrapper path.
- `hooks/hooks.json` — Claude hook manifest contract.

### Runtime Routing And Acceptance Anchors
- `research/knowledge-hub/knowledge_hub/chat_session_support.py` — production
  `session-start` routing.
- `research/knowledge-hub/runtime/scripts/run_first_run_topic_acceptance.py` —
  isolated kernel prep plus bounded bootstrap/loop/status anchor.
- `research/knowledge-hub/runtime/scripts/run_public_install_smoke.py` —
  isolated temp-root install proof pattern.

### Regression Coverage
- `research/knowledge-hub/tests/test_aitp_service.py` — runtime truth surface
  contracts.
- `research/knowledge-hub/tests/test_aitp_cli.py` — human-readable doctor
  output contract.
- `research/knowledge-hub/tests/test_agent_bootstrap_assets.py` — bootstrap/doc
  coverage for Claude Code assets.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `install_agent(... agent=\"claude-code\" ...)` already knows how to materialize
  the `.claude` skills, hooks, wrapper, and settings into a temp target root.
- The Python SessionStart sidecar already emits a structured JSON payload that
  includes the injected `using-aitp` content.
- Production `session-start` already writes `session_start.contract.json`,
  `session_start.generated.md`, current-topic memory, and normal runtime
  protocol artifacts.

### Established Patterns
- Acceptance scripts should emit one operator-readable JSON report and should
  verify real artifacts instead of mocking success.
- Runtime truth should describe current machine/readiness state, while the
  acceptance script should record the actual bounded execution evidence.
- Doctor summaries may surface "probe exists" without overstating
  "parity verified."

### Integration Points
- The shared parity harness should remain the single execution entrypoint for
  Codex, Claude Code, and OpenCode.
- `deep_execution_parity_summary()` should keep treating Claude as pending until
  a later phase actually closes parity, even after the probe exists.

</code_context>

<specifics>
## Specific Ideas

- The Claude probe should be honest about its bridge: it can verify the real
  SessionStart receipt and the downstream AITP runtime lane, but it cannot yet
  prove that a live Claude Code model turn always consumes that receipt exactly
  as intended.
- That remaining gap is acceptable for `Phase 135` as long as it is named
  explicitly in the report and docs.

</specifics>

<deferred>
## Deferred Ideas

- Turning the Claude report into `parity_verified`
- OpenCode-specific parity probe work
- Cross-runtime closure audit and final milestone closeout
- OpenClaw parity

</deferred>

---

*Phase: 135-claude-code-deep-execution-probe*
*Context gathered: 2026-04-11*
