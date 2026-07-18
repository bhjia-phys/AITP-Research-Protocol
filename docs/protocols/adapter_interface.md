# Adapter Interface

Domain: Interaction
Authority: subordinate to `docs/AITP_SPEC.md` and the v5 typed kernel.

## AD1. Role And Authority

AITP adapters connect a research host to the v5 operating-memory kernel. They
translate host-native lifecycle events, deliver bounded context, enforce
pre-tool policy, and report exact process events. They do not define scientific
policy, choose a topic silently, or become a second source of research truth.

AITP v5 is the only production research lifecycle. Legacy L0-L4 material is
available only for read, audit, migration, schema-v1 compatibility, and write
blocking. An adapter must never enable or repair the legacy candidate, stage,
promotion, or graph-write workflow as part of normal research.

## AD2. Required Host Flow

A host integration must preserve this progressive flow:

1. Route the first relevant request to a small route hint or explicit v5 entry
   operation.
2. Resolve an existing `SessionBinding`; do not select or rebind a topic from
   keyword matches alone.
3. Prepare startup or normal bounded context through the shared context
   compiler. Expand exact record families only when the active task needs them.
4. Evaluate risky tools through the existing pre-tool policy.
5. Send completed tool events through the research-moment controller. Exact,
   low-noise process capture may be automatic; semantic content remains staged
   and review gated.
6. At a durable milestone, expose a coalesced recording review or an explicit
   closeout plan. Do not turn every tool call into canonical memory.

Adapter text, hook output, retrieval, summaries, RAG results, and Skill content
are orientation or process inputs. None of them is scientific evidence.

## AD3. Host-Neutral Lifecycle Contract

Every supported native event is normalized into exactly one logical event:
`session_start`, `prompt_submit`, `pre_tool`, `post_tool`, or `session_end`.
The normalized record contains a stable event id, host/session identity,
allowlisted scalar process fields, and an origin marker. Raw host payloads and
prompts are not persisted.

The dispatch layer is fail-closed:

| Logical event | Allowed effect |
|---|---|
| `session_start` | prepare one runtime-only bounded context delivery |
| `prompt_submit` | prepare one runtime-only bounded context delivery |
| `pre_tool` | delegate to existing read-only policy evaluation |
| `post_tool` | append runtime trace or delegate one validated bounded research moment |
| `session_end` | produce `plan_session_closeout`; application remains explicit and reviewed |

Host lifecycle code cannot write trusted evidence, update claim trust, accept a
baseline, bind or rebind a session, promote memory, install or patch a Skill, or
apply closeout. A validated research-moment decision may use only the authority
already declared by its capability contract.

## AD4. Current Host Capability Matrix

This matrix describes the generated owner APIs in the repository. It is not an
installation or readiness claim for any particular workspace.

| Host | Automatically owned events after installation | Unsupported automatic events | Required fallback |
|---|---|---|---|
| Claude Code | SessionStart, PreToolUse, PostToolUse | prompt submit, session end | Session start prepares context; use `plan_session_closeout` explicitly |
| Kimi Code | SessionStart, PreToolUse, PostToolUse | prompt submit, session end | Session start prepares context; use `plan_session_closeout` explicitly |
| Codex | PreToolUse, PostToolUse | session start, prompt submit, session end | First relevant turn uses `aitp_v5_codex_enter`; closeout is plan-only |
| OpenCode | tool.execute.before, tool.execute.after | session start, prompt submit, session end | First relevant turn uses `begin_research_turn`; closeout uses `plan_session_closeout` |

Codex and OpenCode do not infer a session start from pre/post-tool traffic. The
host or agent must call the idempotent first-turn facade when research becomes
relevant. No host may claim automatic closeout when only pre/post-tool events
are installed.

OpenClaw has no release-supported v5 lifecycle installer. A manual MCP
connection is allowed, but it is not part of this capability matrix and must not
claim automatic lifecycle coverage.

## AD5. Context Delivery

All host context uses the same bounded context compiler and named profiles.
Startup orientation is capped at 800 estimated tokens and 4000 bytes; normal
research context is capped at 1500 estimated tokens and 7500 bytes. A host may
request a smaller budget, never a larger one.

