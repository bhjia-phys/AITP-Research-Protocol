---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: Post-Registration Route Coherence
status: milestone_active
stopped_at: "Phase 177.2 complete; milestone lifecycle next"
last_updated: "2026-04-14T05:33:01+08:00"
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 3
  completed_plans: 3
---

# Project State

## Current Position

Status: milestone `v2.3` `Post-Registration Route Coherence` is active. The
next step is making the first post-registration route transition honest before
broader real-topic replay widens again.

**Why this milestone exists:**

`v2.2` closed the bounded first-use reliability slice through fresh-topic
routing, Windows-safe registration, and immediate source-count visibility, but
the same first-use replay still leaves one remaining operator-visible gap:
post-registration next-action surfaces can keep pointing back to the old L0
source-handoff wording even after a source already exists.

The next bounded step is therefore to make the first post-registration route
transition coherent before claiming that broader real-topic replay is honest
across all layers again.

## Immediate Next Step

- active milestone: `v2.3` `Post-Registration Route Coherence`
- latest closed milestone: `v2.2` `Fresh-Topic First-Use Reliability`
- previous closed milestone: `v2.1` `L2 Real-Topic Relevance Hardening`
- older closed milestone: `v2.0` `Three-Lane Real-Topic Natural-Language E2E`
- `v2.2` proved the first-use route through new-topic entry, Windows-safe
  registration, and immediate post-registration source visibility
- Phase `177` now closes persisted runtime-state coherence after registration
- Phase `177.1` now closes stale post-registration next-action selection
- Phase `177.2` now closes the replayable bounded proof of that transition
- immediate next step: audit and archive milestone `v2.3`

## Accumulated Context

### Pending Todos

- 3 pending todos captured on 2026-04-13:
  `fix-new-topic-session-start-misrouting`,
  `shorten-windows-source-layer-paths-and-sync-status`,
  `harden-l2-staging-provenance-and-retrieval-relevance`
- `harden-l2-staging-provenance-and-retrieval-relevance` is now effectively
  closed by `v2.1`, but the todo parking lot has not been cleaned yet
- `fix-new-topic-session-start-misrouting` and
  `shorten-windows-source-layer-paths-and-sync-status` are now effectively
  closed by `v2.2`, but the todo parking lot has not been cleaned yet

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

- `v2.2` now closes the bounded first-use reliability slice: new-topic
  `session-start` routing, Windows-safe first-source registration, and one
  replayable first-use proof with immediate source visibility

- `v2.3` now promotes the remaining bounded first-use gap from that same
  replay: post-registration route and next-action coherence
