# Formal-theory validation starter pack

This pack provides bounded validation guidance for topics in the
`formal_derivation` lane (template_mode=formal_theory).

## Scope

Formal-theory validation checks whether a mathematical derivation or proof
attempt is internally consistent and closes against its stated axioms. It does
not attempt to verify physical correctness beyond the mathematical structure.

## Validation checklist

1. **Goal-state audit**: Does the proof attempt close the stated goal? Check
   the `research_question.contract.json` target claims against the final
   proof state.

2. **Axiom audit**: Are all invoked axioms, lemmas, or theorems either
   (a) in the source basis, (b) in the L2 canonical index, or (c) explicitly
   marked as conjecture?

3. **Lean bridge check** (when applicable): If a Lean formalization exists,
   does it compile without errors or `sorry` placeholders?

4. **Cross-check against source**: Does the derivation reproduce at least one
   key result from the registered L0 source material?

## Concrete example

The `witten-tp-formal-close-*` topics use this pack to validate topological
phase classification proofs against Witten's original paper. The validation
records:

- the theorem statement from the contract,
- the proof sketch steps and their closure status,
- any axioms that lack L2 backing,
- the Lean compilation result (if applicable).

## Input/output contract

Inputs:
- `research_question.contract.json` (target claims and scope)
- L0 source index (source basis)
- L2 canonical index (backed axioms and lemmas)
- Optional: Lean source file for bridge compilation

Outputs:
- `validation/execution-result.json` with `pack_type: "formal_theory"`
- `validation/execution-task.json` with the checklist items as tasks

## Non-claims

This pack does not:
- guarantee physical truth of the mathematical result,
- replace expert peer review,
- validate numerical correctness of any computation in the proof.
