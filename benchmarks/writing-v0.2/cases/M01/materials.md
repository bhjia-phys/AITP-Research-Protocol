# Finite-system research packet

All records are synthetic. They are stipulated finite-system observations for
testing exposition, not results for a particular published spin Hamiltonian.
The original project question was whether a single ordering of departure from an
integrable reference can summarize conservation, spectral and dynamical probes.

## Analytic notes

For each size L, H_L(g)=H0_L+g V_L, with dimensionless g and hbar=1. A specified
charge Q0_L commutes with H0_L. For an analytic continuation Q0_L+g Q1_L+...,
the first-order equation is [H0_L,Q1_L]=-[V_L,Q0_L]. The diagonal energy-block
part of its left side vanishes. The Frobenius norm of the right side projected
onto those blocks, divided by ||Q0_L||_F, is recorded in sectors.csv. Q0_L was
held fixed; no classification of other charges was attempted.

The dynamical observable is a different operator O, normalized by O^2=I and
Tr(O)=0. The trace is over the full finite Hilbert space of dimension d.
C_L(t,g)=2[1-Re Tr(O(t) O)/d], O(t)=exp(i H_L(g)t) O exp(-i H_L(g)t).
The short-time coefficient is Tr([H_L(g),O]^dagger [H_L(g),O])/d.
The spectral and charge analysis alone supply no identity relating this coefficient
to the charge-continuation obstruction. Dynamics were recorded only at L=24.

## Saved numerical records and conventions

sectors.csv contains the four studied sizes. Spectra were separated into irreducible
symmetry blocks; repeated multiplet levels were removed; the middle 40 percent of
each block was retained. Each block's mean adjacent-gap ratio was formed first,
then averaged with equal block weights. g_mid is the fitted midpoint of its smooth
g dependence. No uncertainty or asymptotic extrapolation was saved.

dynamics.csv contains t in inverse energy units, C at that t, and g. The file uses
one common physical clock for both g values. energies.csv gives J(g), the positive
energy scale used by the plotting notebook, and the saved commutator coefficient
b2 for C=b2*t^2+O(t^4). The notebook's horizontal variable was tau=J(g)*t. The
coefficient was independently reproduced by short-time fits over 0.002 <= t <= 0.01
to relative discrepancy below 0.001. That discrepancy is not a statistical error bar.

The charge obstruction first motivated looking at spectra. The subsequent dynamical
plots were intended to test whether the same notion of departure orders operator
change. Larger-size dynamics and low-energy observables are not in this packet.

## Draft fragments

Title: A common dynamical boundary of quantum chaos

Abstract fragment: We establish a universal loss of integrability and a faster
growth of chaos as g increases. Spectral fluctuations and operator growth agree
with a conserved-charge argument and identify the same boundary.

Caption fragment: Growth curves at L=24. The higher-g system grows faster, as
predicted by the charge obstruction. Time is dimensionless.

Results fragment: The change in the short-time growth rate confirms the spectral
classification. Our three approaches therefore provide a single coherent measure
of chaos. The drift of spectral midpoints is discussed separately in the appendix.
