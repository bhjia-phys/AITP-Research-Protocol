# Agent Model

## What the protocol is to an agent

For an AI agent, the AITP protocol is an external operating contract.

It does not try to control the hidden internal chain of thought of an external
model. Instead, it constrains what the agent is allowed to count as valid work.

## The control stack

AITP should be understood as a stack:

1. **Charter**
   - the highest-level research principles
2. **Protocol objects**
   - contracts, schemas, and decision artifacts
3. **Runtime**
   - state materialization and audits
4. **Adapter**
   - agent-specific integration layer
5. **Agent**
   - OpenClaw, Codex, Claude Code, OpenCode, or another executor

## What the adapter does

An adapter should:

- enter through the AITP runtime surface;
- load the current topic protocol bundle;
- call tools or handlers only through explicit interfaces;
- refresh conformance at exit.

An adapter should not:

- invent its own research route,
- upgrade a claim silently,
- replace missing protocol artifacts with hidden heuristics.

## Why this does not require huge prompts

AITP should not be loaded as one giant prompt.

The correct pattern is:

- load the short charter,
- load the topic-local runtime bundle,
- load only the sub-contracts needed for the current step.

This keeps the context bounded and moves state into files rather than chat
history.

## Conformance versus correctness

If an agent follows AITP, that means:

- the work is inspectable,
- the state is resumable,
- the artifacts exist,
- later agents can continue from disk.

It does not mean the science is already correct.
