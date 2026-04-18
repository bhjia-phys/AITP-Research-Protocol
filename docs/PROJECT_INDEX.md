# AITP Project Index

> Map, not encyclopedia. This index tells you *where* to look, not *what* to read.
> Each entry links to the real doc — go there for details.

---

## Where to Start

| I want to... | Start here | Then |
|---|---|---|
| Understand AITP in 5 minutes | [README.md](../README.md) | [QUICKSTART.md](QUICKSTART.md) → [USER_TOPIC_JOURNEY.md](USER_TOPIC_JOURNEY.md) |
| Understand the protocol architecture | [CHARTER.md](CHARTER.md) | [AITP_SPEC.md](AITP_SPEC.md) → specific protocol below |
| Contribute code to AITP itself | [AITP_GSD_WORKFLOW_CONTRACT.md](AITP_GSD_WORKFLOW_CONTRACT.md) | [architecture.md](architecture.md) → [research/knowledge-hub/LAYER_MAP.md](../research/knowledge-hub/LAYER_MAP.md) |
| Do theoretical physics research with AITP | [using-aitp/SKILL.md](../skills/using-aitp/SKILL.md) | [aitp-runtime/SKILL.md](../skills/aitp-runtime/SKILL.md) → [USER_TOPIC_JOURNEY.md](USER_TOPIC_JOURNEY.md) |
| Integrate AITP into my agent platform | [adapters/README.md](../adapters/README.md) | [protocols/adapter_interface.md](protocols/adapter_interface.md) → pick your platform |
| Understand the research protocol mechanics | [AITP_SPEC.md](AITP_SPEC.md) | [contracts/README.md](../contracts/README.md) → [schemas/README.md](../schemas/README.md) |
| Understand the runtime engine | [protocols/brain_protocol.md](protocols/brain_protocol.md) | [research/knowledge-hub/runtime/README.md](../research/knowledge-hub/runtime/README.md) |

---

## Protocol Architecture (Charter → SPEC → Protocols)

```
CHARTER.md (highest authority: 10 articles + three-phase vision)
  └── AITP_SPEC.md (unified specification)
        ├── Brain Domain (global orchestrator)
        │     ├── brain_protocol.md
        │     ├── action_queue_protocol.md
        │     └── followup_lifecycle.md
        ├── Point Domain (layer-specific)
        │     ├── L0_SOURCE_LAYER.md (existing)
        │     ├── L1_intake_protocol.md
        │     ├── L2_backend_interface.md
        │     ├── L3_execution_protocol.md
        │     ├── L4_validation_protocol.md
        │     ├── closed_loop_protocol.md
        │     └── promotion_pipeline.md
        └── Interaction Domain (cross-cutting)
              ├── H_human_interaction.md
              ├── mode_envelope_protocol.md
              └── adapter_interface.md
```

All protocol files live under `docs/protocols/` (new) unless otherwise noted.

---

## Layer Architecture

AITP organizes research into five content layers plus two cross-cutting planes.
The default route is `L0 → L1 → L3 → L4 → L2`.

| Layer | Name | Purpose | Key doc | Key schema |
|---|---|---|---|---|
| **B** | Brain (orchestrator) | Topic lifecycle, routing, memory | [brain_protocol.md](protocols/brain_protocol.md) | — |
| **H** | Human (interaction) | Checkpoints, steering, approval | [H_human_interaction.md](protocols/H_human_interaction.md) | [decision-point.schema.json](../schemas/decision-point.schema.json) |
| **L0** | Source acquisition | Papers, notes, upstream refs | [L0_SOURCE_LAYER.md](../research/knowledge-hub/L0_SOURCE_LAYER.md) | [source-item.schema.json](../schemas/source-item.schema.json) |
| **L1** | Provisional understanding | Source analysis, provenance, notation/contradiction intake | [L1_intake_protocol.md](protocols/L1_intake_protocol.md) | [research-question.schema.json](../schemas/research-question.schema.json) |
| **L2** | Trusted knowledge | Promoted, reusable results | [L2_backend_interface.md](protocols/L2_backend_interface.md) | [promotion-trace.schema.json](../schemas/promotion-trace.schema.json) |
| **L3** | Candidate outputs | Exploratory, tentative | [L3_execution_protocol.md](protocols/L3_execution_protocol.md) | [candidate-claim.schema.json](../schemas/candidate-claim.schema.json) |
| **L4** | Validation & trust audit | Checks, benchmarks, human decisions | [L4_validation_protocol.md](protocols/L4_validation_protocol.md) | [validation.schema.json](../schemas/validation.schema.json) |

