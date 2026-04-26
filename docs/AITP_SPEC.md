# AITP Specification v4

Status: authoritative specification, subordinate to CHARTER.md.
Last updated: 2026-04-26.
Version: 4.0 (brain-driven, skill-first, file-system state, domain-skills).

This document is the single specification that bridges the Charter to the
protocol tree. Every sub-protocol must be consistent with this SPEC.
If a conflict arises, Charter overrides SPEC, SPEC overrides sub-protocols,
sub-protocols override implementation.

---

## S1. Identity

AITP (AI-Verified Theoretical Physics) is a research protocol and runtime
system that turns an AI coding agent into a disciplined theoretical-physics
research collaborator.

The discipline has three parts:

1. **Evidence discipline** — distinguish what is known, derived, conjectured,
   and speculative. Never merge them silently.
2. **Artifact discipline** — if a research step matters, it exists as a
   durable, inspectable artifact on disk, not only in conversation memory.
3. **Promotion discipline** — reusable knowledge is earned through explicit
   validation, not assumed by default.

## S2. Three-Phase Roadmap

The Charter preamble declares three phases. This section specifies what each
phase demands from the protocol architecture.

### Phase 1 — Research Workflow Tool (current)

The system operates as a human-in-the-loop research tool. The human:
- opens and scopes topics,
- steers research direction,
- approves L2 promotion,
- validates or overrides AI judgment at any point.

AITP's role is disciplined execution: literature analysis, derivation checking,
code execution, structured note-taking, and knowledge accumulation.

Protocol requirements for Phase 1:
- full L0-L4 layer pipeline with L2 knowledge graph endpoint,
- explicit human checkpoints at L2 promotion and direction changes,
- durable topic state across sessions,
- markdown-only storage (YAML frontmatter for structured data),
- skill-driven workflow with minimal Python.

### Phase 2 — Learning Collaborator

AITP accumulates enough research history to begin reusing patterns,
anticipating needs, and recognizing when a new topic resembles past work.

Additional requirements for Phase 2:
- cross-topic knowledge retrieval and reuse,
- collaborator memory: research taste, preferred formalisms, physical intuition,
- strategy memory: which approaches succeeded or failed,
- progressive autonomy within established patterns (human still gates novelty).

### Phase 3 — Autonomous Physicist

AITP independently proposes research directions, explores new mathematics,
tests ideas against experiments, and pursues truth creatively.

Additional requirements for Phase 3:
- self-directed topic creation with human notification (not pre-approval),
- novel hypothesis generation and self-validation loops,
- experimental-theory bridge: testing predictions against data,
- research creativity within Charter constraints.

**Phase gate rule:** A phase is not declared complete until its protocol
requirements are implemented, tested, and validated against real research
topics. Phase 3 must not be entered until Phase 2 collaborator memory has
demonstrated genuine cross-topic reuse across at least five distinct topics.

## S3. Layer Model

AITP organizes research state into six content layers plus two cross-cutting
planes.

### Content Layers

| Layer | Name | Purpose | Trust Level |
|-------|------|---------|-------------|
| L0 | Source substrate | Register and trace every input | Source-grounded |
| L1 | Provisional understanding | Assumption extraction, concept mapping | Untrusted |
| L2 | Canonical knowledge | Reusable, promoted results | Trusted |
| L3 | Candidate workspace | Idea→plan→candidate pipeline | Untrusted |
| L4 | Validation & adjudication | Explicit verification | Audit surface |

**Default route:** L0 -> L1 -> L3 -> L4 -> L2

**L5 (writing/publication) is removed in v4.0.** L2 is the endpoint.
The knowledge graph itself is the output. Paper writing is the human's work.

**Low-risk shortcut (Path A):** L0 -> L2 directly, via `aitp_quick_l2_concept`.
For well-understood concepts with clear sources.

**Routing rule:** The runtime may not silently skip L3 candidate formation or
L4 validation when the protocol says they are required.

