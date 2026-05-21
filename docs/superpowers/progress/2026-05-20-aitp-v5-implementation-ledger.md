# AITP v5 Implementation Ledger

This ledger is the review trail for the long-running AITP v5 goal. It records
coherent subfeatures, their planning source, changed surface, verification, and
next recommended work. Typed kernel records remain authoritative; this ledger is
orientation and audit metadata.

## Entry Format

Each entry should record:

- commit hash;
- task name;
- planning source or requirement;
- changed files;
- public API/CLI/MCP/runtime/hook changes;
- tests added or changed;
- verification commands and results;
- residual risks or deferred items;
- next recommended task.

## Entries

### c242fea - Add Goal Instructions

- Task: add long-form `/goal` instructions for completing AITP v5.
- Planning source: user request for a persistent goal objective under the Codex
  objective length limit.
- Changed files:
  - `docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md`
- Public surface changes: none.
- Tests: none; documentation-only change.
- Verification:
  - `git diff --check -- .` passed before commit.
- Residual risks:
  - The goal file defines process, not implementation completeness.
- Next recommended task:
  - Continue closing explicit gaps in the v5 next-agent plan.

### 2087cf7 - Add Post-Tool Hook Adapter

- Task: expose the v5 post-tool trace-event helper through the shell hook
  adapter.
- Planning source:
  - `docs/superpowers/plans/2026-05-18-aitp-v5-hooks-plan.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Changed files:
  - `brain/v5/hook_adapters.py`
  - `hooks/aitp_v5_hook.py`
  - `tests/test_v5_hooks.py`
  - hook and next-agent planning docs
- Public surface changes:
  - `python hooks\aitp_v5_hook.py post-tool ...`
  - output kind `hook_trace_event`
- Tests:
  - added script-level post-tool adapter coverage.
- Verification:
  - `pytest tests\test_v5_hooks.py tests\test_v5_trace_audit.py -q`: 13 passed.
  - full v5 focused suite: 267 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
- Residual risks:
  - Post-tool trace event persistence from platform hooks remains installer/adapter
    work.
- Next recommended task:
  - Add Codex/Claude/OpenCode hook installation docs and later native installer
    templates.

### 855a3e6 - Add Pre-Tool Hook Adapter

- Task: expose pre-tool hook decisions through machine-readable shell output.
- Planning source:
  - `docs/superpowers/plans/2026-05-18-aitp-v5-hooks-plan.md`
- Changed files:
  - `brain/v5/hook_adapters.py`
  - `hooks/aitp_v5_hook.py`
  - `tests/test_v5_hooks.py`
  - hook planning docs
- Public surface changes:
  - `python hooks\aitp_v5_hook.py pre-tool ...`
- Tests:
  - script-level pre-tool adapter coverage.
- Verification:
  - full v5 focused suite at that point: 266 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
- Residual risks:
  - Platform-specific installation templates were not yet documented.
- Next recommended task:
  - Add post-tool shell adapter and installation docs.

### 6f34816 - Document Hook Installation Contract

- Task: document how Codex, Claude Code, and OpenCode should wire v5 hook
  adapters, and establish this implementation ledger.
- Planning source:
  - v5 goal instruction reviewability requirement.
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
    major gap: hook installation docs.
- Changed files:
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/progress/2026-05-20-aitp-v5-implementation-ledger.md`
  - v5 hook and next-agent planning docs
- Public surface changes:
  - no runtime behavior change;
  - documented command contract for `pre-commit`, `pre-tool`, and `post-tool`.
- Tests:
  - no tests added; documentation-only slice.
- Verification:
  - `pytest tests\test_v5_hooks.py -q`: 10 passed.
  - full v5 focused suite: 267 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed for tracked changes before staging.
- Residual risks:
  - Native installer wiring remains future work.
- Next recommended task:
  - Implement or test the first native adapter/installer bridge for one platform,
    likely Codex runtime instructions or Claude Code settings template.

### 0d8a448 - Expose Hook Protocols In Adapter Packets

- Task: expose the v5 hook installation contract as typed adapter metadata.
- Planning source:
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Changed files:
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_contracts.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_contracts.py`
  - hook installation and next-agent planning docs
- Public surface changes:
  - adapter packets now include `runtime_hook_protocols`;
  - adapter protocol registry/fingerprint includes `runtime_hook_protocols`.
- Tests:
  - adapter packet exposes pre-commit, pre-tool, and post-tool hook protocol metadata;
  - adapter packet contract rejects trusted-summary hook protocol tampering.
- Verification:
  - focused red test failed with missing `runtime_hook_protocols`.
  - `pytest tests\test_v5_adapters.py tests\test_v5_contracts.py tests\test_v5_public_surfaces.py tests\test_v5_architecture_boundaries.py -q`: 57 passed.
  - full v5 focused suite: 269 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
- Residual risks:
  - native platform installers still need to consume the typed metadata;
  - post-tool trace event persistence from platform hooks is still not automatic.
- Next recommended task:
  - implement a Codex or Claude Code installer/template test that consumes
    `runtime_hook_protocols` instead of duplicating hook commands.

### 42a500d - Derive Hook Installation Template From Hook Protocols

- Task: expose runtime hook installation instructions in adapter packets without
  duplicating hook command definitions.
- Planning source:
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - previous ledger recommendation after `0d8a448`.
- Changed files:
  - `brain/v5/adapters.py`
  - `brain/v5/adapter_contracts.py`
  - `brain/v5/hook_install_templates.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_contracts.py`
  - hook installation and next-agent planning docs
- Public surface changes:
  - adapter packets now include `runtime_hook_installation`;
  - Codex receives `installation_mode=explicit_guard_calls` derived from
    `runtime_hook_protocols`.
- Tests:
  - Codex adapter packet builds hook installation from hook protocols;
  - adapter packet contract rejects stale hook installation templates.
- Verification:
  - focused red test failed with missing `runtime_hook_installation`.
  - `pytest tests\test_v5_adapters.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`: 48 passed.
  - full v5 focused suite: 271 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
- Residual risks:
  - native platform config writers still need to consume this template;
  - post-tool trace event persistence remains stdout-only until a runtime bridge
    writes it through v5 trace/kernel paths.
- Next recommended task:
  - add a native config writer or bridge test for one runtime using
    `runtime_hook_installation`.

### d71e424 - Generate Codex Hook Bridge From Installation Template

- Task: generate a Codex-readable guard-call bridge from
  `runtime_hook_installation`.
- Planning source:
  - previous ledger recommendation after `42a500d`.
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
- Changed files:
  - `.codex/INSTALL.md`
  - `brain/v5/hook_install_templates.py`
  - `tests/test_v5_adapters.py`
  - hook installation and next-agent planning docs
- Public surface changes:
  - `write_codex_hook_bridge(path, installation)` writes an orientation-only
    Markdown bridge from typed installation metadata.
- Tests:
  - Codex hook bridge rendering uses the supplied installation template rather
    than hardcoded hook commands.
- Verification:
  - focused red test failed with missing `write_codex_hook_bridge`.
  - `pytest tests\test_v5_adapters.py tests\test_v5_architecture_boundaries.py -q`: 17 passed.
  - full v5 focused suite: 272 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
- Residual risks:
  - bridge output is a generated instruction file, not a native Codex lifecycle
    hook integration;
  - post-tool trace persistence remains a separate runtime bridge task.
- Next recommended task:
  - add a CLI/runtime command to materialize the Codex hook bridge from an actual
    adapter packet, or implement the Claude Code native settings writer.

### f460fa3 - Expose Codex Hook Bridge Materializer

- Task: materialize a Codex hook bridge directly from an actual v5 adapter
  packet through public runtime surfaces.
- Planning source:
  - previous ledger recommendation after `d71e424`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for CLI/MCP/runtime symmetry on public capabilities.
- Changed files:
  - `.codex/INSTALL.md`
  - `brain/v5/cli.py`
  - `brain/v5/contracts.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
  - hook installation and next-agent planning docs
- Public surface changes:
  - CLI: `aitp-v5 --base <workspace> adapter hook-bridge codex <session-id>
    --output <path>`;
  - MCP: `aitp_v5_write_codex_hook_bridge`;
  - runtime entrypoint: `codex_hook_bridge`;
  - public contract: `codex_hook_bridge` with `summary_inputs_trusted=false`
    and `can_update_kernel_state=false`.
- Tests:
  - CLI writes the bridge from `runtime_hook_installation` in an adapter packet;
  - MCP wrapper returns the same contracted payload;
  - runtime entrypoint registry advertises the CLI/MCP pair;
  - public surface validator accepts contracted bridge payloads.
- Verification:
  - focused red test failed with missing `hook-bridge` command, missing MCP
    wrapper, missing runtime entrypoint, and unknown public surface.
  - `pytest tests\test_v5_adapters.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_public_surfaces.py tests\test_v5_contracts.py -q`: 63
    passed before architecture-boundary cleanup.
  - `pytest tests\test_v5_adapters.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_public_surfaces.py tests\test_v5_contracts.py
    tests\test_v5_architecture_boundaries.py -q`: 66 passed.
  - full v5 focused suite: 275 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - this is still an explicit Codex guard-call bridge, not native lifecycle hook
    integration;
  - post-tool trace persistence from platform hook output remains a separate
    runtime bridge task.
- Next recommended task:
  - implement either a Claude Code native settings/template writer, or a
    post-tool trace persistence runtime bridge that records hook trace events
    through typed v5 trace/kernel paths.

### 2a9e536 - Persist Post-Tool Hook Traces

- Task: persist `post-tool` hook stdout payloads through the typed v5 trace path
  instead of leaving them as process-local JSON output.
- Planning source:
  - residual risk after `f460fa3`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for hook/MCP/CLI/runtime symmetry and durable research
    process records.
- Changed files:
  - `.codex/INSTALL.md`
  - `README.md`
  - `brain/v5/trace.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `tests/test_v5_trace_audit.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
  - hook installation and next-agent planning docs
- Public surface changes:
  - kernel helper: `persist_hook_trace_event`;
  - CLI: `aitp-v5 --base <workspace> trace hook-event persist --payload-json
    <hook_trace_event_json>`;
  - MCP: `aitp_v5_persist_hook_trace_event`;
  - runtime entrypoint: `persist_hook_trace_event`;
  - public contract: `hook_trace_event_record` with
    `summary_inputs_trusted=false`, `can_update_claim_trust=false`, and
    `writes_trace_event=true`.
- Tests:
  - kernel persistence appends hook payloads to
    `.aitp/runtime/hook_trace_events.jsonl`;
  - CLI persists the same hook payload;
  - MCP wrapper returns the contracted payload;
  - public surface validator accepts `hook_trace_event_record`;
  - runtime entrypoint registry advertises the CLI/MCP pair.
- Verification:
  - focused red tests failed with missing `persist_hook_trace_event`, missing
    `trace` CLI command, missing MCP wrapper, unknown public surface, and missing
    runtime entrypoint.
  - focused green test set: 5 passed.
  - regression set
    `pytest tests\test_v5_trace_audit.py tests\test_v5_hooks.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_adapters.py tests\test_v5_contracts.py
    tests\test_v5_architecture_boundaries.py -q`: 83 passed.
  - full v5 focused suite: 279 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Codex/Claude/OpenCode still need native lifecycle installers to invoke the
    bridge automatically;
  - persisted trace events remain process history, not evidence or trust
    updates.
- Next recommended task:
  - implement a native lifecycle installer/template for one runtime, likely
    Claude Code settings or OpenCode plugin bridge, using the same hook protocol
    metadata and persistence surface.

### 33afc16 - Generate Claude Code Hook Settings

- Task: generate Claude Code native hook settings from the v5 runtime hook
  installation packet, and add a wrapper that can persist Claude `PostToolUse`
  events through the v5 hook trace bridge.
- Planning source:
  - previous ledger recommendation after `2a9e536`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for CLI/MCP/kernel symmetry and platform lifecycle
    hooks that keep typed records authoritative.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/cli.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - hook installation and next-agent planning docs
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public surface changes:
  - CLI: `aitp-v5 --base <workspace> adapter hook-settings claude-code
    <session-id> --output .claude/settings.local.json`;
  - MCP: `aitp_v5_write_claude_code_hook_settings`;
  - runtime entrypoint: `claude_code_hook_settings`;
  - public contract: `claude_code_hook_settings` with
    `summary_inputs_trusted=false`, `can_update_claim_trust=false`, and
    `can_write_trace_events=true`;
  - wrapper: `hooks/aitp_v5_claude_hook.py pre-tool|post-tool`.
- Tests:
  - CLI writes Claude settings from an actual adapter packet;
  - MCP wrapper returns the same contracted payload;
  - Claude hook wrapper persists a `PostToolUse` trace event;
  - public surface validator accepts the contracted settings payload;
  - runtime entrypoint registry advertises the CLI/MCP pair.
- Verification:
  - focused red tests failed with missing `hook-settings` command, missing MCP
    wrapper, missing hook script stdout, unknown public surface, and missing
    runtime entrypoint.
  - focused green test set: 5 passed.
  - regression set
    `pytest tests\test_v5_adapters.py tests\test_v5_hooks.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    81 passed.
  - full v5 focused suite: 283 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - generated settings are still a template/write command, not a one-click safe
    merge into user or project Claude settings;
  - `pre-tool` is log-only and does not yet compute a full typed policy from
    Claude tool JSON;
  - Codex/OpenCode native lifecycle integration remains incomplete.
- Next recommended task:
  - implement one-click Claude settings merge/install guard, or add the OpenCode
    plugin bridge using the same typed hook installation metadata.

### 113673e - Install Claude Hook Settings Safely

- Task: add a Claude Code settings merge installer that preserves existing
  user/project settings while adding missing AITP v5 hook commands.
- Planning source:
  - residual risk after `33afc16`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for practical runtime hook installation without making
    generated settings a truth source.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/cli.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - hook installation and next-agent planning docs
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public surface changes:
  - helper: `install_claude_code_hook_settings`;
  - CLI: `aitp-v5 --base <workspace> adapter install-hooks claude-code
    <session-id> --settings .claude/settings.local.json`;
  - MCP: `aitp_v5_install_claude_code_hook_settings`;
  - runtime entrypoint: `claude_code_hook_installation`;
  - public contract: `claude_code_hook_installation` with
    `summary_inputs_trusted=false`, `can_update_claim_trust=false`, and
    `can_write_trace_events=true`.
- Tests:
  - direct installer preserves existing `PreToolUse`, `Stop`, and non-hook
    settings fields;
  - installer appends missing AITP `PreToolUse` and `PostToolUse` entries;
  - installer is idempotent and avoids duplicate AITP hook entries;
  - CLI and MCP wrappers return contracted installation payloads;
  - public surface registry and runtime entrypoint registry advertise the new
    surface.
- Verification:
  - focused red tests failed with missing installer helper, missing CLI
    subcommand, missing MCP wrapper, unknown public surface, and missing runtime
    entrypoint.
  - focused green test set: 5 passed.
  - regression set
    `pytest tests\test_v5_adapters.py tests\test_v5_hooks.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    85 passed.
  - full v5 focused suite: 287 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - source module line counts remained below 500 lines.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Claude `PreToolUse` remains log-only and does not yet compute a full typed
    blocking policy from Claude tool JSON;
  - Codex/OpenCode native lifecycle integrations remain incomplete;
  - installer rejects malformed settings by raising errors instead of offering a
    repair flow.
- Next recommended task:
  - add OpenCode plugin/bridge generation from the same typed hook installation
    metadata, or deepen the Claude `PreToolUse` policy mapping.

### 9fbcc1d - Materialize OpenCode Hook Bridge

- Task: add OpenCode plugin bridge generation from typed v5 runtime hook
  installation metadata.
- Planning source:
  - residual risk after `113673e`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for Codex/Claude/OpenCode adapter symmetry without
    making generated bridge files truth sources.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/cli.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - hook installation and next-agent planning docs
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public surface changes:
  - helper: `write_opencode_plugin_bridge`;
  - CLI: `aitp-v5 --base <workspace> adapter hook-bridge opencode
    <session-id> --output .opencode/AITP_V5_PLUGIN_BRIDGE.md`;
  - MCP: `aitp_v5_write_opencode_plugin_bridge`;
  - runtime entrypoint: `opencode_plugin_bridge`;
  - public contract: `opencode_plugin_bridge` with
    `summary_inputs_trusted=false`, `can_update_kernel_state=false`, and
    `can_update_claim_trust=false`.
- Tests:
  - direct writer renders lifecycle calls from `runtime_hook_installation`;
  - CLI materializes an OpenCode bridge from an actual adapter packet;
  - MCP wrapper returns the contracted payload;
  - public surface registry validates `opencode_plugin_bridge`;
  - runtime entrypoint registry advertises the CLI/MCP pair.
- Verification:
  - focused red tests failed with missing writer helper, CLI support restricted
    to Codex, missing MCP wrapper, unknown public surface, and missing runtime
    entrypoint.
  - focused green test set: 5 passed.
  - regression set
    `pytest tests\test_v5_adapters.py tests\test_v5_hooks.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    89 passed.
  - full v5 focused suite: 291 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - source module line counts remained below 500 lines.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - generated OpenCode bridge is still an orientation-only guide, not an
    automatically installed native OpenCode plugin;
  - Claude `PreToolUse` remains log-only and does not compute a full typed
    blocking policy from Claude tool JSON.
- Next recommended task:
  - deepen the Claude `PreToolUse` typed policy mapping, or implement native
    OpenCode plugin invocation around the generated bridge.

### 4ab7a4d - Map Claude PreTool Policy Decisions

- Task: make the Claude Code `PreToolUse` wrapper map Claude tool JSON into a
  typed v5 policy decision and return Claude `permissionDecision` output.
- Planning source:
  - residual risk after `9fbcc1d`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement that hooks enforce protocol decisions instead of only
    generating orientation text.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - hook installation and next-agent planning docs
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - Claude `PreToolUse` now returns `hookSpecificOutput.permissionDecision`;
  - destructive Bash commands such as `rm -rf` and `git reset --hard` map to
    `destructive_action`;
  - SSH/SCP commands map to `remote_execution`;
  - scheduler-like Bash commands map to `expensive_compute`;
  - high-risk mapped actions produce a v5 typed pre-tool block with
    `required_actions=["request_human_checkpoint"]` and Claude
    `permissionDecision=deny`;
  - web/literature tools remain `allow` plus a logged typed hook decision.
- Tests:
  - destructive Bash is denied and carries the v5 `hook_decision` payload;
  - WebSearch is allowed and carries the v5 typed log decision.
- Verification:
  - focused red tests failed because the Claude hook output lacked
    `hookSpecificOutput`.
  - focused green test set: 2 passed.
  - regression set
    `pytest tests\test_v5_hooks.py tests\test_v5_adapters.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    91 passed.
  - full v5 focused suite: 293 passed.
  - `python -m compileall -q brain\v5`: passed.
  - `git diff --check -- .`: passed.
  - source module line counts remained below 500 lines.
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Claude `PreToolUse` mapping still covers only coarse Bash/web categories;
  - the wrapper creates the policy decision locally rather than querying the
    full active claim/risk context for every tool event;
  - native OpenCode plugin invocation remains incomplete.
- Next recommended task:
  - extend Claude `PreToolUse` mapping to trust-changing MCP/kernel calls, or
    add native OpenCode plugin invocation around the generated bridge.

### 5da30c9 - Map Claude MCP PreTool Actions

- Task: map Claude Code `PreToolUse` AITP MCP/kernel calls into v5 actions
  before they can alter protocol state.
- Planning source:
  - residual risk after `4ab7a4d`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement that trust-changing actions go through typed kernel
    records and preflight, not generated summaries or raw convenience calls.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - hook installation and next-agent planning docs
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - Claude hook tool names such as `mcp__aitp__aitp_v5_record_evidence` and
    `mcp__aitp__aitp_v5_apply_trust_update` are recognized as v5 actions;
  - direct `aitp_v5_apply_trust_update` maps to
    `change_claim_confidence`;
  - unqualified direct trust application denies with
    `claude_pre_tool_requires_trust_preflight` and
    `required_actions=["aitp_v5_preflight_trust_update"]`;
  - `aitp_v5_record_evidence` maps to `record_evidence` and is allowed as a
    typed write/log action;
  - generated hook output remains orientation-only with
    `summary_inputs_trusted=false`.
- Tests:
  - direct trust apply MCP call is denied and carries the v5 typed
    `hook_decision` payload;
  - evidence-recording MCP call is allowed and logged as `record_evidence`.
- Verification:
  - focused red tests failed because both MCP tools were initially classified as
    generic `claude_tool_use`, then because the public payload lacked the mapped
    `action`;
  - focused green test set:
    `pytest tests\test_v5_hooks.py::test_claude_hook_script_pre_tool_denies_direct_trust_apply_mcp_call tests\test_v5_hooks.py::test_claude_hook_script_pre_tool_allows_record_evidence_mcp_call_as_typed_write -q`:
    2 passed;
  - regression set
    `pytest tests\test_v5_hooks.py tests\test_v5_adapters.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    93 passed;
  - full v5 focused suite: 295 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - MCP mapping is still entrypoint-level and does not validate every tool input
    against full active topic/claim/risk context;
  - direct trust application can be allowed only by a trusted `source_kind`;
    there is no durable preflight token/proof chain yet;
  - native OpenCode lifecycle invocation remains incomplete.
- Next recommended task:
  - add a typed trust-update preflight token/proof chain for Claude MCP calls,
    or broaden validation/promotion MCP mapping with active workspace context.

### 3370330 - Require Trust Preflight Tokens

- Task: make trust-changing confidence mutation require a request-bound typed
  preflight proof token instead of relying on source labels alone.
- Planning source:
  - residual risk after `5da30c9`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 invariant that trust-changing actions must go through kernel records and
    auditable preflight before mutation.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/models.py`
  - `brain/v5/trust_updates.py`
  - `brain/v5/trust_contracts.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_trust_updates.py`
  - `tests/test_v5_hooks.py`
  - Claude install docs, hook installation plan, next-agent plan, and v5
    architecture spec
