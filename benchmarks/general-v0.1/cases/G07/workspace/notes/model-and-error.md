# Candidate integral and controlled quadrature

The [main note](../research.md) states the target and the proposed use of this
calculation. This note establishes statements about Q only.

For f(x)=exp(-x*x), define Q=integral_0^1 f(x) dx. The composite trapezoidal
approximation with N equal subintervals is

    T_N = (0.5*f(0) + sum_{k=1}^{N-1} f(k/N) + 0.5*f(1)) / N.

The standard trapezoidal error estimate gives

    abs(T_N-Q) <= max_{0<=x<=1} abs(f''(x)) / (12*N*N).

Here f''(x)=(4*x*x-2)*exp(-x*x). Its absolute value is at most 2 on [0,1], so

    B_N = 1/(6*N*N)

is a valid conservative error bound. Consequently Q lies in [T_N-B_N,T_N+B_N].
The bound describes discretization error. Ordinary double precision is adequate
for the small grids in this exercise; it is not a universal roundoff bound.

The [script](../code/quadrature.py) implements the stated sum and bound. Existing
[N=2 and N=4 results](../results/grid_checks.csv) have intervals crossing 0.74.
This calculation supplies no relation between Q and another observable by itself.
