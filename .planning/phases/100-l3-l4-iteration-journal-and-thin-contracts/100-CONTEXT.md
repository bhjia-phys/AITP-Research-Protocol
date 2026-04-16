# Phase 100 Context: L3-L4 Iteration Journal And Thin Contracts

## Why this phase exists

The runtime already has durable `L3`, `L4`, and staging artifacts, but they are
still spread across multiple surfaces:

- `next_actions.*`
- `execution_task.*`
- `validation_review_bundle.active.*`
- `returned_execution_result.json`
- staging entries

That is workable for machines, but weak for human review when one run needs
multiple `L3 -> L4 -> L3` iterations before a staging or promotion decision.

## Goal

Add one Markdown-first run journal plus per-iteration subfolders so a human can
inspect:

1. the detailed `L3` plan,
2. the returned `L4` result,
3. the `L3` synthesis and staging decision,
4. the continuity across multiple iterations in one run.

## Scope

In scope:

- run-level iteration journal surfaces
- per-iteration `plan`, `l4_return`, and `l3_synthesis` surfaces
- thin JSON companion rules
- compatibility with existing `execution_task`, review bundle, returned result,
  and staging artifacts

Out of scope:

- redesigning the whole closed-loop execution engine
- replacing existing execution or validation artifacts
- canonical `L2` redesign
- full adapter UI parity

## Key design decisions already agreed

- one `run` may contain multiple `L3 -> L4 -> L3` iterations
- `iteration_journal.md` is the primary human review surface
- each iteration gets its own folder
- Markdown carries the human narrative
- JSON stays thin and machine-facing

## Principle files to keep aligned

- `docs/design-principles.md`
- `docs/HUMAN_IDEA_AI_EXECUTION_STEERING_PROTOCOL_VNEXT.md`
- `research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md`
- `research/knowledge-hub/runtime/DECLARATIVE_RUNTIME_CONTRACTS.md`

## Spec

- `docs/superpowers/specs/2026-04-16-l3-l4-iteration-journal-design.md`
