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
Broader intake maturity remains open. The contradiction-adjudication remainder
landed in `v1.93`; further work would now be broader intake maturity beyond the
contradiction surface itself.
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
**Status:** First production slice implemented in `v1.47`; broader analytical
validation maturity is now promoted into `v1.94`.
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

### 999.52: Proof Engineering Memory And Proof-Fragment Distillation

**Goal:** Turn reusable formal-proof engineering knowledge into a first-class
AITP path by extending run-local `strategy_memory` for proof-engineering
patterns, then distilling high-confidence rows into `proof_fragment`
candidates that can promote into canonical `L2`.
**Success criteria:** one runtime-side proof-engineering memory path exists for
formal topics; one distillation path converts high-confidence
proof-engineering rows into `proof_fragment` candidates; one promoted canonical
`proof_fragment` proves the pattern can survive `L3/L4` review and cross-topic
reuse without collapsing into ad hoc notes.
**Why this matters:** the repository already reserves `proof_fragment` and
`derivation_step` as legal `L2` families, and runtime proof/repair artifacts
already exist, but there is still no honest bridge from real proof debugging
work into durable reusable knowledge. Without that bridge, formal-theory work
keeps rediscovering local Lean/mathlib tactics instead of accumulating them as
governed AITP memory.
**Recommended shape:** do not add a brand-new canonical family. Instead:
- extend `strategy_memory` to support proof-engineering pattern rows
- add family-specific payload contracts and storage routes for canonical
  `proof_fragment`
- distill high-confidence runtime rows into `proof_fragment` candidates before
  normal promotion
**Context:** `.planning/backlog/999.52-proof-engineering-memory-and-proof-fragment-distillation/`

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

## HCI-Prioritized Gap Analysis (2026-04-13)

Cross-reference with wow-harness borrowable patterns below.
Items 999.60–999.73 are new; items already tracked in Phase 165.2 are noted.

### Tier 1 — HCI Foundation (unlocks everything else)

### 999.60: Human-Readable Status/Next Rendering

**Goal:** Add a `--human` flag (or make it default) that renders topic status in
under 10 lines: topic name, current mode, last action, next step, blocked items.
**Problem:** Dashboard outputs 40+ sections with no visual hierarchy; humans
cannot scan status at a glance.
**Files:** `kernel_markdown_renderers.py`, `topic_shell_support.py`
**Source:** HCI gap analysis 2026-04-13

### 999.61: First-Run Onboarding Experience

**Goal:** `aitp hello` or `aitp tutorial` that walks: install check → create
first topic → check status → read a paper. Three steps, zero jargon.
**Problem:** No help.md, no tutorial, no getting-started. 60+ commands with no
guidance.
**Files:** New `cli_onboarding_handler.py`
**Source:** HCI gap analysis 2026-04-13

### 999.62: Jargon Cleanup — Human-Facing Surfaces Only

**Goal:** Audit all `checkpoint_questions` templates; replace "adjudication
route", "L0 recovery", "promotion approval" with plain language. Add a
jargon-regex gate in CI.
**Problem:** Checkpoint questions contain protocol jargon despite explicit rules.
**Files:** All `*_support.py` files that emit checkpoint questions
**Source:** HCI gap analysis 2026-04-13

### 999.63: Progressive Disclosure for CLI Commands

**Goal:** Group commands: Core (5 commands), Advanced, Maintenance. `aitp help`
shows Core only; `aitp help --all` shows everything.
**Problem:** 60+ flat commands with no grouping.
**Files:** `aitp_cli.py`
**Source:** HCI gap analysis 2026-04-13

### 999.64: Natural-Language Steering

**Goal:** `steer-topic` accepts free-text input; parse into structured steering
internally instead of requiring JSON direction/decision/control-note.
**Problem:** Humans should say "换方向到X", not fill JSON.
**Files:** `aitp_cli.py` steer handler, `chat_session_support.py`
**Source:** HCI gap analysis 2026-04-13