Delivery receipts live below `.aitp/runtime`, use SHA-256 namespace components,
and contain fingerprints, selected refs, coverage, and delivery state rather
than a second copy of the full context. `not_found`, `not_checked`, `not_shown`,
stale index, and partial coverage must remain distinct. A delivery receipt is
not canonical evidence and cannot update claim trust.

## AD6. Installation And Readiness

Generated configuration is workspace-local runtime metadata:

- Codex: `.codex/hooks.json` with PreToolUse and PostToolUse runners.
- Claude Code: `.claude/settings.local.json` with SessionStart, PreToolUse, and
  PostToolUse runners.
- Kimi Code: `.kimi/config.toml` with SessionStart, PreToolUse, and PostToolUse
  runners.
- OpenCode: `.opencode/plugins/aitp-v5.js` with `tool.execute.before` and
  `tool.execute.after` handlers.

The command being present on `PATH` is insufficient. Readiness requires both a
successful process probe and an installed, conflict-free workspace hook audit.
If the command works but installation is missing or conflicting, report
`process_ready_installation_incomplete`; do not count the host as ready. If an
installation audit is skipped, report `process_ready_installation_unverified`.
Unavailable, timed-out, and nonzero commands retain distinct statuses.

Use the full CLI for installation and maintenance:

```text
python -m brain.v5.cli --base <workspace> adapter install-paths
python -m brain.v5.cli --base <workspace> adapter install-hooks <runtime> <session-id> <path-option> <path>
python -m brain.v5.cli --base <workspace> adapter install-audit <runtime> <path-option> <path>
python -m brain.v5.cli --base <workspace> adapter host-readiness <runtime>
python -m brain.v5.cli --base <workspace> adapter host-lifecycle <runtime>
```

Lifecycle smoke submits an allowlisted fixture through stdin and records only
the fixture event identity and payload hash. A successful version command does
not prove that the host emitted a lifecycle event.

## AD7. Skill And Prompt Boundary

Hosts may register packaged AITP Skills with their native Skill discovery
mechanism. They must not inject the complete gateway Skill, all topic
`MEMORY.md` bodies, legacy stage instructions, or generated Skill packages into
the system prompt. The route hint and bounded context compiler are the only
normal automatic research-context paths.

OpenCode's repository bootstrap registers a Skill search path. The separately
generated lifecycle plugin owns pre/post-tool events. Old OpenCode
configurations that injected complete Skill or memory bodies are reported as
conflicts and may be replaced only with an exact content-bound, human-reviewed
host-install plan.

Procedural Skill detection, proposal, installation, use evidence, and patching
remain the reviewed v5 Skill lifecycle. Hooks cannot draft, install, update, or
apply a Skill.

## AD8. Human And Trust Boundaries

Hosts present human checkpoints but do not manufacture approval. A trust,
installation, or other high-authority mutation requires the exact checkpoint
and host-verified receipt defined by the owning v5 operation. Descriptive actor
text is not approval authority.

Adapters must preserve these distinctions:

- process observation versus scientific evidence;
- staged semantic candidate versus accepted canonical record;
- installed Skill guidance versus verified run evidence;
- cross-topic reference versus transferred trust;
- prepared closeout plan versus applied closeout.

## AD9. Conformance Claims

An adapter may claim only the capabilities demonstrated by its generated owner,
installation audit, and current smoke evidence. Repository fixture coverage is
not proof that a user's local host is installed. A real-host audit is runtime
evidence for that invocation, not a guarantee about every future UI or session
mode.

The compact MCP surface remains exactly ten progressive research tools.
Installation, readiness, lifecycle probing, and replacement-plan operations are
full-MCP/CLI maintenance surfaces and must not expand compact startup context.

## AD10. New Host Requirements

A new host integration must:

1. characterize the native configuration owner and actual event names first;
2. normalize only observed events into the shared logical event contract;
3. declare every unsupported event and explicit fallback;
4. install workspace-local runtime metadata through a reviewable owner;
5. pass writer-sentinel, recursion, timeout, failure, context-budget, and
   installation-audit tests;
6. preserve v5 canonical, human-checkpoint, Skill, and legacy boundaries;
7. report unavailable or incomplete support truthfully rather than emulating a
   stronger lifecycle in hidden prompt logic.
