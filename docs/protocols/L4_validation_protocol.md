# L4 Validation Protocol

Domain: Point (L4)
Authority: subordinate to AITP SPEC S3.
References: validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md,
validation/EXECUTION_PROTOCOL.md, VERIFICATION_BRIDGE_PROTOCOL.md,
GAP_RECOVERY_PROTOCOL.md.

---

## 4.1. Role

L4 is the surface that decides whether a candidate survives explicit checking.
It is NOT just "execution" — it is the adjudication layer.

**Hard rule:** L4 does not write directly to L2. All L4 results must return
through L3-R. This prevents validated-but-misinterpreted results from entering
trusted knowledge.

## 4.2. Validation Types

### Numerical Validation
- Benchmark runs against known results.
- Convergence checks.
- Parameter sweeps within declared regimes.
- Tolerance and error budgets.

**Coverage:** Partially implemented. Numerical validation occurs when the
topic enters verify mode with computational candidates, but there is no
dedicated numerical validation framework.

### Analytical Validation
- Limiting cases (do formulas reduce correctly in special limits?).
- Dimensional analysis (do equations have correct dimensions?).
- Symmetry checks (do results respect declared symmetries?).
- Self-consistency (are different parts of the derivation compatible?).

**Coverage:** Partially implemented via analytical cross-check surface in
`validation_review_service.py`. The implementation provides structured
analytical checks but does not systematically enforce all four checks.

### Symbolic Validation
- SymPy / Mathematica lane for symbolic verification.
- Automated algebraic simplification and equivalence checking.
- Identity verification against known formulas.

**Coverage:** NOT YET IMPLEMENTED. No SymPy or Mathematica integration exists.
This remains a protocol aspiration.

### Formal Validation
- Proof obligation checking (see PROOF_OBLIGATION_PROTOCOL.md).
- Lean bridge for formal theorem verification.
- Statement compilation before proof repair.

**Coverage:** Partially implemented. The Lean LSP MCP server provides proof
checking capabilities. The verification bridge protocol defines the handoff.
The `lean_build`, `lean_verify`, and related tools support formal validation.

### Human Validation
- Regression questions answered by the human oracle.
- Understanding gates: can the system explain the result coherently?
- Reproduction gates: can the system reproduce a known result?

**Coverage:** ~10% implemented. Human validation occurs through decision points
and popup gates, but the systematic regression question and understanding gate
framework is not implemented as a structured L4 surface.

## 4.3. Trust Audit

Every L4 validation should produce a trust audit that records:
- what was checked,
- how it was checked (method, tool, reference),
- what passed,
- what failed or was inconclusive,
- trust boundary: what is locally closed vs. still open,
- execution provenance: where the heavy computation happened.

### Actual Implementation

The current trust audit is simpler than the protocol envisions. The
implementation records:
- `operation_trust_audit.jsonl` — operation-level trust records,
- validation review bundles — aggregated review results,
- formal theory sub-reviews — structured theory validation records.

The full trust audit fields (execution provenance, trust boundary
classification, method/reference tracking) are NOT yet systematically
recorded.

See: `validation/BASELINE_REPRODUCTION_AND_UNDERSTANDING_GATES.md`.

## 4.4. Formal Theory Sub-Reviews

The implementation provides structured formal theory sub-reviews, which are
NOT in the original protocol but represent significant implementation:

### Faithfulness Review
- Does the formalization faithfully represent the informal statement?
- Checks for meaning-preserving translation.

### Comparator Review
- Are comparison operations well-defined and consistent?
- Checks for ordering and equivalence correctness.

### Provenance Review
- Is the provenance chain from source to formal statement complete?
- Checks for traceability of formal claims.

### Prerequisite Review
- Are all prerequisites stated and available?
- Checks for dependency completeness.

These sub-reviews are managed by `validation_review_service.py` and produce
structured review records.

## 4.5. Validation Review Bundle

The implementation aggregates individual reviews into a validation review
bundle:
- Collects sub-review results (faithfulness, comparator, provenance,
  prerequisite),
- Produces an overall validation status,
- Records the bundle as a durable artifact.

This aggregation is NOT described in the original protocol.

## 4.6. Analytical Cross-Check Surface

The implementation provides an analytical cross-check surface that:
- Compares candidate claims against known results,
- Detects contradictions between candidate and existing L2 knowledge,
- Produces structured cross-check records.

