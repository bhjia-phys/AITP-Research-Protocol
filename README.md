# AITP Research Charter and Protocol

> A protocol-first public repository for building an AI Theoretical Physicist as a disciplined research participant rather than a free-form chat agent.

## What this repository is

AITP stands for **AI Theoretical Physicist**.

This repository is not the claim that AI already is a serious autonomous
theoretical physicist. It is the public home for the **research charter** and
the **executable protocol surface** that an AI system should follow if it wants
to count as working inside AITP.

The core idea is simple:

- the charter defines what serious theoretical-physics research participation
  should respect;
- the protocol defines what artifacts, gates, and decisions must exist on disk;
- the runtime only materializes state, runs audits, and executes explicit tools;
- agents such as OpenClaw, Codex, Claude Code, and OpenCode act as adapters or
  executors, not as the source of truth.

## Why charter and protocol

Large models can produce fluent research language. That is not enough.

AITP is built to preserve the things that matter for real research:

- evidence before speculation;
- durable artifacts instead of chat residue;
- explicit uncertainty instead of false confidence;
- reusable knowledge instead of one-off output;
- visible validation and rejection paths;
- human-readable state that later agents and humans can audit.

This repository therefore treats the **charter** as the upper constraint and the
**protocol** as the executable contract.

## Core model

AITP currently works through an L0-L4 research structure:

- `L0`: source substrate
- `L1`: intake and provisional understanding
- `L2`: canonical reusable knowledge and active memory
- `L3`: exploratory research and candidate formation
- `L4`: validation and adjudication

The default non-trivial route remains:

`L0 -> L1 -> L3 -> L4 -> L2`

What matters is not only the layer map, but the rule that an agent may not
silently decide its own research workflow. It must follow durable contracts.

## What lives in this repository

This repository is the public **AITP protocol repository plus reference
adapter surface**.

It contains:

- the top-level charter and design principles;
- protocol object definitions and schemas;
- reference installation and uninstall guidance;
- adapter assets for OpenClaw, Codex, Claude Code, and OpenCode;
- a minimal reference-runtime boundary document.

It does not pretend to contain the full internal working environment.

## Relationship to the integration workspace

The current integration-heavy working environment still lives outside this
repository. In practice, a larger workspace may host:

- human theory notes,
- topic-local runtime state,
- validation runs,
- source registries,
- and experimental adapters.

This repository defines the public contract that such an environment should obey.

## Install paths

Start here:

- read the charter: [`docs/CHARTER.md`](docs/CHARTER.md)
- understand the agent boundary: [`docs/AGENT_MODEL.md`](docs/AGENT_MODEL.md)
- avoid context bloat: [`docs/CONTEXT_LOADING.md`](docs/CONTEXT_LOADING.md)

Adapter install guides:

- OpenClaw: [`docs/INSTALL_OPENCLAW.md`](docs/INSTALL_OPENCLAW.md)
- Codex: [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md)
- Claude Code: [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md)
- OpenCode: [`docs/INSTALL_OPENCODE.md`](docs/INSTALL_OPENCODE.md)
- Uninstall: [`docs/UNINSTALL.md`](docs/UNINSTALL.md)

## Protocol objects

The first public contract family includes:

- [`contracts/research-question.md`](contracts/research-question.md)
- [`contracts/candidate-claim.md`](contracts/candidate-claim.md)
- [`contracts/derivation.md`](contracts/derivation.md)
- [`contracts/validation.md`](contracts/validation.md)
- [`contracts/operation.md`](contracts/operation.md)
- [`contracts/promotion-or-reject.md`](contracts/promotion-or-reject.md)

Matching schemas live under [`schemas/`](schemas/).

## Reference adapters

Reference adapter assets live under [`adapters/`](adapters/):

- `adapters/openclaw/`
- `adapters/codex/`
- `adapters/claude-code/`
- `adapters/opencode/`

These are reference plugin surfaces. They are intentionally lightweight and
assume an available `aitp` executable on `PATH`.

## Current status

This repository is still early, but its public identity is now explicit:

- it is a charter-and-protocol repository first;
- it provides reference adapter assets second;
- it keeps implementation claims honest;
- it does not hide research logic in undocumented code.

## Repository map

```text
AITP-Research-Protocol/
  README.md
  contracts/
  schemas/
  adapters/
  docs/
  reference-runtime/
```

## See also

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/design-principles.md`](docs/design-principles.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/benchmark-cases.md`](docs/benchmark-cases.md)
- [`reference-runtime/README.md`](reference-runtime/README.md)
