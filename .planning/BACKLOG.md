# Backlog Parking Lot: AITP Runtime And Knowledge Foundations

These items are parked between milestones.

- They are not active GSD phases.
- Their accumulated context lives under `.planning/backlog/`.
- When one is selected, promote it into the next milestone and create a fresh
  `.planning/REQUIREMENTS.md` plus `.planning/ROADMAP.md`.

## Post-Remediation Note

The `v1.37-v1.42` remediation chain shipped on `2026-04-11` and already
consumed part of the older parking-lot backlog, especially around:

- `L2` graph growth, staging, and retrieval
- collaborator memory and strategy-memory runtime surfaces
- CLI human-readable output and E2E coverage
- service/CLI hotspot extraction
- `L5` publication/output protocol support
- real-topic-backed onboarding and acceptance coverage

The follow-on `v1.43` control-plane and paired-backend closure milestone also
shipped on `2026-04-11`. That means the old near-term recommendation to do
control-plane closure next is now complete and should not be re-promoted.

Do not promote older `999.x` items blindly. Re-audit each parking-lot entry
against the archived `v1.37-v1.42` milestone docs before treating it as still
open work.

## Backlog Merge Audit

The older user-facing install/use backlog now needs to be read through the
later remediation and post-remediation milestones rather than as untouched
standalone work:

- `999.2` is already closed by the earlier human-readable CLI slice and should
  not be re-promoted.
- `999.3` is only partially closed: subprocess CLI and real-topic E2E coverage
  now exist, but the exact first-run `bootstrap -> loop -> status` temp-topic
  proof is still a reasonable future hardening target.
- `999.4` is already closed at the narrow warning-contract level; remaining
  Windows install/runtime robustness now belongs to `999.51`.
- `999.5` should not be reopened as synthetic `demo-topic` prose. Its useful
  remainder now lives under real-topic onboarding and quickstart work, mainly
  `999.50`.

## Current Promotion Override

Current user priority is to improve installation and first-use surfaces before
promoting deeper collaborator-core backlog.

That means the next promotion window should prefer:

- `999.48`
- `999.49`
- `999.50`
- `999.51`

unless a fresh regression forces a more urgent kernel-side fix first.

## Recommended Milestone Sequence

The backlog should not be promoted as a flat list.
The intended next sequence is now:

1. **Graph retrieval and consultation maturity**
   - graph traversal and search
   - progressive-disclosure retrieval
   - consultation that actually expands structured context instead of returning
     an empty library surface
   - human-facing graph reports / wiki-like navigation / Obsidian-friendly
     derived views
   - retrieval should ride on compiled memory rather than repeatedly treating
     the whole corpus as unexplained raw context
   - make the `H-plane` interaction semantics explicit across `L0-L4`
2. **Document understanding and source intelligence**
   - source fidelity grading
   - citation graph traversal
   - assumption extraction and reading-depth tracking
   - better cross-paper comparison and contradiction handling
   - explicit extracted-versus-inferred-versus-ambiguous relation labeling in
     intake and staging
   - provide task-type by lane templates for real research paths
3. **Research judgment and theoretical validation**
   - symbolic / analytical reasoning path
   - analytical validation beyond numerical execution
   - decision-making that uses momentum, stuckness, and surprise rather than
     only heuristics
4. **Long-term collaborator memory**
   - collaborator profile
   - research trajectory memory
   - negative-result retention
   - cross-session continuity
5. **Low-bureaucracy exploration**
   - quick exploration mode
   - reduced artifact footprint
   - promotion path from quick exploration into full topic work
6. **Engineering polish and reliability**
   - CLI readability
   - Windows startup reliability
   - E2E and test quality
   - documentation repair
   - dependency pinning
7. **Publication/output layer**
    - `L5 Publication Factory` only after the research-collaborator core is
      genuinely stronger
 8. **Research utility and maturity validation**
     - real topic end-to-end validation
     - cross-runtime deep execution parity
     - multi-user feedback collection
     - knowledge-graph content quality
     - semi-formal Lean bridge with a real theory result
 9. **Installation and adoption readiness**
     - PyPI publishable package replacing editable install
     - install verification command (`aitp doctor` hardening)
     - 5-minute quickstart guide
     - Windows path and symlink robustness

