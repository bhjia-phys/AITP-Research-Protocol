---
name: aitp-runtime
description: Use after AITP v5 routing has claimed a theoretical-physics task; continue the work through typed records, validation gates, and summary regeneration instead of ad hoc notes.
---

# AITP Runtime v5 - Kimi Code

## Runtime Loop

Every real research turn starts by restoring the typed state:

```text
brief = aitp_v5_get_execution_brief(base=<workspace>, session_id=<session-id>)
relation_map = aitp_v5_get_claim_relation_map(base=<workspace>, session_id=<session-id>)
```

Then decide the next action from the brief:

- Missing definition or object: record a physics object or relation.
- Missing provenance: record code state, evidence, reference location, or tool run.
- Claim needs testing: create or update a validation contract, run the check, then record a validation result.
- Interpretation needed: record a sensemaking report, clearly marked as orientation-only.
- Trust change or L2 memory: use preflight, promotion packet, and human checkpoint gates.
- Failure interpretation: read `relation_map.not_tested_by`,
  `current_conclusion.cannot_say`, `current_blockers`, and
  `next_valid_actions` before treating a failure as support or contradiction.

## Interaction Modes And Lifecycle

Use the lightest mode that preserves truth:

- Progress or prior-topic status questions are read-only. Restore the brief and
  relation map, summarize current claims, blockers, and next valid actions, and
  do not write unless the user asks for a durable handoff or resolves a human
  checkpoint.
- Generic old-knowledge or textbook questions stay outside AITP unless they
  name or affect an existing topic, claim, source, route, or gap. Topic-linked
  answers restore context first, then write only durable corrections, sources,
  gaps, or route changes.
- Light exploratory discussion is read-mostly. Do not create a topic, claim,
  or record just because an idea is interesting; wait until a route, question,
  source, artifact, result, or gap becomes durable.
- Active continuation, derivation, source reading, code/numerical execution,
  validation, contradiction handling, final synthesis, trust update, and L2
  promotion use the full typed runtime loop below.

At session start, first locate the topic/session/claim with recovery tools or a
known session id. The start itself is normally read-only; run recording
navigation only if continuation creates a durable start marker, route choice,
or handoff state that future agents must recover.

At session end, write a handoff only when new durable state exists. The handoff
should name the active claim, typed refs just created or relied on, open proof
or validation gaps, human gates, and the next valid action. Verify the handoff
or typed refs with `aitp_v5_verify_recording_effect`.

## Moment Policy

AITP runtime is not a transcript logger. Record only durable research moments:

- source identity or source location becomes reusable,
- tool/code run completes and produced research-relevant output,
- artifact/report/table/plot/log/raw dump is produced,
- result, anomaly, contradiction, negative result, or failed check is observed,
- proof gap, validation gap, missing provenance, or route blocker is found,
- route is selected, pivoted, abandoned, or split,
- active claim scope/status changes are proposed,
- final answer depends on an active claim,
- trust update, promotion, or human decision is requested,
- session-end handoff creates durable state.

Do not record generic explanation, unaccepted brainstorming, repeated
summaries, tool calls that only inspect files, failed setup checks with no
research information, or old-knowledge answers that do not affect a topic.
Those remain conversation or read-only context.

Use this trigger rule:

```text
research-relevant fact changed or became durable -> classify and navigate
only the agent's local reasoning changed -> do not write
```

For those moments, use progressive navigation:

```text
aitp_v5_classify_recording_candidate(...)
aitp_v5_get_recording_navigation_state(base="{{TOPICS_ROOT}}", session_id=<session-id>, claim_id=<claim-id>)
aitp_v5_expand_recording_slot(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, claim_id=<claim-id>)
<existing typed write or preflight tool named by the slot expansion>
aitp_v5_verify_recording_effect(base="{{TOPICS_ROOT}}", session_id=<session-id>, expected_refs=[...])
```

If the classifier says `ignore` or `defer`, do not write. If a live host does
not expose the recording navigator MCP tools, use the CLI fallback for read-only
navigation and mutate only through existing v5 typed write tools.

The first navigation answer should reveal only topic/session/claim position,
first-level slots, blockers, and recommended moments. Expand exactly one slot
at a time. The slot expansion must name an existing typed write or preflight
tool, the minimum fields, known values, unknown values, and the verification
step.

`recording_navigation_state` is intentionally lightweight first-level
navigation. It uses slot counts and relation-boundary hints; it does not replace
`execution_brief` or `process_graph_slice`. Call those separately only when the
next action really needs full context.

## Typed Record Boundaries

- `execution_brief` is the working control panel.
- The claim relation map (`claim_relation_map`) is a read-only
  conclusion-boundary layer, not evidence.
- `summary_orientation` is useful for reading but is never a truth source.
- Hook config and hook traces are runtime metadata, not evidence by themselves.
- Source assets and reference locations are provenance/context, not claim
  support by themselves.
- A validation result supports only the exact checks and failure modes it covers.
- Partial validation should be recorded as a narrow result, not as a pass for a broad contract.

## Kimi Native Hooks

Kimi Code supports TOML lifecycle hooks. AITP v5 installs:

- `PreToolUse`: checks risky or trust-changing tool calls before execution.
- `PostToolUse`: appends trace events after meaningful tools.

Install:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-hooks kimi-code <session-id> --settings <workspace>/.kimi-code/config.toml
```

Audit:

```powershell
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi/config.toml
python -m brain.v5.cli --base <workspace> adapter install-audit kimi-code --settings <workspace>/.kimi-code/config.toml
```

Smoke coverage is visible through:

```powershell
python -m brain.v5.cli adapter smoke-coverage
```

For Kimi CLI builds that support explicit project paths, launch with project
assets directly:

```powershell
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
kimi --work-dir <workspace> --config-file .kimi-code/config.toml --mcp-config-file .kimi-code/mcp.json --skills-dir .kimi-code/skills
```

## Research Workflow

For a natural physics conversation, keep the user-facing flow simple:

1. Restore the brief.
2. Explain the current claim, uncertainty, and next useful check in plain language.
3. Do the math or computation.
4. Record the durable typed objects, evidence, tool runs, validations, and interpretation.
5. Refresh the brief before stating what is now known.

## Failure Discipline

Record these immediately:

- wrong formula or shortcut
- missing source provenance
- dirty or unknown code state behind a numerical result
- incomplete coverage of a validation contract
- finite-size, operator-choice, gauge, normalization, or sector-selection artifacts
- any conclusion that is interpretation rather than validation
