# AITP v5 Hook Installation Templates

This document defines the install-facing contract for the v5 hook adapter.
It is intentionally adapter-neutral: Codex, Claude Code, OpenCode, shell
wrappers, and future agents should call the same `hooks/aitp_v5_hook.py`
entrypoints instead of reimplementing policy logic.

## Status

Implemented:

- shell-facing `pre-commit` adapter;
- shell-facing `pre-tool` adapter;
- shell-facing `post-tool` trace-event adapter;
- typed `runtime_hook_protocols` metadata in v5 adapter packets;
- derived `runtime_hook_installation` templates in v5 adapter packets;
- Codex hook bridge writer derived from `runtime_hook_installation`;
- CLI/MCP materializers for the Codex hook bridge from an actual adapter packet;
- OpenCode plugin bridge writer derived from `runtime_hook_installation`;
- CLI/MCP materializers for the OpenCode plugin bridge from an actual adapter
  packet;
- Claude Code hook settings writer derived from `runtime_hook_installation`;
- Claude Code safe settings merge installer that preserves existing settings and
  deduplicates AITP v5 hook commands;
- Claude Code `PreToolUse` wrapper maps destructive, remote, and expensive Bash
  tool JSON to a typed v5 policy block and Claude `permissionDecision=deny`;
- Claude Code `PreToolUse` wrapper maps coarse AITP MCP/kernel calls into v5
  actions, denying unqualified direct trust application and logging typed writes
  such as evidence recording;
- Claude Code `PreToolUse` wrapper resolves active typed claim context for
  validation and L2 promotion MCP calls, reusing kernel policy for evidence and
  code-state requirements before tool execution;
- trust-update preflight emits request-bound `preflight_token`/`preflight_proof`
  fields, and trust apply requires the matching token before changing typed
  claim confidence;
- Claude Code hook wrapper that can persist `PostToolUse` traces through the v5
  trace bridge;
- CLI/MCP runtime bridge for persisting `post-tool` hook trace events through
  `.aitp/runtime/hook_trace_events.jsonl`;
- short JSON output with `summary_inputs_trusted=false`.

Documented here:

- how Codex, Claude Code, and OpenCode adapters should wire those entrypoints;
- what each platform adapter must supply;
- which outputs are authoritative and which are orientation-only.

Not implemented in this slice:

- one-click installer wiring for Codex, Claude Code, or OpenCode native hook
  configuration.

## Invariants

- Hook adapters are thin surfaces over `brain/v5/hooks.py`,
  `brain/v5/policy.py`, and `brain/v5/trace.py`.
- Hook output is not a truth source.
- `summary_inputs_trusted` must remain `false`.
- A `post-tool` hook emits a serialized `TraceEvent`; it does not write
  evidence or change claim confidence.
- Any adapter that wants durable trace history must persist the returned event
  through `aitp-v5 trace hook-event persist` or
  `aitp_v5_persist_hook_trace_event`, not by editing summary files.
- Decision hooks may block through exit code `2`; trace hooks exit `0`.

## Common Command Contract

The same contract is available to external runtimes through each v5 adapter
packet under `runtime_hook_protocols`. That metadata is the typed source for
installer templates. Adapter packets also include `runtime_hook_installation`,
which is generated from `runtime_hook_protocols` so Codex/Claude/OpenCode bridges
do not need to duplicate hook commands. This Markdown page explains the same
contract for humans.

Run from the AITP repository root, or replace `hooks\aitp_v5_hook.py` with an
absolute path.

### Pre-Commit

```powershell
python hooks\aitp_v5_hook.py pre-commit `
  --changed-file brain/v5/policy.py `
  --test-ref tests/test_v5_policy.py `
  --evolution-note "tighten policy after repeated incident"