## Recently Closed Cluster

### v1.44: L2 knowledge-network MVP

This cluster is now complete on `2026-04-11`:

- activate bounded MVP families including `physical_picture`
- add seed/consult/compile/hygiene production entrypoints
- prove one bounded seeded direction through isolated acceptance

Do not re-promote the older L2 MVP backlog items directly unless a fresh
regression is found.

## Near-Term Stabilization

### 999.1: L5 Publication Factory

**Goal:** Add a final `L5` publication/output layer that turns a completed
topic into a paper-grade writing package without changing scientific truth.
**Requirements:** `PUB-01`, `PUB-02`, `PUB-03`
**Context:** `.planning/backlog/999.1-l5-publication-factory/`

### 999.2: Fix CLI Human-Readable Output

**Goal:** `_emit()` in `aitp_cli.py:22-26` always outputs JSON regardless of
the `--json` flag. Implement a human-readable default output path so users get
actionable status summaries instead of raw JSON.
**Status:** Implemented in `v1.33` and preserved by the later remediation
chain.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.2-fix-cli-human-readable-output/`

### 999.3: Add End-to-End Integration Tests

**Goal:** Add at least one subprocess-based E2E test that exercises
`aitp bootstrap -> aitp loop -> aitp status` against real temp-topic outputs.
**Status:** Partial. Subprocess CLI E2E and real-topic acceptance coverage now
exist across `v1.33` and `v1.42`, but the exact temp-topic
`bootstrap -> loop -> status` proof remains open.
**Merge note:** Treat the remaining first-run install/use proof as part of the
install/adoption cluster (`999.49` and `999.50`) rather than as a standalone
highest-priority kernel milestone.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.3-add-e2e-integration-tests/`

### 999.4: Fix SessionStart Windows Silent Failure

**Goal:** `hooks/run-hook.cmd:25` exits successfully when bash is missing on
Windows. Emit a warning so users can see that AITP session initialization did
not actually run.
**Status:** Implemented directly in `hooks/run-hook.cmd`; remaining Windows
install/runtime polish now belongs to `999.51`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.4-fix-sessionstart-windows-silent-failure/`

### 999.5: Add Complete Demo Topic For Onboarding

**Goal:** Add one worked demo topic, including transcript/history, that shows
the full `L0 -> L1 -> L3 -> L4 -> L2` lifecycle through natural user
interaction.
**Status:** Superseded by `v1.42` real-topic-backed onboarding closure and
merged forward into `999.50`.
**Important boundary:** Do not reopen this as synthetic `demo-topic` prose.
Use real-topic onboarding plus quickstart work instead.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.5-add-complete-demo-topic/`

### 999.6: Service God Class Cleanup

**Goal:** `aitp_service.py` is still large and contains many one-line wrapper
methods. Remove thin wrappers where callers can use the extracted support
modules directly.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.6-service-god-class-cleanup/`

### 999.7: Decision Script Quality Fixes

**Goal:** Document and improve `decide_next_action.py` scoring, including the
hardcoded scoring constants and the duplicate `policy_ranked_pending`
definition.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.7-decision-script-quality/`

### 999.8: Schema And Contract Consistency

**Goal:** Fix the `follow_up_actions` contract/schema mismatch and document the
relationship between the root `schemas/` tree and
`research/knowledge-hub/schemas/`.
**Status:** Implemented in `v1.51`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.8-schema-contract-consistency/`

### 999.9: Documentation Fixes

**Goal:** Repair the broken roadmap link, document the Python version
requirement, and consolidate scattered install guidance.
**Status:** Implemented in `v1.52`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.9-documentation-fixes/`

### 999.10: Dependency Pinning

**Goal:** Add compatible upper bounds or a lockfile for currently open-ended
dependencies such as `mcp` and `jsonschema`.
**Status:** Implemented in `v1.50`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.10-dependency-pinning/`

### 999.11: User Experience Friction Reduction

**Goal:** Reduce operator friction around excessive state files, lossy
subprocess errors, planning noise, and leaked Windows paths in runtime state.
**Status:** Implemented across `v1.53`, `v1.54`, `v1.58`, and `v1.59`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.11-user-experience-friction/`