- Public/runtime behavior changes:
  - `preflight_trust_update` now emits `preflight_token` and
    `preflight_proof`;
  - `apply_trust_update` refuses otherwise policy-allowed confidence mutations
    unless the request carries the matching token;
  - CLI trust apply accepts `--preflight-token`;
  - MCP `aitp_v5_apply_trust_update` accepts `preflight_token`;
  - Claude `PreToolUse` denies direct `aitp_v5_apply_trust_update` unless the
    tool input carries both a trusted source kind and a `trust-preflight-*`
    token;
  - public trust preflight/apply contracts validate token/proof fields and
    require applied mutations to match the preflight token.
- Tests:
  - preflight exposes a proof token;
  - apply without a matching token does not mutate claim confidence;
  - apply with a matching token updates registry and topic ledger records;
  - CLI and MCP trust apply paths accept the matching token;
  - Claude `PreToolUse` blocks trust apply with trusted source kind but no
    token.
- Verification:
  - focused red tests failed because preflight lacked `preflight_token`, direct
    apply mutated without one, CLI/MCP could not pass the token, and Claude
    `PreToolUse` allowed source-kind-only trust apply;
  - focused green set:
    `pytest tests\test_v5_trust_updates.py::test_preflight_allows_code_method_promotion_with_evidence_and_code_state tests\test_v5_trust_updates.py::test_apply_confidence_change_requires_matching_preflight_token tests\test_v5_trust_updates.py::test_apply_confidence_change_updates_registry_and_topic_ledger tests\test_v5_trust_updates.py::test_cli_trust_apply_confidence_change_updates_claim tests\test_v5_trust_updates.py::test_mcp_apply_trust_update_accepts_matching_preflight_token tests\test_v5_hooks.py::test_claude_hook_script_pre_tool_denies_trust_apply_without_preflight_token -q`:
    6 passed;
  - regression set
    `pytest tests\test_v5_trust_updates.py tests\test_v5_hooks.py
    tests\test_v5_cli.py tests\test_v5_mcp_tools.py
    tests\test_v5_public_surfaces.py tests\test_v5_contracts.py
    tests\test_v5_architecture_boundaries.py -q`: 103 passed;
  - full v5 focused suite: 298 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - the token is deterministic and request-bound, not a persisted one-time
    nonce;
  - Claude `PreToolUse` validates token presence/shape before tool execution,
    while the kernel validates exact token matching during apply;
  - native Codex/OpenCode lifecycle invocation remains incomplete.
- Next recommended task:
  - add context-aware Claude/OpenCode/Codex pre-tool policy validation for
    validation and promotion entrypoints, or persist one-time preflight records
    if stricter token replay protection is needed.

### 30a5075 - Add Claude Context PreTool Policy

- Task: make Claude Code `PreToolUse` policy for validation and L2 promotion use
  active typed workspace context instead of entrypoint names alone.
- Planning source:
  - residual risk after `3370330`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md`;
  - v5 invariant that validation and promotion must cite typed claim, evidence,
    and code-state records rather than generated summaries.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - hook installation and next-agent planning docs
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - Claude `PreToolUse` now resolves the v5 workspace, session binding, typed
    claim, evidence refs, and linked or requested code-state records for
    `validate_claim` and `promote_to_l2` MCP entrypoints;
  - context policy reuses `evaluate_policy` instead of duplicating evidence or
    code-state rules in the hook;
  - code-method validation without code-state provenance returns a Claude
    allowed/warn decision with `required_actions=["record_code_state"]`;
  - L2 promotion without evidence refs returns a Claude deny/block decision with
    `required_actions=["attach_evidence_ref"]`.
- Tests:
  - `aitp_v5_create_validation_contract` on a code-method claim without
    code-state provenance warns before tool execution;
  - `aitp_v5_create_promotion_packet` without evidence refs denies before tool
    execution.
- Verification:
  - focused red tests failed because both entrypoints were logged with no policy
    block;
  - focused green set:
    `pytest tests\test_v5_hooks.py::test_claude_hook_script_pre_tool_warns_code_method_validation_without_code_state tests\test_v5_hooks.py::test_claude_hook_script_pre_tool_denies_l2_promotion_without_evidence_refs -q`:
    2 passed;
  - regression set
    `pytest tests\test_v5_hooks.py tests\test_v5_adapters.py
    tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py
    tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    96 passed;
  - full v5 focused suite: 300 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - context policy currently covers Claude validation/promotion entrypoints, not
    every MCP input or all active risk-context dimensions;
  - OpenCode/Codex native lifecycle pre-tool invocation remains incomplete.
- Next recommended task:
  - extend the same context-aware policy to OpenCode/Codex bridge invocation, or
    add tests for summary-sourced validation/promotion attempts through Claude
    MCP calls.

### 5f17915 - Expose Shared PreTool Policy Surface

- Task: extract the context-aware validation/L2-promotion pre-tool policy from
  the Claude wrapper into a reusable v5 kernel capability and expose it through
  CLI/MCP/runtime public surfaces.
- Planning source:
  - residual risk after `30a5075`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md`;
  - v5 invariant that adapter-facing decisions must reuse typed kernel records
    and must not treat generated summaries as truth sources.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/cli.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new kernel helper `brain.v5.pretool_policy.context_policy_decision`;
  - new public kernel payload helper
    `brain.v5.pretool_policy.evaluate_context_pre_tool_policy`;
  - new CLI command:
    `aitp-v5 policy pre-tool <action> --session <session-id> ...`;
  - new MCP wrapper: `aitp_v5_evaluate_pre_tool_policy`;
  - new runtime entrypoint: `pre_tool_policy`;
  - new public surface contract: `pre_tool_policy_decision`;
  - Claude Code `PreToolUse` now reuses the shared kernel helper instead of
    owning duplicate workspace/code-state lookup logic.
- Tests:
  - kernel/public surface blocks L2 promotion without evidence refs;
  - CLI returns a contracted pre-tool policy decision;
  - MCP warns on code-method validation without code-state provenance;
  - public-surface registry validates `pre_tool_policy_decision`;
  - runtime entrypoint registry advertises the CLI/MCP pair.
- Verification:
  - focused red set failed for missing module, CLI command, MCP wrapper, public
    surface, and runtime entrypoint;
  - focused green set:
    `pytest tests/test_v5_pretool_policy.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py -q`:
    23 passed;
  - regression set:
    `pytest tests/test_v5_pretool_policy.py tests/test_v5_hooks.py tests/test_v5_mcp_tools.py tests/test_v5_cli.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_contracts.py tests/test_v5_architecture_boundaries.py -q`:
    99 passed;
  - full v5 focused suite: 304 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Codex/OpenCode bridge documents can call the shared surface, but native
    lifecycle installers still do not invoke it automatically;
  - context policy currently covers validation and L2 promotion record
    requirements, not every MCP input or all active risk-context dimensions.
- Next recommended task:
  - add adapter tests or bridge metadata that make Codex/OpenCode explicitly
    call `pre_tool_policy_decision` before validation/promotion actions, or add
    summary-sourced validation/promotion denial tests for the shared surface.

### d898048 - Advertise PreTool Policy In Bridges

- Task: make generated Codex/OpenCode bridge payloads explicitly advertise the
  shared context-aware pre-tool policy surface, so adapters do not have to
  reconstruct validation/promotion policy entrypoints from prose.
- Planning source:
  - residual risk after `5f17915`;
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`;
  - v5 goal requirement for CLI/MCP/runtime/hook symmetry.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - Codex bridge payloads now include top-level
    `pre_tool_policy_entrypoint`;
  - OpenCode bridge payloads now include
    `plugin_bridge.pre_tool_policy_entrypoint`;
  - both entrypoints point to `aitp-v5 policy pre-tool <args>`,
    `aitp_v5_evaluate_pre_tool_policy`, and
    `pre_tool_policy_decision`;
  - bridge contracts now validate that the entrypoint is typed-record backed,
    summary-untrusted, and cannot mutate kernel state or claim trust;
  - generated bridge Markdown documents the shared policy entrypoint.
- Tests:
  - Codex bridge helper/CLI payloads include the shared pre-tool entrypoint;
  - OpenCode bridge helper/CLI payloads include the shared pre-tool entrypoint;
  - public surface examples include the entrypoint and pass contract validation.
- Verification:
  - focused red set failed because Codex/OpenCode bridge payloads lacked
    `pre_tool_policy_entrypoint`;
  - focused green set:
    `pytest tests/test_v5_adapters.py::test_codex_hook_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_codex_hook_bridge tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_opencode_plugin_bridge -q`:
    6 passed;
  - regression set:
    `pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    79 passed;
  - full v5 focused suite: 304 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Codex/OpenCode still need native lifecycle installers or runtime code that
    automatically invokes the advertised entrypoint;
  - context policy still covers validation/L2-promotion requirements rather than
    every MCP input or all active risk-context dimensions.
- Next recommended task:
  - implement one small native adapter invocation/smoke test for OpenCode or
    Codex that consumes the advertised `pre_tool_policy_entrypoint`, or add
    shared-surface tests for summary-sourced validation/promotion denial.

### 1b02058 - Expose PreTool Policy Reasons

- Task: make `pre_tool_policy_decision` carry machine-readable policy reasons
  so adapters and reviewers can audit warn/block causes without parsing
  free-form hook messages.
- Planning source:
  - residual risk after `5f17915` and `d898048`;
  - v5 invariant that summary/orientation-only surfaces cannot drive
    trust-changing validation or promotion;
  - reviewability requirement in
    `docs/superpowers/plans/2026-05-20-aitp-v5-goal-instructions.md`.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/pretool_policy.py`
  - `docs/INSTALL_CLAUDE_CODE.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - `pre_tool_policy_decision` now includes `policy_reasons`;
  - each reason includes `policy_id`, `severity`, and `message`;
  - public-surface validation now requires reason objects to be structured;
  - CLI/MCP pre-tool policy calls expose hard blocks such as
    `no_summary_surface_as_truth_source` directly in JSON.
- Tests:
  - CLI pre-tool policy blocks a summary-orientation sourced validation attempt
    and exposes `no_summary_surface_as_truth_source`;
  - MCP pre-tool policy exposes `no_l2_promotion_without_evidence_ref`;
  - public-surface validator accepts `policy_reasons`.
- Verification:
  - focused red set failed because `policy_reasons` was missing;
  - focused green set:
    `pytest tests/test_v5_pretool_policy.py::test_cli_pre_tool_policy_exposes_machine_readable_summary_source_block tests/test_v5_pretool_policy.py::test_mcp_pre_tool_policy_exposes_machine_readable_policy_reasons tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_pre_tool_policy_decision -q`:
    3 passed;
  - regression set:
    `pytest tests/test_v5_pretool_policy.py tests/test_v5_public_surfaces.py tests/test_v5_hooks.py tests/test_v5_mcp_tools.py tests/test_v5_cli.py tests/test_v5_contracts.py tests/test_v5_architecture_boundaries.py -q`:
    98 passed;
  - full v5 focused suite: 306 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines;
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - Claude native hook output still nests the shared policy decision inside its
    existing Claude-specific `aitp` payload; the shared CLI/MCP surface is the
    cleaner adapter-neutral path;
  - context policy still covers validation/L2-promotion requirements rather than
    every MCP input or all active risk-context dimensions.
- Next recommended task:
  - implement a small adapter-neutral smoke path that consumes
    `policy_reasons` for routing, or continue the main plan with the next typed
    kernel capability.

### d19b3dc - Require PreTool Policy In Gate Protocols

- Task: make adapter packets explicitly sequence the shared pre-tool policy
  before validation and L2 promotion gate actions, so runtimes cannot satisfy
  gate protocols by calling only the trust preflight.
- Planning source:
  - residual risk after `d898048` and `1b02058`;
  - v5 invariant that summaries are orientation-only and cannot become truth
    sources for validation/promotion;
  - adapter packet contract requirement that runtime gate protocols be
    machine-readable rather than prose-only.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/adapter_contracts.py`
  - `brain/v5/adapter_protocols.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_contracts.py`
- Public/runtime behavior changes:
  - adapter packets now list `aitp_v5_evaluate_pre_tool_policy` as a required
    kernel entrypoint;
  - `runtime_gate_protocols.validate_claim` and
    `runtime_gate_protocols.promote_to_l2` now include `pre_tool_policy`,
    sequence `evaluate_pre_tool_policy` immediately after
    `refresh_execution_brief`, and name `policy_reasons` as the structured
    reasons field;
  - adapter packet contract validation now reports precise issues when gate
    protocols omit or miswire the shared pre-tool policy.
- Tests:
  - adapter packet tests assert the required pre-tool policy entrypoint,
    sequencing, and `policy_reasons` field for validate/promote gates;
  - contract tests reject a gate protocol missing `pre_tool_policy` at the
    precise `adapter.runtime_gate_protocols.validate_claim.pre_tool_policy`
    path.
- Verification:
  - red adapter test failed because `aitp_v5_evaluate_pre_tool_policy` was not
    in `required_kernel_entrypoints`;
  - red contract test failed because the validator only produced a generic gate
    protocol mismatch instead of a precise `pre_tool_policy` issue;
  - focused green set:
    `pytest tests/test_v5_adapters.py::test_adapter_packet_includes_orientation_summaries_and_trusted_brief tests/test_v5_contracts.py::test_adapter_packet_contract_requires_gate_pre_tool_policy -q`:
    2 passed;
  - regression set:
    `pytest tests/test_v5_adapters.py tests/test_v5_contracts.py tests/test_v5_runtime_entrypoints.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    80 passed;
  - full v5 focused suite: 307 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines
    (`adapter_contracts.py`: 495, `adapter_protocols.py`: 471);
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - the adapter packet now defines the gate sequence, but native Codex/OpenCode
    lifecycle installers still need runtime-level tests that consume the gate
    protocol end to end;
  - `adapter_contracts.py` is close to the 500-line architecture limit, so the
    next contract-heavy slice should extract helper code before adding more
    validation logic there.
- Next recommended task:
  - add a small runtime/bridge smoke path proving a generated adapter consumes
    `runtime_gate_protocols.*.pre_tool_policy`, or extract adapter contract
    helpers before the next contract expansion.

### b45c2bc - Carry Gate Protocols Into Hook Bridges

- Task: make generated Codex/OpenCode bridge payloads and Markdown carry the
  adapter packet's runtime gate protocols, so adapter authors can consume the
  validate/promote pre-tool policy sequence without scraping prose.
- Planning source:
  - residual risk after `d19b3dc`;
  - hook installation plan requirement for adapter-neutral bridge payloads;
  - v5 invariant that bridge files are orientation-only while typed kernel
    records and packet protocols define the authoritative sequence.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/cli.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - `codex_hook_bridge` payloads now include top-level `gate_protocols` derived
    from adapter `runtime_gate_protocols`;
  - `opencode_plugin_bridge.plugin_bridge` now includes `gate_protocols`
    derived from adapter `runtime_gate_protocols`;
  - generated bridge Markdown renders each validate/promote gate sequence,
    including `evaluate_pre_tool_policy` before preflight or promotion;
  - public-surface validation now rejects Codex/OpenCode bridge payloads that
    omit the mandatory gate protocols.
- Tests:
  - CLI and MCP bridge materialization tests assert Codex/OpenCode bridge
    payloads expose `gate_protocols`;
  - bridge Markdown tests assert the rendered files include
    `evaluate_pre_tool_policy`;
  - public-surface tests reject a Codex bridge missing gate protocols and accept
    Codex/OpenCode examples with mandatory gate protocols.
- Verification:
  - red adapter tests failed with missing `gate_protocols` keys in generated
    Codex/OpenCode bridge payloads;
  - red public-surface test failed because a Codex bridge without gate
    protocols was accepted;
  - focused green set:
    `pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_mcp_codex_hook_bridge_wrapper_returns_contract_payload tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet tests/test_v5_adapters.py::test_mcp_opencode_plugin_bridge_wrapper_returns_contract_payload tests/test_v5_public_surfaces.py::test_public_surface_validator_rejects_codex_hook_bridge_without_gate_protocols tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_codex_hook_bridge tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_opencode_plugin_bridge -q`:
    7 passed;
  - regression set:
    `pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    81 passed;
  - full v5 focused suite: 308 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines
    (`cli.py`: 498, `hook_install_templates.py`: 414,
    `hook_protocol_contracts.py`: 458, `mcp_tools.py`: 397);
  - `python hooks\aitp_v5_hook.py pre-commit ...`: passed with `mode=log`.
- Residual risks:
  - `cli.py` is now close to the 500-line architecture limit, so future CLI
    changes should extract adapter command dispatch helpers before adding more
    branches;
  - generated Codex/OpenCode bridge files now carry gate protocols, but native
    lifecycle integrations still need installer-level execution tests.
- Next recommended task:
  - extract CLI adapter dispatch into a small module before the next CLI-facing
    feature, or implement a minimal native Codex/OpenCode lifecycle smoke test
    that consumes the generated gate protocol payload.

### 718fc8e - Split Adapter CLI Dispatch

- Task: keep the main v5 CLI from becoming a monolith before adding more
  adapter-facing behavior by moving adapter subcommand dispatch into a focused
  helper module.
