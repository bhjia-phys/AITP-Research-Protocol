# The energy balance and the failed shortcut

The [main note](../research.md) uses real, normalized Gaussian states with $a>0$.
The Gaussian integral gives $\langle x^2\rangle=1/(2a)$. Since
$\psi_a'=-ax\psi_a$ and the boundary term vanishes exponentially,

$$
\langle T\rangle=\frac12\int_{\mathbb R}|\psi_a'|^2dx=\frac a4,
\qquad \langle V\rangle=\frac12\langle x^2\rangle=\frac1{4a}.
$$

Thus $E'(a)=(1-a^{-2})/4$ vanishes at $a=1$. Both endpoints $a\to0^+$
and $a\to\infty$ have divergent energy, and
$E(a)-1/2=(a-1)^2/(4a)\geq0$, proving the minimum within this family.

Why is this the exact ground energy? Define $b=(x+d/dx)/\sqrt2$ on the
oscillator domain. Using $[d/dx,x]=1$ gives
$H=b^\dagger b+1/2$. Its expectation is at least $1/2$, and $b\psi_1=0$.
The variational minimum therefore saturates a bound applying to all admissible
normalized states, not just Gaussians.

Keeping only $\langle V\rangle$ incorrectly favors $a\to\infty$.
The omitted $a/4$ grows without bound. This failure explains why the full
Hamiltonian and endpoint behavior must be checked before trusting an optimum.

The [width table](../calculations/width-check.md) supplies exact scalar checks.
For a transferable check, keep $\hbar=m=1$ but replace the potential by
$\Omega^2x^2/2$ with $\Omega>0$. Then
$E_\Omega(a)=(a+\Omega^2/a)/4$, minimized at $a=\Omega$ with energy
$\Omega/2$. The table includes $\Omega=2$. This is another instance of the same
oscillator exercise; it does not validate Gaussian exactness for other potentials.
