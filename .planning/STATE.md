---
gsd_state_version: 1.0
milestone: v2.9
milestone_name: Promotion-Review Gate Closure
status: milestone_active
stopped_at: "All v2.9 phases executed; milestone audit / archive next"
last_updated: "2026-04-14T09:21:35+08:00"
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 3
  completed_plans: 3
---

# Project State

## Current Position

Status: milestone `v2.9` `Promotion-Review Gate Closure` is active.
All planned phases are now executed and verified. Milestone audit / archive is next.

**Why this milestone exists:**

`v2.8` closed selected-candidate route choice and proved the same fresh topic
can already advance beyond candidate-summary placeholder into a first deeper
route. A follow-up probe still showed one remaining bounded route gap: once
`l2_promotion_review` becomes the selected route, the loop still cannot
materialize the first explicit promotion-review gate from that route.

That bounded promotion-review gate step is now closed at the execution level.
The next procedural step is milestone audit / archive before promoting the next
bounded gap.

## Immediate Next Step

- active milestone: `v2.9` `Promotion-Review Gate Closure`
- latest closed milestone: `v2.8` `Selected-Candidate Route Choice Closure`
- previous closed milestone: `v2.7` `Consultation-Followup Selection Closure`
- older closed milestone: `v2.6` `Staged-L2 Post-Review Advancement`
- `v2.8` proved the same fresh topic can derive one first deeper route choice
  from the selected staged candidate
- a follow-up probe still left `l2_promotion_review` visible but
  non-executable inside the bounded loop
- Phase `183` materialized one explicit promotion-review gate from the selected
  staged candidate
- Phase `183.1` aligned public surfaces on that gate while keeping the route
  choice note as supporting evidence
- Phase `183.2` closed the milestone with one replayable sixth-continue proof
- immediate next step: audit / archive milestone `v2.9`

## Accumulated Context

### Pending Todos

- 4 pending todos captured on 2026-04-13:
  `fix-new-topic-session-start-misrouting`,
  `shorten-windows-source-layer-paths-and-sync-status`,
  `harden-l2-staging-provenance-and-retrieval-relevance`,
  `force-l4-execution-after-l3-planning`
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
- `v2.4` now promotes the next bounded gap from the repaired `v2.3` route: the
  first fresh-topic L1->L2 follow-through must land once, advance to staged-L2
  review, and become mechanically replayable
- `v2.5` now promotes the remaining bounded follow-through friction from the
  `v2.4` replay: benign continue steering still leaves a misleading
  human-control posture during staged-L2 review reentry
- `v2.6` now promotes the next bounded gap from the repaired `v2.5` reentry
  baseline: after staged-L2 review becomes stable, a later `continue` must
  advance onto one bounded post-review consultation step instead of stalling
  on the same review summary
- `v2.7` now promotes the next bounded gap from the repaired `v2.6`
  consultation baseline: once consultation-followup becomes the selected route,
  the loop must execute it, record a durable selection artifact, and advance to
  one selected staged candidate instead of remaining on generic consult
  language
- `v2.8` now promotes the next bounded gap from the repaired `v2.7`
  selection baseline: once a selected staged candidate becomes the selected
  route, the loop must derive one bounded deeper route choice instead of
  stalling on the candidate summary
- `v2.9` now promotes the next bounded gap from the repaired `v2.8`
  route-choice baseline: once `l2_promotion_review` becomes the selected route,
  the loop must materialize one explicit promotion-review gate instead of
  stalling on the summary
- `v2.8` now promotes the next bounded gap from the repaired `v2.7`
  selection baseline: once a selected staged candidate becomes the selected
  route, the loop must derive one bounded deeper route choice instead of
  stalling on the candidate summary
