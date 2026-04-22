<div align="center">
  <img src=".github/assets/aitp-mark.svg" width="80" height="80" alt="AITP">
  <h1>AITP Research Protocol</h1>
  <p><strong>An MCP-based research protocol that turns any AI coding agent into a disciplined theoretical-physics collaborator — keeping evidence separate from conjecture, remembering topics across sessions, and only promoting results to trusted memory after human approval.</strong></p>
  <p>
    <a href="#installation">Install</a> ·
    <a href="brain/PROTOCOL.md">Protocol Manual</a> ·
    <a href="docs/QUICKSTART.md">Quickstart</a> ·
    <a href="docs/roadmap.md">Roadmap</a>
  </p>
</div>

---

## What is AITP

AITP (AI-assisted Theoretical Physics) is a **stage-machine protocol** implemented as an MCP server. Any MCP-compatible agent — Claude Code, Kimi Code, Codex, OpenCode, or a custom wrapper — can drive theoretical-physics research through it.

The protocol enforces:

- **Layered evidence boundaries** — exploratory notes never become trusted results without explicit validation
- **Stage gates** — the agent cannot skip stages or fabricate confidence
- **Human-approval promotion** — nothing enters long-term trusted memory without your say-so
- **Cross-session durability** — topics survive session resets; resume days later with full context

## How it works

1. You describe what you want to study, in plain language.
2. AITP boots a **topic** with a bounded question, scope, and validation plan.
3. The agent works through stages — reading sources, sketching derivations, analyzing — inside the protocol's gate model.
4. When results look promising, AITP runs validation checks before asking for your review.
5. Only after your approval does material enter reusable memory.

## Protocol stages

```
L1 (read/frame) → L3 (ideation → planning → analysis → integration → distillation) → L4 (validate) → L2 (trusted) → L5 (write)
```

| Stage | Purpose | Key artifacts |
|-------|---------|--------------|
| **L1** | Source acquisition, framing | `source_basis.md`, `question_contract.md`, `convention_snapshot.md` |
| **L3** | Derivation through 5 subplanes | `active_idea.md`, `active_plan.md`, `active_analysis.md`, `active_integration.md`, `active_distillation.md` |
| **L4** | Validation and adjudication | `validation_contract.md`, review outcomes (pass / fail / contradiction) |
| **L2** | Promoted trusted knowledge | Global knowledge base, reusable across topics |
| **L5** | Publication writing | `flow_notebook.tex`, provenance files, draft paper |

## Architecture

```
AITP-Research-Protocol/
├── brain/                    # Core protocol engine
│   ├── mcp_server.py         # FastMCP server — 32 tools, prefixed mcp__aitp__aitp_*
│   ├── state_model.py        # Stage evaluation, gate logic, artifact templates
│   └── PROTOCOL.md           # Agent-facing operating manual (single source of truth)
│
├── skills/                   # Per-stage skill files loaded by the agent
│   ├── skill-init.md         # First-run workspace setup
│   ├── skill-read.md         # L1 reading
│   ├── skill-frame.md        # L1 framing
│   ├── skill-l3-*.md         # L3 subplanes (ideate, plan, analyze, integrate, distill)
│   ├── skill-validate.md     # L4 validation
│   ├── skill-promote.md      # L2 promotion
│   ├── skill-write.md        # L5 writing
│   └── skill-explore.md      # Quick-exploration mode
│
├── adapters/                 # Agent-specific integration surfaces
│   ├── claude-code/          # Claude Code adapter (hooks + skills + MCP)
│   ├── codex/                # Codex CLI adapter
│   ├── opencode/             # OpenCode adapter
│   └── openclaw/             # OpenClaw adapter
│
├── deploy/                   # Package manager templates
│   └── templates/            # Agent-specific deployment templates (hooks, skills, configs)
│
├── contracts/                # Human-readable artifact contracts
│   ├── research-question.md
│   ├── derivation.md
│   ├── candidate-claim.md
│   ├── validation.md
│   └── promotion-or-reject.md
│
├── schemas/                  # JSON Schema definitions for all artifacts
│   ├── topic-synopsis.schema.json
│   ├── derivation.schema.json
│   ├── validation.schema.json
│   └── ...                   # 16 schemas total
│
├── hooks/                    # Claude Code hook source scripts
│   ├── session_start.py      # SessionStart — skill injection, topic detection
│   ├── compact.py            # Context compaction handler
│   └── stop.py               # Session stop handler
│
├── scripts/                  # Tooling and migration
│   ├── aitp-pm.py            # Package manager (install / uninstall / update / upgrade)
│   ├── aitp                  # Unix CLI wrapper
│   ├── aitp.cmd              # Windows CLI wrapper
│   └── migrate_v0_to_v2.py   # Legacy topic migration
│
├── templates/                # LaTeX templates
│   └── flow_notebook.tex     # Derivation trail template for L5
│
├── tests/                    # Test suite
│   ├── test_state_model.py
│   ├── test_foundation_safety.py
│   ├── test_l3_subplanes.py
│   ├── test_l4_l2_memory.py
│   ├── test_l5_e2e.py
│   └── test_e2e_scenario_a.py
│
├── research/                 # Research data (git-ignored by default)
│   └── knowledge-hub/        # L2 knowledge base
│
└── docs/                     # Documentation
    ├── INSTALL.md            # Consolidated install index
    ├── QUICKSTART.md         # 5-minute quickstart
    ├── AITP_SPEC.md          # Protocol specification
    ├── CHARTER.md            # Project charter
    └── roadmap.md            # Development roadmap
```