See [LAYER_MAP.md](../research/knowledge-hub/LAYER_MAP.md) for the full filesystem layout per layer.

---

## Protocol Definition (contracts/ + schemas/)

These define *what* AITP tracks and *what shape* the data must have.

| Artifact | Human-readable contract | Machine-readable schema | Role |
|---|---|---|---|
| Research question | [research-question.md](../contracts/research-question.md) | [research-question.schema.json](../schemas/research-question.schema.json) | Scoped question, scope, assumptions, target claims, forbidden proxies |
| Candidate claim | [candidate-claim.md](../contracts/candidate-claim.md) | [candidate-claim.schema.json](../schemas/candidate-claim.schema.json) | Tentative conclusion with evidence level |
| Derivation | [derivation.md](../contracts/derivation.md) | [derivation.schema.json](../schemas/derivation.schema.json) | Symbolic work with assumptions and gaps |
| Validation | [validation.md](../contracts/validation.md) | [validation.schema.json](../schemas/validation.schema.json) | Validation plan with acceptance/rejection rules |
| Operation | [operation.md](../contracts/operation.md) | [operation.schema.json](../schemas/operation.schema.json) | Reusable computation with trust status |
| Promotion/rejection | [promotion-or-reject.md](../contracts/promotion-or-reject.md) | [promotion-or-reject.schema.json](../schemas/promotion-or-reject.schema.json) | Gate decision with reason |
| Decision point | — | [decision-point.schema.json](../schemas/decision-point.schema.json) | Question requiring human input (10 trigger types) |
| Decision trace | — | [decision-trace.schema.json](../schemas/decision-trace.schema.json) | Record of decisions made |
| Topic synopsis | — | [topic-synopsis.schema.json](../schemas/topic-synopsis.schema.json) | Lightweight machine-readable topic status |
| Knowledge packet | — | [knowledge-packet.schema.json](../schemas/knowledge-packet.schema.json) | Reusable research summary |
| Session chronicle | — | [session-chronicle.schema.json](../schemas/session-chronicle.schema.json) | Narrative session summary for resume |

See [contracts/README.md](../contracts/README.md) and [schemas/README.md](../schemas/README.md) for schema usage rules.

---

## Runtime System (research/knowledge-hub/runtime/)

The runtime is the engine that materializes topic state, selects next actions, and coordinates sessions.

Topic-owned truth is converging on `topics/<slug>/`, with runtime-facing state under `topics/<slug>/runtime/`.
For operator-facing truth, Markdown is the human authority; JSON and JSONL stay machine-facing companions.
Local research state belongs in the user kernel, typically `~/.aitp/kernel`;
the git repo should stay code, protocol, and public docs.

| Surface | File | Purpose | Audience |
|---|---|---|---|
| **Runtime overview** | [README.md](../research/knowledge-hub/runtime/README.md) | Full surface inventory, role map, rules | Agent |
| **Topic state** | `topics/<slug>/runtime/topic_state.json` | Machine-readable snapshot: resume stage, layer status, promotion gate, pointers | Agent |
| **Human console** | `topics/<slug>/runtime/operator_console.md` | Immediate execution contract: do now / do not / escalate | Human, Agent |
| **Runtime bundle** | `topics/<slug>/runtime/runtime_protocol.generated.md` | Progressive disclosure bundle: synopsis, contracts, triggers, guardrails | Agent |
| **Next action** | `topics/<slug>/runtime/next_action_decision.json` | Authoritative decision: what to do next and why | Agent |
| **Topic dashboard** | `topics/<slug>/runtime/topic_dashboard.md` | Primary human render of current state | Human |
| **Action queue** | `topics/<slug>/runtime/action_queue_contract.generated.json` | Ordered list of executable actions | Agent |
| **Unfinished work** | `topics/<slug>/runtime/unfinished_work.json` | Index of incomplete actions | Agent |
| **Pending decisions** | `topics/<slug>/runtime/pending_decisions.json` | Unresolved decision points | Agent, Human |
| **Decision ledger** | `topics/<slug>/runtime/decision_ledger.jsonl` | Append-only decision history | Agent |
| **Trajectory log** | `topics/<slug>/runtime/trajectory_log.jsonl` | Human-readable execution narrative | Human |
| **Failure classification** | `topics/<slug>/runtime/failure_classification.json` | Classified failure types | Agent |
| **Topic index** | `topic_index.jsonl` | Registry of all topics | Agent |
| **Active topics** | `active_topics.json` | Authoritative list of active topics | Agent |
| **Current topic** | `current_topic.json` | Local-only compatibility projection | Agent |

