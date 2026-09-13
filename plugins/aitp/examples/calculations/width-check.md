# Width checks

These values evaluate the expression in the [derivation](../notes/gaussian-energy.md)
with $\hbar=m=1$: $E_\Omega(a)=(a+\Omega^2/a)/4$. They are exact rational
arithmetic written as terminating decimals, not an eigensolver run or a fitted
measurement. No external dataset is needed.

| $\Omega$ | $a$ | $\langle T\rangle=a/4$ | $\langle V\rangle=\Omega^2/(4a)$ | $E_\Omega$ |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 0.25 | 0.0625 | 1 | 1.0625 |
| 1 | 0.5 | 0.125 | 0.5 | 0.625 |
| 1 | 1 | 0.25 | 0.25 | 0.5 |
| 1 | 2 | 0.5 | 0.125 | 0.625 |
| 1 | 4 | 1 | 0.0625 | 1.0625 |
| 2 | 1 | 0.25 | 1 | 1.25 |
| 2 | 2 | 0.5 | 0.5 | 1 |
| 2 | 4 | 1 | 0.25 | 1.25 |

The two energy contributions balance at the predicted optima. These sample
values alone do not prove that no unsampled width has lower energy; the
nonnegative expression and endpoint argument in the derivation supply that step.
