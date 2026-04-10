# AITP Workflow Shell And Protocol Kernel

## Decision

AITP should borrow workflow shells from systems like Superpowers, GSD,
Compound, and OpenSpec, but it should not abandon its protocol kernel.

Short form:

- borrow the shell
- preserve the kernel

This is not a claim about Python as a language.
It is a claim about which responsibilities may live in prompts, skills, hooks,
or lightweight workflow files, and which responsibilities still need durable,
testable implementation and artifacts.

## Why This Decision Exists

External workflow systems teach the right lessons about:

- natural-language-first entry
- progressive disclosure
- explicit plans, milestones, and review loops
- inspectable CLI surfaces
- reusable execution patterns

AITP should learn from those systems.
But AITP is not only a workflow wrapper.
It is also a research protocol that must keep:

- `L0 -> L1 -> L3 -> L4 -> L2` semantics
- topic state durable across sessions
- evidence separate from interpretation
- validation and promotion gates explicit
- multi-topic control inspectable
- derived views distinct from source-of-truth artifacts

If those duties move entirely into prompts or informal workflow convention, the
system becomes easier to demo but less reliable to continue, audit, or trust.

## What AITP Should Borrow From Workflow Systems

AITP should borrow these outer-shell patterns aggressively:

- a small number of clear public entrypoints
- CLI-first inspectability behind natural-language-first UX
- skills, commands, hooks, and plugin bootstraps for platform integration
- spec, plan, milestone, and backlog artifacts for repo development
- progressive disclosure so ordinary users do not need protocol jargon first
- reusable route capsules after real work has matured

This is the right layer to feel like Superpowers, GSD, Compound, or OpenSpec.

## What AITP Must Keep As Protocol Kernel

AITP should keep these responsibilities in durable code plus durable artifacts:

- topic lifecycle and topic state transitions
- runtime materialization and synchronization
- `L0-L4` contract generation and update
- validation, conformance, and promotion gates
- active-topic registry and current-topic compatibility projection
- evidence-bearing writeback and backend bridge rules
- schema-backed machine-readable state surfaces
- regression tests for protocol compatibility

These are not product polish details.
They are the minimum machinery that prevents AITP from collapsing into
free-form chat memory.

## Practical Boundary

Use workflow-shell mechanisms when the job is:

- routing the user into the right workflow
- exposing commands or skills
- organizing repo implementation work
- documenting progress and decisions
- adapting AITP to Codex, OpenCode, Claude Code, or OpenClaw

Use protocol-kernel implementation when the job is:

- deciding or persisting topic state
- materializing runtime truth
- expressing trust boundaries
- validating or rejecting claims
- promoting material toward `L2`
- recovering a topic safely after context loss

## Language And Implementation Rule

Python is currently the implementation language for most of the kernel, but
that is an implementation choice, not the principle itself.

The principle is:

- no language gets to quietly redefine the protocol
- no prompt system gets to replace durable state where durable state is needed
- no workflow shell gets to pretend that inspectable research state is optional

If some kernel responsibilities later move out of Python, that is acceptable
only if the replacement preserves the same durability, inspectability, and
testability.

## Three-Layer Target Shape

The intended architecture is:

1. Workflow shell
   - skills
   - hooks
   - plugins
   - slash commands
   - natural-language routing

2. Explicit control plane
   - CLI commands
   - phase/plan docs
   - runtime dashboards
   - status and migration surfaces

3. Protocol kernel
   - artifact materialization
   - state machines
   - validation logic
   - schema contracts
   - audited writeback

The shell may become lighter and friendlier over time.
The control plane may become clearer and smaller.
The kernel must remain strict enough that scientific state does not drift.

## Review Test

When evaluating a simplification, ask:

1. Does this remove user-facing friction only, or does it also remove protocol guarantees?
2. If the conversation resets tomorrow, can the next agent recover the same state from disk?
3. If a topic is challenged later, is there still a durable artifact trail?
4. If this code disappeared and only prompts remained, would trust boundaries become ambiguous?

If the answer to the last two questions is yes, the change went too far toward
workflow shell and cut into protocol kernel.

## Current Consequence For AITP

This means:

- AITP should keep converging toward Superpowers-style outer UX.
- AITP should keep using GSD-style explicit planning for repo work.
- AITP should keep compacting redundant runtime surfaces.
- AITP should not reduce topic state, validation state, or promotion state to
  prompt-only behavior.
- AITP should simplify its implementation without turning protocol semantics
  into optional convention.

That is the intended balance.
