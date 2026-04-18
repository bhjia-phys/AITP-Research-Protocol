# AITP Specification

Status: authoritative specification, subordinate to CHARTER.md.
Last updated: 2026-04-17.

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
- full L0-L5 layer pipeline,
- explicit human checkpoints at L2 promotion and direction changes,
- durable topic state across sessions,
- paired backend (human-readable + typed store),
- adapter support for multiple agent platforms.

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
| L5 | Writing & publication | Paper writing based on topic results | Output |

**Default route:** L0 -> L1 -> L3 -> L4 -> L2

**Low-risk shortcut:** L0 -> L1 -> L2 (requires explicit justification)

**Routing rule:** The runtime may not silently skip L3 candidate formation or
L4 validation when the protocol says they are required.

### Cross-Cutting Planes

| Plane | Name | Purpose |
|-------|------|---------|
| B | Brain | Global orchestrator: routing, cross-topic memory, human gates |
| H | Human | Checkpoints, steering, approval, override at any layer |

The Brain plane is NOT a content layer. It does not store knowledge. It routes,
coordinates, and manages the lifecycle of topics across the content layers.

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
- Typed edges for semantic and workflow relations.
- Deterministic projections: indexes and portal.
- Graph traversal, wiki compilation, cross-topic retrieval.
- Paired backend: human-readable Markdown + typed JSON/JSONL store.
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
- Derivation-heavy candidates become promotion-ready only after they carry a
  detailed L3 derivation record plus an explicit L2 comparison receipt; formal
  theorem/proof candidates also need theory-packet proof surfaces.
- L3-R: interpret L4 results, decide routing.
- L3-D: prepare material for promotion.
- Conjectures, source reconstructions, failed attempts, candidate derivations, anomalies,
  negative results.
- Scratch mode for quick speculative work.
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

**L5 — Writing & Publication**
- Paper drafts, slides, and other publication artifacts.
- Draws from L2 (validated knowledge) and L3 (new results pending review).
- L5 outputs are NOT automatically trusted — human review required before
  external submission.
- See: `docs/protocols/L5_writing_protocol.md`

## S4. Brain Plane (B)

The Brain is the global orchestrator that the AI agent permanently resides in.
It manages the lifecycle of topics, routes decisions, and maintains cross-session
continuity.

### Brain Responsibilities

1. **Topic lifecycle** — bootstrap, loop, status, verify, promote, complete.
2. **Cross-topic routing** — schedule, prioritize, detect dependencies between
   topics.
3. **Human interaction gates** — popups, decision points, checkpoints.
4. **Session continuity** — session chronicle, resume state, trajectory memory.
5. **Collaborator memory** — research taste, preferred formalisms, patterns.
6. **Control plane** — pause, redirect, scope changes, innovation direction.
7. **Mode and posture** — select runtime mode, enforce mode envelopes.

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
|              Brain Plane (B)                           |
|                                                       |
|  Topic Lifecycle Manager                              |
|  +-- bootstrap -> mode-driven loop -> complete        |
|  +-- multi-topic parallel, pause/resume               |
|  +-- bounded auto-steps                               |
|                                                       |
|  Mode Workflow (built-in research process)            |
|  +-- explore:  L0 -> L1 -> L3-I (discover & record)  |
|  +-- learn:    L0-L1 -> L3-A <-> L4 (verify known)   |
|  +-- implement: L3-I -> L3-P -> L3-A <-> L4 (new)    |
|  +-- mode transitions drive topic progression         |
|                                                       |
|  Action Router                                        |
|  +-- select_route -> materialize_task                 |
|  +-- ingest_result -> await_external_result           |
|  +-- heuristic + control-note + contract modes        |
|                                                       |
|  Memory                                               |
|  +-- collaborator profile                             |
|  +-- strategy memory (helpful/harmful patterns)       |
|  +-- research trajectory (cross-session arc)          |
|  +-- mode learning                                    |
|  +-- deferred candidate buffer                        |
+--------------+----------------------------------------+
               |
        +------+------+------+------+------+
        |      |      |      |      |      |
        v      v      v      v      v      v
      +--+  +--+  +--+  +--+  +-----+ +-----+
      |L0|  |L1|  |L3|  |L4|  | L2  | | L5  |
      +--+  +--+  +--+  +--+  +-----+ +-----+