### Cross-Cutting Planes

| Plane | Name | Purpose |
|-------|------|---------|
| B | Brain | MCP server providing tools + skill injection + hooks |
| H | Human | Checkpoints, steering, approval, override at any layer |

The Brain plane is NOT a content layer. It does not store knowledge. It provides
tools for the agent to read/write topic state, and injects skills that enforce
the AITP workflow. Brain is an MCP server providing tools for each
protocol stage plus L2 knowledge graph operations.

The Human plane does not replace protocol discipline. Human approval is a gate,
not a substitute for validation.

### Layer-Specific Details

**L0 — Source Acquisition**
- Register papers, PDFs, URLs, transcripts, conversations, local notes,
  code references.
- Source fidelity grading: peer-reviewed > arXiv preprint > blog > informal
  notes > verbal claims.
- Relation labeling: extracted / inferred / ambiguous.
- Citation graph traversal and BibTeX support.
- L0 never claims anything is true. It only records provenance and fidelity.

**L1 — Provisional Understanding**
- Assumption extraction (structural, not keyword-based).
- Reading depth tracking (scan / close-read / multi-pass cross-check).
- Contradiction detection and notation regime identification.
- Source provenance, intake analysis, and source-anchor mapping for later L3 reconstruction.
- Every claim in L1 is marked "provisional."

**L2 — Canonical Knowledge**
- Reusable typed knowledge objects (concepts, definitions, theorems,
  derivations, methods, equations, notation, warnings, bridges).
- Stored as Markdown files with YAML frontmatter.
- Deterministic projections: indexes and portal.
- Requires explicit promotion gate. No automatic writes.

**L3 — Candidate Workspace**
- Sub-planes: L3-I (ideation), L3-P (planning), L3-A (analysis),
  L3-R (result integration), L3-D (distillation).
- L3-I: idea workspace — record, connect, refine vague ideas before they
  become formal candidates.
- L3-P: plan artifacts — executable research plans with steps, tool needs,
  and knowledge requirements derived from L2.
- L3-A: candidate formation — formal claims with evidence and assumptions.
- L3 is the unified detailed-derivation home, including source reconstructions
  and novel candidate derivations.
- Notebook-facing L3 rounds must declare a scientific `round_type`, satisfy the
  required obligation blocks for that round, and record missing obligations
  honestly enough to block or qualify claim use when necessary.
- Cross-round obligations such as convention ledgers, source-anchor tables, and
  failure-route notes are triggered by content and must flow into unfinished
  work when missing.
- L3-R: interpret L4 results, decide routing.
- L3-D: prepare material for promotion.
- Conjectures, source reconstructions, failed attempts, candidate derivations, anomalies,
  negative results.
- Material here may become reusable IF it passes L4 and L2 promotion.

**L4 — Validation & Adjudication**
- Numerical validation (benchmark runs, convergence checks).
- Analytical validation (limiting cases, dimensional analysis, symmetry,
  self-consistency).
- Symbolic/analytical reasoning paths (SymPy/Mathematica lanes).
- Trust audit with explicit trust-boundary documentation.
- **Hard rule:** L4 does not write directly to L2. All L4 results return
  through L3-R. This prevents validated-but-misinterpreted results from
  entering trusted knowledge.

## S4. Brain Plane (B)

The Brain is an MCP server providing tools for the agent to read/write
topic state, and skills that enforce the AITP workflow. The agent calls
tools at key workflow points, guided by skills and the execution brief.

### Brain Design Principles

1. **Tools for state access.** The Brain provides ~60 MCP tools organized by
   protocol stage (L0-L4) plus cross-cutting utilities. The agent decides
   when to call them. The Brain does not run autonomous loops.
2. **Skills for workflow.** Workflow logic (what to do at each layer, how to
   validate, when to promote) lives in Markdown skills that the agent reads.
   Gate logic lives in `state_model.py` as structured checks.
