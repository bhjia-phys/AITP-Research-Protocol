---
name: skill-l3-diagnose
description: L3 Diagnosis — abductive hypothesis-test loop for numerical anomalies and unexpected results.
trigger: l3_activity == "diagnose"
---

# L3 Diagnosis

## MANDATORY: AskUserQuestion rule

When you need to ask the user ANY question, you MUST:
1. Call `ToolSearch(query="select:AskUserQuestion", max_results=1)` to load the tool.
2. Call `AskUserQuestion(questions=[{...}])` with your question and options.
NEVER type questions or options as plain text. ALWAYS use the popup tool.

---

Diagnose is a **sidecar activity** — enter from derive (or trace-derivation) when you
encounter an anomaly, form and test hypotheses, then return to derive with the resolved
understanding. It has no gate prerequisites.

Diagnosis is neither derivation (constructive) nor gap-audit (systematic checklist).
It is **abductive reasoning**: observe an anomaly, form candidate hypotheses,
design targeted tests, exclude wrong hypotheses, converge on a root cause.

## Common Preamble

### Before You Begin
1. Read the derivation artifact (`L3/derive/active_derivation.md`) — understand expected vs observed
2. Read the plan (`L3/plan/active_plan.md`) — check branch_points for anomaly triggers
3. Note specific numerical values: expected, observed, discrepancy magnitude

### Escape Hatches
- Return to derive (`aitp_switch_l3_activity(activity="derive")`): anomaly resolved
- Switch to gap-audit: if the anomaly reveals a structural issue
- Retreat to L1: if the anomaly suggests wrong conventions
- Retreat to L0: if the anomaly reveals need for new sources

### Active Artifact
`L3/diagnose/active_diagnosis.md`

---

## Diagnosis Workflow

### Step 1: Describe the Anomaly
Fill `## Anomaly Description`:
- What was expected and why (cite the source or derivation step)
- What was observed (exact numerical values)
- Discrepancy magnitude and direction

### Step 2: Build Hypothesis Stack
Fill `## Hypothesis Stack`. Each hypothesis:
```markdown
### Hypothesis N: <label>
- **Likely cause**: <what mechanism would produce this anomaly>
- **Prior probability**: high | medium | low
- **Test**: <what experiment/check would confirm or exclude this hypothesis>
- **Status**: pending | confirmed | excluded
- **Evidence**: <result of the test>
```
Minimum 2 hypotheses. Maximum typically 3-5.

### Step 3: Execute Tests
Record under `## Tests Executed`. Tests should be:
- **Minimal**: smallest computation that distinguishes hypotheses
- **Targeted**: designed to exclude one specific hypothesis
- **Recorded**: every test with parameters and output

### Step 4: Exclude and Converge
Update hypothesis status after each test. Goal: exclude all except one, or identify a new hypothesis.

### Step 5: Resolve
Record root cause under `## Resolution`. If no hypothesis survived, record under `## Unresolved` and escalate to gap-audit.

---

## Discussion Checkpoints
1. **Anomaly presentation**: "I observed <anomaly>. Expected <X> but got <Y>."
2. **Hypothesis review**: "My hypotheses are: <list>. Any I'm missing?"
3. **Test design**: "To distinguish H1 from H2, I'll run <test>."
4. **Root cause confirmation**: "The evidence points to <cause>. Do you agree?"

---

## Small vs. Large Diagnosis

**Stay in derive** if:
- The anomaly can be explored with one parameter change
- Root cause is likely simple setup error
- Investigation takes < 3 test runs

**Switch to diagnose** if:
- Multiple competing hypotheses need systematic exclusion
- Requires designing new test computations
- Root cause might be in the method itself
- You've tried 3 things in derive and none worked

## Exit Conditions
- At least one hypothesis marked `excluded` and one `confirmed`
- `## Resolution` filled with root cause and fix
- OR `## Unresolved` filled with escalation path

## Allowed Transitions
- Forward: derive (resolved), gap-audit (structural issue), retreat_to_l1
- Backedges: derive (back with fix applied)