```

Adapter responsibility:

- pass every staged or candidate changed file as `--changed-file`;
- pass every relevant regression test as `--test-ref`;
- pass a concise evolution note when the change modifies harness behavior.

Expected output:

- `kind=hook_decision`;
- `exit_code=2` when a harness change lacks tests or an evolution note;
- `summary_inputs_trusted=false`.

### Pre-Tool

```powershell
python hooks\aitp_v5_hook.py pre-tool `
  --action promote_to_l2 `
  --risk-level adversarial `
  --policy-json '{"allowed":false,"action":"promote_to_l2","reasons":[{"policy_id":"no_l2_promotion_without_evidence_ref","message":"missing evidence","severity":"block"}],"required_actions":["attach_evidence_ref"]}'
```

Adapter responsibility:

- evaluate or retrieve the typed v5 `PolicyDecision` before calling this hook;
- pass the decision as `--policy-json`, or as `--policy-json @path`;
- map the platform tool event to a protocol action such as `promote_to_l2`,
  `change_claim_confidence`, `remote_execution`, or `expensive_compute`.

Expected output:

- `kind=hook_decision`;
- `mode=log`, `warn`, or `block`;
- `exit_code=2` only for blocking decisions;
- `summary_inputs_trusted=false`.

### Post-Tool

```powershell
python hooks\aitp_v5_hook.py post-tool `
  --session-id s1 `
  --topic-id fqhe `
  --claim-id claim-fqhe `
  --risk-level guided `
  --tool-name exact-diagonalization `
  --evidence-status supports
```

Adapter responsibility:

- provide the active session/topic/claim identifiers from typed v5 state;
- pass the tool name and evidence status as process metadata;
- persist the returned trace event through the v5 trace bridge when durable
  post-tool logging is desired.

Expected output:

- `kind=hook_trace_event`;
- `event` is a serialized v5 `TraceEvent`;
- `exit_code=0`;
- `summary_inputs_trusted=false`.

Persistence command:

```powershell
aitp-v5 --base <workspace> trace hook-event persist --payload-json '<hook_trace_event_json>'
```

MCP persistence wrapper:

```text
aitp_v5_persist_hook_trace_event(base, hook_payload)
```

Persistence output:

- `kind=hook_trace_event_record`;
- appends to `.aitp/runtime/hook_trace_events.jsonl`;
- `can_update_claim_trust=false`;
- does not create evidence, memory, validation, or confidence records.

## Codex Template

Codex currently uses AITP primarily through skills, MCP, runtime entrypoints, and
the repository workflow. Until a native Codex lifecycle hook installer exists,
the Codex-facing runtime should treat these commands as explicit guard calls.

Recommended placement:

- include this document in Codex AITP runtime instructions;
- read `runtime_hook_installation` from the v5 adapter packet when available;
- call `pre-commit` before committing any v5 harness, policy, migration, hook,
  or public-surface change;
- call `pre-tool` before trust-changing actions, L2 promotion, remote execution,
  destructive actions, or expensive compute;
- call `post-tool` after meaningful physics/numerical/literature tool runs when
  active session/topic/claim IDs are known;
- pass the returned `hook_trace_event` to `aitp-v5 trace hook-event persist`
  when the event should survive the current process.

Codex must not infer a trust update from the hook output. If a hook says a tool
run supported a claim, that is process history only until typed evidence and
trust-update records are written.

The repo-backed bridge writer is
`brain.v5.hook_install_templates.write_codex_hook_bridge`. It writes a compact
Markdown guide from `runtime_hook_installation` and deliberately marks the output
as orientation-only.

For an actual v5 workspace/session, materialize it through the public runtime
surface instead of calling the helper by hand:

```powershell
aitp-v5 --base <workspace> adapter hook-bridge codex <session-id> --output .codex/AITP_V5_HOOK_BRIDGE.md
```

MCP clients use:

```text
aitp_v5_write_codex_hook_bridge(base, session_id, output_path)
```

Both surfaces return a contracted `codex_hook_bridge` payload and keep
`summary_inputs_trusted=false`.

## Claude Code Template