### Runtime Control Contracts

| Contract | File | Purpose |
|---|---|---|
| Topic truth root | [TOPIC_TRUTH_ROOT_CONTRACT.md](../research/knowledge-hub/runtime/TOPIC_TRUTH_ROOT_CONTRACT.md) | Single-topic authoritative layout; Markdown-first human truth surfaces and compatibility projection rules |
| Control note | [CONTROL_NOTE_CONTRACT.md](../research/knowledge-hub/runtime/CONTROL_NOTE_CONTRACT.md) | Human redirects, pauses, changes scope |
| Innovation direction | [INNOVATION_DIRECTION_TEMPLATE.md](../research/knowledge-hub/runtime/INNOVATION_DIRECTION_TEMPLATE.md) | Operator changes novelty/scope/acceptance |
| Declarative contracts | [DECLARATIVE_RUNTIME_CONTRACTS.md](../research/knowledge-hub/runtime/DECLARATIVE_RUNTIME_CONTRACTS.md) | Action queues authored explicitly, not inferred |
| Deferred contracts | [DEFERRED_RUNTIME_CONTRACTS.md](../research/knowledge-hub/runtime/DEFERRED_RUNTIME_CONTRACTS.md) | Parked fragments with durable reactivation contract |
| Progressive disclosure | [PROGRESSIVE_DISCLOSURE_PROTOCOL.md](../research/knowledge-hub/runtime/PROGRESSIVE_DISCLOSURE_PROTOCOL.md) | When to load deeper protocol surfaces |

### Runtime Orchestration Scripts

| Script | Purpose |
|---|---|
| `scripts/orchestrate_topic.py` | Bootstrap/resume topic, materialize action queue, update all surfaces |
| `scripts/decide_next_action.py` | Load state, select next action (heuristic or control note), check auto-runnable |

### Derived Continuity Surfaces (per-topic)

| Surface | Purpose |
|---|---|
| `research_judgment.active.json/md` | Momentum, stuckness, surprise signals |
| `collaborator_profile.active.json/md` | Topic-scoped collaborator profile |
| `research_trajectory.active.json/md` | Recent continuity across sessions |
| `mode_learning.active.json/md` | Learned route and guidance patterns |
| `session_chronicle.md/json` | Narrative summary for session handoff |
| `strategy_memory.jsonl` | Helpful and harmful patterns to avoid |
| `conformance_state.json/md` | AITP protocol conformance audit |

---

## Runtime Kernel Modules (research/knowledge-hub/knowledge_hub/)

The Python package `aitp-kernel` provides all runtime services. Key modules:

