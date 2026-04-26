---
name: skill-l3-ideate
description: L3 Ideation subplane — generate and record research ideas.
trigger: l3_activity == "ideation"
---

# L3 Ideation

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the ideation subplane of L3 derivation.

## Pattern B Tool: scientific-brainstorming (INVOKE BEFORE DISCUSSION)

Before starting discussion round 1, invoke `scientific-brainstorming` skill
to structure the idea exploration workflow. This provides a systematic
brainstorming methodology (context understanding → divergent exploration →
convergent refinement → action planning) that makes ideation more rigorous.

## Collaborative Discussion (MANDATORY)

Before filling the artifact, you MUST discuss with the human. Do NOT just write an idea
and move on. The goal is to explore the idea space together like physicists brainstorming.

Use AskUserQuestion for EACH of these discussion rounds (minimum 2 rounds):

1. **Initial exploration**: Present what you understand about the research question.
   Ask the human: "Based on the sources and L1 framing, what directions interest you most?
   Are there specific quantities, regimes, or phenomena you want to investigate?"
2. **Idea refinement**: After the human's initial input, propose 2-3 concrete idea candidates.
   Ask: "Which of these directions is most promising? Or should we combine/refine them?"
3. **Risk assessment**: Once an idea is selected, discuss potential pitfalls.
   Ask: "What could go wrong with this approach? Are there known contradictions or
   degenerate limits we should watch for?"
4. **Scope agreement**: Before advancing, confirm the agreed idea and scope.
   Ask: "To confirm: we're pursuing <idea>, with scope <scope>. Ready to plan?"

The human may add more discussion rounds at any time. Do NOT rush to fill the artifact.

## Escape Hatches

At ANY point during discussion, you may offer these back-paths via AskUserQuestion:

- **Retreat to L1** (`aitp_retreat_to_l1`): if sources are insufficient, framing is wrong,
  or assumptions need revision
- **Query L2** (`aitp_query_l2`): check if related results already exist in the
  global knowledge base — don't reinvent the wheel
- **Register new sources** (`aitp_register_source`): if the discussion reveals missing
  literature, add sources before continuing

These are not just for this subplane — they are available throughout ALL L3 subplanes.

## Active artifact

`L3/ideate/active_idea.md`

## What to do

1. Record the central idea statement.
2. Explain why this idea is worth pursuing (motivation).
3. Note prior work and risks.
4. Do not start planning or analysis yet.

## Exit condition

Advance to **planning** when `active_idea.md` has filled frontmatter fields
`idea_statement` and `motivation`, plus headings `## Idea Statement` and `## Motivation`.

## Allowed transitions

- Forward: `planning`
- Backedges: none (this is the entry subplane)
