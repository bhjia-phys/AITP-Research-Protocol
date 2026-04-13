---
gsd_state_version: 1.0
milestone: v1.99
milestone_name: LibRPA QSGW Positive L0 To L2 Closure
status: milestone_complete
last_updated: "2026-04-14T04:20:00+08:00"
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 3
  completed_plans: 3
---

# Project State

## Current Position

Status: milestone `v1.99` `LibRPA QSGW Positive L0 To L2 Closure` is complete
and archived. The next step is opening the broad three-lane real-topic testing
milestone.

**Why this milestone exists:**

`v1.96` proved the public front door and negative-result route honestly, but it
did **not** land any positive authoritative unit in canonical `L2`. That means
AITP still lacks one fresh positive proof that the current public route can
actually finish in trusted L2 knowledge.

The next bounded step is therefore to close the **most mature** positive lane
first, and use that real landing to harden the L2 compiler, consultation, and
retrieval surfaces before widening back out to more modes and topic paradigms.

## Immediate Next Step

- latest closed milestone: `v1.99` `LibRPA QSGW Positive L0 To L2 Closure`
- previous closed milestone: `v1.98` `Toy Model Positive L0 To L2 Closure`
- older closed milestone: `v1.97` `First Positive L0 To L2 Closure`
- Phase `173` chose one bounded positive `LibRPA QSGW` target:
  the deterministic-reduction thread-consistency core on the
  `H2O/really_tight iter=10` reference workflow

- Phase `173.1` promoted that bounded target into authoritative canonical `L2`
  as `claim:librpa-qsgw-deterministic-reduction-consistency-core`

- Phase `173.2` replayed the positive `LibRPA QSGW` proof and made the
  three-lane convergence baseline explicit

- immediate next step: start the three-lane real-topic natural-language
  dialogue milestone

## Accumulated Context

### Pending Todos

- 3 pending todos captured on 2026-04-13:
  `fix-new-topic-session-start-misrouting`,
  `shorten-windows-source-layer-paths-and-sync-status`,
  `harden-l2-staging-provenance-and-retrieval-relevance`

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
