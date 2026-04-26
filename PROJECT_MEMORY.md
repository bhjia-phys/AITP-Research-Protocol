# AITP Research Protocol — Project Memory

This repository implements the AITP (AI Theoretical Physics) research protocol as a
FastMCP-based MCP server. It provides tools for AI coding agents to conduct
structured theoretical physics research with formal validation.

## Architecture

- `brain/mcp_server.py` — Main MCP server. ~49 @mcp.tool() functions implement the
  AITP protocol (L0-L5 layers). Uses FastMCP + PyYAML with file-based persistence
  (Markdown + YAML frontmatter).
- `brain/state_model.py` — Gate evaluation logic, artifact templates, stage
  definitions (L0, L1, L3, L4, L5), required frontmatter fields, and heading
  contracts. Also defines the knowledge graph types (nodes, edges, towers) and
  the domain skill registry (`DOMAIN_SKILL_REGISTRY`, `resolve_domain_prerequisites`).
- `skills/` — Stage-specific skill Markdown files loaded by agents, plus domain
  skills (e.g., `skill-librpa.md`) that are injected as prerequisites by the
  execution brief when the topic matches a domain pattern.
- `schemas/` — JSON Schema definitions for protocol objects.
- `contracts/` — Protocol contract definitions.
- `adapters/` — Platform-specific adapters (OpenClaw, Codex).
- `templates/` — File templates for topics and artifacts.

## Domain Skill System

The execution brief includes a `domain_prerequisites` field. When a topic slug
matches patterns in `DOMAIN_SKILL_REGISTRY` (in `state_model.py`), the
corresponding domain skill is listed. The agent must load domain skills BEFORE
the stage skill. Domain skills encode domain-specific conventions, invariants,
routing, and validation requirements.

Current domains:
- `abacus-librpa` — triggered by slug patterns: `librpa`, `crpa`, `scrpa`, `qsgw`,
  `gw-topology`. Loads `skill-librpa.md` with oh-my-LibRPA conventions.

## Key Conventions

- **Topic storage**: All state is Markdown files with YAML frontmatter. No JSON
  databases, no SQL.
- **Topics root**: Set via `AITP_TOPICS_ROOT` env var. Each topic is a directory
  with `state.md` as the entry point.
- **Gate model**: Each stage (L0, L1, L3, L4, L5) has required artifacts with
  required frontmatter fields and required Markdown headings. Missing any = blocked.
- **Tool return types**: Tools return `dict` or `_GateResult` (dict subclass).
  `_GateResult.__str__` returns its message for human display.
- **Popup gates**: Tools that require human decisions return popup_gate dicts for
  the agent to render as user prompts.

## Development

- Install: `pip install fastmcp pyyaml`
- Run: `python brain/mcp_server.py`
- Test: `pytest tests/`
- The MCP server is configured in each workspace's `.mcp.json`

## Protocol Layer Map

| Layer | Purpose | Key Tools |
|-------|---------|-----------|
| L0 | Source discovery & ingestion | `register_source`, `list_sources`, `ingest_knowledge` |
| L1 | Reading & framing | (artifacts filled by agent) |
| L2 | Cross-topic knowledge graph | `create_l2_node`, `create_l2_edge`, `promote_candidate` |
| L3 | Derivation campaign | `advance_to_l3`, `advance_l3_subplane`, `submit_candidate` |
| L4 | Validation | `create_validation_contract`, `submit_l4_review`, research loop |
| L5 | Writing | `advance_to_l5`, `return_from_l5` |
| Cross | Health & navigation | `health_check`, `list_topics`, `get_status`, `get_execution_brief` |

## Operator Rule

- Treat this repository as protocol-first.
- Python may materialize state, run audits, and execute explicit handlers.
- Research judgment should remain visible in durable artifacts rather than hidden
  heuristics.
