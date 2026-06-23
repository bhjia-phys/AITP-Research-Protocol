<p align="center">
  <img src="plugins/aitp-research-protocol/assets/icon.svg" alt="AITP icon" width="128" height="128">
</p>

# AITP - AI Theoretical Physicist Protocol

AITP is a local research graph and agent tool layer for theoretical-physics
work. It gives human researchers and AI agents a shared, typed record of what
was claimed, what was actually checked, what remains uncertain, and where the
next valid research action is.

It is not a chatbot, a generic note app, an automatic theorem prover, or a
transcript logger. The goal is more specific: preserve the real scientific
process well enough that another agent or human can continue the work without
confusing notes, guesses, failed setup, validation, and trusted conclusions.

## Protocol Goal

AITP is designed around a human-in-the-loop research loop:

1. A human or agent works on a theoretical-physics problem.
2. Durable research moments are written into a typed graph.
3. Agents read that graph through MCP or CLI tools before acting.
4. Evidence, validation, proof gaps, route changes, and human decisions stay
   distinguishable.
5. Trust or long-term memory promotion only happens after explicit checks.

The protocol tries to enforce one central distinction:

```text
context and orientation != evidence
tool execution != validation
summary != truth
claim status != proof
```

This makes AITP useful for long-running theory projects where intermediate
process matters: literature reading, derivations, numerical checks, code-method
development, failed routes, benchmark provenance, and final synthesis.

## Current Implementation

The current release is **AITP 0.5.0**. Its implementation generation is
**v5**. The active code is under [`brain/v5/`](brain/v5/).

AITP v5 has three layers:

1. **Typed research graph** stored on disk under a workspace-local `.aitp/`
   directory.
2. **Agent-facing MCP server** at
   [`brain/v5/native_mcp.py`](brain/v5/native_mcp.py), exposing `aitp_v5_*`
   tools for reading and writing graph records.
3. **CLI and installer utilities** for diagnostics, fallback operations, and
   project setup.

The normal architecture is:

```text
human / Codex / Claude Code / Kimi Code / Hakimi / other agent
        |
        v
MCP tools: aitp_v5_*
        |
        v
AITP v5 typed records under <topics-root>/.aitp/
        |
        v
derived briefs, graph slices, audits, relation maps, summaries
```

The typed records are the source of truth. Briefs, dashboards, process graph
slices, summaries, and audits are derived views. They are useful for navigation,
but they do not update trust by themselves.

Legacy L0-L4 Markdown tools are read-only by default in 0.5.0. Historical files
and legacy servers remain for audit, migration, rollback, and tests, but normal
research writes must go through `aitp_v5_*` typed tools. Setting
`AITP_LEGACY_ENABLE_WRITES=1` is an explicit migration-debug escape hatch, not a
normal runtime mode.

## What AITP Can Do Today

AITP v5 currently supports:

- project and topic initialization
- topic, session, claim, and claim-status records
- source and reference-location records
- source assets, artifacts, hashes, and output locations
- physics objects, definitions, notation, relations, equations, and assumptions
- code state, tool recipes, tool runs, and execution provenance
- evidence records linked to claims, sources, artifacts, and tool runs
- validation contracts and validation results
- proof obligations and unresolved theory gaps
- route choices, pivots, blocked attempts, and exploratory reasoning
- human checkpoints and checkpoint decisions
- trust preflight, trust update records, and memory-promotion packets
- read-only execution briefs, claim relation maps, graph slices, and audits
- progressive recording navigation for deciding where a durable moment belongs
- project-scope adapter installs for Codex, Claude Code, and Kimi Code
- a repository-backed Codex plugin with first-run configuration tools
- migration and recovery audits for older AITP topic stores

AITP is strongest when the research question has durable structure:

- formal or derivation-heavy theoretical work,
- numerical/model claims that require provenance and validation,
- scientific-code method development,
- literature-to-claim reconstruction,
- long projects that need handoff between sessions or agents.

## What AITP Does Not Do

AITP deliberately does not:

- prove physics claims automatically,
- decide final scientific truth without evidence and validation,
- record every chat turn or every tool call,
- promote summaries into trusted memory by default,
- replace human judgment at theory or trust boundaries,
- guarantee that every host application fires lifecycle hooks perfectly.

The protocol is a truth-preserving substrate. The host agent still has to do
the research work and call the right tools at the right moments.

## Research Graph Layout

A workspace normally has a topics root:

```text
<workspace>/research/aitp-topics/
```

The canonical AITP store is:

```text
<workspace>/research/aitp-topics/.aitp/
```

The v5 store is organized like this:

