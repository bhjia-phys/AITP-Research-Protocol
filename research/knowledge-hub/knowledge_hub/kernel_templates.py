from __future__ import annotations

from pathlib import Path
from typing import Any


def render_session_start_note(payload: dict[str, Any]) -> str:
    routing = payload.get("routing") or {}
    memory_resolution = payload.get("memory_resolution") or {}
    selected_action = payload.get("selected_action") or {}
    must_read_now = payload.get("must_read_now") or []
    linear_flow = payload.get("linear_flow") or []
    hard_stops = payload.get("hard_stops") or []
    human_interaction_posture = payload.get("human_interaction_posture") or {}
    autonomy_posture = payload.get("autonomy_posture") or {}

    memory_summary = str(memory_resolution.get("summary") or "(missing)")
    lines = [
        "# Session start contract",
        "",
        "This file is the durable session-start translation of the latest natural-language request.",
        "Read it before `runtime_protocol.generated.md`, then follow the linear startup order below.",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        f"- Original request: {payload.get('task') or '(missing)'}",
        f"- Route: `{routing.get('route') or '(missing)'}`",
        f"- Routing reason: {routing.get('reason') or '(missing)'}`"[:-1],  # keep string shape stable
        f"- Memory resolution: {memory_summary}",
        f"- Canonical entry: `{payload.get('canonical_entry') or '(missing)'}`",
        "",
        "## Human interaction posture",
        "",
        f"- Requires human input now: `{str(bool(human_interaction_posture.get('requires_human_input_now'))).lower()}`",
        f"- Summary: {human_interaction_posture.get('summary') or '(missing)'}",
        f"- Next action: {human_interaction_posture.get('next_action') or '(missing)'}",
        "",
        "## Autonomous continuation",
        "",
        f"- Mode: `{autonomy_posture.get('mode') or '(missing)'}`",
        f"- Summary: {autonomy_posture.get('summary') or '(missing)'}",
        f"- Requested auto-step budget: `{autonomy_posture.get('requested_max_auto_steps') if autonomy_posture.get('requested_max_auto_steps') is not None else '(none)'}`",
        f"- Applied auto-step budget: `{autonomy_posture.get('applied_max_auto_steps') if autonomy_posture.get('applied_max_auto_steps') is not None else '(none)'}`",
        "",
        "## Read Next",
        "",
    ]
    for index, item in enumerate(must_read_now, start=1):
        lines.append(
            f"{index}. `{item.get('path') or '(missing)'}`"
            + (
                f" - {item.get('reason')}"
                if str(item.get("reason") or "").strip()
                else ""
            )
        )
    if not must_read_now:
        lines.append("1. `(missing)`")
    lines.extend(["", "## Linear Flow", ""])
    for index, item in enumerate(linear_flow, start=1):
        lines.append(
            f"{index}. {item.get('step') or '(missing)'}"
            + (
                f" Result: {item.get('result')}."
                if str(item.get("result") or "").strip()
                else ""
            )
        )
    if not linear_flow:
        lines.append("1. Read the runtime protocol and continue with the bounded action.")
    lines.extend(["", "## Selected Action", ""])
    lines.append(f"- Action id: `{selected_action.get('action_id') or '(none)'}`")
    lines.append(f"- Action type: `{selected_action.get('action_type') or '(none)'}`")
    lines.append(f"- Summary: {selected_action.get('summary') or '(none)'}")
    lines.extend(["", "## Hard Stops", ""])
    for item in hard_stops:
        lines.append(f"- {item}")
    if not hard_stops:
        lines.append("- Do not continue if required runtime artifacts are missing.")
    lines.append("")
    return "\n".join(lines)


def session_start_routing_block(*, hidden_entry: str) -> str:
    return f"""## Session-start routing invariant

Before any substantial response in an AITP-governed workspace:

1. materialize session state through {hidden_entry}
2. check durable current-topic memory first with `aitp current-topic` or `runtime/current_topic.json`
3. if the user says `继续这个 topic`, `continue this topic`, `this topic`, or `current topic`, resolve that to current-topic memory immediately
4. only fall back to latest-topic memory if current-topic memory is missing
5. translate steering requests like `方向改成 X`, `continue this topic but focus on X`, or `先补验证` into durable steering state before substantial execution continues
6. once AITP materializes the runtime bundle, follow `runtime_protocol.generated.md` and its `Must read now` list
7. only ask for a topic slug when both the request and durable memory remain genuinely ambiguous

This rule applies at session start, not later as a soft reminder.
"""


