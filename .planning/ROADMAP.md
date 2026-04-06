# Roadmap: AITP Runtime And Knowledge Foundations

## Milestones

- ✅ **v1.26 Interaction-Surface And Chat-Routing Boundary Extraction And Closure** — Phases 87-89 (shipped 2026-04-07)
- ✅ **v1.25 Contract-Aware Checkpoint/Append Closure And Loop-Execution Boundary Extraction** — Phases 84-86 (shipped 2026-04-07)
- ✅ **v1.24 Source Distillation Boundary Extraction And Closure** — Phases 81-83 (shipped 2026-04-07)
- ✅ **v1.23 Topic-Skill Projection Boundary Extraction And Closure** — Phases 78-80 (shipped 2026-04-07)
- ✅ **v1.22 Theory-Coverage Audit Boundary Extraction And Closure** — Phases 75-77 (shipped 2026-04-07)
- ✅ **v1.21 Lean-Bridge Materialization Boundary Extraction And Closure** — Phases 72-74 (shipped 2026-04-07)
- ✅ **v1.20 Candidate Promotion Boundary Extraction And Closure** — Phases 69-71 (shipped 2026-04-07)
- ✅ **v1.19 Formal-Theory Audit Boundary Extraction And Closure** — Phases 66-68 (shipped 2026-04-07)
- ✅ **v1.18 Declarative Append Policy Closure And Promotion-Gate Boundary Seed** — Phases 63-65 (shipped 2026-04-07)
- ✅ **v1.17 Checkpoint-Aware Queue Shaping And Auto-Promotion Extraction** — Phases 60-62 (shipped 2026-04-07)
- ✅ **v1.16 Contract-Aware Queue Shaping Seed** — Phases 57-59 (shipped 2026-04-07)
- ✅ **v1.15 Queue Materialization And Auto-Action Boundary Extraction** — Phases 53-56 (shipped 2026-04-07)
- ✅ **v1.14 Mode-Aware Queue And Decision Routing Seed** — Phases 50-52 (shipped 2026-04-06)
- ✅ **v1.13 Transition-Aware Auto-Handler Routing Seed** — Phases 47-49 (shipped 2026-04-06)
- ✅ **v1.12 Runtime Mode And Transition Contract Seed** — Phases 44-46 (shipped 2026-04-06)
- ✅ **v1.11 Ontology, Mode, And Context-Policy Formalization** — Phases 41-43 (shipped 2026-04-06)
- ✅ **v1.10 Followup And Closed-Loop Decomposition** — Phases 39-40 (shipped 2026-04-05)
- ✅ **v1.9 Topic Shell Assembly Decomposition** — Phases 37-38 (shipped 2026-04-05)
- ✅ **v1.8 Continued Kernel Decomposition** — Phases 34-36 (shipped 2026-04-05)
- ✅ **v1.7 Kernel Decomposition And Maintainability Guard** — Phases 30-33 (shipped 2026-04-05)
- ✅ **v1.6 Runtime Front-Door Parity Hardening** — Phases 25-29 (shipped 2026-04-05)
- ✅ **v1.5 L2 Knowledge Compiler And Hygiene** — Phases 20-24 (shipped 2026-04-05)
- ✅ **v1.4 Runtime Simplification And Reuse Foundations** — Phases 15-19 (shipped 2026-04-04)
- ✅ **v1.3 Multi-Topic Parallel Execution** — Phases 10-14 (shipped 2026-04-04)
- ✅ **v1.2 Projection-First Formal-Theory Seed** — Phases 06-09 (shipped 2026-04-01)
- ✅ **v1.1 L2 Topic-Skill Projection** — retrospective ship capture in commit `6445c59` (shipped 2026-04-01)
- ✅ **v1.0 Runtime Hardening** — Phases 1-5 (shipped 2026-03-31)

## Overview

`v1.26` is now shipped.

It extracted the operator-facing interaction-surface synthesis out of
`orchestrate_topic.py` and the chat-routing/session-start cluster out of
`aitp_service.py` while keeping the public service methods stable.

What shipped in `v1.26`:

1. Move interaction-state assembly plus operator-console and agent-brief
   rendering into `runtime/scripts/interaction_surface_support.py`.
