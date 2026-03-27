# Decision Trace Protocol

This file defines the public AITP contract for recording why a non-trivial
decision was made.

The aim is not only to preserve the outcome.
The aim is to preserve the reasoning shape that led to the outcome so later
humans and agents can ask what happened and why.

## 1. Purpose

AITP already records many artifacts that say what exists.
That is not enough for post-hoc understanding.

This protocol captures:

- what was decided,
- which options were considered,
- why one route won,
- what inputs fed the choice,
- what outputs were produced,
- and under what conditions the choice should be revisited.

This protocol uses `decision-trace.schema.json`.

## 2. Core object

A `decision_trace` is a structured record with:

- a durable id,
- a topic slug,
- a timestamp,
- a one-line decision summary,
- the chosen route,
- the rationale,
- the input refs,
- optional output refs,
- optional options considered,
- optional counterfactual or revisit conditions,
- and optional links to related traces.

The canonical storage surface is:

- `runtime/topics/<topic_slug>/decision_traces/<trace_file>.json`

## 3. Lifecycle

AITP should create a decision trace after every non-trivial decision, including:

- every `decision_point` resolution
- every routing decision such as sending material to `L3` instead of `L1`
- every method selection such as choosing ED over DMRG
- every gap recovery decision such as preferring `L0` follow-up over deferral
- every promotion or reject decision, even when it did not come from a
  `decision_point`

Minimal compliance is not zero traces.
A conformant session should emit at least one `decision_trace` per
`L3 -> L4` submission and per `L4 -> L2` attempt.

## 4. Causal chain

Each trace should expose a small causal chain through:

- `input_refs`
  - the artifacts that fed into the decision
- `output_refs`
  - the artifacts produced by the decision
- `related_traces`
  - other decisions that influenced or were influenced by this one

Within a topic, these links should form a directed acyclic graph of decision
history rather than an isolated collection of one-line reasons.

## 5. Query interface contract

A conformant AITP runtime should support natural-language questions against
decision traces.

The protocol-level expectation is:

- query resolution should use `rationale` and `would_change_if` as primary
  evidence
- query resolution may use `context` and `options_considered` as supporting
  evidence

The existence of a query interface is part of the protocol contract.
The exact concrete interface may vary:

- CLI
- MCP
- web UI
- or later notebook tooling

This document does not require semantic search.
Simple keyword-based retrieval is an acceptable first implementation.

## 6. Forbidden shortcuts

Do not treat a generic summary paragraph as a decision trace.

Do not emit a decision trace that says only:

- "this seemed best"
- "the model chose this route"
- or another explanation that cannot be tied back to inputs and outputs

If no real rationale is available, the correct trace is an honest limitation
statement, not invented causal prose.

## 7. Integration

This protocol complements existing AITP surfaces rather than replacing them.

- `promotion-or-reject`
  - still records the promotion outcome
  - `decision_trace` adds the causal context
- `GAP_RECOVERY_PROTOCOL`
  - still governs the gap route
  - `decision_trace` records why one route was chosen
- `session_chronicle`
  - should cite the relevant `decision_trace` ids in its narrative summary

## 8. Charter alignment

AITP is supposed to remain inspectable across sessions rather than improvising
per chat.

Decision traces operationalize that by making the causal logic durable instead
of leaving it in short-lived agent memory.