- Planning source:
  - residual risk after `b45c2bc`;
  - v5 invariant that `cli.py`, `mcp_tools.py`, and contract modules must remain
    thin and bounded;
  - current line-count evidence that `cli.py` had reached 498 lines.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_architecture_boundaries.py`
  - `tests/test_v5_cli.py`
- Public/runtime behavior changes:
  - no intended CLI behavior change;
  - `adapter registry`, `adapter public-surfaces`, `adapter packet`,
    `adapter hook-bridge`, `adapter hook-settings`, and `adapter install-hooks`
    now dispatch through `brain.v5.cli_adapters.dispatch_adapter_command`;
  - static adapter registry/public-surface commands still avoid creating a v5
    workspace.
- Tests:
  - architecture test now requires `brain.v5.cli_adapters` and checks `cli.py`
    stays at or below 480 lines;
  - CLI contract tests monkeypatch the new adapter dispatch module boundary.
- Verification:
  - red architecture test failed with `ModuleNotFoundError` for
    `brain.v5.cli_adapters`;
  - first focused regression exposed two stale test monkeypatches against the
    old `brain.v5.cli` module boundary; root cause was the intentional dispatch
    extraction, and the tests were updated to patch `brain.v5.cli_adapters`;
  - focused green set:
    `pytest tests/test_v5_architecture_boundaries.py tests/test_v5_adapters.py tests/test_v5_cli.py tests/test_v5_runtime_entrypoints.py -q`:
    44 passed;
  - full v5 focused suite: 309 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines (`cli.py`: 464,
    `cli_adapters.py`: 93).
- Residual risks:
  - `cli.py` still contains broad command dispatch beyond adapter commands; if
    future non-adapter CLI features push it upward again, repeat this extraction
    pattern for that command family.
- Next recommended task:
  - continue native Codex/OpenCode lifecycle integration work now that the
    adapter CLI surface has room, or add a focused runtime smoke test consuming
    generated `gate_protocols`.

### b96500c - Consume Bridge Gate Protocols At Runtime

- Task: add a small runtime helper that consumes generated Codex/OpenCode bridge
  `gate_protocols` and delegates the actual validation/promotion pre-tool
  decision to the shared typed-record-backed policy surface.
- Planning source:
  - residual risk after `b45c2bc` and `718fc8e`;
  - hook installation plan requirement that Codex/OpenCode adapters consume
    generated bridge gate metadata rather than scraping prose;
  - v5 invariant that generated bridges remain orientation-only while decisions
    are backed by typed kernel records.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/adapter_runtime.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - new `brain.v5.adapter_runtime.evaluate_bridge_gate_pre_tool_policy` helper
    reads Codex top-level `gate_protocols` or OpenCode
    `plugin_bridge.gate_protocols`;
  - the helper verifies the protocol names
    `aitp_v5_evaluate_pre_tool_policy`, includes `evaluate_pre_tool_policy` in
    the sequence, and then delegates to `evaluate_context_pre_tool_policy`;
  - returned `pre_tool_policy_decision` payloads include a
    `runtime_gate_protocol` audit field showing the consumed action sequence.
- Tests:
  - generated Codex and OpenCode bridge payloads both drive a
    `promote_to_l2` pre-tool policy block through the runtime helper;
  - returned payloads remain valid `pre_tool_policy_decision` public surfaces.
- Verification:
  - red test failed with `ModuleNotFoundError` for
    `brain.v5.adapter_runtime`;
  - focused green set:
    `pytest tests/test_v5_bridge_runtime.py tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_pretool_policy.py tests/test_v5_architecture_boundaries.py -q`:
    52 passed;
  - full v5 focused suite: 310 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines
    (`adapter_runtime.py`: 65, `cli.py`: 464, `adapter_contracts.py`: 495).
- Residual risks:
  - this is still a runtime helper/smoke path, not a native Codex or OpenCode
    lifecycle installer that automatically invokes it on live tool events;
  - future installer work should exercise this helper from the platform-specific
    lifecycle wrapper.
- Next recommended task:
  - implement a minimal native Codex/OpenCode lifecycle wrapper or smoke test
    that maps an actual tool event to `evaluate_bridge_gate_pre_tool_policy`, or
    broaden pre-tool policy coverage for additional MCP inputs.

### 9a5f5be - Map Bridge Lifecycle PreTool Events

- Task: add an adapter-neutral lifecycle event wrapper that maps generated
  Codex/OpenCode bridge `pre_tool` events onto the typed-record-backed gate
  pre-tool policy path.
- Planning source:
  - residual risk after `b96500c`;
  - hook installation plan requirement for native-style Codex/OpenCode lifecycle
    invocation;
  - v5 invariant that bridge files are orientation/runtime instructions, while
    policy decisions still come from typed kernel records.
- Changed files:
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `brain/v5/adapter_runtime.py`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - `evaluate_bridge_lifecycle_event` now accepts an adapter-neutral
    `pre_tool` event payload, confirms the bridge declares a pre-tool lifecycle
    call, then delegates to `evaluate_bridge_gate_pre_tool_policy`;
  - returned decisions include a `runtime_event` audit field with the consumed
    lifecycle event and action;
  - unsupported lifecycle events or bridges without pre-tool lifecycle metadata
    fail explicitly.
- Tests:
  - generated Codex and OpenCode bridges both map a `pre_tool` event for
    `promote_to_l2` into the expected typed-record-backed policy block;
  - returned payloads validate as `pre_tool_policy_decision` public surfaces.
- Verification:
  - red test failed with missing `evaluate_bridge_lifecycle_event` import;
  - focused green set:
    `pytest tests/test_v5_bridge_runtime.py tests/test_v5_adapters.py tests/test_v5_pretool_policy.py tests/test_v5_architecture_boundaries.py -q`:
    35 passed;
  - full v5 focused suite: 311 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - source module line counts remained below 500 lines
    (`adapter_runtime.py`: 115, `cli.py`: 464, `adapter_contracts.py`: 495).
- Residual risks:
  - the wrapper is still platform-neutral; a Codex/OpenCode native installer or
    plugin wrapper must call it from real platform hook events;
  - pre-tool policy coverage still does not cover every possible MCP input.
- Next recommended task:
  - add a minimal platform-specific Codex/OpenCode wrapper over
    `evaluate_bridge_lifecycle_event`, or broaden the shared pre-tool policy for
    one additional trust-relevant MCP input class.

### 8a23544 - Guard Evidence Toolrun PreTool Sources

- Task: broaden the shared context-aware pre-tool policy to one additional
  trust-relevant MCP input class: typed evidence/tool-run record attempts.
- Planning source:
  - residual risk after `9a5f5be`;
  - v5 invariant that generated summaries, task plans, findings, and progress
    files are orientation-only and must not justify trust-changing records;
  - goal requirement that public kernel behavior stay available through
    CLI/MCP surfaces without duplicating policy logic.
- Changed files:
  - `brain/v5/pretool_policy.py`
  - `tests/test_v5_pretool_policy.py`
- Public/runtime behavior changes:
  - `evaluate_context_pre_tool_policy` now applies typed policy to
    `record_evidence` and `record_tool_run`, in addition to `validate_claim`
    and `promote_to_l2`;
  - CLI `aitp-v5 policy pre-tool record_tool_run ...` and MCP
    `aitp_v5_evaluate_pre_tool_policy(..., action="record_evidence")` now
    return hard blocks when the source is a summary/task-plan/findings/progress
    orientation surface;
  - returned payloads keep `truth_source=typed_records` and remain permission
    decisions only, with no authority to mutate kernel state.
- Tests:
  - MCP pre-tool policy blocks a `record_evidence` request sourced from
    `findings`;
  - CLI pre-tool policy blocks a `record_tool_run` request sourced from
    `task_plan`;
  - both expose `no_summary_surface_as_truth_source` in `policy_reasons`.
- Verification:
  - red test failed as expected with `mode == "log"` instead of `block`;
  - focused green test: `pytest tests/test_v5_pretool_policy.py -q`: 7 passed;
  - focused policy/MCP/CLI set:
    `pytest tests/test_v5_pretool_policy.py tests/test_v5_mcp_tools.py tests/test_v5_cli.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    55 passed;
  - full v5 focused suite: 313 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- brain/v5/pretool_policy.py tests/test_v5_pretool_policy.py`:
    passed.
- Residual risks:
  - record-time guards still depend on the adapter/runtime invoking the shared
    pre-tool policy before MCP mutation calls;
  - other trust-relevant MCP inputs and active risk context still need expanded
    policy coverage.
- Next recommended task:
  - add native Codex/OpenCode lifecycle wrapper smoke tests for
    `evaluate_bridge_lifecycle_event`, or extend shared pre-tool policy to the
    next trust-changing MCP input with typed-record-backed context.

### 4ea3436 - Normalize Platform PreTool Events

- Task: add a minimal Codex/OpenCode platform-event wrapper over the existing
  bridge lifecycle pre-tool policy path.
- Planning source:
  - residual risk after `9a5f5be` and `8a23544`;
  - hook installation plan requirement that Codex/OpenCode lifecycle events call
    the typed policy surface rather than relying on prose;
  - v5 invariant that generated bridge metadata and platform payloads are not
    truth sources.
- Changed files:
  - `brain/v5/adapter_runtime.py`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - new `brain.v5.adapter_runtime.evaluate_platform_pre_tool_event` helper
    accepts Codex-style guard-call payloads and OpenCode-style plugin lifecycle
    payloads;
  - the helper extracts the AITP MCP action, session id, claim id, evidence refs,
    code-state refs, and source metadata, then delegates to
    `evaluate_bridge_lifecycle_event`;
  - returned decisions include runtime audit metadata for `runtime`,
    `platform_event`, and `tool_name`, while the decision itself still comes from
    typed kernel records.
- Tests:
  - Codex-style `mcp__aitp__aitp_v5_create_promotion_packet` pre-tool payload
    maps to `promote_to_l2` and triggers the evidence gate;
  - OpenCode-style plugin `tool.name`/`tool.input` payload maps to the same gate;
  - both returned payloads validate as `pre_tool_policy_decision`.
- Verification:
  - red test failed as expected with missing
    `evaluate_platform_pre_tool_event` import;
  - focused green test: `pytest tests/test_v5_bridge_runtime.py -q`: 4 passed;
  - focused bridge/adapter set:
    `pytest tests/test_v5_bridge_runtime.py tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_pretool_policy.py tests/test_v5_architecture_boundaries.py -q`:
    57 passed;
  - full v5 focused suite: 315 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - `adapter_runtime.py`: 176 lines.
- Residual risks:
  - this is still a runtime normalizer and smoke path, not an automatic native
    Codex/OpenCode installer;
  - the gate-protocol bridge currently covers validation and L2 promotion, not
    every trust-changing MCP action.
- Next recommended task:
  - decide whether to extend bridge gate protocols beyond validation/promotion
    for `record_evidence` and `record_tool_run`, or add automatic
    Codex/OpenCode installer wiring that invokes the new normalizer.

### 68bc6eb - Gate Evidence And ToolRun PreTool Actions

- Task: extend runtime gate protocols and generated bridges to cover
  `record_evidence` and `record_tool_run`, matching the shared pre-tool policy
  coverage added earlier.
- Planning source:
  - residual risk after `8a23544` and `4ea3436`;
  - v5 invariant that summary/task-plan/findings/progress surfaces must not
    drive trust-changing record writes;
  - hook bridge requirement that runtime adapters consume machine-readable gate
    metadata instead of prose.
- Changed files:
  - `brain/v5/adapter_contracts.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/hook_install_templates.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - `runtime_gate_protocols` now includes `record_evidence` and
    `record_tool_run`;
  - generated Codex/OpenCode bridges carry those gate protocols in payload and
    rendered Markdown;
  - `evaluate_platform_pre_tool_event` maps `aitp_v5_record_evidence` and
    `aitp_v5_record_tool_run` MCP calls to the shared typed policy path;
  - gate protocol constants moved to `brain/v5/gate_protocols.py` so
    `adapter_protocols.py` remains below the v5 module-size boundary.
- Tests:
  - adapter packets expose exact gate protocols for record evidence/tool runs;
  - CLI-generated Codex/OpenCode bridges expose those protocols;
  - a Codex-style `record_evidence` pre-tool payload sourced from `findings`
    hard-blocks with `no_summary_surface_as_truth_source`.
- Verification:
  - red tests failed as expected with missing `record_evidence` gate protocol
    keys and missing platform action inference;
  - first focused fix exposed architecture-boundary failure:
    `adapter_protocols.py` reached 505 lines;
  - root cause fixed by extracting gate protocols into `brain/v5/gate_protocols.py`;
  - focused red-green set plus boundary test: 5 passed;
  - focused adapter/runtime set:
    `pytest tests/test_v5_adapters.py tests/test_v5_bridge_runtime.py tests/test_v5_public_surfaces.py tests/test_v5_pretool_policy.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    61 passed;
  - full v5 focused suite: 316 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - automatic native Codex/OpenCode installation still needs a platform-specific
    invocation path;
  - pre-tool policy still does not cover every possible trust-relevant MCP input
    or all active risk context.
- Next recommended task:
  - add automatic Codex/OpenCode hook invocation docs/tests around the new
    platform event normalizer, or expand pre-tool policy to the next
    trust-relevant MCP action class.

### 43ee8d3 - Expose Adapter PreTool Event Surface

- Task: expose the platform pre-tool event normalizer through public CLI, MCP,
  and runtime-entrypoint surfaces so agents do not need to import Python helpers.
- Planning source:
  - residual risk after `4ea3436` and `68bc6eb`;
  - goal requirement for CLI/MCP/runtime symmetry on public kernel capabilities;
  - hook installation plan requirement that Codex/OpenCode adapters can route
    lifecycle events into the typed policy path.
- Changed files:
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoints.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new CLI command
    `aitp-v5 adapter pre-tool-event <runtime> <session-id> --bridge-json <json> --event-json <json>`;
  - new MCP wrapper `aitp_v5_evaluate_adapter_pre_tool_event`;
  - new runtime entrypoint `adapter_pre_tool_event`, returning the contracted
    `pre_tool_policy_decision` surface;
  - the surface delegates to `evaluate_platform_pre_tool_event`, preserving
    typed records as the decision source.
- Tests:
  - CLI pre-tool-event command evaluates a Codex-style record-evidence event and
    returns a summary-source hard block;
  - MCP wrapper evaluates the same path;
  - runtime entrypoints advertise and validate the new CLI/MCP target.
- Verification:
  - red tests failed as expected because CLI command, MCP wrapper, and runtime
    entrypoint were missing;
  - target green set:
    `pytest tests/test_v5_adapters.py::test_cli_adapter_pre_tool_event_evaluates_platform_payload tests/test_v5_adapters.py::test_mcp_adapter_pre_tool_event_evaluates_platform_payload tests/test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces tests/test_v5_runtime_entrypoints.py::test_runtime_entrypoint_validation_confirms_advertised_targets_exist -q`:
    4 passed;
  - focused adapter/runtime/MCP set:
    `pytest tests/test_v5_adapters.py tests/test_v5_bridge_runtime.py tests/test_v5_mcp_tools.py tests/test_v5_runtime_entrypoints.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    66 passed;
  - full v5 focused suite: 318 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - line counts stayed below 500 (`cli.py`: 466, `cli_adapters.py`: 110,
    `mcp_tools.py`: 407, `runtime_entrypoints.py`: 486).
- Residual risks:
  - platform hooks still need automatic native installation/invocation;
  - current event payload contract is JSON-based and intentionally thin.
- Next recommended task:
  - add a small generated bridge/runtime doc or script example showing how a
    Codex/OpenCode hook invokes `adapter pre-tool-event`, or continue expanding
    pre-tool policy coverage for remaining trust-relevant actions.

### e6ff277 - Advertise Adapter PreTool Event Entrypoint

- Task: make generated Codex/OpenCode bridges advertise the CLI/MCP surface for
  normalizing live platform pre-tool events.
- Planning source:
  - residual risk after `43ee8d3`;
  - hook installation plan requirement that runtime adapters discover the
    correct typed policy invocation without prose scraping;
  - v5 invariant that bridge files are orientation/runtime instructions, not
    truth sources.
- Changed files:
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - Codex hook bridge payloads now include top-level
    `pre_tool_event_entrypoint`;
  - OpenCode plugin bridge payloads now include
    `plugin_bridge.pre_tool_event_entrypoint`;
  - both entrypoints advertise
    `aitp-v5 adapter pre-tool-event <runtime> <session-id> <args>`,
    `aitp_v5_evaluate_adapter_pre_tool_event`, required bridge/event payloads,
    and the `pre_tool_policy_decision` surface.
- Tests:
  - generated Codex/OpenCode bridge payloads include the expected event
    entrypoint metadata;
  - public surface validators accept bridges with the new metadata;
  - hook bridge contracts now validate the event entrypoint shape.
- Verification:
  - red tests failed as expected with missing `pre_tool_event_entrypoint`;
  - target green set:
    `pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_codex_hook_bridge tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_opencode_plugin_bridge -q`:
    4 passed;
  - focused adapter/public/runtime set:
    `pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    51 passed;
  - full v5 focused suite: 318 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - line counts stayed below 500 (`hook_protocol_contracts.py`: 488,
    `hook_install_templates.py`: 445).
- Residual risks:
  - this advertises invocation metadata, but still does not install an automatic
    native Codex/OpenCode hook runner;
  - JSON payload shape remains intentionally thin and should be hardened if a
    specific platform exposes richer native event schemas.
- Next recommended task:
  - add a minimal generated script/wrapper or installation instruction that uses
    `pre_tool_event_entrypoint` to call `adapter pre-tool-event`, then smoke-test
    the script against generated bridge payloads.

### c6ebb72 - Write Bridge Payload Sidecars

- Task: write machine-readable JSON sidecars for generated Codex/OpenCode
  bridges and allow CLI pre-tool event evaluation from `--bridge-path`.
- Planning source:
  - residual risk after `e6ff277`;
  - platform hook runners need bridge payloads without scraping generated
    Markdown or embedding large JSON on the shell command line;
  - generated bridge files remain orientation/runtime instructions, while typed
    kernel records remain authoritative.
- Changed files:
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_install_templates.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - Codex/OpenCode bridge writers now write a sibling JSON sidecar and include
    its path as `payload_path` in returned payloads;
  - `aitp-v5 adapter pre-tool-event` accepts `--bridge-path` in addition to
    `--bridge-json`;
  - event normalization still delegates to typed-record-backed pre-tool policy
    and does not make bridge files truth sources.
- Tests:
  - generated Codex bridge tests assert `payload_path` and read the sidecar;
  - generated OpenCode bridge tests assert `payload_path` and read the sidecar;
  - CLI pre-tool event test evaluates policy through `--bridge-path`.
- Verification:
  - red tests failed as expected with missing `payload_path`;
  - target green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_cli_adapter_pre_tool_event_evaluates_platform_payload tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template -q`:
    3 passed;
  - focused adapter/public/runtime set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    51 passed;
  - full v5 focused suite: 318 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed;
  - relevant source line counts stayed below 500
    (`hook_install_templates.py`: 462, `cli_adapters.py`: 119,
    `cli.py`: 467).
- Residual risks:
  - sidecar support still does not install automatic native Codex/OpenCode hook
    runners;
  - the live platform event schema remains intentionally thin until a concrete
    platform adapter needs a richer contract.
- Next recommended task:
  - add a tiny generated hook-runner/script or installation test that reads the
    bridge sidecar and invokes `adapter pre-tool-event --bridge-path`.

### bf29c94 - Add Bridge PreTool Runner Payloads

- Task: add a machine-readable sidecar-backed runner command vector to generated
  Codex/OpenCode bridges.
- Planning source:
  - residual risk after `c6ebb72`;
  - hook runners need a concrete invocation path from generated sidecar payloads
    to `adapter pre-tool-event`;
  - the runner must remain orientation/runtime metadata and must not become a
    state truth source.
- Changed files:
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_runner_payloads.py`
  - `brain/v5/mcp_tools.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - generated Codex bridge payloads now include top-level
    `pre_tool_event_runner.argv`;
  - generated OpenCode bridge payloads now include
    `plugin_bridge.pre_tool_event_runner.argv`;
  - CLI/MCP hook-bridge materializers pass the actual session id into the runner
    payload;
  - the runner uses `--bridge-path <payload-path>` and
    `<platform-event-json>`, preserving typed kernel records as the policy truth
    source.
- Tests:
  - CLI Codex bridge test asserts runner argv, sidecar source, and Markdown
    `--bridge-path` rendering;
  - MCP Codex bridge test asserts session id and sidecar path are carried into
    runner argv;
  - direct OpenCode bridge test asserts placeholder session runner behavior;
  - CLI OpenCode bridge test asserts actual session id and sidecar path.
- Verification:
  - red tests failed as expected with missing `pre_tool_event_runner`;
  - target green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_mcp_codex_hook_bridge_wrapper_returns_contract_payload tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet -q`:
    4 passed;
  - first focused set exposed an architecture-boundary failure because
    `hook_install_templates.py` reached 508 lines;
  - root cause fixed by extracting runner payload construction to
    `brain/v5/hook_runner_payloads.py`;
  - target runner plus boundary test:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_mcp_codex_hook_bridge_wrapper_returns_contract_payload tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet tests/test_v5_architecture_boundaries.py::test_v5_source_modules_stay_bounded -q`:
    5 passed;
  - focused adapter/public/runtime set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    51 passed.
- Residual risks:
  - this creates a concrete command vector, but still does not install a native
    Codex/OpenCode lifecycle hook;
  - platform event JSON is still supplied by the host adapter.
- Next recommended task:
  - add a tiny host-runner script or platform adapter fixture that fills
    `<platform-event-json>` from stdin/event payload and executes the generated
    argv.

### 82ab863 - Add Adapter Event Stdin Runner

- Task: add a host-facing script that reads platform pre-tool event JSON from
  stdin and evaluates it through a generated bridge sidecar.
- Planning source:
  - residual risk after `bf29c94`;
  - generated runner argv still required host adapters to supply
    `<platform-event-json>` on the command line;
  - Codex/OpenCode-style hosts commonly provide hook event payloads through
    stdin.
- Changed files:
  - `hooks/aitp_v5_adapter_event_runner.py`
  - `tests/test_v5_adapter_event_runner.py`
- Public/runtime behavior changes:
  - new script command:
    `python hooks/aitp_v5_adapter_event_runner.py pre-tool --base <workspace> --runtime <runtime> --session-id <session-id> --bridge-path <payload-path>`;
  - the script reads stdin JSON, loads the bridge sidecar, validates runner
    runtime/session/sidecar metadata, fills runtime/session/pre-tool defaults,
    and delegates to the same typed-record-backed pre-tool policy path;
  - the script returns the contracted `pre_tool_policy_decision` payload and
    exits with its hook `exit_code`.
- Tests:
  - subprocess test generates a Codex bridge sidecar, sends a summary-sourced
    `record_evidence` event through stdin without runtime/session/hook fields,
    and asserts a typed hard block with exit code 2.
- Verification:
  - red test failed as expected because
    `hooks/aitp_v5_adapter_event_runner.py` did not exist and produced no JSON;
  - target green set:
    `python -m pytest tests/test_v5_adapter_event_runner.py -q`: 1 passed.
- Residual risks:
  - this is still a thin host runner, not automatic installation into Codex or
    OpenCode native lifecycle config;
  - richer platform event schemas may need additional normalization fields.
- Next recommended task:
  - advertise the stdin runner in generated bridge payloads or add platform
    installation wiring that calls it directly.

### 13df91c - Advertise Adapter Stdin Runner In Bridge Payloads

- Task: make generated Codex/OpenCode bridge sidecars and Markdown advertise
  the stdin host-runner command vector.
- Planning source:
  - residual risk after `82ab863`;
  - bridge sidecars already had a low-level `adapter pre-tool-event` argv, but
    the host-facing stdin runner was only documented outside the machine
    payload.
- Changed files:
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_runner_payloads.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - `pre_tool_event_runner.stdin_runner.argv` is now present in Codex bridge
    payloads;
  - `plugin_bridge.pre_tool_event_runner.stdin_runner.argv` is now present in
    OpenCode bridge payloads;
  - generated Markdown renders the stdin runner command for hosts that pass
    platform event JSON through stdin.
- Tests:
  - Codex CLI/MCP bridge tests assert actual session id and sidecar path in the
    stdin runner argv;
  - OpenCode direct/CLI bridge tests assert placeholder and actual session id
    behavior;
  - Codex/OpenCode bridge Markdown tests assert the stdin runner script is
    rendered.
- Verification:
  - red tests failed as expected with missing `stdin_runner` and then missing
    Markdown rendering;
  - target green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_mcp_codex_hook_bridge_wrapper_returns_contract_payload tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet -q`:
    4 passed;
  - focused adapter/runtime set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_adapter_event_runner.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    52 passed;
  - `hook_install_templates.py`: 496 lines; `hook_runner_payloads.py`: 59
    lines.
- Residual risks:
  - native Codex/OpenCode installation is still not automatic;
  - `hook_install_templates.py` is close to the 500-line source boundary.
- Next recommended task:
  - add native-ish Codex/OpenCode installation fixtures that call the advertised
    stdin runner, or split bridge Markdown rendering before the next template
    expansion.

### 8898c68 - Split Hook Bridge Markdown Rendering

- Task: split generated bridge Markdown rendering out of
  `brain/v5/hook_install_templates.py`.
- Planning source:
  - residual risk after `13df91c`;
  - v5 module-size invariant and user requirement to avoid recreating the old
    monolithic AITP file pattern;
  - `hook_install_templates.py` reached 496 lines, leaving too little room for
    native-ish installation fixtures.
- Changed files:
  - `brain/v5/hook_bridge_markdown.py`
  - `brain/v5/hook_install_templates.py`
  - `tests/test_v5_architecture_boundaries.py`
- Public/runtime behavior changes:
  - no intended behavior change;
  - Codex/OpenCode bridge writers still render the same Markdown and sidecars;
  - `hook_install_templates.py` now delegates rendering to
    `hook_bridge_markdown.py`.
- Tests:
  - new architecture-boundary test requires `hook_install_templates.py` to stay
    at or below 450 lines;
  - existing Codex/OpenCode bridge rendering tests continue to verify rendered
    policy, sidecar, and stdin runner content.
- Verification:
  - red boundary test failed as expected at 496 lines;
  - after extraction, target green set:
    `python -m pytest tests/test_v5_architecture_boundaries.py::test_hook_install_template_module_stays_renderer_free tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template -q`:
    3 passed;
  - focused adapter/runtime set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_adapter_event_runner.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    53 passed;
  - post-extraction line counts: `hook_install_templates.py`: 334,
    `hook_bridge_markdown.py`: 156.
- Residual risks:
  - renderer tests are still covered through bridge writer behavior rather than
    a dedicated renderer test module;
  - native Codex/OpenCode installation wiring remains unfinished.
- Next recommended task:
  - implement native-ish Codex/OpenCode install fixtures now that the template
    module has room again.

### 2951649 - Add Codex Stdin Runner Install Fixture

- Task: add a Codex native-ish hook installation fixture that points pre-tool
  events at the existing stdin host-runner without making generated files truth
  sources.
- Planning source:
  - hook-installation plan gap for Codex runtime wiring;
  - previous `02c06fe` split made room in `hook_install_templates.py`;
  - v5 rule that typed kernel records remain authoritative and generated
    bridge/fixture files are runtime metadata only.
- Changed files:
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoints.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `aitp-v5 adapter install-hooks codex <session-id> --output <path>` writes
    `.codex/AITP_V5_HOOKS.json` plus the Codex bridge Markdown and JSON sidecar;
  - `aitp_v5_install_codex_hook_fixture` exposes the same behavior through MCP;
  - new public surface `codex_hook_installation` validates the fixture, bridge,
    runner argv, and `summary_inputs_trusted=false`/no state-mutation flags.
- Tests:
  - CLI installer test asserts fixture, bridge, sidecar, runner argv, session id,
    and sidecar path;
  - MCP installer test asserts the contracted payload and runner metadata;
  - runtime entrypoint and public surface registry tests include
    `codex_hook_installation`.
- Verification:
  - red tests failed as expected with missing CLI support, MCP wrapper, and
    runtime entrypoint;
  - target green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_install_hooks_writes_codex_stdin_runner_fixture tests/test_v5_adapters.py::test_mcp_codex_hook_installer_returns_contract_payload tests/test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces tests/test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads -q`:
    4 passed.