2. Keep `orchestrate_topic.py` as a thin coordinator over the extracted
   interaction-surface boundary.
3. Move chat routing, management-route handling, and session-start
   orchestration into `knowledge_hub/chat_session_support.py`.
4. Keep `AITPService.route_codex_chat_request()` and
   `AITPService.start_chat_session()` as thin stable façades.
5. Close the milestone with targeted runtime-script/service regressions and
   maintainability lock.

No post-`v1.26` milestone is active yet. The clearest next targets are:

- the next runtime hotspot such as `sync_topic_state.py` or `closed_loop_v1.py`
- or the next coherent `aitp_service.py` hotspot extraction such as
  capability audit or steering payloads

## Phases

- [x] **Phase 87: Interaction-Surface Boundary Extraction** - Move the shared
  interaction-state and operator-surface synthesis out of `orchestrate_topic.py`
  into a dedicated support module.
- [x] **Phase 88: Chat-Routing Boundary Extraction** - Move the shared Codex
  chat-routing and session-start orchestration out of `aitp_service.py` into a
  dedicated support module.
- [x] **Phase 89: Docs, Regression, And Maintainability Lock** - Close the
  milestone with docs updates, targeted regressions, and maintainability coverage.

## Phase Details

### Phase 87: Interaction-Surface Boundary Extraction
**Goal**: Move the shared interaction-state and operator-surface synthesis out
of the runtime orchestrator while keeping runtime artifacts stable.
**Depends on**: `v1.25` shipped baseline
**Requirements**: [POL-18]
**Success Criteria** (what must be TRUE):
  1. Shared interaction-surface helpers live in a dedicated support module.
  2. `orchestrate_topic.py` keeps operator/runtime surfaces stable behind thin wrappers.
**Plans**: 1 plan

Plans:
- [x] 87-01: Extract the interaction-surface boundary into a support module.

### Phase 88: Chat-Routing Boundary Extraction
**Goal**: Move the shared chat-routing and session-start orchestration out of
the main service façade without changing the public service methods.
**Depends on**: Phase 87
**Requirements**: [MTN-22]
**Success Criteria** (what must be TRUE):
  1. Shared chat-routing/session-start helpers live in a dedicated support module.
  2. `AITPService.route_codex_chat_request()` and `AITPService.start_chat_session()` remain stable façades.
**Plans**: 1 plan

Plans:
- [x] 88-01: Extract the chat-routing boundary into a support module.

### Phase 89: Docs, Regression, And Maintainability Lock
**Goal**: Close `v1.26` with docs, regression, and maintainability lock.
**Depends on**: Phase 88
**Requirements**: [DOC-26]
**Success Criteria** (what must be TRUE):
  1. The targeted runtime-script/service suite passes.
  2. Maintainability budgets remain green.
  3. Docs mention the new helper boundaries and interaction/chat-routing behavior.
**Plans**: 1 plan

Plans:
- [x] 89-01: Run targeted regression and close `v1.26`.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 87. Interaction-Surface Boundary Extraction | 1/1 | Complete | 2026-04-07 |
| 88. Chat-Routing Boundary Extraction | 1/1 | Complete | 2026-04-07 |
| 89. Docs, Regression, And Maintainability Lock | 1/1 | Complete | 2026-04-07 |

## Backlog

### Phase 999.1: L5 Publication Factory (BACKLOG)
**Goal:** Add a final `L5` publication/output layer that turns a completed
topic into a paper-grade writing package without changing scientific truth.
**Requirements:** [PUB-01, PUB-02, PUB-03]
**Plans:** 0 plans

Plans:
- [ ] TBD (promote only when explicitly selected as a new milestone)

