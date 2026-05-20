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