### Tier 2 — Interaction Friction Removal

### 999.65: "Where Am I?" Progress Indicator

**Goal:** Add pipeline stage tracking to topic_state.json; render as progress bar
or stage list in status/next output.
**Problem:** No "Step N of M" metaphor.
**Files:** `topic_shell_support.py`, `topic_state.json` schema
**Source:** HCI gap analysis 2026-04-13

### 999.66: Session Summary / Handoff Surface

**Goal:** Materialize `session_summary.md` on session end: attempted, succeeded,
pending, changed since last session.
**Problem:** Every session starts from amnesia.
**Files:** Extend `session_chronicle_handler.py` or new `session_summary_support.py`
**Source:** HCI gap analysis 2026-04-13

### 999.67: Change Log / Diff Surface

**Goal:** Track artifact timestamps; diff against last session; render delta
summary on session start.
**Problem:** No "what changed since last session" view.
**Files:** `topic_shell_support.py`, new `change_tracking_support.py`
**Source:** HCI gap analysis 2026-04-13

### 999.68: Feedback Mechanism for Checkpoint Questions

**Goal:** Add dismiss/rephrase/skip options to checkpoint rendering; log
dismissals for future prompt improvement.
**Problem:** Cannot say "this question is wrong" or skip.
**Files:** `topic_loop_support.py`, runtime protocol templates
**Source:** HCI gap analysis 2026-04-13

### 999.69: Idea Packet Exploratory Bypass

**Goal:** Add `exploratory` mode requiring only `title` + `one_sentence`;
remaining fields auto-fill with TBD.
**Problem:** 5 required fields block exploration; inspiration dies at the form.
**Files:** `topic_shell_support.py`, idea_packet schema
**Source:** HCI gap analysis 2026-04-13

### 999.70: Error Messages for Humans, Not Python Tracebacks

**Goal:** Wrap all subprocess calls with human-readable error messages + suggested
fix actions.
**Problem:** `FileNotFoundError` from missing `orchestrate_topic.py` leaks
Python exceptions.
**Files:** `aitp_service.py` (orchestrate, audit methods)
**Source:** HCI gap analysis 2026-04-13

### Tier 3 — Knowledge Pipeline (see also 999.14–999.19)

### 999.71: Default `--download-source` for arXiv Registration

**Goal:** Make `--download-source` the default; add `--metadata-only` for
explicit lightweight registration.
**Problem:** Default is metadata-only; most registered papers have no content.
**Status:** Implemented in `v1.92` Phase `166.1`
**Plan:** `166.1-01`
**Files:** `register_arxiv_source.py`
**Source:** HCI gap analysis 2026-04-13

### Tier 4 — Robustness & Recovery (see also 999.21–999.24)

### 999.72: Crash Recovery / Checkpoint-Restore

**Goal:** Snapshot topic_state before each loop step; on crash detect last good
snapshot; offer `aitp recover --topic-slug X`.
**Problem:** Mid-loop failure has no rollback.
**Files:** `topic_loop_support.py`, new `recovery_support.py`
**Source:** HCI gap analysis 2026-04-13

### Tier 5 — wow-harness Borrowable Patterns

### 999.73: Mechanical Completion Verification (from wow-harness stop-evaluator)

**Goal:** Before invoking expensive LLM evaluation for topic completion, run a
zero-cost mechanical check: all tracked operations have `baseline_status:
confirmed`, no unresolved gaps, no pending follow-ups. Only invoke LLM if
mechanical check passes.
**Problem:** AITP relies on LLM evaluation for everything, even trivially
checkable mechanical conditions.
**Pattern source:** `wow-harness/scripts/hooks/stop-evaluator.py`
**Files:** `topic_loop_support.py`, `topic_shell_support.py`
**Source:** wow-harness comparison 2026-04-13

### 999.74: Session-Scoped Context Injection with Dedup (from wow-harness fragments)