- Residual risks:
  - this is a fixture for Codex-style host wiring, not a guaranteed native Codex
    lifecycle installer;
  - OpenCode still lacks the corresponding fixture;
  - `runtime_entrypoints.py` is close to the source-size boundary and should be
    split before adding more entrypoint metadata.
- Next recommended task:
  - split `runtime_entrypoints.py` metadata/sample args, then add the matching
    OpenCode stdin-runner installation fixture.

### 40f6af7 - Split Runtime Entrypoint Catalog Data

- Task: split runtime entrypoint metadata and CLI parser sample arguments out of
  `brain/v5/runtime_entrypoints.py` before adding another hook-installation
  surface.
- Planning source:
  - residual risk from `2951649`;
  - user requirement to avoid old-style large AITP files;
  - v5 architecture boundary that validator modules should stay focused.
- Changed files:
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `brain/v5/runtime_entrypoints.py`
  - `tests/test_v5_architecture_boundaries.py`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - no intended behavior change;
  - `runtime_entrypoints()` continues returning the same CLI/MCP surface map;
  - validation still confirms advertised CLI/MCP targets parse and exist.
- Tests:
  - new architecture-boundary test requires `runtime_entrypoints.py` to stay at
    or below 450 lines;
  - existing runtime-entrypoint tests validate the same public behavior.
- Verification:
  - red boundary test failed as expected at 496 lines;
  - target green set:
    `python -m pytest tests/test_v5_architecture_boundaries.py::test_runtime_entrypoints_module_keeps_catalog_out_of_validator_logic tests/test_v5_runtime_entrypoints.py -q`:
    4 passed.
- Residual risks:
  - the new catalog module is data-heavy by design and should be split by
    runtime/action family if it approaches the global source-size boundary.
- Next recommended task:
  - add the matching OpenCode stdin-runner installation fixture.

### bcc53e0 - Add OpenCode Stdin Runner Install Fixture

- Task: add an OpenCode native-ish plugin fixture that points pre-tool events at
  the existing stdin host-runner without making generated files truth sources.
- Planning source:
  - residual risk from `40f6af7`;
  - hook-installation plan gap for OpenCode fixture-level host wiring;
  - v5 rule that generated bridge/fixture files are runtime metadata only.
- Changed files:
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_fixture_templates.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `aitp-v5 adapter install-hooks opencode <session-id> --output <path>` writes
    `.opencode/AITP_V5_PLUGIN_HOOKS.json` plus the OpenCode plugin bridge
    Markdown and JSON sidecar;
  - `aitp_v5_install_opencode_hook_fixture` exposes the same behavior through
    MCP;
  - new public surface `opencode_hook_installation` validates the fixture,
    embedded plugin bridge, runner argv, and no-trust/no-state-mutation flags;
  - Codex fixture writing moved from `hook_install_templates.py` to
    `hook_fixture_templates.py` to keep bridge templates bounded.
- Tests:
  - CLI installer test asserts fixture, plugin bridge, sidecar, runner argv,
    session id, runtime, and sidecar path;
  - MCP installer test asserts contracted payload and runner metadata;
  - runtime entrypoint and public surface registry tests include
    `opencode_hook_installation`.
- Verification:
  - red tests failed as expected with missing CLI support, MCP wrapper, runtime
    entrypoint, and public surface;
  - target green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_install_hooks_writes_opencode_stdin_runner_fixture tests/test_v5_adapters.py::test_mcp_opencode_hook_installer_returns_contract_payload tests/test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces tests/test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads -q`:
    4 passed.
- Residual risks:
  - this is still fixture-level host wiring, not a guaranteed native OpenCode
    lifecycle installer;
  - native Codex/OpenCode runtime integration still depends on host support for
    invoking the generated stdin runner.
- Next recommended task:
  - expand pre-tool policy coverage for active risk context or add fixture
    smoke tests that execute the generated runner against a sample platform
    event.

### 9a75ec7 - Smoke Test Generated Fixture Runners

- Task: verify generated Codex/OpenCode fixture hooks can execute their declared
  stdin runner argv against sample platform events.
- Planning source:
  - residual risk from `bcc53e0`;
  - fixture-level host wiring must be executable, not only schema-valid;
  - generated fixture files remain runtime metadata only, while typed policy
    decisions remain authoritative.
- Changed files:
  - `brain/v5/hook_fixture_templates.py`
  - `brain/v5/hook_install_contracts.py`
  - `tests/test_v5_adapter_event_runner.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - generated Codex/OpenCode fixture pre-tool hooks now declare a repository
    `cwd` so their relative `hooks/aitp_v5_adapter_event_runner.py` argv can be
    executed by host adapters;
  - fixture contracts require the `cwd` field;
  - no generated fixture gains authority to mutate typed kernel state or claim
    trust.
- Tests:
  - Codex fixture smoke test installs the fixture, executes
    `fixture.hooks.pre_tool.argv` from `cwd`, and confirms a summary-sourced
    evidence record attempt is blocked by typed policy;
  - OpenCode fixture smoke test does the same through
    `fixture.plugin_hooks.pre_tool.argv`.
- Verification:
  - red tests failed as expected with missing `cwd`;
  - target green set:
    `python -m pytest tests/test_v5_adapter_event_runner.py::test_codex_install_fixture_runner_executes_from_declared_cwd tests/test_v5_adapter_event_runner.py::test_opencode_install_fixture_runner_executes_from_declared_cwd -q`:
    2 passed.
- Residual risks:
  - smoke tests execute the generated runner contract but do not prove a real
    Codex/OpenCode host has native lifecycle wiring installed.
- Next recommended task:
  - broaden pre-tool policy coverage for active risk context, or add host-side
    installation docs/tests for the next runtime that exposes a native hook API.

### 1d813e0 - Require Checkpoints For Adversarial Trust Changes

- Task: broaden shared pre-tool policy coverage for active risk context by
  requiring an approved typed human checkpoint for adversarial-risk
  trust-changing actions.
- Planning source:
  - remaining gap in the next-agent implementation plan: pre-tool policy did
    not yet cover all active risk context;
  - v5 invariant that trust-changing actions must go through typed kernel
    records, preflight, validation, or explicit human checkpoint records.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `aitp_v5_evaluate_pre_tool_policy` accepts `human_checkpoint_id`;
  - `aitp-v5 policy pre-tool` accepts `--human-checkpoint`;
  - `evaluate_platform_pre_tool_event` forwards `human_checkpoint_id` from
    platform events/tool inputs;
  - `pre_tool_policy_decision` payloads include `risk_level` and
    `human_checkpoint_id`;
  - adversarial-risk trust-changing actions hard-block with
    `adversarial_trust_change_requires_human_checkpoint` unless the checkpoint
    is a decided typed `HumanCheckpointRecord` with `decision=approve` for the
    active claim.
- Tests:
  - MCP pre-tool policy blocks adversarial promotion without checkpoint even
    when evidence refs exist;
  - MCP pre-tool policy allows adversarial promotion with an approved typed
    checkpoint;
  - CLI pre-tool policy accepts `--human-checkpoint`;
  - adapter pre-tool event path carries adversarial risk/checkpoint context;
  - public-surface validator rejects invalid pre-tool `risk_level`.
- Verification:
  - red tests failed as expected with missing `risk_level` payload field,
    missing MCP `human_checkpoint_id`, missing CLI `--human-checkpoint`, and
    missing risk-level contract validation;
  - target green set:
    `python -m pytest tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_pre_tool_policy_decision tests/test_v5_public_surfaces.py::test_public_surface_validator_rejects_invalid_pre_tool_policy_risk_level tests/test_v5_pretool_policy.py tests/test_v5_adapters.py::test_mcp_adapter_pre_tool_event_passes_adversarial_checkpoint_context -q`:
    13 passed.
- Residual risks:
  - pre-tool policy still does not cover every possible MCP input or every risk
    dimension, but adversarial trust-changing paths now require typed human
    approval.
- Next recommended task:
  - extend bridge/runtime metadata to advertise `human_checkpoint_id` as a
    first-class pre-tool policy input, or broaden policy coverage for another
    trust-relevant MCP input.

### e2b92a9 - Advertise Pre-Tool Input Schemas

- Task: make generated Codex/OpenCode bridge metadata explicitly advertise the
  shared pre-tool policy input schema and platform event optional tool inputs.
- Planning source:
  - previous ledger recommendation to advertise `human_checkpoint_id` as a
    first-class pre-tool policy input;
  - v5 rule that adapters should consume machine-readable public surfaces and
    sidecars, not scrape Markdown or generated summaries.
- Changed files:
  - `brain/v5/hook_entrypoint_schemas.py`
  - `brain/v5/hook_install_templates.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/hook_bridge_markdown.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - generated bridge payloads and JSON sidecars include
    `pre_tool_policy_entrypoint.input_schema`;
  - generated bridge payloads and JSON sidecars include
    `pre_tool_event_entrypoint.platform_event_schema`;
  - the schemas name `risk_level` and optional `human_checkpoint_id` as
    adapter-discoverable policy inputs while typed kernel records remain
    authoritative.
- Tests:
  - Codex bridge generation asserts the policy input schema, event schema,
    sidecar schema, and Markdown orientation text;
  - OpenCode bridge generation asserts the same plugin bridge schema metadata;
  - public-surface validators accept only bridge fixtures with the schema
    metadata required by the contract.
- Verification:
  - red tests failed as expected with missing `input_schema` and missing
    `platform_event_schema` in generated bridge payloads;
  - focused surface/adapter/boundary set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    56 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 332 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - schemas advertise the current policy/event shape, but do not prove native
    Codex/OpenCode hosts have wired lifecycle callbacks.
- Next recommended task:
  - broaden pre-tool policy coverage for another trust-relevant MCP input, or
    add host-side installation documentation/tests for the next native hook API.

### a901ccd - Gate Execute Tool Through Pre-Tool Policy

- Task: broaden shared pre-tool policy coverage to `execute_tool`, which was
  already listed as a trust-changing runtime action.
- Planning source:
  - previous ledger recommendation to broaden pre-tool policy coverage for
    another trust-relevant MCP input;
  - v5 invariant that tool execution producing tool/evidence records must not be
    driven by orientation-only summary/progress surfaces.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `execute_tool` participates in context-aware pre-tool policy evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive `execute_tool`;
  - generated bridge gate protocols now include `execute_tool`;
  - Codex/OpenCode platform pre-tool event normalization can infer
    `execute_tool` from `aitp_v5_execute_tool`.
- Tests:
  - MCP pre-tool policy blocks `execute_tool` when sourced from progress
    orientation;
  - adapter pre-tool event path infers `execute_tool` from the MCP tool name and
    blocks the same orientation-sourced execution through bridge gate metadata.
- Verification:
  - red tests failed as expected: direct MCP policy allowed summary-sourced
    `execute_tool`, and adapter event normalization could not infer
    `aitp_v5_execute_tool`;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py::test_mcp_pre_tool_policy_blocks_execute_tool_from_progress_source tests/test_v5_adapters.py::test_mcp_adapter_pre_tool_event_infers_execute_tool_policy -q`:
    2 passed;
  - focused surface/adapter/boundary set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    68 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 334 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring.
- Next recommended task:
  - broaden pre-tool policy coverage for the next trust-relevant MCP input, or
    add host-side installation documentation/tests for native hook APIs.

### e02ec54 - Gate Subagent Result Ingestion Through Pre-Tool Policy

- Task: broaden shared pre-tool policy coverage to
  `ingest_subagent_result`, which was already listed as a trust-changing
  runtime action.
- Planning source:
  - previous ledger recommendation to broaden pre-tool policy coverage for the
    next trust-relevant MCP input;
  - v5 invariant that subagent outputs are bounded evidence/proposals and must
    not become trust changes when sourced from orientation-only summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `brain/v5/hook_bridge_markdown.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `ingest_subagent_result` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive subagent result ingestion;
  - generated bridge gate protocols now include `ingest_subagent_result`;
  - Codex/OpenCode platform pre-tool event normalization can infer
    `ingest_subagent_result` from `aitp_v5_ingest_subagent_result`;
  - platform event schema metadata advertises optional nested `packet` input,
    allowing adapters to discover where subagent packet context may live.
- Tests:
  - MCP pre-tool policy blocks `ingest_subagent_result` when sourced from
    findings orientation;
  - adapter pre-tool event path infers `ingest_subagent_result` from the MCP
    tool name, reads `claim_id` from nested `packet`, and blocks the same
    orientation-sourced ingestion through bridge gate metadata;
  - Codex/OpenCode bridge schema tests assert optional `packet` metadata.
- Verification:
  - red tests failed as expected: direct MCP policy allowed summary-sourced
    `ingest_subagent_result`, and adapter event normalization could not infer
    `aitp_v5_ingest_subagent_result`;
  - bridge schema red test failed as expected because generated platform event
    metadata did not advertise optional nested `packet` input;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py::test_mcp_pre_tool_policy_blocks_subagent_ingestion_from_findings_source tests/test_v5_adapters.py::test_mcp_adapter_pre_tool_event_infers_subagent_ingestion_policy -q`:
    2 passed;
  - bridge schema green set:
    `python -m pytest tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_codex_bridge_from_packet tests/test_v5_adapters.py::test_opencode_plugin_bridge_is_rendered_from_installation_template tests/test_v5_adapters.py::test_cli_adapter_hook_bridge_writes_opencode_bridge_from_packet tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_codex_hook_bridge tests/test_v5_public_surfaces.py::test_public_surface_validator_accepts_opencode_plugin_bridge -q`:
    5 passed;
  - focused surface/adapter/boundary set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    70 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 336 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - live external-subagent execution adapters still need integration tests.
- Next recommended task:
  - broaden pre-tool policy coverage for validation-contract or promotion-packet
    creation inputs, or add native hook installer documentation/tests.

### bd2f3eb - Gate Validation Contract Creation Through Pre-Tool Policy

- Task: give `create_validation_contract` its own pre-tool gate action instead
  of treating the MCP entrypoint as `validate_claim`.
- Planning source:
  - previous ledger recommendation to broaden pre-tool policy coverage for
    validation-contract creation inputs;
  - v5 invariant that validation contracts shape later trust decisions and must
    not be created from orientation-only summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `create_validation_contract` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive validation contract creation;
  - generated bridge gate protocols now include `create_validation_contract`;
  - Codex/OpenCode platform pre-tool event normalization now maps
    `aitp_v5_create_validation_contract` to `create_validation_contract`
    instead of `validate_claim`.
- Tests:
  - MCP pre-tool policy blocks `create_validation_contract` when sourced from
    findings orientation;
  - adapter pre-tool event path infers `create_validation_contract` from the MCP
    tool name and blocks the same orientation-sourced contract creation through
    bridge gate metadata.
- Verification:
  - red tests failed as expected: direct MCP policy allowed summary-sourced
    `create_validation_contract`, and adapter event normalization mapped
    `aitp_v5_create_validation_contract` to `validate_claim`;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py::test_mcp_pre_tool_policy_blocks_validation_contract_from_findings_source tests/test_v5_adapters.py::test_mcp_adapter_pre_tool_event_infers_validation_contract_policy -q`:
    2 passed;
  - focused surface/adapter/boundary set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    72 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 338 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - promotion-packet creation still needs a separate pre-tool coverage pass.
- Next recommended task:
  - broaden pre-tool policy coverage for `create_promotion_packet`, or add
    native hook installer documentation/tests.

### 85df059 - Gate Promotion Packet Creation Through Pre-Tool Policy

- Task: give `create_promotion_packet` its own pre-tool gate action instead of
  treating the MCP entrypoint as `promote_to_l2`.
- Planning source:
  - previous ledger recommendation to broaden pre-tool policy coverage for
    promotion-packet creation;
  - v5 invariant that proposed L2 memory packets shape future durable memory and
    must not be created from orientation-only summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/hooks.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_bridge_runtime.py`
  - `tests/test_v5_hooks.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `create_promotion_packet` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive promotion-packet creation;
  - generated bridge gate protocols now include `create_promotion_packet`;
  - Codex/OpenCode platform pre-tool event normalization now maps
    `aitp_v5_create_promotion_packet` to `create_promotion_packet` instead of
    `promote_to_l2`.
  - Claude Code `PreToolUse` maps `aitp_v5_create_promotion_packet` through
    `create_promotion_packet`, preserving the same evidence-ref gate in native
    hook output;
  - adapter `trust_changing_actions` / `requires_kernel_call_before` now list
    validation-contract and promotion-packet creation alongside the existing
    trust-relevant actions.
- Tests:
  - MCP pre-tool policy blocks `create_promotion_packet` when sourced from
    findings orientation;
  - MCP pre-tool policy blocks `create_promotion_packet` without evidence refs;
  - adapter pre-tool event path infers `create_promotion_packet` from the MCP
    tool name and blocks the same orientation-sourced packet creation through
    bridge gate metadata.
  - Codex/OpenCode bridge runtime tests assert the independent
    `create_promotion_packet` gate action for platform MCP calls;
  - Claude hook test asserts native hook output names `create_promotion_packet`
    while still denying missing evidence refs;
  - adapter packet tests assert validation-contract and promotion-packet
    creation are advertised as kernel-gated trust-relevant actions.
- Verification:
  - red tests failed as expected: direct MCP policy allowed summary-sourced
    `create_promotion_packet`, adapter event normalization mapped the MCP call
    to `promote_to_l2`, and adapter protocol payloads omitted
    validation-contract/promotion-packet creation from the kernel-gated action
    list;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py -q -k "promotion_packet"`:
    2 passed;
  - bridge/hook target set:
    `python -m pytest tests/test_v5_bridge_runtime.py -q -k "promotion_packet or maps_mcp_call_to_gate_policy or maps_plugin_call_to_gate_policy"`:
    2 passed;
  - Claude hook target set:
    `python -m pytest tests/test_v5_hooks.py -q -k "promotion_without_evidence_refs"`:
    1 passed;
  - adapter protocol target set:
    `python -m pytest tests/test_v5_adapters.py -q -k "orientation_summaries_and_trusted_brief or tampered_summary"`:
    2 passed;
  - focused policy/adapter/bridge/hook set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_bridge_runtime.py tests/test_v5_hooks.py -q`:
    73 passed;
  - focused surface/boundary set:
    `python -m pytest tests/test_v5_public_surfaces.py tests/test_v5_architecture_boundaries.py -q`:
    25 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 341 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring.
- Next recommended task:
  - add host-side installation documentation/tests for native hook APIs, or
    broaden pre-tool policy coverage for the next uncovered trust-relevant MCP
    input.

### f9de0f2 - Gate Promotion Packet Application Through Pre-Tool Policy

- Task: give `apply_promotion_packet` its own pre-tool gate action instead of
  treating the MCP entrypoint as generic `promote_to_l2`.
- Planning source:
  - previous ledger recommendation to broaden pre-tool coverage for the next
    uncovered trust-relevant MCP input;
  - v5 invariant that applying a promotion packet creates durable L2 memory and
    must be distinguishable from creating a packet or generic promotion intent.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/hooks.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `apply_promotion_packet` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive promotion-packet application;
  - generated bridge gate protocols now include `apply_promotion_packet` with
    `human_checkpoint_required=true` and required typed refs
    `packet_id`/`checkpoint_id`;
  - Codex/OpenCode platform pre-tool event normalization now maps
    `aitp_v5_apply_promotion_packet` to `apply_promotion_packet` instead of
    `promote_to_l2`;
  - adapter event schemas advertise optional `checkpoint_id` so promotion
    application can pass the actual approval identifier without prose parsing;
  - Claude Code `PreToolUse` maps `aitp_v5_apply_promotion_packet` through
    `apply_promotion_packet` and emits machine-readable `policy_reasons` in the
    `aitp` hook payload.
- Tests:
  - MCP pre-tool policy blocks `apply_promotion_packet` when sourced from
    findings orientation;
  - adapter pre-tool event path infers `apply_promotion_packet` from the MCP
    tool name and blocks summary-sourced application through bridge gate
    metadata;
  - adapter packet tests assert `apply_promotion_packet` is advertised as a
    kernel-gated trust-relevant action;
  - Claude hook test asserts native hook output names `apply_promotion_packet`
    and includes machine-readable summary-source policy reasons.
- Verification:
  - red tests failed as expected: direct MCP policy allowed summary-sourced
    `apply_promotion_packet`, adapter event normalization mapped
    `aitp_v5_apply_promotion_packet` to `promote_to_l2`, Claude hook output
    named the coarse action, and adapter protocol payloads omitted
    `apply_promotion_packet` from the kernel-gated action list;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py -q -k "apply_promotion_packet"`:
    1 passed;
  - adapter target set:
    `python -m pytest tests/test_v5_adapters.py -q -k "apply_promotion_packet_policy or orientation_summaries_and_trusted_brief or tampered_summary or hook_bridge_writes_codex"`:
    4 passed;
  - Claude hook target set:
    `python -m pytest tests/test_v5_hooks.py -q -k "apply_promotion_packet"`:
    1 passed;
  - focused policy/adapter/hook/public/bridge set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_bridge_runtime.py -q`:
    95 passed;
  - focused boundary/runtime/runner set:
    `python -m pytest tests/test_v5_architecture_boundaries.py tests/test_v5_runtime_entrypoints.py tests/test_v5_adapter_event_runner.py -q`:
    12 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 344 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring.
- Next recommended task:
  - add host-side installation documentation/tests for native hook APIs, or
    continue scanning remaining public MCP inputs for pre-tool policy gaps.

### 9066c34 - Gate Human Checkpoint Request/Decision Through Pre-Tool Policy

- Task: make typed human checkpoint request/decision actions first-class
  pre-tool/gate actions instead of leaving them as record-only MCP writes.
- Planning source:
  - v5 invariant that trust-changing actions must go through typed kernel
    records, pre-tool policy, validation, or explicit human checkpoint records;
  - previous ledger recommendation to continue scanning remaining public MCP
    inputs for pre-tool policy gaps;
  - human checkpoints are the authorization boundary for risky research steps,
    so the request/decision records themselves must not be driven by generated
    summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/hooks.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - `request_human_checkpoint` and `decide_human_checkpoint` participate in
    context-aware pre-tool policy evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive checkpoint request or decision records;
  - adapter `trust_changing_actions` and `requires_kernel_call_before` include
    checkpoint request/decision actions;
  - generated bridge `runtime_gate_protocols` include checkpoint request and
    decision sequences with `evaluate_pre_tool_policy` before the typed write;
  - Codex/OpenCode platform event normalization maps the checkpoint MCP tool
    names to explicit v5 actions;
  - Claude Code `PreToolUse` maps checkpoint MCP calls through the shared
    typed-record-backed policy path, so summary-sourced approvals are denied
    before the MCP tool runs.
- Tests:
  - MCP pre-tool policy blocks summary/task-plan sourced checkpoint request;
  - MCP pre-tool policy blocks findings-sourced checkpoint decision;
  - adapter pre-tool event path infers checkpoint request/decision actions from
    MCP tool names and returns the bridge gate protocol;
  - Claude hook test denies a summary-sourced checkpoint approval attempt.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "human_checkpoint_request_policy or human_checkpoint_decision_policy or human_checkpoint_request_from_task_plan_source or human_checkpoint_decision_from_findings_source or summary_sourced_human_checkpoint_decision"`:
    5 failed because direct policy returned `log`, adapter runtime could not
    infer checkpoint actions, and Claude hook allowed the decision;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "human_checkpoint_request_policy or human_checkpoint_decision_policy or human_checkpoint_request_from_task_plan_source or human_checkpoint_decision_from_findings_source or summary_sourced_human_checkpoint_decision"`:
    5 passed;
  - focused related set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py -q`:
    128 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 349 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - pre-tool coverage still does not cover every possible public MCP input or
    active risk dimension.
