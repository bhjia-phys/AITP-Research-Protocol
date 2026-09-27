# Can the candidate integral settle the threshold question?

The target is to decide whether a dimensionless response R is above 0.74.
This is a synthetic problem. The candidate surrogate is

    Q = integral from 0 to 1 of exp(-x*x) dx.

The current proposal is to learn about R by evaluating Q. R belongs to the
target model, but no definition, derivation or calibration relating R to Q
has been supplied. In particular, R = Q is a proposed identification rather
than an established input. No direct observations of R are available.

## Agreed stage

The researcher agreed to examine whether a controlled numerical evaluation of
the candidate Q can settle the sign of R-0.74. Grid changes and routine checks
using the existing script are within that agreement. Introducing a new relation
between R and Q would require discussing its evidence and approach first.

## Existing work

The [numerical note](notes/model-and-error.md) derives a conservative error bound
for the composite trapezoidal rule. The [completed checks](results/grid_checks.csv)
use N=2 and N=4. Their intervals for Q both contain 0.74. The N=4 approximation
itself is above the threshold, but its interval still crosses it.

At the last pause, increasing N to 8 was mentioned as the next possible grid
calculation. No N=8 calculation or other work has been done since these records.
The stage conclusion has not yet been integrated into this note.