### Phase 999.2: Fix CLI Human-Readable Output (BACKLOG)
**Goal:** `_emit()` in `aitp_cli.py:22-26` always outputs JSON regardless of
`--json` flag. Implement human-readable plain-text output for the default
(non-JSON) path so users get actionable status summaries instead of raw JSON.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.3: Add End-to-End Integration Tests (BACKLOG)
**Goal:** No test exercises the full `aitp bootstrap → aitp loop → aitp status`
pipeline. Add at least one subprocess-based E2E test that creates a temp topic,
runs it through the CLI, and verifies real file outputs at each stage.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.4: Fix SessionStart Windows Silent Failure (BACKLOG)
**Goal:** `hooks/run-hook.cmd:25` silently exits with code 0 when bash is not
found on Windows. Print a warning so users know AITP session is not properly
initialized. The README claims Windows-native support but the Claude Code
SessionStart path has a hard bash dependency.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.5: Add Complete Demo Topic For Onboarding (BACKLOG)
**Goal:** No topic in the repository demonstrates the full L0→L1→L3→L4→L2
lifecycle through natural user interaction. Add a worked demo topic (with
transcript) that a new user can follow to understand the complete AITP workflow.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.6: Service God Class Cleanup (BACKLOG)
**Goal:** `aitp_service.py` is still 6,459 lines with ~400 methods. Many are
one-line delegation wrappers (e.g. `_load_followup_subtopic_rows` just calls
`load_followup_subtopic_rows(path)`). Remove the thin wrappers and let callers
use the extracted support modules directly.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.7: Decision Script Quality Fixes (BACKLOG)
**Goal:** (1) `decide_next_action.py:392-414` has hardcoded scoring magic
numbers (+1000, +250, +20, etc.) with no calibration docs. (2)
`policy_ranked_pending` is defined twice (lines 384 and 479), the first is dead
code. Add scoring rationale docs and remove the duplicate function.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.8: Schema And Contract Consistency (BACKLOG)
**Goal:** (1) `contracts/promotion-or-reject.md` declares `follow_up_actions` as
required but `schemas/promotion-or-reject.schema.json` omits it (with
`additionalProperties: false`). (2) Root-level `schemas/` and kernel-internal
`research/knowledge-hub/schemas/` are separate uncross-validated schema sets.
Fix the schema gap and document the relationship between the two schema trees.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.9: Documentation Fixes (BACKLOG)
**Goal:** (1) `README.md:706` links to nonexistent `docs/roadmap.md`. (2) Quick
Start does not mention Python 3.10+ requirement. (3) Install docs are scattered
across 8+ files with no single entry point. Fix the broken link, add version
requirement, and consider consolidating install guidance.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.10: Dependency Pinning (BACKLOG)
**Goal:** `requirements.txt` has `mcp>=1.0.0` and `jsonschema>=4.0.0` with no
upper bounds. A breaking upstream change could silently break the runtime. Pin
compatible upper bounds or use a lockfile for reproducibility.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.11: User Experience Friction Reduction (BACKLOG)
**Goal:** (1) Each topic produces 20+ state files; `current_topic.json` has empty
`human_request` and provides no useful summary. (2) `_run()` in
`aitp_service.py:322-327` loses subprocess exit codes in RuntimeError. (3)
`.planning/` directory (26+ phase dirs) adds cognitive noise for users. (4)
Windows path leak in haldane-shastry topic `control_note_path`.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.12: Test Suite Quality Improvement (BACKLOG)
**Goal:** (1) ~40 test functions across 4 files are pure structural checks that
pass even if service code is broken — segregate into integrity tests. (2) No
`conftest.py`; 3+ files duplicate identical `_bootstrap_path()` and temp-dir
setup. (3) CLI tests use `MagicMock` for all service calls — upgrade critical
paths to use real service methods.
**Source:** User-perspective audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

---

## L2 Knowledge Graph Evolution (conceptual audit 2026-04-07)