**Goal:** When agents edit theory artifacts, auto-inject domain-specific context
(notation bindings, prerequisite closure status, relevant L2 units) via a
path-scoped fragment map. Deduplicate with TTL so same fragment injects once per
session.
**Problem:** Agents edit theory files without seeing the notation/convention
context they should follow.
**Pattern source:** `wow-harness/scripts/context_router.py`,
`wow-harness/scripts/guard-feedback.py`
**Files:** New `theory_context_injection.py`, `runtime_bundle_support.py`
**Source:** wow-harness comparison 2026-04-13

### 999.75: Schema-Level Agent Isolation (from wow-harness review-agent-gatekeeper)

**Goal:** Enforce that Skeptic-D and review agents are physically unable to modify
the artifacts they review — not via prompt constraint but via tool manifest
exclusion.
**Problem:** AITP relies on prompt-level "do not edit" constraints that can be
violated.
**Pattern source:** `wow-harness/scripts/hooks/review-agent-gatekeeper.py`
**Files:** MCP tool registration, agent dispatch
**Source:** wow-harness comparison 2026-04-13

### 999.76: JSONL Metrics → Self-Evolution Loop (from wow-harness trace-analyzer)

**Goal:** Log all theory operations (coverage audits, promotion attempts,
conformance checks, derivation retries) as append-only JSONL. Periodically
analyze for systematic patterns: "Skeptic-D consistently flags missing
prerequisite proofs in quantum gravity topics". Surface actionable proposals for
human review.
**Problem:** No observability into what patterns recur across topics.
**Pattern source:** `wow-harness/scripts/hooks/trace-analyzer.py`
**Files:** New `theory_metrics.py`, extend existing audit flows
**Source:** wow-harness comparison 2026-04-13

### 999.77: Derivation Loop Detection with Intervention (from wow-harness loop-detection)

**Goal:** Track per-artifact edit count within a topic loop. When a derivation or
proof attempt exceeds N retries on the same approach, inject a suggestion to
decompose or try a different strategy.
**Problem:** AITP can silently retry failing approaches without intervention.
**Pattern source:** `wow-harness/scripts/hooks/loop-detection.py`
**Files:** `topic_loop_support.py`
**Source:** wow-harness comparison 2026-04-13

### 999.78: Manifest-as-Truth-Source (from wow-harness MANIFEST.yaml)

**Goal:** Formalize what artifacts must exist at each topic state (bootstrapped,
exploring, verifying, promoting, completed). Enable integrity checks: "topic
claims to be in verify mode but validation_contract.md is missing".
**Problem:** No single source of truth for what the protocol requires at each
state; drift goes undetected.
**Pattern source:** `wow-harness/.wow-harness/MANIFEST.yaml`
**Files:** New `protocol_manifest.py` or extend `conformance_state`
**Source:** wow-harness comparison 2026-04-13

## wow-harness Comparison Summary (2026-04-13)

## L0/L1 Deep Integration — DeepXiv + Graphify (2026-04-14)

These items capture the integration of design patterns from DeepXiv SDK
(progressive arXiv reading) and Graphify (knowledge graph construction from
documents) into AITP's L0 source layer and L1 intake layer. Both tools are MIT
License; integration requires copyright attribution in source files + NOTICE entry.

**External references:**
- Graphify v0.4.5: https://github.com/safishamsi/graphify
- DeepXiv SDK v0.2.4: https://github.com/DeepXiv/deepxiv_sdk

**Key design principle:** Deep internalization of their patterns with
physics-specific extensions, not shallow `pip install`. The integration must feel
like AITP-native code written from a theoretical physicist's research perspective.

### 999.79: Post-Registration Source Enrichment via DeepXiv Progressive Reading

**Goal:** Add a post-registration enrichment step (`enrich_with_deepxiv.py`) that
runs after `register_arxiv_source.py` completes. Uses DeepXiv's 5-level progressive
reading chain to fill `provenance` with TLDR, keywords, section structure
({name, idx, tldr, token_count} per section), and GitHub URL.
**Axis:** A1 (L0 internal)
**Phase:** 165.5 (plan 165.5-01)
**Files:** New `enrich_with_deepxiv.py`, existing `register_arxiv_source.py`,
  existing `discover_and_register.py`
