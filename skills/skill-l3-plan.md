---
name: skill-l3-plan
description: L3 Planning subplane — design derivation route from idea.
trigger: l3_activity == "plan"
---

# L3 Planning

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question (clarification, scope, direction, missing info), you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

## Entry Profile Detection

Check the execution brief for `entry_profile`:
- **`explore_idea`** → Design derivation route from an idea
- **`learn_paper`** → Skip plan — go directly to trace-derivation (the paper's structure IS the plan)
- **`continue_work`** → Load existing plan, fill gaps
- **`l4_return`** → Re-plan based on L4 review feedback

## Pre-Derive Setup (MANDATORY for code_method lane)

If the topic lane is `code_method`, fill the `## Pre-Derive Setup` checklist before completion:
- [ ] Code builds without errors on target machine
- [ ] Pseudopotentials / basis sets verified
- [ ] DFT baseline passes sanity check (known system: Si PBE gap ~0.6 eV)
- [ ] Input file templates validated

If any setup item fails, switch to diagnose.

## Branch Points

Under `## Branch Points` in the artifact, define expected outcomes:
```markdown
### main → gap-audit (trigger: result within tolerance)
### anomaly → diagnose (trigger: deviation > threshold)
### dead_end → retreat_to_l1 (trigger: no progress after N attempts)
```
Execution brief will surface these when plan is ready.

---

You are in the planning subplane of L3 derivation.

## Collaborative Discussion (MANDATORY)

Before writing the plan, you MUST discuss the derivation strategy with the human.
Do NOT just write a plan and move on.

Use AskUserQuestion for EACH of these discussion rounds (minimum 2 rounds):

1. **Strategy proposal**: Present your proposed derivation route.
   Ask: "Here's my suggested approach: <route>. Does this match what you had in mind?
   Are there alternative methods worth considering?"
2. **Computation design** (for numeric lanes): Discuss what to compute and how.
   Ask: "For the numerical experiments: what system sizes, parameter ranges, and
   observables should we prioritize? What's the minimal computation that would
   give us a meaningful result?"
3. **Priority and phasing**: Discuss what to do first vs. what can wait.
   Ask: "Should we start with a quick proof-of-concept or go straight to the
   full computation? What results would change our approach?"
4. **Plan confirmation**: Before advancing, confirm the plan.
   Ask: "The plan is: <summary>. Ready to execute, or any adjustments?"

The human may add more discussion rounds at any time. Do NOT rush to fill the artifact.

## Escape Hatches

At ANY point during discussion, you may offer these back-paths via AskUserQuestion:

- **Back to ideation** (`aitp_switch_l3_activity(activity="ideate")`): if the plan
  reveals the idea itself needs rethinking
- **Retreat to L1** (`aitp_retreat_to_l1`): if sources or conventions are insufficient
- **Query L2** (`aitp_query_l2`): check if related derivations or results exist
- **Register new sources** (`aitp_register_source`): if the plan requires literature
  not yet in the knowledge base

## Active artifact

`L3/plan/active_plan.md`

## What to do

1. State the derivation plan.
2. Map the route from starting anchors to target claims.
3. List expected outcomes and milestones.
4. Do not start calculation or analysis yet.

## Pre-Execution Checks

Before advancing to derive, run these to validate the plan:

1. **Order-of-magnitude estimation**: does the target quantity even make sense?
   ```
   aitp_estimate_order(topics_root, topic_slug, quantity="<name>", expression="<LaTeX>")
   ```
   This catches dimensional errors and physically impossible values before
   you invest in a full derivation.

2. **Check available inference rules**: what proof techniques are available?
   ```
   aitp_list_inference_rules(topics_root)
   ```
   Returns all registered inference rules (substitution, integration by parts,
   residue theorem, Wick's theorem, etc.). Your derivation steps will be
   verified against these rules. If you need a rule that doesn't exist,
   plan to add it.

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

Advance to **derive** when `active_plan.md` has filled frontmatter fields
`plan_statement` and `derivation_route`, plus headings `## Plan Statement` and `## Derivation Route`.

## Allowed transitions

- Forward: `derive` — call `aitp_switch_l3_activity(activity="derive")` to advance.
- Backedges: `ideate`
