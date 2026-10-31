# From Coulomb fitting to the four LRI contractions

Reconstructed intermediate steps connect the primary equations to the full
endpoint contractions. The accompanying finite controls test the stated algebra,
not material fitting accuracy or a production implementation. Read this with
the [GW equation chain](gw-equation-chain.md) and the conditional
[LibRI array map](libri-code-map.md).

The primary equation locators are Ren 2012 RI, §§3.2–3.4, Eqs. (35)–(50);
Ren 2021 periodic GW, §II.C, Eqs. (23)–(31); and Zhang et al. 2026
[2603.27292v2](https://arxiv.org/abs/2603.27292v2), §§2.3–2.4.3 and §3.1,
Eqs. (12)–(22), (35)–(37), (44)–(47), pp. 9–22. The public editions and known
qualifications are in the [source comparison](theory-notation.md). Intermediate
steps and the endpoint notation below are an explicit reconstruction, not a
claim that these steps are printed verbatim in the papers.

## 1. Fix the spaces before suppressing any labels

Spatial NAOs $\varphi_{i\mathbf R}$ and ABFs $P_{\mu\mathbf R}$ are real.
Bloch coefficients, Green functions and spinors may be complex. Here $i\in I$
means a spatial AO belonging to atom $I$ in the primitive cell, and $\mu\in U$
means an ABF on atom $U$. Neither index contains spin. A complete center is
$(I,\mathbf R)$; $(I,0)$ and $(I,\mathbf R\ne0)$ are different centers.

For the first derivation, use composite AO indices $a=(i,\mathbf R_a)$ and
ABF indices $p=(\mu,\mathbf R_p)$ over a finite BvK cell. All real-space
translations are then contained in the indices. Later we restore every cell
argument. The symbol $\mathcal C^p_{ab}$ denotes a **complete product-fit
coefficient**; $C^p_{ab}$ below denotes a **first-end contribution**. They must
not be interchanged. In a target manuscript already using $C$ for the complete
fit, retain that choice and explicitly rename the first-end storage quantity.

## 2. Derive the Coulomb fit, rather than guessing an inverse

For $\rho_{ab}(\mathbf r)=\varphi_a(\mathbf r)\varphi_b(\mathbf r)$ define

$$
(f|g)_v=\iint f^*(\mathbf r)v(\mathbf r,\mathbf r')g(\mathbf r')
\,d\mathbf r\,d\mathbf r',\qquad
V_{pq}=(P_p|P_q)_v,\qquad b_p=(P_p|\rho_{ab})_v.
\tag{L1}
$$

For a selected auxiliary set $\mathcal A$, minimize the residual norm

$$
\mathcal E(c)=\left\|\rho_{ab}-\sum_{p\in\mathcal A}P_pc_p\right\|_v^2
=(\rho_{ab}|\rho_{ab})_v-c^\dagger b-b^\dagger c+c^\dagger V_{\mathcal A}c.
\tag{L2}
$$

Differentiation with respect to $c^*$ gives the normal equation and its solution
on a nonsingular retained Coulomb space:

$$
V_{\mathcal A}c=b,\qquad
\mathcal C^{\mathcal A}_{ab}=V_{\mathcal A}^{-1}b,\qquad
(P_p|\rho_{ab}-\widetilde\rho_{ab})_v=0\quad(p\in\mathcal A).
\tag{L3}
$$

For the real basis used here this is the column form of the 2012 paper's
row-coefficient formula. A truncated eigenvalue inverse or pseudoinverse solves
the problem in a declared retained space; it is not an inverse on discarded
directions. Distinguish the auxiliary linear-dependence threshold from a later
threshold that discards whole atom-pair tensors.

Global RI selects all auxiliary centers. LRI selects
$\mathcal A=\mathcal A[A]\cup\mathcal A[B]$, where $A,B$ are the actual
centers of $a,b$. Consequently

$$
\left(V_{\mathcal A\mathcal A}\right)^{-1}b_{\mathcal A}
\ne \left(V^{-1}b\right)_{\mathcal A}
\quad\hbox{in general}.
\tag{L4}
$$

The left side solves the restricted fitting problem; the right side solves a
different global problem before discarding coefficients. The distinction
survives even if both arrays have the same shape.

For fitted products, a Coulomb integral is approximated by

$$
(ab|cd)_{\rm fitted}=(\mathcal C_{ab})^T V\mathcal C_{cd},\qquad
M_{ab}=V^{1/2}\mathcal C_{ab},\qquad
(ab|cd)_{\rm fitted}=M_{ab}^TM_{cd}.
\tag{L5}
$$

These transposes assume real spatial fits. The three-center integral $b$, the
coefficient $\mathcal C$ and the weighted coefficient $M$ are different tensors.
In global RI, the residual is Coulomb-orthogonal to the common fitting space.
In pair-dependent LRI, $r_{ab}$ is orthogonal only to its own pair space, so
one cannot import global cross-product error cancellation without checking it.
Indeed

$$
(\rho_{ab}|\rho_{cd})_v-(\widetilde\rho_{ab}|\widetilde\rho_{cd})_v
=(r_{ab}|\widetilde\rho_{cd})_v+
(\widetilde\rho_{ab}|r_{cd})_v+(r_{ab}|r_{cd})_v.
\tag{L6}
$$

This note uses the fitted-product $CVC$ approximation; a robust correction to
it is a separate prescription. Accuracy in the Coulomb metric is also distinct
from pointwise agreement of functions, as RI12 §4.4 illustrates.

## 3. Two endpoints, same-center factors, and translations

Package the complete fit in two oriented contributions:

$$
\mathcal C^p_{ab}=C^p_{ab}+C^p_{ba},\qquad
C^p_{ab}=0\quad\hbox{unless }\operatorname{center}(p)=\operatorname{center}(a).
\tag{L7}
$$

For distinct centers the two terms have disjoint auxiliary support. For a
same-center product, they have the **same** support. A symmetric first-end
convention uses $C^p_{ab}=\mathcal C^p_{ab}/2$ there. More generally the required
identity is the sum in (L7), not a universal factor attached to every tensor.
For an exporter using this first-end contract, the one-AO control must
reconstruct complete coefficient one from raw $C=1/2$.
Do not halve data a second time if the producer has already done so.

This explains why a union-of-centers formula and a two-endpoint formula can
agree. In the former, a same-center auxiliary function is counted once. In
the latter, two contributions add to its coefficient. Inserting the full
same-center coefficient independently in both endpoints doubles the product
and can quadruple a two-vertex contraction.

Translation invariance for the full coefficient means

$$
\mathcal C^{\mu(\mathbf R_p)}_{i(\mathbf R_a),j(\mathbf R_b)}
=\mathcal C^{\mu(0)}_{i(\mathbf R_a-\mathbf R_p),j(\mathbf R_b-\mathbf R_p)}
=\mathcal C^{\mu(0)}_{j(\mathbf R_b-\mathbf R_p),i(\mathbf R_a-\mathbf R_p)}.
\tag{L8}
$$

The last equality uses real commuting spatial products. Store the first-end
block as

$$
C^\mu_{ij}(\mathbf R)
\equiv C^{\mu(0)}_{i(0),j(\mathbf R)},\qquad \mu\in I,\quad i\in I,
\tag{L9}
$$

whose array shape is $(n_{\rm aux}^I,n_{\rm AO}^I,n_{\rm AO}^J)$. Then

$$
\varphi_{i0}\varphi_{j\mathbf R}\simeq
\sum_{\mu\in I}C^\mu_{ij}(\mathbf R)P_{\mu0}
+\sum_{\nu\in J}C^\nu_{ji}(-\mathbf R)P_{\nu\mathbf R}.
\tag{L10}
$$

Swapping the two AOs changes both their order and the cell displacement. The
second term's stored block is rooted at $J$, not at $I$. No additional
complex conjugation is needed for the real spatial coefficients in this note.
Complex spatial orbitals require a separately defined conjugated-product fit.

## 4. Start the response from its kernel

With the conventional zero-temperature imaginary-time Green function,

$$
G^{st}(\mathbf r,\mathbf r',\tau)
=\sum_{ab}\varphi_a(\mathbf r)G^{st}_{ab}(\tau)\varphi_b(\mathbf r'),
\qquad
\chi^0(\mathbf r,\mathbf r',\tau)
=\sum_{st}G^{st}(\mathbf r,\mathbf r',\tau)
G^{ts}(\mathbf r',\mathbf r,-\tau).
\tag{L11}
$$

This $\chi^0$ is the density response with a minus sign relative to the
connected imaginary-time density correlator. Its sign and occupations are
derived in the [GW chain](gw-equation-chain.md). The multiplication in (L11)
is pointwise in spatial arguments, not a product of AO matrices. Expansion
gives products $\varphi_a\varphi_c$ at $\mathbf r$ and
$\varphi_b\varphi_d$ at $\mathbf r'$. Fitting these products therefore yields

$$
\chi^0(\mathbf r,\mathbf r',\tau)
\simeq\sum_{pq}P_p(\mathbf r)\chi^0_{pq}(\tau)P_q(\mathbf r'),\qquad
\chi^0_{pq}(\tau)=\sum_{abcd,st}
\mathcal C^p_{ac}\mathcal C^q_{bd}
G^{st}_{ab}(\tau)G^{ts}_{dc}(-\tau).
\tag{L12}
$$

The ABF response array is a matrix of **expansion coefficients**, not
$\langle P_p|\chi^0|P_q\rangle$. That distinction controls the metric factors
in the screening equation. Notice especially the reversed indices $dc$ and
the reversed spin pair $ts$ on the negative-time Green function.

## 5. Derive all four response terms by relabelling dummy indices

Insert (L7) twice into (L12). For a fixed auxiliary pair $p\in U$, $q\in V$,
relabel each term so its first-end tensors have the common form
$C^p_{ik}C^q_{jl}$, with $i\in U$, $j\in V$:

| Endpoints selected before relabelling | Dummy-index change | Green-function product afterwards |
|---|---|---|
| $C^p_{ac}C^q_{bd}$ | $a=i,c=k,b=j,d=l$ | $G^{st}_{ij}(\tau)G^{ts}_{lk}(-\tau)$ |
| $C^p_{ac}C^q_{db}$ | exchange $b,d$ | $G^{st}_{il}(\tau)G^{ts}_{jk}(-\tau)$ |
| $C^p_{ca}C^q_{bd}$ | exchange $a,c$ | $G^{st}_{kj}(\tau)G^{ts}_{li}(-\tau)$ |
| $C^p_{ca}C^q_{db}$ | exchange both pairs | $G^{st}_{kl}(\tau)G^{ts}_{ji}(-\tau)$ |

In the order used in the 2026 Eq. (22), the result is

$$
\begin{aligned}
\chi^0_{pq}(\tau)=\sum_{i\in U,j\in V}\sum_{kl,st}C^p_{ik}C^q_{jl}
\big[&G^{st}_{ij}(\tau)G^{ts}_{lk}(-\tau)
+G^{st}_{il}(\tau)G^{ts}_{jk}(-\tau)\\
&+G^{st}_{kl}(\tau)G^{ts}_{ji}(-\tau)
+G^{st}_{kj}(\tau)G^{ts}_{li}(-\tau)\big].
\end{aligned}
\tag{L13}
$$

There are four **endpoint terms before any spin sum**. For one scalar channel,
drop $s,t$. For two identical scalar channels, sum them or multiply by two with
occupations defined per spin. For a SOC spinor, the sum over $s,t$ has four
component pairs and is logically independent of the four endpoint terms.
The two factors of four describe different index spaces.

Restore $p=(\mu,0)$, $q=(\nu,\mathbf R)$, $k=(k,\mathbf R_1)$,
$l=(l,\mathbf R_2)$. With spin indices suppressed only for readability,

$$
\begin{aligned}
\chi^0_{\mu\nu}(\mathbf R,\tau)
=\sum_{i\in U,j\in V}\sum_{k\mathbf R_1,l\mathbf R_2}
C^\mu_{ik}(\mathbf R_1)C^\nu_{jl}(\mathbf R_2-\mathbf R)
\big[&G_{ij}(\mathbf R,\tau)G_{lk}(\mathbf R_1-\mathbf R_2,-\tau)\\
&+G_{il}(\mathbf R_2,\tau)G_{jk}(\mathbf R_1-\mathbf R,-\tau)\\
&+G_{kl}(\mathbf R_2-\mathbf R_1,\tau)G_{ji}(-\mathbf R,-\tau)\\
&+G_{kj}(\mathbf R-\mathbf R_1,\tau)G_{li}(-\mathbf R_2,-\tau)\big].
\end{aligned}
\tag{L14}
$$

Every displacement is **second-coordinate center minus first-coordinate center** in the corresponding
kernel-coefficient array $G_{ab}$. Equation (L14) is a way to audit all six
distinct displacement expressions before compressing them into atom labels.

## 6. Expose an actual contraction order

For fixed composite centers $U,V$ and a fixed spin pair, consider the first
term. Define, retaining its free AO index $i$ and internal index $l$,

$$
X^{p,-}_{il}=\sum_k C^p_{ik}G^-_{lk},\qquad
Y^{p,+-}_{jl}=\sum_{i\in U}G^+_{ij}X^{p,-}_{il},\qquad
\chi^{(1)}_{pq}=\sum_{j\in V,l}Y^{p,+-}_{jl}C^q_{jl}.
\tag{L15}
$$

Here $G^+_{ij}=G^{st}_{ij}(\tau)$ and $G^-_{lk}=G^{ts}_{lk}(-\tau)$.
The first intermediate can be reused across compatible output centers $V$;
it need not be rebuilt inside a naive four-center output loop. For the second
term the two independent sums separate even more directly:

$$
X^p_{ij}=\sum_k C^p_{ik}G^-_{jk},\qquad
Y^q_{ji}=\sum_l C^q_{jl}G^+_{il},\qquad
\chi^{(2)}_{pq}=\sum_{i\in U,j\in V}X^p_{ij}Y^q_{ji}.
\tag{L16}
$$

The other two terms use the exchanged time assignments with the correct
transpose/conjugation orientations. The 2026 Algorithm 1 reorganizes these
operations over atom-pair neighborhoods. The three-index arrays are not
ordinary matrices until a flattening such as $(p,i)$ is declared. Give the
shape of an intermediate when explaining which operation is a GEMM.

At fixed AO/ABF sizes per atom and fixed spatial support, the neighbor sums
over $K$ near $U$ and $L$ near $V$ are bounded as system size grows. A dense
set of output pairs can therefore cost $O(N_{\rm atom}^2)$ per time point;
this argument does not make the screening matrix inversion quadratic. Further
discarding $G$ blocks introduces an additional numerical approximation.

## 7. Derive the four self-energy terms separately

The correlation self-energy is a pointwise kernel product,
$\Sigma^{c,st}(\mathbf r,\mathbf r',\tau)=-G^{st}(\mathbf r,\mathbf r',\tau)
W^c(\mathbf r,\mathbf r',\tau)$. Its AO quantity is now a **projected operator
matrix element**. Inserting $G$ and integrating the external AOs gives

$$
\Sigma^{c,st}_{ab}(\tau)
=-\sum_{cd}G^{st}_{cd}(\tau)
\iint[\varphi_a\varphi_c](\mathbf r)
W^c(\mathbf r,\mathbf r',\tau)[\varphi_b\varphi_d](\mathbf r')
\,d\mathbf r\,d\mathbf r'
\simeq-\sum_{cd,pq}\mathcal C^p_{ac}G^{st}_{cd}(\tau)
W^c_{pq}(\tau)\mathcal C^q_{bd}.
\tag{L17}
$$

There is no spin trace here: $s,t$ are the external self-energy components.
$W^c_{pq}=\iint P_p W^cP_q$ already contains the auxiliary integrations.
Thus no auxiliary overlap inverse is inserted in (L17).

For external $i(0)$ and $j(\mathbf R)$ and internal $k(\mathbf R_1)$,
$l(\mathbf R_2)$, expanding the two endpoint sums gives

$$
\Sigma^{c,st}_{ij}(\mathbf R,\tau)
=-\sum_{k\mathbf R_1,l\mathbf R_2}
G^{st}_{kl}(\mathbf R_2-\mathbf R_1,\tau)
\left[\mathcal S_{IJ}+\mathcal S_{IL}+\mathcal S_{KJ}+\mathcal S_{KL}\right],
\tag{L18}
$$

where all four contributions are explicit:

$$
\begin{aligned}
\mathcal S_{IJ}&=\sum_{\mu\in I,\nu\in J}
C^\mu_{ik}(\mathbf R_1)W^c_{\mu\nu}(\mathbf R,\tau)
C^\nu_{jl}(\mathbf R_2-\mathbf R),\\
\mathcal S_{IL}&=\sum_{\mu\in I,\nu\in L}
C^\mu_{ik}(\mathbf R_1)W^c_{\mu\nu}(\mathbf R_2,\tau)
C^\nu_{lj}(\mathbf R-\mathbf R_2),\\
\mathcal S_{KJ}&=\sum_{\mu\in K,\nu\in J}
C^\mu_{ki}(-\mathbf R_1)W^c_{\mu\nu}(\mathbf R-\mathbf R_1,\tau)
C^\nu_{jl}(\mathbf R_2-\mathbf R),\\
\mathcal S_{KL}&=\sum_{\mu\in K,\nu\in L}
C^\mu_{ki}(-\mathbf R_1)W^c_{\mu\nu}(\mathbf R_2-\mathbf R_1,\tau)
C^\nu_{lj}(\mathbf R-\mathbf R_2).
\end{aligned}
\tag{L19}
$$

This expansion corresponds to 2026 Eq. (37), with the second and third
contributions ordered by endpoint choice rather than the source's display
order. The four $W^c$ displacements are dictated by the auxiliary centers;
they are not four copies of $W^c(\mathbf R)$.

For example, suppressing cells only after (L19), the $IJ$ contribution can be
evaluated through

$$
X^\mu_{il}=\sum_k C^\mu_{ik}G^{st}_{kl},\qquad
Y^\nu_{il}=\sum_{\mu\in I}X^\mu_{il}W^c_{\mu\nu},\qquad
\Sigma^{c,st,(IJ)}_{ij}=-\sum_{\nu\in J,l}Y^\nu_{il}C^\nu_{jl}.
\tag{L20}
$$

Other endpoints change which AO axes remain external. An atom-pair algorithm
can instead loop over the auxiliary centers and accumulate several external
AO blocks from shared intermediates. This is the role of the reorganization
around 2026 Eq. (47); algebraic equivalence and the chosen parallel schedule
are separate statements.

The exchange formula follows by replacing $G^{st}_{cd}(\tau)$ with the
density-kernel coefficients $D^{st}_{cd}$ and $W^c$ with $V$:

$$
\Sigma^{x,st}_{ab}=-\sum_{cd,pq}\mathcal C^p_{ac}D^{st}_{cd}
V_{pq}\mathcal C^q_{bd},\qquad D=G(0^-).
\tag{L21}
$$

The coincidence prescription is needed for the instantaneous bare interaction;
one should not sample its delta function on a finite positive-time grid.

## 8. What was checked

The reproducible [finite-control script](../scripts/check_lri_gw_identities.py)
constructs three spatial AOs on two centers, four auxiliary functions and six
complex spinor states. It compares the four response terms with both a full
product tensor and spectral band vertices; compares the four self-energy terms
with full tensors and band projection; and independently differentiates the
occupied density under the constructed matrix perturbation
$H\mapsto H+hO_\nu$, $O_\nu=I_{\rm spin}\otimes\mathcal C^\nu$, for the static
response. This is an abstract source coupled to the synthetic auxiliary
coefficient, not the projected literal potential $P_\nu(\mathbf r)$; that
literal potential would involve the auxiliary overlap. No physical NAO
potential integrals are generated by this control.

The observed maximum discrepancies are $1.9\times10^{-15}$ for the response
contraction comparisons, $1.5\times10^{-14}$ for self-energy/band projection,
and $5.1\times10^{-8}$ for the central density finite difference with step
$2\times10^{-5}$. Missing negative-time conjugation gives a discrepancy of
$2.71$ in this synthetic example; omitting off-diagonal spin blocks gives
$0.194$. A scalar same-center coefficient test distinguishes $4(1/2)^2=1$
from the incorrectly doubled product's $4(1)^2=4$.
An explicit three-cell BvK assembly also checks every restored displacement
in (L14) and (L19), with residuals $5.2\times10^{-16}$ and
$4.1\times10^{-15}$ respectively, against the full-supercell tensors.

These controls test index algebra, signs and multiplicities. They do not
measure LRI fitting quality for physical NAOs, execute LibRI, certify a
distributed implementation, or establish material accuracy. The local fit
control also confirms that truncating a global solution changes the restricted
normal-equation result. The array map explains the additional source inspection needed before
applying these identities to a particular library and consumer.
