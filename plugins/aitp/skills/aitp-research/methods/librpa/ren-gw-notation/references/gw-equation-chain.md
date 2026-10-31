# A detailed GW equation chain in NAO and auxiliary bases

This reference develops $G_0\to\chi^0\to W_0^c\to\Sigma\to E^{\rm QP}$
with declared spaces, normalizations and approximations. The [LRI derivation](lri-tensor-derivation.md)
supplies the real-space contractions; the [array map](libri-code-map.md) explains
how to check alternative stored Green-function conventions in a target backend.
These are reconstructed steps and finite controls, not validation of a full implementation.

The source backbone is Ren 2012 RI §§2.4–2.5 and 3.6, Ren 2021 periodic GW
§II, and Zhang et al. [2603.27292v2](https://arxiv.org/abs/2603.27292v2)
§§2.1–2.4, Appendix A. RPA's coupling integral follows the 2012 RPA review
§II.B. Exact editions and printed-equation qualifications remain in the
[source comparison](theory-notation.md). This is not a functional-derivative
derivation of the exact Hedin equations: choosing the independent reference
$G_0$ and a bare charge vertex is the stated $G_0W_0$/RPA approximation.

## 1. Nonorthogonal AOs: identify the kind of matrix

For fixed momentum, and a fixed independent spin channel when such channels
exist, suppress those labels temporarily. With SOC, use the combined AO/spin
index and the spatial overlap extended as $I_{\rm spin}\otimes S$; do not
diagonalize spin blocks independently. Let
$S_{ij}=\langle\varphi_i|\varphi_j\rangle$ and
$H^0_{ij}=\langle\varphi_i|\hat h_0|\varphi_j\rangle$, with
$\hat h_0=T+v_{\rm ext}+v_H+v^{\rm xc}$. A complete set of generalized
eigenvectors in the retained AO space satisfies

$$
H^0c=Sc\epsilon,\qquad c^\dagger Sc=I,\qquad
cc^\dagger=S^{-1},\qquad H^0=Sc\epsilon c^\dagger S.
\tag{G1}
$$

Use Hartree atomic units. Write $\xi_n=\epsilon_n-\mu_{\rm chem}$ and let
$z$ denote energy relative to the chemical potential. The coefficients of
the Green-function kernel are

$$
\mathcal G(z)=c\,\operatorname{diag}\left[(z-\xi_n)^{-1}\right]c^\dagger
=\left[(z+\mu_{\rm chem})S-H^0\right]^{-1}.
\tag{G2}
$$

To verify the inverse, multiply its first expression on the left by
$(z+\mu_{\rm chem})S-H^0$ and use (G1), obtaining $Scc^\dagger=I$.
The corresponding kernel and its projected matrix elements are

$$
G(\mathbf r,\mathbf r',z)=\sum_{ij}\varphi_i(\mathbf r)
\mathcal G_{ij}(z)\varphi_j^*(\mathbf r'),\qquad
G^{\rm proj}_{ij}=\langle\varphi_i|\hat G|\varphi_j\rangle
=(S\mathcal G S)_{ij}.
\tag{G3}
$$

The finite-space resolution is
$\hat{\mathcal P}_{\rm AO}=\sum_{ij}|\varphi_i\rangle(S^{-1})_{ij}\langle\varphi_j|$.
Thus $(\hat A\hat{\mathcal P}_{\rm AO}\hat B)^{\rm proj}
=A^{\rm proj}S^{-1}B^{\rm proj}$. Identifying this with the full
$(\hat A\hat B)^{\rm proj}$ additionally assumes the intermediate action
stays in the retained space, or explicitly defines a projected theory.
For example, in a two-level space with only $|0\rangle$ retained and
$A=B=\sigma_x$, the full product has projected value one, while multiplication
of the two projected matrices gives zero. The finite-space identity does
**not** justify inserting $S^{-1}$ into every tensor
contraction: (G2) is a kernel coefficient matrix, and LRI separately fits
products of the basis functions. If only a subset of eigenstates is retained,
the spectral expression still defines a truncated kernel, but it is no longer
the inverse of the full AO matrix in (G2).

## 2. Occupations and time ordering fix the signs

For zero temperature, a gapped reference and occupations per individual state
$f_n\in\{0,1\}$, define

$$
G(1,2)=-\langle T_\tau\hat\psi(1)\hat\psi^\dagger(2)\rangle_0,
\qquad
g_n(\tau)=e^{-\xi_n\tau}
\left[-\theta(\tau)(1-f_n)+\theta(-\tau)f_n\right].
\tag{G4}
$$

At positive time only empty states propagate and carry a minus sign; at
negative time only occupied states propagate and carry a plus sign. With

$$
A(i\omega)=\int_{-\infty}^{\infty}e^{i\omega\tau}A(\tau)d\tau,
\qquad
A(\tau)=\int_{-\infty}^{\infty}\frac{d\omega}{2\pi}
e^{-i\omega\tau}A(i\omega),
\tag{G5}
$$

the empty-state integral is $-1/(\xi_n-i\omega)$ and the occupied-state
integral is $1/(i\omega-\xi_n)$. Both give
$g_n(i\omega)=(i\omega-\xi_n)^{-1}$. The density coefficients are
$D=cfc^\dagger=\mathcal G(0^-)$ and the electron count is $\operatorname{Tr}SD$
with the declared spin multiplicity. The jump is
$\mathcal G(0^+)-\mathcal G(0^-)=-S^{-1}$ in a complete retained AO space.

Fractional numerical occupations alone do not turn these expressions into a
finite-temperature derivation. At finite temperature the interval, boundary
conditions, Matsubara grids and $1/\beta$ normalization must all be changed.
Metals additionally require the intraband/zero-gap limit. The present controls
cover neither extension.

## 3. Derive the bubble and its transition denominator

For the charge response, Wick contraction gives, in the convention (G4),

$$
\chi^0(1,2)=\operatorname{tr}_{s}\left[G_0(1,2)G_0(2,1)\right].
\tag{G6}
$$

For a molecule, define the transition density and its auxiliary coefficients
by the **bra–ket order**

$$
\rho_{mn}(\mathbf r)=\psi_m^*(\mathbf r)\psi_n(\mathbf r)
\simeq\sum_\mu d^\mu_{mn}P_\mu(\mathbf r),\qquad
d^\mu_{mn}=\sum_{ij,s}c^*_{im s}\mathcal C^\mu_{ij}c_{jn s}.
\tag{G7}
$$

The spin sum occurs within each charge vertex because the charge operator is
the spin identity. $d$ here is only a temporary name to separate a band vertex
from a first-end storage tensor. If the target calls it $C^\mu_{mn}$, keep
that symbol and define its index spaces.

Substituting spectral Green functions into (G6) gives

$$
\chi^0_{\mu\nu}(\tau)=\sum_{mn}d^\mu_{mn}d^{\nu *}_{mn}
g_n(\tau)g_m(-\tau).
\tag{G8}
$$

For $m$ occupied and $n$ empty, the positive-time factor is
$-e^{-(\epsilon_n-\epsilon_m)\tau}$. Its transform contributes
$1/(i\omega+\epsilon_m-\epsilon_n)$. The reverse transition is supported on
negative time. Combining the two occupation cases yields

$$
\chi^0_{\mu\nu}(i\omega)=\sum_{mn}
\frac{f_m-f_n}{i\omega+\epsilon_m-\epsilon_n}
d^\mu_{mn}d^{\nu *}_{mn}.
\tag{G9}
$$

The factor $f_m-f_n$ is essential for an unrestricted band sum. A factor two
for identical spin channels, when appropriate, is separate from including
both transition directions. For one real occupied–empty transition with gap
$\Delta>0$ and real vertex vector $d$, the two directions combine to

$$
\chi^0(i\omega)
=dd^T\left[\frac1{i\omega-\Delta}-\frac1{i\omega+\Delta}\right]
=-\frac{2\Delta}{\omega^2+\Delta^2}dd^T.
\tag{G10}
$$

This negative response is a useful sign control. For complex transition
densities, the reverse transition uses the conjugated vertex: do not replace
its outer product by the forward one without proving the required symmetry.

## 4. Periodic normalization: derive the lattice coefficients

Take a uniform BvK mesh with $N$ cells and $N$ momenta. Use Bloch sums without
an intra-cell atomic phase:

$$
\varphi_{i\mathbf k}=\frac1{\sqrt N}\sum_{\mathbf R}
e^{i\mathbf k\cdot\mathbf R}\varphi_{i\mathbf R},\qquad
\psi_{n\mathbf k}=\sum_i c_{in}(\mathbf k)\varphi_{i\mathbf k},\qquad
c^\dagger(\mathbf k)S(\mathbf k)c(\mathbf k)=I.
\tag{G11}
$$

Inserting both Bloch sums into the full spectral sum over normalized states
produces

$$
G_{ij}(\mathbf R,\tau)=\frac1N\sum_{n\mathbf k}
e^{-i\mathbf k\cdot\mathbf R}c_{in}(\mathbf k)c^*_{jn}(\mathbf k)g_{n\mathbf k}(\tau),
\quad
G(\mathbf r,\mathbf r',\tau)=\sum_{ij,\mathbf R_a\mathbf R_b}
\varphi_{i\mathbf R_a}(\mathbf r)G_{ij}(\mathbf R_b-\mathbf R_a,\tau)
\varphi_{j\mathbf R_b}(\mathbf r').
\tag{G12}
$$

The $1/N$ comes from the two normalized orbitals. There is no additional
$1/N$ in the original sum over the normalized BvK states. The consistent
matrix transform pair is

$$
A(\mathbf q)=\sum_{\mathbf R}e^{i\mathbf q\cdot\mathbf R}A(\mathbf R),\qquad
A(\mathbf R)=\frac1N\sum_{\mathbf q}e^{-i\mathbf q\cdot\mathbf R}A(\mathbf q).
\tag{G13}
$$

General normalized quadrature weights may replace uniform sums in BZ
integration, but the discrete inverse and convolution identities of a full
uniform mesh cannot be silently applied to an irreducible list with arbitrary
weights. A basis using $e^{i\mathbf k\cdot(\mathbf R+\boldsymbol\tau_I)}$
instead has an additional diagonal orbital phase. Transform eigenvectors,
operators and vertices together; do not insert atomic phases in only one line.

## 5. Obtain the periodic LRI band vertex, including both phases

To align the following response with (G13), use a **positive-$\mathbf q$
transition density** with the larger momentum on the ket:
$\rho_{m\mathbf k,n\mathbf k+\mathbf q}=\psi^*_{m\mathbf k}\psi_{n\mathbf k+\mathbf q}$.
Let $P_{\mu\mathbf q}=N^{-1/2}\sum_{\mathbf R}e^{i\mathbf q\cdot\mathbf R}P_{\mu\mathbf R}$.
Before applying LRI, the orbital products are

$$
\rho_{m\mathbf k,n\mathbf k+\mathbf q}(\mathbf r)
=\frac1N\sum_{ij,\mathbf R,\boldsymbol\Delta}
c^*_{im}(\mathbf k)c_{jn}(\mathbf k+\mathbf q)
e^{i\mathbf q\cdot\mathbf R}e^{i(\mathbf k+\mathbf q)\cdot\boldsymbol\Delta}
\varphi_{i\mathbf R}(\mathbf r)\varphi_{j,\mathbf R+\boldsymbol\Delta}(\mathbf r).
\tag{G14}
$$

The first endpoint stays at $\mathbf R$. In the second endpoint set
$\mathbf T=\mathbf R+\boldsymbol\Delta$, then interchange the two AO labels
and use $-\boldsymbol\Delta$ as the displacement stored at the new first end.
These operations give

$$
\rho_{m\mathbf k,n\mathbf k+\mathbf q}
\simeq\frac1{\sqrt N}\sum_\mu
d^\mu_{m\mathbf k,n\mathbf k+\mathbf q}P_{\mu\mathbf q},
\tag{G15}
$$

$$
\begin{aligned}
d^\mu_{m\mathbf k,n\mathbf k+\mathbf q}
=\sum_{i\in U,j,\boldsymbol\Delta,s}C^\mu_{ij}(\boldsymbol\Delta)
\big[&c^*_{im s}(\mathbf k)c_{jn s}(\mathbf k+\mathbf q)
e^{i(\mathbf k+\mathbf q)\cdot\boldsymbol\Delta}\\
&+c^*_{jm s}(\mathbf k)c_{in s}(\mathbf k+\mathbf q)
e^{-i\mathbf k\cdot\boldsymbol\Delta}\big],\qquad \mu\in U.
\end{aligned}
\tag{G16}
$$

The two exponential factors are different. They follow from which endpoint
carries the auxiliary function, not from an arbitrary choice of Fourier sign.
Combining (G9) and (G15) gives the per-cell response coefficients

$$
\chi^0_{\mu\nu}(\mathbf q,i\omega)=\frac1N\sum_{\mathbf k,mn}
\frac{f_{m\mathbf k}-f_{n\mathbf k+\mathbf q}}
{i\omega+\epsilon_{m\mathbf k}-\epsilon_{n\mathbf k+\mathbf q}}
d^\mu_{m\mathbf k,n\mathbf k+\mathbf q}
d^{\nu *}_{m\mathbf k,n\mathbf k+\mathbf q}.
\tag{G17}
$$

The 2021 source instead writes the bra at $\mathbf k+\mathbf q$ and expands
the product in $P_{\mu\mathbf q}^*$. That source transition is the one above
with $\mathbf k' =\mathbf k+\mathbf q$ and $\mathbf q'=-\mathbf q$.
Reconstruct the kernel expansion before identifying its response array with
ours: a forward vertex, a conjugate vertex and a relabelled response momentum
must not be exchanged individually. Equations (G14)–(G17) state a complete
local convention, not an assertion that the source prints these exact labels.

## 6. Derive screening with the correct mixed representations

The independent response has an ABF **coefficient** expansion, while $V$ and
$W$ are **projected interaction integrals**. In real-space composite notation,

$$
\chi^0(\mathbf r,\mathbf r')\simeq\sum_{pq}P_p(\mathbf r)\chi^0_{pq}P_q(\mathbf r'),
\qquad V_{pq}=\iint P_pvP_q,\qquad W_{pq}=\iint P_pWP_q.
\tag{G18}
$$

Project $W=v+v\chi^0W$ and insert the coefficient expansion into its second
term. The first spatial integration produces $V_{p\mu}$, the second
$W_{\nu q}$, hence

$$
W_{pq}=V_{pq}+\sum_{\mu\nu}V_{p\mu}\chi^0_{\mu\nu}W_{\nu q},\qquad
W=(I-V\chi^0)^{-1}V=V(I-\chi^0V)^{-1}.
\tag{G19}
$$

There is no auxiliary overlap inverse in this mixed representation. At each
momentum and frequency, on a positive retained Coulomb space, define

$$
\Pi=V^{1/2}\chi^0V^{1/2},\qquad
\widetilde\varepsilon=I-\Pi,\qquad
W=V^{1/2}\widetilde\varepsilon^{-1}V^{1/2},\qquad W^c=W-V.
\tag{G20}
$$

Multiplication of (G19) by $V^{-1/2}$ on both sides proves (G20). Moving $V$
through an inverse is invalid unless the relevant matrices commute. In the
normalized Bloch basis of (G11), $\langle P_{\mu\mathbf q}|v|P_{\nu\mathbf q}\rangle$
over the BvK cell equals $\sum_{\mathbf R}e^{i\mathbf q\cdot\mathbf R}V_{\mu\nu}(\mathbf R)$:
the double cell sum cancels the Bloch normalization once. Source formulas with
unnormalized Bloch sums must specify their integration volume/normalization.

At the Coulomb singularity, the square root, inverse and small-$\mathbf q$
limit refer to a specified regularization or retained space. For an insulating
response the plane-wave head and wings have different small-$q$ orders
($q^2$ and $q$), so simply deleting the divergent Coulomb entry is not a
derivation of its finite screened limit. Use the actual head/wing prescription
and the target project's derivation
when this limit is part of the requested passage; the present algebra does
not select a correction scheme or validate metals.

## 7. Connect RPA screening to the correlation energy

In the scalar setting with the usual positive-frequency ACFD reduction, the
coupling-dependent **reducible** response is

$$
\chi_\lambda^{\rm RPA}=\chi^0+\chi^0\lambda V\chi_\lambda^{\rm RPA},\qquad
E_c^{\rm RPA}=-\frac1{2\pi}\sum_{\mathbf q}w_{\mathbf q}
\int_0^\infty d\omega\int_0^1d\lambda\,
\operatorname{Tr}\left[V(\chi_\lambda^{\rm RPA}-\chi^0)\right].
\tag{G21}
$$

Here $\sum_{\mathbf q}w_{\mathbf q}=1$ and the energy is per primitive cell.
Since $d\ln\det(I-\lambda\Pi)/d\lambda=-\operatorname{Tr}[(I-\lambda\Pi)^{-1}\Pi]$,
the coupling integral yields

$$
E_c^{\rm RPA}=\frac1{2\pi}\sum_{\mathbf q}w_{\mathbf q}
\int_0^\infty d\omega\,
\operatorname{Tr}\{\ln(I-\Pi)+\Pi\}.
\tag{G22}
$$

The linear term cancels the first-order term of the logarithm. It is not
outside the frequency integral. The unsymmetrized $\chi^0V$ is similar to
$\Pi$ on the retained nonsingular space and gives the same trace-log, although
its entries and apparent Hermiticity differ. This is correlation energy;
EXX+RPA total energy includes the separately defined one-body, Hartree and
exchange contributions. In a magnetic setting, establish the actual
frequency/momentum symmetry before using a positive-frequency or cosine-only
reduction; scalar time-reversal formulas are not a general proof for it.

## 8. From screened interaction to the self-energy

The bare-vertex GW approximation in convention (G4) is

$$
\Sigma^{c,st}(\mathbf r,\mathbf r',\tau)
=-G_0^{st}(\mathbf r,\mathbf r',\tau)W_0^c(\mathbf r,\mathbf r',\tau),
\qquad \Sigma=\Sigma^x+\Sigma^c.
\tag{G23}
$$

Only $W^c$ is transformed as a regular time function; the instantaneous bare
interaction supplies the separately evaluated exchange operator. Substituting
the Fourier pair (G5) into the product and integrating over $\tau$ gives

$$
\Sigma^c(\mathbf r,\mathbf r',i\omega)
=-\int_{-\infty}^{\infty}\frac{d\nu}{2\pi}
G_0(\mathbf r,\mathbf r',i\omega-i\nu)
W_0^c(\mathbf r,\mathbf r',i\nu).
\tag{G24}
$$

Equation (G24) is still pointwise in the two spatial arguments. Projection
produces the $\mathcal C G W^c\mathcal C$ contraction and all four LRI terms
derived in (L17)–(L20), not an ordinary product of the AO matrices $G$ and $W$.

For the diagonal band element, define a vertex with internal state on the bra,
$B^\mu_{m\mathbf k-\mathbf q,n\mathbf k}=d^\mu_{m\mathbf k-\mathbf q,n\mathbf k}$,
whose transition momentum is $+\mathbf q$ in (G16). Integration of the external
band orbitals then gives the diagonal band formula, with spin contractions
already contained in $B$,

$$
\Sigma^c_{nn}(\mathbf k,i\omega)
=-\frac1N\sum_{\mathbf q,m}\int_{-\infty}^{\infty}\frac{d\nu}{2\pi}
\frac{\sum_{\mu\eta}B^{\mu *}_{m\mathbf k-\mathbf q,n\mathbf k}
W^c_{\mu\eta}(\mathbf q,i\nu)B^\eta_{m\mathbf k-\mathbf q,n\mathbf k}}
{i\omega-i\nu-\xi_{m\mathbf k-\mathbf q}}.
\tag{G25}
$$

The conjugation follows because the density at the first coordinate is
$\psi^*_{n\mathbf k}\psi_{m\mathbf k-\mathbf q}$, the conjugate of the
defined $B$ transition. This is an alternative to the real-space algorithm,
not an instruction to reintroduce an expensive internal-band convolution.
For a general AO self-energy, projection instead gives

$$
\Sigma^{\rm band}_{mn}(\mathbf k,z)
=\sum_{ij,st}c^*_{im s}(\mathbf k)\Sigma^{st}_{ij}(\mathbf k,z)c_{jn t}(\mathbf k),
\qquad
\Sigma_{ij}(\mathbf k,z)=\sum_{\mathbf R}e^{i\mathbf k\cdot\mathbf R}\Sigma_{ij}(\mathbf R,z).
\tag{G26}
$$

$\Sigma_{ij}$ here is a projected AO operator matrix. Its transformation in
(G26) has no added overlap matrices. Its spin-off-diagonal components need
not vanish even though the interaction is a scalar charge interaction.

## 9. Even/odd transforms and continuation are separate operations

For any component with integrable time dependence, define
$A_e(\tau)=[A(\tau)+A(-\tau)]/2$ and
$A_o(\tau)=[A(\tau)-A(-\tau)]/2$. Splitting (G5) at zero proves

$$
A(i\omega)=2\int_0^\infty d\tau\,
\left[\cos(\omega\tau)A_e(\tau)+i\sin(\omega\tau)A_o(\tau)\right].
\tag{G27}
$$

A quadrature may absorb the factor two into its weights. Check its definition
before adding another factor. The self-energy generally needs both terms even
in the scalar nonmagnetic case. Reusing $W^c(+\tau)$ for $W^c(-\tau)$ requires
the evenness assumed in that scalar source setting; it is not a consequence
of an arbitrary matrix being labelled Hermitian. For complex spinors, use the
actual transpose/conjugation and momentum relations.

Analytic continuation approximates an analytic function from imaginary-axis
samples; it is not the Fourier transform (G27). State the continued component,
energy origin, fit order and data window. Padé interpolation through all input
points does not alone establish real-axis accuracy or causality. In a retarded
one-pole control $\Sigma^c(z)=a/(z-b)$ with $a>0$, use $z=E-\mu_{\rm chem}+i0^+$;
the same model can check the derivative and QP equation without treating it
as a material calculation.

## 10. Obtain the nonlinear and linearized QP equations from Dyson

For a one-shot correction relative to the reference containing $v^{\rm xc}$,
the interacting inverse kernel in the AO representation is

$$
\mathcal G_{\rm int}^{-1}(z)
=(z+\mu_{\rm chem})S-H^0-
\left[\Sigma^x+\Sigma^c(z)-V^{\rm xc}\right].
\tag{G28}
$$

This convention excludes Hartree from $\Sigma$; the reference Hartree is
already in $H^0$. Multiplying by $c^\dagger$ and $c$ gives a band-space
inverse with $(z+\mu_{\rm chem})I-\epsilon$ and the projected correction.
Neglecting off-diagonal band elements and taking the real quasiparticle pole
condition gives, with an **absolute** energy $E$,

$$
F_n(E)=E-\epsilon_n-\Sigma^x_{nn}
-\operatorname{Re}\Sigma^{c,R}_{nn}(E-\mu_{\rm chem})+V^{\rm xc}_{nn}=0.
\tag{G29}
$$

Expansion about $E=\epsilon_n$ yields

$$
Z_n=\left[1-\left.\partial_E\operatorname{Re}\Sigma^{c,R}_{nn}(E-\mu_{\rm chem})
\right|_{E=\epsilon_n}\right]^{-1},\qquad
E^{\rm lin}_n=\epsilon_n+Z_n\left[
\Sigma^x_{nn}+\operatorname{Re}\Sigma^{c,R}_{nn}(\epsilon_n-\mu_{\rm chem})-V^{\rm xc}_{nn}\right].
\tag{G30}
$$

The factor $Z_n$ multiplies the entire correction, including static exchange
minus $V^{\rm xc}$, even though only the dynamic self-energy contributes to
its derivative. A linearized root need not satisfy (G29) exactly. Near poles
there can be multiple roots and large spectral redistribution; a small
equation residual does not by itself identify the physically relevant
quasiparticle. The root selection and validity of the diagonal approximation
must be stated. A QSGW static Hermitian map is a further definition and does
not follow merely by relabelling (G29).

## 11. Auxiliary basis changes and compression

For a real invertible auxiliary change $P'=PA$, preserving the fitted kernel
and projected interactions requires

$$
\mathcal C'=A^{-1}\mathcal C,\qquad
\chi^{0\prime}=A^{-1}\chi^0A^{-T},\qquad
V'=A^TVA,\qquad W'=A^TWA.
\tag{G31}
$$

Substitution proves invariance of $\mathcal C^TW\mathcal C$ and of the
screening equation. Also $\chi^{0\prime}V'=A^{-1}(\chi^0V)A$, so the
trace-log is invariant. Complex transformations need the consistently
defined conjugate/dual basis; this real-basis formula should not be altered
by adding daggers selectively.

If $A$ is rectangular, it selects a smaller subspace and has no ordinary
inverse. In a specified Coulomb projection, the least-squares coefficient is
$\mathcal C'=(A^TVA)^{-1}A^TV\mathcal C$ on the retained positive space.
This is an approximation unless the target lies in that space. The
producer's actual compression/unfolding map must be inspected before matching
compressed $C$, $V$, $W$ or vertices; the square-basis identity does not certify
an arbitrary shrink transformation.

## 12. Reproducible checks and their limits

Run the [finite-control script](../scripts/check_lri_gw_identities.py)
with Python and NumPy. It uses independent representations where possible:

- A complex nonorthogonal spectral Green function agrees with the generalized
  inverse to $1.7\times10^{-15}$; inserting the two projection overlaps changes
  the array by $0.744$ in that example.
- Direct quadrature of both time halves agrees with the spectral response to
  $1.6\times10^{-11}$; an unjustified cosine-only transform differs by $3.25$
  in the complex synthetic example. The separate density finite difference
  is recorded in the LRI note.
- A three-cell explicit BvK construction checks the two phases in (G16) to
  $3.0\times10^{-15}$ and the $1/N$ response normalization in (G17) to
  $1.1\times10^{-14}$. The fixed-time spatial convolution underlying (G25)
  agrees with the full-supercell AO self-energy projected into bands to
  $9.5\times10^{-15}$; this last check does not numerically integrate its
  frequency convolution.
- Noncommuting-matrix screening, auxiliary-basis covariance and trace-log
  invariance agree within $4.0\times10^{-14}$. Reversing the dielectric order
  changes the result by $2.85$ in the control.
- Direct quadrature of the RPA coupling integral agrees with the trace-log
  expression to $1.0\times10^{-13}$ for the same finite matrix model.
- A one-pole model satisfies the nonlinear QP residual, while its linearized
  energy differs by about $10^{-6}$ Hartree. Omitting the chemical-potential
  shift leaves a residual of $7.69\times10^{-3}$ Hartree in that model.

These are finite identity and counterexample checks, not an execution of the
production code, a physical acceptance test, a proof of continuation quality,
or validation of SOC/cRPA/QSGW/metallic extensions as complete methods.