| Module | Function |
|---|---|
| `aitp_cli.py` | CLI frontdoor, parses all `aitp` commands |
| `aitp_service.py` | Core service layer |
| `semantic_routing.py` | Routes natural language to protocol actions |
| `topic_shell_support.py` | Topic bootstrap, dashboard materialization, state derivation |
| `orchestrate_topic.py` | Action queue orchestration and runtime policy application |
| `runtime_bundle_support.py` | Builds the progressive-disclosure runtime bundle |
| `runtime_path_support.py` | Runtime path normalization and resolution |
| `runtime_read_path_support.py` | Determines which protocol surfaces to load |
| `decide_next_action.py` | Next-action decision with heuristic/control-note/contract modes |
| `decision_point_handler.py` | Materializes and tracks decision points |
| `promotion_gate_support.py` | L2 promotion gate logic |
| `auto_promotion_support.py` | Auto-promotion for qualified candidates |
| `candidate_promotion_support.py` | Candidate preparation for promotion |
| `source_catalog.py` | L0 source management and BibTeX support |
| `source_intelligence.py` | Citation neighborhood analysis |
| `l1_source_intake_support.py` | L1 assumption and reading-depth surface |
| `l1_vault_support.py` | L1 three-layer vault materialization |
| `l2_compiler.py` | L2 knowledge graph compilation |
| `l2_graph.py` | L2 knowledge graph queries |
| `l2_reuse_context_support.py` | Progressive L3 reuse contexts over global L2 |
| `l2_staging.py` | L2 staging before promotion |
| `l2_hygiene.py` | L2 canonical store hygiene |
| `l3_derivation_support.py` | Run-local L3 derivation ledger and notebook-entry projection |
| `l3_comparison_support.py` | Run-local L2 comparison receipt ledger for derivation-heavy candidates |
| `research_notebook_support.py` | XeLaTeX topic notebook compiler over runtime, provenance, derivation, and log surfaces |
| `capability_plane_support.py` | Runtime capability plane for tools, servers, and environments |
| `lean_bridge_support.py` | Lean 4 bridge for formal theory |
| `statement_compilation_support.py` | Statement compilation before proof repair |
| `validation_review_service.py` | L4 review bundle orchestration |
| `formal_theory_audit_support.py` | Formal theory coverage/consistency audit |
| `consultation_support.py` | Deep research consultation |
| `exploration_session_support.py` | Lightweight speculative exploration |
| `auto_action_support.py` | Autonomous action queue progression |
| `capability_audit_support.py` | Runtime capability audit |
| `research_judgment_support.py` | Momentum/stuckness/surprise detection |
| `research_trajectory_support.py` | Session continuity tracking |
| `collaborator_profile_support.py` | Collaborator profile management |
| `session_chronicle_handler.py` | Session chronicle materialization |
| `control_plane_support.py` | Operator control plane (pause, redirect, etc.) |
| `dispatch_execution_task.py` | External executor (Codex/OpenClaw) dispatch |
| `subprocess_error_support.py` | Subprocess failure formatting and recovery |
| `tpkn_bridge.py` | Theoretical-Physics-Knowledge-Network backend bridge |

---

## Layer-Specific Protocols (research/knowledge-hub/)

### L0: Source Layer (`source-layer/`)

| File | Purpose |
|---|---|
| [README.md](../research/knowledge-hub/source-layer/README.md) | Source acquisition overview |
| `global_index.jsonl` | Global source registry |

### L1: Intake Layer (`intake/`)

| File | Purpose |
|---|---|
| [README.md](../research/knowledge-hub/intake/README.md) | Intake overview |
| [ARXIV_FIRST_SOURCE_INTAKE.md](../research/knowledge-hub/intake/ARXIV_FIRST_SOURCE_INTAKE.md) | ArXiv-specific intake workflow |
| [L1_VAULT_PROTOCOL.md](../research/knowledge-hub/intake/L1_VAULT_PROTOCOL.md) | Three-layer vault (raw/wiki/output) |

### L3: Feedback Layer (`feedback/`)

| File | Purpose |
|---|---|
| [README.md](../research/knowledge-hub/feedback/README.md) | Feedback (candidate outputs) overview |
| [CANDIDATE.md](../research/knowledge-hub/feedback/CANDIDATE.md) | Candidate management |
| [SPLIT_PROTOCOL.md](../research/knowledge-hub/feedback/SPLIT_PROTOCOL.md) | Splitting candidate fragments |
| [STRATEGY_MEMORY_TEMPLATE.md](../research/knowledge-hub/feedback/STRATEGY_MEMORY_TEMPLATE.md) | Pattern memory template |

### L4: Validation Layer (`validation/`)

| File | Purpose |
|---|---|
| [README.md](../research/knowledge-hub/validation/README.md) | Validation overview |
| [BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md](../research/knowledge-hub/validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md) | Reproduction and understanding gates |
| [EXECUTION_PROTOCOL.md](../research/knowledge-hub/validation/EXECUTION_PROTOCOL.md) | Validation execution workflow |