**Borrowed patterns:** DeepXiv SDK's `PaperInfo` TypedDict, `_match_section_name()`
  fuzzy matching, `_retry()` exponential backoff, `brief()`/`head()` progressive
  reading API
**Contract safety:** New data goes into `provenance` sub-object (free-form, safe to
  extend without changing `source-item.schema.json` top-level). Graceful degradation:
  if DeepXiv cloud API unavailable, proceeds with metadata-only registration.
**Source:** DeepXiv SDK integration analysis 2026-04-14

### 999.80: Physics-Adapted Concept Graph Construction from Sources

**Goal:** Add a concept graph construction step (`build_concept_graph.py`) that
runs after enrichment. Uses an adapted version of Graphify's LLM extraction prompt
with physics-specific node types (theorem, definition, conjecture, regime,
approximation, notation_system, proof, equation, observable) and relation types
(assumes, valid_in, contradicts, derives, notation_for, generalizes,
special_case_of, implies). Runs Graphify's 3-layer dedup + Leiden community
detection. Supports hyperedges for physics patterns like "theorem + assumption +
approximation → conclusion".
**Axis:** A1 (L0 internal — graph construction is a source-layer capability)
**Phase:** 165.5 (plan 165.5-01)
**Files:** New `build_concept_graph.py`, new physics-specific extraction prompt,
  new `concept_graph.schema.json`
**Borrowed patterns:** Graphify's LLM extraction prompt (skill.md ~L253-303),
  3-tier confidence (EXTRACTED/INFERRED/AMBIGUOUS), `build.py` 3-layer dedup,
  `cluster.py` Leiden detection, SHA256 per-file caching, `extract_pdf_text()`,
  `_looks_like_paper()` heuristic
**Output:** `concept_graph.json` stored alongside `source.json` in source directory.
**Source:** Graphify integration analysis 2026-04-14

### 999.81: Graph-Based L1 Intake Extension with Concept Graph Data

**Goal:** Extend L1 intake to include concept graph data as a new `concept_graph`
key containing `{nodes[], edges[], hyperedges[], communities[], god_nodes[]}`.
`god_nodes[]` identifies foundational concepts (many dependents) for prerequisite
detection. Preserves all 8 existing required L1 keys — graph data augments, does
not replace, regex patterns.
**Axis:** A1 (L1 internal)
**Phase:** 165.5 (plan 165.5-02)
**Files:** Existing `source_intelligence.py`, existing `l1_source_intake_support.py`,
  existing `source_distillation_support.py`
**Contract safety:** New key in L1 intake dict; existing consumers ignore unknown
  keys. No changes to 8 required fields.
**Source:** L1 contract analysis 2026-04-14

### 999.82: Progressive Reading Chain in L0→L1 Distillation

**Goal:** Replace brute-force preview truncation (currently 200–500 chars) with
DeepXiv's section-aware progressive loading: brief (~200 tokens) → head (~2K
tokens) → section (targeted) → raw (full paper). Token-budget-aware by AITP mode:
Discussion=brief only, Explore=brief+head, Verify=brief+head+relevant sections,
Promote=full as needed. Reuse DeepXiv agent submodule's LangGraph ReAct pattern
for token-budget management.
**Axis:** A2 (L0→L1 connection)
**Phase:** 165.5 (plan 165.5-02)
**Files:** Existing `source_distillation_support.py`, existing
  `runtime_bundle_support.py`
**Depends on:** Phase 165.2 (mode-aware runtime bundle must exist for mode-varying
  context loading)
**Borrowed patterns:** DeepXiv SDK's progressive reading chain (brief/head/section/
  raw), token-budget-aware agent from `agent/` submodule, LangGraph ReAct pattern
