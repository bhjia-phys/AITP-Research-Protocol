# Conventions for writing GW/RPA theory

These are **proposed writing defaults grounded in selected papers**, with
algebraic bridges stated below. Existing manuscript definitions take priority.
The [source comparison](theory-notation.md)
owns the checked locators and printed-equation qualifications.

This file is an overview. For a derivation, use the
[full LRI tensor development](lri-tensor-derivation.md),
[GW equation chain](gw-equation-chain.md)
and, when implementation arrays matter, the
[LibRI code correspondence](libri-code-map.md).
They expose the intermediate substitutions, endpoint choices, lattice phases
and matrix types that the summary below suppresses.

## Symbols and their spaces

| Object | Default | Qualification |
|---|---|---|
| NAO, auxiliary function, KS orbital | $\varphi_i$, $P_\mu$, $\psi_{n\mathbf k\sigma}$ | $P_\mu$ is a function, not a polarization matrix |
| AO indices | $i,j,k,l$ | Distinguish scalar index $k$ from vector $\mathbf k$ |
| ABF indices | $\mu,\nu,\lambda,\kappa$ | Use $\mu_{\rm chem}$ if the chemical potential would be ambiguous |
| Band indices | $m,n$ | For occupied/empty sums declare ranges; $a,b$ are possible empty-state indices |
| Atoms | $I,J,K,L$ | $\mu\in I$ restricts an ABF to atom $I$ |
| Lattice / intra-cell positions | $\mathbf R$, $\boldsymbol\tau_I$ | Imaginary time $\tau$ is a scalar; 2026 uses $\mathbf t_I$ for atomic positions |
| Bloch / transfer momenta | $\mathbf k$, $\mathbf q$ | State which orbital is the bra in a two-momentum vertex |
| Eigenvectors / RI coefficients | $c_{in\sigma}(\mathbf k)$ / $C^\mu_{ij}$ | 2021 uses $\widetilde C$ for AO and $C$ for band triples |
| Bare kernel / Coulomb matrix | $v(\mathbf r,\mathbf r')$ / $V_{\mu\nu}(\mathbf q)$ | $V$ includes basis integrals |
| Independent / reducible response | $\chi^0$ / $\chi^{\rm RPA}$ | In GW, $P^{\rm RPA}=\chi^0$ denotes an irreducible polarization |
| Dielectric / symmetrized dielectric | $\varepsilon$ / $\widetilde\varepsilon$ | Define matrix order rather than inferring it from the name |
| Screened interaction | $W_0$ or $W$; $W^c=W-v$ | Specify the reference; matrices subtract $V$, not the kernel symbol |
| Self-energy | $\Sigma^x+\Sigma^c$ | $\Sigma$ here excludes Hartree |

Use Hartree atomic units if appropriate and say so. Distinguish $\epsilon_{n\mathbf k}$
from dielectric $\varepsilon$. A superscript $0$ or subscript $0$ both occur in
the corpus; choose one consistently. Reserve cRPA for **constrained RPA** when
that method appears, and spell out RPA correlation otherwise.

## Orbitals, RI coefficients and Coulomb weighting

For real spatial NAOs in a molecular example,

$$
\psi_{n\sigma}(\mathbf r)=\sum_i c_{in\sigma}\varphi_i(\mathbf r),\qquad
\varphi_i(\mathbf r)\varphi_j(\mathbf r)
\simeq\sum_\mu C^\mu_{ij}P_\mu(\mathbf r).
$$

The product basis is generally nonorthogonal. In the **global Coulomb fit**,

$$
V_{\mu\nu}=(\mu|\nu),\quad
C^\mu_{ij}=\sum_\nu(ij|\nu)(V^{-1})_{\nu\mu},\quad
M^\mu_{ij}=\sum_\nu C^\nu_{ij}(V^{1/2})_{\nu\mu},
$$

where $(ij|\nu)=\iint \varphi_i(\mathbf r)\varphi_j(\mathbf r)
v(\mathbf r,\mathbf r')P_\nu(\mathbf r')\,d\mathbf r\,d\mathbf r'$.
These are Ren 2012 RI Eqs. (35), (37), (45), (46), (50). A local fit in LRI
uses the auxiliary space of the two centers and its Coulomb submatrix;
it is not obtained by truncating a previously computed global inverse.

The unweighted and weighted band vertices are respectively

$$
C^\mu_{mn,\sigma}=\sum_{ij}c^*_{im\sigma}C^\mu_{ij}c_{jn\sigma},\qquad
O^\mu_{mn,\sigma}=\sum_{ij}c^*_{im\sigma}M^\mu_{ij}c_{jn\sigma}.
$$

The bra is $m$ in $\rho_{mn,\sigma}=\psi^*_{m\sigma}\psi_{n\sigma}$.
Thus $C$ contracts with $W$, while the $O$ vertices already contain
$V^{1/2}$ and contract with the corresponding inverse dielectric matrix.
Substituting $O$ for $C$ without changing the intervening matrix double-counts
the metric. For complex AOs or Bloch products, define the conjugated product
and the conjugate second vertex explicitly instead of extending real-AO ERIs
by typography alone.

In periodic writing, the two-center restriction can be shown with a union of
actual centers, avoiding double counting when they coincide:

$$
\varphi_{i\mathbf R_1}\varphi_{j\mathbf R_2}
\simeq\sum_{(\mu,\mathbf R_3)\in
\mathcal A[I\mathbf R_1]\cup\mathcal A[J\mathbf R_2]}
C^{\mu(\mathbf R_3)}_{i(\mathbf R_1),j(\mathbf R_2)}P_{\mu\mathbf R_3}.
$$

Here $\mathcal A$ is the auxiliary set on the specified center. This union
notation is a local explanatory choice; the sources write two center terms.
The $C$ in this complete-fit formula is not automatically a raw first-end
`Cs` block. In the detailed derivation, $\mathcal C=C+C^{T_{\rm AO}}$ separates
the complete fit from the stored endpoint contribution, including same-center
counting. Translate that distinction into the target manuscript's notation.
Translate all lattice labels together using translational invariance. The
2021 reciprocal-space convention expands
$\psi^*_{m,\mathbf k+\mathbf q}\psi_{n\mathbf k}$ in $P_\mu^{\mathbf q*}$.
If writing the opposite transition, change both the momenta and conjugations.

## Response, screening and the trace-log

An expansion coefficient matrix and a matrix of projected operator elements
are different objects. For real molecular ABFs write

$$
\chi^0(\mathbf r,\mathbf r',i\omega)
\simeq\sum_{\mu\nu}P_\mu(\mathbf r)\chi^0_{\mu\nu}(i\omega)P_\nu(\mathbf r'),
\qquad W_{\mu\nu}=\iint P_\mu W P_\nu.
$$

With these definitions, the following is an ordinary matrix equation:

$$
W=V+V\chi^0W,\qquad
\widetilde\varepsilon=I-V^{1/2}\chi^0V^{1/2},\qquad
W=V^{1/2}\widetilde\varepsilon^{-1}V^{1/2},\qquad W^c=W-V.
$$

The right-side kernel dielectric is $\varepsilon=1-v\chi^0$, so $W=\varepsilon^{-1}v$.
For the other matrix order the equivalent expression is
$W=V(I-\chi^0V)^{-1}$, **not** $(I-\chi^0V)^{-1}V$ in general.
If both operators were represented by ordinary nonorthogonal-basis matrix
elements, their product would require the appropriate dual-basis metric.
Do not add an overlap inverse to the mixed coefficient/projection equation above.

For periodic ground-state RPA energy **per primitive cell**, with normalized
$\sum_{\mathbf q}w_{\mathbf q}=1$,

$$
E_c^{\rm RPA}=\frac1{2\pi}\sum_{\mathbf q}w_{\mathbf q}
\int_0^\infty d\omega\,
\operatorname{Tr}\{\ln[I-\Pi(\mathbf q,i\omega)]+\Pi(\mathbf q,i\omega)\}.
$$

Choose and define either $\Pi=V^{1/2}\chi^0V^{1/2}$ (2012 RI) or
$\Pi=\chi^0V$ (2024 LibRPA). They are similar on a nonsingular positive
Coulomb space, so their traces and determinant-based energies agree. They
are not equal entrywise; only the former is Hermitian when $\chi^0$ is
Hermitian. Restrict such claims to the regularized retained space at a Coulomb
singularity or after rank reduction. In a magnetic/complex setting, establish
the required response symmetry rather than assuming Hermiticity at each $\mathbf q$.

If explaining ACFD, distinguish
$\chi_\lambda^{\rm RPA}=\chi^0+\chi^0\lambda v\chi_\lambda^{\rm RPA}$
from $P^{\rm RPA}=\chi^0$. The reducible response contains the screening series;
the bare bubble does not. EXX+RPA total energy also contains the kinetic,
external, Hartree and exact-exchange terms evaluated with a stated reference.

## Time, frequency and periodic normalization

A consistent **zero-temperature imaginary-time default** is

$$
G(1,2)=-\langle T_\tau\hat\psi(1)\hat\psi^\dagger(2)\rangle,\quad
\chi^0(1,2)=\operatorname{tr}_{s}[G_0(1,2)G_0(2,1)],\quad
\Sigma^c(1,2)=-G_0(1,2)W_0^c(1,2).
$$

This defines the density response with a minus sign relative to the connected
imaginary-time density correlator. Products here are pointwise in space and
time (with the displayed spin contraction); they are not AO matrix products.
Use

$$
A(i\omega)=\int_{-\infty}^{\infty}d\tau\,e^{i\omega\tau}A(\tau),\qquad
A(\tau)=\int_{-\infty}^{\infty}\frac{d\omega}{2\pi}
e^{-i\omega\tau}A(i\omega).
$$

For a reference state of energy $\epsilon_n$ and occupation $f_n$,
$g_n(\tau)=e^{-(\epsilon_n-\mu_{\rm chem})\tau}
[-\theta(\tau)(1-f_n)+\theta(-\tau)f_n]$.
Consequently $g_n(i\omega)=(i\omega+\mu_{\rm chem}-\epsilon_n)^{-1}$.
The sources also label the time argument $i\tau$; this label alone does not
specify the Green-function phase. The 2024 paper has $G_{24}(i\tau)=-iG(\tau)$,
$\chi^0_{24}(i\tau)=i\chi^0(\tau)$ and an extra $-i$ in its response transform.
The 2026 Eq. (4) and Appendix A agree with the default above, but its Eqs.
(17)–(18) have the opposite overall sign; see the source qualification before use.
The inspected local LibRPA arrays use $\overline G=-G$ and a correspondingly
positive $C\overline GW^cC$ self-energy contraction, as traced in the code map.
This consistent array conversion is distinct from mixing the printed paper's
two definitions without changing the self-energy formula.

Only use a cosine-only transform when the object's evenness has been
established. In the scalar symmetry setting of the 2026 paper, $\Sigma^c$
requires both the cosine transform of its even part and $i$ times the sine
transform of its odd part. Magnetic or SOC matrix elements require checking
their actual transpose/conjugation relations. Finite-temperature work instead
declares $\beta$, fermionic/bosonic Matsubara grids and the $1/\beta$ sums.

A consistent lattice pair, used in the LibRPA space-time papers, is

$$
A(\mathbf q)=\sum_{\mathbf R}e^{i\mathbf q\cdot\mathbf R}A(\mathbf R),\qquad
A(\mathbf R)=\frac1{N_q}\sum_{\mathbf q}e^{-i\mathbf q\cdot\mathbf R}A(\mathbf q).
$$

Distinguish this from the normalization of the Bloch basis itself. The 2021
paper uses unnormalized Bloch sums with normalized BZ weights, whereas 2026
Eq. (11) displays $1/\sqrt{N_k}$ for BvK-normalized orbitals. In the latter
convention a full normalized-state spectral sum has no extra $1/N_k$; the
real-space AO coefficient matrix acquires $1/N_k$ on expanding the two orbitals.
Do not mix unit-cell-normalized orbitals with a supercell-normalized spectral sum.
Quadrature weights $w_{\mathbf k}$ and a spin degeneracy are separate factors.

## Spin and nonorthogonal AO extensions

For collinear states, keep $\sigma$ fixed inside one charge vertex, then sum
channels in $\chi^0$. A factor two can replace that sum only for identical
spin channels with occupations defined per spin. For SOC, a state $n$ is one
spinor; $\alpha,\beta$ are its components and not additional band labels.
When the target already uses the following notation,

$$
C^\mu_{mn}=\sum_{ij\alpha}C^*_{im\alpha}C^\mu_{ij}C_{jn\alpha}.
$$

The scalar density operator supplies $\delta_{\alpha\beta}$ **inside each
vertex**. The bubble multiplies two such vertices and has independent component
sums at the two vertices. Off-diagonal spin blocks of $G$ and $\Sigma$ need not
vanish. This is an algebraic extension using the existing SOC note, not a
spinor derivation established by the selected scalar papers.

For a nonorthogonal AO basis, $c^\dagger S c=I$ and
$\Sigma^{\rm band}=c^\dagger\Sigma^{\rm AO}c$ for projected self-energy
matrix elements. The coefficients of the Green-function kernel are
$\mathcal G(z)=[(z+\mu_{\rm chem})S-H]^{-1}$ for a complete reference AO
space, where $z$ is relative to the chemical potential. Its projected matrix
elements are $S\mathcal G S$. Label which of these is called $G_{ij}$.
An energy-dependent self-energy or truncated band space requires its own
stated Dyson equation/projection. Do not insert $S$ factors by analogy.

For a diagonal quasiparticle equation with an absolute energy variable $E$,

$$
E^{\rm QP}_{n\mathbf k}=\epsilon_{n\mathbf k}
+\operatorname{Re}\langle\psi_{n\mathbf k}|
\Sigma^R(E^{\rm QP}_{n\mathbf k})-v^{\rm xc}|\psi_{n\mathbf k}\rangle.
$$

State the diagonal approximation. If the continued self-energy uses energies
relative to $\mu_{\rm chem}$, evaluate it at $E^{\rm QP}-\mu_{\rm chem}$.
A linearized equation additionally defines $Z$ and its expansion point; it is
not identical to solving the nonlinear equation. A QSGW note must specify the
static Hermitian mapping and reference frame separately.

## Small checks that discriminate between conventions

These are algebraic checks, not numerical validation of LibRPA or a material.

1. **Response sign.** For one spin channel with one real occupied–empty
   transition of gap $\Delta>0$ and real auxiliary vertex vector $d$,
   $\chi^0(i\omega)=-2\Delta\,dd^T/(\Delta^2+\omega^2)$.
   The factor two comes from the two frequency directions, not spin degeneracy.
   It follows directly by transforming $-e^{-\Delta|\tau|}dd^T$.
   With positive $V$, $\widetilde\varepsilon\succeq I$, and
   $\ln(1-x)+x\le0$ for every eigenvalue $x\le0$ of the weighted response.
   A double spin factor or a positive bubble fails this control.
2. **Matrix order.** Pick positive non-diagonal $V$ and a real negative
   semidefinite $\chi^0$ with $[V,\chi^0]\ne0$. Compare
   $(I-V\chi^0)^{-1}V$, $V(I-\chi^0V)^{-1}$ and
   $V^{1/2}(I-V^{1/2}\chi^0V^{1/2})^{-1}V^{1/2}$.
   They agree, whereas moving $V$ through the inverse generally fails.
3. **SOC reduction.** Set $C_{in\alpha}=c_{in}\delta_{\alpha\sigma_n}$.
   The charge vertex vanishes between opposite collinear spins and reduces to
   the fixed-channel orbital vertex for equal spins. A free double component
   sum inside one vertex fails this control.

The source note records which checks were actually run when this skill was
prepared. These examples do not establish complete behavioral validation or
settle magnetic, finite-temperature, cRPA or QSGW physics.