**Context:** Deep review of AITP from a theoretical physicist collaborator
perspective. The core finding is that AITP manages metadata about research
without doing research, and the L2 knowledge base (the "active research
memory") is completely empty despite an elaborate 22-type ontology and 11-type
edge schema. The following items capture the design changes needed to evolve
L2 from an empty filing cabinet into a knowledge graph that grows with each
research discussion.

**Design reference:** Inspired by math community practices (Lean, formal
knowledge graphs) but adapted for theoretical physics where physical intuition,
overlapping assumptions, and less systematic technique relationships require a
rougher but still auditable structure. Key principle: each node has keywords,
title, and summary; AI searches to find nodes then follows dependency edges to
gather all needed context — similar to how physicists find literature.

### Phase 999.13: Implement Graph Traversal And Search (BACKLOG)
**Goal:** The L2 knowledge graph has 11 typed edge relations defined in
`edge.schema.json` and retrieval profiles with `edge_expansion` fields, but
zero graph traversal code exists. `edges.jsonl` is empty. The
`l2_compiler.py` only does tag grouping, no graph expansion. Implement:
(1) A `graph_expand(node_id, edge_types, max_depth)` function (~50-80 lines)
supporting BFS along dependency edges. (2) Integration with L2 consultation so
that a search hit on a concept node automatically expands its `depends_on`,
`uses_method`, and `warned_by` neighbors. (3) Token-budget-aware expansion that
returns index-level summaries first, full payloads only on explicit AI request.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.14: Add Physical Picture Object Type (BACKLOG)
**Goal:** Theoretical physics has "physical intuition/images" (物理图像) that
don't fit any of the existing 22 canonical types. A physicist's mental model
— flux attachment as composite fermions, Luttinger liquid picture, mean-field
decoupling channels — is neither a formal concept nor a theorem. Add a
`physical_picture` object type with payload fields: `picture_description`
(informal but precise physical image), `formal_analog` (link to theorem or
definition), `intuitive_arguments` (heuristic reasoning chain),
`known_limitations` (where the picture breaks down), `domain`,
`subdomain`. This bridges the gap between physical intuition (how physicists
actually think) and formal statements (what AITP currently stores).
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.15: Define MVP Type Subset For Knowledge Graph Seed (BACKLOG)
**Goal:** 22 object families are too heavy for starting a knowledge graph in
one direction. Define a minimal viable subset of 5-6 core types:
`concept` (atomic concepts), `theorem_card` (conclusions/theorems),
`method` (related techniques), `assumption_card` (physics assumptions),
`physical_picture` (physical intuition — see 999.14), `warning_note` (known
traps). Update `canonical-unit.schema.json` to mark the remaining types as
`extended` rather than `core`. Update retrieval profiles to prefer core types
by default. Ensure the full 22-type schema remains available for future
expansion.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.16: Add Lightweight Knowledge Entry Path (BACKLOG)
**Goal:** The current L3→L4→L2 promotion pipeline (14 gate checks) is too
heavy for recording a concept mentioned during a research discussion. Add a
lightweight entry path: (1) CLI command `aitp note-concept --title "..." --summary
"..." --tags "..." --type concept` that creates a staging entry without
requiring a topic context. (2) During topic discussions, AI auto-suggests
staging entries when it identifies recordable knowledge points. (3) Staging
entries are automatically discoverable by subsequent topic work. (4) Periodic
batch review of staging → promotion (e.g., per milestone). The existing
`l2_staging.py` provides the foundation; this item adds the lightweight CLI
and auto-suggestion integration.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.17: Implement Progressive Disclosure Retrieval For AI Context (BACKLOG)
**Goal:** AI should receive a knowledge index first (like skill indexes) and
expand details on demand, not load the entire knowledge base into context.
Implement a 3-step retrieval flow: (1) AI constructs query from
human_request + topic_context → calls L2 search (BM25 or keyword match). (2)
Returns index layer: per hit {id, title, summary(≤2 sentences), tags,
maturity}. AI selects relevant nodes. (3) AI requests expansion → returns full
payload + one-hop dependency edge summaries. Optional deep crawl with token
budget limit (~4000 tokens per knowledge packet). This connects the existing
`knowledge-packet.schema.json` design to actual runtime retrieval code.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.18: Seed First Direction Knowledge Graph (BACKLOG)
**Goal:** The L2 knowledge base is completely empty (0 canonical units, 0
edges). Before building more pipeline infrastructure, manually seed a real
knowledge graph for one small direction (e.g., Haldane-Shastry chaos
transition or quantum Hall effects). Steps: (1) Create 10-20 core concept
nodes using the MVP type subset (see 999.15). (2) Manually establish
dependency edges between them. (3) Implement basic search + one-hop graph
traversal (see 999.13). (4) Validate that AI can search → expand → crawl
edges to retrieve relevant knowledge. (5) Use this as the regression baseline
for all subsequent L2 infrastructure work. The principle: build data first,
then refine the pipeline around real data.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

---

## Conceptual Gaps — Scoped Backlog Items

These gaps were identified during the deep conceptual audit from a theoretical
physicist's perspective. Each has been refined into a concrete, actionable
backlog entry.

### Phase 999.19: Add Symbolic And Analytical Reasoning Path (BACKLOG)

**Goal:** `closed_loop_v1.py` (1801 lines) only validates numerical execution
(python scripts). Theoretical physics primarily advances through mathematical
derivation — limiting-case analysis, dimensional analysis, symmetry arguments,
perturbation expansions, proof sketches. Add: (1) A `symbolic_validation`
execution lane that accepts SymPy/Mathematica/sage scripts alongside Python.
(2) An `analytical_review` lane where the AI checks a derivation's internal
consistency (dimensional analysis of each step, limiting-case agreement,
cross-reference with known results in L2). (3) Update `lane` classification in
L1 distillation to recognize analytical vs numerical work. (4) Add validation
that a formal-theory candidate's proof sketch survives basic sanity checks
before promotion. Priority: HIGH — this is the single biggest capability gap.
**Source:** Conceptual audit 2026-04-07, L0-L4 layer audit
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.20: Add Research Judgment To Decision-Making (BACKLOG)

**Goal:** `decide_next_action.py` uses keyword substring matching and hardcoded
scoring magic numbers (lines 392-414) to select actions. A real collaborator
decides based on research momentum: "I'm making progress on this approach, keep
going" vs "I'm stuck after 3 attempts, switch strategy" vs "This surprising
result deserves deeper investigation." Add: (1) A `research_momentum` signal
derived from recent action outcomes (success/failure pattern, diminishing
returns detection). (2) A `stuck_detection` heuristic that triggers after N
failed attempts on the same sub-question and suggests pivoting. (3) A
`surprise_capture` mechanism that flags unexpected results for deeper
investigation rather than treating them as errors. (4) Replace keyword scoring
with a lightweight decision model that weights: progress velocity, blocking
dependency resolution, and novelty of findings. Priority: HIGH — directly
affects research quality.
**Source:** Conceptual audit 2026-04-07, code audit of decide_next_action.py
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.21: Make Layer Model Flexible For Real Research Iteration (BACKLOG)

**Goal:** The L0→L1→L3→L4→L2 pipeline with explicit prohibitions (e.g., no
L1→L4→L2 bypass) forces serialization of what is inherently parallel and
iterative. Real research flows: read paper (L0) → realize assumption is wrong
(L1) → check L2 knowledge → revise understanding → go back to paper → iterate.
The current model treats each layer as a state machine transition. Add: (1)
Explicit "iteration edges" — allow L4→L1 backedges when validation fails (not
just to L3). (2) Allow L1→L2 direct consultation during intake (not just
through formal topic work). (3) Model research as a graph with recommended
paths, not a linear pipeline with gates. (4) Keep the existing gates as
"promotion" checks (for L2 publication) while allowing exploratory loops that
don't require full gate passage. Priority: MEDIUM — current model works for
structured work but breaks for exploratory research.
**Source:** Conceptual audit 2026-04-07, L0-L4 layer audit
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.22: Model Creativity, Taste, And Physical Intuition (BACKLOG)

**Goal:** The CHARTER has 10 principles all about discipline and process. Nothing
about what makes a problem interesting, what makes an approach elegant, or when
to pursue a surprising result. This is the hardest gap to address technically,
but concrete steps: (1) Add a `physical_picture` object type (see 999.14) so
intuitive mental models are first-class knowledge. (2) Add a `research_taste`
profile to the operator model — preferred formalisms (path integral vs operator
vs canonical), preferred tools (analytic vs numerical vs diagrammatic), and
problem aesthetic (elegance of result vs breadth of applicability). (3) When
the AI encounters multiple solution approaches, annotate each with qualitative
assessments: elegance, generality, computational cost, conceptual clarity.
(4) Add a "surprise detector" that flags when a result contradicts physical
intuition — this is often where breakthroughs happen. Priority: LOW-MEDIUM —
this is a long-term research direction, not a quick fix.
**Source:** Conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.23: Cross-Session Collaborator Learning (BACKLOG)

**Goal:** "Resume from JSON state" is not the same as "remember the context of
our conversation." A real collaborator remembers: the researcher's reasoning
style (prefers geometric arguments), ongoing concerns (still worried about the
convergence issue from last month), and communication preferences (likes brief
updates, hates excessive detail). Add: (1) A `collaborator_profile` stored in
the operator's AITP config — tracks reasoning preferences, formalism choices,
communication style. (2) Cross-topic context threads — when a new topic starts,
automatically surface relevant conclusions from related past topics. (3) A
`research_trajectory` summary that persists across sessions: what directions
have been explored, what was abandoned and why, what is still open. (4) The AI
should proactively reference past work: "Last time we tried X and it failed
because Y — should we try a different approach?" Priority: MEDIUM — enhances
long-term research collaboration quality.
**Source:** Conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.24: Quick Exploration Mode With Low Bureaucracy (BACKLOG)

**Goal:** A single topic step produces 14+ administrative artifacts.
`orchestrate_topic.py` runs 7+ subprocess calls before any research happens.
Real research includes 30-minute idea sessions: "what if we try X?" — scribble
on a whiteboard, check a few limits, decide if it's worth pursuing. Add: (1)
A `quick_explore` mode that skips full topic bootstrap: no runtime protocol
bundle, no queue materialization, no checkpoint gates. (2) Quick mode produces
a lightweight session log (not 14 artifacts) that can be promoted to a full
topic if it proves fruitful. (3) CLI entry: `aitp explore "what if flux
attachment gives composite fermions in this model?"` that goes directly to AI
interaction with minimal ceremony. (4) Promotion path: quick session → "this
looks promising" → auto-creates full topic with accumulated context. Priority:
HIGH — the bureaucracy problem is the most immediately painful gap for actual
use.
**Source:** Conceptual audit 2026-04-07, code audit of orchestrate_topic.py
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.25: Source Fidelity Grading (BACKLOG)

**Goal:** Papers, arXiv preprints, blog posts, YouTube videos, and hallway
conversations are registered identically in the L0 source model. A physicist
assigns very different trust levels: published journal > arXiv with citations >
arXiv without citations > blog post > informal note. Add: (1) A `fidelity`
field to source registration: `peer_reviewed`, `arXiv_cited`, `arXiv_preprint`,
`preprint_unreviewed`, `blog_or_popular`, `informal_note`, `verbal`. (2)
Automatic fidelity inference from source metadata (DOI → peer_reviewed, arXiv
ID → arXiv_preprint, etc.). (3) Candidate promotion gates weight evidence by
source fidelity — a claim backed only by blog posts should not promote to L2
without stronger evidence. (4) Display fidelity in source lists so the operator
can see trust levels at a glance. Priority: MEDIUM — important for research
integrity but not blocking current work.
**Source:** Conceptual audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

---

## L0-L4 Layer-Specific Audit Findings

These items address specific gaps found when auditing each protocol layer
against real theoretical physics research workflow.

### Phase 999.26: L0 Citation Graph Traversal And BibTeX Support (BACKLOG)

**Goal:** L0 (source layer) registers individual papers but has no citation
graph traversal. A physicist reading a key paper immediately follows its
references forward (who cited this?) and backward (what does this cite?). Add:
(1) Citation graph construction — when a paper is registered, extract its
references and citing papers from available metadata. (2) A `traverse_citations`
action that follows citation chains N hops deep. (3) BibTeX import/export so
papers can be managed with standard physics tooling (Overleaf, Zotero,
LaTeX). (4) "Related work" suggestions based on citation co-occurrence. (5)
Integration with arXiv API for automatic metadata enrichment. Priority: HIGH —
citation traversal is how physicists actually navigate literature.
**Source:** L0-L4 layer audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.27: L1 Assumption Extraction And Reading Depth Model (BACKLOG)

**Goal:** L1 (intake/distillation) extracts novelty via keyword matching
(`source_distillation_support.py`) and classifies lanes as
formal_theory/numerical/exploratory — both are too shallow. Missing: (1)
Assumption extraction — every paper makes explicit and implicit assumptions.
The AI should identify: "This paper assumes non-interacting electrons" or
"This derivation uses the Born-Oppenheimer approximation." (2) Reading depth
tracking — distinguish between "skimmed abstract" vs "read introduction and
conclusions" vs "studied key equations" vs "reproduced calculation." (3)
Method identification — not just "numerical" but specifically "DMRG on a
1D chain with PBC, 200 sites, bond dimension χ=800." (4) Assumption
contradiction detection — flag when two papers in the same topic make
incompatible assumptions. Priority: HIGH — shallow intake means shallow
research.
**Source:** L0-L4 layer audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.28: L3 Scratch Mode And Negative Results Documentation (BACKLOG)

**Goal:** L3 (candidate layer) only supports formal candidate objects with
structured claims and evidence. Real research includes: scratch work that may
never become formal, dead ends worth remembering (so you don't retry them),
and exploratory calculations. Add: (1) A `scratch` candidate type — informal
working notes that don't need claim/evidence structure. (2) A `negative_result`
type — "Tried X approach, it failed because Y, don't retry." These are
valuable research knowledge that prevents wasted effort. (3) Candidate
demotion — not everything promoted to L3 should stay. Allow "this didn't pan
out" resolution with reasons. (4) A `calculation_log` type for intermediate
computational results that aren't ready for formal status. Priority: MEDIUM —
important for research hygiene.
**Source:** L0-L4 layer audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.29: L4 Analytical Validation Beyond Numerical Execution (BACKLOG)

**Goal:** L4 (validation) only validates via numerical code execution through
`closed_loop_v1.py`. Missing validation modes for theoretical physics: (1)
Limiting-case analysis — does the result agree with known limits? (2)
Dimensional analysis — are the units correct at each step? (3) Symmetry
checks — does the result respect the symmetries of the problem? (4)
Cross-reference validation — does the result agree with published values in L2?
(5) Self-consistency — does the result satisfy its own assumptions? Add these
as validation modes alongside the existing numerical execution mode. Each mode
produces a structured validation report. The AI should automatically suggest
appropriate validation modes based on the candidate type. Priority: HIGH —
without analytical validation, AITP cannot reliably evaluate theoretical work.
**Source:** L0-L4 layer audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.30: Cross-Layer Parallel Research And Context Carrying (BACKLOG)

**Goal:** The current pipeline routes research sequentially: L0→L1→L3→L4→L2.
Real research is parallel: while waiting for a calculation to finish, you read
another paper; while writing up one result, you explore a related question.
Missing: (1) Parallel action execution — allow multiple research actions
simultaneously (read + calculate + explore). (2) Backward context carrying —
when L4 validation fails and sends back to L3, carry the failure reason forward
instead of starting from scratch. (3) Cross-topic context — when working on
topic B, surface relevant findings from topic A without manual intervention.
(4) Interrupt and resume — allow pausing a research thread, working on
something else, then resuming with full context. Priority: MEDIUM — improves
research efficiency but requires significant runtime changes.
**Source:** L0-L4 layer audit 2026-04-07
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)

### Phase 999.31: Artifact Footprint Reduction (BACKLOG)

**Goal:** A single topic step produces 14+ administrative artifacts (runtime
protocol bundle, queue materialization, action logs, checkpoint files, status
updates, etc.). `orchestrate_topic.py` runs 7+ subprocess calls before any
research happens. This overhead: (1) Slows down every interaction. (2) Makes
the topic directory overwhelming for the operator to navigate. (3) Consumes
token budget on administrative content instead of research content. Add: (1)
Audit all artifacts per topic step — classify as essential vs optional vs
redundant. (2) Consolidate related artifacts (e.g., merge 3 status files into
1). (3) Make optional artifacts opt-in rather than default. (4) Reduce
subprocess calls in orchestrate_topic.py by combining related operations. (5)
Target: reduce per-step artifact count from 14+ to ≤5 essential artifacts.
Priority: MEDIUM — overlaps with 999.24 (quick exploration mode).
**Source:** L0-L4 layer audit 2026-04-07, code audit of orchestrate_topic.py
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd:review-backlog when ready)