**Source:** DeepXiv SDK integration analysis 2026-04-14

### 999.83: Concept Graph Analysis Tools for L1→L2 Knowledge Staging

**Goal:** Adapt Graphify's `analyze.py` functions for AITP's L1→L2 connection:
`surprising_connections()` for cross-domain links between sources,
`suggest_questions()` for auto-generating research questions from graph structure,
`graph_diff()` for tracking knowledge evolution across topic iterations. These
feed into Phase 165.2's literature-intake fast path for L2 staging.
**Axis:** A2 (L1→L2 connection)
**Phase:** 165.5 (plan 165.5-02)
**Files:** New `graph_analysis_tools.py`, existing `source_distillation_support.py`
**Borrowed patterns:** Graphify's `god_nodes()`, `surprising_connections()`,
  `suggest_questions()`, `graph_diff()` from `analyze.py`
**Source:** Graphify integration analysis 2026-04-14

### 999.84: Obsidian Concept Graph Export for Theoretical-Physics Brain

**Goal:** Adapt Graphify's Obsidian vault export for direct compatibility with the
theoretical-physics brain. Export concept graph nodes as Obsidian notes with
wikilinks for edges. Community clusters map to Obsidian folders. Enables seamless
flow from AITP concept graphs to the researcher's existing knowledge vault.
**Axis:** A1 (L1 internal — export is a layer capability)
**Phase:** 165.5 (plan 165.5-03)
**Files:** New `obsidian_graph_export.py`
**Borrowed patterns:** Graphify's vault export format, Obsidian wikilink + embed
  syntax from existing AITP Obsidian integration skills
**Source:** Graphify + Obsidian integration analysis 2026-04-14

### 999.85: MIT Attribution for Integrated DeepXiv and Graphify Code

**Goal:** Add copyright notice comments in all AITP source files that borrow code
or design patterns from Graphify or DeepXiv SDK. Add both projects to AITP's
NOTICE/LICENSE file with full MIT license text. This is a legal requirement under
MIT License — must preserve copyright notices and license text.
**Axis:** A3 (data recording — license/attribution metadata)
**Phase:** 165.5 (plan 165.5-01 — done early to ensure compliance from start)
**Files:** All new files from 999.79–999.84, existing `NOTICE` or `LICENSE` file
**Source:** MIT License compliance requirement 2026-04-14

### 999.86: Concrete L0 Source-Acquisition Handoff After Public Bootstrap

**Goal:** When a fresh public bootstrap honestly returns a topic to `L0 source
expansion`, the selected next action should point to the concrete shipped source
entry surfaces (`discover_and_register.py`, `register_arxiv_source.py`,
`ARXIV_FIRST_SOURCE_INTAKE.md`) instead of generic prose about converting the
topic statement into sources and candidates.
**Axis:** A4 (human experience) + A2 (L0→L1 connection)
**Status:** Implemented in `v1.92` Phase `166`
**Phase:** `166`
**Plan:** `166-01`
**Files:** `topic_shell_support.py`, `runtime_bundle_support.py`,
  `topic_dashboard_surface_support.py`, related CLI/runtime tests
**Source:** public-front-door closure run 2026-04-13

## wow-harness Comparison Summary (2026-04-13)

**Repo**: https://github.com/NatureBlueee/wow-harness
**Domain**: AI agent governance for software development (Claude Code)
**Core insight**: "CLAUDE.md instruction compliance: ~20% / PreToolUse hook enforcement: 100%"
**Key borrowable patterns**: 999.73–999.78 above
**Architecture**: 16 hooks across 7 lifecycle stages, 17 context fragments with
path-scoped injection, 15 guard scripts, 16 skills, 8-gate state machine,
self-evolving via JSONL metrics → trace-analyzer → proposals

### Key Difference

wow-harness enforces via **mechanical hooks** (Python scripts that block/allow
tool calls). AITP enforces via **layer promotion gates** (L3→L4→L2 audits).
Both are trust-boundary systems, but wow-harness's approach is more
deterministic and zero-LLM-cost for mechanical checks. The borrowable insight:
use mechanical checks first, LLM evaluation only when mechanical passes.