### L2: Canonical Layer (`canonical/`)

| File | Purpose |
|---|---|
| [README.md](../research/knowledge-hub/canonical/README.md) | Trusted knowledge store overview |
| [CANONICAL_UNIT.md](../research/knowledge-hub/canonical/CANONICAL_UNIT.md) | Canonical unit structure and rules |
| [LAYER_MAP.md](../research/knowledge-hub/canonical/LAYER_MAP.md) | L2 filesystem layout |
| [LAYER2_OBJECT_FAMILIES.md](../research/knowledge-hub/canonical/LAYER2_OBJECT_FAMILIES.md) | Object type families |
| [PROMOTION_POLICY.md](../research/knowledge-hub/canonical/PROMOTION_POLICY.md) | Promotion rules and policy |
| [L2_COMPILER_PROTOCOL.md](../research/knowledge-hub/canonical/L2_COMPILER_PROTOCOL.md) | Knowledge graph compilation |
| [L2_BACKEND_BRIDGE.md](../research/knowledge-hub/canonical/L2_BACKEND_BRIDGE.md) | Backend writeback |
| [L2_STAGING_PROTOCOL.md](../research/knowledge-hub/canonical/L2_STAGING_PROTOCOL.md) | Staging before canonical promotion |
| [L2_MVP_CONTRACT.md](../research/knowledge-hub/canonical/L2_MVP_CONTRACT.md) | MVP direction contracts |
| [L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md](../research/knowledge-hub/canonical/L2_PAIRED_BACKEND_MAINTENANCE_PROTOCOL.md) | Paired backend maintenance |
| `compiled/obsidian_l2/` | Fixed-folder Obsidian-friendly Markdown mirror over canonical L2 |

---

## Cross-Cutting Protocols