- Next recommended task:
  - continue scanning remaining public MCP inputs for pre-tool policy gaps, or
    add host-side installation documentation/tests for native hook APIs.

### c2a99ab - Gate Code State Recording Through Pre-Tool Policy

- Task: make `record_code_state` a first-class pre-tool/gate action rather than
  leaving code provenance writes as record-only MCP calls.
- Planning source:
  - v5 invariant that typed kernel records are authoritative and summaries are
    orientation-only;
  - formula-code translation and numerical validation require trustworthy code
    provenance before code-method claims can be validated;
  - previous ledger recommendation to continue scanning public MCP inputs for
    pre-tool policy gaps.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - `record_code_state` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive code-state provenance records;
  - adapter `trust_changing_actions` and `requires_kernel_call_before` include
    `record_code_state`;
  - generated bridge `runtime_gate_protocols` include a `record_code_state`
    sequence with `evaluate_pre_tool_policy` before the typed write;
  - Codex/OpenCode platform event normalization maps
    `aitp_v5_record_code_state` to the explicit v5 action;
  - Claude Code `PreToolUse` maps code-state MCP calls through the shared
    typed-record-backed policy path.
- Tests:
  - MCP pre-tool policy blocks progress-summary sourced code-state recording;
  - adapter pre-tool event path infers `record_code_state` from the MCP tool
    name and returns the bridge gate protocol;
  - Claude hook test denies a summary-sourced code-state recording attempt;
  - adapter packet tests assert `record_code_state` is advertised as a
    kernel-gated trust-relevant action.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "code_state_from_progress_source or infers_code_state_policy or summary_sourced_code_state"`:
    3 failed because direct policy returned `log`, adapter runtime could not
    infer `record_code_state`, and Claude hook allowed the call;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "code_state_from_progress_source or infers_code_state_policy or summary_sourced_code_state"`:
    3 passed;
  - focused related set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py -q`:
    131 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 352 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - pre-tool coverage still does not cover every public MCP input or every
    active risk dimension.
- Next recommended task:
  - continue scanning remaining public MCP inputs for pre-tool policy gaps,
    especially reference/physics-object/sensemaking writes, or add host-side
    installation documentation/tests for native hook APIs.

### f9efbf7 - Gate Physics Object Graph Writes Through Pre-Tool Policy

- Task: make `record_physics_object` and `record_object_relation` first-class
  pre-tool/gate actions instead of leaving object-graph writes as record-only
  MCP calls.
- Planning source:
  - v5 invariant that typed kernel records are authoritative and summaries are
    orientation-only;
  - physics objects and object relations feed known context, mandatory
    reflection, and later theoretical reasoning, so they must not be written
    directly from generated summaries;
  - previous ledger recommendation to scan reference/physics-object/sensemaking
    writes for pre-tool gaps.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - `record_physics_object` and `record_object_relation` participate in
    context-aware pre-tool policy evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive physics-object or object-relation records;
  - adapter `trust_changing_actions` and `requires_kernel_call_before` include
    both object-graph write actions;
  - generated bridge `runtime_gate_protocols` include physics-object and
    object-relation sequences with `evaluate_pre_tool_policy` before the typed
    write;
  - Codex/OpenCode platform event normalization maps
    `aitp_v5_record_physics_object` and `aitp_v5_record_object_relation` to
    explicit v5 actions;
  - Claude Code `PreToolUse` maps object-graph MCP calls through the shared
    typed-record-backed policy path.
- Tests:
  - MCP pre-tool policy blocks findings-sourced physics-object recording;
  - MCP pre-tool policy blocks task-plan-sourced object-relation recording;
  - adapter pre-tool event path infers both object-graph actions from MCP tool
    names and returns the bridge gate protocol;
  - Claude hook test denies a summary-sourced object-relation write attempt;
  - adapter packet tests assert both actions are advertised as kernel-gated
    trust-relevant actions.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "physics_object_from_findings_source or object_relation_from_task_plan_source or infers_physics_object_policy or infers_object_relation_policy or summary_sourced_object_relation"`:
    5 failed because direct policy returned `log`, adapter runtime could not
    infer the object-graph actions, and Claude hook allowed the relation write;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "physics_object_from_findings_source or object_relation_from_task_plan_source or infers_physics_object_policy or infers_object_relation_policy or summary_sourced_object_relation"`:
    5 passed;
  - focused related set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_physics_objects.py -q`:
    147 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 357 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - pre-tool coverage still does not cover every public MCP input or every
    active risk dimension.
- Next recommended task:
  - continue with remaining public write surfaces such as
    `record_reference_location` and `record_sensemaking_report`, or add
    host-side installation documentation/tests for native hook APIs.

### 7b6cec2 - Gate Reference And Sensemaking Writes Through Pre-Tool Policy

- Task: make `record_reference_location` and `record_sensemaking_report`
  first-class pre-tool/gate actions instead of leaving them as record-only MCP
  writes.
- Planning source:
  - v5 invariant that typed kernel records are authoritative and generated
    summaries, task plans, findings files, progress files, and external-note
    pointers are orientation-only;
  - reference locations are not evidence by themselves, but they still become
    typed research context and should not be created directly from generated
    summaries;
  - sensemaking reports steer future theoretical interpretation, so they must
    go through the same pre-tool policy path as other context-shaping writes;
  - previous ledger recommendation to cover `record_reference_location` and
    `record_sensemaking_report`.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - `record_reference_location` and `record_sensemaking_report` participate in
    context-aware pre-tool policy evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive reference-location or sensemaking-report typed records;
  - adapter `trust_changing_actions` and `requires_kernel_call_before` include
    both actions;
  - generated bridge `runtime_gate_protocols` include reference-location and
    sensemaking-report sequences with `evaluate_pre_tool_policy` before the
    typed write;
  - Codex/OpenCode platform event normalization maps
    `aitp_v5_record_reference_location` and
    `aitp_v5_record_sensemaking_report` to explicit v5 actions;
  - Claude Code `PreToolUse` maps sensemaking/report and reference-location MCP
    calls through the shared typed-record-backed policy path.
- Tests:
  - MCP pre-tool policy blocks findings-sourced reference-location recording;
  - MCP pre-tool policy blocks progress-sourced sensemaking-report recording;
  - adapter pre-tool event path infers both actions from MCP tool names and
    returns the bridge gate protocol;
  - Claude hook test denies a summary-sourced sensemaking-report write attempt;
  - adapter packet tests assert both actions are advertised as kernel-gated
    trust-relevant actions.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "reference_location_from_findings_source or sensemaking_report_from_progress_source or infers_reference_location_policy or infers_sensemaking_report_policy or summary_sourced_sensemaking_report"`:
    5 failed because direct policy returned `log`, adapter runtime could not
    infer the actions, and Claude hook allowed the sensemaking write;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "reference_location_from_findings_source or sensemaking_report_from_progress_source or infers_reference_location_policy or infers_sensemaking_report_policy or summary_sourced_sensemaking_report"`:
    5 passed;
  - focused related set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_reference_locations.py tests/test_v5_sensemaking.py -q`:
    153 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 362 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - pre-tool coverage still does not cover every public MCP input or every
    active risk dimension;
  - reference-location records remain pointers, not evidence or validation.
- Next recommended task:
  - audit remaining MCP write surfaces against the pre-tool policy/gate list,
    then either close the current policy-coverage pass or add the next missing
    trust-relevant write surface.

### 4273be0 - Gate Tool Recipe Registration Through Pre-Tool Policy

- Task: make `register_tool_recipe` a first-class pre-tool/gate action instead
  of leaving tool-recipe creation as a record-only MCP write.
- Planning source:
  - v5 invariant that fixed tool-layer behavior and validation recipes must be
    typed records, not generated summary claims;
  - tool recipes shape future numerical, literature, and formal-theory checks,
    so a summary-generated recipe should not become durable kernel context
    without the same pre-tool policy path as other context-shaping writes;
  - previous ledger recommendation to audit remaining MCP write surfaces.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/gate_protocols.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_hooks.py`
- Public/runtime behavior changes:
  - `register_tool_recipe` participates in context-aware pre-tool policy
    evaluation;
  - summary/task-plan/findings/progress orientation surfaces cannot directly
    drive tool-recipe registration;
  - adapter `trust_changing_actions` and `requires_kernel_call_before` include
    `register_tool_recipe`;
  - generated bridge `runtime_gate_protocols` include a tool-recipe sequence
    with `evaluate_pre_tool_policy` before the typed write;
  - Codex/OpenCode platform event normalization maps
    `aitp_v5_register_tool_recipe` to the explicit v5 action;
  - Claude Code `PreToolUse` maps tool-recipe MCP calls through the shared
    typed-record-backed policy path.
- Tests:
  - MCP pre-tool policy blocks findings-sourced tool-recipe registration;
  - adapter pre-tool event path infers `register_tool_recipe` from the MCP tool
    name and returns the bridge gate protocol;
  - Claude hook test denies a summary-sourced tool-recipe registration attempt;
  - adapter packet tests assert the action is advertised as a kernel-gated
    trust-relevant action.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "tool_recipe_from_findings_source or infers_tool_recipe_policy or summary_sourced_tool_recipe"`:
    3 failed because direct policy returned `log`, adapter runtime could not
    infer the action, and Claude hook allowed the write;
  - target green set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py -q -k "tool_recipe_from_findings_source or infers_tool_recipe_policy or summary_sourced_tool_recipe"`:
    3 passed;
  - focused related set:
    `python -m pytest tests/test_v5_pretool_policy.py tests/test_v5_adapters.py tests/test_v5_hooks.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_evidence_tools.py tests/test_v5_runtime_entrypoints.py -q`:
    153 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 365 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - pre-tool coverage still does not cover every public MCP input or every
    active risk dimension;
  - registering a tool recipe remains a typed catalog write, not evidence that
    the recipe has been executed or validated.
- Next recommended task:
  - add an explicit registry consistency audit test that prevents future
    runtime record protocols from being introduced without a conscious gate
    decision.

### c10ecb1 - Add Record Gate Coverage Audit

- Task: expose a contracted audit showing whether runtime typed-record
  protocols have runtime gate coverage.
- Planning source:
  - v5 invariant that typed records are authoritative and generated summaries
    cannot become truth sources;
  - previous ledger recommendation to prevent future runtime record protocols
    from being introduced without a conscious gate decision;
  - project architecture rule that v5 modules stay bounded and focused.
- Changed files:
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/record_gate_audit_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_cli.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - `record_gate_coverage_audit()` reports runtime record protocols, runtime
    gate protocols, gated record actions, ungated record actions, and extra
    non-record gates from the adapter protocol registry;
  - CLI exposes `aitp-v5 adapter record-gate-audit` without initializing a v5
    workspace;
  - MCP exposes `aitp_v5_audit_record_gate_coverage`;
  - public-surface contracts validate `record_gate_coverage_audit`;
  - runtime entrypoints advertise the audit so external reviewers can discover
    it without reading implementation modules.
- Tests:
  - adapter audit reports no ungated record protocols;
  - MCP wrapper returns the contracted audit payload;
  - CLI wrapper returns the same static audit without creating `.aitp`;
  - public-surface validator accepts the audit surface;
  - runtime entrypoint catalog advertises the audit CLI/MCP/surface tuple.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_cli.py tests/test_v5_public_surfaces.py tests/test_v5_runtime_entrypoints.py -q -k "record_gate_coverage_audit or record_gate_audit or record_gate_coverage"`:
    4 failed because the helper/public surface/CLI/MCP entrypoints did not yet
    exist;
  - target green set:
    same command: 4 passed;
  - focused related set:
    `python -m pytest tests/test_v5_adapters.py tests/test_v5_cli.py tests/test_v5_public_surfaces.py tests/test_v5_contracts.py tests/test_v5_runtime_entrypoints.py tests/test_v5_architecture_boundaries.py -q`:
    122 passed after moving the audit contract into
    `record_gate_audit_contracts.py` to keep modules within the 500-line v5
    architecture boundary;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 369 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - the audit proves registry coverage, not semantic correctness of every gate;
  - native Codex/OpenCode hosts still need true lifecycle installer wiring;
  - active risk dimensions beyond current pre-tool inputs remain partial.
- Next recommended task:
  - use the new audit as a guard while moving to the next remaining v5 gap:
    native hook lifecycle wiring, migration completeness, or broader active-risk
    policy inputs.

### 2c52781 - Migrate Legacy L3 Process Notes

- Task: preserve old-topic L3 process artifacts during explicit v5 migration,
  not only final L3 candidates and L4 reviews.
- Planning source:
  - goal invariant that old topic content should migrate into v5 typed records
    rather than remain a long-term compatibility truth source;
  - user concern that research process, wrong attempts, gap audits, and
    derivation work must not disappear when old topics move into the new
    architecture;
  - architecture-boundary constraint that v5 modules should stay small.
- Changed files:
  - `brain/v5/legacy_bridge.py`
  - `brain/v5/legacy_l3_process_records.py`
  - `tests/test_v5_legacy_bridge.py`
- Public/runtime behavior changes:
  - legacy migration dry-run now maps L3 process notes under `L3/ideate`,
    `L3/plan`, `L3/derive`, `L3/trace-derivation`, `L3/gap-audit`,
    `L3/diagnose`, `L3/integrate`, `L3/distill`, and `L3/runs`;
  - explicit migration converts those notes into `legacy_l3_*_process_note`
    evidence records plus linked sensemaking reports on the active migrated
    claim;
  - migrated reports carry `review_legacy_l3_process_note` as the next action,
    making old derivation routes, failed comparisons, and gap-audit findings
    visible for v5 review before any trust promotion.
- Tests:
  - dry-run maps `L3/derive/active_derivation.md`,
    `L3/gap-audit/active_gaps.md`, and `L3/diagnose/failed-route.md`;
  - migration writes typed evidence for derive, gap-audit, and diagnose process
    notes;
  - migration writes sensemaking reports preserving the note summaries and
    provenance refs.
- Verification:
  - red test failed as expected:
    `python -m pytest tests\test_v5_legacy_bridge.py -q -k "l3_process"`:
    1 failed with `KeyError: 'L3/derive/active_derivation.md'`;
  - target green set:
    same command: 1 passed;
  - focused related set:
    `python -m pytest tests\test_v5_legacy_bridge.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    76 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 370 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - migrated process notes preserve summaries and provenance refs; full
    original prose remains available through the referenced legacy file until a
    future archival-content-copy policy is defined;
  - old process notes are imported as `legacy_seed` evidence, not validation or
    L2 memory.
- Next recommended task:
  - continue migration completeness by deciding whether old L3 process-note
    bodies should be copied into v5 archival records or remain provenance-linked
    summaries, then move to the next gap if that policy is intentionally deferred.

### 173fa1a - Archive Legacy L3 Process Bodies

- Task: reduce long-term dependence on legacy topic files by copying migrated L3
  process-note bodies into v5 typed evidence Markdown, not just preserving
  summaries and provenance refs.
- Planning source:
  - goal invariant that legacy content should migrate into v5 typed records;
  - previous residual risk that process-note migration preserved only summaries
    plus `legacy_l3_process:*` source refs;
  - user requirement that wrong attempts, derivation paths, and gap-audit
    process should remain detailed in the new architecture.
- Changed files:
  - `brain/v5/evidence.py`
  - `brain/v5/legacy_l3_process_records.py`
  - `tests/test_v5_legacy_bridge.py`
- Public/runtime behavior changes:
  - `record_evidence` accepts an optional explicit Markdown `body` while keeping
    the previous summary-only default for existing callers;
  - legacy L3 process-note migration writes evidence bodies with source path and
    a `Migrated Legacy Body` section containing the original legacy Markdown
    body;
  - process-note evidence remains `legacy_seed` and still requires v5 review
    before validation or promotion.
- Tests:
  - legacy L3 process migration now asserts that derive, gap-audit, and diagnose
    evidence files contain the original legacy note prose after migration.
- Verification:
  - red test failed as expected:
    `python -m pytest tests\test_v5_legacy_bridge.py -q -k "l3_process"`:
    1 failed because the migrated evidence body only contained `# Evidence` and
    the summary;
  - target green set:
    same command: 1 passed;
  - focused related set:
    `python -m pytest tests\test_v5_legacy_bridge.py tests\test_v5_evidence_tools.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    82 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 370 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - this archives L3 process-note bodies, but L1 and L4 legacy evidence still
    mainly preserve summaries plus provenance refs unless separately expanded;
  - very large legacy process artifacts may eventually need artifact-reference
    policy rather than inline Markdown bodies.
- Next recommended task:
  - either extend archival-body migration to L1/L4 legacy artifacts, or switch
    to the next planned implementation gap: native Codex/OpenCode lifecycle
    hook wiring.

### b2af15a - Archive Legacy L1 And L4 Bodies

- Task: extend legacy archival-body migration beyond L3 process notes so L1
  understanding artifacts and L4 reviews also carry their original Markdown
  bodies inside v5 typed evidence files.
- Planning source:
  - goal invariant that old topic content should migrate into v5 typed records,
    not remain a long-term legacy truth source;
  - previous ledger residual risk that L1 and L4 evidence still mainly
    preserved summaries plus provenance refs;
  - user requirement that reading/framing context and validation reviews remain
    detailed after migration.
- Changed files:
  - `brain/v5/legacy_bridge.py`
  - `brain/v5/legacy_migration_records.py`
  - `brain/v5/legacy_record_bodies.py`
  - `tests/test_v5_legacy_bridge.py`
- Public/runtime behavior changes:
  - added a shared legacy evidence Markdown body builder;
  - L1 source basis, convention snapshot, derivation anchors, contradiction
    register, question contract, and intake notes now write migrated legacy
    bodies into v5 evidence Markdown;
  - L4 review evidence now writes the review body into v5 evidence Markdown;
  - imported records remain `legacy_seed` and require v5 review before
    validation or promotion.
- Tests:
  - L1 source-basis/convention migration asserts the migrated evidence Markdown
    contains original source/convention prose;
  - L4 review migration asserts the migrated evidence Markdown contains the
    original review prose.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_legacy_bridge.py -q -k "converts_all_candidates_and_reviews or source_basis_and_conventions"`:
    2 failed because evidence bodies only contained `# Evidence` plus summary;
  - target green set:
    same command: 2 passed;
  - focused related set:
    `python -m pytest tests\test_v5_legacy_bridge.py tests\test_v5_evidence_tools.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    82 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 370 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - migrated source path placeholders (`legacy_source`) still preserve paths and
    reference-location metadata, not full PDF/source file content;
  - very large legacy bodies may need future artifact-ref policy instead of
    inline archival bodies.
- Next recommended task:
  - move from legacy migration completeness back to native Codex/OpenCode
    lifecycle hook wiring, because the main remaining goal gap is runtime host
    integration rather than typed-record migration.

### 27dc47c - Add Codex/OpenCode Post-Tool Fixture Runners

- Task: extend generated Codex/OpenCode stdin-runner installation fixtures from
  pre-tool policy only to pre-tool plus post-tool lifecycle coverage.
- Planning source:
  - hook-installation plan requires post-tool trace events to stay process
    history only, not evidence/trust;
  - next-agent plan identified native Codex/OpenCode lifecycle hook wiring as a
    remaining gap;
  - goal invariant that generated fixture files are runtime metadata and typed
    kernel records remain authoritative.
- Changed files:
  - `brain/v5/hook_fixture_templates.py`
  - `brain/v5/hook_install_contracts.py`
  - `hooks/aitp_v5_adapter_event_runner.py`
  - `tests/test_v5_adapter_event_runner.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - Codex fixtures now include `hooks.post_tool` pointing to
    `hooks/aitp_v5_adapter_event_runner.py post-tool`;
  - OpenCode fixtures now include `plugin_hooks.post_tool` pointing to the same
    runner with `--runtime opencode`;
  - the adapter event runner can persist post-tool trace events through
    `persist_hook_trace_event`, returning the contracted
    `hook_trace_event_record` public surface;
  - post-tool defaults are derived from the active session binding when the host
    event omits `topic_id` or `claim_id`;
  - installation contracts now require both pre-tool and post-tool hook entries.
