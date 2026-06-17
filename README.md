# AITP - AI Theoretical Physicist Protocol

> A typed research graph and agent-facing protocol layer for theoretical physics.

AITP is not a chatbot, note app, or automatic theorem prover. It is the local
research substrate that lets human researchers and AI agents work on theory
problems without losing the scientific trail.

AITP has three jobs:

1. **Research graph**: store claims, sources, physics objects, relations,
   evidence, code/tool provenance, validation results, open obligations, human
   checkpoints, and memory promotion decisions as typed records.
2. **Agent tool layer**: expose safe read/write operations through MCP
   (`aitp_v5_*`) and a CLI fallback (`aitp-v5`) so Codex, Claude Code, Kimi,
   Hakimi, and other agents can inspect and update the same graph.
3. **Research workflow guidance**: tell an agent when to read context, when to
   record provenance, when to ask the human, when to validate, and when not to
   claim trust.

The current implementation is **AITP v5** under `brain/v5/`.

## Mental Model

```text
human / agent / Hakimi
        |
        v
MCP tools and CLI commands
        |
        v
typed AITP records in .aitp/
        |
        v
read-only graph, brief, moment policy, audits, summaries
```

The typed records are the source of truth. Process graph slices, execution
briefs, summaries, and dashboards are derived views. They help a host agent
navigate the project, but they do not update claim trust by themselves.

## What AITP Records

AITP v5 can record:

- topics, sessions, active claims, claim status, and uncertainty
- papers, notes, source assets, artifacts, hashes, and locations
- physics objects, definitions, notation, relations, equations, and assumptions
- evidence linked to claims, sources, tools, artifacts, and validation results
- code state, tool recipes, tool runs, and execution environments
- validation contracts, validation results, failure modes, and missing checks
- proof obligations and unresolved theory gaps
- exploratory reasoning, route choices, pivots, blocked attempts, and lessons
- human checkpoints and promotion decisions
- scoped long-term memory entries

This makes AITP a research graph for the process of doing theory, not just a
folder of final notes.

## Store Layout

A workspace that uses AITP has a topics root, usually something like:

```text
research/aitp-topics/
```

The canonical AITP store is:

```text
research/aitp-topics/.aitp/
```

The v5 store is organized around stable top-level areas:

```text
.aitp/
|-- topics/        topic-local runtime views and dashboards
|-- contexts/      research context records
|-- registry/      typed records: claims, evidence, sources, tools, validation, etc.
|-- runtime/       sessions and runtime state
|-- memory/        promoted scoped memory
|-- surfaces/      generated read-only views and review packets
|-- tools/         tool metadata
|-- curated_rag/   optional heuristic background corpus
|-- migrations/    migration audits and old-store accounting
`-- schemas/       schema and contract material
```

The `registry/` directory is the core graph store. It contains record families
such as `claims`, `evidence`, `reference_locations`, `source_assets`,
`physics_objects`, `object_relations`, `tool_runs`, `code_states`,
`validation_contracts`, `validation_results`, `proof_obligations`,
`research_runs`, `research_run_events`, `checkpoints`, `promotion_packets`, and
`trust_updates`.

## Agent Tool Layer

AITP exposes the graph through two equivalent layers:

- **MCP**: `brain/v5/native_mcp.py`, exposing typed tools such as
  `aitp_v5_get_execution_brief`, `aitp_v5_get_process_graph_slice`,
  `aitp_v5_record_evidence`, and `aitp_v5_record_validation_result`.
- **CLI**: `python -m brain.v5.cli` or the installed `aitp-v5` wrapper.

Example MCP configuration:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "python",
      "args": ["/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"]
    }
  }
}
```

Do not point MCP at the CLI wrapper. MCP hosts should run `native_mcp.py`.
The CLI is for local diagnostics, scripted operations, and fallback use.

Useful CLI checks:

```bash
python -m brain.v5.cli init /path/to/topics-root
python -m brain.v5.cli --base /path/to/topics-root adapter public-surfaces
python -m brain.v5.cli --base /path/to/topics-root adapter bridge-targets
python -m brain.v5.cli --base /path/to/topics-root adapter payload-profiles
python -m brain.v5.cli --base /path/to/topics-root workspace recording-audit
python -m brain.v5.cli --base /path/to/topics-root graph slice <session-id>
python -m brain.v5.cli --base /path/to/topics-root graph moment-policy <session-id>
```

## Workflow Guidance

AITP gives host agents a conservative research workflow.

For a normal AITP-aware agent:

1. Classify the user request: status/Q&A can be read-only; continuation,
   derivation, validation, contradiction, final synthesis, and promotion are
   heavier.