| Protocol | File | When it matters |
|---|---|---|
| Autonomy & operator model | [AUTONOMY_AND_OPERATOR_MODEL.md](../research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md) | Understanding human vs agent roles |
| Communication contract | [COMMUNICATION_CONTRACT.md](../research/knowledge-hub/COMMUNICATION_CONTRACT.md) | How agent and human communicate |
| Execution guardrails | [RESEARCH_EXECUTION_GUARDRAILS.md](../research/knowledge-hub/RESEARCH_EXECUTION_GUARDRAILS.md) | Bounded action packets, forbidden proxies |
| Clarification | [CLARIFICATION_PROTOCOL.md](../research/knowledge-hub/CLARIFICATION_PROTOCOL.md) | When the question is ambiguous |
| Decision points | [DECISION_POINT_PROTOCOL.md](../research/knowledge-hub/DECISION_POINT_PROTOCOL.md) | When agent needs human input |
| Decision traces | [DECISION_TRACE_PROTOCOL.md](../research/knowledge-hub/DECISION_TRACE_PROTOCOL.md) | Recording decisions |
| Routing policy | [ROUTING_POLICY.md](../research/knowledge-hub/ROUTING_POLICY.md) | How questions are routed to layers |
| Mode envelope | [AITP_MODE_ENVELOPE_PROTOCOL.md](../docs/AITP_MODE_ENVELOPE_PROTOCOL.md) | Runtime mode and posture |
| Transition & backedge | [AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md](../docs/AITP_TRANSITION_AND_BACKEDGE_PROTOCOL.md) | Layer transitions including backward jumps |
| Thought protocol | [AITP_THOUGHT_PROTOCOL.md](../docs/AITP_THOUGHT_PROTOCOL.md) | How agent reasons through problems |
| Intelligence preservation | [AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md](AITP_INTELLIGENCE_PRESERVATION_PRINCIPLES.md) | Preventing context loss |
| L3-L4 iterative verify | [AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md](../docs/AITP_L3_L4_ITERATIVE_VERIFY_LOOP_PROTOCOL.md) | Iterative verification cycles |
| Proof obligation | [PROOF_OBLIGATION_PROTOCOL.md](../research/knowledge-hub/PROOF_OBLIGATION_PROTOCOL.md) | Formal proof requirements |
| Semi-formal theory | [SEMI_FORMAL_THEORY_PROTOCOL.md](../research/knowledge-hub/SEMI_FORMAL_THEORY_PROTOCOL.md) | Semi-formal theory objects |
| Formal theory automation | [FORMAL_THEORY_AUTOMATION_WORKFLOW.md](../research/knowledge-hub/FORMAL_THEORY_AUTOMATION_WORKFLOW.md) | Automated formal theory pipeline |
| Upstream reference | [FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md](../research/knowledge-hub/FORMAL_THEORY_UPSTREAM_REFERENCE_PROTOCOL.md) | Tracking upstream formal theory refs |
| Section formalization | [SECTION_FORMALIZATION_PROTOCOL.md](../research/knowledge-hub/SECTION_FORMALIZATION_PROTOCOL.md) | Section-level formalization |
| Gap recovery | [GAP_RECOVERY_PROTOCOL.md](../research/knowledge-hub/GAP_RECOVERY_PROTOCOL.md) | When a gap is discovered |
| Verification bridge | [VERIFICATION_BRIDGE_PROTOCOL.md](../research/knowledge-hub/VERIFICATION_BRIDGE_PROTOCOL.md) | Verification handoff |
| Family fusion | [FAMILY_FUSION_PROTOCOL.md](../research/knowledge-hub/FAMILY_FUSION_PROTOCOL.md) | Merging related topics |
| Publication factory | [L5_PUBLICATION_FACTORY_PROTOCOL.md](../research/knowledge-hub/L5_PUBLICATION_FACTORY_PROTOCOL.md) | Publication output layer |
| Topic replay | [TOPIC_REPLAY_PROTOCOL.md](../research/knowledge-hub/TOPIC_REPLAY_PROTOCOL.md) | Replaying topic history |
| Topic completion | [TOPIC_COMPLETION_PROTOCOL.md](../research/knowledge-hub/TOPIC_COMPLETION_PROTOCOL.md) | Completing a topic |
| Session chronicle | [SESSION_CHRONICLE_PROTOCOL.md](../research/knowledge-hub/SESSION_CHRONICLE_PROTOCOL.md) | Session summaries for resume |
| L2 consultation | [L2_CONSULTATION_PROTOCOL.md](../research/knowledge-hub/L2_CONSULTATION_PROTOCOL.md) | Consulting trusted knowledge |
| Indexing rules | [INDEXING_RULES.md](../research/knowledge-hub/INDEXING_RULES.md) | How artifacts are indexed |
| Lightweight profile | [LIGHTWEIGHT_RUNTIME_PROFILE.md](../research/knowledge-hub/LIGHTWEIGHT_RUNTIME_PROFILE.md) | Minimal runtime mode |
| Test runbook | [AITP_TEST_RUNBOOK.md](../research/knowledge-hub/runtime/AITP_TEST_RUNBOOK.md) | How to run tests |

---

## Agent Skills (skills/)

| Skill | File | When agent loads it |
|---|---|---|
| **using-aitp** | [using-aitp/SKILL.md](../skills/using-aitp/SKILL.md) | Session start — determines whether AITP should be activated. Routes to AITP or normal processing. |
| **aitp-runtime** | [aitp-runtime/SKILL.md](../skills/aitp-runtime/SKILL.md) | After AITP activation — reads runtime bundle, follows protocol, emits decisions. |

---

## Platform Adapters (adapters/)

Each adapter provides platform-specific integration instructions for the agent.

| Adapter | File | Runtime |
|---|---|---|
| Codex (baseline) | [codex/SKILL.md](../adapters/codex/SKILL.md) | Codex CLI via `.codex/` |
| Claude Code | [claude-code/SKILL.md](../adapters/claude-code/SKILL.md) | Claude Code via hooks |
| OpenClaw (autonomous) | [openclaw/SKILL.md](../adapters/openclaw/SKILL.md) | OpenClaw via plugin |
| OpenCode (plugin) | [opencode/SKILL.md](../adapters/opencode/SKILL.md) | OpenCode via `opencode.json` plugin |

---

## Design and Architecture Docs (docs/)

### Core