## 4.7. Comparison Validation Mode

A validation mode where the candidate is checked by comparison to a known
reference result. This is distinct from analytical validation in that it
requires an explicit reference result as ground truth.

## 4.8. Execution Protocol

Before non-trivial L4 execution:
1. Materialize a concrete execution plan.
2. Make explicit: lane, runtime target, resource scale, pass/failure contract.
3. If runtime target or resource class is not already approved, stop until
   the operator confirms.

See: `validation/EXECUTION_PROTOCOL.md`.

## 4.9. Verification Bridge

When validation requires external tools or formal systems:
- `VERIFICATION_BRIDGE_PROTOCOL.md` governs the handoff.
- The bridge produces: proof obligations, proof states, lean-ready packets.
- Bridge results return through L3-R, not directly to L2.

## 4.10. Gap Recovery

When L4 discovers a gap:
1. Classify the gap kind (missing source, missing derivation, missing
   capability, contradiction).
2. Create or update the relevant open gap.
3. Route to gap recovery:
   - `GAP_RECOVERY_PROTOCOL.md` for recovery workflow.
   - Follow-up source task for literature recovery.
   - Sub-topic spawning for independent investigation.
4. Record the gap honestly. Do not fake closure.

**Implementation note:** Gap classification (missing_source, missing_derivation,
missing_capability, contradiction) is NOT YET IMPLEMENTED as a first-class
dispatch mechanism. The `gap_map.md` renderer exists but does not emit gap
kinds. See `followup_lifecycle.md` FL7 for the routing protocol.

## 4.11. Validation Outcomes

The protocol defines six validation outcomes:

| Outcome | Meaning | Next Step |
|---------|---------|-----------|
| `pass` | Candidate meets all validation criteria | Route to L3-D for distillation |
| `partial_pass` | Some criteria met, others inconclusive | Determine if partial result is useful; route gaps |
| `fail` | Candidate does not meet criteria | Record failure; return to L3-A for revision |
| `contradiction` | Candidate contradicts known results | Route to conflict resolution; open gap |
| `stuck` | Cannot complete validation (missing capability/source) | Escalate; route to capability loop or L0 callback |
| `timeout` | External execution did not complete | Classify as stuck or retry with modified plan |

### Actual Implementation

The code currently uses a simpler outcome vocabulary:
- `ready` — candidate is ready for promotion consideration (maps to `pass`),
- `blocked` — candidate cannot proceed (maps to `fail` / `stuck`).

The remaining four outcomes (`partial_pass`, `contradiction`, `timeout`,
and the distinction between `fail` and `stuck`) are NOT yet distinguished
by the code.

## 4.12. Iterative L3-L4 Loop

L3 and L4 form an iterative loop:
```
L3-A (form candidate) -> L4 (validate) -> L3-R (integrate result) -> L3-D (prepare for promotion)
     ^                                                           |
     +-----------------------------------------------------------+
```

This loop continues until:
- the candidate passes validation and enters promotion pipeline, or
- the candidate is revised into a new candidate, or
- the candidate is rejected, or
- a hard blocker requires human intervention.

## 4.13. Implementation Status

### Currently implemented
- Validation review service with bundle aggregation.
- Formal theory sub-reviews (faithfulness, comparator, provenance, prerequisite).
- Analytical cross-check surface.
- Comparison validation mode.
- Lean LSP integration for formal validation (partial).
- Human validation through decision points and popup gates (~10%).
- Simple validation outcomes (ready/blocked).
- Operation trust audit (simplified).
- Verification bridge protocol.

### Not yet implemented
- Symbolic validation (SymPy/Mathematica) — 0%.
- Full human validation framework (regression questions, understanding gates) — ~10%.
- Six-outcome validation vocabulary (only ready/blocked used).
- Full trust audit fields (execution provenance, trust boundary classification).
- Gap classification as first-class dispatch.
- Numerical validation framework (dedicated).
- Systematic analytical validation (all four checks).

## 4.14. What L4 Should Not Do

- Write directly to L2.
- Treat plausibility as validation.
- Accept proxy evidence for declared validation criteria.
- Silently weaken validation criteria to make a candidate pass.
- Decide that coverage equals correctness.
- Skip the trust audit.
- Collapse six outcomes into two without recording the nuance.
