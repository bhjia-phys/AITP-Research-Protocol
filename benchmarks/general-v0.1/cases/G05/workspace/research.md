# Weighted readout and exchange of channels

We are studying a two-channel readout. There are weights, an exchange operation,
and an output difference. The project has obtained several formulas and an
example. This note collects them.

## Starting point

Let the channel values be x1 and x2 and the weights be w1 and w2. The supplied
[source excerpt](references/source-excerpt.md) gives the convex-average identity
for nonnegative weights with w1 + w2 = 1. This is the starting material.

## Calculation

The [derivation](notes/weighted-readout.md) compares the readouts before and after
exchanging the channel values while retaining the weights in their original
positions. It gives qA - qB = (w1 - w2)(x1 - x2). There are two ways this vanishes.

## Example

The [example](results/example.csv) uses w1 = 0.75, w2 = 0.25, x1 = 2 and x2 = 6.
The two readouts are 3 and 5, and their difference is -2. This agrees with the
formula above.

## Interpretation

The intended question is whether a candidate weighted readout can explain the
change in a target instrument's response y when its two input channels are
exchanged. The algebra describes q, not a measured y. A possible relationship
is y = a q + b, with the same a and b before and after the exchange. Under that
relationship, yA - yB = a (w1 - w2)(x1 - x2).

The relationship to y has not been established. No observations of the target
instrument have been supplied, and a and b have not been calibrated. It is
also unknown whether the same relationship applies in the two configurations.
The conditional formula does not establish an instrument response or a fit.

## What remains

The calculation and its example are complete. The next research question is
what observation or model argument could establish a common map from q to y.
Without that map, the project has a result about the candidate readout and a
conditional consequence for the instrument, rather than a prediction already
verified for that instrument.
