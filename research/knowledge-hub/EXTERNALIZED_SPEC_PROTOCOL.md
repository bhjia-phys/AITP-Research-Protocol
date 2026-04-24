# Externalized Specification and Reproducibility Protocol

This document formalizes two principles that distinguish disciplined AI-assisted
physics research from ad-hoc code generation:

1. **Externalized specifications** — intermediate technical specs that capture
   implementation-critical knowledge absent from source literature
2. **Absolute reproducibility** — every conversation, spec, and code version
   is preserved with structured naming

These principles are grounded in quantitative evidence. The DMRG-LLM study
([arXiv:2604.04089](https://arxiv.org/abs/2604.04089)) showed that a
multi-stage workflow with an externalized intermediate specification achieved
**100% success** across 16 LLM combinations, compared to **46% for direct
zero-shot implementation**. The critical factor was not the formal document
structure but the *externalized domain knowledge* contained within it —
explicit index conventions, contraction orderings, and memory constraints that
source papers leave implicit.

---

## 1. Core principle

The **externalized specification** is a first-class research artifact, not a
byproduct or a summary. It serves as a compiler intermediate representation
between theoretical source material and executable code.

```
Source literature     Externalized spec        Executable code
(papers, reviews)  -> (this protocol)      -> (implementation)
   implicit           explicit, reviewed        follows spec
   ambiguous          unambiguous               verifiable
   incomplete         completed by domain       tested against
                      knowledge
```

AITP's derive-first workflow already requires LaTeX derivation before code.
This protocol sharpens that requirement: the derivation must explicitly
externalize the implementation-critical knowledge that the source literature
omits.

---

## 2. The spec artifact

An externalized specification must contain the following elements. Not every
element applies to every domain; the domain skill declares which are mandatory
through the `on_spec_quality_check` hook.

### 2.1 Mandatory elements (when applicable)

| Element | Description | Example |
|---------|-------------|---------|
| **Index conventions** | Tensor indices, their ranges, storage order (row-major vs column-major) | "Bond indices run from 1 to L, physical indices from 1 to d, chi-bond indices from 1 to D" |
| **Contraction orderings** | Which contractions happen first, and why | "Contract left environment first (O(D^3)), then right (O(D^2)), avoiding O(D^4) intermediate" |
| **Memory constraints** | Matrix-free requirements, maximum storage bounds | "Never form W_full explicitly; use Lanczos with matrix-free H\|x> product" |
| **Numerical stability** | Conditioning requirements, safe ranges, overflow/underflow guards | "Singular values below 1e-12 should be truncated, not inverted" |
| **Gauge choices** | Left/right canonical forms, normalization conventions | "Left-canonical MPS: sum A^dagger A = I; right-normalize before truncation" |
| **Symmetry handling** | How point group, time-reversal, or spin symmetries constrain implementation | "For SOC calculations, time-reversal symmetry doubles the basis; off-diagonal Sigma blocks are non-zero" |
| **Domain of validity** | Under what conditions this specification is correct | "Valid for gapped systems with D <= 40; metallic systems require Fermi-surface sampling" |

### 2.2 What source literature typically omits

Papers and review articles are written for human experts who fill in gaps from
experience. An externalized spec must make these gaps explicit:

- **Implicit assumptions**: "We assume the system is gapped" (never stated)
- **Convention differences**: "Our `i` is their `j`" (different papers use different conventions)
- **Computational shortcuts**: "We never store the full Hamiltonian" (obvious to experts, invisible to LLMs)
- **Failure modes**: "This algorithm fails for degenerate eigenvalues" (known but unstated)

### 2.3 Spec quality criteria

A spec is ready for human review (Gate G0) when it passes these checks:

1. **Completeness**: Every assumption the code will depend on is stated
2. **Precision**: No ambiguity in index conventions or operation ordering
3. **Testability**: The spec predicts specific numerical behavior that can be verified
4. **Human-reviewable**: A domain expert can verify correctness without running code
5. **Model-agnostic**: Any LLM can implement from the spec without access to the conversation that produced it

The domain skill's `on_spec_quality_check` hook defines how many of these
criteria must pass (minimum 4 by default).

---

## 3. Spec lifecycle

The externalized spec maps to AITP phases as follows:

```
Phase 0 (scoping)       -> Identify what knowledge needs externalization
Phase 1 (derive)        -> Produce the spec, iterate with human review
         *** Gate G0: Spec approved ***
Phase 2 (plan)          -> Plan implementation against the approved spec
Phase 3 (implement)     -> Code strictly follows the spec
Phase 4 (smoke test)    -> Verify code matches spec on minimal system
Phase 5 (benchmark)     -> Verify spec-predicted behavior matches numerics
Phase 6 (debug)         -> If mismatch, diagnose: spec error or code error?
Phase 7 (production)    -> Spec + code promoted together to L2
```

### 3.1 Phase 0: Knowledge gap identification

When scoping a feature or computation, the domain skill identifies which
elements from §2.1 need to be externalized. This is returned via the
`on_scope` hook.

### 3.2 Phase 1: Spec production

The spec is produced alongside the LaTeX derivation in
`docs/sections/02_derivation.tex`. It may also be captured as a separate
structured document in `archive/specs/`.

The spec may go through multiple versions:

- `spec-v1.md` — initial LLM output (may contain errors)
- `spec-v2.md` — after human review corrections
- `spec-final.md` — approved version that code will follow

### 3.3 Gate G0: Spec approval

The human reviews the spec for:

- Correctness of all stated conventions and constraints
- Completeness of failure mode enumeration
- Whether the predicted behavior is physically reasonable
- Whether the domain of validity is honestly stated

**The spec is not approved until the human explicitly says so.** This is the
same gate as in the derive-first workflow (see
`PROJECT_STRUCTURE_CONVENTION.md`).

### 3.4 Phase 3: Spec-driven implementation

Code should include comments referencing specific elements of the approved
spec:

```cpp
// Implements contraction ordering from spec §2.2: left env first (O(D^3))
// Memory constraint: matrix-free, never form H_full (spec §2.3)
```

### 3.5 Phase 6: Spec-code mismatch diagnosis

When validation fails, the first diagnostic question is:

> **Is this a spec error or a code error?**

- If the spec is wrong -> go back to Phase 1, update spec, re-approve
- If the spec is right but code deviates -> fix the code
- If the spec is incomplete -> extend the spec with the missing knowledge

This distinction prevents the common failure mode of "fixing" code to pass
tests while silently violating the physics.

---

## 4. Cross-model handoff

The model that produces the spec (Phase 1) and the model that implements from
it (Phase 3) can be different. The DMRG-LLM study tested 16 combinations of
4 foundation models and found that **all spec-guided combinations succeeded**,
regardless of which model produced the spec and which produced the code.

### 4.1 Model roles

| Role | Phase | Responsibility |
|------|-------|---------------|
| Spec model (LLM-1) | Phase 1 | Parse source literature, externalize knowledge, produce spec |
| Code model (LLM-2) | Phase 3 | Read spec, implement code, follow stated conventions exactly |

### 4.2 Domain skill recommendations

Domain skills declare `recommended_model_combos` in their manifest to guide
model selection:

```json
"recommended_model_combos": [
  {
    "spec_model": "claude",
    "code_model": "claude",
    "typical_hitl_rounds": 5,
    "notes": "Same-model: more HITL rounds but stable"
  },
  {
    "spec_model": "claude",
    "code_model": "gemini",
    "typical_hitl_rounds": 1,
    "notes": "Cross-model: spec quality dominates"
  }
]
```

### 4.3 The spec is the contract

The spec must be **model-agnostic**: any competent LLM should be able to
implement from it without access to the conversation that produced it. This
means:

- No references to "what we discussed earlier"
- No implicit context from the spec-producing conversation
- All assumptions stated explicitly in the spec document itself

---

## 5. Reproducibility requirements

### 5.1 What must be preserved

All materials associated with a research project must be archived:

| Material | Location | Format |
|----------|----------|--------|
| Conversation transcripts | `archive/conversations/` | Unedited Markdown |
| Spec versions | `archive/specs/` | Versioned Markdown |
| Code versions | `archive/code/` | Source files with pass/fail status |
| HITL log | `archive/hitl-log.md` | Markdown with YAML frontmatter |

### 5.2 Naming convention

All archived materials follow a structured naming convention:

```
{artifact}-{model1}-{model2}#{round}-{status}.{ext}
```

Where:

- `artifact`: what was produced (`spec`, `code`, `conversation`)
- `model1`: model that produced the spec (blank for zero-shot)
- `model2`: model that produced the code
- `round`: iteration number (1, 2, 3, ...)
- `status`: `Pass` or `Fail`
- `ext`: file extension

Examples:

```
archive/conversations/spec-claude-1.md
archive/specs/spec-claude-v1.md
archive/specs/spec-claude-v2.md
archive/specs/spec-final.md
archive/code/code-claude-claude#1-Fail.py
archive/code/code-claude-claude#2-Fail.py
archive/code/code-claude-claude#3-Pass.py
archive/code/code-claude-gemini#1-Pass.py
```

### 5.3 HITL log schema

```json
{
  "project": "project-name",
  "entries": [
    {
      "round": 1,
      "phase": "3",
      "spec_model": "claude",
      "code_model": "claude",
      "status": "Fail",
      "human_feedback_summary": "Off-diagonal Sigma blocks computed with wrong gauge",
      "timestamp": "2026-04-15T10:30:00Z",
      "artifact_path": "archive/code/code-claude-claude#1-Fail.py"
    }
  ]
}
```

### 5.4 Archive rules

1. **Append-only**: never modify or delete past archive entries
2. **Unedited**: conversation transcripts are preserved exactly as they occurred
3. **Complete**: every round must have an entry, including failures
4. **Traceable**: each entry links to the corresponding artifact file

---

## 6. Relationship to existing documents

| Document | Relationship |
|----------|-------------|
| `FEATURE_DEVELOPMENT_PLAYBOOK.md` | This protocol sharpens the Phase 1 (derive) and Phase 3 (implement) requirements |
| `PROJECT_STRUCTURE_CONVENTION.md` | Adds the `archive/` directory to the project folder structure |
| `DOMAIN_SKILL_INTERFACE_PROTOCOL.md` | Adds `reproducibility` and operation-level `spec_required` / `min_path` fields to the domain manifest schema |
| `FIRST_PRINCIPLES_LANE_PROTOCOL.md` | Domain-specific spec requirements come from the domain skill's `on_spec_quality_check` hook |

---

## 7. Summary

| Principle | What it means | Why it matters |
|-----------|--------------|----------------|
| Externalized spec | First-class artifact capturing implicit domain knowledge | 100% vs 46% success ([arXiv:2604.04089](https://arxiv.org/abs/2604.04089)) |
| Spec before code | Human-approved spec gates all implementation | Prevents physics errors from propagating |
| Cross-model handoff | Spec model != code model is allowed | Leverages each model's strengths |
| Absolute reproducibility | All materials preserved, structured naming | Enables quantitative evaluation |
| HITL round tracking | Count human feedback per model combo | Predicts effort, optimizes model selection |
| Append-only archive | Never modify past entries | Honest history, no retroactive edits |