### 999.12: Test Suite Quality Improvement

**Goal:** Separate structural integrity checks from behavioral tests, remove
duplicated bootstrap fixtures, and upgrade critical CLI tests from mocks to
real service paths.
**Status:** Implemented across `v1.55` through `v1.57`.
**Source:** User-perspective audit 2026-04-07
**Context:** `.planning/backlog/999.12-test-suite-quality/`

## L2 Knowledge Graph Evolution

These items were captured during the 2026-04-07 conceptual audit of the empty
L2 knowledge base and its overbuilt ontology surface.

### 999.13: Implement Graph Traversal And Search

**Goal:** Add graph expansion, dependency-edge traversal, and token-budgeted
knowledge-packet retrieval on top of the current empty `edges.jsonl` / tag-only
consultation path.
**Status:** Implemented across `v1.44` and `v1.45`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.13-implement-graph-traversal-and-search/`

### 999.14: Add Physical Picture Object Type

**Goal:** Add a first-class `physical_picture` knowledge object so AITP can
store physics intuition, heuristic arguments, formal analogs, and known
limitations rather than only formal concepts/theorems.
**Status:** Implemented in `v1.44`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.14-add-physical-picture-object-type/`

### 999.15: Define MVP Type Subset For Knowledge Graph Seed

**Goal:** Define a smaller core subset of `concept`, `theorem_card`, `method`,
`assumption_card`, `physical_picture`, and `warning_note` so the graph can
start from real data before carrying the full 22-type ontology.
**Status:** Implemented in `v1.44`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.15-define-mvp-type-subset-for-knowledge-graph-seed/`

### 999.16: Add Lightweight Knowledge Entry Path

**Goal:** Add a lightweight staging/CLI path for recording concepts outside the
full `L3 -> L4 -> L2` promotion bureaucracy, with later review into trusted
knowledge.
**Status:** Implemented in `v1.44`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.16-add-lightweight-knowledge-entry-path/`

### 999.17: Implement Progressive Disclosure Retrieval For AI Context

**Goal:** Make AI retrieve an index first and request deeper knowledge payloads
on demand, rather than loading the full knowledge base into context.
**Status:** Implemented across `v1.44` and `v1.45`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.17-implement-progressive-disclosure-retrieval-for-ai-context/`

### 999.18: Seed First Direction Knowledge Graph

**Goal:** Seed one small real knowledge graph direction with 10-20 nodes and
dependency edges, then use it as the regression baseline for later L2 work.
**Status:** Implemented in `v1.44`.
**Source:** L2 knowledge graph conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.18-seed-first-direction-knowledge-graph/`

## Conceptual Gaps

These items came from the theoretical-physics collaborator audit of AITP's
current research loop.

### 999.19: Add Symbolic And Analytical Reasoning Path

**Goal:** Extend validation beyond executable numerical scripts to symbolic and
analytical work such as SymPy/Mathematica lanes, dimensional analysis, limiting
cases, and proof-sketch sanity checks.
**Status:** Implemented in `v1.47`.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.19-symbolic-analytical-reasoning-path/`

### 999.20: Add Research Judgment To Decision-Making

**Goal:** Replace purely keyword-and-score action routing with momentum,
stuckness, surprise capture, and lightweight research-judgment signals.
**Status:** Implemented in `v1.47`.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.20-research-judgment-in-decision-making/`

### 999.21: Make Layer Model Flexible For Real Research Iteration

**Goal:** Treat the AITP layer model more like a graph with iteration edges and
exploratory loops, not only as a serialized promotion pipeline.
**Status:** First production slice implemented in `v1.60` (`layer_graph`
artifact, `topic_status`, and `aitp layer-graph`). Broader flexible-iteration
work remains open.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.21-flexible-layer-model/`

### 999.22: Model Creativity, Taste, And Physical Intuition

**Goal:** Give the operator/research loop a place to represent elegance,
physical taste, preferred formalisms, and intuition-driven surprise handling.
**Status:** First production slice implemented in `v1.61` (`research_taste`
artifact, `record-taste`, and `taste-profile`). Broader creativity/taste work
remains open.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.22-creativity-taste-and-physical-intuition/`

