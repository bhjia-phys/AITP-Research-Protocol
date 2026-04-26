# Phase 136: OpenCode Deep-Execution Probe - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase lands the first OpenCode-specific deep-execution probe for `v1.67`.

The phase owns:

- exercising the supported OpenCode plugin bootstrap surface
- proving that the OpenCode plugin can be checked against real bounded AITP
  runtime artifacts on an isolated kernel root
- recording exactly which bounded deep-execution surfaces match the Codex
  baseline and which still fall short
- promoting OpenCode from `probe_pending` to an honest "probe now exists"
  state in runtime truth surfaces

This phase does **not** yet claim full OpenCode parity with Codex, and it does
**not** close the final cross-runtime audit. Those belong to Phase `137`.

</domain>

<decisions>
## Implementation Decisions

### Probe Entry Surface
- **D-01:** The probe must enter through the supported OpenCode plugin surface,
  not through an OpenCode-only synthetic shim.
- **D-02:** The bounded bootstrap proof should execute the plugin module
  directly with Node, calling the real `config` and
  `experimental.chat.system.transform` hooks.
- **D-03:** The report should stay explicit that direct plugin execution is a
  bootstrap receipt, not a proof of a full live OpenCode app turn.

### Probe Shape
- **D-04:** Reuse the shared parity harness from Phases `134` and `135` rather
  than creating an OpenCode-only script.
- **D-05:** Keep the probe bounded: install project-local `.opencode` assets
  into a temp root, verify plugin hook output, then route a real
  natural-language `aitp session-start` plus `status` flow on an isolated
  kernel root.
- **D-06:** Reuse the shared Jones Chapter 4 topic so the OpenCode probe can be
  compared directly against the Codex baseline artifact bar and the Claude
  probe report.

### Honesty Contract
- **D-07:** The probe report must distinguish "plugin bootstrap and bounded AITP
  runtime behavior match Codex expectations" from "live OpenCode session parity
  is closed."
- **D-08:** `aitp doctor` should stop saying OpenCode deep execution is
  `probe_pending` once the probe lands, but it still must not imply parity is
  closed before the final audit phase.

### the agent's Discretion
- Exact status labels may evolve if they keep "probe exists" separate from
  "parity verified."
- Helper fields may be added to the report when they make plugin debugging
  easier for operators.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone Scope
- `.planning/REQUIREMENTS.md` — active requirement mapping for `REQ-PARITY-04`.
- `.planning/ROADMAP.md` — phase ordering for `v1.67`.
- `.planning/MILESTONE-CONTEXT.md` — why OpenCode is the next runtime probe.
- `.planning/phases/134-runtime-parity-contract-and-shared-acceptance-harness/134-CONTEXT.md`
  — shared parity contract and baseline vocabulary.
- `.planning/phases/135-claude-code-deep-execution-probe/135-CONTEXT.md` —
  prior runtime-specific probe pattern.

### Shared Parity And Doctor Surfaces
- `research/knowledge-hub/runtime/scripts/run_runtime_parity_acceptance.py` —
  shared parity harness to extend.
- `research/knowledge-hub/knowledge_hub/runtime_support_matrix.py` — deep
  execution parity truth surface for doctor.
- `research/knowledge-hub/knowledge_hub/frontdoor_support.py` — top-level
  doctor parity summary.
- `research/knowledge-hub/knowledge_hub/cli_compat_handler.py` — human-readable
  doctor output.

### OpenCode Install And Bootstrap Assets
- `docs/INSTALL_OPENCODE.md` — supported OpenCode install/verify story.
- `.opencode/INSTALL.md` — plugin-first install guidance.
- `docs/README.opencode.md` — compact operator-facing OpenCode entrypoint.
- `.opencode/plugins/aitp.js` — OpenCode plugin module contract.
- `research/knowledge-hub/knowledge_hub/agent_install_support.py` — OpenCode
  asset installer and plugin template.

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
  coverage for OpenCode assets.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `install_agent(... agent="opencode" ...)` already knows how to materialize
  the `.opencode` skills, plugin, and optional MCP config into a temp target
  root.
- The OpenCode plugin is a real ESM module with two concrete hooks:
  `config` and `experimental.chat.system.transform`.
- Production `session-start` already writes `session_start.contract.json`,
  `session_start.generated.md`, current-topic memory, and normal runtime
  protocol artifacts.

### Established Patterns
- Acceptance scripts should emit one operator-readable JSON report and should
  verify real hook/runtime artifacts instead of mocking success.
- Runtime truth should describe current readiness, while the parity harness
  records the actual bounded execution evidence.
- Doctor summaries may surface "probe exists" without overstating
  "parity verified."

### Integration Points
- The shared parity harness should remain the single execution entrypoint for
  Codex, Claude Code, and OpenCode.
- `deep_execution_parity_summary()` should keep treating OpenCode as pending
  until Phase `137` actually closes parity.

</code_context>

<specifics>
## Specific Ideas

- The OpenCode probe should be honest about its bridge: it can verify the real
  plugin module behavior and the downstream AITP runtime lane, but it cannot
  yet prove that a live restarted OpenCode session always consumes those hooks
  before its first substantive model action.
- That remaining gap is acceptable for `Phase 136` as long as it is named
  explicitly in the report and docs.

</specifics>

<deferred>
## Deferred Ideas

- turning the OpenCode report into `parity_verified`
- cross-runtime closure audit and final milestone closeout
- OpenClaw parity

</deferred>

---

*Phase: 136-opencode-deep-execution-probe*
*Context gathered: 2026-04-11*
