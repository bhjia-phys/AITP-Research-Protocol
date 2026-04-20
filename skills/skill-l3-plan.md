---
name: skill-l3-plan
description: L3 Planning subplane — design derivation route from idea.
trigger: l3_subplane == "planning"
---

# L3 Planning

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

You are in the planning subplane of L3 derivation.

## Active artifact

`L3/planning/active_plan.md`

## What to do

1. State the derivation plan.
2. Map the route from starting anchors to target claims.
3. List expected outcomes and milestones.
4. Do not start calculation or analysis yet.

## Computational Environment (MANDATORY for toy_numeric and code_method lanes)

If the topic lane is `toy_numeric` or `code_method`, or if the plan includes ANY
numerical computation, you MUST include an **Execution Environment** section in
the plan with the following details:

1. **Target machine** — Which server/workstation will run the computation?
   Use AskUserQuestion to confirm with the human if not specified in topic MEMORY.md.
2. **Software stack** — Required packages, versions, and any special setup.
3. **Data paths** — Where inputs live and where outputs go on the target machine.
4. **Estimated resources** — Rough estimate of CPU/GPU time, memory, disk space.

Example:
```markdown
## Execution Environment
- Machine: Fisher (ssh Fisherd-Server100.96.1.64)
- Python: 3.13.5, numpy 2.4.3, scipy 1.17.1
- Data: /home/user/aitp/<topic_slug>/data/
- Estimate: L=10000, 500 trajectories, ~30 min wall time
```

If the human has not specified the target machine, you MUST ask before proceeding.

## Exit condition

Advance to **analysis** when `active_plan.md` has filled frontmatter fields
`plan_statement` and `derivation_route`, plus headings `## Plan Statement` and `## Derivation Route`.

## Allowed transitions

- Forward: `analysis`
- Backedges: `ideation`
