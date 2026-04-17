# L3 Execution Protocol

Domain: Point (L3)
Authority: subordinate to AITP SPEC S3.
References: feedback/CANDIDATE.md, feedback/SPLIT_PROTOCOL.md,
feedback/STRATEGY_MEMORY_TEMPLATE.md.

---

## 3.1. Role

L3 is the workspace for untrusted but useful material. It is where the agent
forms candidates, explores conjectures, records failed attempts, and prepares
material that may become reusable if it passes L4 validation.

Nothing in L3 is trusted. Material here may become reusable IF it passes L4
and L2 promotion.

## 3.2. Five Sub-Planes

L3 is divided into five sub-planes that form the idea-to-candidate pipeline:

### L3-I — Ideation
- Record, connect, and refine vague ideas before they become formal candidates.
- Idea fragments, observations, pattern recognitions, research questions.
- Comparison with existing L2 knowledge to assess novelty.
- Output: structured ideas with novelty assessment and connections to other ideas.

### L3-P — Planning
- Translate ideas into executable research plans.
- Each plan specifies: steps, required knowledge (from L2), required tools
  (from domain skills), and checkpoints.
- Plans may be generated from domain-specific templates (e.g., feature
  development playbooks) or written from scratch.
- Output: plan artifacts with step sequence, tool dependencies, and checkpoint
  definitions.

### L3-A — Analysis
- Execute plans, form formal candidates.
- Candidate claims, explanatory notes, tentative reusable material.
- Conjectures and hypotheses with explicit claim statements.
- Source-bound analysis and comparison.
- Output: candidate claims marked "exploratory", not "trusted."

### L3-R — Result Integration
- Interprets what L4 returns.
- Explains validation outcomes.
- Decides what to do with failures.
- Bridge between validation and reusable preparation.

### L3-D — Distillation Preparation
- Prepares material that may be reusable.
- Structures candidates for promotion pipeline entry.
- Ensures promotion-readiness requirements are met.

**Hard rule:** L4 results return through L3-R before any promotion consideration.
This prevents validated-but-misinterpreted results from entering trusted
knowledge.

**Pipeline flow:** L3-I (idea) -> L3-P (plan) -> L3-A (candidate) -> L3-R
(result) -> L3-D (distillation). Each transition requires the previous
sub-plane to produce a concrete artifact.

## 3.3. Candidate Management

### Candidate Formation
A candidate is a tentative conclusion with:
- explicit claim statement,
- supporting derivation or calculation,
- assumptions and regime.

The protocol envisions but does not yet enforce:
- `evidence_level` field (source-grounded / derived / conjectured / speculative),
- `validation_requirements` field (explicit criteria for L4).

Currently candidates are represented as structured dictionaries in the
candidate ledger without these fields being mandatory.

### Candidate Ledger
The implementation maintains a candidate ledger that tracks:
- candidate ID and fingerprint (for deduplication),
- layer graph state transitions (L3-A → L3-R → L3-D),
- promotion status,
- associated gaps and followup tasks.

### Candidate Splitting
When a candidate mixes independent claims or mixes reusable content with
unresolved material:
1. `apply_candidate_split_contract` processes the split.
2. Individual bounded children are created in the candidate ledger.
3. Unresolved fragments are parked in the deferred buffer.
4. Split receipts record the operation.
5. Fingerprint deduplication prevents duplicate child candidates.

See: `feedback/SPLIT_PROTOCOL.md`, `followup_lifecycle.md` FL4.

### Wide Candidate Rule
A wide candidate (spanning multiple independent claims) must not be promoted
as one object. The correct route is always split, then promote bounded pieces.

## 3.4. Scratch Mode

L3 provides a scratch mode for quick speculative work:
- no formal candidate structure required,
- intermediate calculations and informal reasoning,
- negative-result documentation,
- failed paths are preserved to avoid repeated trial-and-error.

Scratch material is explicitly untrusted and must not be treated as
candidate-ready without explicit promotion to the candidate surface.

**Implementation note:** There is currently no formal bridge from scratch
material to the candidate surface. Scratch work exists in session context
and topic notes, but there is no structured scratch-to-candidate promotion
mechanism. This is a known gap.

## 3.5. Strategy Memory

L3 records helpful and harmful patterns:
- approaches that succeeded or failed in past topics,
- domain-specific patterns that transfer,
- collaborator-specific preferences.