### 999.23: Cross-Session Collaborator Learning

**Goal:** Persist collaborator preferences, long-horizon concerns, and research
trajectory memory across sessions and across related topics.
**Status:** Implemented in `v1.48`.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.23-cross-session-collaborator-learning/`

### 999.24: Quick Exploration Mode With Low Bureaucracy

**Goal:** Add a lightweight `aitp explore` path that skips full topic bootstrap
and heavy artifact generation for short speculative sessions.
**Status:** Implemented in `v1.49`.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.24-quick-exploration-mode/`

### 999.25: Source Fidelity Grading

**Goal:** Distinguish peer-reviewed papers, arXiv preprints, blog posts,
informal notes, and verbal claims so evidence weight is visible and promotion
logic can use fidelity.
**Status:** Implemented in `v1.46`.
**Source:** Conceptual audit 2026-04-07
**Context:** `.planning/backlog/999.25-source-fidelity-grading/`

## L0-L4 Layer Audit

These items are the layer-specific follow-ups from the 2026-04-07 audit.

### 999.26: L0 Citation Graph Traversal And BibTeX Support

**Goal:** Add citation traversal, related-work suggestions, and BibTeX import /
export so literature navigation matches how physicists actually work.
**Status:** Implemented across `v1.46` and `v1.63`.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.26-l0-citation-graph-and-bibtex/`

### 999.27: L1 Assumption Extraction And Reading Depth Model

**Goal:** Make intake track assumptions, reading depth, method specificity, and
contradictory assumptions instead of shallow keyword extraction alone.
**Status:** First production slice implemented in `v1.64`
(`method_specificity_rows`, runtime/status exposure, and isolated acceptance).
Broader intake maturity remains open.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.27-l1-assumption-extraction-reading-depth/`

### 999.28: L3 Scratch Mode And Negative Results Documentation

**Goal:** Add scratch notes, negative-result memory, candidate demotion, and
intermediate calculation logs so exploratory dead ends become durable knowledge
instead of disappearing.
**Status:** First production slice implemented in `v1.62` (`scratchpad`
artifact, `record-scratch-note`, `record-negative-result`, and `scratch-log`).
Broader scratch-mode work remains open.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.28-l3-scratch-mode-negative-results/`

### 999.29: L4 Analytical Validation Beyond Numerical Execution

**Goal:** Add limiting-case, dimensional, symmetry, cross-reference, and
self-consistency validation modes alongside current numerical execution checks.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.29-l4-analytical-validation/`

### 999.30: Cross-Layer Parallel Research And Context Carrying