def codex_skill_template(*, kernel_root: Path) -> str:
    session_start = session_start_routing_block(
        hidden_entry="platform bootstrap plus fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
    )
    return f"""---
name: aitp-runtime
description: Route Codex research work through the AITP kernel. Use when the request is a theory topic, current-topic continuation, idea steering, derivation or validation planning, paper-learning task, or other AITP-governed execution instead of plain coding.
---

# AITP Runtime

{session_start}

## Required entry

1. In a bare `codex` research session, do not start with direct browsing or free-form synthesis.
2. Let the installed bootstrap route natural-language research work into AITP first. Use `aitp session-start "<task>"` only as the manual fallback.
3. Once the runtime bundle exists, read `runtime_protocol.generated.md`, then the files listed under `Must read now`.
4. Treat `session_start.generated.md` as a runtime audit artifact when it exists, not as a separate user ritual.
5. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
6. Keep `innovation_direction.md` and `control_note.md` current before touching the queue.
7. Expand promotion, consultation, capability, or queue details only when the named trigger in the runtime bundle fires.
8. Register reusable operations with `aitp operation-init ...`.
9. For human-reviewed `L2`, use `aitp request-promotion ...` and wait for `aitp approve-promotion ...`.
10. For theory-formal `L2_auto`, materialize coverage/consensus artifacts with `aitp coverage-audit ...` and then use `aitp auto-promote ...`.
11. report the current human-control posture and autonomous-continuation posture in plain language after reading `session_start.generated.md` and `runtime_protocol.generated.md`.
12. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.
13. If iterative verify is active, keep the L3-L4 loop moving until success, a real blocker, or a real human checkpoint appears.
14. End with `aitp audit --topic-slug <topic_slug> --phase exit`.
15. When a human-choice surface is active, inspect it with `aitp interaction --topic-slug <topic_slug>`.
16. If the active surface is a formal decision point, answer it with `aitp resolve-decision ...`; if it is an operator checkpoint, answer it with `aitp resolve-checkpoint ...` and include a comment when the choice needs extra steering detail.

## Hard rules

- If the conformance audit fails, the run does not count as AITP work.
- If the task is theoretical-physics research rather than plain coding, staying inside AITP is mandatory.
- Prefer durable control notes and contract files over Python heuristic defaults.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Every reusable operation must pass through `aitp trust-audit ...` before AITP treats it as trusted.
- If a new numerical backend or diagnostic is being trusted, scaffold a baseline first with `aitp baseline ...`.
- If a derivation-heavy method is being claimed as understood, scaffold atomic understanding first with `aitp atomize ...`.
- If there is a capability gap, prefer `aitp loop ... --skill-query ...` so discovery becomes runtime state instead of ad hoc browsing.
- Human-reviewed Layer 2 promotion is blocked until `promotion_gate.json` says `approved` and `aitp promote ...` records the writeback.
- Theory-formal `L2_auto` promotion is blocked until `coverage_ledger.json` passes and `agent_consensus.json` is ready.
- Do not expose protocol jargon in ordinary user-facing dialogue.

## Common commands

```bash
aitp session-start "<task>"
aitp loop --topic-slug <topic_slug> --human-request "<task>" --skill-query "<capability gap>"
aitp resume --topic-slug <topic_slug> --human-request "<task>"
aitp interaction --topic-slug <topic_slug> --json
aitp list-decisions --topic-slug <topic_slug> --pending-only --json
aitp resolve-decision --topic-slug <topic_slug> --decision-id <decision_id> --option <index> --comment "<why>"
aitp resolve-checkpoint --topic-slug <topic_slug> --option <index> --comment "<why>"
aitp coverage-audit --topic-slug <topic_slug> --candidate-id <candidate_id> --source-section <section> --covered-section <section>
aitp request-promotion --topic-slug <topic_slug> --candidate-id <candidate_id> --backend-id backend:theoretical-physics-knowledge-network
aitp approve-promotion --topic-slug <topic_slug> --candidate-id <candidate_id>
aitp promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp auto-promote --topic-slug <topic_slug> --candidate-id <candidate_id> --target-backend-root <tpkn_root>
aitp operation-init --topic-slug <topic_slug> --run-id <run_id> --title "<operation>" --kind numerical
aitp operation-update --topic-slug <topic_slug> --run-id <run_id> --operation "<operation>" --baseline-status passed
aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>
aitp capability-audit --topic-slug <topic_slug>
aitp audit --topic-slug <topic_slug> --phase exit
aitp baseline --topic-slug <topic_slug> --run-id <run_id> --title "<baseline title>" --reference "<source>" --agreement-criterion "<criterion>"
aitp atomize --topic-slug <topic_slug> --run-id <run_id> --method-title "<method title>"
```

Kernel root default: `{kernel_root}`
"""


