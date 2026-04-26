---
name: using-aitp
description: HIGHEST PRIORITY — Use for ANY theoretical-physics research, topic continuation, idea steering, paper learning, derivation work, validation planning, or study of physical systems. This skill MUST be loaded BEFORE brainstorming, exploration, or any other skill. Enter AITP before any substantial response.
---

# Using AITP (v2)

## CRITICAL: Tool-first rules

You MUST follow these rules in this exact order. Violating ANY of them is a protocol error:

1. **NEVER browse files with Grep/Glob/Read to "check what exists"**. Use `mcp__aitp__aitp_get_execution_brief` or `mcp__aitp__aitp_get_status` instead.
2. **NEVER manually read or edit files under the AITP topics directory.** Always use `mcp__aitp__*` tools.
3. **NEVER type out questions as plain text.** Use `AskUserQuestion` tool for ALL questions to the user.
4. **NEVER guess the topics_root path.** It is always: `{{TOPICS_ROOT}}`

## Environment

- AITP v2 runs as an MCP server. All tools are prefixed `mcp__aitp__aitp_*`.
- Topics root: `{{TOPICS_ROOT}}`
- Protocol manual: `{{REPO_ROOT}}/brain/PROTOCOL.md`

## Override rule

This skill takes precedence over brainstorming, exploration, and all other process skills when the request involves physics research. Do NOT load brainstorming first. Load this skill, enter AITP, and let the AITP protocol handle ideation internally.

## When to use

- The user asks to study or continue a physics topic.
- The user says `继续这个 topic`, `current topic`, `this topic`, or equivalent.
- The user asks to change direction, refine scope, set validation, or update steering.
- The user asks to learn papers, evaluate an idea, recover a derivation, plan formalization, or build a bounded research loop.

## Hard gate

- If there is even a small chance the request is real theoretical-physics research rather than plain coding, enter AITP first.
- Do not start with free-form browsing, synthesis, or editing when the task belongs inside AITP.
- Treat natural-language steering as state, not chat decoration.

## Entry procedure (follow exactly)

When this skill activates, do these steps IN ORDER:

### Step 1: Find matching topic
```
Call: mcp__aitp__aitp_list_topics(topics_root="{{TOPICS_ROOT}}")
```
- Read the returned list. Match the user's request to the best topic by title/question/slug.
- If a matching topic is found → go to Step 3
- If no match → go to Step 2

### Step 2: Bootstrap new topic
```
Call: mcp__aitp__aitp_bootstrap_topic(
    topics_root="{{TOPICS_ROOT}}",
    topic_slug=<slug>,
    title=<title>,
    question=<question>,
    lane=<lane>
)
```

### Step 3: Get execution brief
```
Call: mcp__aitp__aitp_get_execution_brief(topics_root="{{TOPICS_ROOT}}", topic_slug=<slug>)
```
Read the brief. It tells you exactly what to do next.

### Step 4: Ask clarification (if needed)
**BEFORE asking ANY question to the user, you MUST load the AskUserQuestion tool first:**
```
Call: ToolSearch(query="select:AskUserQuestion", max_results=1)
```
Then use it for ALL questions. NEVER type options as plain text.
```
Call: AskUserQuestion(questions=[{
    "question": "<your question>",
    "header": "<short label>",
    "options": [
        {"label": "<option1>", "description": "<what it means>"},
        {"label": "<option2>", "description": "<what it means>"},
    ],
    "multiSelect": false,
}])
```

### Step 5: Follow the brief
The brief tells you the current stage and what to do. Follow it.

## Protocol stages (quick reference)

0. **L0 (discover)**: Find, evaluate, and register sources before deep reading begins
1. **L1 (read → frame)**: Register sources, fill reading notes, frame research question
2. **L3 (flexible workspace)**: Switch between ideate, derive, trace-derivation, gap-audit, connect, integrate, distill — no forced sequence
3. **L4 (validate)**: Submit adversarial review with counterargument; non-pass returns to L3
4. **Promote**: Request promotion → human gate → promote to global L2
5. **L2 is the endpoint** — L5 (writing) removed in v4.0

## Conversation style rules

- Do not expose protocol jargon to the user.
- Ask in plain language, as if you are a research collaborator.
- Use `AskUserQuestion` for ALL clarification questions — never just type options as plain text.
- Ask one question at a time by default.
- If the user says `you decide`, `just go`, `直接做`, stop clarifying and continue.

## Clarification sub-protocol

1. Tighten the research question before substantive execution.
2. Ask at most 3 clarification rounds, with 1-3 questions per round.
3. Prefer questions that remove the biggest ambiguity first: scope, assumptions, target claims.
4. If the human says `just go`, proceed and mark missing fields as deferred.

## Skill activation

After getting the execution brief, load the matching skill:
- L0 discover → `skill-discover.md`
- L1 read → `skill-read.md`
- L1 frame → `skill-frame.md`
- L3 workspace → `skill-l3-ideate.md` through `skill-l3-distill.md`
- L4 verify → `skill-validate.md`
- Promote → `skill-promote.md`

## Domain skills

Check `brief.domain_prerequisites` — if it lists domain skill files (e.g. `skill-librpa`),
load them after the stage skill. Domain skills encode domain-specific invariants, validation
criteria, and workflow lanes that the stage skill assumes are present.

## Red flags (STOP if you catch yourself doing these)

- "I can just answer this research question directly."
- "This topic change is small enough to skip routing."
- "I will read files first and decide later whether AITP applies."
- "Let me search the codebase to see what already exists."

If one of these is true, stop and enter AITP first.