**Goal:** Support parallel research actions, backward context carrying after
failed validation, cross-topic reuse, and pause/resume with richer continuity.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.30-cross-layer-parallel-research-context/`

### 999.31: Artifact Footprint Reduction

**Goal:** Audit and reduce the 14+ artifacts and 7+ subprocess calls produced
by a single topic step, aiming for a much smaller essential surface.
**Source:** L0-L4 layer audit 2026-04-07
**Context:** `.planning/backlog/999.31-artifact-footprint-reduction/`

### 999.32: Research Trajectory Recording And Mode Learning

**Goal:** Record what research modes the operator actually uses and learn from
full research arcs, rather than assuming a fixed predetermined pipeline.
**Source:** Research workflow learning discussion 2026-04-07
**Context:** `.planning/backlog/999.32-research-trajectory-recording-and-mode-learning/`

### 999.33: Mixed-Corpus Graph Seed Ingestion For L0/L1/Staging

**Goal:** Add a graph-building intake path over mixed artifacts such as papers,
notes, code, and image-derived descriptions so AITP can cheaply seed staging
and early `L2` graph structure from real corpora instead of relying only on
manual canonical entry.
**Important boundary:** This path may seed `L0/L1/staging`, but it must not
directly bypass canonical `L2` promotion gates.
**Source:** External pattern review (`graphify`) 2026-04-08
**Context:** `.planning/backlog/999.33-mixed-corpus-graph-seed-ingestion/`

### 999.34: Extracted Versus Inferred Versus Ambiguous Graph Labels

**Goal:** Distinguish directly extracted relations, model-inferred relations,
and ambiguous candidates during intake, staging, and graph review so AITP can
use graph growth without confusing convenience edges with trusted scientific
structure.
**Source:** External pattern review (`graphify`) 2026-04-08
**Context:** `.planning/backlog/999.34-extracted-inferred-ambiguous-graph-labels/`

### 999.35: Human-Facing Graph Report And Obsidian-Derived Navigation

**Goal:** Add human-readable graph views such as reports, wiki-style maps, or
Obsidian-friendly derived pages so the operator can inspect knowledge growth
without reading raw JSONL indexes and edges.
**Source:** External pattern review (`graphify`) 2026-04-08
**Context:** `.planning/backlog/999.35-human-facing-graph-report-and-obsidian-navigation/`

### 999.36: Incremental Graph Rebuild And Update Hooks

**Goal:** Add incremental update, rebuild, and cache-aware graph refresh
mechanisms so continued literature intake and note growth can update the graph
cheaply instead of rebuilding everything from scratch each time.
**Source:** External pattern review (`graphify`) 2026-04-08
**Context:** `.planning/backlog/999.36-incremental-graph-rebuild-and-update-hooks/`

### 999.37: Persistent Wiki-Style Knowledge Compilation

**Goal:** Move beyond retrieval-only memory by compiling repeated reading,
discussion, and route-comparison outcomes into a durable linked research brain
that records updates, contradictions, and what new knowledge was added.
**Important boundary:** This compilation loop may enrich staging and prepared
canonical candidates, but it must still respect `L4` validation and promotion
gates before authoritative `L2` writeback.
**Source:** External pattern review (Karpathy `LLM Wiki`) plus collaborator
capability tracks 2026-04-08
**Context:** `.planning/backlog/999.37-persistent-wiki-style-knowledge-compilation/`

### 999.38: Freeze Task-Type Axis And Orchestration Templates

**Goal:** Replace the too-coarse scenario framing with explicit task types:
`open_exploration`, `conjecture_attempt`, and `target_driven_execution`, then
define how those task types shape routing without replacing `L0-L4`.
**Source:** Research-scenario freeze 2026-04-08
**Context:** `.planning/backlog/999.38-task-type-axis-and-orchestration-templates/`

### 999.39: Human Interaction Plane

**Goal:** Model human interaction as a cross-cutting `H-plane` that can
intervene at any layer, rather than smearing checkpoint/stop/update behavior
across unrelated runtime notes.
**Source:** Research-scenario freeze 2026-04-08
**Context:** `.planning/backlog/999.39-human-interaction-plane/`

### 999.40: Decompose L3 Into Analysis, Result-Integration, And Distillation

**Goal:** Keep top-level `L3` continuity while explicitly splitting its current
overload into `L3-A` topic analysis, `L3-R` `L4` return interpretation, and
`L3-D` `L2` distillation preparation.
**Source:** Research-scenario freeze 2026-04-08
**Context:** `.planning/backlog/999.40-decompose-l3-into-analysis-result-integration-and-distillation/`

### 999.41: Mandatory L4 To L3 Synthesis Return

**Goal:** Freeze and implement the rule that `L4` does not write directly to
`L2`; instead it must return through `L3-R`, after which `L3-D` decides what is
actually reusable.
**Source:** Research-scenario freeze 2026-04-08
**Context:** `.planning/backlog/999.41-mandatory-l4-to-l3-synthesis-return/`

### 999.42: Task-Type By Lane Template Library

**Goal:** Provide reusable orchestration templates for combinations such as
`open_exploration × formal_theory`, `conjecture_attempt × model_numeric`, and
`target_driven_execution × code_and_materials`.
**Source:** Research-scenario freeze 2026-04-08
**Context:** `.planning/backlog/999.42-task-type-by-lane-template-library/`

## Research Utility And Maturity Validation

These items address gaps that remain even after all protocol-surface backlog
entries are closed. They answer "is AITP actually useful for research?" rather
than "does this feature exist?".

### 999.43: Real Topic End-To-End Validation

**Goal:** Run at least 1-2 genuine physics research topics through the full
`L0 -> L1 -> L3 -> L4 -> L2` loop, documenting where the protocol helped, where
it created friction, and where bounded steps were too loose or too rigid.
**Success criteria:** A written post-mortem per topic comparing the AITP-assisted
research arc against the operator's unassisted baseline, with concrete examples
of protocol surfaces that added value and surfaces that did not.
**Why this matters:** Every closed milestone so far proves that a surface
exists and has tests. None of them prove that the surface helps a real
researcher do better work.
**Context:** `.planning/backlog/999.43-real-topic-e2e-validation/`

### 999.44: Cross-Runtime Deep Execution Parity

**Goal:** Bring OpenCode, Claude Code, and OpenClaw from "parity target"
(current front-door diagnosable but not documented as deep execution lanes)
to verified deep execution parity with Codex.
**Success criteria:** At least one real topic run end-to-end on each runtime with
equivalent artifact quality, plus documented gaps where a runtime cannot yet
match Codex behavior.
**Why this matters:** Codex is the only baseline. If AITP only works well on one
runtime, its value is constrained to that ecosystem.
**Context:** `.planning/backlog/999.44-cross-runtime-deep-parity/`

### 999.45: Multi-User Feedback Collection

**Goal:** Collect structured feedback from at least 2-3 real theoretical-physics
researchers who used AITP for non-trivial topic work, covering protocol
comprehension, bounded-step usefulness, artifact quality, and overall friction
versus value trade-off.
**Success criteria:** A compiled feedback report with concrete improvement
requests and a revised prioritization of backlog items based on actual user pain
rather than developer assumptions.
**Why this matters:** A protocol designed by one person and tested by one
person cannot claim design validity. Multi-user feedback is the cheapest way to
discover whether the bounded-step model actually matches how physicists think.
**Context:** `.planning/backlog/999.45-multi-user-feedback/`

### 999.46: Knowledge-Graph Content Quality Beyond Seeded Baseline

**Goal:** Grow the L2 knowledge graph from a thin seeded baseline into a
non-trivial corpus (50+ nodes with real dependency edges) covering at least one
real research direction, then validate that retrieval and consultation return
results that are measurably more useful than raw paper re-reading.
**Success criteria:** A documented corpus with provenance, a retrieval
precision/recall evaluation against a gold-standard question set, and an honest
assessment of what the graph can and cannot answer.
**Why this matters:** An empty graph with good retrieval code is still an empty
graph. Content quality is the difference between a tool that could be useful and
a tool that is technically complete but practically useless.
**Context:** `.planning/backlog/999.46-knowledge-graph-content-quality/`

### 999.47: Semi-Formal Lean Bridge With Real Theory Result

**Goal:** Export at least one real (non-toy) semi-formal theory result through the
Lean bridge, producing a Lean-ready declaration packet with proof-obligation and
proof-state sidecars that survive Lean type-checking or produce a documented
mismatch report.
**Success criteria:** A Lean module file derived from a real AITP topic, with
documentation of what was exported, what survived, and what failed type-checking.
**Why this matters:** The Lean bridge currently exists as infrastructure. A real
export would prove whether the semi-formal protocol actually produces material
that formal verification tools can consume, or whether the gap between AITP's
semi-formal layer and Lean's formal requirements is too large to bridge
without additional intermediate tooling.
**Context:** `.planning/backlog/999.47-lean-bridge-real-theory-result/`

## Installation And Adoption Readiness

These items address the gap between "a researcher who already committed to AITP
can install it" and "a curious researcher can try AITP without friction." They
answer "can someone else actually start using this?" rather than "does the
install documentation exist?". Current assessment: AITP sits at Maturity Level
1→2 transition on installation; to reach Level 3 (research utility for others),
it needs one public `pip install aitp-kernel` path while keeping the `aitp` CLI
name and a 5-minute quickstart.

Merge note for this cluster:

- `999.48` through `999.51` are now the canonical adoption-facing successors to
  the older user-perspective install/use backlog.
- In particular, they absorb the still-useful remainder of `999.3`, `999.4`,
  and `999.5` without reopening synthetic onboarding or already-fixed warning
  contracts.

### 999.48: PyPI-Publishable Package

**Goal:** Replace `pip install -e research/knowledge-hub` with
`pip install aitp-kernel` from PyPI while preserving the `aitp` CLI command.
Ship versioned releases with proper dependency resolution instead of requiring a
local editable install from a git clone.
**Success criteria:** `pip install aitp-kernel` works on a clean Python 3.10+
environment on both Linux and Windows; `aitp --version` returns a meaningful
semver string; existing editable installs continue to work via the migration
guide.
**Why this matters:** Requiring a git clone and editable install means only
developers already committed to the project can try AITP. PyPI publication is
the single highest-impact step toward making AITP available to other
researchers. Without it, every other adoption improvement is locked behind a
manual clone step.
**Context:** `docs/INSTALL.md`, `research/knowledge-hub/setup.py`

### 999.49: Installation Verification And Smoke Test Hardening

**Goal:** Make `aitp doctor` a reliable post-install verification command that
checks kernel health, runtime adapter readiness, skill discovery, and Windows
path correctness. It should return a clear pass/fail per surface and an
actionable remediation hint for each failure.
**Success criteria:** `aitp doctor` passes on a fresh install across at least 2
runtimes; `aitp doctor --json` produces machine-parseable output usable in CI;
each failure includes a one-line remediation command or doc link.
**Why this matters:** Currently there is no way for a new user to confirm their
install works without attempting a full topic bootstrap and seeing if it breaks.
A reliable doctor command turns "I hope this installed correctly" into a
verifiable green check.
**Merged predecessors:** the still-open first-run proof remainder from `999.3`.
**Context:** `research/knowledge-hub/runtime/`, `scripts/aitp-local.cmd`

### 999.50: 5-Minute Quickstart Guide

**Goal:** Write a tutorial-grade quickstart that takes a brand-new user from
zero to their first real AITP topic in under 5 minutes, covering install, first
topic creation, one bounded work step, and status inspection.
**Success criteria:** A new user following only the quickstart (no other docs)
can run `aitp bootstrap`, `aitp loop`, and `aitp status` on a real topic and
understand what happened; the guide is tested on at least 2 runtimes and 2 OSes.
**Why this matters:** Current install docs are reference-quality: they tell you
what to type but not why, and they assume you already understand the AITP model.
A quickstart is the difference between "I installed it" and "I used it once and
decided whether to continue."
**Merged predecessors:** the non-synthetic onboarding remainder of `999.5`,
plus the user-facing first-run path from `999.3`.
**Context:** `docs/INSTALL.md`, `docs/USER_TOPIC_JOURNEY.md`

### 999.51: Windows Path And Symlink Robustness

**Goal:** Audit and fix all Windows-specific installation friction: POSIX-only
path assumptions in docs and scripts, symlink requirements that need elevated
privileges or Developer Mode, and forward-slash assumptions that break in edge
cases.
**Success criteria:** Full install and first topic bootstrap works on Windows 10+
without WSL, without Developer Mode, and without elevated privileges; all doc
paths use OS-appropriate separators or cross-platform alternatives.
**Why this matters:** A significant fraction of potential physics researchers
work on Windows. Currently the Windows path works but is noticeably rougher than
POSIX, and the docs default to POSIX conventions. This friction is unnecessary
and directly gates adoption for non-Linux users.
**Merged predecessors:** broader Windows follow-up beyond the already-fixed
warning contract in `999.4`.
**Context:** `scripts/aitp-local.cmd`, `docs/INSTALL.md`, all `INSTALL_*.md`

## Legacy Note

### Legacy: L2 Knowledge Compiler And Hygiene

**Status:** Retained for reference only.
**Why kept:** This older backlog note predates the shipped `v1.5` milestone and
the later conceptual L2 graph audit. It is now superseded by the newer L2
backlog cluster above, but its context may still be useful when selecting a
future milestone.
**Context:** `.planning/backlog/legacy-l2-knowledge-compiler-and-hygiene/`
