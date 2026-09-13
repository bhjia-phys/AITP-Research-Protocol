---
name: check-gaussian-width
description: Check optimization of a normalized one-dimensional Gaussian trial state against the full Hamiltonian, endpoint behavior and the scope of a variational claim.
---

# Check a Gaussian variational width

Use the [oscillator derivation](../../notes/gaussian-energy.md) as the worked
source. Fix the Hamiltonian, units, normalization and positive width parameter.
Derive the kinetic and potential expectations before optimizing their sum;
minimizing either contribution alone can drive a false endpoint solution.

Find the stationary widths and compare them with the admissible endpoints.
Check the stated minimum analytically where possible, then use a few explicit
widths to catch sign, scale or transcription mistakes. A finite sample is not
a proof of a global minimum.

For $H=(-d^2/dx^2+\Omega^2x^2)/2$ and $\psi_a\propto e^{-ax^2/2}$,
$E_\Omega=(a+\Omega^2/a)/4$ is minimized at $a=\Omega>0$.
The [table](../../calculations/width-check.md) checks $\Omega=1$ and $2$.
For another potential, derive its expectation afresh instead of reusing this
formula. A minimum within the family is a variational upper bound on the true
ground energy; exactness requires a separate lower bound or eigenstate check.
This authored transfer exercise is not independent-session validation.
