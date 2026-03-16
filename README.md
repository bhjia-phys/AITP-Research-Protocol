# AITP Research Charter and Kernel

> A protocol-first and now minimally installable public repository for building
> an AI Theoretical Physicist as a disciplined research participant rather than
> a free-form chat agent.

## What This Repository Is

AITP stands for **AI Theoretical Physicist**.

This repository now exposes a public research charter plus a standalone AITP
kernel:

- the **charter** that defines what serious AI-assisted theoretical-physics work
  should respect;
- the **protocol contracts** that define the durable artifacts and gates;
- a **standalone installable kernel** with fixed `L0-L4` directories, schemas,
  and cross-layer protocol surfaces;
- a **minimal runtime** that materializes state, runs audits, and executes
  explicit handlers inside that kernel;
- **reference adapters** for Codex, OpenClaw, Claude Code, and OpenCode.

The public repository is intentionally general.
It ships the fixed layer surfaces, contracts, and runtime boundaries, but not a
single fixed scientific agenda.
Different users should be able to populate the same `L0-L4` structure for:

- formal theory and derivation-heavy research;
- toy-model theoretical-physics numerics;
- code-backed theoretical-physics algorithm development.

The intended rule is:

- the charter is above the runtime;
- the protocol is above agent heuristics;
- agents are executors and adapters, not the source of truth.

## Why This Exists

Large models can produce fluent research language. That is not enough.

AITP is built to preserve the things that matter for real research:

- evidence before speculation;
- durable artifacts instead of chat residue;
- explicit uncertainty instead of false confidence;
- reusable knowledge instead of one-off output;
- visible validation and rejection paths;
- human-readable state that later agents and humans can audit.

## Core Research Model

AITP currently works through an `L0-L4` research structure:

- `L0`: source entry, survey, and acquisition substrate
- `L1`: analysis and provisional understanding
- `L2`: long-term reusable knowledge and active memory
- `L3`: exploratory conclusions, candidate claims, and not-yet-trusted reusable material
- `L4`: planning, execution, validation, and adjudication

The default non-trivial route remains:

`L0 -> L1 -> L3 -> L4 -> L2`

What matters is not only the layer map, but the rule that an agent may not
silently decide its own research workflow. It must follow durable contracts.
Each clone may extend the content inside these layers and may bridge external
formal-theory note systems, software repositories, or result stores, but the
directory and contract surfaces should remain stable.

## Quick Start

Clone the repository, install the minimal runtime, then install the wrapper for
the runtime you actually want to use:

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol

python -m pip install -e research/knowledge-hub
aitp doctor

# choose one, or install them all
aitp install-agent --agent codex --scope user
aitp install-agent --agent openclaw --scope user
aitp install-agent --agent claude-code --scope user
aitp install-agent --agent opencode --scope user
```

Then start AITP work through the runtime instead of through free-form prompting:

```bash
aitp loop --topic "Bounded formal-theory smoke topic" --human-request "do a bounded literature and route check without scientific conclusions"
```

For Codex-driven coding or execution work, use the wrapper that forces a loop
refresh before `codex exec`:

```bash
aitp-codex --topic-slug bounded-formal-theory-smoke-topic "continue the bounded task"
```

The public runtime now defaults to the repo-local kernel root:

- `research/knowledge-hub`

So a fresh clone no longer depends on the original private integration
workspace just to get `aitp` running.

`aitp doctor` now serves as the structural check for a fresh clone: it should
show the detected repo/kernel roots plus the layer and contract surfaces that
make the standalone install complete.

## Installation Flow

```mermaid
flowchart TD
    A[Clone AITP-Research-Protocol] --> B[pip install -e research/knowledge-hub]
    B --> C[aitp doctor]
    C --> D{Choose runtime}
    D --> E[aitp install-agent --agent codex]
    D --> F[aitp install-agent --agent openclaw]
    D --> G[aitp install-agent --agent claude-code]
    D --> H[aitp install-agent --agent opencode]
    E --> I[Open runtime normally]
    F --> I
    G --> I
    H --> I
    I --> J[Enter through aitp loop or aitp-codex]
    J --> K[Read runtime_protocol.generated.md]
    K --> L[Do bounded research work]
    L --> M[Run audits and trust gates]
```

## Runtime Flow

```mermaid
flowchart TD
    A[Human research request] --> B[aitp bootstrap or aitp loop]
    B --> C[Materialize topic state and queue]
    C --> D[Generate runtime protocol bundle]
    D --> E[Agent reads protocol bundle and runtime artifacts]
    E --> F{Bounded next action}
    F --> G[L0 or L1 source/intake work]
    F --> H[L3 candidate or exploratory work]
    F --> I[L4 validation or execution]
    G --> J[aitp audit]
    H --> J
    I --> K[baseline / atomize / trust-audit when required]
    K --> J
    J --> L{Passes conformance?}
    L -->|yes| M[Persist reproducible artifacts and notes]
    L -->|no| N[Run does not count as AITP work]
    M --> O[L2 promote or reject]