```text
.aitp/
|-- topics/        topic-local runtime views and dashboards
|-- contexts/      research context records
|-- registry/      typed graph records
|-- runtime/       sessions and runtime state
|-- memory/        promoted scoped memory
|-- surfaces/      generated read-only views and review packets
|-- tools/         tool metadata and tool surfaces
|-- curated_rag/   optional heuristic background corpus
|-- migrations/    migration audits and old-store accounting
`-- schemas/       schema and contract material
```

The core graph records live under `registry/`. Important record families include
`claims`, `evidence`, `reference_locations`, `source_assets`,
`physics_objects`, `object_relations`, `code_states`, `tool_recipes`,
`tool_runs`, `validation_contracts`, `validation_results`,
`proof_obligations`, `research_runs`, `research_run_events`, `checkpoints`,
`promotion_packets`, and `trust_updates`.

## How Agents Should Use AITP

AITP should be used as a progressive, read-first protocol.

For status questions or old-topic recovery, agents should usually read only:

1. find the topic/session/claim,
2. read the execution brief,
3. read the claim relation map,
4. summarize current support, limits, blockers, and next valid actions.

For active research, agents should write only at durable moments:

- a reusable source or source location was identified,
- a tool/code run produced research-relevant output,
- an artifact, report, table, plot, log, or raw dump was produced,
- a result, anomaly, contradiction, negative result, or failed check appeared,
- a proof gap, validation gap, missing provenance, or route blocker was found,
- a route was selected, pivoted, abandoned, or split,
- claim scope/status changed or needs review,
- a human checkpoint or promotion decision is needed,
- a session-end handoff creates durable future context.

The recommended recording flow is:

```text
classify recording candidate
        |
        v
read first-level recording navigation state
        |
        v
expand exactly one slot
        |
        v
call the named typed write or preflight tool
        |
        v
verify the recording effect
```

This keeps the graph useful without making the agent write on every internal
thought step.

## MCP Tool Layer

The MCP server entrypoint is:

```text
brain/v5/native_mcp.py
```

MCP hosts should run that file directly. Do not point MCP at `aitp-v5` or at the
legacy servers.

If a host accidentally calls a legacy write tool such as
`aitp_bootstrap_topic`, `aitp_submit_candidate`, or `aitp_promote_candidate`,
the legacy stdio/HTTP wrappers return a JSON-RPC error instead of writing old
`state.md`, L0, L1, L3, L4, or legacy L2 files. Legacy read tools may still be
used for orientation and migration discovery.

Generic MCP config shape:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "uv",
      "args": [
        "run",
        "--with",
        "pyyaml",
        "--with",
        "jsonschema",
        "--with",
        "fastmcp",
        "python",
        "/absolute/path/to/AITP-Research-Protocol/brain/v5/native_mcp.py"
      ],
      "cwd": "/absolute/path/to/AITP-Research-Protocol",
      "env": {
        "AITP_TOPICS_ROOT": "/absolute/path/to/workspace/research/aitp-topics"
      }
    }
  }
}
```

Different hosts use slightly different config keys. The installer writes the
correct project-local files for supported hosts.

## CLI Layer

The CLI is useful for diagnostics, smoke tests, scripted fallback operations,
and local inspection.

Use it from the repository root:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --help
```

Common commands:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli init /path/to/workspace/research/aitp-topics

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics brief <session-id>

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics relation-map <session-id>

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics workspace recording-audit

uv run --with pyyaml --with jsonschema --with fastmcp \
  python -m brain.v5.cli --base /path/to/workspace/research/aitp-topics recording navigation-state <session-id>
```

If you have linked the Node wrapper from `package.json`, `aitp-v5` is a shorter
alias for the same v5 CLI. The repository-local `uv run ... python -m
brain.v5.cli` form is the most explicit and portable.

## Install

Prerequisites:

- Git
- Python 3.10 or newer
- `uv` recommended for dependency isolation
- at least one supported host agent if you want automatic agent wiring:
  Codex, Claude Code, or Kimi Code

Clone the repository:

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
```

### Recommended: Project-Scope Install

Project-scope install keeps AITP configuration inside one research workspace.
This is the safest mode for reproducible research and multi-agent use.

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent all \
  --scope project \
  --target-root /absolute/path/to/workspace \
  --topics-root /absolute/path/to/workspace/research/aitp-topics
```

This installs workspace-local adapter files such as:

- `.mcp.json`
- `.codex/skills/...`
- `.codex/mcp.json`
- `.codex/config.toml`
- `.claude/...`
- `.kimi/...`
- `.kimi-code/...`

The exact files depend on the selected agent and the host's conventions.

Project-scope install does **not** register a global `aitp` wrapper. It keeps
host configuration local to the target workspace.

### Optional: User-Scope Install

User-scope install writes into user-level agent config locations. Use it only if
you intentionally want AITP available globally for that host account.

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py install \
  --agent codex \
  --scope user \
  --topics-root /absolute/path/to/workspace/research/aitp-topics
```

User scope may register a global `aitp` package-manager wrapper when possible.
For shared or sensitive research machines, prefer project scope.

### Verify Install

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status

uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py doctor
```

`status` reads `~/.aitp/install-record.json` and reports recorded installs.
`doctor` checks Python dependencies, the 0.5.0/v5 version contract, v5 server
files, topics root health, MCP entrypoints, project-scope consistency, and
common stale-residue problems.

After installing or changing MCP config, restart the host agent so it reloads
its MCP servers and skills.

### Optional: Codex Plugin

