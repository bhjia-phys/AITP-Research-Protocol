# Theory notation across selected Ren GW, RI and RPA papers

This source comparison supports the [notation skill](../SKILL.md). It records
selected public-paper definitions and internal-consistency qualifications;
it is neither an official group standard nor a full survey of the authors' work.
The linked [LRI derivation](lri-tensor-derivation.md) and
[GW chain](gw-equation-chain.md) reconstruct intermediate steps. The companion
[organization study](../../ren-gw-writing/references/organization.md) supplies
the separate writing decisions. Recheck a source if the edition changes.

## Which originals support the choices?

The following editions were read directly. Page numbers are physical PDF pages;
for the 2021 article they match the suffix of the printed article page.

| Original | Inspected theory | What it contributes |
|---|---|---|
| Ren et al., *Resolution-of-identity approach to Hartree–Fock, hybrid density functionals, RPA, MP2, and GW with numeric atom-centered orbital basis functions*, NJP **14**, 053020 (2012); [1201.0655v2](https://arxiv.org/abs/1201.0655v2), [PDF](https://arxiv.org/pdf/1201.0655v2) | §§2.4–2.5, pp. 10–13; §§3.2–3.6, pp. 15–20 | Distinct orbital/product spaces, Coulomb fitting, weighted vertices, RPA/GW connection |
| Ren, Rinke, Joas and Scheffler, *Random-phase approximation and its applications in computational chemistry and materials science*, J. Mater. Sci. **47**, 7447–7471 (2012); [1203.5536v2](https://arxiv.org/abs/1203.5536v2), [PDF](https://arxiv.org/pdf/1203.5536v2) | §§II.A–II.B, pp. 5–7, especially Eqs. (19)–(24) | Coupling-dependent reducible response, independent response, EXX versus correlation energy |
| Ren et al., *All-electron periodic G0W0 implementation with numerical atomic orbital basis functions: Algorithm and benchmarks*, PR Materials **5**, 013807 (2021); [publisher](https://doi.org/10.1103/PhysRevMaterials.5.013807), [published PDF](https://pure.mpg.de/rest/items/item_3263538/component/file_3285757/content) | §§II.A–II.C, pp. 3–6, Eqs. (1)–(31) | Periodic vertices, Bloch phases, AO versus band triples, two-center LRI, dielectric symmetrization |
| Shi, Zhang, Lin, He and Ren, *LibRPA: A Software Package for Low-scaling First-principles Calculations of Random Phase Approximation Electron Correlation Energy Based on Numerical Atomic Orbitals*, [2407.19930v1](https://arxiv.org/abs/2407.19930v1), [PDF](https://arxiv.org/pdf/2407.19930v1); published as CPC **309**, 109496 (2025) | §2, pp. 4–9, Eqs. (1)–(12) and the associated algorithm | Cell labels on RI coefficients, imaginary-time phase factors, lattice transforms and energy per cell |
| Zhang, Lin, Shi and Ren, *Low-scaling GW calculations of quasi-particle energies for extended systems within the numerical atomic orbital framework*, [2603.27292v2](https://arxiv.org/abs/2603.27292v2), [PDF](https://arxiv.org/pdf/2603.27292v2) | §§2.1–2.4.3, pp. 5–16, Eqs. (1)–(40); Appendix A, pp. 57–58, Eqs. (57)–(60) | Recent LibRPA GW conventions, explicit BvK normalization, exchange/correlation separation, even/odd transforms |

The 2024 and 2026 entries use the pinned preprints for equation locators, not
uninspected journal versions. The five-paper selection addresses theory writing;
benchmarks, later implementation sections and beyond-GW diagrammatics were not
systematically reviewed in this notation study; the subsequent
[organization study](../../ren-gw-writing/references/organization.md) expands the selected readings and adds
the 2015 SOSEX article. Source PDFs are linked rather than redistributed in this skill.

## The common vocabulary and the changes that matter

The 2012 RI paper distinguishes $\varphi_i$ (orbital basis), $P_\mu$ (auxiliary
basis), $c^i_{n\sigma}$ (orbital coefficients), $C^\mu_{ij}$ (product-fit
coefficients), $M^\mu_{ij}$ (Coulomb-weighted AO vertices) and $O^\mu_{mn,\sigma}$
(weighted orbital vertices): Eqs. (35), (45), (50), (55). Its $\Pi$ represents
$V^{1/2}\chi^0V^{1/2}$, Eqs. (58)–(60). Thus $C$, $M$ and $O$ cannot be
interchanged by renaming. In §2.4, “cRPA” means the RPA correlation contribution;
that abbreviation conflicts with constrained RPA in writing about constrained RPA.

The 2021 periodic paper explicitly assigns band indices $m,n$, AO indices
$i,j,k,l$, and ABF indices $\mu,\nu,\alpha,\beta$ after Eq. (7).
Eqs. (21)–(22) distinguish AO $\widetilde C$ from band $C$. Eqs. (8)–(9)
place a $\mathbf k+\mathbf q$ bra against a $\mathbf k$ ket and expand their
product in $P_\mu^{\mathbf q*}$. Eqs. (23)–(31) preserve that orientation in
the LRI construction. Eq. (18) uses unnormalized Bloch sums; Eq. (2) carries
normalized BZ weights. For SOC notes the proposed convention reserves $\alpha,\beta$ for
spin and uses different ABF dummy indices: an explicit adaptation, not the paper's
unchanged index convention.

The 2024 LibRPA paper writes $c_{i,n}(\mathbf k)$ and cell-qualified
$C^{\mu(\mathbf R_1)}_{i(\mathbf R_1),k(\mathbf R_2)}$ in Eqs. (1)–(3).
Its $\Pi=\chi^0V$ before Eq. (12) differs entrywise from the 2012 $\Pi$.
Eq. (3) has imaginary prefactors in $G(i\tau)$; Eqs. (4) and (9) supply the
matching $-i$ factors in the bubble and its transform. These equations must
be translated as a set. Eq. (12) is explicitly an energy per unit cell.

The 2026 paper writes $c^i_{n\mathbf k}$, $\varphi_{i\mathbf R}$,
$P_{\mu\mathbf R}$ and $\mathbf t_I$ in §§2.2–2.3. Its Eq. (11) has
$1/\sqrt{N_k}$ in the Bloch sum. Eqs. (28)–(30) distinguish
$\widetilde\varepsilon$, $W$ and $W^c$, and Eqs. (34), (39)–(40) separate
exchange/correlation and even/odd time parts. Appendix A specifies a
zero-temperature Fourier pair. The scalar spin-restricted presentation in
§2.1 is not a derivation of the SOC extension.

The RPA review distinguishes $\chi_\lambda^{\rm RPA}$ from $\chi^0$ in
Eq. (19). Its Eq. (23) connects the coupling integral to the trace-log, and
Eq. (21) separates EXX from the RPA correlation contribution. A note that
equates the irreducible RPA bubble to the *reducible* RPA response has changed
the theory, not just its symbols.

## Printed inconsistencies that a notation skill must not propagate

These are bounded internal-consistency findings, not a general review of the
papers or evidence of an implementation error. The decisive PDF equations
were visually inspected as well as text-extracted.

- **2021 published p. 4, Eq. (11):** the displayed unrestricted band sum
  lacks the occupation difference present in the preceding Adler–Wiser
  expression. Eq. (8) defines $C$ as a wavefunction-product coefficient, so
  occupations are not absorbed there. Eq. (10) also displays $w_{\mathbf k}$
  under a $\mathbf q$ sum. In a new derivation, recover occupations and the
  actual quadrature variable from the response definition; do not copy the
  abbreviated display as a complete all-band formula. The frequency sign,
  product orientation and time-transform convention must also be reconciled
  together for complex vertices.
- **2024 preprint p. 9, Eq. (11):** the last Coulomb lattice sum is printed
  as $\sum_{\mathbf q}$ while its summand depends on $\mathbf R$; the first
  equality and Eq. (10) identify the required lattice variable. Eq. (12)'s
  second line leaves the trace term outside the printed integral grouping.
  Write braces around the complete frequency integrand, as already specified
  unambiguously in its first line and Eq. (8).
- **2026 v2 pp. 6 and 11, Eqs. (4), (16)–(18):** Eq. (4) gives
  $-\theta(\tau)(1-f)+\theta(-\tau)f$, whereas Eq. (18) gives its negative.
  Substitution into Eq. (16) with the orbital expansion (11) cannot produce
  both signs for the same $G$. The writing default retains Eq. (4) and the
  Appendix A Fourier pair. It does not silently copy Eq. (18). A simultaneous
  sign flip on both $G$ factors leaves a bubble unchanged but reverses a
  self-energy proportional to a single $G$, so a response-only check misses it.

No claim is made here about an author-issued erratum or a later journal fix.
These qualifications refer only to the named editions and inspected equations.

