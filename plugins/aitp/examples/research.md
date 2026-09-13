# Can a Gaussian recover the oscillator ground state?

For the one-dimensional harmonic oscillator on the real line, a normalized
Gaussian does recover the exact ground state. In units with $\hbar=m=\omega=1$,
the optimum is $a=1$ and the energy is $1/2$. The reason is the balance of kinetic
and potential energy, together with an independent lower bound on the energy.

For

$$
H=\frac12\left(-\frac{d^2}{dx^2}+x^2\right),\qquad
\psi_a(x)=\left(\frac a\pi\right)^{1/4}e^{-ax^2/2},\quad a>0,
$$

the [detailed calculation](notes/gaussian-energy.md) gives
$E(a)=(a+a^{-1})/4\geq1/2$, with equality only at $a=1$.
It also shows $H=b^\dagger b+1/2$, so no admissible normalized state has lower
energy. This lower bound establishes exactness beyond the Gaussian family.

Minimizing potential energy alone would favor unlimited narrowing. That route
fails because the kinetic contribution grows with $a$ and makes the total
energy diverge. The detailed note retains this useful failed shortcut and links
the supporting width calculations. The table illustrates the result; the
analytic bound establishes it.

This resolves the stated teaching question. Gaussian optimization for a different
potential would normally give a variational upper bound, not an exact ground
state. The reusable [width-checking procedure](skills/check-gaussian-width/SKILL.md)
therefore includes endpoint checks and a separate test of any exactness claim.
