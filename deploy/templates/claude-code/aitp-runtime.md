---
name: aitp-runtime
description: Use after AITP routing has claimed the task; continue theory work through the v4 protocol loop instead of ad hoc browsing or free-form synthesis.
---

# AITP Runtime (v4)

## CRITICAL: Mandatory tool-first behavior

- Topics root is ALWAYS: `{{TOPICS_ROOT}}`
- ALWAYS pass this exact string as `topics_root` to every MCP tool call.
- NEVER use Grep/Glob/Read to inspect AITP topic state. Use MCP tools only.
- ALWAYS call `aitp_get_execution_brief` before deciding what to do next.
- ALWAYS use `AskUserQuestion` for user questions. NEVER type options as plain text.
- BEFORE using AskUserQuestion, load it: `ToolSearch(query="select:AskUserQuestion", max_results=1)`

## Environment gate (mandatory first step)

- AITP runs as an MCP server. Tools are available as `mcp__aitp__aitp_*`.
- Protocol manual: `{{REPO_ROOT}}/brain/PROTOCOL.md`

## Agent decision loop

Every iteration MUST start with `aitp_get_execution_brief`:

```
TOPICS_ROOT = "{{TOPICS_ROOT}}"

while topic is not complete:
    brief = mcp__aitp__aitp_get_execution_brief(TOPICS_ROOT, topic_slug)

    if brief.gate_status starts with "blocked":
        # Fix the flagged artifact using MCP tools
        continue

    if brief.gate_status == "ready":
        Match on brief.stage:
            "L0" → Register sources, fill source_registry.md, advance to L1
            "L1" → Fill remaining L1 artifacts or advance to L3
            "L3" → Work on active activity (ideate/derive/gap-audit/integrate/distill)
            "L4" → Submit L4 review, then return to L3 for analysis
        continue
```

## Popup gates (AskUserQuestion)

When an MCP tool returns a result containing `popup_gate`, call `AskUserQuestion` before proceeding:

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
- `aitp_retreat_to_l1` — L3→L1 retreat reason

## Workflow

1. Call `aitp_get_execution_brief(TOPICS_ROOT, topic_slug)` to determine current state.
2. Based on the result:
   - **blocked_missing_artifact**: Create the missing file.
   - **blocked_missing_field**: Edit the artifact and fill required frontmatter fields + body headings.
   - **ready + stage=L0**: Register sources, fill source_registry.md, then `aitp_advance_to_l1`.
   - **ready + stage=L1**: Fill remaining L1 artifacts, then `aitp_advance_to_l3`.
   - **ready + stage=L3**: Work on active activity, call `aitp_switch_l3_activity` to change.
   - **After distillation**: `aitp_submit_candidate`, then advance to L4 for validation.
   - **After L4 review pass**: `aitp_return_to_l3_from_l4` to analyze results, then `aitp_request_promotion`.
3. After each state change, re-check the execution brief.
4. Do not skip stages. Do not call tools for a later stage while blocked.

## Key constraints

- Only "pass" in L4 review allows promotion.
- L2 promotion requires human approval via popup gate.
- Respect `authority_warning` from query results.
- L5 (writing) is removed in v4.0. L2 is the endpoint.

## Flexible navigation

The protocol is NOT strictly linear. You can:

1. **Register sources at any stage**: `aitp_register_source` works during L1, L3, L4. No stage change needed.

2. **Retreat L3 → L1**: If analysis reveals insufficient sources or wrong framing, call `aitp_retreat_to_l1`. This preserves all L3 work but lets you re-read and re-frame.

3. **Switch L3 activity**: L3 allows any activity at any time. Use `aitp_switch_l3_activity` with any valid target (ideate, derive, trace-derivation, gap-audit, connect, integrate, distill).

4. **Return L4 → L3**: After submitting L4 review, call `aitp_return_to_l3_from_l4` to analyze results before promoting. Required by SPEC S3.

5. **Resume after compaction**: After context compaction, call `aitp_get_execution_brief` first to re-orient.

## Lane awareness

The lane (`formal_theory`, `toy_numeric`, `code_method`) affects how the agent frames work but does not change gate logic. Match the lane when filling artifacts.

## Skill activation per stage

| Stage | Posture/Activity | Skill file |
|-------|-----------------|------------|
| L0 | discover | `skill-discover.md` |
| L1 | read | `skill-read.md` |
| L1 | frame | `skill-frame.md` |
| L3 | ideate | `skill-l3-ideate.md` |
| L3 | plan | `skill-l3-plan.md` |
| L3 | analyze | `skill-l3-analyze.md` |
| L3 | gap-audit | `skill-l3-gap-audit.md` |
| L3 | integrate | `skill-l3-integrate.md` |
| L3 | distill | `skill-l3-distill.md` |
| L4 | verify | `skill-validate.md` |

## Domain skills

After loading the stage skill, check `brief.domain_prerequisites` — if it lists domain
skill files, load them. Domain skills encode domain-specific invariants, validation criteria,
and workflow lanes that the stage skill assumes are present.

## Intensity and interaction awareness

The execution brief returns `research_intensity` (quick/standard/full) and
`interaction_level` (collaborative/direct/silent). Respect these:
- Quick intensity means minimal L1, flexible L3, abbreviated L4.
- Silent interaction means suppress all AskUserQuestion except promotion rejection.
| L2 | promote | `skill-promote.md` |

## Conversation style

- Do not expose protocol jargon to the user.
- Report progress in plain language: "I've framed the question, now setting up the derivation."
- Ask one question at a time for clarification.
- If the user says `just go`, stop asking and continue execution.
