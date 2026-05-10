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
5. **ALWAYS load domain skills when listed.** Check `brief.domain_prerequisites` after getting the execution brief. If it lists domain skill files (e.g. `skill-librpa`), load them BEFORE the stage skill. Domain skills contain hard invariants that will produce physically wrong results if ignored.

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

### Step 3.5: Multi-idea selection (if applicable)
If the session-start context mentions "Multi-Idea Topic", the topic has multiple registered ideas. You MUST ask the user to select which idea to pursue BEFORE doing anything else:

```
Call: AskUserQuestion(questions=[{
    "question": "This topic has multiple ideas. Which one should I work on?",
    "header": "Select Idea",
    "options": [
        {"label": "<idea1-id> (active)", "description": "<statement>"},
        {"label": "<idea2-id> (parked)", "description": "<statement>"},
    ],
    "multiSelect": false,
}])
```

After the user selects:
- If a parked idea is selected, update `L3/ideate/idea_registry.md` frontmatter: change `active_idea` to the selected ID, swap statuses
- Copy the selected idea's content to `active_idea.md`
- Read `MEMORY.md` for cross-idea context

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

## Research Notebook

The research notebook (`flow_notebook.tex` at the topic root) is generated by AI agents
that read structured L0-L4 artifacts and write LaTeX directly using the JHEP+AITP template.
See `skill-notebook-generate.md` for the full parallel-agent workflow.

**When to regenerate:**
- After `aitp_submit_candidate` (major L3 milestone)
- After L4 review completion
- When the user asks "生成notebook" or "compile notebook"

## Domain skills

Check `brief.domain_prerequisites` — if it lists domain skill files (e.g. `skill-librpa`),
load them after the stage skill. Domain skills encode domain-specific invariants, validation
criteria, and workflow lanes that the stage skill assumes are present.

## Red Flags

These thoughts mean STOP — you are rationalizing. Each entry comes from a real protocol violation
observed in live research sessions:

| Thought | Reality |
|---------|---------|
| "I can SSH/read the files to check what's there" | NEVER browse AITP topic files with Grep/Glob/Read/Bash. Use `mcp__aitp__aitp_get_execution_brief`. Code sources must be registered via `aitp_register_source` before deep reading. |
| "Let me check the server code first, then register" | Register sources FIRST. Then explore. Reverse order = lost traceability and unregistered knowledge. |
| "The derivation is obvious from the code, I'll just write it" | Record each step via `aitp_create_derivation_step` with `source_ref` to file:line. "Obvious" derivations are where unstated assumptions hide. |
| "Domain skill is optional background reading" | Domain constraints from `brief.domain_prerequisites` are mandatory. Load domain skills BEFORE the stage skill. |
| "The gate just checks headings exist, empty content passes" | Gates check heading presence AND content completeness. Fill all required sections with substantive content. |
| "I can write the artifact directly with Write tool" | Use AITP MCP tools to write artifacts. They ensure state consistency. |
| "The notebook was auto-generated, no need to check it" | After `aitp_submit_candidate`, regenerate the notebook using `skill-notebook-generate.md` — AI agents read the updated artifacts and write LaTeX sections. Review each section for physics accuracy and readability. |
| "Discussion rounds are just protocol overhead" | Each round must eliminate ONE specific uncertainty. Ask one question per round. If the user says "直接做", proceed — but record what was deferred. |
| "This is just a simple code/config check" | Code reading for AITP topics IS research. Follow the pipeline — register sources, trace functions, record derivation steps. |
| "I already understand the physics, let me skip to implementation" | Understanding ≠ recording. Recorded claims persist across sessions and feed L2 knowledge. Unrecorded understanding is lost when context compacts. |
| "SymPy verification failed — that's fine for code_method" | code_method uses source anchoring (file:line references), not SymPy. The verification path differs by lane. Use lane-appropriate verification. |
| "I can just answer this research question directly" | Direct answers bypass source registration, derivation recording, and L2 accumulation. Enter AITP first. |
| "I will read files first and decide later whether AITP applies" | Skill check comes BEFORE file exploration. AITP tells you HOW to explore. |
| "MCP is down, I'll just work directly and record later" | Use `aitp_event.py` to record events OFFLINE. Test submissions, failures, and results must be logged as they happen, not retroactively. `python3 hooks/aitp_event.py <topics_root> <slug> <event_type> <desc>` |
| "I'll record the test results after the job finishes" | Record job SUBMISSION now. Record FAILURE when it fails. Don't batch — each event is a data point. The harness can't track what it doesn't know about. |

## Offline Recording (When MCP Is Unavailable)

When the AITP MCP server is disconnected, use `hooks/aitp_event.py` to record events
directly to the topic's `runtime/log.md`. No MCP dependency needed.

```
python3 D:/BaiduSyncdisk/repos/AITP-Research-Protocol/hooks/aitp_event.py \
  D:/BaiduSyncdisk/Theoretical-Physics/research/aitp-topics \
  qsgw-headwing-update-librpa \
  L4_test_submit \
  "Job 1732319: full pipeline, 8 procs, 120GB"
```

Event types for HPC work: `L4_test_submit`, `L4_test_fail`, `L4_test_complete`,
`L4_test_ooms`, `L4_test_fpe`, `L4_numerical_result`.

If you catch yourself thinking any of these, you are rationalizing. Stop. Return to the protocol.
