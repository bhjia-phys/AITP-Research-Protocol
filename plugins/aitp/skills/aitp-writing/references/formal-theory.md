# Formal theory and derivation

Use this when the answer rests on a construction, identity, proof, or an
obstruction to one. The reader needs to see what the objects are, why a step
is licensed, and exactly which statement has been established.

## Give the argument a mathematical setting

Introduce the space, fields or operators and their relevant equivalence
relation before comparing them. Specify a gauge quotient, spin structure,
boundary condition, regulator or operator domain where it affects the claim.
An isomorphism of vector spaces need not be an equivalence of representations;
matching anomalies need not identify a physical theory. State the structure
the proposed map must preserve and test that structure.

For a theorem, quantify the data and state the conclusion precisely: existence,
uniqueness, a bound, classification, or equivalence. Distinguish sufficient from
necessary hypotheses, local from global conclusions, and finite-dimensional
statements from their field-theory extensions. Give the mechanism of a long
proof before its technical lemmas. Do not demand theorem formatting for a
calculation whose natural form is a physical derivation.

A conjectural physical identification can be an explicit assumption of an
otherwise exact calculation. Its conditional status must survive into the
abstract and interpretation. An exact calculation inside a proposed effective
description does not by itself derive that description from the UV theory.

## Show the transition that carries the result

Start from an identity or definition the reader can locate. For a consequential
transition, expose both the operation and its justification in prose or the
display itself. In particular:

- Write product, variation and commutator terms whose order or relative signs
  matter. Show the contraction that fixes multiplicities and conventions.
- Display a boundary term before invoking the condition that removes it.
  Compactness, falloff, topology and absence of singularities are different
  reasons; use the one the argument actually has.
- Identify kernels and the relevant range before dividing or taking an inverse.
  A pseudoinverse solves only the projected equation; retain the compatibility
  condition on the kernel.
- Specify the expansion parameter, retained order and remainder. Identify a
  nonuniform limit or resonance that can invalidate naive power counting.
- Justify a trace rearrangement, contour deformation, limit exchange or analytic
  continuation at the first step whose validity depends on it.

One fully explained representative calculation can license exact mechanical
repetition. A new zero mode, branch choice, global condition or limit requires
its own explanation. The appropriate detail is set by the reader and the
conceptual difficulty, not a fixed number of intermediate equations.

## Let an example reveal why a definition is needed

For example, consider $[H_0,X]=B$ in a finite-dimensional eigenbasis. The
matrix-element equation is

$$
(E_m-E_n)X_{mn}=B_{mn}.
$$

Different energies determine $X_{mn}$. Equal energies instead impose
$B_{mn}=0$ and leave the corresponding entries of $X$ undetermined. Only
after explaining this distinction is it useful to introduce the energy-block
projection and a Liouvillian pseudoinverse. This exhibits both the solvability
condition and the nonuniqueness, which writing $X=\mathcal L_0^{-1}B$ would hide.

When transporting such an example to unbounded operators, state the additional
domain, spectral and convergence issues. The finite matrix calculation supplies
the mechanism, not those analytic estimates.

For two formulations, explain what each makes manifest and identify the actual
map between them. Agreement on a restricted slice does not establish an
intertwiner on a full module. A counterexample should isolate the exact failed
step and the class of constructions it excludes.

## Separate proof from checks and interpretation

Distinguish an exact symbolic identity, a formal manipulation, a controlled
perturbative result, a numerical check, and a proposed physical interpretation
where each enters the reasoning. “All orders” in a perturbative series need
not imply a nonperturbative statement. Finite checks support a general identity
only with the additional argument that makes them sufficient, such as a
justified degree bound and exact evaluations.

An obstruction rules out the specified construction under its assumptions.
Explain what freedom was allowed before declaring a no-go result. Failure of
one ansatz or absence in a restricted dictionary cannot classify all possible
solutions. Keep the surviving question specific enough to continue.

An appendix can carry long expansions, supporting lemmas and alternate proofs.
Keep the main implication, its decisive hypothesis and the physical meaning in
the main text, and point to a necessary appendix result where it is used.
Conclude with what the argument establishes and which actual obstacle remains.
