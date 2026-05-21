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
- Codex native `hooks.json` merge installer that preserves existing hooks and
  deduplicates AITP v5 hook commands;
- OpenCode plugin bridge writer derived from `runtime_hook_installation`;
- CLI/MCP materializers for the OpenCode plugin bridge from an actual adapter
  packet;
- CLI/MCP materializers for the OpenCode stdin-runner plugin fixture from an
  actual adapter packet;
- CLI/MCP materializers for an OpenCode project-local plugin file under
  `.opencode/plugins/`, using `tool.execute.before` and `tool.execute.after`;
- CLI/MCP read-only install audit for supplied Codex, Claude Code, and OpenCode
  runtime hook files;
- CLI/MCP read-only install path discovery for workspace-local Codex, Claude
  Code, and OpenCode hook targets;
- Claude Code hook settings writer derived from `runtime_hook_installation`;
- Claude Code safe settings merge installer that preserves existing settings and
  deduplicates AITP v5 hook commands;
- Claude Code `PreToolUse` wrapper maps destructive, remote, and expensive Bash
  tool JSON to a typed v5 policy block and Claude `permissionDecision=deny`;
- Claude Code `PreToolUse` wrapper maps coarse AITP MCP/kernel calls into v5
  actions, denying unqualified direct trust application and logging typed writes
  such as evidence recording;
- Claude Code `PreToolUse` wrapper resolves active typed claim context for
  validation, promotion-packet creation/application, and L2 promotion MCP
  calls, reusing kernel policy for evidence and code-state requirements before
  tool execution;
- shared context-aware pre-tool policy is available as
  `aitp-v5 policy pre-tool <args>` and `aitp_v5_evaluate_pre_tool_policy`,
  returning a contracted `pre_tool_policy_decision` public surface with no
  kernel-state or claim-trust mutation authority;
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

- end-to-end in-host smoke tests that execute generated hooks inside actual
  host runtimes.

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
the repository workflow. Codex can either call these commands explicitly as
guard calls or install them into a native `hooks.json` file with the merge
installer documented below.

Recommended placement:

- include this document in Codex AITP runtime instructions;
- read `runtime_hook_installation` from the v5 adapter packet when available;
- call `pre-commit` before committing any v5 harness, policy, migration, hook,
  or public-surface change;
- call `pre-tool` before trust-changing actions, L2 promotion, remote execution,
  destructive actions, or expensive compute;
- for validation, promotion-packet creation/application, and L2 promotion
  decisions that depend on active claim evidence/code provenance, call
  `aitp-v5 policy pre-tool <action> --session <session-id> ...` or the matching
  MCP wrapper instead of reconstructing policy from generated summaries;
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
as orientation-only. It also writes a machine-readable JSON sidecar next to the
Markdown guide and returns the sidecar as `payload_path`; runtime hook runners
should consume that file, not the Markdown text. The generated payload includes
`pre_tool_event_runner.argv`, a machine-readable command vector for invoking
`aitp-v5 adapter pre-tool-event` with the concrete runtime, session id, sidecar
path, and a `<platform-event-json>` placeholder.

If a host hook supplies the platform event JSON on stdin, use the thin runner:

```powershell
python hooks/aitp_v5_adapter_event_runner.py pre-tool --base <workspace> --runtime codex --session-id <session-id> --bridge-path <payload-path>
```

The runner loads the sidecar, validates the generated runner metadata, fills
runtime/session/pre-tool defaults into the stdin event, and returns the same
`pre_tool_policy_decision` payload and hook exit code. It is a host adapter, not
a truth source. The generated bridge sidecar includes this command vector at
`pre_tool_event_runner.stdin_runner.argv`.

For an actual v5 workspace/session, materialize it through the public runtime
surface instead of calling the helper by hand:

```powershell
aitp-v5 --base <workspace> adapter hook-bridge codex <session-id> --output .codex/AITP_V5_HOOK_BRIDGE.md
```