- Tests:
  - CLI/MCP fixture tests assert post-tool hook metadata, non-blocking behavior,
    and `append_trace_event` state mutation;
  - runner tests execute Codex/OpenCode post-tool fixture commands and verify
    `.aitp/runtime/hook_trace_events.jsonl` receives the trace event.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_adapter_event_runner.py -q -k "install_fixture or install_hooks"`:
    4 failed because generated fixtures did not contain `post_tool`;
  - target green set:
    same command: 7 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_adapter_event_runner.py tests\test_v5_hooks.py tests\test_v5_trace_audit.py tests\test_v5_public_surfaces.py tests\test_v5_architecture_boundaries.py -q`:
    107 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 372 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - this is still generated fixture metadata, not a true Codex/OpenCode native
    installer API integration;
  - platform-specific event schemas may need additional normalization once real
    host events are available.
- Next recommended task:
  - add explicit native-lifecycle adapter installation docs/tests for the actual
    Codex/OpenCode host surfaces, or continue broadening pre-tool policy
    coverage for remaining trust-relevant MCP inputs.

### 234381a - Require Validation Contracts For High-Risk Tool Execution

- Task: add a risk-triggered pre-tool policy gate so rigorous/adversarial tool
  execution cannot proceed without a typed validation plan.
- Planning source:
  - user requirement that AITP should not rely on uncontrolled model intuition
    for correctness-critical steps;
  - next-agent plan residual gap that pre-tool policy did not cover every active
    risk dimension;
  - hook-installation rule that runtime/hook decisions must delegate to typed
    kernel records, not generated summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/adapter_protocols.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - `aitp-v5 policy pre-tool ...` and `aitp_v5_evaluate_pre_tool_policy` accept
    `validation_contract_ids`;
  - `pre_tool_policy_decision` now reports the resolved open
    `validation_contract_ids`;
  - rigorous/adversarial `execute_tool` and `record_tool_run` are hard-blocked
    unless at least one provided validation contract is open and belongs to the
    active claim;
  - Codex/OpenCode pre-tool event normalization now forwards
    `validation_contract_ids` from platform tool input;
  - bridge schemas and record/gate protocol metadata advertise validation
    contracts as accepted typed refs for tool execution.
- Tests:
  - MCP policy blocks rigorous `execute_tool` without a validation contract;
  - MCP and CLI policy allow rigorous `execute_tool` when an open typed
    validation contract is provided;
  - adapter pre-tool events block/allow rigorous `execute_tool` based on
    `validation_contract_ids`.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_pretool_policy.py tests\test_v5_adapters.py -q -k "validation_contract_id or rigorous_execute"`:
    5 failed because rigorous tool execution was allowed and CLI/MCP/adapter
    surfaces did not accept `validation_contract_ids`;
  - target green set:
    same command: 5 passed;
  - focused related set:
    `python -m pytest tests\test_v5_pretool_policy.py tests\test_v5_adapters.py tests\test_v5_hooks.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py tests\test_v5_validation.py tests\test_v5_architecture_boundaries.py -q`:
    179 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 377 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - current policy checks that the supplied contract is open and claim-linked,
    but does not yet inspect whether its required checks match the exact tool
    recipe/executor;
  - native host events may need additional platform-specific field aliases for
    validation-contract IDs.
- Next recommended task:
  - either deepen the validation-contract/tool-recipe match, or continue toward
    true native Codex/OpenCode lifecycle installer wiring.

### acddfa1 - Bind Validation Contracts To Concrete Tools

- Task: deepen the high-risk tool gate so an arbitrary open claim-linked
  validation contract cannot authorize a different tool path.
- Planning source:
  - previous ledger residual risk that validation contracts did not inspect
    whether required checks matched the exact tool recipe/executor;
  - user requirement that AITP should force actual physicist-style verification
    instead of letting an AI pass a gate with a generic plan;
  - v5 invariant that typed kernel records, not generated summaries or model
    intuition, authorize trust-relevant work.
- Changed files:
  - `brain/v5/models.py`
  - `brain/v5/validation.py`
  - `brain/v5/record_contracts.py`
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `brain/v5/adapter_protocols.py`
  - `tests/test_v5_validation.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - `ValidationContractRecord` now carries `tool_recipe_ids` and
    `executor_ids`;
  - `aitp-v5 validation contract create` accepts `--recipe-id` and
    `--executor-id`;
  - `aitp_v5_create_validation_contract` accepts `tool_recipe_ids` and
    `executor_ids`;
  - `aitp-v5 policy pre-tool` accepts `--recipe` and `--executor`;
  - `aitp_v5_evaluate_pre_tool_policy`, bridge lifecycle evaluation, and
    Codex/OpenCode platform event normalization pass `recipe_id` and
    `executor_id` into the typed policy decision;
  - rigorous/adversarial `execute_tool` requires a provided open validation
    contract for the active claim whose `tool_recipe_ids` contains the current
    `recipe_id` and whose `executor_ids` contains the current `executor_id`;
  - rigorous/adversarial `record_tool_run` requires a provided open validation
    contract for the active claim whose `tool_recipe_ids` contains the current
    `recipe_id`;
  - generated hook/adapter schemas advertise optional `recipe_id` and
    `executor_id`, keeping the bridge machine-readable while preserving
    `summary_inputs_trusted=false`.
- Tests:
  - validation contract creation stores and exposes recipe/executor bindings
    through kernel, CLI, and MCP paths;
  - MCP pre-tool policy blocks rigorous `execute_tool` when the supplied
    validation contract is unbound to the requested recipe/executor;
  - MCP and CLI pre-tool policy allow rigorous `execute_tool` only when the
    supplied contract binds the requested recipe/executor;
  - adapter pre-tool event normalization blocks unbound rigorous tool
    execution and allows the bound case.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_adapters.py -q -k "validation_contract_id or rigorous_execute or recipe_id or executor_id or unbound"`:
    5 failed because validation contracts and policy calls did not yet accept
    `tool_recipe_ids`/`executor_ids`/`recipe_id`/`executor_id`, and the adapter
    allowed an unbound contract;
  - target green set:
    same command: 7 passed;
  - focused related set:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_adapters.py tests\test_v5_hooks.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py -q`:
    181 passed;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 379 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - the binding proves that the validation contract names the current tool
    identity, but it does not yet semantically verify that every required check
    is sufficient for the physics claim;
  - real host adapters may expose recipe/executor aliases beyond the current
    `recipe_id`/`recipe` and `executor_id`/`executor` forms.
- Next recommended task:
  - add a typed post-tool validation-result/evidence gate that checks whether a
    completed high-risk tool run satisfied the bound validation contract
    outputs before it can support a claim.

### 63b4c95 - Record Validation Results For Tool Runs

- Task: add the typed post-tool validation-result record that links a completed
  tool run back to a validation contract and its required outputs.
- Planning source:
  - previous ledger recommendation to check whether completed high-risk tool
    runs satisfied bound validation-contract outputs;
  - v5 invariant that trust-relevant validation must be recorded as typed
    kernel state, not inferred from summaries or model claims;
  - user requirement that numerical/formula-code work leave auditable evidence
    of what was checked and why it passed or failed.
- Changed files:
  - `brain/v5/models.py`
  - `brain/v5/paths.py`
  - `brain/v5/validation.py`
  - `brain/v5/record_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_validation.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_validation.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
  - `tests/test_v5_adapters.py`
  - `PROJECT_MEMORY.md`
  - `README.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - added `ValidationResultRecord` and `.aitp/registry/validation_results`;
  - added `record_validation_result` kernel logic that resolves the referenced
    contract and tool run, computes `missing_outputs`, and forbids `passed`
    results with missing required outputs or observed failure modes;
  - added `validation_result_record` as a public surface;
  - added CLI `aitp-v5 validation result record ...`;
  - added MCP `aitp_v5_record_validation_result`;
  - added runtime entrypoint `record_validation_result`;
  - added pre-tool summary-source blocking for `record_validation_result`;
  - added adapter record/gate protocol metadata and Claude/Codex/OpenCode
    action inference for validation-result recording;
  - moved validation CLI parsing/dispatch into `brain/v5/cli_validation.py` so
    `brain/v5/cli.py` stays below the architecture boundary.
- Tests:
  - kernel test records a passed validation result and persists it;
  - kernel rejects `passed` when contract-required outputs are missing;
  - CLI/MCP/runtime entrypoint tests cover validation-result recording;
  - pre-tool policy blocks summary/findings-sourced validation-result writes;
  - public surface and adapter packet tests advertise the new surface and gate.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py -q -k "validation_result or record_validation_result or public_surface_registry_names_all_runtime_facing_payloads or runtime_entrypoints_advertise_typed_write_surfaces or adapter_packet_includes"`:
    7 failed because the validation-result model, kernel function, MCP wrapper,
    public surface, runtime entrypoint, pre-tool action, and adapter metadata did
    not exist;
  - target green set:
    same command: 7 passed;
  - focused related set:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py tests\test_v5_contracts.py tests\test_v5_architecture_boundaries.py tests\test_v5_hooks.py -q`:
    188 passed after moving validation CLI code into `cli_validation.py` and
    keeping `contracts.py` at the 500-line boundary;
  - full v5 regression set:
    `python -m pytest tests/test_v5_*.py -q`: 383 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - validation results currently check declared output names, not the semantic
    quality of each physics check;
  - validation results are recorded separately from evidence support, so a later
    policy should require passed validation-result refs before a high-risk tool
    run can support a claim or promotion packet.
- Next recommended task:
  - require high-risk tool-derived evidence or promotion packets to reference a
    passed `ValidationResultRecord` for the relevant `ToolRunRecord`.

### 14d2b9b - Require Passed Validation Results For Tool Evidence

- Task: prevent high-risk tool-derived evidence from supporting a claim unless
  it links the relevant tool run to a passed validation result.
- Planning source:
  - previous ledger recommendation to require passed `ValidationResultRecord`
    references before high-risk tool-derived evidence can support a claim;
  - v5 invariant that typed kernel records, not generated summaries or model
    confidence, are the authority for validation state;
  - user requirement that numerical/formula-code work leave auditable proof of
    what was checked before it is trusted.
- Changed files:
  - `brain/v5/models.py`
  - `brain/v5/evidence.py`
  - `brain/v5/record_contracts.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/mcp_evidence.py`
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/gate_protocols.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_validation.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - `EvidenceRecord` now carries `validation_result_ids`;
  - kernel, CLI, and MCP evidence recording accept validation-result links;
  - the shared CLI/MCP/runtime pre-tool policy accepts `tool_run_ids` and
    `validation_result_ids`;
  - rigorous/adversarial `record_evidence` with linked `tool_run_ids` is
    hard-blocked unless passed validation results cover the same tool runs;
  - Codex/OpenCode adapter event normalization forwards these fields;
  - hook entrypoint schemas advertise both fields;
  - Claude hook context policy forwarding now includes record-evidence,
    record-tool-run, execute-tool, subagent-ingestion, validation contract,
    tool-run, validation-result, recipe, executor, and risk context;
  - `brain/v5/mcp_evidence.py` keeps the evidence MCP wrapper out of the
    already-large `mcp_tools.py` module.
- Tests:
  - kernel/CLI/MCP evidence recording preserves `validation_result_ids`;
  - pre-tool policy blocks rigorous tool evidence without a passed validation
    result;
  - pre-tool policy accepts rigorous tool evidence with a passed matching
    validation result;
  - adapter pre-tool event normalization blocks/allows the same scenarios;
  - adapter packet and public-surface contract tests expose the new link field.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py -q -k "validation_result_id or rigorous_tool_evidence or adapter_packet_includes_orientation or typed_write_records"`:
    5 failed because MCP/policy entrypoints did not accept `tool_run_ids` or
    `validation_result_ids`, adapter protocols did not advertise the new field,
    and adapter events did not block unvalidated high-risk tool evidence;
  - target green set:
    same command: 6 passed;
  - focused related set:
    `python -m pytest tests\test_v5_validation.py tests\test_v5_pretool_policy.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_cli.py tests\test_v5_mcp_tools.py tests\test_v5_hooks.py tests\test_v5_bridge_runtime.py tests\test_v5_adapter_event_runner.py tests\test_v5_contracts.py tests\test_v5_tool_executors.py -q`:
    229 passed;
  - full v5 regression set initially failed only the module-size boundary
    because `mcp_tools.py` reached 503 lines; after extracting
    `brain/v5/mcp_evidence.py`, the boundary-focused set passed:
    `python -m pytest tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py tests\test_v5_validation.py -q`:
    41 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    388 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - the guard verifies that a passed validation result covers each linked tool
    run, but still trusts the validation-result record's declared checked
    outputs rather than independently evaluating physics semantics;
  - promotion packets can still cite evidence without separately requiring
    validation-result coverage, so promotion should get the same high-risk
    validation-result gate next.
- Next recommended task:
  - require high-risk promotion packets or memory promotion paths to reference
    passed validation results for tool-derived evidence before L2 promotion.

### 14a2f9a - Require Passed Validation Results For Promotion Packets

- Task: prevent tool-derived evidence from entering promotion packets or L2
  memory unless the promotion packet cites passed validation results for the
  same tool runs.
- Planning source:
  - previous ledger recommendation after `14d2b9b`;
  - v5 invariant that typed kernel records, not summaries or model confidence,
    are the authority for validation state;
  - user requirement that numerical/formula-code work leave auditable proof
    before a result becomes trusted research memory.
- Changed files:
  - `brain/v5/models.py`
  - `brain/v5/record_contracts.py`
  - `brain/v5/memory.py`
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/adapter_protocols.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_memory.py`
  - `tests/test_v5_pretool_policy.py`
- Public/runtime behavior changes:
  - `PromotionPacketRecord` now carries `validation_result_ids`;
  - kernel `create_promotion_packet` accepts validation-result links and rejects
    tool-derived evidence unless every linked tool run has a passed validation
    result with no missing outputs or observed failure modes;
  - `apply_promotion_packet` repeats the same validation-result guard before
    writing an L2 memory entry, so stale or manually authored packets cannot
    bypass the check;
  - CLI `promotion packet create` accepts `--validation-result-id`;
  - MCP `aitp_v5_create_promotion_packet` accepts `validation_result_ids`;
  - the shared pre-tool policy resolves typed evidence records and hard-blocks
    rigorous/adversarial promotion attempts whose tool-derived evidence lacks
    matching passed validation results;
  - adapter protocol metadata and runtime sample args advertise the new link
    field so adapters can pass it without prose scraping.
- Tests:
  - kernel rejects promotion packet creation for tool-derived evidence without
    validation-result links;
  - kernel records validation-result links on promotion packets;
  - applying a manually authored packet without links is rejected before L2
    memory write;
  - CLI/MCP promotion packet creation preserves validation-result links;
  - MCP pre-tool policy blocks rigorous promotion without passed validation
    results and allows it with matching passed results.
- Verification:
  - red tests failed as expected:
    `python -m pytest tests\test_v5_memory.py tests\test_v5_pretool_policy.py -q -k "validation_result or rigorous_promotion_packet"`:
    4 failed, 4 passed, 46 deselected because promotion packets did not carry
    `validation_result_ids` and pre-tool policy did not inspect tool-derived
    evidence records for promotion;
  - target green set:
    `python -m pytest tests\test_v5_memory.py tests\test_v5_pretool_policy.py -q -k "validation_result or promotion_cli or promotion_mcp or rigorous_promotion_packet"`:
    10 passed, 44 deselected;
  - focused related set:
    `python -m pytest tests\test_v5_memory.py tests\test_v5_pretool_policy.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_adapters.py tests\test_v5_contracts.py -q`:
    161 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    393 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - validation results still assert declared output coverage rather than
    independently judging physics correctness;
  - the direct kernel guard only triggers for evidence refs that resolve to
    typed `EvidenceRecord`s with `tool_run_ids`; placeholder or missing
    evidence refs remain governed by existing evidence-ref presence checks.
- Next recommended task:
  - add an adapter-event or bridge-runtime test that exercises
    `create_promotion_packet` with tool-derived evidence and
    `validation_result_ids`, or move to the next high-risk typed-record guard
    from the implementation plan.

### b91032c - Expose Evidence Refs In Pre-Tool Decisions

- Task: make pre-tool policy decisions explicitly return the evidence and
  validation-link inputs used for promotion/evidence checks, so review does not
  rely on reconstructing hook input from logs.
- Planning source:
  - previous ledger residual risk after `14a2f9a` to exercise adapter-event
    promotion validation links;
  - v5 invariant that adapter decisions must be auditable typed surfaces rather
    than prose-only hook messages.
- Changed files:
  - `brain/v5/pretool_policy.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - `pre_tool_policy_decision` payloads now include `evidence_refs`;
  - the pre-tool public-surface contract now requires list-shaped
    `evidence_refs`, `validation_contract_ids`, `tool_run_ids`, and
    `validation_result_ids`;
  - Codex-style platform pre-tool events are covered for
    `create_promotion_packet` with tool-derived evidence and matching
    `validation_result_ids`.
- Tests:
  - MCP pre-tool promotion tests assert `evidence_refs` are returned for both
    blocked and allowed rigorous promotion decisions;
  - public-surface contract test accepts the expanded audit-field payload;
  - bridge-runtime test verifies Codex platform events pass promotion evidence
    refs and validation-result links into the typed decision.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_pretool_policy.py -q -k "rigorous_promotion_packet"`:
    2 failed because `pre_tool_policy_decision` did not expose
    `evidence_refs`;
  - target green set:
    `python -m pytest tests\test_v5_bridge_runtime.py tests\test_v5_pretool_policy.py tests\test_v5_public_surfaces.py -q -k "promotion_validation_links or rigorous_promotion_packet or pre_tool_policy_decision"`:
    5 passed, 54 deselected;
  - focused related set:
    `python -m pytest tests\test_v5_bridge_runtime.py tests\test_v5_pretool_policy.py tests\test_v5_public_surfaces.py tests\test_v5_hooks.py tests\test_v5_adapters.py tests\test_v5_contracts.py -q`:
    167 passed;
  - full v5 regression set initially failed only the module-size boundary
    because `hook_protocol_contracts.py` reached 501 lines; after compressing
    repeated list-contract checks, full v5 passed:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    394 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - the decision surface exposes IDs used in policy checks, but it still does
    not include a full resolved evidence-record snapshot; consumers must read
    typed records when they need details.
- Next recommended task:
  - continue the next high-risk typed-record guard from the implementation
    plan, or add equivalent OpenCode platform-event coverage for promotion
    validation links.

### 0873c7d - Read Nested Packet Links In Adapter Events

- Task: make platform pre-tool event normalization consume promotion link fields
  from nested `packet` input, matching the adapter schema that already
  advertises optional nested packet payloads.
- Planning source:
  - previous ledger recommendation after `b91032c`;
  - v5 invariant that generated adapter schemas must match runtime behavior.
- Changed files:
  - `brain/v5/adapter_runtime.py`
  - `tests/test_v5_bridge_runtime.py`
- Public/runtime behavior changes:
  - `_input_list` now reads list and singular link fields from top-level tool
    input first, then falls back to nested `packet`;
  - OpenCode-style platform events that wrap `claim_id`, `evidence_refs`, and
    `validation_result_ids` inside `tool.input.packet` now reach the same typed
    pre-tool policy decision path as top-level Codex events.
- Tests:
  - OpenCode platform pre-tool event test uses nested promotion packet input
    with tool-derived evidence plus passed validation-result links and expects
    the decision to allow the action while exposing the resolved audit fields.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_bridge_runtime.py -q -k "nested_promotion_packet_links"`:
    1 failed because nested `packet.evidence_refs` and
    `packet.validation_result_ids` were not read;
  - target green set:
    `python -m pytest tests\test_v5_bridge_runtime.py -q -k "nested_promotion_packet_links or promotion_validation_links or maps_plugin_call_to_gate_policy"`:
    3 passed, 4 deselected;
  - focused related set:
    `python -m pytest tests\test_v5_bridge_runtime.py tests\test_v5_adapter_event_runner.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_contracts.py -q`:
    116 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    395 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - nested packet extraction currently covers list-shaped IDs and singular
    aliases; other nested scalar fields still follow existing explicit helper
    logic.
- Next recommended task:
  - continue broadening high-risk typed-record guard coverage, or start the
    realistic workflow acceptance skeletons once the remaining public runtime
    gaps are closed.

### 68f4a85 - Expose L2 Memory In Execution Brief

- Task: extend the realistic FQHE workflow acceptance path so a validated tool
  result can become scoped L2 memory through a promotion packet and approved
  human checkpoint, then appear in the next execution brief as orientation-only
  context.
- Planning source:
  - Task 12 real workflow acceptance skeleton;
  - v5 invariant that generated briefs can orient agents but typed kernel
    memory records remain authoritative;
  - user requirement that research memory preserve the validated path from
    literature/context through numerical check, validation, and promotion.
- Changed files:
  - `brain/v5/brief.py`
  - `brain/v5/memory.py`
  - `tests/test_v5_real_workflows.py`
- Public/runtime behavior changes:
  - added `list_memory_entries_for_claim`;
  - added `memory_entry_brief_payload`, which renders active L2 memory entries
    with `orientation_only=true`;
  - execution briefs now include `known_context.memory_entries` for active
    claim L2 memory entries;
  - the FQHE real workflow test now exercises validation contract/result,
    promotion packet creation, human checkpoint approval, L2 memory write, and
    refreshed brief orientation.
- Tests:
  - FQHE acceptance test asserts the promoted L2 memory entry preserves evidence
    refs and appears in `known_context.memory_entries`;
  - existing GW workflow skeleton remains as the code-method benchmark path.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_real_workflows.py::test_fqhe_learning_to_idea_to_toy_check_workflow -q`:
    1 failed with `KeyError: 'memory_entries'` because briefs did not expose
    L2 memory context;
  - target green set:
    same command: 1 passed;
  - focused related set:
    `python -m pytest tests\test_v5_real_workflows.py tests\test_v5_memory.py tests\test_v5_contracts.py tests\test_v5_kernel.py -q`:
    63 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    395 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - execution brief memory entries intentionally expose compact orientation
    fields only; consumers that need the statement/non-claims/failure modes
    should read the typed `MemoryEntryRecord`.
- Next recommended task:
  - strengthen the GW real workflow in the same way: require a validation
    contract/result before any code-method promotion, including code-state refs.

### f95ba36 - Carry Code-State Refs Into L2 Brief Context

- Task: strengthen the GW/code-method real workflow so a benchmark result tied
  to an exact code state can pass validation, be promoted through a human
  checkpoint, and then surface its code provenance in the next execution brief.