The repository also ships a local Codex plugin at
[`plugins/aitp-research-protocol/`](plugins/aitp-research-protocol/). The plugin
wraps the v5 MCP server and gateway skills in a Codex plugin package.

<p>
  <img src="plugins/aitp-research-protocol/assets/icon.svg" alt="AITP Research Protocol plugin icon" width="96" height="96">
</p>

Install the repo-local marketplace once:

```bash
codex plugin marketplace add .agents/plugins
codex plugin add aitp-research-protocol@aitp-local
```

On first use, if the plugin cannot find an AITP checkout, it starts in setup
mode instead of failing. Setup mode exposes `aitp_config_status`,
`aitp_suggest_config`, and `aitp_configure`, so Codex can ask for:

- the local `AITP-Research-Protocol` checkout path,
- the topics root where AITP should store records.

The plugin saves this to `~/.aitp/codex-plugin-config.json`. After configuration,
restart Codex or open a new thread so the full `aitp_v5_*` MCP surface loads.

## Update

To refresh installed adapters from the current repository checkout:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py update
```

To pull the latest repository changes and redeploy recorded installs:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py upgrade
```

Run `doctor` after update or upgrade.

## Uninstall

Use the package manager whenever possible. It removes only files recorded during
install.

Project-scope uninstall:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope project \
  --target-root /absolute/path/to/workspace
```

User-scope uninstall:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py uninstall \
  --agent all \
  --scope user
```

Then verify:

```bash
uv run --with pyyaml --with jsonschema --with fastmcp \
  python scripts/aitp-pm.py status
```

Manual cleanup notes are in [`docs/UNINSTALL.md`](docs/UNINSTALL.md).

## Hakimi And Other Harnesses

AITP can be used by a specialized research harness or by a general coding
agent.

For Hakimi-style integration:

- Hakimi owns the live work loop and workframes.
- AITP owns durable scientific records and trust boundaries.
- Hakimi should read AITP context through MCP, write durable moments through
  typed AITP tools, and avoid maintaining a parallel scientific truth layer.

For a generic agent harness:

- expose only a small AITP entry surface at startup,
- let the agent discover deeper graph structure progressively,
- use read tools for navigation and context,
- use typed write tools only at durable research moments,
- run trust preflight before confidence or memory-promotion changes.

Hooks can help with session start, pre-tool policy, post-tool trace capture, or
stop-time handoffs, but hooks are runtime metadata. They should not be treated
as scientific evidence or trusted memory by themselves.

## Optimization Direction

The current v5 implementation is usable, but the main improvement directions
are clear:

- make progressive recording navigation easier for agents to follow,
- keep the exposed MCP surface small at startup and reveal detail on demand,
- strengthen graph schema validation and migration accounting,
- improve host lifecycle hook reliability across Codex, Claude Code, Kimi Code,
  Hakimi, and other runtimes,
- improve source reconstruction from papers, notes, and artifacts,
- make validation contracts easier to generate and review,
- improve human review packets for trust updates and memory promotion,
- add more end-to-end acceptance tests with real project workspaces.

These optimizations should preserve the same boundary: AITP records research
truth through typed records, not through unverified summaries or hidden agent
memory.

## Repository Map

```text
AITP-Research-Protocol/
|-- brain/v5/              current typed kernel, CLI, MCP tools, adapters
|-- brain/mcp_server.py    legacy L0-L4 MCP server, read-only by default
|-- deploy/                host templates and agent-facing skill material
|-- docs/                  protocol docs, install notes, historical designs
|-- hooks/                 lifecycle hook runners and guards
|-- scripts/               installer, maintenance, migration helpers
|-- tests/                 v5 and compatibility tests
|-- bin/aitp-v5.mjs        optional Node CLI wrapper
`-- package.json           optional package metadata for the CLI wrapper
```

New integrations should use `brain/v5/native_mcp.py` and `brain/v5/`.
Legacy L0-L4 files remain for migration and historical interpretation only;
they are not the active 0.5.0 research workflow.

## Development Checks

For v5-focused changes:

```bash
python -m compileall -q brain/v5
pytest tests -q
git diff --check -- .
```

For narrow changes, run the focused tests that cover the touched surface first.
Some legacy tests describe older protocol behavior, so prefer v5-specific tests
when modifying v5 runtime, MCP, graph, or adapter code.

## Key Docs

- [`docs/AITP_SPEC.md`](docs/AITP_SPEC.md) - protocol specification
- [`docs/INSTALL.md`](docs/INSTALL.md) - install guide
- [`docs/UNINSTALL.md`](docs/UNINSTALL.md) - manual uninstall notes
- [`docs/INSTALL_CODEX.md`](docs/INSTALL_CODEX.md) - Codex adapter notes
- [`docs/INSTALL_CLAUDE_CODE.md`](docs/INSTALL_CLAUDE_CODE.md) - Claude Code setup
- [`docs/INSTALL_KIMI_CODE.md`](docs/INSTALL_KIMI_CODE.md) - Kimi Code setup

## License

MIT. See [`LICENSE`](LICENSE).
