# Phase 143: L0 Source Discovery Via DeepXiv MCP Integration

## Status

pending

## Goal

Close the pre-registration discovery gap in L0 by integrating DeepXiv SDK
as an MCP-based search tool, enabling the "idea → search → evaluate →
register" workflow that currently does not exist.

## Background

L0 source registration (`register_arxiv_source.py`) requires an explicit
arxiv_id. There is no search or discovery step. `L0_SOURCE_LAYER.md`
design mentions "source search expansion" but this remains unimplemented.

The entire knowledge-hub Python codebase contains zero search
implementations. Registration is always identifier-based, never search-based.

## Requirements

- DeepXiv SDK (`pip install "deepxiv-sdk[mcp]"`) wired as MCP server for
  agent runtimes (OpenCode, OpenClaw)
- Hybrid BM25+vector search over arXiv metadata with configurable weights,
  category/author/date/citation filters, and pagination
- Search results return arxiv_id, title, abstract, categories, citation
  count, and relevance score — sufficient for candidate evaluation
- Thin adapter script (`source-layer/scripts/discover_and_register.py`) that
  bridges search results into existing `register_arxiv_source.py`
- Discovery flow documented in `L0_SOURCE_LAYER.md` as recommended
  pre-registration path
- Search-tool-agnostic design: DeepXiv as primary, Semantic Scholar
  MCP and arXiv API as documented fallbacks
- Must NOT embed DeepXiv into L0 core code — external MCP dependency only
- Progressive reading: agent can request brief/head/section of candidates
  before committing to full registration
- Token/rate-limit documentation (anonymous: 1000/day, registered: 10000/day)

## Depends On

Phase 140 (v1.68 closure must complete first)

## Deliverables

1. DeepXiv MCP server configuration for OpenCode and OpenClaw
2. `source-layer/scripts/discover_and_register.py` adapter script
3. Updated `L0_SOURCE_LAYER.md` with discovery workflow documentation
4. Fallback chain documentation (DeepXiv → Semantic Scholar → arXiv API)

## Plans

- [ ] TBD (run /gsd:plan-phase 143 to break down)