def using_aitp_skill_template(*, platform: str) -> str:
    if platform == "codex":
        runtime_reference = "the installed `aitp-runtime` skill plus Codex native skill discovery"
        entry_commands = "`aitp session-start \"<task>\"`, `aitp new-topic ...`, `aitp resume ...`, `aitp loop ...`, or `aitp bootstrap ...`"
        hidden_entry = "platform bootstrap with fallback `aitp session-start \"<original request>\"`"
    elif platform == "claude-code":
        runtime_reference = "the installed `aitp-runtime` skill, the `using-aitp` gatekeeper, and the Claude SessionStart bootstrap"
        entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
        hidden_entry = "the Claude bootstrap with fallback `aitp session-start \"<original request>\"`"
    elif platform == "opencode":
        runtime_reference = "the installed `aitp-runtime` skill, the `using-aitp` gatekeeper, and the OpenCode plugin bootstrap"
        entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
        hidden_entry = "the OpenCode bootstrap with fallback `aitp session-start \"<original request>\"`"
    else:
        runtime_reference = "the installed `aitp-runtime` skill"
        entry_commands = "`aitp session-start \"<task>\"`, `aitp loop ...`, `aitp resume ...`, or `aitp bootstrap ...`"
        hidden_entry = "plain `aitp session-start \"<original request>\"`"

    session_start = session_start_routing_block(hidden_entry=hidden_entry)

    return f"""---
name: using-aitp
description: Use when starting any conversation in a workspace where AITP is installed, or when the user says things like `继续这个 topic`, `continue this topic`, `current topic`, `开一个新 topic`, `方向改成 X`, asks to study a paper, evaluate an idea, plan a derivation, or set a validation route. Establishes whether work must first enter AITP before ANY substantial response.
---

# Using AITP

Use this skill to decide whether the current task must be governed by AITP
before you do substantial work.

<EXTREMELY-IMPORTANT>
If there is even a small chance the task is non-trivial theoretical-physics
research, theory-to-code validation, idea evaluation, literature-grounded
scientific synthesis, or protocol-governed topic work, you MUST enter AITP
first through {entry_commands}.

Do not start with free-form browsing, free-form explanation, or ad hoc file
editing if the task should actually be inside AITP.
</EXTREMELY-IMPORTANT>

{session_start}

## Mandatory triage

Before doing substantial work, classify the task into one of these buckets:

1. `AITP research execution`
   - a real research topic, idea, paper set, validation target, derivation,
     benchmark, or theory-side execution loop
2. `AITP protocol / tooling maintenance`
   - editing the AITP repo itself, its docs, adapters, tests, or installer
3. `plain coding outside AITP`
   - normal software work that does not claim to be AITP-governed research

## Hard gate

If the task is bucket `1`, you MUST:

1. enter through {runtime_reference}
2. materialize or resume runtime state
3. make sure `innovation_direction.md` and `control_note.md` are current before substantial execution continues
4. if the operator speaks in natural steering language such as `继续这个 topic，方向改成 X`, translate that request into durable steering artifacts before continuing
5. read `runtime_protocol.generated.md`
6. read the files named under `Must read now`
7. treat `session_start.generated.md` as a backend routing artifact when it exists, not as a user-facing entry ritual
8. report the current human-control posture in plain language before deeper work
9. if no active checkpoint is present, continue bounded execution instead of asking ritual permission again
10. only then continue with the task

If conformance fails, the work does not count as AITP work.

## Conversation style rules

- Do not expose protocol jargon to the user. Avoid phrases like `decision_point`, `L2 consultation`, or `load profile`.
- Ask in plain research language.
- By default ask one question at a time.
- If the user already gave enough direction, do not ask just to satisfy a workflow ritual.
- If the user says `you decide`, `just go`, or `直接做`, treat that as authorization to proceed and record the durable trace in the background.

## Natural-language routing

Do not make the user translate a clear research request into AITP shell syntax
when the intent is already recoverable from durable routing memory.

Preferred hidden routing:

- If the user is clearly opening a new research topic, for example `开一个新 topic：Topological phases from modular data`, extract the topic title and route through `aitp session-start "<original request>"` or the platform bootstrap.
- If the user says `继续这个 topic`, `continue this topic`, `current topic`, or otherwise refers to the active topic without naming a slug, route through `aitp session-start "<original request>"` or the platform bootstrap, letting current-topic memory win first.
- If the user says `方向改成 X`, `continue this topic but focus on X`, `先补验证`, or another steering phrase, translate it into durable steering artifacts before continuing.
- Resolve current-topic memory first and only fall back to the latest topic if that memory is missing.
- If the user names a known topic slug, preserve that slug and continue without asking for it again.
- Only ask the user to specify a topic manually when the topic reference is genuinely ambiguous.

The user experience target is: natural language first, AITP commands hidden in
the implementation path.

## Allowed exception

If the task is bucket `2`, you may work on the AITP codebase directly without
opening a topic shell, but you must preserve:

- the `L0 -> L1 -> L3 -> L4 -> L2` ontology
- research-execution guardrails
- promotion and audit semantics
- adapter/runtime install consistency

## Red flags

These thoughts mean you are about to drift out of AITP discipline:

- "I'll just answer the research question directly first."
- "I only need a quick literature summary."
- "I can inspect files before deciding whether AITP applies."
- "This is probably too small to need runtime state."
- "I'll come back and register the topic later."

If one of those is true and the task is research-governed, stop and enter AITP
first.

## Practical rule

- Research task: route through AITP first.
- AITP repo maintenance task: edit code/docs/tests directly, but keep AITP
  contracts strict.
- When uncertain: bias toward entering AITP, not away from it.
"""