3. **Hooks for continuity.** SessionStart, Compact, and Stop hooks ensure the
   agent re-enters the correct workflow after context resets.

### Brain Architecture

```
Human Researcher
    |
    v
+-----------------------------------------------------+
|              H-Plane (Human Interaction Layer)        |
|  Intervene at any layer: redirect, approve, correct, |
|  pause, or approve L2 promotion                      |
+-----------------------------------------------------+
               |
+--------------v----------------------------------------+
|              Brain MCP Server (~5100 lines Python)    |
|                                                       |
|  Stage tools:                                         |
|  +-- aitp_bootstrap_topic: create topic + scaffolds  |
|  +-- aitp_register_source / aitp_list_sources        |
|  +-- aitp_parse_source_toc / aitp_write_section_intake|
|  +-- aitp_get_execution_brief: gate status + next step|
|  +-- aitp_submit_candidate / aitp_submit_l4_review   |
|  +-- aitp_request_promotion / aitp_promote_candidate  |
|  +-- aitp_advance_to_l1 / _l3 / aitp_retreat_to_*    |
|                                                       |
|  L2 knowledge graph:                                  |
|  +-- aitp_query_l2_index / aitp_query_l2_graph       |
|  +-- aitp_create_l2_node / _edge / _tower            |
|  +-- aitp_quick_l2_concept (Path A shortcut)         |
|                                                       |
|  Verification:                                        |
|  +-- aitp_verify_dimensions / _algebra / _limit       |
|  +-- aitp_verify_derivation_step / _chain            |
|                                                       |
|  Skills (Markdown, 22 files):                         |
|  +-- skill-discover.md (L0) / skill-read.md (L1)     |
|  +-- skill-frame.md (L1) / skill-l3-*.md (L3 x8)    |
|  +-- skill-validate.md (L4) / skill-write.md         |
|  +-- skill-continuous.md (resume)                     |
|                                                       |
|  Hooks:                                               |
|  +-- SessionStart: inject using-aitp skill            |
|  +-- UserPromptSubmit: keyword routing to AITP        |
|  +-- PreToolUse: guard against topic file bypass      |
|  +-- Stop: save progress to state.md                  |
+--------------+----------------------------------------+
               |
        +------+------+------+------+
        |      |      |      |      |
        v      v      v      v      v
      +--+  +--+  +--+  +--+  +-----+
      |L0|  |L1|  |L3|  |L4|  | L2  |
      +--+  +--+  +--+  +--+  +-----+
      (Markdown with YAML frontmatter;
       numerical data may use JSON)
```

### Skill Injection

Skills are loaded by the agent platform (Claude Code hooks, Kimi Code skills).
The `using-aitp` skill activates on theoretical-physics requests and routes
into the protocol. The `aitp-runtime` skill executes the stage-driven loop:

| Stage | Skill | Agent Does |
|-------|-------|------------|
| L0 | skill-discover | Search literature, register sources |
| L1 (read) | skill-read | TOC-first reading, per-section intake |
| L1 (frame) | skill-frame | Frame question, map anchors, register contradictions |
| L3 | skill-l3-* | Flexible workspace: ideate, derive, gap-audit, connect, integrate, distill |
| L4 | skill-validate | Adversarial review, dimensional analysis, limiting cases |
| L2 | skill-promote | Submit for human approval, promote to L2 |
| any (resume) | skill-continuous | Resume from `aitp_get_execution_brief` |

The agent reads the injected skill and follows it. `aitp_get_execution_brief`
is the primary orientation tool — call it before deciding what to do next.

### Brain Protocol Reference

See: `brain/PROTOCOL.md`

## S5. Human Plane (H)

The Human plane provides structured interaction points where the human
researcher can steer, approve, correct, or pause the system at any layer.

### H Responsibilities

