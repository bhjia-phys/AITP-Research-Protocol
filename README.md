<div align="center">
  <img src=".github/assets/aitp-mark.svg" width="80" height="80" alt="AITP">
  <h1>AITP Research Protocol</h1>
  <p><em>Because your AI collaborator shouldn't hallucinate a breakthrough at 3 AM and forget it by morning.</em></p>
  <p>
    <a href="#installation">Install</a> ·
    <a href="brain/PROTOCOL.md">Protocol Manual</a> ·
    <a href="docs/QUICKSTART.md">Quickstart</a>
  </p>
</div>

---

## The problem

You've tried using an AI coding assistant for physics research. It went something like this:

- You ask about a symmetry argument. It gives you a plausible-sounding derivation. You spend an hour checking — turns out it silently dropped a boundary condition.
- You close your laptop. The next morning, the session is gone. The AI has no memory of yesterday's work.
- It confidently claims a result. You ask "where did this come from?" and it can't trace its own reasoning.

Sound familiar? These are not bugs in the AI. They're missing **discipline** — the same discipline you'd enforce in a research group meeting: *show your sources, justify your claims, don't skip steps, and get sign-off before calling something "known."*

## What AITP does

AITP gives your AI agent that discipline. It's a protocol layer that sits between you and any MCP-compatible AI agent (Claude Code, Kimi Code, Codex, etc.) and enforces the same workflow you'd use in real theoretical work:

1. **Read before you reason.** Register your sources. Record what each paper actually says, not what you wish it said.
2. **Frame a bounded question.** Not "study quantum gravity" — but "under what conditions does the WKB approximation break down for this class of potentials?"
3. **Derive in stages.** Ideation → plan → analysis → integration → distillation. Each step has a gate. You can't skip ahead.
4. **Validate before you trust.** The agent proposes a result. AITP runs consistency checks. Then *you* review it.
5. **Promote only with human approval.** Nothing enters the trusted knowledge base unless you say so. Nothing.

Think of it as an infinitely patient research collaborator who keeps a perfect lab notebook — but never calls a result "done" without showing you the work.

## Protocol stages

```
L0 (discover) → L1 (read/frame) → L3 (ideation → planning → analysis → integration → distillation) → L4 (validate) → L2 (trusted) → L5 (write)
```

| Stage | What happens | Physics analogy |
|-------|-------------|-----------------|
| **L0** | Find and register sources | The literature search before the seminar — papers, datasets, code, experiments |
| **L1** | Read sources, frame the question | Literature review + defining the scope of your calculation |
| **L3** | Derive through 5 subplanes | The actual work: scratchpad → formal derivation → checking → synthesizing → distilling claims |
| **L4** | Validation and adjudication | The "show me" moment — consistency checks, boundary cases, cross-references |
| **L2** | Promoted to trusted knowledge | What goes into your group's shared notes — only after you sign off |
| **L5** | Publication writing | The paper draft, with full provenance of every claim |

The key insight: **L2 is not the starting point.** It's where things arrive after passing through the evidence pipeline. Your AI can't just *declare* something as known. It has to earn it.

## Cross-session durability

You close your laptop. Three days later, you reopen the conversation. The AI says:

> *"I have no memory of what we were doing."*

AITP fixes this. Every topic's state — what stage it's at, what sources were read, what derivations were attempted, what claims are pending validation — is stored in plain Markdown files. The AI picks up exactly where it left off, because the protocol state is in your filesystem, not in a chat window that disappears.

## Research lanes

Different kinds of physics work need different discipline:

| Lane | When to use it | How AITP validates |
|------|---------------|-------------------|
| `formal_theory` | Proofs, algebraic manipulations, logical arguments | Proof-gap analysis, logical consistency |
| `toy_numeric` | Model calculations, numerical experiments, benchmarks | Convergence checks, finite-size scaling, sanity bounds |
| `code_method` | Algorithm development, computational methods | Reproduction, trust audits |

## Architecture

```
AITP-Research-Protocol/
├── brain/                    # Core protocol engine
│   ├── mcp_server.py         # FastMCP server — 32 tools, prefixed mcp__aitp__aitp_*
│   ├── state_model.py        # Gate logic: what transitions are allowed, when
│   └── PROTOCOL.md           # The operating manual your AI reads
│
├── skills/                   # Per-stage instructions loaded by the agent
│   ├── skill-init.md         # First-run workspace setup
│   ├── skill-read.md         # "Read the paper carefully" as a protocol step
│   ├── skill-frame.md        # "Define the question precisely"
│   ├── skill-l3-*.md         # Five L3 subplanes (ideate → plan → analyze → integrate → distill)
│   ├── skill-validate.md     # "Prove it or lose it"
│   ├── skill-promote.md      # "Get the human to sign off"
│   └── skill-write.md        # "Write it up with full provenance"
│
├── adapters/                 # Agent-specific integration surfaces
│   ├── claude-code/          # Claude Code hooks + skills + MCP
│   ├── codex/                # Codex CLI
│   ├── opencode/             # OpenCode
│   └── openclaw/             # OpenClaw
│
├── contracts/                # Human-readable artifact templates
│   ├── research-question.md  # What a well-formed question looks like
│   ├── derivation.md         # What a derivation record must contain
│   ├── candidate-claim.md    # What a claim must state before validation
│   ├── validation.md         # What a validation contract checks
│   └── promotion-or-reject.md # What the human sees at the gate
│
├── schemas/                  # Machine-readable JSON Schemas (16 total)
├── deploy/                   # Package manager deployment templates
├── hooks/                    # Claude Code hook source scripts
├── scripts/                  # Package manager + migration tools
├── templates/                # LaTeX templates (flow notebook for L5)
├── tests/                    # Test suite
└── docs/                     # Documentation
```