```

## Agent Support Matrix

| Runtime | Public install path | Enforcement surface |
|---------|----------------------|---------------------|
| Codex | `aitp install-agent --agent codex` | Skill + MCP + `aitp-codex` wrapper |
| OpenClaw | `aitp install-agent --agent openclaw` | Skill + MCP bridge setup note |
| Claude Code | `aitp install-agent --agent claude-code` | Skill + command bundle |
| OpenCode | `aitp install-agent --agent opencode` | Command harness + MCP config |

Current strength differs by runtime:

- `Codex` is the strongest path right now because `aitp-codex` hard-wraps the
  loop before it launches `codex exec`.
- `OpenCode`, `Claude Code`, and `OpenClaw` are currently constrained through
  installed command/skill surfaces plus conformance requirements, not through an
  equally strong native wrapper binary yet.

## What Python Still Does

AITP is protocol-first, not “Python decides the science”.

The runtime is only trusted to do the following:

- materialize protocol and state artifacts;
- build deterministic projections;
- run conformance, capability, and trust audits;
- execute explicit tool handlers;
- expose a thin `aitp` CLI and optional `aitp-mcp` surface.

It should not become the hidden source of scientific judgment.

## Repository Map

```text
AITP-Research-Protocol/
  README.md
  AGENTS.md
  docs/
  contracts/
  schemas/
  adapters/
  research/
    adapters/
      openclaw/
    knowledge-hub/
      LAYER_MAP.md
      ROUTING_POLICY.md
      COMMUNICATION_CONTRACT.md
      AUTONOMY_AND_OPERATOR_MODEL.md
      L2_CONSULTATION_PROTOCOL.md
      INDEXING_RULES.md
      L0_SOURCE_LAYER.md
      setup.py
      schemas/
      knowledge_hub/
      source-layer/
      intake/
      canonical/
      feedback/
      consultation/
      runtime/
      validation/
```

## Public Docs

Start here:

- charter: [`docs/CHARTER.md`](docs/CHARTER.md)
- agent boundary: [`docs/AGENT_MODEL.md`](docs/AGENT_MODEL.md)
- context loading: [`docs/CONTEXT_LOADING.md`](docs/CONTEXT_LOADING.md)
- architecture: [`docs/architecture.md`](docs/architecture.md)
- lessons from `get-physics-done`: [`docs/LESSONS_FROM_GET_PHYSICS_DONE.md`](docs/LESSONS_FROM_GET_PHYSICS_DONE.md)

Kernel contract surface:

- layer map: [`research/knowledge-hub/LAYER_MAP.md`](research/knowledge-hub/LAYER_MAP.md)
- routing policy: [`research/knowledge-hub/ROUTING_POLICY.md`](research/knowledge-hub/ROUTING_POLICY.md)
- communication contract: [`research/knowledge-hub/COMMUNICATION_CONTRACT.md`](research/knowledge-hub/COMMUNICATION_CONTRACT.md)
- autonomy/operator model: [`research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md`](research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md)
- L2 consultation: [`research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md`](research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md)
- indexing rules: [`research/knowledge-hub/INDEXING_RULES.md`](research/knowledge-hub/INDEXING_RULES.md)

Install guides:

- OpenClaw: [`docs/INSTALL_OPENCLAW.md`](docs/INSTALL_OPENCLAW.md)
- Codex: [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md)
- Claude Code: [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md)
- OpenCode: [`docs/INSTALL_OPENCODE.md`](docs/INSTALL_OPENCODE.md)
- Uninstall: [`docs/UNINSTALL.md`](docs/UNINSTALL.md)

Protocol objects:

- [`contracts/research-question.md`](contracts/research-question.md)
- [`contracts/candidate-claim.md`](contracts/candidate-claim.md)
- [`contracts/derivation.md`](contracts/derivation.md)
- [`contracts/validation.md`](contracts/validation.md)
- [`contracts/operation.md`](contracts/operation.md)
- [`contracts/promotion-or-reject.md`](contracts/promotion-or-reject.md)

## Current Status

The repository is now more than a pure protocol archive:

- it remains charter-and-protocol first;
- it now ships a standalone installable kernel under `research/knowledge-hub`;
- it now ships fixed `L0-L4` directories plus `consultation/`, `runtime/`, and `schemas/`;
- it can install user-side wrappers for the main target runtimes;
- it can bridge separate human-note and software backends into `L2` without hard-wiring one private knowledge base as the only target;
- it still keeps stronger private integration claims honest.

What is still incomplete:

- OpenClaw and OpenCode do not yet have a wrapper as hard as `aitp-codex`;
- the reference OpenClaw plugin assets are present, but the standalone
  workspace-seeding path is still less mature than the CLI-based wrapper path;
- full multi-runtime smoke testing should continue to expand.

## See Also

- [`docs/design-principles.md`](docs/design-principles.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/benchmark-cases.md`](docs/benchmark-cases.md)
- [`reference-runtime/README.md`](reference-runtime/README.md)
