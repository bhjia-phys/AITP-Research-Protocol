# AITP 5-Axis Development Taxonomy

This file is the canonical reference for classifying AITP development work
into the 5-axis advancement model. GSD agents MUST consult this file when
creating new phases, plans, or backlog items to ensure correct axis tagging.

## Axis Definitions

### Axis 1: Layer-Internal Optimization

**Intent signals:** "improve X layer", "make L0/L1/L2/L3/L4/L5 better",
"fix extraction", "add parsing", "enhance retrieval", "improve human UI"

Each layer's own capability, independent of how it connects to others.

| Layer | What belongs here |
|-------|-------------------|
| L0 (Source) | PDF/TeX parsing, source download, metadata quality, citation extraction |
| L1 (Intake) | Assumption/regime/notation extraction, content chunking, distillation quality |
| L2 (Canonical) | Knowledge population, graph structure, retrieval quality, hygiene |
| L3 (Candidate) | Coverage audit completeness, candidate formation quality |
| L4 (Adjudication) | Trust gate calibration, validation contract design |
| L5 (Publication) | Output factory, paper generation, export formats |
| Human | Status rendering, onboarding, jargon cleanup, CLI grouping, progress indicator |

### Axis 2: Inter-Layer Connection Optimization

**Intent signals:** "connect X to Y", "fast path", "pipeline", "handoff",
"promotion flow", "data flow between layers", "bridge"

How data and artifacts move between layers.

| Connection | What belongs here |
|------------|-------------------|
| L0→L1 | Source projection, auto-registration, metadata propagation |
| L1→L2 | Literature-intake fast path, staging bridge, provisional deposit |
| L3→L4 | Coverage + trust audit pipeline, candidate handoff |
| L4→L2 | Promotion gate, auto-promote, canonical writeback |
| L5←L2 | Publication from canonical knowledge |

### Axis 3: Layer-Internal Data Recording

**Intent signals:** "schema", "metric", "log", "manifest", "track",
"record", "data model", "JSONL", "observability"

How data is structured, persisted, and made inspectable — cross-cutting
concern that affects all layers.

| Sub-area | What belongs here |
|----------|-------------------|
| Schema evolution | topic_state.json changes, operation manifest updates, contract versioning |
| JSONL metrics | Self-evolution loop, theory operation logging, pattern analysis |
| Manifest-as-truth | Integrity checks, artifact presence validation, state machine verification |

### Axis 4: Global Infrastructure

**Intent signals:** "crash", "recovery", "session", "mode", "mode dispatch",
"escalation", "onboarding", "tutorial", "status", "dashboard", "checkpoint",
"pause", "resume"

Three sub-categories:

| Sub-area | What belongs here |
|----------|-------------------|
| Protocol skeleton | Crash recovery, state machine, checkpoint-restore, deep pause, error handling |
| Human experience | Session summary, change diff, progress indicator, progressive disclosure, feedback, onboarding, jargon cleanup, CLI grouping |
| Execution strategy | Mode dispatch (4 modes), escalation sensitivity, loop detection, derivation retry intervention, task-type routing |

### Axis 5: AI Agent Integration

**Intent signals:** "agent", "MCP", "Skeptic-D", "agent behavior",
"context injection", "isolation", "gatekeeper", "natural language",
"steering", "routing"

Two sub-categories:

| Sub-area | What belongs here |
|----------|-------------------|
| Agent governance | Schema-level isolation, context injection with dedup, mechanical verification, deploy-guard equivalents, tool manifest control |
| Agent interface | Natural-language steering, MCP routing, chat session routing, feedback mechanism, front-door convergence |

## Classification Decision Tree

```
Is it about one specific layer's capability?
  YES → Axis 1
  NO ↓
Is it about how two layers exchange data?
  YES → Axis 2
  NO ↓
Is it about data schemas, logging, or integrity checking?
  YES → Axis 3
  NO ↓
Is it about mode dispatch, crash recovery, or human-facing rendering?
  YES → Axis 4
  NO ↓
Is it about agent behavior, MCP tools, or agent-human interface?
  YES → Axis 5
  NO → Ask for clarification; may span multiple axes
```

## Multi-Axis Items

Some items naturally span two axes. Tag with primary axis first:
- "Mode-aware runtime bundle" = Axis 4 (execution strategy) + Axis 2 (varies context per mode)
- "Literature-intake fast path" = Axis 2 (L1→L2 connection) + Axis 4 (new execution mode)
- "LLM replacing regex in L1" = Axis 1 (L1 capability) + Axis 5 (agent-driven extraction)

## Complete Backlog-to-Axis Mapping

### Items 999.1–999.52 (pre-framework)