## AI Scientist Benchmark Alignment (2026-04-14)

**Source**: AI Scientist Benchmark PDF — a structured framework for evaluating
AI research capabilities along two axes: paper search (expert-level literature
relevance grading) and paper understanding (structured knowledge extraction
with conditions, motivations, and open problems).

**Core insight**: The benchmark defines a granular knowledge-extraction standard
that AITP's current L0/L1/L3 layers do not yet match. Specifically:
- source-item has no relevance tier or role labels
- candidate-claim has no knowledge type distinction (conclusion vs motivation vs open problem)
- candidate-claim does not require conditions/assumptions
- evidence tracing is section-level, not sentence-level
- L4 validation has no condition-understanding completeness dimension

These gaps mean AITP's knowledge extraction is structurally weaker than what
the benchmark treats as the minimum for evaluating AI research competence.

**Milestone proposal**: `.planning/backlog/999.87-ai-scientist-benchmark-alignment/CONTEXT.md`
— proposed `v1.96` with 5 phases (A–E), dependency graph, and success criteria.

**Borrowable patterns (999.87–999.92)**:

### 999.87: Source Relevance Tier and Role Labels

**Goal:** Add expert-grade relevance classification to `source-item.schema.json`.
Introduce a five-tier relevance scale (`canonical`, `must_read`,
`strongly_relevant`, `useful`, `irrelevant`) and an open vocabulary of role
labels (`foundational`, `key_result`, `modern_reference`, `review`,
`technical_tool`, `limitation`, `application_connection`) so that L0 sources
carry structured relevance metadata beyond simple acquire/pending status.

**Motivation:** AITP's L0 currently distinguishes acquired vs pending sources
but provides no structured judgment about which sources are core, which are
supplementary, and which serve specific roles (foundational, technical tool,
review, etc.). This means the L0→L1 transition treats all acquired sources
equally, which is not how researchers actually triage literature.

**Axis:** A1 (L0 internal capability) + A2 (L0→L1 connection — relevance
tier directly informs which sources deserve deep L1 reading)
**Files:** `schemas/source-item.schema.json`, runtime mirror, L0 intake
helpers, `source_catalog_support.py`, runtime bundle surfaces
**Source:** AI Scientist Benchmark §3.4 (relevance tiers 3+/3/2/1/0) and
§3.6 (role labels)

### 999.88: Candidate Knowledge Type Trichotomy

**Goal:** Extend `candidate-claim.schema.json` with a `knowledge_type` field
that distinguishes three categories of extractable knowledge:
- `conclusion` — what the paper establishes, under what conditions
- `motivation_insight` — why the paper is worth doing, what difficulty it
  targets, what the central idea or conceptual transformation is
- `open_problem` — where the paper stops, what the most important next step is

Each type would carry type-specific required fields (e.g., conclusions require
`conditions_and_assumptions`; open problems require `boundary_origin`).

**Motivation:** AITP's L3 candidate claims are currently flat — all claims are
treated identically regardless of whether they represent an established result,
a motivating insight, or an unsolved problem. The benchmark's trichotomy is
more aligned with how researchers actually organize their knowledge and would
enable type-specific validation in L4.

**Axis:** A1 (L3 internal — candidate type discrimination) + A2 (L3→L4 —
type-specific validation paths)
**Files:** `schemas/candidate-claim.schema.json`, runtime mirror, candidate
production helpers, validation contract surfaces
**Source:** AI Scientist Benchmark §4.2 (three extraction categories)

### 999.89: Mandatory Conditions and Assumptions on Conclusions

**Goal:** Make `conditions_and_assumptions` a required field for all
candidate claims of type `conclusion`. The field must explicitly state the
regime, model assumptions, parameter ranges, or other prerequisites under
which the claimed result holds. Claims without this field should fail schema
validation.