Claude Code has existing AITP SessionStart and PreToolUse integration for the
legacy harness. A v5 Claude adapter should keep that bootstrap, but route v5
policy decisions through `hooks/aitp_v5_hook.py`.

Recommended mapping:

- SessionStart: load AITP skills and current execution brief.
- PreToolUse: translate the platform tool event into a v5 action, obtain a
  typed `PolicyDecision`, then call `pre-tool`.
- PostToolUse: call `post-tool` with active v5 identifiers and persist the
  returned trace event through `aitp_v5_persist_hook_trace_event`.
- Pre-commit or Stop-time repository guard: call `pre-commit` for staged
  harness changes before allowing a commit recommendation.

The repo-backed settings writer is available through:

```powershell
aitp-v5 --base <workspace> adapter hook-settings claude-code <session-id> --output .claude/settings.local.json
```

The safe merge installer is available through:

```powershell
aitp-v5 --base <workspace> adapter install-hooks claude-code <session-id> --settings .claude/settings.local.json
```

MCP clients use:

```text
aitp_v5_write_claude_code_hook_settings(base, session_id, output_path)
aitp_v5_install_claude_code_hook_settings(base, session_id, settings_path)
```

The generated settings follow Claude Code's native hook JSON shape:
`hooks -> PreToolUse/PostToolUse -> matcher -> command`. They call
`hooks/aitp_v5_claude_hook.py`, which reads Claude Code hook JSON from stdin.
This shape follows the Claude Code hooks reference:
https://code.claude.com/docs/en/hooks.
The current wrapper:

- maps `PreToolUse` to a v5 pre-tool decision and returns Claude
  `hookSpecificOutput.permissionDecision`; destructive, remote, and expensive
  Bash commands currently deny with `request_human_checkpoint`;
- maps AITP MCP entrypoints such as `aitp_v5_record_evidence` and
  `aitp_v5_apply_trust_update` to v5 actions; direct trust application without
  a trusted `tool_input.source_kind` and `trust-preflight-*` token denies with
  `aitp_v5_preflight_trust_update`;
- maps validation and L2-promotion entrypoints through active typed claim
  context; code-method validation without code state warns with
  `record_code_state`, and L2 promotion without evidence blocks with
  `attach_evidence_ref`;
- maps `PostToolUse` to a v5 `TraceEvent` and persists it through
  `.aitp/runtime/hook_trace_events.jsonl`;
- keeps `summary_inputs_trusted=false` and `can_update_claim_trust=false`.

## OpenCode Template

OpenCode should use the same contract as Codex and Claude Code:

- runtime/plugin setup loads the AITP skills and MCP server;
- before high-risk tool calls, the OpenCode adapter computes a v5 policy packet
  and calls `pre-tool`;
- after tool calls, the adapter calls `post-tool` and persists trace events only
  through `aitp_v5_persist_hook_trace_event` or the matching CLI command;
- before repository commits, it calls `pre-commit` with changed files, test refs,
  and evolution note.

OpenCode adapters should avoid writing generated summaries as state. Any compact
view should be treated as orientation-only.

The repo-backed OpenCode plugin bridge writer is available through:

```powershell
aitp-v5 --base <workspace> adapter hook-bridge opencode <session-id> --output .opencode/AITP_V5_PLUGIN_BRIDGE.md
```

MCP clients use:

```text
aitp_v5_write_opencode_plugin_bridge(base, session_id, output_path)
```

The generated bridge records lifecycle calls and the persistence entrypoint, but
it is still orientation-only. OpenCode must write durable state through typed v5
kernel records and `aitp_v5_persist_hook_trace_event`.

## Installer Work Still Needed

Future implementation should add tests and installer assets for:

- Codex runtime instructions or hook bridge that can call this adapter directly;
- native OpenCode plugin invocation that calls the generated bridge automatically;
- broader Claude Code `PreToolUse` typed policy coverage beyond current Bash,
  trust-apply token, validation, and promotion mapping.