2. If the topic or current graph position is unclear, call the read-only
   workspace recording audit (`aitp_v5_build_workspace_recording_audit`) to see
   which topic rows are navigable, which are blocked by recovery gaps, and which
   first-level slots should be inspected.
3. Restore the active session with `aitp_v5_get_execution_brief`.
4. Read the claim relation map before interpreting failures or support.
5. At durable moments, use the progressive recording navigator:
   classify candidate -> read per-topic navigation state -> expand one slot ->
   call the existing typed write/preflight tool -> verify the effect.
6. Record durable work through typed tools: source assets, references, tool
   runs, evidence, validation results, proof obligations, routes, and
   checkpoints.
7. Run trust preflight before any confidence or memory-promotion step.

For Hakimi integration:

1. Hakimi owns the runtime work loop and WorkFrame.
2. AITP owns the durable typed graph and trust boundaries.
3. Hakimi may read AITP context, compile graph/moment-policy decisions into
   call obligations, and execute allowed write-bridge operations.
4. Hakimi should not invent a parallel scientific memory or silently apply
   trust changes.

For a general harness:

1. Treat AITP as the canonical local kernel.
2. Use MCP to read graph state and write typed records.
3. Keep host-side summaries, traces, and prompt injections as orientation only.
4. Put final gates around evidence, validation, and trust decisions, not every
   ordinary coding or note-taking step.

## Trust Boundary

AITP is deliberately strict about trust:

- A reference location is a pointer, not evidence.
- A tool run is provenance, not validation.
- A summary is orientation, not claim support.
- Curated RAG is heuristic context, not evidence.
- A process graph slice is a derived view, not a new truth record.
- `trust_apply` is not exposed as a normal host write bridge target.
- Long-term memory promotion requires evidence, validation or scoped
  justification, and the required human or failure-mode checkpoints.

The weight should sit at scientific boundaries: evidence, validation,
promotion, contradiction, failure modes, and route changes.

## Quick Start

```bash
python -m brain.v5.cli init /path/to/topics-root

python -m brain.v5.cli --base /path/to/topics-root topic create fqhe \
  --context condensed-matter \
  --title "FQHE edge-sector counting"

python -m brain.v5.cli --base /path/to/topics-root claim create \
  --topic fqhe \
  --statement "Finite-size counting identifies the edge sector." \
  --evidence-profile finite_numeric \
  --confidence-state hypothesis \
  --uncertainty "finite-size artifacts may mimic the target counting"

python -m brain.v5.cli --base /path/to/topics-root session bind s1 \
  --topic fqhe \
  --context condensed-matter \
  --claim <claim-id>

python -m brain.v5.cli --base /path/to/topics-root brief s1
```

In normal use an agent calls the MCP tools rather than typing each command by
hand.

## Project-Scope Install

For a real research workspace, keep Codex, Claude Code, Kimi Code, and other
host agents pointed at the same AITP repo and topics root.

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent all \
  --scope project \
  --target-root /path/to/theory-workspace \
  --topics-root /path/to/theory-workspace/research/aitp-topics
```

Then verify:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status
```

Project installs write host glue into workspace-local surfaces such as
`.mcp.json`, `.codex/`, `.claude/`, and `.kimi/`. Those files are adapters. The
scientific authority remains the typed store under `<topics-root>/.aitp/`.

## Repository Map

```text
AITP-Research-Protocol/
|-- brain/v5/              typed kernel, CLI, MCP tools, contracts, adapters
|-- docs/                  specifications, install notes, design plans
|-- deploy/templates/      host skill and runtime templates
|-- hooks/                 lifecycle guards and runtime hooks
|-- tests/                 v5 and legacy tests
|-- scripts/               install and maintenance helpers
`-- brain/mcp_server.py    legacy L0-L4 MCP server
```

New research workflows should use `brain/v5/` and `brain/v5/native_mcp.py`.
Legacy L0-L4 material remains for migration and historical interpretation.

## Development Checks

For v5-focused changes:

```bash
python -m compileall -q brain/v5
pytest tests -q
git diff --check -- .
```

Some legacy tests may reflect older protocol surfaces. When changing only v5,
prefer focused v5 tests and targeted adapter smoke checks.

## Key Docs

- [`docs/AITP_SPEC.md`](docs/AITP_SPEC.md) - protocol specification
- [`docs/INSTALL.md`](docs/INSTALL.md) - general install guide
- [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md) - Codex adapter notes
- [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md) - Claude Code setup
- [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md) - Kimi Code setup

## License

MIT. See [`LICENSE`](LICENSE).