**Motivation:** The benchmark's strongest design choice is requiring every
conclusion to state its conditions. This directly serves AITP Charter Article
2 (evidence hierarchy) — without condition tracking, "theoretical conclusion"
and "approximation valid only in a specific regime" are indistinguishable.
Current AITP candidate-claim has no such field, so L4 audits cannot check
whether the agent understood the scope of a result.

**Axis:** A1 (L1/L3 internal — extraction quality) + A2 (L3→L4 — condition
completeness as a validation dimension)
**Files:** `schemas/candidate-claim.schema.json`, runtime mirror, candidate
production helpers, L4 validation surfaces
**Source:** AI Scientist Benchmark §4.5.1 (conditions/assumptions mandatory
field)

### 999.90: Sentence-Level Evidence Anchoring

**Goal:** Add sentence-level evidence anchoring to the L1 vault intake path.
Each extracted knowledge unit should carry 1–3 sentence identifiers that
constitute the minimal necessary evidence for that extraction. This refines
AITP's current section-level source tracing to the sentence level.

**Motivation:** The benchmark requires evidence sentence IDs for every
annotated knowledge unit. AITP's current source tracing operates at section
granularity. Sentence-level anchoring makes L4 audits mechanical (does the
claim follow from these sentences?) and directly supports the "evidence before
confidence" charter principle.

**Axis:** A1 (L1 internal — extraction precision) + A3 (data recording —
evidence traceability)
**Files:** L1 vault intake helpers, `l1_source_intake` path, source trace
schema, validation surfaces
**Source:** AI Scientist Benchmark §4.5.1 (evidence sentences, 1–3 IDs)

### 999.91: Multi-Reviewer L4 Cross-Validation Protocol

**Goal:** Introduce a multi-reviewer cross-validation mechanism in L4. When a
candidate claim reaches L4 validation, it should be evaluated by at least two
independent reviewer passes (e.g., different LLM calls with different system
prompts). Claims where reviewers disagree should be flagged for human
escalation. Higher-importance claims get weighted more in the aggregate score.

**Motivation:** The benchmark uses three fixed AI reviewer models to evaluate
consistency with expert annotations, weighting higher-importance items more.
AITP's current L4 is single-path. Multi-reviewer cross-validation would make
the L4→L2 promotion gate more robust and catch single-reviewer blind spots.

**Axis:** A1 (L4 internal — validation quality) + A2 (L4→L2 — gate robustness)
**Files:** L4 validation contract, validation helpers, promotion gate surfaces
**Source:** AI Scientist Benchmark §5 (three fixed AI reviewers, importance
weighting)

### 999.92: Expert Annotation Attachment on L2 Knowledge

**Goal:** Allow L2 promoted knowledge items to carry structured expert
annotations — including relevance tier, role labels, short comments, and key
points — that were either provided by the human during the promotion gate or
imported from external benchmark data. This makes L2 knowledge traceable to
human expert judgment rather than only AI-generated summaries.

**Motivation:** The benchmark's expert annotations are themselves high-value
data. If AITP can attach expert-level annotations to L2 items, then promoted
knowledge becomes anchored to human judgment rather than purely AI-synthesized
summaries. This directly improves L2 reusability and trustworthiness.

**Axis:** A2 (L4→L2 — promotion enrichment) + A4 (human experience —
annotation workflow)
**Files:** L2 compiler helpers, promotion contract, `knowledge-packet.schema.json`
**Source:** AI Scientist Benchmark §4.5 (structured annotation template)

## Legacy Note

### Legacy: L2 Knowledge Compiler And Hygiene

**Status:** Retained for reference only.
**Why kept:** This older backlog note predates the shipped `v1.5` milestone and
the later conceptual L2 graph audit. It is now superseded by the newer L2
backlog cluster above, but its context may still be useful when selecting a
future milestone.
**Context:** `.planning/backlog/legacy-l2-knowledge-compiler-and-hygiene/`
