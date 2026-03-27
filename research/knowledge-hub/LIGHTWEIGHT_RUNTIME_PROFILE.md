# Lightweight Runtime Profile

This file defines a minimal AITP conformance profile for lightweight usage.

The goal is to lower adoption friction without abandoning the core safety
properties that make AITP more than an ad hoc chat workflow.

## 1. Purpose

Some sessions need a smaller runtime surface than the strict 14+ artifact
profile in `AGENT_CONFORMANCE_PROTOCOL.md`.

This profile defines the minimum viable runtime shell that still preserves:

- durable topic identity
- a human-visible operator state
- a scoped research question
- and a durable human steering surface

## 2. Minimum required artifacts

The lightweight profile requires exactly 4 artifacts:

- `runtime/topics/<topic_slug>/topic_state.json`
  - what topic is active, what phase it is in, and which layer is current
- `runtime/topics/<topic_slug>/operator_console.md`
  - human-visible state surface including pending decision points
- `runtime/topics/<topic_slug>/research_question.contract.json`
  - the scoped research-question contract
- `runtime/topics/<topic_slug>/control_note.md`
  - the durable human steering surface

If any of these are missing, the topic is not lightweight-conformant.

## 3. Optional but recommended artifacts

The full runtime may additionally expose:

- `interaction_state.json`
- `conformance_state.json`
- `conformance_report.md`
- `agent_brief.md`
- `action_queue.jsonl`
- `resume.md`
- `runtime_protocol.generated.md`
- `session_start.generated.md`
- `innovation_direction.md`
- `next_action_decision.md`

These remain recommended because they improve resumability and audit strength.

## 4. Conformance levels

The public interpretation should stay:

- `Lightweight`
  - 4 required artifacts
  - AITP may run, but the audit should note lightweight mode
- `Standard`
  - 10 or more runtime artifacts
  - full normal conformance for everyday use
- `Strict`
  - all 14 or more artifacts required by `AGENT_CONFORMANCE_PROTOCOL.md`
  - full conformance plus entry and exit gate checks

## 5. Transition path

A lightweight session may upgrade itself to `Standard` or `Strict` by running:

```bash
aitp audit --phase entry
```

The runtime may scaffold missing artifacts during that upgrade path.

## 6. Integration with agent conformance

`AGENT_CONFORMANCE_PROTOCOL.md` defines the strongest full runtime contract.

This document defines a narrower subset for lightweight usage.

Both profiles may coexist:

- the runtime or operator may choose which level to enforce
- audit output should say which level was actually satisfied
- lightweight mode should never be mislabeled as strict mode