def claude_code_skill_template(*, kernel_root: Path) -> str:
    session_start = session_start_routing_block(
        hidden_entry="the Claude SessionStart bootstrap, with fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
    )
    return f"""---
name: aitp-runtime
description: Route Claude Code through the AITP runtime so natural-language research requests like `继续这个 topic`, new-topic creation, idea steering, and theory validation work become durable AITP state before execution.
---

# AITP Runtime For Claude Code

{session_start}

## Required entry

1. Let the Claude SessionStart bootstrap route natural-language research work into AITP before any substantial response. Use `aitp session-start "<task>"` only as the manual fallback.
2. Use `aitp loop ...` or `aitp resume ...` after AITP has materialized the topic shell.
3. Use `aitp bootstrap ...` only to create a new topic, then return to `aitp loop ...`.
4. Read `runtime_protocol.generated.md`, then follow its `Must read now` list before deeper work.
5. Treat `session_start.generated.md` as a routing audit artifact when it exists.
6. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
7. Expand deferred surfaces only when the named trigger fires.
8. Treat missing conformance as a hard failure for AITP work.
9. report the current human-control posture in plain language before deeper work.
10. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.
11. If iterative verify is active, keep the bounded verify loop running until success, a real blocker, or a real human checkpoint appears.
12. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.
13. When a human-choice surface is active, inspect it with `aitp interaction --topic-slug <topic_slug>`.
14. If the active surface is a formal decision point, answer it with `aitp resolve-decision ...`; if it is an operator checkpoint, answer it with `aitp resolve-checkpoint ...` and include a comment when the choice needs extra steering detail.

## Hard rules

- Charter first, adapter second.
- Contracts before hidden heuristics.
- Do not silently upgrade exploratory output into reusable knowledge.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming method reuse.
- Do not expose protocol jargon in ordinary user-facing dialogue.

Kernel root default: `{kernel_root}`
"""