- Planning source:
  - previous ledger recommendation after `68f4a85`;
  - v5 invariant that code-dependent physics claims must retain code-state
    provenance across validation and L2 memory orientation;
  - user concern that failed reproductions can come from version/worktree
    mismatch rather than physics disagreement.
- Changed files:
  - `brain/v5/brief.py`
  - `brain/v5/memory.py`
  - `tests/test_v5_real_workflows.py`
- Public/runtime behavior changes:
  - `memory_entry_brief_payload` can receive typed evidence and tool-run records
    and include derived `code_state_ids` for memory entries whose supporting
    evidence came from code-bound tool runs;
  - execution briefs pass active-claim tool runs into the memory brief renderer;
  - GW/code-method workflow acceptance now exercises code-state provenance,
    validation contract/result, promotion packet creation, human checkpoint
    approval, L2 memory write, and refreshed brief orientation.
- Tests:
  - GW acceptance test asserts the promoted L2 memory entry appears in
    `known_context.memory_entries` with the expected `code_state_ids`;
  - FQHE acceptance test remains green without `code_state_ids`, proving the
    field is conditional on code-bound evidence.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_real_workflows.py::test_gw_formula_code_translation_records_code_state_and_benchmark -q`:
    1 failed because `known_context.memory_entries` did not include
    `code_state_ids`;
  - implementation correction:
    first attempt incorrectly read `code_state_ids` from `EvidenceRecord`,
    causing an `AttributeError`; the final implementation resolves them through
    linked `ToolRunRecord.code_state_ids`;
  - target green set:
    `python -m pytest tests\test_v5_real_workflows.py::test_gw_formula_code_translation_records_code_state_and_benchmark tests\test_v5_real_workflows.py::test_fqhe_learning_to_idea_to_toy_check_workflow -q`:
    2 passed;
  - focused related set:
    `python -m pytest tests\test_v5_real_workflows.py tests\test_v5_memory.py tests\test_v5_contracts.py tests\test_v5_kernel.py tests\test_v5_tool_executors.py -q`:
    74 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    395 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings.
- Residual risks:
  - `code_state_ids` are derived for brief orientation from current typed
    evidence/tool-run records; consumers needing full repository metadata must
    read the referenced `CodeStateRecord`.
- Next recommended task:
  - add a compact review/audit surface for L2 memory brief entries or continue
    closing remaining hook installer/native lifecycle gaps.

### 50dc9d4 - Contract L2 Memory Brief Context

- Task: make execution-brief validation explicitly check L2 memory orientation
  entries, so `known_context.memory_entries` cannot silently become an
  uncontracted truth source.
- Planning source:
  - residual risk after `68f4a85` and `f95ba36`;
  - v5 invariant that public derived context must remain orientation-only;
  - architecture rule to keep modules small and avoid rebuilding the old
    monolithic AITP style.
- Changed files:
  - `brain/v5/brief_contracts.py`
  - `brain/v5/contracts.py`
  - `tests/test_v5_contracts.py`
- Public/runtime behavior changes:
  - execution-brief contract validation is now implemented in
    `brain/v5/brief_contracts.py`, while `contracts.py` remains the public
    wrapper;
  - `known_context.memory_entries` is validated as a list when present;
  - each memory brief entry must keep `orientation_only=true`;
  - `evidence_refs` must be list-shaped, and optional `code_state_ids` must
    also be list-shaped.
- Tests:
  - contract rejects memory brief entries with `orientation_only=false`;
  - contract rejects string-shaped `evidence_refs` and `code_state_ids`;
  - current execution briefs still satisfy the public contract.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_contracts.py -q -k "memory_entry"`:
    2 failed because `validate_execution_brief` ignored memory entry content;
  - target green set:
    `python -m pytest tests\test_v5_contracts.py -q -k "execution_brief_contract"`:
    4 passed, 31 deselected;
  - focused related set:
    `python -m pytest tests\test_v5_contracts.py tests\test_v5_real_workflows.py tests\test_v5_adapters.py tests\test_v5_mcp_tools.py tests\test_v5_legacy_bridge.py -q`:
    115 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    397 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with only line-ending warnings;
  - architecture line count check from full v5 left `contracts.py` at 435 lines,
    below the 500-line boundary.
- Residual risks:
  - the contract validates memory brief shape, not the full typed
    `MemoryEntryRecord` semantics; consumers still need typed records for
    authoritative details.
- Next recommended task:
  - continue with remaining hook installer/native lifecycle gaps, or add a
    dedicated L2 memory audit surface if review needs more than brief context.

### f334f0e - Audit L2 Memory Provenance

- Task: add a compact read-only audit surface for active claim L2 memory, so a
  reviewer can inspect the typed provenance behind memory brief entries without
  treating generated summaries or execution briefs as truth sources.
- Planning source:
  - previous ledger recommendation after `50dc9d4`;
  - v5 invariant that typed kernel records remain authoritative while derived
    public surfaces must keep `summary_inputs_trusted=false`;
  - user requirement that research records be detailed enough for later GPT or
    human review without re-trusting compressed conversation context.
- Changed files:
  - `brain/v5/memory_audit.py`
  - `brain/v5/memory_audit_contracts.py`
  - `brain/v5/cli_memory.py`
  - `brain/v5/mcp_memory.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_memory_audit.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - new kernel function `audit_l2_memory_context(ws, claim_id=...)`;
  - new public surface `l2_memory_audit`;
  - new CLI command `aitp-v5 memory audit --claim <claim-id>`;
  - new MCP wrapper `aitp_v5_audit_l2_memory_context`;
  - new runtime entrypoint `audit_l2_memory_context`;
  - audit entries expose `source_packet_id`, promotion packet status, human
    checkpoint id/decision, evidence refs, validation result ids, derived
    code-state ids, and `missing_links` while remaining orientation-only.
- Tests:
  - audit payload links a promoted code-method L2 memory entry to its promotion
    packet, approved human checkpoint, evidence, validation result, and
    code-state provenance;
  - CLI/MCP/runtime entrypoints expose the same contracted payload;
  - public surface contract rejects summary-sourced audit payloads.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_memory_audit.py -q`: 3 failed because
    `brain.v5.memory_audit`, `aitp_v5_audit_l2_memory_context`, and the
    `l2_memory_audit` public surface did not exist;
  - target green set:
    same command: 3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_memory.py tests\test_v5_memory_audit.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_cli.py tests\test_v5_mcp_tools.py -q`:
    71 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    400 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --cached --check -- .`: passed.
- Residual risks:
  - this is an audit/orientation surface, not a mutation path and not a full
    graph query; reviewers needing full record bodies should still read the
    referenced typed records directly.
- Next recommended task:
  - add a small review helper that audits claim trust/confidence changes against
    evidence, validation results, and L2 memory, or continue the remaining
    native lifecycle installer work for Codex/OpenCode.

### c5136f9 - Audit Claim Trust Support

- Task: add a compact read-only audit surface for a claim's current confidence
  state, so reviewers can see whether typed evidence, validation results, L2
  memory, and code-state provenance support that state.
- Planning source:
  - previous ledger recommendation after `f334f0e`;
  - v5 invariant that trust-changing actions must be backed by typed kernel
    records and never by summaries;
  - goal requirement that another AI or human reviewer can audit each step.
- Changed files:
  - `brain/v5/trust_audit.py`
  - `brain/v5/trust_audit_contracts.py`
  - `brain/v5/mcp_trust_audit.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_trust_audit.py`
  - `tests/test_v5_public_surfaces.py`
- Public/runtime behavior changes:
  - new kernel function `audit_claim_trust(ws, claim_id=...)`;
  - new public surface `claim_trust_audit`;
  - new CLI command `aitp-v5 trust audit --claim <claim-id>`;
  - new MCP wrapper `aitp_v5_audit_claim_trust`;
  - new runtime entrypoint `audit_claim_trust`;
  - audit payloads expose current confidence, evidence profile, support state,
    supporting/challenging evidence refs, passed/failed validation result ids,
    active L2 memory entry ids, code-state ids, review actions, and explicit
    `mutation_history_available=false`.
- Tests:
  - audit payload reports `validated_memory_backed` support for a code-method
    claim that has typed evidence, passed validation result, promoted L2 memory,
    and code-state provenance;
  - CLI/MCP/runtime entrypoints expose the same contracted payload;
  - public surface contract rejects summary-sourced audit payloads.
- Verification:
  - red test:
    `python -m pytest tests\test_v5_trust_audit.py -q`: 3 failed because
    `brain.v5.trust_audit`, `aitp_v5_audit_claim_trust`, and the
    `claim_trust_audit` public surface did not exist;
  - target green set:
    same command: 3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_trust_audit.py tests\test_v5_trust_updates.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_cli.py tests\test_v5_mcp_tools.py -q`:
    63 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    403 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --cached --check -- .`: passed.
- Residual risks:
  - trust-update apply currently mutates claim confidence but does not persist a
    separate trust-update history record; the audit therefore reports
    `mutation_history_available=false` and focuses on current typed support.
- Next recommended task:
  - either add durable trust-update history records for confidence transitions,
    or continue the remaining native lifecycle installer integration for
    Codex/OpenCode.

### d4aa384 - Persist Trust Update History

- Task: make confidence-changing trust apply attempts durable typed records, so
  later audits can show actual mutation history rather than a placeholder flag.
- Planning source:
  - previous ledger recommendation after `c5136f9`;
  - v5 invariant that trust-changing actions must go through kernel records and
    must remain auditable from typed records instead of summaries;
  - goal requirement that every implemented step is reviewable by another AI or
    human.
- Changed files:
  - `brain/v5/models.py`
  - `brain/v5/paths.py`
  - `brain/v5/trust_updates.py`
  - `brain/v5/trust_contracts.py`
  - `brain/v5/trust_audit.py`
  - `brain/v5/trust_audit_contracts.py`
  - `brain/v5/record_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/cli.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_trust_updates.py`
  - `tests/test_v5_trust_audit.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new typed dataclass `TrustUpdateRecord`;
  - new registry directory `.aitp/registry/trust_updates`;
  - `apply_trust_update` writes a `TrustUpdateRecord` for both applied and
    blocked attempts and returns `trust_update_record_id`;
  - new public surface `trust_update_record`;
  - new kernel getter `get_trust_update_record(ws, update_id)`;
  - new CLI command `aitp-v5 trust update-record <update-id>`;
  - new MCP wrapper `aitp_v5_get_trust_update_record`;
  - new runtime entrypoint `get_trust_update_record`;
  - `claim_trust_audit` now reports `trust_update_record_ids` and sets
    `mutation_history_available=true` when typed history exists.
- Tests:
  - apply writes an applied history record and blocks summary-sourced attempts
    while still recording the blocked attempt;
  - the trust-update record public surface validates the persisted record;
  - CLI/MCP/runtime surfaces expose the new history record getter;
  - claim trust audit reads typed mutation history from the registry.
- Verification:
  - red audit-history test:
    `python -m pytest tests\test_v5_trust_updates.py::test_apply_confidence_change_updates_registry_and_topic_ledger tests\test_v5_trust_updates.py::test_apply_confidence_change_blocks_summary_source_without_mutating tests\test_v5_trust_audit.py::test_claim_trust_audit_reports_typed_support_for_current_confidence tests\test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads -q`:
    1 failed, 3 passed because `claim_trust_audit` omitted
    `trust_update_record_ids`;
  - red CLI/MCP/runtime getter tests:
    `python -m pytest tests\test_v5_trust_updates.py::test_can_read_persisted_trust_update_record_by_id tests\test_v5_trust_updates.py::test_cli_trust_update_record_returns_contract_payload tests\test_v5_trust_updates.py::test_mcp_get_trust_update_record_returns_contract_payload tests\test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces -q`:
    4 failed because the getter, CLI subcommand, MCP wrapper, and runtime
    entrypoint did not exist;
  - target getter set:
    same command: 4 passed;
  - focused related set:
    `python -m pytest tests\test_v5_trust_updates.py tests\test_v5_trust_audit.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_cli.py tests\test_v5_mcp_tools.py -q`:
    66 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    406 passed;
  - `python -m compileall -q brain\v5`: passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - trust-update history is currently an apply-attempt ledger, not a full
    narrative explanation graph; reviewers still need to inspect linked
    evidence, validation results, and code states for the physics justification.
- Next recommended task:
  - continue with remaining native Codex/OpenCode lifecycle installer wiring,
    or deepen pre-tool policy coverage for MCP inputs and active risk
    dimensions.

### a43851a - Install Codex Native Hooks

- Task: add a Codex-native `hooks.json` merge installer so AITP v5 can wire
  lifecycle events into an existing Codex hooks file instead of relying only on
  generated fixture metadata.
- Planning source:
  - major remaining hook gap in
    `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`;
  - v5 invariant that runtime hooks and generated bridge files are metadata and
    cannot become truth sources;
  - goal requirement for CLI/MCP/runtime/hook symmetry and reviewable
    implementation steps.
- Changed files:
  - `brain/v5/hook_codex_install.py`
  - `brain/v5/mcp_hook_install.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - new helper `install_codex_hooks_json(...)` in a focused Codex installer
    module;
  - `aitp-v5 adapter install-hooks codex <session-id> --settings <hooks.json>`
    merges AITP `PreToolUse` and `PostToolUse` command hooks into an existing
    Codex hooks JSON file;
  - the installer preserves existing events, avoids duplicate AITP hooks on
    repeated runs, writes the bridge Markdown plus JSON sidecar, and returns the
    contracted `codex_hook_installation` public surface;
  - `aitp_v5_install_codex_hook_fixture(..., hooks_path=<hooks.json>)` exposes
    the same native install path through MCP while retaining the older fixture
    path with `output_path`.
- Tests:
  - native installer preserves existing Codex hooks, writes sidecar bridge, and
    is idempotent;
  - CLI `adapter install-hooks codex --settings` returns the contracted payload;
  - MCP `aitp_v5_install_codex_hook_fixture(..., hooks_path=...)` returns the
    contracted payload;
  - architecture boundary test keeps hook template rendering separate from the
    Codex native installer module.
- Verification:
  - initial red set:
    `python -m pytest tests\test_v5_adapters.py::test_codex_native_hooks_json_installer_merges_lifecycle_hooks tests\test_v5_adapters.py::test_cli_adapter_install_hooks_merges_codex_hooks_json tests\test_v5_adapters.py::test_mcp_codex_native_hook_installer_returns_contract_payload -q`:
    3 failed because the helper, CLI `--settings`, and MCP `hooks_path` surface
    did not exist;
  - target set after implementation and refactor:
    `python -m pytest tests\test_v5_adapters.py::test_codex_native_hooks_json_installer_merges_lifecycle_hooks tests\test_v5_adapters.py::test_cli_adapter_install_hooks_merges_codex_hooks_json tests\test_v5_adapters.py::test_mcp_codex_native_hook_installer_returns_contract_payload tests\test_v5_architecture_boundaries.py::test_hook_install_template_module_stays_renderer_free -q`:
    4 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_cli.py tests\test_v5_architecture_boundaries.py -q`:
    107 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    409 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this installs into a supplied Codex hooks JSON path; a future packaged
    installer should discover the host config path and report conflicts before
    writing;
  - OpenCode still has a generated plugin fixture but not equivalent native
    lifecycle config merging.
- Next recommended task:
  - implement the OpenCode native lifecycle installer or broaden pre-tool
    policy coverage for remaining MCP inputs and active risk dimensions.

### 68ba87b - Install OpenCode Local Plugin Hooks

- Task: add a real OpenCode project-local plugin installer that wires OpenCode
  lifecycle hooks to the AITP v5 adapter event runner instead of only writing a
  generated JSON fixture.
- Planning source:
  - previous ledger recommendation after `a43851a`;
  - hook-installation plan requirement to move beyond generated fixture metadata
    for Codex/OpenCode lifecycle events;
  - OpenCode plugin contract for project-local plugins under
    `.opencode/plugins/` with lifecycle hooks such as `tool.execute.before`.
- Changed files:
  - `brain/v5/hook_opencode_install.py`
  - `brain/v5/mcp_hook_install.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/mcp_tools.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - new helper `install_opencode_plugin_file(...)` writes an OpenCode local
    plugin file such as `.opencode/plugins/aitp-v5.js`;
  - new CLI path:
    `aitp-v5 adapter install-hooks opencode <session-id> --plugin <path>`;
  - MCP `aitp_v5_install_opencode_hook_fixture(..., plugin_path=<path>)` exposes
    the same plugin installer while preserving the existing fixture path through
    `output_path`;
  - generated plugin subscribes to `tool.execute.before` and
    `tool.execute.after`, calls `hooks/aitp_v5_adapter_event_runner.py`, throws
    on blocking typed pre-tool policy output, and logs post-tool trace failures;
  - `opencode_hook_installation` contract now accepts either the older fixture
    payload or the new native plugin payload.
- Tests:
  - direct installer writes the plugin, bridge Markdown, JSON sidecar, and is
    idempotent on a second run;
  - CLI `adapter install-hooks opencode --plugin` returns the contracted
    `opencode_hook_installation` payload;
  - MCP `aitp_v5_install_opencode_hook_fixture(..., plugin_path=...)` returns
    the contracted payload.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapters.py::test_opencode_local_plugin_installer_writes_native_plugin tests\test_v5_adapters.py::test_cli_adapter_install_hooks_writes_opencode_local_plugin tests\test_v5_adapters.py::test_mcp_opencode_local_plugin_installer_returns_contract_payload -q`:
    3 failed because `brain.v5.hook_opencode_install`, CLI `--plugin`, and MCP
    `plugin_path` did not exist;
  - target green set:
    same command: 3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_adapter_event_runner.py tests\test_v5_bridge_runtime.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_cli.py tests\test_v5_architecture_boundaries.py -q`:
    122 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    412 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this generates a local plugin file and statically verifies its lifecycle
    wiring; it does not yet run inside a live OpenCode host process;
  - packaged installer UX still needs host path discovery and conflict reporting
    across Codex, Claude Code, and OpenCode.
- Next recommended task:
  - add host-installation discovery/audit surfaces for runtime config paths, or
    broaden pre-tool policy coverage for remaining MCP inputs and active risk
    dimensions.

### cb78039 - Audit Runtime Hook Installation

- Task: add a read-only public audit surface for installed runtime hook files,
  so agents can check whether supplied Codex, Claude Code, and OpenCode hook
  configs contain the expected AITP v5 lifecycle runners without treating those
  files as truth sources.
- Planning source:
  - previous ledger recommendation after `68ba87b`;
  - v5 invariant that generated hook/plugin files are runtime metadata only;
  - goal requirement for reviewable hook/MCP/CLI/runtime surfaces.
- Changed files:
  - `brain/v5/hook_install_audit.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/mcp_tools.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new kernel helper `audit_hook_installation(ws, runtime=..., settings_path=...,
    plugin_path=..., output_path=...)`;
  - new CLI command `aitp-v5 adapter install-audit <runtime> <args>`;
  - new MCP wrapper `aitp_v5_audit_hook_installation`;
  - new public surface `runtime_hook_installation_audit`;
  - new runtime entrypoint catalog item
    `runtime_hook_installation_audit`;
  - audit payloads report `installed`, `partial`, `missing`, or `conflict`,
    checked paths, findings, and required actions while keeping
    `summary_inputs_trusted=false`, `orientation_only=true`,
    `can_update_kernel_state=false`, and `can_update_claim_trust=false`.
- Tests:
  - direct audit verifies Codex native `hooks.json` installed by the v5
    installer;
  - CLI audit verifies an OpenCode local plugin generated by the v5 installer;
  - MCP audit verifies Claude Code settings generated by the v5 installer;
  - public-surface and runtime-entrypoint registries advertise the new audit.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapters.py::test_hook_installation_audit_reports_codex_native_hooks tests\test_v5_adapters.py::test_cli_adapter_install_audit_reports_opencode_local_plugin tests\test_v5_adapters.py::test_mcp_hook_installation_audit_reports_claude_settings tests\test_v5_public_surfaces.py::test_public_surface_validator_accepts_runtime_hook_installation_audit tests\test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces -q`:
    5 failed because the audit module, CLI subcommand, MCP wrapper, public
    surface, and runtime entrypoint did not exist;
  - target green set:
    same command: 5 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_cli.py tests\test_v5_architecture_boundaries.py -q`:
    114 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    416 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - the audit checks supplied paths; it does not yet discover every possible
    host config path automatically;
  - live host smoke tests are still needed to execute generated lifecycle hooks
    inside Codex/OpenCode rather than only through repo-level tests.
- Next recommended task:
  - implement packaged host-path discovery for Codex, Claude Code, and OpenCode,
    or continue broadening pre-tool policy coverage for remaining MCP inputs and
    active risk dimensions.

### 217acd0 - Discover Runtime Hook Install Paths

- Task: add a read-only path discovery surface for runtime hook installation, so
  agents can find workspace-local Codex, Claude Code, and OpenCode install
  targets before calling installer or audit commands.
- Planning source:
  - previous ledger recommendation after `cb78039`;
  - hook-installation plan residual gap for host-path discovery;
  - v5 invariant that runtime hook files are convention metadata, not typed
    kernel state.
- Changed files:
  - `brain/v5/hook_install_paths.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/mcp_tools.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new helper `discover_hook_install_paths(ws)`;
  - new CLI command `aitp-v5 adapter install-paths`;
  - new MCP wrapper `aitp_v5_discover_hook_install_paths`;
  - new public surface `runtime_hook_installation_paths`;
  - new runtime entrypoint catalog item
    `runtime_hook_installation_paths`;
  - payload lists preferred and alternate workspace-local targets for Codex
    `.codex/hooks.json`/fixture, Claude Code `.claude/settings.local.json`, and
    OpenCode `.opencode/plugins/aitp-v5.js`/fixture, plus matching install and
    audit commands.
- Tests:
  - direct helper returns Codex/Claude/OpenCode defaults with preferred install
    args and commands;
  - CLI `adapter install-paths` returns contracted defaults;
  - MCP wrapper returns contracted defaults;
  - public-surface and runtime-entrypoint registries advertise the new surface.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapters.py::test_hook_installation_paths_discover_workspace_defaults tests\test_v5_adapters.py::test_cli_adapter_install_paths_returns_default_paths tests\test_v5_adapters.py::test_mcp_hook_installation_paths_returns_contract_payload tests\test_v5_public_surfaces.py::test_public_surface_validator_accepts_runtime_hook_installation_paths tests\test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces -q`:
    5 failed because the path module, CLI subcommand, MCP wrapper, public
    surface, and runtime entrypoint did not exist;
  - target green set:
    same command: 5 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_cli.py tests\test_v5_architecture_boundaries.py -q`:
    118 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    420 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this covers workspace-local path conventions; global host config discovery
    can be added if later runtime integration needs it;
  - live host smoke tests are still needed to prove generated hooks execute
    inside the real Codex/OpenCode host processes.