| Item | Title | Axis | Status |
|------|-------|------|--------|
| 999.1 | L5 Publication Factory | A1 (L5) | open |
| 999.2 | CLI Human-Readable Output | A4 (human exp) | **closed** v1.33 |
| 999.3 | E2E Integration Tests | A4 (protocol skeleton) | partial |
| 999.4 | SessionStart Windows Fix | A4 (protocol skeleton) | **closed** |
| 999.5 | Demo Topic Onboarding | A4 (human exp) | **closed** → 999.50 |
| 999.6 | Service God Class Cleanup | A4 (protocol skeleton) | open |
| 999.7 | Decision Script Quality | A4 (execution strategy) | open |
| 999.8 | Schema And Contract Consistency | A3 (schema) | **closed** v1.51 |
| 999.9 | Documentation Fixes | A4 (human exp) | **closed** v1.52 |
| 999.10 | Dependency Pinning | A4 (protocol skeleton) | **closed** v1.50 |
| 999.11 | User Experience Friction | A4 (human exp) | **closed** v1.53-59 |
| 999.12 | Test Suite Quality | A4 (protocol skeleton) | **closed** v1.55-57 |
| 999.13 | Graph Traversal And Search | A1 (L2) | **closed** v1.44-45 |
| 999.14 | Physical Picture Object Type | A1 (L2) | **closed** v1.44 |
| 999.15 | MVP Type Subset | A1 (L2) | **closed** v1.44 |
| 999.16 | Lightweight Knowledge Entry | A2 (L1→L2) | **closed** v1.44 |
| 999.17 | Progressive Disclosure Retrieval | A5 (agent interface) | **closed** v1.44-45 |
| 999.18 | Seed First Direction | A1 (L2) | **closed** v1.44 |
| 999.19 | Symbolic/Analytical Reasoning | A1 (L4) | **closed** v1.47 |
| 999.20 | Research Judgment | A4 (execution strategy) | **closed** v1.47 |
| 999.21 | Layer Model Flexibility | A4 (execution strategy) | partial v1.60 |
| 999.22 | Creativity/Taste/Intuition | A4 (execution strategy) | partial v1.61 |
| 999.23 | Cross-Session Collaborator | A3 (data recording) | **closed** v1.48 |
| 999.24 | Quick Exploration Mode | A4 (execution strategy) | **closed** v1.49 |
| 999.25 | Source Fidelity Grading | A1 (L0) | **closed** v1.46 |
| 999.26 | Citation Graph BibTeX | A1 (L0) | **closed** v1.46-63 |
| 999.27 | Assumption Extraction | A1 (L1) | partial v1.64 |
| 999.28 | Scratch Mode/Negative Results | A3 (data recording) | partial v1.62 |
| 999.29 | L4 Analytical Validation | A1 (L4) | open |
| 999.30 | Cross-Layer Parallel Research | A2 + A4 | open |
| 999.31 | Artifact Footprint Reduction | A4 (protocol skeleton) | open |
| 999.32 | Research Trajectory Recording | A3 (data recording) | open |
| 999.33 | Mixed-Corpus Graph Seed | A2 (L0→L1) | open |
| 999.34 | Extracted/Inferred/Ambiguous Labels | A3 (schema) | open |
| 999.35 | Human-Facing Graph Report | A4 (human exp) | open |
| 999.36 | Incremental Graph Rebuild | A1 (L2) | open |
| 999.37 | Persistent Wiki Compilation | A3 (data recording) | open |
| 999.38 | Task-Type Axis/Templates | A4 (execution strategy) | open |
| 999.39 | Human Interaction Plane | A4 (human exp) | open |
| 999.40 | Decompose L3 | A1 (L3) | open |
| 999.41 | Mandatory L4→L3 Return | A2 (L4→L3) | open |
| 999.42 | Task-Type By Lane Templates | A4 (execution strategy) | open |
| 999.43 | Real Topic E2E Validation | all (diagnostic) | → Phase 165 |
| 999.44 | Cross-Runtime Parity | A5 (agent interface) | open |
| 999.45 | Multi-User Feedback | A4 (human exp) | open |
| 999.46 | Knowledge-Graph Content Quality | A1 (L2) | open |
| 999.47 | Semi-Formal Lean Bridge | A2 (L4→L5) | open |
| 999.48 | PyPI Package | A4 (protocol skeleton) | open |
| 999.49 | Install Verification | A4 (human exp) | open |
| 999.50 | 5-Minute Quickstart | A4 (human exp) | open |
| 999.51 | Windows Robustness | A4 (protocol skeleton) | open |
| 999.52 | Proof Engineering Memory | A3 (data recording) + A1 (L2) | open |