1. **Checkpoint** — pause at any point for human review.
2. **Update** — modify direction, scope, or assumptions mid-flow.
3. **Approve** — gate L2 promotion, approve publication.
4. **Override** — acknowledge a stuckness signal and choose to continue.
5. **Clarify** — resolve ambiguity when the research question is underspecified.

### H Gate Policy

- L2 promotion always requires human approval.
- Direction changes and scope modifications are human-initiated.
- The system may request human input at any decision point.
- Human guidance is not a protocol failure (Charter Article 8).
- The system may auto-progress through bounded steps within an approved plan,
  but must re-checkpoint when the plan boundary is reached.

### H Protocol Reference

See: `docs/protocols/H_human_interaction.md`

## S6. Mode Envelope

The Brain operates in one of three modes. Each mode represents a distinct
research activity and constrains which layers the agent may work in, what
transitions are allowed, and what writeback is required.

The three modes correspond to the core cognitive cycle of physics research:
discover ideas, verify understanding, create new results.

| Mode | Purpose | Foreground Layers | L3 Focus | Key Constraints |
|------|---------|-------------------|----------|-----------------|
| `explore` | Discover literature, record ideas | L0, L1, L3 | L3-I | No formal candidates, compare with L2 |
| `learn` | Study literature, verify known results | L0, L1, L3, L4 | L3-P, L3-A | L3↔L4 loop for derivation/numerical verification, results promote to L2 |
| `implement` | Pursue new ideas, produce novel results | L3, L4 | L3-I→L3-P→L3-A | L3↔L4 loop, new conclusions in L3 for human review |

**L2 promotion** is NOT a separate mode. It is an operation triggered within
`learn` (verified knowledge) or `implement` (novel results) when candidates
pass validation and are ready for human approval.

Mode transitions are enforced by skills, not by Python code. The skill for the
current mode defines when transition is appropriate and what writeback is
required.

Valid transition graph:

```
explore -> learn -> implement -> explore
  ^          |          |
  |          v          v
  +----------+----------+
       (backward transitions)
```

### Mode Protocol Reference

See: `docs/protocols/mode_envelope_protocol.md`

## S7. Skill-Driven Workflow

In v2, the closed-loop state machine (v1) is replaced by a skill-driven
workflow. The agent reads the appropriate skill and follows it.

### Workflow Cycle

```
1. SessionStart hook fires → injects using-aitp skill
2. Agent reads using-aitp skill → routes theory requests into AITP
3. Agent calls aitp_list_topics or aitp_bootstrap_topic
4. Agent calls aitp_get_execution_brief → reads stage, gate, next action
5. Agent loads the stage-appropriate skill and follows it
6. Agent calls MCP tools to record results, create artifacts
7. Agent calls aitp_get_execution_brief again → checks gate, advances stage
8. If session ends: Stop hook saves progress
9. Next session resumes from aitp_session_resume or aitp_get_execution_brief
```

### Skill Responsibilities

Each skill defines:
- **What to do** at this workflow stage
- **Which MCP tools to call** and when
- **What artifacts to produce** (Markdown files)
- **When to transition** to the next stage
- **What writeback is required** before transitioning

### What Skills Replace

| v1 Component | v2 Replacement |
|-------------|----------------|
| orchestrate_topic.py | skill-explore / skill-derive |
| decide_next_action.py | skill-continuous reads state.md |
| closed_loop_v1.py | skill-validate + skill-derive |
| advance_closed_loop.py | skill-continuous |
| action_queue_protocol.md | skill step-by-step instructions |
| runtime bundle (generated JSON) | injected skill (Markdown) |

## S8. Promotion Pipeline

L2 promotion follows a skill-driven flow:

1. Agent determines candidate is ready (skill-validate criteria met).
2. Agent calls `aitp_request_promotion(topic_slug, candidate_id)`.
3. Brain updates `candidate.md` frontmatter: `status: pending_approval`.
4. Agent asks human for approval (popup gate).
5. On approval: agent calls `aitp_update_status` to set `status: promoted`.
6. Agent writes the knowledge to L2 as a new `.md` file.

