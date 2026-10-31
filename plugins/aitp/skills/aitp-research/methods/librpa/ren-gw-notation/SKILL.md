---
name: ren-gw-notation
description: Write and check detailed LRI/LibRI, GW and RPA derivations for papers and notes using notation grounded in Xinguo Ren's coauthored work. Derive endpoint tensors, all four response and self-energy contractions, periodic band vertices, screening and quasiparticle equations with explicit indices, signs and normalization. Preserve the target manuscript's definitions; use for theory writing and equation-to-array correspondence, not production calculations.
---

# Write GW and RPA theory with familiar group notation

Use this skill for an article, a research note, or a theory passage. It supplies
source-grounded writing defaults, not an official group standard or a claim about
Ren's personal authorship of every convention. The linked source comparison
records the selected coauthored papers and their qualifications. Explicit user
choices and an existing coherent manuscript take precedence. For research-topic
work, reuse [AITP's research cycle](../../../../aitp-memory/SKILL.md) and the
target's current note; this method adds no separate research record.

For article structure, section transitions, result discussion and captions,
use the companion [ren-gw-writing](../ren-gw-writing/SKILL.md). It owns the
argument and paragraph organization; this skill owns conventions and equation
consistency. A full theory draft uses both, reusing the definitions already
settled. A local notation edit needs only this skill; the reciprocal links do
not request repeated invocation or a new article outline.

## Establish the passage's conventions

Read the target passage and the definitions it uses. Determine whether it treats
molecules or periodic systems; real or imaginary frequency/time; scalar,
collinear or spinor states; and kernels, expansion coefficients or operator
matrix elements. Recover the actual reference approximation and energy zero.
For a short edit, resolve only the conventions that affect that edit.

Use [conventions](references/conventions.md) as a symbol/convention overview,
not as a replacement for a requested derivation. For detailed LibRI/LRI and GW
work, follow the appropriate derivation route below; a symbol overview alone
is insufficient.
Consult the [source comparison](references/theory-notation.md)
when translating a paper's formulas, checking an attribution, or resolving a
phase/normalization discrepancy. It records exact editions and known printed
inconsistencies; a published equation is not by itself a consistency check.

## Detailed derivation routes

| Requested passage | Read and develop |
|---|---|
| RI/LRI fitting and coefficient definitions | [LRI derivation §§1–3](references/lri-tensor-derivation.md): spaces → Coulomb residual → normal equation → restricted pair fit → full versus first-end coefficient → same-center counting → cell reversal |
| Hartree and density-difference updates | [Hartree derivation](references/hartree-contraction.md): energy variation → nonorthogonal density → two-sided product fit → four endpoint terms → auxiliary density and potential → BvK normalization → zero mode and fixed-reference offset |
| LibRI response / `CGGC` | [LRI derivation §§4–6](references/lri-tensor-derivation.md): kernel bubble → product fitting → four explicit terms and their dummy-index relabellings → all lattice displacements → reusable intermediates; then the [code map](references/libri-code-map.md) if array correspondence is requested |
| GW correlation/exchange contraction | [LRI derivation §7](references/lri-tensor-derivation.md): projected AO element → internal Green function → four auxiliary-center combinations with distinct interaction displacements → contraction order → exchange limit |
| Periodic Green functions and band response | [GW chain §§1–5](references/gw-equation-chain.md): nonorthogonal resolvent → time ordering → transition denominator → BvK normalization → both endpoint Bloch phases and the band vertex |
| Screening, RPA energy and basis compression | [GW chain §§6–7 and 11](references/gw-equation-chain.md): mixed coefficient/projection representations → ordered Dyson inverse → dielectric symmetrization → coupling integral/trace-log → basis covariance and rank-reduction boundary |
| Self-energy, transforms and QP energies | [GW chain §§8–10](references/gw-equation-chain.md): pointwise product → frequency convolution → AO/band projection → even/odd transform → continuation → Dyson equation → nonlinear root and linearization |

The source notes own the derivations and qualifications; do not duplicate them
as another symbol dictionary. Read the route needed by the user's question,
including its prerequisites. Existing definitions can be recalled briefly,
but a nontrivial new contraction, relabelling or approximation needs its
intermediate steps in the delivered passage.

For detailed writing, make the reader able to reconstruct the requested
result. Define the quantity before introducing shorthand; state all free
indices and the ranges of summed indices; show which equation is substituted;
write the resulting uncontracted expression; then show the relabelling or
factorization that produces the compact form. Put exact equalities, finite
basis/LRI approximations and numerical truncations at their actual steps.
Explain why an intermediate is useful and which output indices it retains.
Do not replace this work with “after straightforward algebra”, “by symmetry”,
an arrow chain, or a reference to the final equation.

For a four-term LRI formula, give the four terms and their origin. Distinguish
the two endpoint choices at each product from spin sums. For a periodic
formula, retain cells through at least one full derivation before combining
atom and cell labels. For a nonorthogonal matrix formula, identify kernel
coefficients versus projected elements before deciding on overlap factors.
For source-to-code correspondence, identify tensor axes, storage order,
input sign and output axes; the mnemonic `CGGC` or `CWGC` is insufficient.

The detailed notes use real spatial NAOs/ABFs and allow complex Bloch
coefficients and SOC spinors. They explicitly separate complete product
coefficients from first-end `Cs`, and conventional $G$ from the alternative
stored convention $\overline G=-G$. Preserve these distinctions even when a
target uses different symbol names. The array mapping states a contract to
check; inspect and name the actual target revision before claiming agreement.

For new writing, use lowercase Latin indices for NAOs, Greek indices for ABFs,
and separate band and atom indices. Introduce $\varphi_i$, $P_\mu$ and
$\psi_{n\mathbf k\sigma}$ through their roles. Prefer $c$ for eigenvector
coefficients and $C$ for RI coefficients. If the user already uses
$C_{in\alpha}$, $C^\mu_{ij}$ and $C^\mu_{mn}$, retain all three and define their
index spaces. The 2021 paper's tilde on AO triple coefficients is a useful
optional distinction, not a requirement to rename every existing $C$.

Do not use $\alpha,\beta$ simultaneously as spin and auxiliary indices. Reserve
$P_\mu$ for auxiliary functions in an NAO derivation; introduce a separate
explicitly defined symbol if irreducible polarization is also denoted by $P$.

## Develop the theory in the order the reader needs it

State the approximation and the physical quantity first. Introduce the continuum
objects, then the orbital/product basis, then the contractions needed by the
result. For example, a GW methods passage normally connects
$G_0\to\chi^0\to W_0\to\Sigma\to E^{\rm QP}$; an RPA energy passage ends with
the trace-log instead. A short note can begin at the already defined object.
This is a dependency order, not a compulsory section template.

Define each new symbol beside its first consequential equation. Explain the
step's purpose and the approximation made there. Keep the derivation's physical
indices visible until the contraction is clear; suppress indices only with a
sentence saying what remains fixed or summed. Use $\simeq$ for finite RI/LRI
fitting rather than implying exact completeness.

Distinguish these objects before compacting formulas:

- $C^\mu_{ij}$, the three-center integral $(ij|\mu)$, and the Coulomb-weighted
  tensor $M^\mu_{ij}$; they differ by powers of the Coulomb metric.
- The expansion coefficients of $\chi^0$ and the ABF-projected matrices $V,W$.
  Nonorthogonal bases make this distinction consequential.
- $\varepsilon=1-v\chi^0$, its symmetrized matrix $\widetilde\varepsilon$,
  the irreducible response $\chi^0$, and the reducible $\chi^{\rm RPA}$.
- $W$ and $W^c=W-v$, and $\Sigma=\Sigma^x+\Sigma^c$.
- Collinear spin channels and components of one SOC spinor.

Declare a Fourier pair and occupation normalization before writing a space-time
chain. The 2024 and 2026 papers use different phases for $G(i\tau)$; never take
$G$ from one and the bubble or transform prefactor from the other. Zero-temperature
integrals and finite-temperature Matsubara sums are different conventions, even
if numerical occupations are smeared.

Keep the RPA correlation energy $E_c^{\rm RPA}$ distinct from the total
EXX+RPA energy. Older papers' abbreviation “cRPA” for correlation in RPA must
not be imported into a manuscript where cRPA means constrained RPA.

## Check the passage before returning it

Follow the changed equation through its uses, checking free and dummy indices,
bra conjugation, momentum transfer, spin sums, metric factors and normalized
$\mathbf k/\mathbf q$ weights. Select a check that could expose the actual
ambiguity: a real occupied–empty transition for a response sign, a non-diagonal
Coulomb matrix for matrix order, or the collinear limit for a spinor vertex.
The worked examples in [conventions](references/conventions.md#small-checks-that-discriminate-between-conventions)
show these checks and their limits.

For an extended derivation, [check_lri_gw_identities.py](scripts/check_lri_gw_identities.py)
provides reproducible NumPy controls for the endpoint contractions, complex
spinor bubble, nonorthogonal resolvent, BvK vertex phases, screening order and
QP energy zero. Use the relevant existing check or add a discriminating one
when a new convention changes its premise. Spectral evaluation, a density
finite difference and an explicit finite supercell are distinct reference
routes. Passing them supports those finite identities; it is not a LibRI
regression run or material validation.

For Hartree, [check_hartree_derivation.py](scripts/check_hartree_derivation.py)
compares direct grid integration, fitted products, energy derivatives and
explicit periodic tensors. Use it to distinguish endpoint, overlap, mesh-weight
and fixed-density errors; its synthetic kernels do not measure material accuracy.

Do not fix a questionable sign by renaming a symbol. Derive the conversion from
the definitions; if it cannot be established, flag the exact unresolved equation
and avoid using it as a premise. Clearly distinguish a source definition, an
algebraic translation, and a proposed local writing choice.

Return the requested prose/equations at the requested depth. A notation table is
useful for a long methods section but unnecessary for a two-equation note.
When translating symbols into Markdown, preserve inline math delimiters around
indexed tensors; plain parentheses around raw TeX do not render the formula.
Report consequential convention changes briefly outside the finished passage.
Do not attach a generic audit checklist to the article.

For SOC, cRPA, QSGW, metals, magnetic response or finite temperature, read the
target's own theory and appropriate primary sources. This skill helps maintain
notation; the selected corpus does not establish all those extensions. In
particular it does not choose a QSGW staticization prescription or a cRPA
correlated subspace.

Follow the target's language, journal and artifact requirements; produce
LaTeX/PDF only when requested. This method imposes no workspace-specific format.
