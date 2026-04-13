---
gsd_state_version: 1.0
milestone: v2.2
milestone_name: Fresh-Topic First-Use Reliability
status: milestone_active
stopped_at: "Phase 176 complete; Phase 176.1 next"
last_updated: "2026-04-14T05:14:24+08:00"
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 3
  completed_plans: 1
---

# Project State

## Current Position

Status: milestone `v2.2` `Fresh-Topic First-Use Reliability` is active. The
next step is restoring honest fresh-topic public-entry behavior before broader
real-topic replay widens again.

**Why this milestone exists:**

`v2.1` closed the bounded `L2` hardening slice for fresh-topic multi-paper
intake, but the same real-topic measurement-induced / observer-algebra run also
showed that the front door can still misroute an explicit new-topic request and
that Windows first-source registration can fail or leave status surfaces stale.

The next bounded step is therefore to repair first-use reliability before
claiming that broader real-topic natural-language replay is trustworthy across
all layers again.

## Immediate Next Step

- active milestone: `v2.2` `Fresh-Topic First-Use Reliability`
- latest closed milestone: `v2.1` `L2 Real-Topic Relevance Hardening`
- previous closed milestone: `v2.0` `Three-Lane Real-Topic Natural-Language E2E`
- older closed milestone: `v1.99` `LibRPA QSGW Positive L0 To L2 Closure`
- `v2.1` proved the bounded fresh-topic `L2` staging and consultation
  hardening slice on a replayable multi-paper lane
- Phase `176` now closes the fresh-topic `session-start` misrouting regression
  for bounded "from scratch" requests
- the remaining first-use blocker is Windows source registration and status
  coherence after successful registration
- immediate next step: start Phase `176.1`

## Accumulated Context

### Pending Todos

- 3 pending todos captured on 2026-04-13:
  `fix-new-topic-session-start-misrouting`,
  `shorten-windows-source-layer-paths-and-sync-status`,
  `harden-l2-staging-provenance-and-retrieval-relevance`
- `harden-l2-staging-provenance-and-retrieval-relevance` is now effectively
  closed by `v2.1`, but the todo parking lot has not been cleaned yet

### 5-Axis Advancement Framework (2026-04-13)

**Canonical reference**: `.planning/AXIS_TAXONOMY.md` — contains axis
definitions, intent-signal keywords, decision tree, and complete
backlog-to-axis mapping (999.1–999.86 + all ROADMAP phases). GSD agents
MUST consult this file when classifying new work.

All future AITP work is organized along five axes:

1. **Layer-Internal Optimization** — improve each layer's capability (L0 PDF
   parsing, L1 LLM extraction, L2 population, Human HCI)

2. **Inter-Layer Connection Optimization** — optimize paths between layers
   (L0→L1, L1→L2 fast path, L3→L4, L4→L2, L5←L2)

3. **Layer-Internal Data Recording** — schema evolution, JSONL metrics,
   manifest-as-truth-source

4. **Global Infrastructure** — protocol skeleton, human experience, execution
   strategy (mode dispatch, loop detection)

5. **AI Agent Integration** — agent governance (schema isolation, context
   injection) and agent interface (natural-language steering, MCP routing)

Priority sequence: Axis 4 (human experience) → Axis 5 (agent governance) →
Axis 1 (layer capability) → Axis 2 (inter-layer) → Axis 3 (data recording,
cross-cutting).

### Roadmap Evolution

- `v1.91` is now archived after proving one honest real-topic public-front-door
  run and converting its remaining friction into routed follow-up work

- Phase `166` is promoted into the new active milestone `v1.92`
- `v1.92` stays narrow: concrete `L0` source handoff first, contentful arXiv
  registration second

- `v1.93` now promotes the broader contradiction-adjudication remainder from
  `L1` intake maturity into one bounded milestone

- `v1.94` now promotes the broader post-baseline analytical-validation
  remainder into one bounded milestone

- `v1.95` now closes the L4→L2 promotion pipeline gap discovered during Jones
  E2E testing — the pipeline's engineering (not the science) is what failed

- `v1.96` now promotes the deferred full-proof remainder from `v1.95`: one
  three-mode front-door bootstrap proof plus one honest negative-result L2
  proof

- `v1.97` now narrows back down to the first real positive authoritative L2
  landing so L2 itself becomes trustworthy before broader multi-mode closure