### Promotion Trace

Every promotion must leave a trace in the candidate file's frontmatter:
- validation results that supported the promotion,
- human approval record,
- resulting L2 file path.

### Promotion Protocol Reference

See: `docs/protocols/promotion_pipeline.md`

## S9. Followup Lifecycle

Topics may spawn child sub-topics and may park deferred candidates.

### Sub-topic Spawning

- A parent topic may spawn a child when the research question splits,
  a gap requires separate investigation, or an external consultation is needed.
- Each child is a separate topic directory with its own `state.md`.
- On completion, the child's results are noted in the parent's state.

### Deferred Candidate Buffer

- Candidates that are not yet actionable may be parked in `L3/deferred.md`
  with reactivation conditions.
- Deferred candidates are not forgotten. They remain inspectable.

### Followup Protocol Reference

See: `docs/protocols/followup_lifecycle.md`

## S10. Storage

AITP stores **protocol state** (topic artifacts, knowledge graph, gate state)
as Markdown files with YAML frontmatter. One file serves both human readability
and structured data access.

### Protocol State Format

Every protocol artifact follows this structure:

```markdown
---
key1: value1
key2: value2
created_at: 2026-04-19T10:00:00
---

# Title

Human-readable content here.
```

- **YAML frontmatter** holds structured/queryable data.
- **Markdown body** holds human-readable content (narrative, notes, derivations).
- The MCP server reads frontmatter with a YAML parser.
- The agent can read the full file naturally.

### Collections

For list-type data (sources, candidates, derivations), use one of:
- **One file per item** in a directory (e.g., `L0/sources/hs-1988.md`).
- **Single file with sections** for append-only logs.

### Numerical Data

Numerical computation outputs (configs, benchmark results, scan data) may use
JSON. These are runtime artifacts, not protocol state. Protocol state (gates,
contracts, knowledge graph nodes) remains Markdown + YAML.

### Why Markdown for Protocol State

- AI agents parse Markdown as naturally as JSON.
- YAML frontmatter is queryable and typed.
- Humans can read and edit everything with any text editor.
- No paired-backend synchronization required.

## S11. Control Axes

The Brain uses six control axes to determine runtime behavior:

| Axis | Role | Values |
|------|------|--------|
| `runtime_mode` | Core driver — what the agent is doing | explore, learn, implement |
| `transition_posture` | Core driver — how the agent transitions | forward, backedge, lateral, pause |
| `layer` | Where the work happens | L0, L1, L2, L3, L4 |
| `L3_subplane` | L3 sub-plane if relevant | ideation, planning, analysis, result_integration, distillation |
| `lane` | Research domain | formal_theory, model_numeric, code_and_materials |
| `task_type` | Research intent | open_exploration, conjecture_attempt, target_driven |

Only `runtime_mode` and `transition_posture` are core drivers. The rest are
auxiliary context that shapes behavior within the current mode.

## S12. Adapter Interface

Agent platforms execute AITP through adapters. In v2, adapters are thin:
they load skills, configure hooks, and connect to the MCP server.

### Adapter Obligations

1. **Connect to Brain MCP** — configure the MCP server endpoint.
2. **Load skills at session start** — inject `using-aitp` and `aitp-runtime`
   skills via platform-native mechanisms (Claude Code hooks, Kimi Code skills).
3. **Configure hooks** — SessionStart, Compact, Stop.
4. **Handle popups** — present blocker questions to the human via
   `AskUserQuestion`.
5. **Produce artifacts** — every AITP session must leave protocol artifacts.
6. **Respect the Charter** — may not weaken evidence, artifact, or promotion
   discipline.

### Adapter Categories

1. **Platform adapters** — connect AITP to agent platforms (Claude Code,
   Kimi Code).
2. **Domain skills** — connect AITP to domain-specific physics capabilities
   (e.g., GW workflows, DFT codes). Domain skills are Markdown files with
   domain-specific templates and validation criteria.