def opencode_skill_template(*, kernel_root: Path) -> str:
    session_start = session_start_routing_block(
        hidden_entry="the OpenCode plugin bootstrap, with fallback `aitp session-start \"<original request>\"` when you need to materialize routing explicitly"
    )
    return f"""---
name: aitp-runtime
description: Route OpenCode through the AITP runtime so natural-language research requests like `继续这个 topic`, new-topic creation, idea steering, and theory validation work become durable AITP state before execution.
---

# AITP Runtime For OpenCode

{session_start}

## Required entry

1. Let the OpenCode plugin bootstrap route natural-language research work into AITP before any substantial response. Use `aitp session-start "<task>"` only as the manual fallback.
2. Use `aitp loop ...` or `aitp resume ...` after AITP has materialized the topic shell.
3. Use `aitp bootstrap ...` only to create a new topic, then return to `aitp loop ...`.
4. Read `runtime_protocol.generated.md`, then follow its `Must read now` list before deeper work.
5. Treat `session_start.generated.md` as a routing audit artifact when it exists.
6. Ordinary topic work should stay in the light runtime profile unless a benchmark mismatch, scope change, promotion step, or explicit deep check forces the full profile.
7. Expand deferred surfaces only when the named trigger fires.
8. Treat missing conformance as a hard failure for AITP work.
9. report the current human-control posture in plain language before deeper work.
10. If no active checkpoint is present, continue bounded execution instead of asking ritual permission again.
11. If iterative verify is active, keep the bounded verify loop running until success, a real blocker, or a real human checkpoint appears.
12. Close with `aitp audit --topic-slug <topic_slug> --phase exit`.
13. When a human-choice surface is active, inspect it with `aitp interaction --topic-slug <topic_slug>`.
14. If the active surface is a formal decision point, answer it with `aitp resolve-decision ...`; if it is an operator checkpoint, answer it with `aitp resolve-checkpoint ...` and include a comment when the choice needs extra steering detail.

## Hard rules

- OpenCode should feel natural-language first, but routing must still become durable AITP state immediately.
- Keep `innovation_direction.md` and `control_note.md` current before substantial execution continues.
- Use `aitp baseline ...`, `aitp atomize ...`, and `aitp trust-audit ...` before claiming reusable method progress.
- Do not expose protocol jargon in ordinary user-facing dialogue.

Kernel root default: `{kernel_root}`
"""


def openclaw_skill_template(*, kernel_root: Path) -> str:
    return f"""---
name: aitp-runtime
description: Enter the AITP kernel from OpenClaw using the `aitp` CLI and `mcporter` bridge so the run stays auditable, resumable, and conformance-checked.
---

# AITP Runtime For OpenClaw

Use this skill when the task belongs inside AITP rather than a free-form note workflow.

## Start here

```bash
aitp loop --topic-slug <topic_slug> --human-request "<task>"
```

Then read `topics/<topic_slug>/runtime/runtime_protocol.generated.md` and follow its `Must read now` and `Escalate only when triggered` sections before acting on the queue. Do not bypass the loop and jump straight into ad hoc browsing or execution.

If the topic does not exist yet:

```bash
aitp bootstrap --topic "<topic>" --statement "<statement>"
```

## Before finishing

```bash
aitp audit --topic-slug <topic_slug> --phase exit
```

## Structured tool path

If you need the structured AITP MCP tool surface from OpenClaw, use the `aitp`
server registered in `mcporter`.

## Trust gates

- Reusable operations require `aitp operation-init ...` and `aitp trust-audit ...`
- Numerical novelty requires `aitp baseline ...`
- Theory-method understanding requires `aitp atomize ...`
- Human-reviewed Layer 2 promotion requires `aitp request-promotion ...`, a human `aitp approve-promotion ...`, and only then `aitp promote ...`
- Theory-formal `L2_auto` promotion requires `aitp coverage-audit ...` and then `aitp auto-promote ...`

Kernel root default: `{kernel_root}`
"""
