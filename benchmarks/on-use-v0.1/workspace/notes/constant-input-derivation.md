# Constant inputs with normalized weights

Original derivation, 2025-02-02, for the [two-channel study](../research.md).

Let w1,w2 be nonnegative real weights with w1+w2=1. For real inputs x1,x2 define

    S(w,x) = w1*x1 + w2*x2.

If x1=x2=c, then

    S(w,(c,c)) = w1*c+w2*c = c*(w1+w2) = c.

This proves preservation of a constant input under the stated normalization.
The equality on the last step uses w1+w2=1; the calculation makes no claim for
unnormalized weights or for changing their total weight.
