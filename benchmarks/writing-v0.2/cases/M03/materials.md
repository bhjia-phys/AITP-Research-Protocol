# Scalar screening fixture

All quantities are dimensionless. Consider a scalar response on the imaginary-frequency axis,

\[
\Pi(i\omega)=-\frac{a}{\omega^2+\Delta^2},\qquad
W(i\omega)=\frac{v}{1-v\Pi(i\omega)},\qquad
W_c(i\omega)=W(i\omega)-v,
\]

with \(v=2\), \(a=3\), \(\Delta=2\), and \(\omega\geq0\). The sign convention for \(\Pi\) is part of the definition. The target is the positive integrated screening weight

\[
S=-\frac1\pi\int_0^\infty W_c(i\omega)\,d\omega.
\]

This is a defined observable of the toy model. It has not been identified with a material energy, an experimental observable, or the result of a self-consistent electronic-structure calculation.

Use the fixed cutoff \(\Lambda=12\), and define

\[
S_\Lambda=-\frac1\pi\int_0^\Lambda W_c(i\omega)\,d\omega,
\qquad
h=\frac{\Lambda}{N},\qquad
\omega_j=(j+\tfrac12)h,
\]

\[
Q_N=-\frac h\pi\sum_{j=0}^{N-1}W_c(i\omega_j),\qquad
T_\Lambda=-\frac1\pi\int_\Lambda^\infty W_c(i\omega)\,d\omega,
\qquad
\widetilde Q_N=Q_N+T_\Lambda.
\]

The integrals have elementary analytic forms. The correction uses the exact tail of this specified model. No tail model is fitted from the quadrature data. Requested accuracy for an estimate of \(S\) is absolute error at most \(10^{-7}\), in these dimensionless units. Select a grid from those actually supplied; the experiment does not sample every possible integer \(N\).

## Numerical data

`quadrature.csv` contains double-precision raw midpoint estimates from two implementations at identical inputs and grids. The loop implementation recomputes each midpoint and evaluates each term in a Python loop, accumulating a scalar sum. The cached implementation stores the midpoint array and \(\omega_j^2+\Delta^2\) at setup, then forms the denominator, evaluates all terms with NumPy, and reduces the array for each evaluation. Both use the same formula; neither stores and returns a previous final answer. They differ only in preparation, array evaluation, and floating-point summation order. `loop_raw` and `cached_raw` exclude the analytic tail. CSV values are not rounded presentation values.

Use either column consistently for reported estimates; identify your choice. Small differences in the last few floating-point digits are not extra samples of physical uncertainty. Treat the analytic solution as the independent reference. The convergence figure should show both the error of the raw estimate relative to the full integral and the error after the tail correction, together with the analytic cutoff contribution as a horizontal reference. An additional discretization-error curve or an order-of-convergence guide is welcome if readable.

## Synthetic performance fixture

`timing.csv` supplies five independent synthetic batch summaries for \(N=512\), \(\Lambda=12\), and the model parameters above. They are invented timing observations for comparing cost conventions, not measurements made on a real machine. Within the hypothetical protocol, both implementations run on the same otherwise idle CPU in double precision with one computational thread. Each `*_eval_ms` entry is the mean wall time per evaluation in a batch of 1000 evaluations after its setup. No JIT compilation, process startup, file I/O, or plotting is charged. Setup is rebuilt at the start of each batch, and is retained within the batch.

`*_setup_ms` includes that implementation's preparatory work and evaluation of the exact analytic tail. `*_eval_ms` includes formation and reduction of the midpoint sum and addition of the stored tail. The loop path has only light setup; the cached path prepares reusable arrays. Treat these columns as exhaustive under this fixture's cost convention: there are no further shared costs to add or subtract. Repeated evaluations deliberately recompute the result at the fixed parameters; result memoization is disabled. Performance for changing grids, different parameters, different hardware, or new implementations is outside the fixture.

For the comparison, use the median of the five entries separately in each setup and evaluation column. For \(R\) evaluations reusing a setup, use

\[
C(R)=\operatorname{median}(t_{\rm setup})+
R\operatorname{median}(t_{\rm eval}).
\]

This is a cost model built from those specified medians, not a request to infer a distribution or confidence interval. Plot it for integer \(R\) from 1 through 1000. Compare the smallest positive integer \(R\) for which the cached cost is strictly lower. The two deployment workloads are one evaluation from a fresh setup and 100 evaluations sharing one setup; both require the stated absolute accuracy. Timing observations are available only for \(N=512\). Do not extrapolate those timings to other grids.
