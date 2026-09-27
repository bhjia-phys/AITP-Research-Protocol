# A QSGW cleanup with numerical acceptance

This example comes from [LibRPA PR #7](https://github.com/minyez/LibRPA/pull/7),
with the reviewed implementation at
[e2d2700d](https://github.com/bhjia-phys/LibRPA/tree/e2d2700dbd89d1937e9ef86799819008496b45e6).
The task was to simplify an existing fixed-basis QSGW implementation while
preserving the agreed numerical behavior. The researcher had selected
end-to-end regression as the acceptance scope. This is a dated worked example,
not a prescription to remove component tests from other LibRPA developments.

## Input should carry the matrix, not a second description of the dataset

The existing G0W0 readers already handled common reference and RI/Coulomb data.
QSGW needed full Vxc matrices, including off-diagonal elements, so substituting
G0W0's diagonal Vxc table would have changed the calculation. The useful
simplification was to remove the QSGW inventory and manifest layer, read the
native full matrices by spin/k filename, and retain decoding and projection.

Producer inspection resolved an ambiguity: ABACUS `out_mat_xc` exported a
KS-state matrix in Ry even though its filename ended in `_nao.txt`. Guessing
AO basis from that suffix would apply the wrong transformation. The driver
kept an ordinary explicit basis option for genuine AO inputs and reused the
generic ELSI reader for FHI-aims CSC matrices in Hartree. Direct filename
reading requires the same spin/k ordering as the reference; removing the
manifest also removes its independent coordinate comparison.

See the [input implementation](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/driver/qsgw/vxc_io.cpp)
and [user-facing conventions](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/docs/user_guide/qsgw.md).

## Matrix arithmetic must preserve the reference

Replacing packed-vector mixer classes with
`H_next = H_in + beta * (H_out - H_in)` reduced the implementation. An initial
version copied a `Matz` and wrote into it, inadvertently changing shared
storage. The existing two-update H2O calculation exposed the error. The
corrected [matrix update](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/src/qsgw/hamiltonian_mixing.cpp)
allocates an independent result.

This was a reason to inspect ownership and retain the numerical trajectory,
not to add a general testing framework. The regression uses beta = 0.2, so it
also distinguishes the input and output mixing weights. Maximum Hamiltonian
residuals use complex-entry magnitudes consistently after the packed-vector
layer is removed.

## A failing comparison can originate in the baseline

An added ABACUS H2O calculation initially compared two updates. The second
update differed by about 0.0018 eV between versions. Repeating the old
executable itself changed that update by about 0.0017 eV, whereas its first
update agreed within 2.4e-10 eV. The observation did not establish the cause of
the later-update sensitivity.

Because the new case targeted native Vxc input, it retained initialization and
one complete QSGW update as its acceptance domain. Other cases continued to
check two-update trajectories. Reference rows came unchanged from the baseline;
the eigenvalue tolerance remained 2e-5 Ha. The
[case description](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/regression_tests/testcases/qsgw_abacus_mole_H2O_libri/README.md)
records the excluded second-update problem. This narrowing would not satisfy
a task whose claim was reproducible long-time iteration.

## Validate the version that will be reviewed

Upstream changed LibRI and the numerical paths during the PR update. After
incorporating that version, the combined tree was rebuilt with Intel oneAPI,
Release and LibRI, and the same seven cases were rerun at four MPI ranks and
one thread. Four QSGW cases and three existing G0W0 cases passed all 29 numerical
comparisons. The [regression definitions](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/regression_tests/testsuite.xml)
use the existing table comparator.

The Gamma-band case omitted `nfreq` and exercised the accepted default of 16.
Tracing the initializer showed that changing 6 to 16 affected all calculations
using the shared default, so the PR description stated that scope explicitly.
Neither these regression results nor the default choice establish frequency
convergence or a physically converged QSGW spectrum.
