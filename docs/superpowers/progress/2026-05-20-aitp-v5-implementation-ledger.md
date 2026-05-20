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
