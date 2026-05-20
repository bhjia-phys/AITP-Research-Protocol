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