## MCP tools (32)

The AI drives the protocol through 34 structured tools — it cannot directly edit topic files. Every action goes through a gate:

| Category | Tools |
|----------|-------|
| **Topic lifecycle** | `bootstrap_topic`, `list_topics`, `get_status`, `update_status`, `archive_topic`, `restore_topic`, `fork_topic` |
| **L0 — discovery** | `register_source`, `list_sources`, `advance_to_l1`, `retreat_to_l0` |
| **L1 — reading** | `session_resume`, `ingest_knowledge` |
| **L3 — derivation** | `advance_to_l3`, `advance_l3_subplane`, `retreat_to_l1`, `record_derivation`, `switch_lane` |
| **L3 → L4 — validation gate** | `submit_candidate`, `list_candidates`, `create_validation_contract`, `submit_l4_review`, `return_to_l3_from_l4` |
| **L2 — trusted knowledge** | `request_promotion`, `resolve_promotion_gate`, `promote_candidate`, `query_l2`, `ingest_knowledge`, `query_knowledge`, `lint_knowledge`, `writeback_query_result` |
| **L5 — writing** | `advance_to_l5`, `return_from_l5` |
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

The package manager deploys hooks, skills, and MCP configs to your agent(s), and registers the `aitp` command globally. After the first run:

```bash
aitp install          # Deploy to all agents
aitp uninstall        # Remove everything
aitp update           # Re-sync from repo
aitp upgrade          # git pull + re-deploy
aitp status           # Check install state
aitp doctor           # Full health check
```

### First-run topics root

AITP asks where to store your research topics. Pre-set it if you prefer:

- **Environment variable**: `AITP_TOPICS_ROOT=/path/to/aitp-topics`
- **CLI flag**: `python scripts/aitp-pm.py install --topics-root /path/to/aitp-topics`

Saved to `~/.aitp/install-record.json` — persists across sessions.

### Supported agents

| Agent | What gets deployed |
|-------|-------------------|
| **Claude Code** | Hooks (SessionStart, UserPromptSubmit, PreToolUse), skills, MCP server |
| **Kimi Code** | `~/.kimi/mcp.json` + `config.toml` |
| **Codex CLI** | See `adapters/codex/` |
| **OpenCode** | See `adapters/opencode/` |
| **Any MCP agent** | Connect to `brain/mcp_server.py` via stdio — protocol is agent-agnostic |

## Topic file structure

Every topic is a directory of plain Markdown files. No database, no proprietary format. You can read, diff, and grep your own research:

```
<topics_root>/
  <topic-slug>/
    state.md                         # Current stage, posture, lane
    L0/
      source_registry.md             # Source inventory, search methodology, coverage
      sources/                       # Individual source files (papers, datasets, code, ...)
    L1/
      source_basis.md                # What the sources actually say
      question_contract.md           # The bounded question
      convention_snapshot.md         # Notation and assumptions locked in
    L3/
      ideation/active_idea.md
      planning/active_plan.md
      analysis/active_analysis.md
      result_integration/active_integration.md
      distillation/active_distillation.md
      candidates/                    # Claims awaiting validation
      tex/flow_notebook.tex          # Derivation trail
    L4/
      validation_contract.md         # What we're checking and how
      reviews/                       # Pass / fail / contradiction
    L5_writing/
      outline.md, provenance/, draft/
    runtime/                         # Execution state (auto-managed)
```

## Design principles

- **Evidence before confidence.** The AI doesn't get to act like it knows something until it has shown the work.
- **Bounded questions, not open-ended exploration.** Every topic has a contract: a specific question, a scope, and a plan for knowing when you're done.
- **Humans own trust.** The promotion gate exists because "the AI seems confident" is not a valid reason to trust a result.
- **Durable by default.** Research state lives in your filesystem, not in a chat session. Close your laptop. Come back in a week. It's all still there.
- **Agent-agnostic.** The protocol is defined by the MCP tools and the Markdown artifacts. Any agent that speaks MCP can drive it.

## License

MIT License — see [LICENSE](LICENSE).

## Documentation

| Document | Description |
|----------|-------------|
| [brain/PROTOCOL.md](brain/PROTOCOL.md) | The operating manual your AI reads |
| [docs/AITP_SPEC.md](docs/AITP_SPEC.md) | Formal protocol specification |
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | 5-minute quickstart |
| [docs/INSTALL.md](docs/INSTALL.md) | Consolidated install guide |
| [docs/CHARTER.md](docs/CHARTER.md) | Project charter and principles |
| [docs/roadmap.md](docs/roadmap.md) | Development roadmap |
| [docs/design-principles.md](docs/design-principles.md) | Design principles |