### Items 999.60–999.78 (HCI gap analysis + wow-harness)

| Item | Title | Axis | Status |
|------|-------|------|--------|
| 999.60 | Human-Readable Status/Next | A4 (human exp) | open |
| 999.61 | First-Run Onboarding | A4 (human exp) | open |
| 999.62 | Jargon Cleanup | A4 (human exp) | open |
| 999.63 | CLI Progressive Disclosure | A4 (human exp) | open |
| 999.64 | Natural-Language Steering | A5 (agent interface) | open |
| 999.65 | Progress Indicator | A4 (human exp) | open |
| 999.66 | Session Summary/Handoff | A4 (human exp) | open |
| 999.67 | Change Log/Diff | A4 (human exp) | open |
| 999.68 | Checkpoint Feedback | A4 (human exp) | open |
| 999.69 | Idea Packet Bypass | A4 (human exp) | open |
| 999.70 | Error Messages for Humans | A4 (human exp) | open |
| 999.71 | Default download-source | A1 (L0) | open |
| 999.72 | Crash Recovery | A4 (protocol skeleton) | open |
| 999.73 | Mechanical Verification | A5 (agent governance) | open |
| 999.74 | Context Injection + Dedup | A5 (agent governance) | open |
| 999.75 | Schema-Level Agent Isolation | A5 (agent governance) | open |
| 999.76 | JSONL Metrics → Self-Evolution | A3 (data recording) | open |
| 999.77 | Derivation Loop Detection | A4 (execution strategy) | open |
| 999.78 | Manifest-as-Truth | A3 (data recording) | open |

### Items 999.79–999.86 (DeepXiv + Graphify integration and post-E2E follow-up)

| Item | Title | Axis | Status |
|------|-------|------|--------|
| 999.79 | DeepXiv Post-Registration Enrichment | A1 (L0) | open → Phase 165.5 |
| 999.80 | Physics-Adapted Concept Graph | A1 (L0) | open → Phase 165.5 |
| 999.81 | Graph-Based L1 Intake Extension | A1 (L1) | open → Phase 165.5 |
| 999.82 | Progressive Reading in L0→L1 | A2 (L0→L1) | open → Phase 165.5 |
| 999.83 | Graph Analysis Tools L1→L2 | A2 (L1→L2) | open → Phase 165.5 |
| 999.84 | Obsidian Concept Graph Export | A1 (L1) | open → Phase 165.5 |
| 999.85 | MIT Attribution | A3 (license metadata) | open → Phase 165.5 |
| 999.86 | Concrete L0 Source Handoff | A4 (human exp) + A2 (L0→L1) | implemented → Phase 166 |

### ROADMAP Phases

| Phase | Title | Axis |
|-------|-------|------|
| 165 | Real Topic E2E Validation | all (diagnostic) |
| 165.1 | Proof Engineering Knowledge | A1 (L2) + A3 |
| 165.2 | Mode Envelope + Literature | A4 (strategy) + A2 (L1→L2) |
| 165.3 | HCI Foundation | A4 (human exp) |
| 165.4 | Agent Governance | A5 |
| 165.5 | L0/L1 Integration: DeepXiv + Graphify | A1 (L0+L1) + A2 (L0→L1) |
| 165.6 | Public Front Door Real-Topic Proof | A4 (human exp) + A2 (L0→L1) |
| 166 | Public Front Door L0 Source Handoff | A4 (human exp) + A2 (L0→L1) |
| 166.1 | Contentful Source Registration Default | A1 (L0) + A2 (L0→L1) |

## Verification: Axis Coverage

Every backlog item (999.1–999.86) and every ROADMAP phase maps to at least
one axis. No orphans. Items that span two axes are tagged with primary first.

### Open items by axis (priority order):

- **A4 (human experience)**: 999.60–999.63, 999.65–999.70 (10 items) — highest priority
- **A5 (agent governance)**: 999.64, 999.73–999.75 (4 items) — second priority
- **A1 (layer-internal)**: 999.1, 999.27, 999.29, 999.40, 999.46, 999.71, 999.79, 999.80, 999.81, 999.84 (10 items)
- **A2 (inter-layer)**: 999.30, 999.33, 999.41, 999.47, 999.82, 999.83 (6 items)
- **A3 (data recording)**: 999.28, 999.32, 999.34, 999.37, 999.76, 999.78, 999.85 (7 items)
- **A4 (protocol skeleton)**: 999.6, 999.7, 999.31, 999.48, 999.51, 999.72 (6 items)
- **A4 (execution strategy)**: 999.21, 999.22, 999.38, 999.42, 999.77 (5 items)
- **A5 (agent interface)**: 999.44 (1 item)
