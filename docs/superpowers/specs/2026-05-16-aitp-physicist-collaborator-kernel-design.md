# AITP Physicist Collaborator Kernel Design

Status: design target

Date: 2026-05-16

## Goal

Upgrade AITP from a protocol harness into a persistent physicist collaborator
kernel.

The goal is not only to enforce `L0 -> L1 -> L3 -> L4 -> L2`. The goal is to
make an AI research assistant behave like a useful theoretical-physics
collaborator:

- it can choose the next physics move without asking for constant supervision,
- it can use physical intuition to propose routes and checks,
- it cannot silently promote intuition into trusted knowledge,
- it can handle formal theory, toy models, and first-principles/code-method
  work without forcing the user to pick a rigid top-level mode,
- it preserves enough state that a later session can recover what happened,
  why it happened, what is still uncertain, and what the next useful action is.

This design intentionally allows deeper architectural change than a narrow
compatibility-preserving patch. Backward compatibility is valuable, but it is
secondary to making the protocol scientifically useful.

## Problem

The current implementation has the right protocol instincts but still behaves
too much like a staged harness:

- stage gates validate artifact shape more reliably than claim meaning,
- `lane` is too coarse to express the evidence structure of a live research
  claim,
- `aitp_get_execution_brief` often returns mechanical next work instead of a
  physics-shaped next move,
- code-method work is treated mostly as numerical evidence, but real
  computational physics also needs formula-to-code translation checks,
- L4 validates candidates, but the deeper object that needs validation is the
  claim plus its scope, assumptions, evidence profile, and failure modes,
- human interaction is not yet tied to explicit epistemic triggers.

The failure mode to avoid is a polished wrapper around free-form chat. AITP
should not only make the AI more orderly. It should make the AI more useful as
a research collaborator by externalizing the epistemic discipline that good
physicists already practice.

## Core Decision

Use one top-level AITP protocol, but make claim-level evidence profiles the
unit of scientific control.

Do not split AITP into separate products such as "formal theory mode" and
"code method mode." Real topics mix these modes. Instead, each active claim
declares an evidence profile:

- `formal_theory`
- `toy_numeric`
- `code_method`
- `literature_synthesis`
- `mixed`

The topic remains unified. The evidence obligations vary by claim and by route.

## Collaborator Kernel

Introduce a protocol kernel made of seven responsibilities.

### 1. State Observer

Reads durable topic state and summarizes:

- current question,
- active claim inventory,
- source and evidence basis,
- route decisions,
- blockers,
- open human checkpoints,
- last meaningful evidence return,
- next possible transitions.

This observer should feed `aitp_get_execution_brief`.

### 2. Evidence Profile Resolver

Classifies the current uncertainty by evidence structure, not by user-facing
topic label.

Examples:

- a quantum-gravity definition question maps to `formal_theory`,
- a TFIM finite-size check maps to `toy_numeric`,
- a LibRPA QSGW implementation check maps to `code_method`,
- a paper-reading synthesis maps to `literature_synthesis`,
- a GW method paper plus code implementation audit maps to `mixed`.

The resolver may infer a default, but the active claim must record the chosen
profile and the reason.

### 3. Claim Ledger

Maintains claims as first-class objects before L2 promotion.

Each important claim should carry:

- `claim_id`,
- `statement`,
- `scope`,
- `assumptions`,
- `non_claims`,
- `evidence_profile`,
- `confidence_state`,
- `supporting_evidence`,
- `missing_evidence`,
- `strongest_failure_mode`,
- `human_checkpoint_triggers`.

The confidence state is not a single "correct/incorrect" flag. It is one of:

- `hypothesis`,
- `coherent`,
- `source_anchored`,
- `stress_tested`,
- `human_accepted`,
- `promotable`,
- `rejected`,
- `deferred`.

The AI may autonomously move a claim from `hypothesis` to `coherent` or
`source_anchored` when evidence supports it. It must not move a claim to
`human_accepted` or `promotable` without the relevant checkpoint.

