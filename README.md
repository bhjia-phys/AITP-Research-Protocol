# AITP Research Protocol

**AI-assisted Theoretical Physics.** Protocol v4.0.

> 追求真理而非沽名钓誉。 *Pursue truth, not fame.*

AITP is a protocol layer that gives your AI agent the discipline of a good research collaborator: show your sources, justify your claims, don't skip steps, and only call something "known" after it passes gates.

## Quick start

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
python scripts/aitp-pm.py install
```

The installer detects your AI agents (Claude Code, Kimi Code), prompts for a topics directory, and deploys hooks, skills, and MCP configs automatically. After install, use `aitp` from anywhere:

```bash
aitp doctor     # Verify everything is working
aitp status     # Show what's installed
```

### Manual MCP setup

If you prefer to wire the MCP server yourself, add to `~/.claude/mcp.json` or project `.mcp.json`:

```json
{
  "mcpServers": {
    "aitp": {
      "command": "python",
      "args": ["/path/to/AITP-Research-Protocol/brain/mcp_server.py"]
    }
  }
}
```

Then run `/reload-plugins` in Claude Code.

### Other agents

AITP is agent-agnostic. Any MCP-compatible agent can use it. See `adapters/` for specific setups. Run `python scripts/aitp-pm.py install --agent kimi-code` for Kimi Code support.

## How to use

### Your first research topic

Once AITP is installed, tell your AI agent what you want to study in plain language. For example:

> "I want to understand how the GW approximation relates to the Kadanoff-Baym equations. Start by checking what's already known, then find the key papers."

The agent (equipped with the `using-aitp` skill) will:

1. **Check existing knowledge** — calls `aitp_query_l2_index` to see what's already in the L2 graph
2. **Create the topic** — calls `aitp_bootstrap_topic` to set up the directory structure
3. **Walk through the stages** — guided by `aitp_get_execution_brief` at each step

### Stage-by-stage workflow

**L0 — Discover sources.** The agent searches for papers, registers them (`aitp_register_source`), fills the source registry with coverage assessment. This stage answers: *Do I have enough to answer the question?*

**L1 — Read and frame.** TOC-first reading for every source. Skim all sections (Phase A), deep-extract the relevant ones (Phase B). Each extracted section immediately contributes concepts and obvious edges to L2. This stage answers: *What exactly are we trying to figure out?*

**L3 — Derive.** Flexible workspace with 7 activities: ideate, derive, trace-derivation, gap-audit, connect, integrate, distill. Switch between them freely — no forced sequence. Submit candidates when claims are ready.

**L4 — Validate.** Adversarial review with mandatory counterargument. Dimensional analysis, symmetry checks, limiting cases. Non-pass outcomes return to L3 for revision. This is the trust gate.

**L2 — Knowledge persists.** Promoted results enter the global L2 knowledge graph. L2 is both the endpoint of every topic and the starting point of the next.

### Two paths to L2

- **Path A (Lightweight):** L0 → L2 directly. For well-understood concepts with clear sources. Use `aitp_quick_l2_concept` to create concept + theorem nodes with edges in one call.
- **Path B (Deep):** L0 → L1 → L3 → L4 → L2. For novel or uncertain claims requiring derivation and adversarial review.

### Checking progress

Ask your AI: *"What's the status of this topic?"* — the AI calls `aitp_get_execution_brief` which returns gate status, missing requirements, and the next action.

### Resuming after a break

Just open the topic again. State is stored in plain Markdown files. No database. No session dependency. Call `aitp_session_resume` to restore full context.

### Best practices

- **Push after every feature.** See `skills/aitp-push-after-feature.md` — this exists because we learned the hard way.
- **Start from L2.** Every new topic should call `aitp_query_l2_index` first to discover what's already known.
- **Source everything.** Every L2 node and edge requires a `source_ref`. Provenance is mandatory.
- **Let the brief guide you.** Always call `aitp_get_execution_brief` before deciding what to do next. It tells you gates, blockers, and the next allowed action.

## Protocol stages (v4.0)

```
L0 (discover) → L1 (read → frame) → L3 (derive) ⇄ L4 (validate) → L2 (knowledge)
```

| Stage | What happens | Key artifacts |
|-------|-------------|--------------|
| **L0** | Find and register sources | `source_registry.md`, `L0/sources/*.md` |
| **L1** | TOC-first reading, bounded question, section intake | `source_toc_map.md`, `question_contract.md`, `L1/intake/` |
| **L3** | Derivation (research) or literature study | Subplane artifacts, candidates |
| **L4** | Adversarial validation with mandatory counterargument | Validation contracts, reviews |
| **L2** | Persistent, cross-topic knowledge graph | Nodes, edges, EFT towers |

**L5 (writing/publication) is removed in v4.0.** L2 is the endpoint. The knowledge graph itself is the output. Paper writing is the human's work.

## Expanding the L2 Knowledge Graph

L2 is the protocol's persistent memory — it grows with every topic. Here's how to expand it:

### Path A — Lightweight (L0 → L2 directly)

For concepts you already understand well and have clear sources for:

1. **Check what exists:** The agent calls `aitp_query_l2_index` to see domains and existing nodes
2. **Create nodes:** The agent calls `aitp_quick_l2_concept` which creates a concept node, a theorem/technique node, and an edge between them — all in one call. Every node requires `source_ref` (where the knowledge comes from).
3. **Add edges:** Call `aitp_create_l2_edge` to link related nodes across domains

Example: *"Add the Kramers-Kronig relations to L2 from this optics textbook chapter 3"* — the agent registers the source, creates the concept node, and links it to existing nodes like "Green's Function" and "Linear Response Theory".

### Path B — Deep (full pipeline)

For novel claims that need derivation and validation:

1. **Complete the full pipeline:** L0 → L1 → L3 → L4
2. **Request promotion:** `aitp_request_promotion` — you (the human) approve what enters L2
3. **Resolve conflicts:** If a new claim contradicts an existing L2 node, the protocol flags it. You decide: update the existing node (version bump), reject the new claim, or mark both as regime-dependent.

### What makes good L2 content

- **Concepts** — well-defined physical ideas (e.g., "Quasiparticle", "Spectral Function")
- **Theorems** — precise mathematical statements (e.g., "Wick's Theorem", "Fluctuation-Dissipation Theorem")
- **Relations** — typed edges between nodes: `derives_from`, `generalizes`, `approximates`, `contradicts`, `depends_on`, `is_dual_to`
- **Regime boundaries** — where approximations break down (e.g., "GW approximation fails for strongly correlated systems")
- **EFT towers** — organize approximations by energy scale

### Querying L2

Before starting any new topic, the agent should call `aitp_query_l2_index` to get the domain taxonomy. Then `aitp_query_l2_graph` with filters (domain, node type) to find specific nodes. Source provenance is hidden by default (to keep context lean) but available via `aitp_get_l2_provenance`.

### Trust levels

Nodes evolve through trust levels as evidence accumulates:
`source_grounded` → `multi_source_confirmed` → `validated` → `independently_verified`

You control promotion. The protocol provides evidence; you decide what enters the knowledge graph.

## Install / Update / Uninstall

AITP includes a package manager (`aitp-pm.py`) that handles deployment across AI agents. After initial setup, use the `aitp` command from anywhere.

### Install

```bash
git clone git@github.com:bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
python scripts/aitp-pm.py install
```

The installer:
- Detects installed AI agents (Claude Code, Kimi Code)
- Prompts for `topics_root` — where research topics live (default: `~/aitp-topics`)
- Deploys hooks (SessionStart, keyword routing, routing guard)
- Deploys skills (`using-aitp`, `aitp-runtime`)
- Registers MCP server config
- Creates a global `aitp` CLI wrapper

Options:
```bash
aitp install                          # All agents, user scope (auto-detects topics_root)
aitp install --agent claude-code      # Claude Code only
aitp install --scope project          # Project-level install (writes to .claude/)
aitp install --topics-root /path/to/topics  # Custom topics directory
```

### Update

Re-sync deployed files from the current repo state (no git pull):

```bash
aitp update
```

Options: `--agent claude-code`, `--topics-root <path>`

### Upgrade

Git pull latest + automatic re-deploy of all agents:

```bash
aitp upgrade
aitp upgrade --force    # Auto-stash local changes and proceed
```

### Uninstall

Remove hooks, skills, MCP configs, and CLI wrapper from all detected agents:

```bash
aitp uninstall
```

Options: `--agent claude-code`, `--scope project`

### Verify

```bash
aitp doctor     # Full health check (Python, deps, MCP, hooks, skills, topics)
aitp status     # Show install state and file health per agent
```

The `doctor` command checks: Python version, dependencies, repo integrity, topics root, Claude Code hooks/skills/settings, Kimi Code MCP/config.

## Architecture

```
AITP-Research-Protocol/
├── brain/
│   ├── mcp_server.py         # FastMCP server (~3500 lines, 35+ tools)
│   ├── state_model.py        # Gate logic, stage machine, domain taxonomy
│   ├── sympy_verify.py       # Symbolic verification (dimensions, algebra, limits)
│   └── PROTOCOL.md           # Protocol operating manual v4.0
├── scripts/
│   ├── aitp-pm.py            # Package manager (install/update/upgrade/uninstall)
│   ├── aitp / aitp.cmd       # CLI entry wrappers
│   └── generate_l2_viz.py    # L2 graph visualization
├── deploy/templates/         # Agent-specific deploy templates
│   ├── claude-code/          # Skills, hooks, routing guard for Claude Code
│   └── kimi-code/            # Skills for Kimi Code
├── skills/                   # Per-stage instructions
│   ├── skill-discover.md     # L0: source discovery
│   ├── skill-read.md         # L1: TOC-first reading workflow
│   ├── skill-l3-*.md         # L3 subplanes (research + study)
│   └── aitp-push-after-feature.md  # Push discipline
├── tests/                    # Test suite
├── docs/                     # Specs, guides, design documents
├── hooks/                    # Agent hook scripts (session start, compact, stop)
├── adapters/                 # Agent-specific integrations
├── contracts/                # Artifact templates
├── schemas/                  # JSON Schema definitions
└── templates/                # LaTeX templates
```

## Design principles

- **Evidence before confidence.** No claim without provenance.
- **Bounded questions, not open-ended exploration.** Every topic has a contract.
- **Humans own trust.** The promotion gate exists because "the AI seems confident" is not a valid reason.
- **Durable by default.** Research state lives in your filesystem (plain Markdown), not in chat sessions.
- **Agent-agnostic.** Any MCP-speaking agent can drive the protocol.
- **Compiled, not raw.** L2 stores distilled knowledge. Source provenance is stored for auditing but hidden from default queries to prevent context bloat.

## Documentation

| Document | Description |
|----------|-------------|
| [brain/PROTOCOL.md](brain/PROTOCOL.md) | Protocol operating manual (the AI reads this) |
| [docs/superpowers/specs/](docs/superpowers/specs/) | Feature specs |
| [research/knowledge-hub/](research/knowledge-hub/) | Protocol playbooks and contracts |

## License

MIT. See [LICENSE](LICENSE).