- `v2.1` now closes the bounded fresh-topic `L2` hardening slice: clean staged
  rows, correct per-entry provenance, and one replayable multi-paper relevance
  proof

- `v2.2` now promotes the remaining fresh-topic front-door regressions from the
  same real-topic run: new-topic `session-start` routing plus Windows
  first-source registration and status coherence

- Phase `171` now proves one fresh formal-theory theorem can land in
  authoritative canonical `L2` with repo-local compile and `consult-l2`
  parity; the next gap is coexistence with the negative-result route

- Phase `171.1` now proves the positive theorem row and a staged
  `negative_result -> contradiction_watch` row coexist honestly on the same
  compiled and consultation surfaces

- Comprehensive HCI gap analysis (2026-04-13) identified 30 issues across 6
  tiers; all captured as 999.60–999.70 in BACKLOG.md

- wow-harness comparison (2026-04-13) identified 6 borrowable patterns; all
  captured as 999.73–999.78 in BACKLOG.md

### Protected Closed Scope

- keep the shipped route-transition and adoption surfaces closed unless a fresh
  regression appears

- use the current public entry surfaces first instead of bypassing them with
  seeded hidden artifacts

- do not assume GSD will auto-discover arbitrary issues from runtime artifacts
  alone; capture them explicitly during the milestone

### Mode Envelope Context

- `docs/AITP_MODE_ENVELOPE_PROTOCOL.md` defines the 4 modes (discussion,
  explore, verify, promote) with draft working doctrine status

- `mode_envelope_support.py` already has mode specs, auto-selection, and
  markdown rendering

- The gap: runtime bundle generation does not actually vary context loading
  by mode, and there is no lightweight literature-intake fast path

- Phase 165.2 addresses both gaps after Phase 165 validates real-topic friction

### wow-harness Reference

- wow-harness (https://github.com/NatureBlueee/wow-harness) governs AI coding
  agents through mechanical hooks rather than prompt instructions

- Core insight: "CLAUDE.md instruction compliance: ~20% / Hook enforcement:
  100%" — mechanical constraints beat prompt constraints

- Key borrowable patterns: mechanical-first verification, context injection
  with dedup, schema-level agent isolation, JSONL self-evolution, loop
  detection, manifest-as-truth-source

- See BACKLOG.md Tier 5 (999.73–999.78) for details

### DeepXiv SDK + Graphify Integration (2026-04-14)

**DeepXiv SDK** (MIT, v0.2.4): Cloud API client for progressive arXiv reading.
Key borrowable patterns: 5-level reading chain (brief→head→section→preview→raw),
`PaperInfo` TypedDict schema, token-budget-aware agent mode (LangGraph ReAct),
section fuzzy matching, exponential backoff retry. Currently integrated as
shallow `subprocess.run("deepxiv search ...")` fallback — only search, no
brief/head/section/TLDR. What's cloud-only: search index, trending signals, all
paper parsing. What's borrowable locally: progressive reading paradigm, schema,
token-budget pattern, exception hierarchy, retry logic.

**Graphify** (MIT, v0.4.5): Local Python library for knowledge graph construction.
Key borrowable patterns: LLM extraction prompt with 3-tier confidence
(EXTRACTED/INFERRED/AMBIGUOUS) + numeric scores, 3-layer dedup (exact→fuzzy→LLM),
Leiden community detection, `analyze.py` functions (god_nodes,
surprising_connections, suggest_questions, graph_diff), hyperedge support, SHA256
caching, Obsidian export, PDF text extraction. What needs adaptation for physics:
add physics-specific relation/node types, extraction targets (assumptions,
validity regimes, notation conventions).

**Integration architecture:**

```
register_arxiv_source.py → enrich_with_deepxiv.py → build_concept_graph.py → L1
```

Phase 165.5 covers this with 3 plans and 7 backlog items (999.79–999.85).
Depends on Phase 165.2 (mode-aware runtime) for progressive reading integration.

### Public Front Door Closure (2026-04-13)

- `.planning/phases/165.6/evidence/jones-von-neumann-algebras-public-entry/`
  now proves one real topic entered through the public front door with a fresh
  slug

- the bounded result was an honest return to `L0 source expansion`, not a fake
  theorem-facing success claim

- one remaining non-blocking HCI debt from that run is routed to `BACKLOG 999.86`