| Doc | Purpose | Audience |
|---|---|---|
| [architecture.md](architecture.md) | Technical architecture and layer design | Contributor |
| [CHARTER.md](CHARTER.md) | Research charter — what counts as disciplined AI-assisted research | Contributor, Researcher |
| [design-principles.md](design-principles.md) | Design principles behind protocol decisions | Contributor |
| [AITP_UNIFIED_RESEARCH_ARCHITECTURE.md](AITP_UNIFIED_RESEARCH_ARCHITECTURE.md) | Unified research architecture across lanes | Contributor |
| [AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md](AITP_ONTOLOGY_AND_MODE_COMPLETENESS.md) | Ontology completeness checklist | Contributor |

### User-Facing

| Doc | Purpose | Audience |
|---|---|---|
| [QUICKSTART.md](QUICKSTART.md) | Step-by-step walkthrough with a real topic | New user |
| [USER_TOPIC_JOURNEY.md](USER_TOPIC_JOURNEY.md) | What AITP feels like in practice | New user |
| [CONTEXT_LOADING.md](CONTEXT_LOADING.md) | How context is loaded and managed | Agent |
| [LESSONS_FROM_GET_PHYSICS_DONE.md](LESSONS_FROM_GET_PHYSICS_DONE.md) | Lessons from completed research | Contributor |

### Operations

| Doc | Purpose | Audience |
|---|---|---|
| [INSTALL.md](INSTALL.md) | Full installation guide | Operator |
| [UNINSTALL.md](UNINSTALL.md) | Removal guide | Operator |
| [MIGRATE_MULTI_TOPIC.md](MIGRATE_MULTI_TOPIC.md) | Migration notes for multi-topic state | Operator |
| [MIGRATE_RUNTIME_SURFACES.md](MIGRATE_RUNTIME_SURFACES.md) | Runtime surface migration | Contributor |
| [MIGRATE_LOCAL_INSTALL.md](MIGRATE_LOCAL_INSTALL.md) | Local install migration | Operator |
| [PUBLISH_PYPI.md](PUBLISH_PYPI.md) | PyPI publishing workflow | Contributor |
| [benchmark-cases.md](benchmark-cases.md) | Benchmark test cases | Contributor |

### Platform-Specific Install

| Doc | Platform |
|---|---|
| [INSTALL_CODEX.md](INSTALL_CODEX.md) | Codex |
| [INSTALL_CLAUDE_CODE.md](INSTALL_CLAUDE_CODE.md) | Claude Code |
| [INSTALL_OPENCLAW.md](INSTALL_OPENCLAW.md) | OpenClaw |
| [INSTALL_OPENCODE.md](INSTALL_OPENCODE.md) | OpenCode |

### Development

| Doc | Purpose | Audience |
|---|---|---|
| [AITP_GSD_WORKFLOW_CONTRACT.md](AITP_GSD_WORKFLOW_CONTRACT.md) | Boundary: AITP research vs GSD repo work | Contributor |
| [AITP_WORKFLOW_SHELL_AND_PROTOCOL_KERNEL.md](AITP_WORKFLOW_SHELL_AND_PROTOCOL_KERNEL.md) | Why the UX converges on this shape | Contributor |
| [V142_ARCHITECTURE_VISION.md](V142_ARCHITECTURE_VISION.md) | Architecture vision for v1.42+ | Contributor |

---

## Project Boundaries

| Area | Owned by | Doc |
|---|---|---|
| AITP research topic state | AITP protocol (runtime/) | — |
| AITP protocol/schema changes | AITP protocol (`contracts/`, `schemas/`) | — |
| AITP runtime code changes | GSD workflow ([AITP_GSD_WORKFLOW_CONTRACT.md](AITP_GSD_WORKFLOW_CONTRACT.md)) | — |
| AITP tests and acceptance | GSD workflow | — |
| GSD project planning | GSD (`.planning/`) | — |

---

## Backlog (GSD)

Backlog items are tracked in `.planning/ROADMAP.md` under the `## Backlog` section, numbered `999.x`. These represent identified improvements not yet scheduled into phases.

Current backlog (from harness engineering analysis):
- `999.28` Phase transition log — research path traceability
- `999.29` Demotion history — allow layer backtrack with reason
- `999.30` L2 override human modifications record
- `999.31` Competing hypotheses explicit support
- `999.32` Runtime README capability matrix
- `999.33` Runtime protocol generated sample in docs/
