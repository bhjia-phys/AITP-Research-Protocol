# A perturbative finite-size model

The synthetic model is the real matrix

H_L(g) = [[0,g],[g,1/L]], L a positive integer, g real.

We study its lower eigenvalue E_L(g), not a many-body ground-state phase diagram.
Energies and g use the same fixed energy unit, with the numerator of 1/L set to one.
The usual nondegenerate second-order expression about g=0 is E2_L(g)=-L*g^2.
Writing Delta=1/L, the exact eigenvalue is

E_L(g)=(Delta-sqrt(Delta^2+4*g^2))/2.

The second-order expression was first derived at fixed L. We then varied L while
holding g fixed. In a later campaign we varied L at fixed x=g*L. Both sets of records
are in numerics.csv; campaign and x columns identify how points were chosen. Values
are retained outputs of double-precision diagonalization of the displayed matrix.
The fixture's absolute eigensolver acceptance tolerance is 1e-12; it does not estimate perturbation
error. No random sampling was used. There is no noise model or statistical error bar.

Our original interpretation was that worsening agreement at large L might be an
eigensolver problem. A separate diagonalization agreed with the saved values within
1e-12. We need to understand the error before using this approximation as L grows.

## Draft fragments and requests from the researcher

Opening fragment: Second-order perturbation theory provides an efficient uniform
description of the large-L limit. We confirm this by two independent solvers.

Figure caption fragment: Energy convergence with system size. The perturbative
and exact curves approach each other, proving that the expansion is controlled.

Discussion fragment: The expansion and the exact result both vanish as g tends to
zero, so the large-L and weak-coupling limits commute. The same approximation can
therefore be used at fixed coupling as the gap closes.

I would like a useful quantitative statement about when the approximation works,
not only a warning that it can fail. If a bound follows from the exact expression,
explain its assumptions and relate it to both numerical campaigns. Distinguish a
claim about E itself from a claim about a rescaled response or Taylor coefficient.
