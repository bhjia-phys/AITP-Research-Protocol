# 5-Minute Quickstart

From "AITP is installed" to "AITP handled a real topic."

## 1. Verify the install

```bash
aitp doctor
```

All checks should pass: Python, dependencies, repo files, topics root,
Claude Code hooks/skills/MCP.

If anything is missing, run:

```bash
python scripts/aitp-pm.py install
```

from the AITP repo.

## 2. Start your first research topic

Open your AI agent (Claude Code, Kimi Code, etc.) and tell it what you want
to study in plain language. The `using-aitp` skill loads automatically and
routes your request into the protocol.

Example:

> "I want to understand the GW approximation. Start by checking what's already
> known in the knowledge graph, then find the key papers."

The agent will:

1. Call `aitp_query_l2_index` to check existing knowledge
2. Call `aitp_bootstrap_topic` to create the topic structure
3. Walk through the stages guided by `aitp_get_execution_brief`

## 3. The research flow

The agent follows the protocol stages automatically:

- **L0** — Searches for and registers sources (papers, datasets, code)
- **L1** — Reads each source (TOC-first), extracts concepts and equations, frames a bounded question
- **L3** — Derives, traces derivations, audits gaps, connects ideas
- **L4** — Validates claims with dimensional analysis, symmetry checks, limiting cases
- **L2** — Promotes validated results into the persistent knowledge graph

At any point you can ask:

> "What's the status?"

The agent calls `aitp_get_execution_brief` and tells you the current stage,
what's blocking, and what comes next.

## 4. Resume later

Just open the topic again and say:

> "Continue this topic."

State is stored in plain Markdown files — no database, no session dependency.
The agent calls `aitp_session_resume` to restore context.

## 5. Check what you've built

Your research accumulates in the L2 knowledge graph. Ask:

> "Show me what's in the L2 knowledge graph."

The agent calls `aitp_query_l2_index` for the domain taxonomy and
`aitp_query_l2_graph` for specific nodes.

## Agent notes

- **Claude Code**: Preferred UX is SessionStart bootstrap. The `using-aitp`
  skill loads automatically. Natural-language theory requests enter AITP
  before substantive work.
- **Kimi Code**: Same pattern — `using-aitp` skill routes theory requests.
- **Claude Code / Kimi Code**: Use `aitp install --agent <name>`.
  See agent-specific install docs for details.

## Windows note

If `aitp` is not on PATH, use the repo-local launcher:

```cmd
python scripts\aitp-pm.py doctor
python scripts\aitp-pm.py install
```
