# Clarification Protocol

This file defines the public AITP contract for multi-round clarification when a
user starts from a vague or underspecified idea.

Clarification is an agent interaction rule.
It is not a background process controller and it does not authorize an internal
event loop.

## 1. Purpose

When a user provides a vague idea, AITP should not immediately start execution.

The correct first move is to tighten the active research-question contract until
the topic is scoped enough to support bounded work.

## 2. Clarification rounds

Clarification uses at most 3 rounds.

Each round should:

1. identify the most important missing fields in the research-question contract
2. generate 1-3 clarification questions as non-blocking decision points with
   `phase: clarification`
3. wait for human response, explicit skip, or equivalent natural-language
   steering
4. fill in the contract and re-check the remaining critical fields

If the contract becomes execution-ready before round 3, the loop should stop
early.

## 3. Critical fields

The following fields must be filled before normal execution unless explicitly
deferred:

- `scope`
- `assumptions`
- `target_claims`

These are the minimum fields that define what the topic is trying to do and
what it is not yet allowed to assume implicitly.

## 4. Non-critical fields

The following fields may be refined later:

- `deliverables`
- `acceptance_tests`
- `observables`

These may evolve during `L3` or `L4` as the validation surface becomes more
specific.

## 5. Escape hatch

If the human says "just go", "skip clarification", or an equivalent explicit
instruction, AITP may proceed with the current contract.

When that happens, any still-missing critical fields should be marked:

- `clarification_deferred: true`

The deferred status should remain visible rather than being silently treated as
resolved.

## 6. Integration

Clarification decision points should use:

- `phase: clarification`
- `trigger_rule: direction_ambiguity`

They should be non-blocking by default so the operator may ignore them and let
the bounded loop continue after timeout or explicit skip.

The practical rule for agent behavior is:

- do not begin full `L0-L4` routing until clarification is complete or
  explicitly skipped
- if clarification is skipped, proceed honestly with deferred fields marked in
  the research-question contract
