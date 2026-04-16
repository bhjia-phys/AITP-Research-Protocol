# L3-L4 Iteration Journal Design

## Goal

Add a Markdown-first run journal for real research loops where one `L3` run can
iterate multiple times through:

- `L3` planning,
- `L4` execution and review,
- `L3` synthesis and staging decision.

The design should improve human auditability without replacing the existing
execution, review, and staging artifacts.

## Problem

The current runtime already has durable pieces of the loop:

- `next_actions.md` / `next_actions.contract.json`
- `execution_task.json` / `execution_task.md`
- `validation_review_bundle.active.json` / `.md`
- `returned_execution_result.json`
- staging entries and manifests

But those pieces are still distributed across several surfaces.

That is acceptable for machines, but it is weak for human review when:

- `L3` revises the plan after one failed or partial `L4` pass,
- the same run needs multiple benchmark or derivation iterations,
- the operator wants one continuous audit trail before approving staging,
  promotion, or later `L5` writing.

## Core design choice

Adopt one `run = one complete research round` model.

Inside that run, allow multiple `iteration-*` children.

Use:

- one run-level Markdown journal as the primary human review surface,
- one per-iteration folder for detailed records,
- thin JSON companions only for machine-stable state and replay pointers.

This keeps:

- the human story continuous,
- per-iteration detail isolated,
- machine automation stable,
- existing runtime artifacts unchanged as source-of-truth execution surfaces.

## File layout

Recommended layout:

```text
topics/<topic_slug>/L3/runs/<run_id>/
  next_actions.md
  next_actions.contract.json
  candidate_ledger.jsonl
  iteration_journal.md
  iteration_journal.json
  iterations/
    iteration-001/
      plan.md
      plan.contract.json
      l4_return.md
      l4_return.json
      l3_synthesis.md
      l3_synthesis.json
```

Run-level role:

- `iteration_journal.md`
  - human-facing review index for the whole run
- `iteration_journal.json`
  - thin machine companion with current iteration pointer and stable refs

Iteration-level roles:

- `plan.md`
  - the detailed L3 plan for this round
- `plan.contract.json`
  - thin machine contract for the plan
- `l4_return.md`
  - the human-readable summary of what L4 returned
- `l4_return.json`
  - thin machine record of the returned result and linked artifacts
- `l3_synthesis.md`
  - L3's interpretation, next step, and staging judgment
- `l3_synthesis.json`
  - thin machine record of that synthesis decision

## Markdown versus JSON boundary

### Markdown owns

- the detailed plan
- server / runtime / script / parameter notes
- derivation and benchmark intent
- human-readable result interpretation
- why the run should continue, stop, or stage

### JSON owns

- ids
- status fields
- stable artifact paths
- replay inputs
- staging decisions that automation must read deterministically

### Explicit rule

Do not write the same long narrative twice.

If the narrative matters to a human reviewer, it belongs in Markdown.

If a field must remain stable under automation, it belongs in a thin JSON
companion.

## State model

One run may progress through these run-level states:

- `planning`
- `iterating`
- `awaiting_human_review`
- `staged`
- `completed`
- `abandoned`

Each iteration may progress through:

- `planned`
- `dispatched`
- `returned`
- `synthesized`
- `staged`
- `superseded`

The run journal should always expose:

- current iteration id
- latest iteration status
- latest staging decision
- latest recommended next step
- links to the primary execution and review artifacts

## Existing artifact compatibility

This design does not replace:

- `next_actions.contract.json`
- `runtime/execution_task.json`
- `runtime/validation_review_bundle.active.json`
- `L4/runs/<run_id>/returned_execution_result.json`
- canonical staging entries

Instead:

- `plan.contract.json` may help generate or validate `execution_task.json`
- `l4_return.*` should point at the existing `L4` result artifacts
- `l3_synthesis.*` should decide whether a staging write is honest
- the run journal should index those surfaces for review

## Staging rule

`L3` synthesis, not raw `L4` execution output, should decide whether a result is
ready for provisional staging.

The minimum honest chain is:

1. `L3 plan`
2. `L4 execution and review`
3. `L3 synthesis`
4. optional staging write

This keeps staging aligned with reusable research judgment rather than treating
every raw returned result as already reusable.

## Out of scope

This design does not attempt to:

- replace the existing closed-loop execution protocol
- redesign canonical `L2` storage
- make all adapters render native popup UIs
- move all legacy compatibility paths in one step

## Recommended implementation order

1. freeze principle and contract text
2. add failing tests for journal layout and thin-contract rules
3. add run/iteration path helpers plus Markdown renderers
4. materialize journal updates alongside execution-task and return ingestion
5. surface the journal through status/runtime bundle/replay
6. wire staging decisions from `l3_synthesis`

## One-line memory

One run may contain many `L3 -> L4 -> L3` iterations; Markdown owns the human
review journal, while JSON remains the thin machine companion.
