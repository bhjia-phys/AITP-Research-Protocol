# Phase 143: L0 Source Discovery Via DeepXiv MCP Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md.

**Date:** 2026-04-12
**Phase:** 143-l0-source-discovery-via-deepxiv-mcp
**Areas discussed:** discovery gap, adapter boundary, fallback chain

---

## Search Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| external MCP-backed search provider | keeps L0 protocol-first and dependency-light | ✓ |
| embed DeepXiv logic inside L0 core code | would overcouple protocol state to one service | |

## Registration Bridge

| Option | Description | Selected |
|--------|-------------|----------|
| thin adapter into `register_arxiv_source.py` | reuses existing registration truth path | ✓ |
| replace the existing registration helper | unnecessary churn and greater regression risk | |

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| bounded search -> evaluate -> register path | matches the actual missing feature | ✓ |
| broad literature automation and topic scouting | too wide for the immediate L0 gap | |