```

### Brain Protocol Reference

See: `docs/protocols/brain_protocol.md`

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

Each mode carries an envelope with:
- `foreground_layers` — which layers the agent works in.
- `allowed_backedges` — which backward transitions are permitted.
- `required_writeback` — what must be written before exiting the mode.
- `forbidden_shortcuts` — transitions that are never allowed in this mode.
- `human_checkpoint_policy` — when human approval is required.
- `entry_conditions` — what must be true to enter this mode.
- `exit_conditions` — what must be true to leave this mode.

Mode transitions are not arbitrary. The valid transition graph is:

```
explore -> learn -> implement -> explore
  ^          |          |
  |          v          v
  +----------+----------+
       (backward transitions)
```

Valid forward transitions:
- `explore -> learn` (idea discovered, ready to study deeply)
- `learn -> implement` (understanding sufficient, ready to pursue new work)
- `implement -> explore` (new questions emerged from results)

Valid backward transitions (require explicit reason and writeback):
- `learn -> explore` (need more source material)
- `implement -> learn` (implementation revealed knowledge gap)
- `implement -> explore` (results suggest different direction)

### Mode Protocol Reference

See: `docs/protocols/mode_envelope_protocol.md`

## S7. Closed-Loop State Machine

Within each topic loop, the Brain executes a bounded closed-loop cycle:

```
select_route -> materialize_task -> ingest_result -> dispatch_execution_task -> await_external_result
      ^                                                                              |
      |                                                                              v
      +------------------------------------------------------------------------------+