See: `feedback/STRATEGY_MEMORY_TEMPLATE.md`.

**Implementation note:** Strategy/collaborator memory is NOT YET IMPLEMENTED
as a persistent cross-topic store. Individual topics record failure patterns
in topic-specific notes, but there is no cross-topic pattern extraction or
strategy memory retrieval.

## 3.6. Run Records

Each L3 execution leaves a run record. The protocol originally specified:

```
L3/runs/<run_id>/next_actions.md
L3/runs/<run_id>/result_summary.md
L3/runs/<run_id>/validation_plan.md
```

The actual implementation stores run-related information in the topic
runtime directory under:
- `runtime/topics/<topic_slug>/runtime/` — action decisions, decision traces,
  topic state.
- Candidate records in the candidate ledger (in-memory and JSONL).

The `L3/runs/` path structure is NOT currently used. Run records are managed
through the topic runtime artifacts instead.

## 3.7. Layer Graph State Machine

The implementation tracks candidate position through a layer graph state
machine. Each candidate has a layer state that transitions:

```
L3-I (ideation) -> L3-P (planning) -> L3-A (analysis) -> L3-R (result) -> L3-D (distillation)
                                                                             ↓
                                                                      promotion pipeline
```

State transitions are recorded in the candidate ledger. The state machine
enforces that candidates cannot skip sub-planes (e.g., no direct L3-I -> L3-A).

The L3-A <-> L4 loop is the core research cycle in `learn` and `implement`
modes: L3-A sends candidates to L4 for validation, L4 returns results to
L3-R, which may route back to L3-A for revision.

## 3.8. Auto-Promotion Pipeline

When a candidate meets auto-promotion criteria (see `promotion_pipeline.md` P4),
the code can route it directly to L2_auto without explicit human approval.
This pipeline:
1. Checks auto-promotion eligibility (review_mode: "ai_auto"),
2. Validates the candidate meets auto-promotion thresholds,
3. Writes to L2_auto canonical layer,
4. Records the promotion in the promotion ledger.

This bypasses L3-R and L3-D as separate steps but performs equivalent
checks inline.

## 3.9. TPKN Backend

The implementation provides a TPKN (Theoretical Physics Knowledge Network)
backend that:
- Stores canonical knowledge units (L2),
- Tracks unit families and relationships,
- Provides query and retrieval interfaces for L3 candidate formation.

Candidates may reference TPKN units as evidence or prior knowledge.

## 3.10. Loop Detection

The topic loop includes loop detection to prevent the agent from cycling
through the same actions without making progress:
- Tracks recent action fingerprints,
- Detects when the same action type is repeated without state change,
- Triggers intervention (escalation, mode change, or human checkpoint).

## 3.11. Proof Engineering Distillation

When a candidate involves formal theory material, L3-D includes proof
engineering distillation:
- Extract formalizable statements from candidates,
- Prepare Lean-compatible proof obligations,
- Record proof status (proved / partial / stuck).

See: `PROOF_OBLIGATION_PROTOCOL.md`, `VERIFICATION_BRIDGE_PROTOCOL.md`.

## 3.12. Implementation Status

### Currently implemented
- Three sub-planes (L3-A, L3-R, L3-D) with state machine transitions.
- Candidate management with ledger, fingerprinting, and deduplication.
- Candidate split contract with deferred fragment buffering.
- Auto-promotion pipeline (bypasses L3-R for eligible candidates).
- Layer graph state machine for candidate position tracking.
- TPKN backend for canonical knowledge storage and retrieval.
- Loop detection in topic execution.
- Proof engineering distillation pathway.
- Run records via topic runtime artifacts (not the L3/runs/ path).

### Not yet implemented
- Mandatory `evidence_level` field on candidates.
- Mandatory `validation_requirements` field on candidates.
- Scratch-to-candidate promotion bridge.
- Strategy/collaborator memory (cross-topic persistent store).
- `L3/runs/<run_id>/` path structure for run records.
- Negative-result documentation system.

## 3.13. What L3 Should Not Do

- Promote directly to L2 (except through auto-promotion pipeline).
- Treat exploratory results as validated.
- Discard failed paths without recording them.
- Claim coverage equals understanding.
- Substitute scratch material for validated candidates.
- Bypass L3-R interpretation for candidates that need human review.
