# AITP v1.42 Architecture Vision

Status: reference vision document (last updated 2026-04-11)

This document captures the intended architecture after all 42 milestones are
complete, and explains why AITP exists as a distinct approach from letting
LLM agents do research directly.

## Target Architecture

```
Human Researcher
    |
    v
+-----------------------------------------------------+
|              H-Plane (Human Interaction Layer)        |
|  Can intervene at any layer: redirect, approve,       |
|  correct, pause, or approve L2 promotion              |
+-----------------------------------------------------+
               |
+---------------v---------------------------------------+
|              Topic Lifecycle Manager                 |
|  bootstrap -> loop -> status -> verify -> promote      |
|  Multi-topic parallel · pause/resume · bounded       |
|  auto-steps                                           |
+---------------+---------------------------------------+
               |
+---------------v---------------------------------------+
|           Task-Type x Lane Router                    |
|                                                      |
|  Task Types:          Lanes:                         |
|  | open_exploration    | formal_theory               |
|  | conjecture_attempt  | model_numeric               |
|  | target_driven_exec  | code_and_materials           |
|                                                      |
|  Each combination has an orchestration template that  |
|  shapes artifact footprint and validation path.        |
+---------------+--+----------+-----------+----------+
                |  |          |           |
                v  v          v           v
              +----+  +----+  +----+  +----+
              | L0 |  | L1 |  | L3 |  | L4 |
              +--+--+  +--+--+  +--+--+  +--+--+
                 |        |        |        |
                 v        v        v        v
              +-------------------------------------------+
              |         L2 Knowledge Network             |
              |  graph traversal · wiki compilation     |
              |  TPKN backend · Obsidian views          |
              +-------------------+-----------------------+
                                  |
                                  v
                            +-----------+
                            |    L5     |
                            | Publication |
                            |  Factory   |
                            +-----------+
```

## Layer Model

### L0 - Source Acquisition and Traceability

Register, grade, and trace every input to the research process.

- Paper registration (arXiv, local notes, code references)
- Citation graph traversal and BibTeX support
- **Source fidelity grading**: peer-reviewed > arXiv preprint > blog >
  informal notes > verbal claims
- **Relation labeling**: extracted / inferred / ambiguous
- Mixed-corpus graph seeding (papers + notes + code + image-derived
  descriptions)

L0 never claims anything is true. It only records where things come
from and how reliable the source is.

### L1 - Provisional Understanding

Build structured, explicit provisional models without promoting them.

- Assumption extraction (structural, not keyword-based)
- Reading depth tracking (scan vs close-read vs multi-pass cross-check)
- Contradiction detection and notation regime identification
- Derivation sketches and concept structure
- Regime identification

L1 explicitly marks every claim as "provisional".  Nothing in L1 is
trusted enough to reuse without re-verification.

### L3 - Exploratory Output (three sub-layers)

L3 is the workspace for untrusted but useful material.

- **L3-A** topic analysis: candidate claims, explanatory notes,
  tentative reusable material
- **L3-R** result integration: interprets what L4 returns, explains
  validation outcomes, decides what to do with failures
- **L3-D** distillation preparation: prepares material that may be
  reusable if it passes validation

Additional capabilities:

- Scratch mode for quick speculative work
- Negative-result documentation (failed paths are preserved)
- Intermediate calculation logs

### L4 - Validation and Adjudication

Enforce explicit verification before anything becomes reusable.

- Numerical validation (benchmark runs, convergence checks)
- **Analytical validation** (limiting cases, dimensional analysis,
  symmetry checks, self-consistency)
- Symbolic/analytical reasoning path (SymPy/Mathematica lanes)
- Trust audit with explicit trust-boundary documentation

**Hard rule**: L4 does not write directly to L2.  All L4 results must
return through L3-R, after which L3-D decides what is actually reusable.
This prevents validated-but-misinterpreted results from entering
trusted knowledge.

### L2 - Long-Term Trusted Memory

The only layer whose outputs survive across topics and sessions.

- Graph traversal and search with progressive-disclosure retrieval
- Wiki-style knowledge compilation (repeated reading and discussion
  outcomes become durable linked structures)
- TPKN backend bridge (typed knowledge network)
- Obsidian-friendly human-readable derived views
- Incremental graph rebuild and update hooks

**Requires explicit human approval** before any write.  L2 promotion
is a gate, not an automatic process.

### L5 - Publication Factory

Transform completed, validated topics into publication-grade outputs.

- Paper-grade writing packages
- Does not create new scientific truth
- Only formats and presents already-validated work

## Collaborator Memory System

```
+----------------------------------------------+
|        Collaborator Profile               |
|  Research taste · preferred formalisms    |
|  Physical intuition patterns               |
+----------------------------------------------+
|      Research Trajectory Memory            |
|  Cross-session research arc tracking       |
|  Mode learning from full research cycles   |
+----------------------------------------------+
|    Cross-Session Continuity                |
|  Pause/resume · cross-topic knowledge      |
|  reuse · context carrying after failure    |
+----------------------------------------------+
|    Negative-Result Retention              |
|  Failed paths preserved to avoid           |
|  repeated trial-and-error                  |
+----------------------------------------------+
```

The system learns from the human collaborator over time:
what kinds of validation they prefer, which formalisms they trust,
what counts as "interesting" versus "pedantic", and which research
modes they actually use in practice.

## Task-Type and Lane System

Three task types define the *intent* of a research step:

| Task Type | Description |
|-----------|-------------|
| `open_exploration` | Broad survey, no specific target, high tolerance for dead ends |
| `conjecture_attempt` | Testing a specific hypothesis, needs structured validation |
| `target_driven_execution` | Known goal, method, and success criteria |