Codex can also write a native-ish stdin-runner fixture plus the bridge and
sidecar:

```powershell
aitp-v5 --base <workspace> adapter install-hooks codex <session-id> --output .codex/AITP_V5_HOOKS.json
```

That command writes `.codex/AITP_V5_HOOKS.json`,
`.codex/AITP_V5_HOOK_BRIDGE.md`, and `.codex/AITP_V5_HOOK_BRIDGE.json`.
The fixture declares the repository `cwd` for the relative
`hooks/aitp_v5_adapter_event_runner.py` argv. It contains `hooks.pre_tool` for
typed policy decisions and `hooks.post_tool` for appending contracted
`hook_trace_event_record` entries to `.aitp/runtime/hook_trace_events.jsonl`.
It is runtime metadata only; typed kernel records remain authoritative.

For Codex hosts that use a native `hooks.json`, install into the existing file
instead of writing a separate fixture:

```powershell
aitp-v5 --base <workspace> adapter install-hooks codex <session-id> --settings .codex/hooks.json
```

That command preserves existing Codex hook events, adds idempotent `PreToolUse`
and `PostToolUse` command hooks that call
`hooks/aitp_v5_adapter_event_runner.py`, writes the Codex bridge Markdown plus
JSON sidecar, and returns the same contracted `codex_hook_installation` payload.
The hooks file remains runtime metadata; it cannot update kernel state or claim
trust directly.

MCP clients use:

```text
aitp_v5_write_codex_hook_bridge(base, session_id, output_path)
aitp_v5_install_codex_hook_fixture(base, session_id, output_path)
aitp_v5_install_codex_hook_fixture(base, session_id, hooks_path=<hooks.json>)
```

The bridge surface returns a contracted `codex_hook_bridge` payload; the install
surfaces return a contracted `codex_hook_installation` payload. Both keep
`summary_inputs_trusted=false`. The bridge payload also carries
`pre_tool_policy_entrypoint`, pointing to the shared
`pre_tool_policy_decision` CLI/MCP surface for validation and L2-promotion
pre-tool checks. It also carries `gate_protocols` generated from the adapter
packet's `runtime_gate_protocols`, and the generated Markdown renders the
code-state provenance, tool-recipe registration, reference-location pointers, physics-object/relation
graph writes, sensemaking reports, validation-contract, human-checkpoint
request/decision, promotion-packet creation/application, and validate/promote sequences including
`evaluate_pre_tool_policy` before typed record creation, preflight, or promotion.

Adapter packets also encode the same rule in `runtime_gate_protocols`:
`record_code_state`, `register_tool_recipe`, `record_reference_location`, `record_physics_object`,
`record_object_relation`, `record_sensemaking_report`,
`create_validation_contract`, `create_promotion_packet`,
`apply_promotion_packet`, `request_human_checkpoint`,
`decide_human_checkpoint`, `validate_claim`, and `promote_to_l2` sequence
`evaluate_pre_tool_policy` before the trust-relevant step and name
`policy_reasons` as the machine-readable routing field.

