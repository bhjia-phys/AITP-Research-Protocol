# Exchange sensitivity of a two-channel readout

The [main study](../research.md) asks whether this candidate readout can account
for a target instrument's response. This note treats the candidate itself.

Let w1 and w2 be fixed real weights and x1 and x2 be real channel values. Define

    qA = w1*x1 + w2*x2
    qB = w1*x2 + w2*x1.

Here the inputs exchange positions and the weights stay fixed. Subtracting gives

    qA - qB = w1*(x1-x2) + w2*(x2-x1)
            = (w1-w2)*(x1-x2).

This identity does not require positive or normalized weights. For real inputs,
qA = qB exactly when w1 = w2 or x1 = x2. Thus invariance of a weighted sum under
exchange is a condition on the weights or this particular input, not automatic.

The [supplied source](../references/source-excerpt.md) treats the distinct fact
that a normalized nonnegative weighted average lies between its inputs. Its
identity is imported starting material; the exchange calculation above was
carried out in this project.

For the [worked numbers](../results/example.csv),

    qA = 0.75*2 + 0.25*6 = 3
    qB = 0.75*6 + 0.25*2 = 5
    qA - qB = -2 = (0.75-0.25)*(2-6).

The example illustrates the general derivation; a single example would not prove
the formula for arbitrary inputs.

If the target response obeys y = a*q + b with common coefficients for the two
configurations, subtraction yields yA-yB = a*(qA-qB). This conditional implication
survives even when a = 0; a nonzero difference in y additionally requires a != 0
and nonzero factors in qA-qB. No target response, calibration or common-map test
has been performed. Repeating this arithmetic cannot supply that missing map.