- Next recommended task:
  - add live-style host smoke tests for generated hook/plugin files where
    practical, or broaden pre-tool policy coverage for remaining MCP inputs and
    active risk dimensions.

### 7298be0 - Make Codex Native Hooks Cwd Independent

- Task: make generated Codex native `hooks.json` command strings executable
  from a user workspace cwd, so host smoke coverage does not assume the host
  process starts in the AITP repository root.
- Planning source:
  - previous ledger recommendation after `217acd0`;
  - hook-installation plan residual gap for live-style host smoke coverage;
  - v5 invariant that runtime hook files are metadata only and must route real
    decisions through typed pre-tool policy and trace surfaces.
- Changed files:
  - `brain/v5/hook_codex_install.py`
  - `tests/test_v5_adapter_event_runner.py`
- Public/runtime behavior changes:
  - Codex `install-hooks --settings <hooks.json>` now emits command strings
    using the active Python interpreter and an absolute
    `hooks/aitp_v5_adapter_event_runner.py` path;
  - generated `PreToolUse` and `PostToolUse` command hooks can be executed from
    the user's workspace cwd while still reading the bridge sidecar and writing
    trace events through v5 public surfaces;
  - no kernel truth-source authority was added to runtime hook files.
- Tests:
  - added host-cwd smoke coverage for generated Codex native pre-tool command
    strings, asserting summary-sourced evidence writes are blocked through the
    typed pre-tool policy;
  - added host-cwd smoke coverage for generated Codex native post-tool command
    strings, asserting hook trace events persist to the v5 trace log.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapter_event_runner.py::test_codex_native_hooks_json_pre_tool_command_executes_from_workspace_cwd tests\test_v5_adapter_event_runner.py::test_codex_native_hooks_json_post_tool_command_executes_from_workspace_cwd -q`:
    2 failed because `python hooks/aitp_v5_adapter_event_runner.py` was resolved
    relative to the temporary user workspace cwd;
  - target green set:
    same command: 2 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapter_event_runner.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    111 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    422 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this proves generated Codex native commands from a host-style workspace cwd;
    broader in-host Codex/OpenCode execution inside the actual app processes is
    still needed;
  - OpenCode local plugin JavaScript lifecycle loading still needs a comparable
    host smoke path where practical.
- Next recommended task:
  - add OpenCode local plugin lifecycle smoke coverage using the generated
    plugin file, or continue broadening pre-tool policy coverage for remaining
    MCP inputs and active risk dimensions.

### 8c11abb - Smoke Test OpenCode Local Plugin Lifecycle

- Task: make OpenCode project-local plugin installation more host-realistic by
  generating cwd-independent runner argv and smoke-testing the generated
  JavaScript plugin lifecycle handlers.
- Planning source:
  - previous ledger recommendation after `7298be0`;
  - hook-installation plan residual gap for live-style host smoke coverage;
  - v5 invariant that generated runtime files remain metadata and must delegate
    decisions to typed pre-tool policy and trace surfaces.
- Changed files:
  - `brain/v5/hook_opencode_install.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/hook_install_audit.py`
  - `tests/test_v5_adapter_event_runner.py`
  - `tests/test_v5_adapters.py`
- Public/runtime behavior changes:
  - OpenCode local plugin `pre_tool` and `post_tool` runner argv now use the
    active Python interpreter and an absolute
    `hooks/aitp_v5_adapter_event_runner.py` path;
  - hook installation contracts and read-only install audit accept cwd-independent
    absolute runner paths while still requiring the adapter runner file and
    lifecycle command tokens;
  - generated plugin JavaScript is loaded with Node in tests, then
    `tool.execute.before` blocks a summary-sourced evidence write and
    `tool.execute.after` persists a hook trace event.
- Tests:
  - added argv-shape coverage for OpenCode local plugin hooks;
  - added generated-plugin lifecycle smoke coverage using Node dynamic import;
  - updated OpenCode installer/audit assertions to recognize absolute runner
    paths.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapter_event_runner.py::test_opencode_local_plugin_runner_argv_is_cwd_independent tests\test_v5_adapter_event_runner.py::test_opencode_local_plugin_lifecycle_smoke_executes_generated_plugin -q`:
    2 failed because OpenCode plugin argv used `python` plus a relative
    `hooks/aitp_v5_adapter_event_runner.py` path;
  - target green set:
    same command: 2 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapter_event_runner.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    113 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    424 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this loads and executes the generated plugin module locally with Node; it
    still is not a full OpenCode app process integration test;
  - global/non-workspace host configuration discovery remains deferred unless a
    runtime integration requires it.
- Next recommended task:
  - add a lightweight runtime hook smoke-report/audit surface that summarizes
    which generated host smoke checks exist for Codex/OpenCode/Claude Code, or
    continue broadening pre-tool policy coverage for remaining MCP inputs and
    active risk dimensions.

### b3cdeb5 - Report Runtime Hook Smoke Coverage

- Task: expose a machine-readable, orientation-only report of which generated
  runtime hook paths have test-backed smoke coverage and which real-host gaps
  remain.
- Planning source:
  - previous ledger recommendation after `8c11abb`;
  - hook-installation plan residual gap for reviewable host smoke coverage;
  - v5 invariant that summaries, generated hook files, and test reports are
    not kernel truth sources.
- Changed files:
  - `brain/v5/hook_smoke_coverage.py`
  - `brain/v5/hook_install_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/cli.py`
  - `brain/v5/cli_adapters.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_public_surfaces.py`
  - `tests/test_v5_runtime_entrypoints.py`
- Public/runtime behavior changes:
  - new helper `runtime_hook_smoke_coverage_report()`;
  - new CLI command `aitp-v5 adapter smoke-coverage`;
  - new MCP wrapper `aitp_v5_report_hook_smoke_coverage`;
  - new public surface `runtime_hook_smoke_coverage`;
  - new runtime entrypoint catalog item
    `runtime_hook_smoke_coverage`;
  - report lists test-backed Codex native hooks, Codex fixture, OpenCode
    fixture, OpenCode local plugin, and Claude Code settings coverage, plus
    remaining real-host process gaps.
- Tests:
  - direct helper validates the contracted coverage report;
  - CLI and MCP wrappers return the contracted payload;
  - public-surface and runtime-entrypoint registries advertise the new surface.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_adapters.py::test_runtime_hook_smoke_coverage_reports_test_backed_host_smokes tests\test_v5_adapters.py::test_cli_adapter_smoke_coverage_returns_contract_payload tests\test_v5_adapters.py::test_mcp_hook_smoke_coverage_returns_contract_payload tests\test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads tests\test_v5_runtime_entrypoints.py::test_runtime_entrypoints_advertise_typed_write_surfaces -q`:
    5 failed because the module, CLI subcommand, MCP wrapper, public surface,
    and runtime entrypoint did not exist;
  - target green set:
    same command: 5 passed;
  - focused related set:
    `python -m pytest tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    107 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    427 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - report is a static contract registry of known smoke tests; it does not
    execute those tests or prove real app host integration;
  - broader in-host smoke tests remain a separate implementation task.
- Next recommended task:
  - deepen real app host smoke coverage where feasible, or continue broadening
    pre-tool policy coverage for remaining MCP inputs and active risk
    dimensions.

### 3231592 - Require Known Failure Modes In Promotion Pre-Tool Policy

- Task: broaden pre-tool policy coverage for promotion-packet creation so an
  agent cannot pass the L2 memory gate by attaching evidence and validation
  links while skipping explicit failure-mode reflection.
- Planning source:
  - previous ledger recommendation after `b3cdeb5`;
  - v5 promotion packet contract requiring non-empty `known_failure_modes`;
  - user requirement that gates should induce real physicist thinking rather
    than fast checklist completion.
- Changed files:
  - `brain/v5/policy.py`
  - `brain/v5/pretool_policy.py`
  - `brain/v5/cli_policy.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/adapter_runtime.py`
  - `brain/v5/hook_entrypoint_schemas.py`
  - `brain/v5/hook_protocol_contracts.py`
  - `brain/v5/hook_bridge_markdown.py`
  - `hooks/aitp_v5_claude_hook.py`
  - `tests/test_v5_pretool_policy.py`
  - `tests/test_v5_adapters.py`
  - `tests/test_v5_bridge_runtime.py`
  - `tests/test_v5_hooks.py`
  - `tests/test_v5_public_surfaces.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - shared pre-tool policy accepts `known_failure_modes` through kernel helper,
    CLI, MCP, generated bridge schemas, Codex/OpenCode platform event
    normalization, and the Claude Code hook wrapper;
  - `create_promotion_packet` pre-tool decisions hard-block when no known
    failure mode is supplied, using policy id
    `promotion_packet_requires_known_failure_mode` and required action
    `record_known_failure_mode`;
  - pre-tool decision payloads now expose `known_failure_modes` as a contracted
    list, while still carrying no kernel mutation authority.
- Tests:
  - added MCP block coverage for promotion-packet creation without known
    failure modes;
  - added CLI acceptance coverage when `--known-failure-mode` is supplied;
  - updated adapter/runtime/Claude-hook smoke tests to propagate
    `known_failure_modes` where the test focus is another policy dimension.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_pretool_policy.py::test_mcp_pre_tool_policy_blocks_promotion_packet_without_known_failure_modes tests\test_v5_pretool_policy.py::test_cli_pre_tool_policy_accepts_promotion_packet_known_failure_mode -q`:
    2 failed because payloads lacked `known_failure_modes` and CLI rejected
    `--known-failure-mode`;
  - target green set:
    same command: 2 passed;
  - pre-tool set:
    `python -m pytest tests\test_v5_pretool_policy.py -q`: 35 passed;
  - focused related set:
    `python -m pytest tests\test_v5_pretool_policy.py tests\test_v5_policy.py tests\test_v5_mcp_tools.py tests\test_v5_adapters.py tests\test_v5_bridge_runtime.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py -q`:
    151 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    429 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this strengthens the policy contract but does not evaluate whether a named
    failure mode is physically sufficient; deeper physics adequacy checks remain
    a later domain-tool/policy task;
  - real host-process hook smoke coverage remains incomplete.
- Next recommended task:
  - add a failure-mode adequacy or active-risk-dimension audit for promotion and
    validation, or continue real app host smoke coverage for Codex/OpenCode/
    Claude Code.

### 4db4118 - Align Promotion Failure Modes With Claim Risk

- Task: strengthen promotion-packet pre-tool policy from non-empty failure-mode
  capture to deterministic claim-risk coverage when the active claim already
  records a `strongest_failure_mode`.
- Planning source:
  - previous ledger recommendation after `3231592`;
  - user requirement that harness gates should induce real physicist-style
    reflection instead of shallow checklist completion;
  - v5 invariant that typed claim records are authoritative over derived
    summaries.
- Changed files:
  - `brain/v5/policy.py`
  - `tests/test_v5_pretool_policy.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-hook-installation.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - `create_promotion_packet` pre-tool policy still accepts
    `known_failure_modes`, but now checks them against the claim's
    `strongest_failure_mode` when that typed field is set;
  - if the supplied modes miss the recorded claim-local risk, the policy
    hard-blocks with policy id
    `promotion_failure_modes_must_cover_claim_failure_mode` and required action
    `align_failure_mode_with_claim_risk`;
  - the check is deterministic token coverage from typed record fields, not an
    LLM adequacy judgment.
- Tests:
  - added MCP coverage that blocks a rigorous promotion packet whose supplied
    failure mode does not cover the claim's `strongest_failure_mode`;
  - added MCP coverage that accepts the same packet once the supplied failure
    mode covers the recorded risk;
  - factored a focused validation/evidence seeding helper for the new cases.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_pretool_policy.py::test_mcp_pre_tool_policy_blocks_promotion_failure_mode_that_misses_claim_risk tests\test_v5_pretool_policy.py::test_mcp_pre_tool_policy_accepts_promotion_failure_mode_covering_claim_risk -q`:
    1 failed and 1 passed because mismatched failure modes were still allowed;
  - target green set:
    same command: 2 passed;
  - pre-tool set:
    `python -m pytest tests\test_v5_pretool_policy.py -q`: 37 passed;
  - focused related set:
    `python -m pytest tests\test_v5_pretool_policy.py tests\test_v5_policy.py tests\test_v5_mcp_tools.py tests\test_v5_adapters.py tests\test_v5_bridge_runtime.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_hooks.py -q`:
    177 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    431 passed;
- Residual risks:
  - token coverage is intentionally deterministic and reviewable, but it cannot
    prove physical adequacy across synonyms, conventions, or deeper theoretical
    equivalences;
  - a later domain-tool or adversarial reviewer packet should assess whether
    the named failure mode is physically sufficient for the claim.
- Next recommended task:
  - add a read-only failure-mode adequacy/audit surface that reports uncovered
    claim uncertainty, strongest failure mode, validation-contract failure
    modes, and promotion-packet known failure modes without mutating trust.

### 9498735 - Audit Failure-Mode Coverage

- Task: add a read-only public audit surface that reports whether a claim's
  recorded failure modes are covered by validation contracts and promotion
  packet known failure modes.
- Planning source:
  - previous ledger recommendation after `4db4118`;
  - v5 invariant that typed records, not summaries, are authoritative;
  - user requirement that harness gates should induce actual physics-style
    reflection without making every step a trust-changing action.
- Changed files:
  - `brain/v5/failure_mode_audit.py`
  - `brain/v5/failure_mode_audit_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/cli_memory.py`
  - `brain/v5/mcp_memory.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_memory_audit.py`
  - `tests/test_v5_public_surfaces.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - new kernel helper `audit_failure_mode_coverage`;
  - new CLI command `aitp-v5 memory failure-modes --claim <claim-id>`;
  - new MCP wrapper `aitp_v5_audit_failure_mode_coverage`;
  - new public surface `failure_mode_audit`;
  - new runtime entrypoint catalog item `audit_failure_mode_coverage`;
  - payload reports active uncertainty, strongest failure mode, validation
    contract failure modes, promotion-packet known failure modes, uncovered
    claim/validation modes, coverage status, and recommended review actions;
  - payload is explicitly read-only:
    `summary_inputs_trusted=false`, `can_update_kernel_state=false`, and
    `can_update_claim_trust=false`.
- Tests:
  - added a typed-record fixture with claim risk, validation-contract failure
    modes, and a mismatched promotion packet;
  - added kernel/public-surface coverage for uncovered claim and validation
    failure modes;
  - added CLI, MCP, and runtime-entrypoint coverage for the same audit surface.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_memory_audit.py::test_failure_mode_audit_reports_uncovered_claim_and_contract_modes tests\test_v5_memory_audit.py::test_failure_mode_audit_cli_mcp_and_runtime_entrypoint tests\test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads -q`:
    3 failed because the module, MCP wrapper, and public surface did not exist;
  - target green set:
    same command: 3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_memory_audit.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    46 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    433 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - coverage is deterministic token coverage and does not prove physical
    adequacy across synonyms, conventions, or deeper theoretical equivalences;
  - the audit is read-only and advisory; later policy work can use it as input
    but should still route trust changes through typed validation/promotion
    records.
- Next recommended task:
  - add a physics adequacy review packet or domain-tool-backed failure-mode
    review flow that can assess whether recorded failure modes are physically
    sufficient before promotion, without making summaries authoritative.

### 8746acc - Build Failure-Mode Review Packets

- Task: turn the read-only failure-mode coverage audit into a review packet
  that asks concrete physical adequacy questions before promotion.
- Planning source:
  - previous ledger recommendation after `9498735`;
  - user requirement that harness questions should be physically meaningful,
    state-dependent, and not merely checklist gates;
  - v5 invariant that review surfaces cannot update kernel state or claim trust.
- Changed files:
  - `brain/v5/failure_mode_review.py`
  - `brain/v5/failure_mode_review_contracts.py`
  - `brain/v5/contracts.py`
  - `brain/v5/cli_memory.py`
  - `brain/v5/mcp_memory.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/public_surfaces.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `tests/test_v5_memory_audit.py`
  - `tests/test_v5_public_surfaces.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - new kernel helper `build_failure_mode_review_packet`;
  - new CLI command `aitp-v5 memory failure-mode-review --claim <claim-id>`;
  - new MCP wrapper `aitp_v5_build_failure_mode_review_packet`;
  - new public surface `failure_mode_review_packet`;
  - new runtime entrypoint catalog item `build_failure_mode_review_packet`;
  - packet includes per-failure-mode source labels, coverage labels, and
    physical adequacy questions for human/adversarial review;
  - packet remains read-only:
    `truth_source=typed_records`, `summary_inputs_trusted=false`,
    `can_update_kernel_state=false`, and `can_update_claim_trust=false`.
- Tests:
  - added kernel/public-surface coverage that expects review questions for
    uncovered claim/validation failure modes and promotion-packet-only modes;
  - added CLI, MCP, and runtime-entrypoint coverage;
  - updated the public surface registry expectation.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_memory_audit.py::test_failure_mode_review_packet_generates_physics_adequacy_questions tests\test_v5_memory_audit.py::test_failure_mode_review_packet_cli_mcp_and_runtime_entrypoint tests\test_v5_public_surfaces.py::test_public_surface_registry_names_all_runtime_facing_payloads -q`:
    3 failed because the review module, MCP wrapper, and public surface did not
    exist;
  - target green set:
    same command: 3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_memory_audit.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    48 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    435 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - questions are deterministic and state-dependent, but they still do not run
    a domain numerical/symbolic/literature tool;
  - physical adequacy remains a review target, not an automatic trust update.
- Next recommended task:
  - connect this review packet to a typed human/adversarial checkpoint or a
    domain-tool-backed review result so promotion can require explicit review
    completion while keeping summaries non-authoritative.

### 47eee91 - Request Failure-Mode Review Checkpoints

- Task: connect failure-mode review packets to durable typed human checkpoint
  records so physical adequacy review can be tracked before promotion.
- Planning source:
  - previous ledger recommendation after `8746acc`;
  - v5 invariant that durable review state must be a typed kernel record;
  - user requirement that physics review should be meaningful without becoming
    an uncontrolled automatic trust update.
- Changed files:
  - `brain/v5/failure_mode_review.py`
  - `brain/v5/cli_memory.py`
  - `brain/v5/mcp_memory.py`
  - `brain/v5/mcp_tools.py`
  - `brain/v5/runtime_entrypoint_catalog.py`
  - `brain/v5/adapter_runtime.py`
  - `tests/test_v5_memory_audit.py`
  - `tests/test_v5_adapters.py`
  - `README.md`
  - `PROJECT_MEMORY.md`
  - `docs/superpowers/plans/2026-05-20-aitp-v5-next-agent-implementation-plan.md`
- Public/runtime behavior changes:
  - new kernel helper `request_failure_mode_review_checkpoint`;
  - new CLI command
    `aitp-v5 memory request-failure-mode-review --claim <claim-id>`;
  - new MCP wrapper `aitp_v5_request_failure_mode_review_checkpoint`;
  - new runtime entrypoint catalog item
    `request_failure_mode_review_checkpoint`;
  - helper writes a normal `human_checkpoint_record` with options
    `approve_failure_mode_review` and `revise_failure_modes`;
  - adapter pre-tool event mapping treats the wrapper as
    `request_human_checkpoint`, so summary/task-plan sourced calls inherit the
    same blocking policy as ordinary checkpoint requests.
- Tests:
  - added kernel/public-surface coverage that the helper creates an open typed
    human checkpoint whose reason includes failure modes requiring review;
  - added CLI/MCP/runtime-entrypoint coverage;
  - added adapter pre-tool coverage showing the new MCP wrapper maps to
    `request_human_checkpoint` and blocks task-plan sourced attempts.
- Verification:
  - red target set:
    `python -m pytest tests\test_v5_memory_audit.py::test_failure_mode_review_checkpoint_requests_typed_human_review tests\test_v5_memory_audit.py::test_failure_mode_review_checkpoint_cli_mcp_and_runtime_entrypoint -q`:
    2 failed because the kernel helper and MCP wrapper did not exist;
  - adapter red target:
    `python -m pytest tests\test_v5_adapters.py::test_mcp_adapter_pre_tool_event_maps_failure_mode_review_checkpoint_to_human_checkpoint -q`:
    1 failed because the adapter normalizer could not infer an AITP action from
    `aitp_v5_request_failure_mode_review_checkpoint`;
  - target green set:
    `python -m pytest tests\test_v5_memory_audit.py::test_failure_mode_review_checkpoint_requests_typed_human_review tests\test_v5_memory_audit.py::test_failure_mode_review_checkpoint_cli_mcp_and_runtime_entrypoint tests\test_v5_adapters.py::test_mcp_adapter_pre_tool_event_maps_failure_mode_review_checkpoint_to_human_checkpoint -q`:
    3 passed;
  - focused related set:
    `python -m pytest tests\test_v5_memory_audit.py tests\test_v5_adapters.py tests\test_v5_public_surfaces.py tests\test_v5_runtime_entrypoints.py tests\test_v5_mcp_tools.py tests\test_v5_architecture_boundaries.py -q`:
    117 passed;
  - full v5 regression set:
    `$files = Get-ChildItem tests -Filter 'test_v5_*.py' | ForEach-Object { $_.FullName }; python -m pytest $files -q`:
    438 passed;
  - `python -m compileall -q brain\v5 hooks\aitp_v5_adapter_event_runner.py hooks\aitp_v5_claude_hook.py`:
    passed;
  - `git diff --check -- .`: passed, with line-ending warnings only.
- Residual risks:
  - this creates durable review state, but it does not yet require a decided
    review checkpoint before promotion packet creation or L2 application;
  - actual physical adequacy can still require domain tools, literature, or
    adversarial review beyond the generated question packet.
- Next recommended task:
  - add policy/promotion awareness of failure-mode review checkpoints so high
    risk promotion can require an approved review checkpoint before L2 memory
    promotion, while preserving explicit human decision semantics.