## MCP tools (32)

The MCP server exposes 32 tools organized by function:

| Category | Tools |
|----------|-------|
| **Topic lifecycle** | `bootstrap_topic`, `list_topics`, `get_status`, `update_status`, `archive_topic`, `restore_topic`, `fork_topic` |
| **L1 reading & framing** | `register_source`, `list_sources`, `session_resume` |
| **L3 derivation** | `advance_to_l3`, `advance_l3_subplane`, `retreat_to_l1`, `record_derivation`, `switch_lane` |
| **L3 → L4 validation** | `submit_candidate`, `list_candidates`, `create_validation_contract`, `submit_l4_review`, `return_to_l3_from_l4` |
| **L2 knowledge** | `request_promotion`, `resolve_promotion_gate`, `promote_candidate`, `query_l2`, `ingest_knowledge`, `query_knowledge`, `lint_knowledge`, `writeback_query_result` |
| **L5 writing** | `advance_to_l5`, `return_from_l5` |
| **Agent guidance** | `get_execution_brief`, `get_skill_context` |

## Installation

### Prerequisites

- Python 3.10+
- An MCP-compatible AI agent (Claude Code, Kimi Code, Codex, OpenCode, etc.)

### Quick start

```bash
git clone https://github.com/bhjia-phys/AITP-Research-Protocol.git
cd AITP-Research-Protocol
python scripts/aitp-pm.py install
```

That's it. The package manager will:

1. **Deploy hooks and skills** to Claude Code (`~/.claude/`)
2. **Configure MCP server** for Kimi Code (`~/.kimi/`)
3. **Register the `aitp` command** globally — after this first run, you can use `aitp` from anywhere:

```bash
aitp install          # Install all agents (claude-code + kimi-code)
aitp uninstall        # Remove everything
aitp update           # Re-sync from repo to deployed locations
aitp upgrade          # Git pull + re-deploy (one-command update)
aitp status           # Show install status
aitp doctor           # Health check
```

### First-run topics root

On first install, AITP asks where to store research topics. You can pre-set this:

- **Environment variable**: `AITP_TOPICS_ROOT=/path/to/aitp-topics`
- **CLI flag**: `python scripts/aitp-pm.py install --topics-root /path/to/aitp-topics`

The choice is saved to `~/.aitp/install-record.json` and reused on subsequent runs.

### Supported agents

| Agent | Install method | What gets deployed |
|-------|---------------|-------------------|
| **Claude Code** | `aitp install` | Hooks (SessionStart, UserPromptSubmit, PreToolUse), skills (using-aitp, aitp-runtime), MCP server in settings.json |
| **Kimi Code** | `aitp install` | `~/.kimi/mcp.json` + `~/.kimi/config.toml` [mcp.servers.aitp] |
| **Codex CLI** | See `adapters/codex/` | Skill file integration |
| **OpenCode** | See `adapters/opencode/` | MCP + skill integration |
| **Any MCP agent** | Manual | Connect to `brain/mcp_server.py` via stdio |

## Research lanes

| Lane | Typical work | Validation |
|------|-------------|-----------|
| `formal_theory` | Proofs, derivations, algebra | Proof-gap analysis, consistency checks |
| `toy_numeric` | Model calculations, benchmarks | Convergence, finite-size scaling |
| `code_method` | Algorithm development | Reproduction, trust audit |

## Topic file structure

```
<topics_root>/
  <topic-slug>/
    state.md                         # YAML frontmatter: stage, posture, lane, subplane
    L0/sources/                      # Registered source metadata
    L1/
      source_basis.md
      question_contract.md
      convention_snapshot.md
      anchors.md
      contradictions.md
    L3/
      ideation/active_idea.md
      planning/active_plan.md
      analysis/active_analysis.md
      result_integration/active_integration.md
      distillation/active_distillation.md
      candidates/                    # Submitted distilled claims
      tex/flow_notebook.tex          # Derivation trail
    L4/
      validation_contract.md
      reviews/
    L5_writing/
      outline.md
      provenance/
      draft/
    runtime/                         # Execution state
```

## Philosophy

- **Evidence before confidence** — sources stay separate from speculation
- **Bounded steps, not freestyle** — every work unit has a clear question and scope
- **Humans own trust** — nothing becomes reusable memory without explicit approval
- **Durable by default** — research state survives session resets
- **Agent-agnostic** — any MCP client can drive the protocol

## License

MIT License — see [LICENSE](LICENSE) file for details.

## Documentation

| Document | Description |
|----------|-------------|
| [brain/PROTOCOL.md](brain/PROTOCOL.md) | Full agent-facing operating manual |
| [docs/AITP_SPEC.md](docs/AITP_SPEC.md) | Protocol specification |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | 5-minute quickstart guide |
| [docs/INSTALL.md](docs/INSTALL.md) | Consolidated install index |
| [docs/CHARTER.md](docs/CHARTER.md) | Project charter and principles |
| [docs/roadmap.md](docs/roadmap.md) | Development roadmap |
| [docs/design-principles.md](docs/design-principles.md) | Design principles |