### 4. Next-Move Planner

Turns protocol state into a physics-shaped next action.

The public execution brief should include:

```yaml
next_physical_move:
  action: ""
  why: ""
  claim_being_advanced: ""
  evidence_profile: ""
  expected_evidence_gain: ""
  allowed_autonomy: []
  human_checkpoint: null
  do_not_do_yet: []
```

The planner is where AI physical intuition is allowed to operate. It may
choose whether the next useful move is reading, derivation, toy computation,
benchmarking, formula-code mapping, debugging, or asking the human.

The planner must also name what it refuses to do yet.

### 5. Validation Contract Builder

Creates validation contracts from the claim's evidence profile.

For `formal_theory`, required checks may include:

- definition lock,
- assumption audit,
- derivation trace,
- symmetry or covariance check,
- limiting case,
- known-example comparison,
- counterexample search,
- literature equivalence or contradiction check.

For `toy_numeric`, required checks may include:

- minimal model statement,
- parameter regime,
- exact or semi-exact reference,
- convergence or finite-size trend,
- random seed and environment provenance,
- negative comparator,
- plot/table output provenance.

For `code_method`, required checks may include:

- formula-code map,
- unit and convention audit,
- input-output semantic map,
- parser/data-layout audit,
- minimal reproducible case,
- benchmark comparison,
- convergence/error budget,
- parallel consistency,
- source commit and runtime environment provenance.

For `literature_synthesis`, required checks may include:

- source role classification,
- claim-source map,
- cross-source agreement or disagreement,
- notation translation,
- regime comparison,
- unresolved contradiction register.

### 6. Human Checkpoint Manager

Human interaction should be triggered by epistemic conditions, not by generic
uncertainty.

The AI should ask the human when:

- there is a direction or novelty fork,
- definitions or assumptions require a research taste decision,
- a validation route, benchmark, or tolerance is underdetermined,
- the next action is expensive or risky,
- evidence contradicts known literature or trusted L2 memory,
- a claim is about to become `human_accepted` or `promotable`,
- the user has issued steering that changes the route.

The AI should not ask the human for low-cost checks it can run or record itself.

### 7. Surface Renderer

Renders the same state for different platforms:

- MCP result for Codex, Claude Code, OpenCode, or other agents,
- Markdown dashboard for humans,
- JSON state for machines,
- active checkpoint surfaces,
- promotion packet surfaces.

The renderer should hide protocol machinery when possible, but it must not hide
trust boundaries.

## L0-L4 Refit

### L0: Evidence Basis

Current role: source discovery and ingestion.

Target role: establish what evidence objects exist and what claims they can
support.

L0 should recognize source families:

- paper or preprint,
- book chapter or lecture note,
- code repository and commit,
- input deck,
- run output,
- benchmark reference,
- dataset,
- local derivation note,
- discussion or steering note.

L0 artifacts should answer:

- what is the evidence basis,
- which sources are load-bearing,
- which sources are only context,
- which claims each source can support,
- what evidence family is missing.

### L1: Understanding And Translation

Current role: reading and framing.

Target role: build a usable research model before execution.

For all profiles, L1 should create:

- bounded question,
- claim inventory,
- assumption ledger,
- convention snapshot,
- contradiction register,
- source-to-claim map.

For `code_method`, L1 should additionally create translation anchors:

- formula-code map skeleton,
- unit and convention table,
- array/index semantic table,
- workflow dependency map,
- parser/input-output boundary map.

### L3: Research Workbench

Current role: flexible derivation workspace.

Target role: claim-centered route execution.

L3 should record:

- route decisions,
- active claim under work,
- evidence profile selected for the claim,
- why this route has high information gain,
- attempts and dead ends,
- local checks run by the AI,
- human steering received,
- return payloads from failed L4 attempts.

For formal work, L3 actions look like:

- define,
- derive,
- trace,
- compare,
- find counterexample,
- narrow regime,
- distill claim.

