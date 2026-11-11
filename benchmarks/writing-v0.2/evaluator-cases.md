# Case-specific evidence: evaluator only

## M01

The supported synthesis is that three finite-system diagnostics answer different
questions, and a claimed common ordering must specify both the observable and the
clock. The fixed-seed obstruction is nonzero at four L values, but does not classify
all conserved charges. Its coefficient concerns Q0, not O. Spectral midpoint drift
from 0.34 to 0.23 is a finite-size observation, not a demonstrated phase boundary.

The dynamical expansion is C(t)=b2*t^2+O(t^4), b2=||[H,O]||_F^2/d; the linear term
vanishes by trace cyclicity and the quadratic term follows from the double commutator.
Under tau=J*t, the coefficient is b2/J^2. At g=0.1 and 0.4 the raw coefficients are
4 and 9, while the reduced coefficients are 4 and 1. Raw-clock curvature therefore
increases by 2.25 while reduced-clock curvature decreases to one quarter. Neither
coefficient is an exponential growth exponent. The data cannot provide an identity
between the obstruction, midpoint and dynamical curvature.

A good figure makes the reversal visible, for example with two panels showing the
same data against t and tau, or a well-defined comparison of both coefficients.
Alternatives can earn full credit if they demonstrate the same inference honestly.
A useful table compares g, J, b2 and b2/J^2 with units/conventions. A spectral table
alone may be useful, but does not replace the decisive clock comparison somewhere
in the article. Check the actual generator and plotted lines against CSV inputs.
No supplied statistical error bars exist. Report 0.001 as the bound on the stated
fit/commutator discrepancy, not a sampling standard error. Do not call g a physical
energy, the drift convergence, or a polynomial onset a Lyapunov regime.

## M02

Let x=g/Delta=gL. E/Delta=(1-sqrt(1+4*x^2))/2. At fixed L,
E=-L*g^2+O(L^3*g^4); the small parameter is |g|L, not |g| alone.
The exact difference from E2 is

E-E2 = 4*g^4/[Delta*(Delta+sqrt(Delta^2+4*g^2))^2] >= 0.

For nonzero g, (E-E2)/|E2| <= (g/Delta)^2. Relative to |E|, the exact error is
(sqrt(1+4*x^2)-1)/2 <= x^2. A writer may choose either denominator, but must define
it and use it consistently in the table, curve and text. The bound gives a genuine
uniform statement on a scaled domain |g|L<=epsilon. Do not erase that positive result
by saying that nothing can be concluded because L is finite.

At fixed g=0.02, the relative error against the exact value at L=10,20,40,80 is
about 0.0385165, 0.1403124, 0.4433981, 1.1763055 (3.85165%, 14.03124%, 44.33981%,
117.63055%). Verify all values independently; evaluation tolerance is 1e-5 in a
displayed dimensionless ratio or the appropriate last displayed digit. Table rounding
must not create an apparent bound violation. Solver tolerance does not bound this error.

E itself has both iterated limits equal to zero as g->0 and L->infinity. Thus a blanket
claim that these two limits of E do not commute is wrong. At fixed nonzero g,
E_L(g)->-|g|, whereas E2=-L*g^2 diverges. The expansion is not uniform. For the rescaled
response -E/|g| (g!=0), the weak-coupling-first limit is zero and the large-L-first
limit is one. An acceptable note can establish nonuniformity without introducing that
response; if it asserts noncommutation it must specify the quantity and the limits.

A meaningful plot should expose the dimensionless control parameter and/or compare
both campaigns. Raw energies tending toward zero along g=x/L can visually approach
while their relative error stays fixed; that appearance is not improving relative
accuracy. A focused table should quantify approximation error separately from solver
agreement and state its denominator. Preserve the model's two-level scope; L labels a
closing gap, not a demonstrated many-body thermodynamic phase transition.
