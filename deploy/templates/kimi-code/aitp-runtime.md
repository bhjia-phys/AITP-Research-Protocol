---
name: aitp-runtime
description: Use after AITP routing has claimed the task; continue theory work through the v2 protocol loop instead of ad hoc browsing or free-form synthesis.
---

# AITP Runtime (v2)

## CRITICAL: Mandatory tool-first behavior

- Topics root is ALWAYS: `{{TOPICS_ROOT}}`
- ALWAYS pass this exact string as `topics_root` to every MCP tool call.
- NEVER use Grep/Glob/Read to inspect AITP topic state. Use MCP tools only.
- ALWAYS call `aitp_get_execution_brief` before deciding what to do next.
- ALWAYS use `AskUserQuestion` for user questions. NEVER type options as plain text.
- BEFORE using AskUserQuestion, you MUST load it first: `ToolSearch(query="select:AskUserQuestion", max_results=1)`

## Environment gate (mandatory first step)

- AITP v2 runs as an MCP server. Tools are available as `mcp__aitp__aitp_*`.
- Read the protocol manual: `{{REPO_ROOT}}/brain/PROTOCOL.md`

## Agent decision loop

Every iteration MUST start with `aitp_get_execution_brief`:

```
TOPICS_ROOT = "{{TOPICS_ROOT}}"

while topic is not complete:
    brief = mcp__aitp__aitp_get_execution_brief(TOPICS_ROOT, topic_slug)

    if brief.gate_status starts with "blocked":
        # Fix the flagged artifact using MCP tools or file edits
        continue

    if brief.gate_status == "ready":
        Match on brief.stage:
            "L1" → Fill remaining L1 artifacts or advance to L3
            "L3" → Work on active subplane artifact, then advance
            "L5" → Fill provenance files, then draft paper
        continue
```

## Popup gates (AskUserQuestion)

### Rule 1: Protocol transition popups

When an MCP tool returns a result containing `popup_gate`, you MUST call `AskUserQuestion` before proceeding:

```
result = mcp__aitp__aitp_advance_to_l3(TOPICS_ROOT, topic_slug)
if result has "popup_gate":
    pg = result["popup_gate"]
    Call AskUserQuestion(questions=[{
        "question": pg["question"],
        "header": pg["header"],
        "options": pg["options"],
        "multiSelect": false,
    }])
```

Tools that may return `popup_gate`:
- `aitp_advance_to_l3` — L1→L3 transition confirmation
- `aitp_submit_candidate` — candidate submission confirmation
- `aitp_request_promotion` — promotion approval gate
- `aitp_submit_l4_review` — non-pass review outcome handling
- `aitp_advance_to_l5` — L4→L5 transition confirmation
- `aitp_retreat_to_l1` — L3→L1 retreat reason

### Rule 2: Clarification popups

Whenever you need to ask the user a question, use `AskUserQuestion`:

```
Call AskUserQuestion(questions=[{
    "question": "<your question here>",
    "header": "Scope",
    "options": [
        {"label": "Option A", "description": "What option A means"},
        {"label": "Option B", "description": "What option B means"},
    ],
    "multiSelect": false,
}])
```

This applies at ALL stages: L1 framing, L3 direction changes, L4 review decisions, L5 writing priorities.

## Workflow

1. Call `aitp_get_execution_brief(TOPICS_ROOT, topic_slug)` to determine current state.
2. Based on the result:
   - **blocked_missing_artifact**: Create the missing file.
   - **blocked_missing_field**: Edit the artifact and fill required frontmatter fields + body headings.
   - **ready + stage=L1**: Fill remaining L1 artifacts, then `aitp_advance_to_l3`.
   - **ready + stage=L3**: Edit active subplane artifact, then `aitp_advance_l3_subplane`.
   - **After distillation**: `aitp_submit_candidate`, then `aitp_create_validation_contract`.
   - **After L4 review pass**: `aitp_render_flow_notebook`, then promote.
   - **After promotion**: `aitp_advance_to_l5`, fill provenance files.
3. After each state change, re-check the execution brief.
4. Do not skip stages. Do not call tools for a later stage while blocked.

## Key constraints

- Only "pass" in L4 review allows promotion.
- `flow_notebook.tex` must exist before advancing to L5.
- L2 writeback is blocked — use promotion gate instead.
- Respect `authority_warning` from query results.

## Flexible navigation

The protocol is NOT strictly linear. You can:

1. **Register sources at any stage**: `aitp_register_source` works during L1, L3, L4, L5. If you discover during L3 analysis that you need more literature, call `aitp_register_source` directly — no stage change needed.

2. **Retreat L3 → L1**: If analysis reveals insufficient sources or wrong framing, call `aitp_retreat_to_l1`. This preserves all L3 work but lets you re-read and re-frame. Then call `aitp_advance_to_l3` again when ready.

3. **Jump within L3 subplanes**: L3 subplanes allow back-edges (analysis → planning, integration → analysis). Use `aitp_advance_l3_subplane` with any allowed target.

4. **Resume after compaction**: After context compaction, call `aitp_get_execution_brief` first to re-orient. The tool returns all the state you need.

## Lane awareness

The lane (`formal_theory`, `toy_numeric`, `code_method`) affects how the agent frames work but does not change gate logic. Match the lane when filling artifacts.

## Skill activation per stage

| Stage | Subplane/Posture | Skill file |
|-------|-----------------|------------|
| L0 | discover | `skill-discover.md` |
| L1 | read | `skill-read.md` |
| L1 | frame | `skill-frame.md` |
| L3 | ideation | `skill-l3-ideate.md` |
| L3 | planning | `skill-l3-plan.md` |
| L3 | analysis | `skill-l3-analyze.md` |
| L3 | result_integration | `skill-l3-integrate.md` |
| L3 | distillation | `skill-l3-distill.md` |
| L4 | verify | `skill-validate.md` |
| L5 | write | `skill-write.md` |

## Conversation style

- Do not expose protocol jargon to the user.
- Report progress in plain language: "I've framed the question, now setting up the derivation plan."
- Ask one question at a time for clarification.
- If the user says `just go`, stop asking and continue execution.
