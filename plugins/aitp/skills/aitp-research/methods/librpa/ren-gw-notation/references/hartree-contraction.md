# Deriving the Hartree contraction with explicit endpoints

Use this route for a Hartree theory passage or a density-difference update.
It uses real spatial AOs and ABFs, complex spinor coefficients, atomic units,
and the first-end convention of the [LRI derivation](lri-tensor-derivation.md).
The physical definitions follow [Ren et al. 2012, §2.2, Eqs. (6)–(10)](https://arxiv.org/abs/1201.0655v2);
the periodic product notation follows [Shi et al. 2024, Eq. (1)](https://arxiv.org/abs/2407.19930v1).
The intermediate steps below are reconstructed, not quotations from those papers.

## Density, energy and projected operator

Define kernel coefficients and their spin trace by

$$
D_{ij}^{\alpha\beta}=\sum_n f_n c_{in\alpha}c_{jn\beta}^*,\qquad
D_{ij}=\sum_\alpha D_{ij}^{\alpha\alpha},\qquad
n(\mathbf r)=\sum_{ij}D_{ji}\varphi_i(\mathbf r)\varphi_j(\mathbf r).
$$

The spinor occupations lie between zero and one. A spin-degenerate spatial
storage may instead include both spins in occupations between zero and two;
do not use both conventions at once. With $S_{ij}=\langle\varphi_i|\varphi_j\rangle$,
$N_e=\operatorname{Tr}(SD)$. Projected density elements are $SDS$, whereas
$D$ above already consists of kernel coefficients.

Let $v(\mathbf r,\mathbf r')=1/|\mathbf r-\mathbf r'|$, with the periodic
zero mode treated as specified below when needed. For the electron number
density, the direct electron–electron energy is
$E_H=\frac12\iint n(\mathbf r)v(\mathbf r,\mathbf r')n(\mathbf r')$.
Varying both densities gives

$$
\begin{aligned}
\delta E_H
&=\frac12\iint[\delta n(\mathbf r)v n(\mathbf r')
 +n(\mathbf r)v\delta n(\mathbf r')]\,d\mathbf r\,d\mathbf r'\\
&=\int\delta n(\mathbf r)v_H(\mathbf r)\,d\mathbf r,\qquad
v_H(\mathbf r)=\int v(\mathbf r,\mathbf r')n(\mathbf r')\,d\mathbf r'.
\end{aligned}
$$

The second line interchanges the integration variables in the second term
and uses the symmetry of $v$. The potential has no remaining factor $1/2$.
Substituting the density before performing the two integrals gives

$$
\begin{aligned}
J_{ij}&=\iint\varphi_i\varphi_j(\mathbf r)v(\mathbf r,\mathbf r')
 \sum_{kl}D_{lk}\varphi_k\varphi_l(\mathbf r')\,d\mathbf r\,d\mathbf r'\\
&=\sum_{kl}(ij|kl)D_{lk},\qquad
E_H=\tfrac12\operatorname{Tr}(DJ),\qquad
\delta E_H=\operatorname{Tr}(J\delta D).
\end{aligned}
$$

The output pair $i,j$ stays intact and the input is the spin trace. Thus
$J^{\alpha\beta}_{ij}=J_{ij}\delta_{\alpha\beta}$ even with SOC.
The Hartree functional contains self-interaction; it is not the full
two-body expectation value, which also contains exchange for a Slater
determinant. An added constant potential has matrix $v_0S$, not $v_0I$.

## Fit both products, then factor the contraction

Here $a,b,c,d$ are spatial AO labels and $p,q$ are auxiliary labels; they
include cells when using a finite supercell. Use
$\widetilde\rho_{ab}=\sum_p\mathcal C^p_{ab}P_p$ and
$V_{pq}=(P_p|P_q)_v$. At this step introduce the two-sided approximation
$(ab|cd)\simeq\sum_{pq}\mathcal C^p_{ab}V_{pq}\mathcal C^q_{cd}$.
For raw first-end coefficients $\mathcal C^p_{ab}=C^p_{ab}+C^p_{ba}$,
substitution exposes all four terms:

$$
\widetilde J_{ab}=\sum_{cdpq}D_{dc}
\big[C^p_{ab}V_{pq}C^q_{cd}+C^p_{ab}V_{pq}C^q_{dc}
+C^p_{ba}V_{pq}C^q_{cd}+C^p_{ba}V_{pq}C^q_{dc}\big].
$$

The auxiliary centers are respectively $(a,c),(a,d),(b,c),(b,d)$.
Relabeling $c\leftrightarrow d$ in the second internal-end contribution gives

$$
\begin{aligned}
\rho_q&=\sum_{cd}(C^q_{cd}+C^q_{dc})D_{dc}
 =\sum_{cd}C^q_{cd}(D_{dc}+D_{cd}),\\
u_p&=\sum_qV_{pq}\rho_q,\qquad
\widetilde J_{ab}=\sum_p(C^p_{ab}+C^p_{ba})u_p,\\
\widetilde E_H&=\tfrac12\rho^TV\rho,\qquad
\delta\widetilde E_H=\sum_pu_p\delta\rho_p
 =\operatorname{Tr}(\widetilde J\delta D).
\end{aligned}
$$

$\rho$ contains density expansion coefficients; $u$ contains projections
$\int P_pv_H[\widetilde n]$. There is no additional auxiliary-overlap inverse.
For a single AO with $\varphi^2=P$, raw $C=1/2$ gives $\rho=D$, $J=VD$.
Using complete coefficient one at each endpoint instead multiplies $J$ by
four. This factor is independent of spin degeneracy.

Two-sided $CVC$ and exact projection of the fitted density's potential are
different approximations. The latter gives $\sum_q b^q_{ab}\rho_q$ with
$b^q_{ab}=(P_q|\varphi_a\varphi_b)_v$; $CVC$ gives
$\sum_{pq}\mathcal C^p_{ab}V_{pq}\rho_q$. A common global Coulomb fit
equates them. Pair-dependent LRI only satisfies its normal equation within
each pair's auxiliary set, so this equality is not general. The energy-gradient
identity above is exact within the fixed $CVC$ prescription.

## Periodic cells and the single mesh average

Use $\varphi_{i\mathbf k}=N_k^{-1/2}\sum_{\mathbf T}
e^{i\mathbf k\cdot\mathbf T}\varphi_{i\mathbf T}$ and
$d_{ij}(\mathbf R)=N_k^{-1}\sum_{\mathbf k}e^{-i\mathbf k\cdot\mathbf R}
D_{ij}(\mathbf k)$. Expanding $|\psi_{n\mathbf k}|^2$ gives

$$
n(\mathbf r)=\sum_{ij\mathbf T\mathbf R}d_{ji}(-\mathbf R)
\varphi_{i\mathbf T}(\mathbf r)\varphi_{j,\mathbf T+\mathbf R}(\mathbf r),
\qquad d_{ji}(-\mathbf R)=d_{ij}(\mathbf R)^*.
$$

Apply the LRI product expansion

$$
\varphi_{i\mathbf T}\varphi_{j,\mathbf T+\mathbf R}\simeq
\sum_{\mu\in I}C^\mu_{ij}(\mathbf R)P_{\mu\mathbf T}
+\sum_{\nu\in J}C^\nu_{ji}(-\mathbf R)P_{\nu,\mathbf T+\mathbf R}.
$$

For $P_{\mu0}$, the first term requires $\mathbf T=0$; the second requires
$\mathbf T=-\mathbf R$. In the second term relabel $i\leftrightarrow j$
and $\mathbf R\mapsto-\mathbf R$. Both contributions then have the same
first-end coefficient:

$$
\rho_\mu=\sum_{i\in I,j\mathbf R}C^\mu_{ij}(\mathbf R)
[d_{ji}(-\mathbf R)+d_{ij}(\mathbf R)].
$$

Define $C^\mu_{ij}(\mathbf k)=\sum_{\mathbf R}e^{i\mathbf k\cdot\mathbf R}
C^\mu_{ij}(\mathbf R)$, with coefficients zero outside their first-center
support. Transforming the two terms gives $C^\mu_{ij}(\mathbf k)D_{ji}(\mathbf k)$
and $C^\mu_{ij}(\mathbf k)^*D_{ij}(\mathbf k)$. Relabeling $i,j$ in the
second yields the Hermitian vertex
$\Gamma^\mu_{ij}(\mathbf k)=C^\mu_{ij}(\mathbf k)+C^\mu_{ji}(\mathbf k)^*$.
Consequently

$$
\begin{aligned}
\rho_\nu&=\frac1{N_k}\sum_{\mathbf k,ij}\Gamma^\nu_{ij}(\mathbf k)D_{ji}(\mathbf k),\\
u_\mu&=\sum_\nu V_{\mu\nu}(\mathbf q=0)\rho_\nu,\\
\widetilde J_{ij}(\mathbf k)&=\sum_\mu\Gamma^\mu_{ij}(\mathbf k)u_\mu,\\
\widetilde E_H^{\rm cell}&=\frac1{2N_k}\sum_{\mathbf k}\operatorname{Tr}[D(\mathbf k)\widetilde J(\mathbf k)]
=\tfrac12\rho^TV(0)\rho.
\end{aligned}
$$

The potential backprojection contains no second mesh average. Zero transferred
momentum does not remove the external electron momentum in $\Gamma$.
For $\mathbf k=\boldsymbol\kappa+\mathbf k_0$, a backend working on an
unshifted BvK mesh may first multiply each physical $C(\mathbf R)$ by
$e^{i\mathbf k_0\cdot\mathbf R}$ before folding translations. For a BvK
translation $\mathbf T_B$, $e^{i\boldsymbol\kappa\cdot\mathbf T_B}=1$;
this proves that the folded transform at $\boldsymbol\kappa$ equals the
unwrapped transform at $\mathbf k$. Off-mesh evaluation still requires the
unwrapped translations.

## Electrostatics and a fixed reference

A periodic charged electronic density requires a stated zero-mode convention,
for example $v_H(\mathbf G=0)=0$ with the matching compensating-background
prescription. This removes one plane-wave component, not the entire
auxiliary matrix $V(\mathbf q=0)$. Use the same regularization in $V$, the
density update and the reference Hamiltonian. An unconstrained product fit
need not preserve integrated charge, even when $\operatorname{Tr}(S\Delta D)=0$.

With a fixed basis, fit and kernel, $\Delta\widetilde J=
\widetilde J[D_t-D_0]$ follows from linearity. If the reference Hamiltonian
contains a native $J_0$, its updated Hartree part is

$$
J_t=J_0+\widetilde J[D_t-D_0]
=\widetilde J[D_t]+(J_0-\widetilde J[D_0]).
$$

The native-minus-fitted reference offset remains unless it is independently
zero in the same gauge. For energies, expanding the quadratic form gives
$\widetilde E_H[\rho_0+\Delta\rho]-\widetilde E_H[\rho_0]
=\rho_0^TV\Delta\rho+\tfrac12\Delta\rho^TV\Delta\rho$;
the energy of the difference alone omits the first term.

## Checks

Run [check_hartree_derivation.py](../scripts/check_hartree_derivation.py) with
Python and NumPy. It compares direct grid integrals with exact-product RI,
energy finite differences with $J$, and full-supercell tensors with the
periodic factorization. Counterexamples distinguish doubled endpoints,
missing conjugation, double mesh division and local versus global fitting.
It also checks shifted-mesh folding, spin rotation and the constant-potential
overlap identity. These are finite algebra tests; they do not call LibRI,
estimate material fitting error or establish QSGW convergence.
