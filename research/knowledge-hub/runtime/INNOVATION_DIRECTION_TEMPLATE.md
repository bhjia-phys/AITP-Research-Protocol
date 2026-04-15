# Innovation Direction Template

Use this file at:

- `topics/<topic_slug>/runtime/innovation_direction.md`

This is the human steering companion to `control_note`.
Use it to keep novelty intent and branch decisions explicit across loop steps.

---

topic_slug: `<topic_slug>`
updated_by: `<human_or_operator>`
updated_at: `YYYY-MM-DDTHH:MM:SSZ`
run_id: `<optional_latest_run_id>`

## 1) Initial idea and novelty target

- Idea statement:
- Why this direction is potentially new:
- What would count as meaningful novelty:
- What would count as "not new enough":

## 2) Current evidence boundary

- Highest reliable layer currently reached: `L1 | L3 | L4 | L2`
- Strongest supporting evidence artifacts:
- Strongest contradictory evidence artifacts:
- Main unresolved gap:

## 3) Human steering decision (required)

- Decision: `continue | branch | redirect | stop`
- Why this decision was chosen:
- Resource/risk limit for next loop step:
- Deadline or stop condition:

## 4) Next bounded question for AI

- Next question:
- Required deliverables:
- Required checks:
- Forbidden proxies:

## 5) Promotion posture

- Promotion allowed this step: `yes | no`
- If yes, which candidate IDs are eligible:
- If no, what must be true first:

---

Quick rule:

- If this file changes scope, observables, deliverables, or acceptance tests,
  update the matching research-question or validation contract in the same step.