Three lanes define the *domain* of a research step:

| Lane | Description |
|------|-------------|
| `formal_theory` | Proofs, derivations, formal structures, Lean bridges |
| `model_numeric` | Computational models, benchmark runs, numerical validation |
| `code_and_materials` | Code-backed algorithms, reproducibility, implementation |

Each task-type x lane combination has an orchestration template
that shapes artifact footprint, validation requirements, and promotion
criteria without replacing the L0-L4 layer model.

## H-Plane (Human Interaction Layer)

A cross-cutting interaction model that applies at any layer:

- Checkpoint/stop: pause at any point for human review
- Update: modify direction, scope, or assumptions mid-flow
- Approve: gate L2 promotion, approve publication
- Override: human can acknowledge a stuckness signal and choose to continue

The H-plane prevents interaction behavior from being smeared across
unrelated runtime notes.

## Runtime Shell

Every active topic maintains these durable surfaces under
`runtime/topics/<slug>/`:

- `research_question.contract.{json,md}` - what we are trying to answer
- `validation_contract.active.{json,md}` - what must be verified
- `topic_dashboard.md` - current state at a glance
- `promotion_readiness.md` - is this topic ready for L2?
- `gap_map.md` - what is still unknown or unverified
- `topic_completion.{json,md}` - regression manifest and gate checks
- `lean_bridge.active.{json,md}` - Lean export state
- `followup_reintegration.{jsonl,md}` - child topic return contracts

These are not decorative notes.  They are the bounded shell that tells
any agent what the active question is, what must be validated, whether
the topic is promotion-ready, and whether the honest next move is to
return to L0 for missing sources.

## AITP vs Agent Direct Research

### Concrete scenario

**Task**: "Research the role of von Neumann algebras in quantum gravity
and identify promising new directions."

### Agent direct approach

```
User asks question
  -> Agent searches web/papers
  -> Agent synthesizes LLM knowledge into an answer
  -> User asks follow-up
  -> Agent searches again, writes more
  -> Conversation ends, all context disappears
```

Problems:
- Evidence and speculation are mixed; unclear what came from papers vs LLM
- Cannot continue; next conversation starts from zero
- No record of which paths were explored and failed
- "Promising directions" are LLM improvisation without verification
- User cannot inspect the reasoning chain

### AITP approach

```
User: "Research von Neumann algebras in quantum gravity"
  -> AITP guides entry, creates topic shell
  -> Clarification: formal_theory lane or open_exploration?
     -> User: "Explore first"
  -> Selects open_exploration x formal_theory template

L0: Register relevant papers and existing knowledge
     -> Source fidelity grading
     -> Citation graph construction
     -> Output: source map + fidelity grades

L1: Provisional understanding
     -> Assumption extraction: "vN algebras may have a natural
        place in algebraic states of AQFT"
     -> Contradiction: "Connes' non-commutative geometry path is
        not fully compatible with standard vN algebra framework"
     -> Output: assumption cards + concept structure + contradiction notes
     -> Nothing here is "trusted"

L3-A: Analysis
     -> Candidate 1: vN algebras + algebraic states in AQFT
     -> Candidate 2: factor algebras + quantum reference frames
     -> Candidate 3: vN algebras + AdS/CFT algebraic boundary
     -> Output: candidate claims (marked "exploratory", not "trusted")

Human intervention (H-Plane):
  -> "Direction 2 looks most novel. Go deeper."
  -> AITP records: research judgment = direction 2 has momentum

L4: Validation
     -> Check factor algebra usage in quantum reference frames
     -> Analytical validation: limiting cases, dimensional consistency
     -> Discovery: known difficulty (Type II1 factors are unstable)
     -> Output: trust audit + gap map
     -> Forced return through L3-R, no direct L2 write

L3-R: Result integration
     -> Is the instability a real obstacle or a bypassable difficulty?
     -> Output: integration note

Human intervention:
  -> "I know that difficulty, but Type III factors might bypass it.
     Continue."
  -> AITP updates: stuckness = identified, human override = continue

... iterate ...

Eventually:
  -> User judges a direction mature enough, approves L2 promotion
  -> Knowledge written to TPKN backend (typed graph)
  -> Next conversation can retrieve L2 knowledge
  -> Entire process is auditable: why this path? what was validated?
     what remains uncertain?
```

### Summary of differences

| Dimension | Agent Direct | AITP |
|-----------|-------------|------|
| Evidence vs speculation | Mixed together | L0 sources strictly separated from L1/L3 inference |
| Validation | Agent says "verified" when confident | L4 mandatory verification + trust audit, results return through L3-R |
| Knowledge accumulation | Starts from zero every conversation | L2 persistent graph network, cross-session retrievable |
| Failed paths | Disappear when conversation ends | Scratch mode preserves negative results |
| Human role | Question-asker | Substantive decisions at L2 promotion, direction changes, H-plane |
| Auditability | Cannot reconstruct reasoning chain | Every step has artifacts: decision trace, gap map, trust boundary |
| Cross-session | Impossible | Topic state + multi-topic runtime + collaborator memory |
| Knowledge trustworthiness | Unknown what is LLM-fabricated | Promotion gate guarantees L2 content is verified + human-approved |
| Research judgment | Hardcoded scoring | Momentum/stuckness/surprise signals + collaborator preferences |

In short: an agent doing research directly is like a graduate student
with no notebook, no lab records, and no memory who confidently
improvises answers.  AITP is like a research collaborator who keeps a
notebook, records experimental results, knows which paths are dead ends,
and labels every statement as "confirmed" or "my best guess".
