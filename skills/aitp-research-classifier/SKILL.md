---
name: aitp-research-classifier
description: Classify the research mode of a topic using semantic reasoning instead of keyword matching. Load before session-start or resume to ensure research mode is recorded.
---

# AITP Research Mode Classifier

## Environment gate

- This skill runs inside an AITP session. Confirm AITP routing has already claimed the task.
- If the topic already has a recorded research mode in `classification_contract.jsonl`, skip to the "Verify or override" section.

## Classification task

Determine which research mode best describes the current topic from these four options:

| Mode | When to choose |
|------|---------------|
| `formal_derivation` | The topic centers on mathematical proof, formal derivation, theorem verification, operator algebra, bootstrap arguments, consistency conditions, or any argument that must close by logical deduction rather than numerical evidence. |
| `toy_model` | The topic studies a simplified or lattice model (Ising, Heisenberg, spin chain, TFIM, SU(2) lattice, MPS/DMRG) to extract qualitative or semi-quantitative physics. The model is analytically or numerically tractable at small system sizes. |
| `first_principles` | The topic uses ab initio methods (DFT, GW, QSGW, BSE, QMC, Hartree-Fock) or computational chemistry / condensed matter codes (VASP, Quantum ESPRESSO, ABINIT, LibRPA) to compute observables from electronic structure. Convergence, basis sets, and benchmark comparison are central concerns. |
| `exploratory_general` | The topic does not clearly fit the above categories. This includes literature surveys, open-ended idea exploration, physics discussion without a bounded computational or formal target, and topics still being scoped. |

## Reasoning priority

1. **Explicit declaration**: If the user, topic contract, or source material explicitly names a research mode (e.g., "this is a first-principles calculation" or "we study the Heisenberg spin chain"), use that mode.
2. **Research question semantics**: Read the research question and its target claims. What kind of answer would close the question? A proof → `formal_derivation`. A numerical result from a lattice model → `toy_model`. A converged ab initio observable → `first_principles`. An open-ended exploration → `exploratory_general`.
3. **Contextual signals**: Look at the surrounding materials — cited papers, named methods, mentioned codes, symbols used. These support but should not override the above.
4. **Default**: If no clear signal, choose `exploratory_general`.

## Recording the classification

After reasoning, call the MCP tool:

```
aitp_record_classification(
    topic_slug=<current topic>,
    classification_type="research_mode",
    value=<one of: exploratory_general, first_principles, toy_model, formal_derivation>,
    rationale=<1-3 sentence explanation of why this mode was chosen>,
    signals_used=<list of key signals that informed the decision>,
    source="ai_reasoning"
)
```

## Verify or override

If a prior classification exists, check whether the current human request or topic evolution has changed the research character. If so, record a new classification (the contract is append-only). If the prior classification is still valid, do nothing.

## Hard rules

- Do not use substring or keyword matching. Read the full context and reason semantically.
- A topic can have multiple classifications over time; the latest one is active.
- Never skip recording. The classification must be durable before execution continues.
