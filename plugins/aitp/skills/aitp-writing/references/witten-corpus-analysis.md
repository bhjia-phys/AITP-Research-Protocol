# Witten 2011-2026 Corpus Analysis For Theory Writing

This is the retained analysis from `witten-style-theory-note` 1.1.0, supplied
with the researcher's earlier Skill. Its reading claims and census describe
that earlier study; they were not independently repeated for AITP. Consult it
only when the source basis or a particular manuscript architecture is relevant.
The current writing instructions are in [aitp-writing](../SKILL.md).

## Purpose

This reference extracts reusable manuscript architecture from Edward Witten's
public work during 2011-2026. It concerns problem formulation, dependency
order, derivations, proof presentation, examples, qualifications, and
manuscript scale. It does not authorize impersonation, sentence-level
imitation, or attribution of every feature of a coauthored paper to one author.

## Contents

- [Method And Limits](#method-and-limits)
- [Changes Across The Period](#changes-across-the-period)
- [Genre Findings](#genre-findings)
- [Derivation And Proof Findings](#derivation-and-proof-findings)
- [Cross-Corpus Principles](#cross-corpus-principles)
- [What Not To Infer](#what-not-to-infer)

## Method And Limits

The underlying census contains 88 arXiv records with Edward Witten in the
author list, submitted from 2011-01-01 through 2026-07-11. The exhaustive list
and close-read markers are in `witten-2011-2026-corpus.md`.

Twenty-seven papers were sampled more closely across three periods and six
manuscript modes. Inspection covered the abstract, introduction, section
dependency, placement of definitions, proof or calculation architecture,
examples, caveats, and ending. Proof-dense papers received additional
inspection of theorem statements and key proof transitions. The result is a
stratified structural analysis, not a claim of line-by-line reading of all 88
papers.

The sample includes:

- long construction papers such as [Fivebranes and Knots](https://arxiv.org/abs/1101.3216),
  [Superstring Perturbation Theory Revisited](https://arxiv.org/abs/1209.5461),
  and [Gauge Theory and the Analytic Form of the Geometric Langlands
  Program](https://arxiv.org/abs/2107.01732);
- proof-oriented papers such as [The Nahm Pole Boundary
  Condition](https://arxiv.org/abs/1311.3167), [A Note on Continuous
  Entropy](https://arxiv.org/abs/2202.03357), [The Timelike Tube Theorem in
  Curved Spacetime](https://arxiv.org/abs/2303.16380), and [Scale and
  Conformal Invariance in 2d Sigma Models](https://arxiv.org/abs/2404.19526);
- pedagogical works such as [Three Lectures on Topological Phases of
  Matter](https://arxiv.org/abs/1510.07698), [Notes on Some Entanglement
  Properties of Quantum Field Theory](https://arxiv.org/abs/1803.04993),
  [Light Rays, Singularities, and All That](https://arxiv.org/abs/1901.03928),
  [Why Does Quantum Field Theory in Curved Spacetime Make
  Sense?](https://arxiv.org/abs/2112.11614), [Liouville Theory: An
  Introduction to Rigorous Approaches](https://arxiv.org/abs/2404.02001), and
  [Introduction to Black Hole Thermodynamics](https://arxiv.org/abs/2412.16795);
- compact conceptual or computational notes such as [The Feynman i Epsilon in
  String Theory](https://arxiv.org/abs/1307.5124), [An SYK-Like Model Without
  Disorder](https://arxiv.org/abs/1610.09758), [Anomaly Inflow and the
  Eta-Invariant](https://arxiv.org/abs/1909.08775), [Bras and Kets in
  Euclidean Path Integrals](https://arxiv.org/abs/2503.12771), [Localization of
  Strings on Group Manifolds](https://arxiv.org/abs/2506.20028), [Duality and
  Axion Wormholes](https://arxiv.org/abs/2601.01587), and [A Note on
  Corrections to Entanglement Wedge
  Reconstruction](https://arxiv.org/abs/2606.18639);
- proposal-oriented papers such as [A Note on Complex Spacetime
  Metrics](https://arxiv.org/abs/2111.06514), [A Background Independent
  Algebra in Quantum Gravity](https://arxiv.org/abs/2308.03663), and
  [Wormholes and Averaging over N](https://arxiv.org/abs/2605.15180).

## Changes Across The Period

### 2011-2015: construction before interpretation

The long gauge/string papers commonly organize the article around a chain of
physical or mathematical transformations. In *Fivebranes and Knots*, the
introduction separates the object, earlier physical formulations, their
limitations, and the present route. The body follows the dependency of
Chern-Simons theory, dualities, and higher-dimensional constructions rather
than a generic methods/results template.

*Superstring Perturbation Theory Revisited* states exactly what remains opaque
in the familiar formalism and identifies one central change of arena: carry
the analysis, especially integration by parts, on supermoduli space. The paper
then makes gauge invariance, supersymmetry, and infrared behavior the tests of
that choice. The transferable lesson is that a claim of a simpler proof must
name the altered object or arena that removes the original obstruction.

The period also contains a strong prototype-to-general pattern. Elementary
ordinary differential equations, finite-dimensional integrals, or simple
worldsheet configurations appear before the full boundary-value or path-
integral problem. The prototype is not decorative; it defines the singularity,
contour, or geometric mechanism that the full theorem must control.

### 2016-2020: sharper contrasts and modular exposition

Compact model papers often begin from a known construction and alter one
ingredient. *An SYK-Like Model Without Disorder* needs only an introduction,
the model, and details because the contrast with the disorder-averaged model
already supplies the organizing question. Short notes in this period do not
manufacture a long architecture when one contrast can carry the paper.

Expository works become highly modular. *Notes on Some Entanglement
Properties* alternates abstract statements with finite-dimensional examples
and later returns to the general von Neumann algebraic setting. *Light Rays,
Singularities, and All That* begins with geometric questions and lets those
questions determine the order of causal curves, global hyperbolicity, focal
points, and singularity theorems.

In anomaly papers, a recurring expository move is to begin with the familiar
local or perturbative expression, explain why it is globally insufficient,
then replace it with a globally defined invariant. The general formula is
connected back to the perturbative limit before examples are organized by
dimension.

### 2021-2026: operational objects and local caveats

Recent gravity and operator-algebra papers frequently begin by asking what an
observable, algebra, state, or area term is supposed to accomplish. The formal
machinery follows the operational target. *A Note on the Canonical Formalism
for Gravity* is representative: the holographic observable problem is stated
before the canonical constraints are developed.

Proposal papers become especially explicit about false positives. *A Note on
Complex Spacetime Metrics* first shows why unrestricted complex saddles admit
unphysical configurations, then proposes an admissibility condition and tests
both useful and excluded examples. *A Background Independent Algebra in
Quantum Gravity* lists distinct failures of ordinary region algebras, builds a
controlled observer model, treats de Sitter space, and only then makes a more
speculative extension.

Recent short notes also separate a qualitative argument from a quantitative
calculation. *A Note on Corrections to Entanglement Wedge Reconstruction*
states the expected scaling, defines the compared relative entropies, performs
the perturbative calculation, and then relaxes simplifying assumptions one at
a time. The calculation is sized to one question, while the assumptions are
repeated at the step where each is relaxed.

## Genre Findings

### Long technical construction paper

The stable architecture is:

```text
several motivations
-> exact obstruction in the familiar formulation
-> overview of dependencies
-> controlled prototype
-> general machinery
-> implementation in the target theory
-> checks and examples
-> consequences and unresolved global issues
```

An overview is useful only when it explains why several layers are needed.
It should not paraphrase the table of contents.

### Short conceptual note

The stable architecture is:

```text
one mismatch
-> exact question
-> two or more logically distinct cases
-> one mechanism-revealing example
-> general statement
-> narrow technical refinement
```

*Bras and Kets in Euclidean Path Integrals* is a clear example: Hermitian and
bilinear pairings create the mismatch, reflection and no-reflection settings
separate the cases, and gauge theory with a theta angle exposes the role of
orientation and conjugation.

### Theorem or proof paper

The stable architecture is:

```text
precise statement and why standard tools do not directly apply
-> simple model or reformulation
-> proof dependency map
-> technical lemmas in dependency order
-> global/domain/boundary control
-> main theorem
-> corollaries and necessity tests
```

*The Nahm Pole Boundary Condition* separates the adapted identity, indicial
analysis, boundary definition, kernel/cokernel analysis, index, Fredholm
property, and regularity. *A Note on Continuous Entropy* separates the bounded
case, approximation lemmas, the semifinite extension, and optimality. These
are different proof subjects but share visible lemma dependencies.

### Pedagogical or review note

The first paragraph should establish a reader contract, but the contract should
normally be written as an inviting paragraph rather than displayed as a
checklist or a section called `Scientific contract`:

- intended audience and prerequisites;
- narrow or broad purpose;
- what is reviewed and what is new;
- important omissions;
- whether arguments are heuristic, sketched, or proved.

The stable architecture is:

```text
familiar question or paradox
-> elementary model
-> first derivation under transparent assumptions
-> abstract formulation
-> second example or theorem
-> removal of the initial simplification
-> scope and further reading
```

*Why Does Quantum Field Theory in Curved Spacetime Make Sense?* explicitly
uses a spin system and harmonic oscillators before field theory. *Liouville
Theory: An Introduction to Rigorous Approaches* gives a conceptual overview,
then convergence arguments, then identifies where naive continuation breaks
down, and only afterward supplies more detailed proofs.

### Proposal or conjectural paper

The stable architecture is:

```text
puzzle
-> failures of the naive criterion
-> proposed selector or object
-> controlled special case
-> accepted and rejected examples
-> conditional generalization
-> open construction or integration-cycle problem
```

Strong assumptions should appear in the introduction. Confidence should be
calibrated locally rather than collected in a global status table. A question
mark in a section title, or an explicit "we do not know" near the extension,
can be more precise than a vague caveat in the conclusion.

### Computational or localization paper

The stable hierarchy is:

```text
known solvable mechanism
-> one-dimensional or minimal model
-> simplest nontrivial group/geometry
-> general compact case
-> analytic continuation or noncompact case
-> independent checks
```

The generalization must identify what changes at each rung. A formal
replacement of group labels is not a derivation.

### Theory/numerics synthesis

This mode is not dominant in the Witten sample, so its rules combine the
corpus's structural discipline with standard numerical reporting:

```text
diagnostic ambiguity
-> exact algebraic/geometric decomposition
-> observable defined on that decomposition
-> data treatment and convergence protocol
-> generic behavior
-> exceptional mechanisms
-> finite-size interpretation and open limit
```

The exact structure must precede a statistic whose meaning depends on that
structure.

## Derivation And Proof Findings

### The theorem is stated at the resolution used in the proof

Proof-dense papers specify the manifold or algebra, the map/operator, regularity
or weight interval, boundary or faithfulness conditions, and the exact result.
The proof is not asked to recover hypotheses that the theorem failed to state.

### Long proofs are layered

The corpus repeatedly separates:

1. geometric or physical identity;
2. linearized operator;
3. spectral, microlocal, or indicial input;
4. boundary, domain, or convergence control;
5. Fredholm, monotonicity, or uniqueness statement;
6. regularity, nonlinear, or physical conclusion.

This layering should remain visible even if some details move to appendices.

### Heuristic intuition and proof are both useful, but named

Recent quantitative notes often give a scaling argument first and a technical
calculation second. Pedagogical papers may give a finite-dimensional analogy
before the operator-algebra theorem. The transition must state what the second
argument adds: a coefficient, a bound, a domain statement, or a removal of an
assumption.

### Plausible shortcuts deserve an exact diagnosis

The sigma-model paper includes a section explaining why an apparently natural
alternative flow has the wrong sign. The complex-metric paper exhibits the
unphysical saddles admitted by the naive rule. A "why not" section is useful
when it reveals the sign, domain, compactness, or global obstruction that the
successful argument must address.

### Necessity is tested by failure cases

Noncompact, incomplete, singular, or nonfaithful examples are placed near the
result whose hypotheses they probe. This distinguishes a convenient
assumption from a necessary mechanism.

### Appendices complete but do not rescue the argument

Appendices carry technical identities, alternative derivations, global path-
integral details, and long calculations. The main text still states the main
object, the essential hypothesis, the proof map, and the conclusion. An
appendix should not be the first place the reader learns why the theorem is
true.

## Cross-Corpus Principles

1. **Open with an exact mismatch.** Importance alone does not define a paper.
2. **Make the new object answer the obstruction.** Definitions should repair a
   named failure.
3. **Use controlled examples before uncontrolled generality.** State the map
   from prototype to target.
4. **Compare formulations by explanatory power.** Say what each makes
   manifest and what it obscures.
5. **Use an overview only for dependencies.** A long paper needs a map, not a
   second abstract.
6. **Keep assumptions local.** A late caveat cannot repair an earlier
   unconditional assertion.
7. **Make examples perform logical work.** They establish existence, mechanism,
   necessity, distinction, or limitation.
8. **Return from intuition to precision.** State what was simplified and where
   it is restored.
9. **Separate formal, perturbative, and exact conclusions.** "All orders" does
   not mean nonperturbative.
10. **Let manuscript scale follow the question.** One contrast may need three
    sections; a multistage construction may need an overview and appendices.
11. **Use ordinary section titles when they are clearer.** `Introduction`,
    `Overview`, `Examples`, and `Discussion` are not stylistic failures.
12. **End when the argument is complete.** A conclusion is useful for
    synthesis, not compulsory bookkeeping.

## What Not To Infer

- Do not reproduce characteristic phrases, humor, autobiographical voice, or
  sentence rhythms.
- Do not assume every paper has the same opening or section sequence.
- Do not infer sole authorship of stylistic choices in coauthored work.
- Do not turn corpus observations into scientific citations unless the target
  manuscript actually depends on the cited physics or mathematics.
- Do not claim that the 88-paper census is a full-text close reading.
- Do not treat a pattern seen in one manuscript as universal; route it by
  genre and subject.
