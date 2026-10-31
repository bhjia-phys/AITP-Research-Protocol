# From LRI equations to a LibRI interface

LRI is a product-fitting approximation; [LibRI](https://github.com/abacusmodeling/LibRI)
is a tensor library. This reference gives the array contracts and algebra to
check in a target implementation. It does not certify an uninspected checkout,
fork, exporter or CPU/GPU backend. Record the target revision in the consuming
note and trace the caller as well as the library wrapper. The
[LRI derivation](lri-tensor-derivation.md) owns the full equations.

## First establish the representation and array axes

For the first-end storage convention, the map
`map<I, map<(J,R), Tensor>>` connects centers $(I,0)$ and $(J,\mathbf R)$.
The following is the expected contract to verify, not a deduction from a
variable's name:

| Array | Meaning and axes |
|---|---|
| `Cs[I][{J,R}](mu,i,j)` | First-end $C^\mu_{ij}(\mathbf R)$, `(aux_I, AO_I, AO_J)` |
| `Gs[I][{J,R}](i,j)` | Selected spin block of kernel coefficients, `(AO_I, AO_J)` |
| `Ws[I][{J,R}](mu,nu)` | Projected auxiliary interaction, `(aux_I, aux_J)`; identify whether the caller supplies $V$, $W$ or $W^c$ |
| `chi0s[I][{J,R}](mu,nu)` | Auxiliary expansion coefficients, not automatically projected response elements |
| `Sigmas[I][{J,R}](i,j)` | AO operator elements; physical sign depends on the input Green-function convention |

Locate the exporter/reader and the physics wrappers, commonly
`include/RI/physics/RPA.hpp` and `GW.hpp`, in the actual dependency tree.
Read allocation, transpose and flattening operations. For row-major `Cs`,
the offset is $\mu n_i n_j+i n_j+j$; a flattened $(\mu,i)$ axis is different
from a flattened $(\mu,j)$ axis. Trace any conversion before assuming that
the consumer's matrix layout matches the tensor layout.

The complete product coefficient must satisfy
$\mathcal C^p_{ab}=C^p_{ab}+C^p_{ba}$, with the endpoint and cell change.
A one-AO control with complete coefficient one requires raw $C=1/2$ under
this convention. A producer that already stores first-end coefficients must
not be halved again. Check its actual same-center contract before applying
this rule to data.

## Recover the contraction from the labels

Let the endpoint tensors have axes $a=(a_0,a_1,a_2)$ and
$b=(b_0,b_1,b_2)$, where zero is auxiliary and the other axes are AOs.
For the label convention defined in `include/RI/ri/Label.h`, `a1b2` joins
$a_1$ and $b_2$. The uncontracted axes determine the output.

For response, use $a=(\mu,i,k)$ and $b=(\nu,j,l)$:

$$
\begin{aligned}
\texttt{a1b1\_a2b2}:&\quad
 \sum_{ikjl}C^\mu_{ik}C^\nu_{jl}A_{ij}B_{kl},\\
\texttt{a1b2\_a2b1}:&\quad
 \sum_{ikjl}C^\mu_{ik}C^\nu_{jl}A_{il}B_{kj}.
\end{aligned}
$$

The negative-time factor has reversed AO and spin direction. Define
$H^{st}_{ab}(-\tau)=G^{ts}_{ba}(-\tau)$, restoring the reversed lattice
displacement when cells are explicit. Assigning
$(A,B)=(G(\tau),H(-\tau))$ gives the first two terms of (L13);
exchanging the time assignments gives the other two. Thus a wrapper with
two topology labels and two time-assignment passes can implement four
endpoint terms. These passes do not supply a spin sum. Inspect the outer
spin loops and occupation normalization separately.

For self-energy, the interaction connects the two auxiliary axes:

| Topology | External axes | Auxiliary centers for external $i\in I,j\in J$ and internal $k\in K,l\in L$ |
|---|---|---|
| `a0b0_a2b2` | $(a_1,b_1)$ | $I,J$ |
| `a0b0_a2b1` | $(a_1,b_2)$ | $I,L$ |
| `a0b0_a1b2` | $(a_2,b_1)$ | $K,J$ |
| `a0b0_a1b1` | $(a_2,b_2)$ | $K,L$ |

These are (L19)'s four terms. Their output atom pairs and interaction
displacements differ. Check the scheduler's routing; fixed input `Cs` keys
do not imply that all contributions have the same external pair.

## Determine the stored Green-function sign from its builder

The conventional zero-temperature gapped kernel uses
$g_n(\tau)=e^{-\xi_n\tau}[-\theta(\tau)(1-f_n)+\theta(-\tau)f_n]$.
If the actual builder instead uses a positive empty-state sum and a negative
occupied-state sum, name its output $\overline G=-G$. Then

$$
\chi^0=GG=\overline G\,\overline G,\qquad
\Sigma^c=-\mathcal C G W^c\mathcal C
=+\mathcal C\overline G W^c\mathcal C.
$$

A positive tensor accumulation is then compatible with the physical negative
self-energy formula. Establish this from the builder and caller before
changing a wrapper's sign. Occupation rescaling, band selection, exponent
clamps and even/odd transforms are separate operations. In particular,
an assembly factor $1/2$ does not fix a wrong Green-function convention,
and fractional occupations do not by themselves establish a finite-temperature
Green function. The [source comparison](theory-notation.md) explains why
mixing printed conventions between papers is also unsafe.

For a Hermitian reference with real spatial AOs,

$$
G^{ts}_{ji}(-\mathbf R,-\tau)
=\left[G^{st}_{ij}(\mathbf R,-\tau)\right]^*.
$$

When the tensor engine stores both two-index inputs in the same direction,
conjugating the negative-time block implements this reversal. Swapping only
spin labels does not. Derive the required direction first: a backend that
already transposes or reverses its input must not be corrected twice.

## Hartree has a separate density normalization contract

Use the [Hartree derivation](hartree-contraction.md) before mapping a `CVCD`
routine. Identify whether its input density includes $k$ weights and whether
the kernel divides by $N_k$. If its operation is
$M=\sum_k\Gamma(k)D^{\rm in}(k)$ followed by $u=VM/N_k$, a caller holding
$\overline D(k)=w_kD(k)$ must pass $D^{\rm in}=N_k\overline D$.
This is a conditional interface conversion, not a reason to rescale any
array named `Ds` without reading the implementation.

Inspect the zero-transferred-momentum Coulomb prescription, both endpoint
backprojections and any shifted-mesh phase conversion. A regular-mesh
contract cannot be satisfied by passing an irreducible mesh with weights
alone when the required density/vertex symmetry rotations are missing.

## Establish the scope of the correspondence

Write the continuum definition, full tensor indices and sign convention
before identifying arrays and labels. Then inspect thresholds, rank
reduction, translation folding and ownership if the claim involves them.
The [finite controls](../scripts/check_lri_gw_identities.py) distinguish the
two response topologies, endpoint multiplicity, negative-input conjugation
and the alternative self-energy sign. They do not execute LibRI.
Source correspondence, a passing implementation regression and physical
accuracy remain separate claims.