```

### select_route
- Load runtime contract for mode-based action preferences.
- Load any frozen decision contracts.
- Load topic state, research question, control note.
- Determine which mode, layer, and action type.
- Check for pending decisions, popups, or human gates.
- Output: a route decision with mode, layer, action, and rationale.

Routing modes: `heuristic`, `control_note`, `declared_contract`, `decision_contract`.

### materialize_task
- Translate the route decision into a concrete action.
- Resolve research mode profile (research_mode, executor_kind, reasoning_profile).
- Prepare inputs (source material, previous results, context).
- Set up validation plan if entering verify mode.
- Output: a materialized task ready for execution.

### ingest_result
- Receive the result of the task (from agent execution or external backend).
- Classify: `success` / `partial` / `failed`, with optional `contradiction_detected` flag.
- Determine routing decision: `keep` / `revise` / `discard` / `defer`.
- Route gaps to gap writeback system and gap recovery.
- Output: classified result with routing decision.

### dispatch_execution_task
- Dispatch the materialized task to the execution target.
- Record dispatch state.

### await_external_result
- If the task requires external execution (numerical, symbolic, remote),
  suspend and await the result.
- Track timeout, failure, and re-entry conditions.
- Output: external result or timeout/failure classification.

### Loop Constraints

- Each cycle must produce at least one durable artifact.
- The loop may not run indefinitely without a human checkpoint.
- Stuckness detection triggers escalation, not silent retry.
- The loop respects the current mode envelope.

### Closed-Loop Protocol Reference

See: `docs/protocols/closed_loop_protocol.md`

## S8. Promotion Pipeline

L2 promotion follows a three-step flow (current implementation) with a
four-stage counting state machine as the aspirational target.

### Current: Three-Step Flow

| Step | Status | Description |
|------|--------|-------------|
| 1 | `pending_human_approval` | Candidate is staged and awaiting review |
| 2 | `approved` | Gate has been approved (human or auto) |
| 3 | `promoted` | Content written to L2 or L2_auto |

### Aspirational: Four-Stage Counting Model

| Stage | Name | Threshold | Description |
|-------|------|-----------|-------------|
| 1 | `candidate` | 0 | Fresh candidate in L3 |
| 2 | `validated` | 2 | Passed L4 validation at least twice |
| 3 | `promotion_ready` | 3 | Validated + integration complete + human not objected |
| 4 | `promoted` | 4 | Human explicitly approved L2 write |

Auto-promotion: when all criteria are met and the topic's trust boundary
permits it, content may be auto-promoted to the `L2_auto` canonical layer
(distinguished from human-reviewed L2 by `review_mode: "ai_auto"`).
Human-reviewed L2 promotion always requires explicit human approval.

### Promotion Protocol Reference

See: `docs/protocols/promotion_pipeline.md`

## S9. Followup Lifecycle

Topics may spawn child sub-topics and may park deferred candidates.

### Sub-topic Spawning

- A parent topic may spawn a child when the research question splits,
  a gap requires separate investigation, or an external consultation is needed.
- The child carries a return packet: what it must deliver back to the parent.
- On completion, the child's results are reintegrated into the parent.

### Deferred Candidate Buffer

- Candidates that are not yet actionable may be parked with reactivation
  conditions:
  - `source_ids_any` — reactivate when any of these sources appear.
  - `text_contains_any` — reactivate when topic text matches.
  - `child_topics_any` — reactivate when any child topic completes.
- Deferred candidates are not forgotten. They remain inspectable.

### Followup Protocol Reference

See: `docs/protocols/followup_lifecycle.md`

## S10. Paired Backend Design

AITP maintains a paired backend: human-readable and machine-readable surfaces
for the same knowledge.

### Human-Readable Backend (Brain Side)

- Markdown-first: research questions, operator consoles, dashboards,
  control notes, innovation directions, session chronicles, gap maps,
  promotion readiness reports.
- The human researcher should be able to read one Markdown-first journal.
- No JSON scraping required for human review.

### Typed Backend (Knowledge Network / open-physics-kb)

- JSON/JSONL canonical store: units, edges, queues, regressions, sources.
- Deterministic projections: indexes, portal.
- Typed retrieval for agents and scripts.
- The typed backend is the machine-facing authority for reusable knowledge.

### Compatibility Rule

- Markdown and JSON are companions, not duplicates.
- Markdown carries narrative and judgment.
- JSON carries stable ids, statuses, triggers, and replay pointers.
- Do not duplicate full narratives in both formats.
- When they conflict on a machine-actionable field, JSON wins.
- When they conflict on a human judgment field, Markdown wins.

## S11. Control Axes

The Brain uses six control axes to determine runtime behavior:

| Axis | Role | Values |
|------|------|--------|
| `runtime_mode` | Core driver — what the agent is doing | explore, learn, implement |
| `transition_posture` | Core driver — how the agent transitions | forward, backedge, lateral, pause |
| `layer` | Where the work happens | L0, L1, L2, L3, L4, L5 |
| `L3_subplane` | L3 sub-plane if relevant | ideation, planning, analysis, result_integration, distillation |
| `lane` | Research domain | formal_theory, model_numeric, code_and_materials |
| `task_type` | Research intent (redundant with mode in practice) | open_exploration, conjecture_attempt, target_driven |

Only `runtime_mode` and `transition_posture` are core drivers. The rest are
auxiliary context that shapes behavior within the current mode.

## S12. Adapter Interface

Agent platforms (Claude Code, Codex, OpenClaw, OpenCode, others) execute AITP
through adapters. Domain-specific physics capabilities (GW workflows, DFT
codes, etc.) plug in through domain skills. Both are protocol executors, not
protocol definers (Charter Article 10).

### Adapter Categories

1. **Platform adapters** — connect AITP to agent platforms (Claude Code, Codex).
2. **Domain skills** — connect AITP to domain-specific physics capabilities
   (e.g., oh-my-LibRPA for ABACUS+LibRPA workflows). Domain skills provide
   domain knowledge, contract schemas, and plan templates through structured
   manifest files, not through API calls.

### Adapter Obligations

1. **Skill loading** — load the `using-aitp` skill at session start.
2. **Front-door routing** — route user requests through AITP's front-door
   before free-form processing.
3. **Artifact production** — leave required AITP artifacts on disk.
4. **Popup handling** — present popups to the human and return choices.
5. **Conformance** — a run claims to be AITP work only if it passes the
   declared conformance checks (Charter Article 9).
6. **No charter redefinition** — adapters may add convenience, but may not
   weaken evidence, artifact, or promotion discipline.

### Adapter Protocol Reference

See: `docs/protocols/adapter_interface.md`

## S13. Conformance and Trust

### Conformance

A conformant run means the agent followed the Charter and protocol surface.
It does not guarantee the science is correct (design principle 10).

Conformance checks include:
- required artifacts exist and are well-formed,
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
| Brain protocol | `docs/protocols/brain_protocol.md` | Topic lifecycle, cross-topic routing, memory, control plane |
| Action queue | `docs/protocols/action_queue_protocol.md` | Next-action decision, queue shaping, auto-progression |
| Followup lifecycle | `docs/protocols/followup_lifecycle.md` | Sub-topic spawning, deferred candidates, reintegration |

### Point Domain — Layer-Specific Protocols

| Protocol | File | Purpose |
|----------|------|---------|
| L0 source layer | `research/knowledge-hub/L0_SOURCE_LAYER.md` | Source registration, fidelity grading, citation graphs |
| L1 intake protocol | `docs/protocols/L1_intake_protocol.md` | Assumption extraction, vault protocol, reading depth |
| L2 backend interface | `docs/protocols/L2_backend_interface.md` | Typed store contract, promotion policy, paired backend |
| L3 execution protocol | `docs/protocols/L3_execution_protocol.md` | Ideation, planning, candidate formation, sub-planes |
| L4 validation protocol | `docs/protocols/L4_validation_protocol.md` | Validation types, trust audit, L4 -> L3-R rule |
| L5 writing protocol | `docs/protocols/L5_writing_protocol.md` | Paper writing, publication artifacts |
| Closed-loop | `docs/protocols/closed_loop_protocol.md` | Select-route / materialize / ingest / await cycle |
| Promotion pipeline | `docs/protocols/promotion_pipeline.md` | 3-step flow (aspirational 4-stage model) |

### Interaction Domain — Cross-Cutting Protocols

| Protocol | File | Purpose |
|----------|------|---------|
| Human interaction | `docs/protocols/H_human_interaction.md` | Checkpoints, steering, approval, override, clarification |
| Mode envelope | `docs/protocols/mode_envelope_protocol.md` | 3 modes, envelopes, transitions |
| Adapter interface | `docs/protocols/adapter_interface.md` | Platform adapter + domain skill obligations |

### Legacy Protocol Map

The following existing protocols remain authoritative within their scope
unless explicitly superseded by a new domain protocol:

| Existing Protocol | Status | New Home |
|-------------------|--------|----------|
| `AUTONOMY_AND_OPERATOR_MODEL.md` | Active | Merged into brain_protocol |
| `COMMUNICATION_CONTRACT.md` | Active | Merged into H_human_interaction |
| `CLARIFICATION_PROTOCOL.md` | Active | Merged into H_human_interaction |
| `DECISION_POINT_PROTOCOL.md` | Active | Merged into H_human_interaction |
| `DECISION_TRACE_PROTOCOL.md` | Active | Merged into action_queue_protocol |
| `ROUTING_POLICY.md` | Active | Merged into closed_loop_protocol |
| `RESEARCH_EXECUTION_GUARDRAILS.md` | Active | Merged into closed_loop_protocol |
| `PROGRESSIVE_DISCLOSURE_PROTOCOL.md` | Active | Merged into brain_protocol |
| `SESSION_CHRONICLE_PROTOCOL.md` | Active | Merged into brain_protocol |
| `TOPIC_COMPLETION_PROTOCOL.md` | Active | Merged into brain_protocol |
| `TOPIC_REPLAY_PROTOCOL.md` | Active | Merged into brain_protocol |
| `GAP_RECOVERY_PROTOCOL.md` | Active | Referenced from closed_loop_protocol |
| `PROOF_OBLIGATION_PROTOCOL.md` | Active | Stays as-is (formal theory) |
| `SEMI_FORMAL_THEORY_PROTOCOL.md` | Active | Stays as-is (formal theory) |
| `SECTION_FORMALIZATION_PROTOCOL.md` | Active | Stays as-is (formal theory) |
| `FORMAL_THEORY_AUTOMATION_WORKFLOW.md` | Active | Stays as-is (formal theory) |
| `FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md` | Active | Stays as-is (formal theory) |
| `FAMILY_FUSION_PROTOCOL.md` | Active | Stays as-is (L2 canonical) |
| `VERIFICATION_BRIDGE_PROTOCOL.md` | Active | Merged into L4_validation_protocol |
| `L2_CONSULTATION_PROTOCOL.md` | Active | Referenced from L2_backend_interface |
| `L5_PUBLICATION_FACTORY_PROTOCOL.md` | Active | Stays as-is (publication layer) |
| `AGENT_CONFORMANCE_PROTOCOL.md` | Active | Merged into adapter_interface |
| `INDEXING_RULES.md` | Active | Referenced from L2_backend_interface |
| `LIGHTWEIGHT_RUNTIME_PROFILE.md` | Active | Referenced from brain_protocol |
| `MODE_AND_LAYER_OPERATING_MODEL.md` | Active | Merged into mode_envelope_protocol |
| `intake/L1_VAULT_PROTOCOL.md` | Active | Referenced from L1_intake_protocol |
| `intake/ARXIV_FIRST_SOURCE_INTAKE.md` | Active | Referenced from L0_SOURCE_LAYER |
| `canonical/PROMOTION_POLICY.md` | Active | Referenced from promotion_pipeline |
| `canonical/L2_COMPILER_PROTOCOL.md` | Active | Referenced from L2_backend_interface |
| `canonical/L2_STAGING_PROTOCOL.md` | Active | Referenced from L2_backend_interface |
| `canonical/LAYER_MAP.md` | Active | Referenced from L2_backend_interface |
| `canonical/LAYER2_OBJECT_FAMILIES.md` | Active | Referenced from L2_backend_interface |
| `canonical/L2_BACKEND_BRIDGE.md` | Active | Referenced from L2_backend_interface |
| `canonical/L2_MVP_CONTRACT.md` | Active | Referenced from L2_backend_interface |
| `canonical/L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md` | Active | Referenced from L2_backend_interface |
| `feedback/CANDIDATE.md` | Active | Referenced from L3_execution_protocol |
| `feedback/SPLIT_PROTOCOL.md` | Active | Referenced from L3_execution_protocol |
| `feedback/STRATEGY_MEMORY_TEMPLATE.md` | Active | Referenced from brain_protocol |
| `validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md` | Active | Referenced from L4_validation_protocol |
| `validation/EXECUTION_PROTOCOL.md` | Active | Merged into L4_validation_protocol |
| `runtime/TOPIC_TRUTH_ROOT_CONTRACT.md` | Active | Referenced from brain_protocol |
| `runtime/CONTROL_NOTE_CONTRACT.md` | Active | Referenced from H_human_interaction |
| `runtime/INNOVATION_DIRECTION_TEMPLATE.md` | Active | Referenced from H_human_interaction |
| `runtime/DECLARATIVE_RUNTIME_CONTRACTS.md` | Active | Referenced from action_queue_protocol |
| `runtime/DEFERRED_RUNTIME_CONTRACTS.md` | Active | Referenced from followup_lifecycle |
| `AITP_THOUGHT_PROTOCOL.md` (docs/) | Active | Stays as-is (agent reasoning) |
| `AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md` (docs/) | Active | Stays as-is (agent discipline) |
| `AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md` (docs/) | Active | Superseded by mode_envelope_protocol |
| `AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md` (docs/) | Active | Superseded by mode_envelope_protocol |
| `AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md` (docs/) | Active | Superseded by closed_loop_protocol |
| `AITP_UNIFIED_RESEARCH_ARCHITECTURE.md` (docs/) | Active | Superseded by this SPEC |
| `AITP_WORKFLOW_SHELL_AND_PROTOCOL_KERNEL.md` (docs/) | Active | Superseded by this SPEC |
| `AITP_MODE_ENVELOPE_PROTOCOL.md` (docs/) | Active | Superseded by mode_envelope_protocol |
| `V142_ARCHITECTURE_VISION.md` (docs/) | Reference | Kept as historical reference |

## S15. Execution Surface Provenance

If a canonical writeback depends on nontrivial execution, the upstream runtime
or note set must record the execution host and why it was chosen.

- Local Windows host: AI orchestration, human-facing curation, lightweight
  smoke tests.
- Remote hosts (`el`, `fish`, etc.): default AITP execution surface for
  model-side numerical checks and script-driven validation.
- LibRPA hosts (`kx`, `hr`, etc.): LibRPA builds, regressions, performance
  tests.

Host choice is part of trust provenance, not incidental commentary.

## S16. Charter Coverage

Every Charter article is enforced by specific protocol surfaces:

| Charter Article | Enforced By |
|-----------------|-------------|
| Art. 1 — Truth over fluency | Evidence discipline (S1), mode envelopes (S6) |
| Art. 2 — Evidence hierarchy | L0 fidelity grading, L1 assumption extraction |
| Art. 3 — Layered state | Layer model (S3), paired backend (S10) |
| Art. 4 — Contracts over hidden state | Artifact discipline (S1), conformance (S13) |
| Art. 5 — Earned promotion | Promotion pipeline (S8), L2 gate |
| Art. 6 — Conditional tool trust | Trust gates (S13), capability audit |
| Art. 7 — Uncertainty survives | Gap recovery, stuckness detection, deferred candidates |
| Art. 8 — Human checkpoints | H plane (S5), popup gate protocol |
| Art. 9 — Enforceable conformance | Conformance checks (S13), adapter obligations (S12) |
| Art. 10 — Adapters don't redefine | Adapter interface (S12), charter-first rule |

## S17. Filesystem Convention

```
AITP-Research-Protocol/
├── docs/
│   ├── CHARTER.md                          # Highest authority
│   ├── AITP_SPEC.md                        # This document
│   ├── design-principles.md                # Design principles
│   ├── architecture.md                     # Architecture overview
│   ├── PROJECT_INDEX.md                    # Navigation map
│   ├── protocols/                          # NEW: unified protocol home
│   │   ├── brain_protocol.md               # B plane orchestrator
│   │   ├── action_queue_protocol.md        # Next-action decision
│   │   ├── followup_lifecycle.md           # Sub-topics, deferred buffer
│   │   ├── L1_intake_protocol.md           # L1 layer
│   │   ├── L2_backend_interface.md         # L2 typed store contract
│   │   ├── L3_execution_protocol.md        # L3 candidate workspace
│   │   ├── L4_validation_protocol.md       # L4 validation surface
│   │   ├── L5_writing_protocol.md          # L5 writing & publication
│   │   ├── closed_loop_protocol.md         # Closed-loop state machine
│   │   ├── promotion_pipeline.md           # 4-stage promotion
│   │   ├── H_human_interaction.md          # H plane gates
│   │   ├── mode_envelope_protocol.md       # 3-mode envelopes
│   │   └── adapter_interface.md            # Platform adapter obligations
│   └── ...                                 # Existing docs preserved
├── research/knowledge-hub/                 # Runtime + implementation
│   ├── knowledge_hub/                      # Python package (aitp-kernel)
│   ├── source-layer/                       # L0
│   ├── intake/                             # L1
│   ├── canonical/                          # L2
│   ├── feedback/                           # L3
│   ├── validation/                         # L4
│   ├── runtime/                            # Brain runtime
│   └── topics/                             # Topic instances
├── contracts/                              # Human-readable contracts
├── schemas/                                # Machine-readable schemas
├── skills/                                 # Agent skills
├── adapters/                               # Platform adapters
└── scripts/                                # Runtime scripts
```

Legacy protocol files in `research/knowledge-hub/` and `docs/` remain in place
until their content is formally merged into the new `docs/protocols/` files.
At that point the legacy file should contain a redirect pointer:

```markdown
This protocol has been consolidated into `docs/protocols/<new_name>.md`.
This file is kept for backward compatibility only.
```
