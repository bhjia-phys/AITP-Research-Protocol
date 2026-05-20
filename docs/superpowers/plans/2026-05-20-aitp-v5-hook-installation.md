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
- short JSON output with `summary_inputs_trusted=false`.

Documented here:

- how Codex, Claude Code, and OpenCode adapters should wire those entrypoints;
- what each platform adapter must supply;
- which outputs are authoritative and which are orientation-only.

Not implemented in this slice:

- one-click installer wiring for Codex, Claude Code, or OpenCode native hook
  configuration;
- automatic persistence of `post-tool` trace events from platform hook output.

## Invariants

- Hook adapters are thin surfaces over `brain/v5/hooks.py`,
  `brain/v5/policy.py`, and `brain/v5/trace.py`.
- Hook output is not a truth source.
- `summary_inputs_trusted` must remain `false`.
- A `post-tool` hook emits a serialized `TraceEvent`; it does not write
  evidence or change claim confidence.
- Any adapter that wants durable trace history must persist the returned event
  through the v5 trace/kernel path, not by editing summary files.
- Decision hooks may block through exit code `2`; trace hooks exit `0`.

## Common Command Contract

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
- persist the returned trace event through the v5 trace path if the platform
  supports durable post-tool logging.

Expected output:

- `kind=hook_trace_event`;
- `event` is a serialized v5 `TraceEvent`;
- `exit_code=0`;
- `summary_inputs_trusted=false`.

## Codex Template

Codex currently uses AITP primarily through skills, MCP, runtime entrypoints, and
the repository workflow. Until a native Codex lifecycle hook installer exists,
the Codex-facing runtime should treat these commands as explicit guard calls.

Recommended placement:

- include this document in Codex AITP runtime instructions;
- call `pre-commit` before committing any v5 harness, policy, migration, hook,
  or public-surface change;
- call `pre-tool` before trust-changing actions, L2 promotion, remote execution,
  destructive actions, or expensive compute;
- call `post-tool` after meaningful physics/numerical/literature tool runs when
  active session/topic/claim IDs are known.

Codex must not infer a trust update from the hook output. If a hook says a tool
run supported a claim, that is process history only until typed evidence and
trust-update records are written.

## Claude Code Template

Claude Code has existing AITP SessionStart and PreToolUse integration for the
legacy harness. A v5 Claude adapter should keep that bootstrap, but route v5
policy decisions through `hooks/aitp_v5_hook.py`.

Recommended mapping:

- SessionStart: load AITP skills and current execution brief.
- PreToolUse: translate the platform tool event into a v5 action, obtain a
  typed `PolicyDecision`, then call `pre-tool`.
- PostToolUse: call `post-tool` with active v5 identifiers and persist the
  returned trace event through the trace/kernel path.
- Pre-commit or Stop-time repository guard: call `pre-commit` for staged
  harness changes before allowing a commit recommendation.

Claude-specific JSON hook configuration should be generated by a future native
installer. This document defines the command contract that installer must call.

## OpenCode Template

OpenCode should use the same contract as Codex and Claude Code:

- runtime/plugin setup loads the AITP skills and MCP server;
- before high-risk tool calls, the OpenCode adapter computes a v5 policy packet
  and calls `pre-tool`;
- after tool calls, the adapter calls `post-tool` and persists trace events only
  through v5 trace/kernel functions;
- before repository commits, it calls `pre-commit` with changed files, test refs,
  and evolution note.

OpenCode adapters should avoid writing generated summaries as state. Any compact
view should be treated as orientation-only.

## Installer Work Still Needed

Future implementation should add tests and installer assets for:

- Codex runtime instructions or hook bridge that can call this adapter directly;
- Claude Code settings/template generation for v5 lifecycle hooks;
- OpenCode plugin or runtime bridge configuration;
- post-tool trace persistence through the v5 kernel rather than stdout-only
  event emission.