### Adapter Protocol Reference

See: `docs/protocols/adapter_interface.md`

## S13. Conformance and Trust

### Conformance

A conformant run means the agent followed the Charter and protocol surface.
It does not guarantee the science is correct.

Conformance checks (enforced by skills, not Python):
- required artifacts exist and are well-formed Markdown,
- promotion gates were respected,
- evidence levels were not silently merged,
- uncertainty markers were preserved,
- mode envelopes were followed.

### Trust Gates

New operations, methods, or backends are not trusted until relevant trust
gates are satisfied (Charter Article 6). Trust gates include:
- capability audit — can the runtime actually do what is requested?
- validation audit — has the method been tested against known results?
- execution provenance — where did the heavy execution happen?

## S14. Protocol Domain Structure

All sub-protocols are organized into three domains:

### Brain Domain — Global Orchestrator

| Protocol | File | Purpose |
|----------|------|---------|
| Brain protocol | `docs/protocols/brain_protocol.md` | MCP tools, skill injection, hooks |

### Point Domain — Layer-Specific Protocols

| Protocol | File | Purpose |
|----------|------|---------|
| L1 intake protocol | `docs/protocols/L1_intake_protocol.md` | Assumption extraction, reading depth |
| L2 backend interface | `docs/protocols/L2_backend_interface.md` | Canonical knowledge, promotion |
| L3 execution protocol | `docs/protocols/L3_execution_protocol.md` | Ideation, planning, candidate formation |
| Topic notebook obligation protocol | `docs/protocols/TOPIC_NOTEBOOK_OBLIGATION_PROTOCOL.md` | Round types, obligation closure, claim-readiness, physicist-facing notebook ordering |
| L4 validation protocol | `docs/protocols/L4_validation_protocol.md` | Validation types, trust audit |
| Closed loop protocol | `docs/protocols/closed_loop_protocol.md` | L3↔L4 iterative verification loop |
| Promotion pipeline | `docs/protocols/promotion_pipeline.md` | Promotion flow and gates |

### Interaction Domain — Cross-Cutting Protocols

| Protocol | File | Purpose |
|----------|------|---------|
| Human interaction | `docs/protocols/H_human_interaction.md` | Checkpoints, steering, approval |
| Mode envelope | `docs/protocols/mode_envelope_protocol.md` | 3 modes, transitions |
| Adapter interface | `docs/protocols/adapter_interface.md` | Platform adapter obligations |

### Skills — Workflow Instructions

| Skill | File | Purpose |
|-------|------|---------|
| skill-discover | `skills/skill-discover.md` | L0: discover and register sources |
| skill-read | `skills/skill-read.md` | L1 read: TOC-first reading, section intake |
| skill-frame | `skills/skill-frame.md` | L1 frame: question contract, convention snapshot |
| skill-l3-* | `skills/skill-l3-*.md` | L3: ideate, plan, analyze, gap-audit, integrate, distill |
| skill-validate | `skills/skill-validate.md` | L4: adversarial validation |
| skill-promote | `skills/skill-promote.md` | L2 promotion |
| skill-continuous | `skills/skill-continuous.md` | Resume after session break |

## S15. Execution Surface Provenance

If a canonical writeback depends on nontrivial execution, the upstream runtime
or note set must record the execution host and why it was chosen.

- Local Windows host: AI orchestration, human-facing curation, lightweight
  smoke tests.
- Remote hosts: default AITP execution surface for model-side numerical checks
  and script-driven validation.

Host choice is part of trust provenance, not incidental commentary.

## S16. Charter Coverage

Every Charter article is enforced by specific protocol surfaces:

| Charter Article | Enforced By |
|-----------------|-------------|
| Art. 1 — Truth over fluency | Evidence discipline (S1), mode envelopes (S6) |
| Art. 2 — Evidence hierarchy | L0 fidelity grading, L1 assumption extraction |
| Art. 3 — Layered state | Layer model (S3), markdown storage (S10) |
| Art. 4 — Contracts over hidden state | Artifact discipline (S1), conformance (S13) |
| Art. 5 — Earned promotion | Promotion pipeline (S8), L2 gate |
| Art. 6 — Conditional tool trust | Trust gates (S13), capability audit |
| Art. 7 — Uncertainty survives | Gap recovery, deferred candidates |
| Art. 8 — Human checkpoints | H plane (S5), popup gate protocol |
| Art. 9 — Enforceable conformance | Conformance checks (S13), adapter obligations (S12) |
| Art. 10 — Adapters don't redefine | Adapter interface (S12), charter-first rule |

## S17. Filesystem Convention

```
aitp-v2/
├── docs/
│   ├── CHARTER.md                     # Highest authority
│   ├── AITP_SPEC.md                   # This document
│   ├── design-principles.md           # Design principles
│   └── protocols/                     # Protocol documents
│       ├── brain_protocol.md          # B plane: MCP tools, skills, hooks
│       ├── L1_intake_protocol.md      # L1 layer
│       ├── L2_backend_interface.md    # L2 canonical knowledge
│       ├── L3_execution_protocol.md   # L3 candidate workspace
│       ├── L4_validation_protocol.md  # L4 validation surface
│       ├── promotion_pipeline.md      # Promotion flow and gates
│       ├── H_human_interaction.md     # H plane gates
│       ├── mode_envelope_protocol.md  # 3-mode envelopes
│       └── adapter_interface.md       # Platform adapter obligations
├── brain/
│   └── mcp_server.py             # MCP server (60+ tools)
├── skills/
│   ├── skill-discover.md              # L0 source discovery
│   ├── skill-read.md                  # L1 TOC-first reading
│   ├── skill-frame.md                 # L1 question framing
│   ├── skill-l3-*.md                  # L3 flexible workspace (8 files)
│   ├── skill-validate.md              # L4 validation
│   ├── skill-promote.md               # L2 promotion
│   └── skill-continuous.md            # Session resume
├── hooks/
│   ├── session_start.py               # Inject skill at session start
│   ├── compact.py                     # Re-inject skill after compaction
│   └── stop.py                        # Save progress at session end
├── adapters/                          # Platform-specific configs
├── schemas/                           # Markdown format examples
└── topics/                            # Topic instances (runtime)
    └── <topic-slug>/
        ├── state.md                   # Topic state (frontmatter: status, mode, etc.)
        ├── L0/
        │   └── sources/
        │       ├── hs-1988.md         # Per-source file
        │       └── yang-1993.md
        ├── L1/
        │   └── intake/
        │       ├── hs-1988.md         # Per-source intake notes
        │       └── yang-1993.md
        ├── L2/
        │   └── canonical/
        │       ├── def-spin-operator.md   # Promoted knowledge units
        │       └── thm-hs-integrable.md
        ├── L3/
        │   ├── derivations.md         # All derivation records (append)
        │   ├── candidates/
        │   │   └── level-spacing.md   # Per-candidate file
        │   └── deferred.md            # Deferred candidates
        ├── L4/
        │   └── reviews/
        │       └── level-spacing.md   # Per-candidate validation record
        └── runtime/
            └── control_note.md        # Human directives
```

All files are Markdown. No JSON. No JSONL. No paired backend.

### Topic state.md Format

```markdown
---
topic_slug: hs-chaos-window
title: Haldane-Shastry Chaos Window
status: intake_done
mode: learn
layer: L3
created_at: 2026-04-19T10:00:00
updated_at: 2026-04-19T15:30:00
sources_count: 3
candidates_count: 1
---

# HS Chaos Window

## Research Question
What is the nature of the chaotic window in the Haldane-Shastry model?

## Current Focus
Analyzing level spacing distributions from numerical data.
```
