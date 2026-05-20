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

### Pending - Expose Hook Protocols In Adapter Packets

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