For code-method work, L3 actions look like:

- map formula to code,
- isolate minimal case,
- audit units/conventions,
- audit parser and data layout,
- run cheap benchmark,
- debug workflow,
- estimate error budget,
- distill implementation claim.

### L4: Adversarial Validation

Current role: validate candidates.

Target role: attempt to falsify claims under their declared evidence profile.

L4 should not ask only "does this pass?" It should ask:

- what exact claim is being challenged,
- what would falsify it,
- which required checks were executed,
- which failure modes remain,
- what confidence state is allowed after this review,
- whether the result returns to L3, asks the human, or becomes promotable.

L4 pass should not always mean "validated." A pass may mean:

- source-anchored but not stress-tested,
- numerically supported but not converged,
- implementation-consistent but not physically interpreted,
- physically plausible but not promotable.

### L2: Reusable Memory

Current role: persistent knowledge graph.

Target role: only store reusable knowledge whose trust scope is explicit.

L2 promotion should require:

- claim statement,
- scope and regime,
- evidence profile,
- evidence bundle,
- validation result,
- non-claims,
- known failure modes,
- provenance,
- human or gate approval.

Negative results and failure modes should be promotable when they are
well-scoped and reproducible.

## Implementation Strategy

The implementation should proceed top-down, even if that touches central code.

### Phase 1: Core objects

Add a small kernel module for claim evidence:

- evidence profiles,
- confidence states,
- profile-specific obligations,
- helper functions to build next physical moves.

Extend candidate and validation schemas to carry these fields. Existing
candidates can default to `mixed` and `hypothesis` during migration.

### Phase 2: Execution brief

Make `aitp_get_execution_brief` return `next_physical_move` for every stage.

This is the critical adapter boundary for Codex and other agents. If this
brief is good, the model can behave like an AITP-aware physicist without
needing to expose every internal artifact to the user.

### Phase 3: Candidate and review flow

Update `aitp_submit_candidate` so candidates declare evidence profile, scope,
assumptions, non-claims, and failure mode.

Update `aitp_submit_l4_review` so review outcomes update confidence state
instead of blindly turning `pass` into `validated`.

### Phase 4: L0-L1 templates

Refit templates to support source-to-claim and formula-to-code translation
without forcing every topic to fill code-method fields.

### Phase 5: Human checkpoints

Materialize checkpoint triggers as durable runtime artifacts and expose them in
briefs and dashboards.

### Phase 6: Real-topic acceptance

Add acceptance scenarios for:

- formal theory definition/derivation topic,
- toy model numerical topic,
- GW/code-method formula-code translation topic,
- mixed literature plus implementation topic.

The current global test suite is not clean. This work should add targeted
acceptance tests first, then use broader cleanup as a separate hardening wave.

## Non-Goals

This design does not require:

- full autonomy,
- full proof assistant integration,
- full HPC execution automation,
- replacing Markdown topic state with a database,
- making the user pick rigid topic modes,
- treating AI intuition as evidence.

## Acceptance Criteria

The design is successful when a user can ask AITP to continue a research topic
and the system can answer:

- what claim is active,
- why this claim matters,
- which evidence profile governs it,
- what the next useful physics move is,
- what the AI can do autonomously,
- what requires human steering,
- what evidence is still missing,
- why the claim is or is not promotable.

For code-method work, the system must also answer:

- which formula is being implemented,
- where it appears in code,
- how units, indices, and conventions are mapped,
- which run or benchmark supports the result,
- which implementation artifact could still explain the observation.

For formal-theory work, the system must answer:

- which definition or theorem-like claim is active,
- which assumptions and examples support it,
- which counterexample or limit has been checked,
- which conceptual choice still requires human taste.

## Design Principle

AITP should let the AI think like a physicist, but force every consequential
judgment to leave a trail:

```text
intuition -> route -> claim -> evidence profile -> check -> confidence state
```

The assistant may be creative in the first two steps. The protocol must be
strict in the last four.