Runtime adapters can consume generated bridge gate metadata through
`brain.v5.adapter_runtime.evaluate_bridge_gate_pre_tool_policy`. That helper
checks that the bridge protocol names `aitp_v5_evaluate_pre_tool_policy` and
sequences `evaluate_pre_tool_policy`, then delegates the decision to the shared
typed-record-backed pre-tool policy surface. The bridge remains orientation-only;
the returned decision is still backed by typed kernel records.
Generated gate protocols now cover code-state, record-evidence,
record-tool-run, execute-tool, tool-recipe, reference-location, physics-object,
object-relation, sensemaking-report, subagent-ingestion, validation-contract,
promotion-packet creation/application, human-checkpoint request/decision,
validation, and L2-promotion actions.
`aitp-v5 adapter record-gate-audit` and
`aitp_v5_audit_record_gate_coverage` expose a contracted audit over the same
registry so reviewers can see whether any runtime record protocol lacks a
conscious gate decision.
The shared policy carries `risk_level` and optional `human_checkpoint_id`.
Adversarial-risk trust-changing actions are hard-blocked unless that checkpoint
is a decided typed human checkpoint with `decision=approve` for the active
claim.
Rigorous/adversarial `execute_tool` and `record_tool_run` lifecycle decisions
also require at least one explicit open typed validation contract for the active
claim, passed as `validation_contract_ids`. For high-risk `execute_tool`, the
contract must bind the current `recipe_id` and `executor_id`; for high-risk
`record_tool_run`, it must bind the current `recipe_id`. This keeps heavyweight
numerical or formula-code execution tied to an auditable validation plan for
the actual tool path rather than model intuition.
After execution, `record_validation_result` records whether a completed
`tool_run_id` satisfied the contract's required evidence outputs. Passed
validation results must have no missing outputs and no observed failure modes.
For live-style adapter events, `evaluate_bridge_lifecycle_event` maps an
adapter-neutral `pre_tool` event payload onto the same helper after confirming
that the generated bridge declares a pre-tool lifecycle call. Codex/OpenCode
platform-style pre-tool payloads can be normalized first through
`brain.v5.adapter_runtime.evaluate_platform_pre_tool_event`, which extracts the
AITP action, typed refs, source metadata, and session id before delegating to the
same bridge lifecycle path. Runtime adapters can call the same path without
Python imports through:

```powershell
aitp-v5 adapter pre-tool-event <runtime> <session-id> --bridge-json <json> --event-json <json>
```

Prefer the sidecar form for generated Codex/OpenCode bridges:

```powershell
aitp-v5 adapter pre-tool-event <runtime> <session-id> --bridge-path <payload-path> --event-json <json>
```

or the MCP wrapper:

```text
aitp_v5_evaluate_adapter_pre_tool_event(base, bridge_payload, platform_event)
```

Generated Codex/OpenCode bridge payloads include `pre_tool_event_entrypoint`
metadata with those CLI/MCP targets, the required `bridge_payload` and
`platform_event` inputs, and the same `pre_tool_policy_decision` surface.
The same generated payloads and sidecars expose
`pre_tool_policy_entrypoint.input_schema` and
`pre_tool_event_entrypoint.platform_event_schema`. The schema metadata names
the required policy inputs (`session_id`, `action`, `claim_id`, `risk_level`),
optional typed refs/source metadata including `validation_contract_ids`,
optional `recipe_id`, optional `executor_id`, optional nested `packet` input,
optional `human_checkpoint_id`, and optional `checkpoint_id`; it is a
machine-readable adapter contract, not a truth source.

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
- maps validation, promotion-packet creation/application, and L2-promotion
  entrypoints through active typed claim context; code-method validation without
  code state warns with `record_code_state`, and promotion-packet creation/L2
  promotion without evidence blocks with `attach_evidence_ref`; this path
  reuses the shared
  `brain.v5.pretool_policy.context_policy_decision` kernel helper;
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

This follows the OpenCode plugin contract: project-local plugin files under
`.opencode/plugins/` are loaded automatically, and plugins can return lifecycle
hooks such as `tool.execute.before` from their exported function:
https://opencode.ai/docs/plugins/.

Generated OpenCode bridge payloads include
`plugin_bridge.pre_tool_policy_entrypoint`, pointing to the same
`pre_tool_policy_decision` CLI/MCP surface used by Codex and Claude Code. They
also include `plugin_bridge.gate_protocols`, generated from adapter
`runtime_gate_protocols`, so plugin authors can consume record, validation,
promotion-packet creation/application, and promote sequences without scraping
prose.

The repo-backed OpenCode plugin bridge writer is available through:

```powershell
aitp-v5 --base <workspace> adapter hook-bridge opencode <session-id> --output .opencode/AITP_V5_PLUGIN_BRIDGE.md
```

MCP clients use:

```text
aitp_v5_write_opencode_plugin_bridge(base, session_id, output_path)
aitp_v5_install_opencode_hook_fixture(base, session_id, output_path)
```

The generated bridge records lifecycle calls, gate protocols, and the
persistence entrypoint, and it writes a sibling JSON sidecar exposed as
`payload_path`. Its `plugin_bridge.pre_tool_event_runner.argv` provides the
same sidecar-backed pre-tool event invocation for plugin authors, but it is
still orientation-only. OpenCode must write durable state through typed v5
kernel records and `aitp_v5_persist_hook_trace_event`.
OpenCode hosts that provide event JSON over stdin can use the same
`hooks/aitp_v5_adapter_event_runner.py pre-tool` path with `--runtime opencode`.
The OpenCode bridge sidecar advertises it under
`plugin_bridge.pre_tool_event_runner.stdin_runner.argv`.
OpenCode can also write a native-ish stdin-runner plugin fixture plus the bridge
and sidecar:

```powershell
aitp-v5 --base <workspace> adapter install-hooks opencode <session-id> --output .opencode/AITP_V5_PLUGIN_HOOKS.json
```

That command writes `.opencode/AITP_V5_PLUGIN_HOOKS.json`,
`.opencode/AITP_V5_PLUGIN_BRIDGE.md`, and
`.opencode/AITP_V5_PLUGIN_BRIDGE.json`. The fixture declares the repository
`cwd` for the relative `hooks/aitp_v5_adapter_event_runner.py` argv. It
contains `plugin_hooks.pre_tool` for typed policy decisions and
`plugin_hooks.post_tool` for appending contracted `hook_trace_event_record`
entries to `.aitp/runtime/hook_trace_events.jsonl`. It is runtime metadata only;
typed kernel records remain authoritative.

For an actual project-local OpenCode plugin file, install with:

```powershell
aitp-v5 --base <workspace> adapter install-hooks opencode <session-id> --plugin .opencode/plugins/aitp-v5.js
```

That command writes `.opencode/plugins/aitp-v5.js`, plus
`.opencode/AITP_V5_PLUGIN_BRIDGE.md` and
`.opencode/AITP_V5_PLUGIN_BRIDGE.json`. The plugin subscribes to
`tool.execute.before` and `tool.execute.after`, calls
`hooks/aitp_v5_adapter_event_runner.py`, throws on blocking typed
`pre_tool_policy_decision` output, and logs post-tool trace persistence
failures without giving generated files authority over typed kernel records.

## Install Audit

Before installation, discover workspace-local targets:

```powershell
aitp-v5 --base <workspace> adapter install-paths
```

MCP clients use:

```text
aitp_v5_discover_hook_install_paths(base)
```

The returned `runtime_hook_installation_paths` surface lists preferred and
alternate target paths and matching install/audit commands for Codex, Claude
Code, and OpenCode. This is workspace convention metadata, not kernel state.

After installation, audit the supplied runtime file without trusting it as
kernel state:

```powershell
aitp-v5 --base <workspace> adapter install-audit codex --settings .codex/hooks.json
aitp-v5 --base <workspace> adapter install-audit claude-code --settings .claude/settings.local.json
aitp-v5 --base <workspace> adapter install-audit opencode --plugin .opencode/plugins/aitp-v5.js
```

MCP clients use:

```text
aitp_v5_audit_hook_installation(base, runtime, settings_path?, plugin_path?, output_path?)
```

The returned `runtime_hook_installation_audit` surface reports
`installed`, `partial`, `missing`, or `conflict`, lists checked paths, and keeps
`summary_inputs_trusted=false`, `orientation_only=true`,
`can_update_kernel_state=false`, and `can_update_claim_trust=false`.

## Installer Work Still Needed

Future implementation should add tests and installer assets for:

- in-host smoke tests that execute the generated Codex/OpenCode lifecycle hooks
  in their real host runtimes rather than only through repo-level runner tests.
