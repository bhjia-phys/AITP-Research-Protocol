# Weighted readout research log

## Current understanding — 2025-02-01

We want a two-channel readout whose value is insensitive to a common rescaling
of its weights. The current quantity is S(w,x)=w1*x1+w2*x2, with nonnegative
weights and a positive weight sum. The weighted-sum construction preserves
a constant input and is independent of the overall scale of the weights.
The remaining task is to test what happens when both weights are doubled.

The agreed work concerns the algebra of this two-channel example. A later
application to noisy inputs has been mentioned, but no noise model, dataset or
follow-up study has been chosen.

## Entry — 2025-02-02

The [constant-input derivation](notes/constant-input-derivation.md) is complete.
It writes S(w,(c,c))=c*(w1+w2)=c using w1+w2=1. This seemed to support the
readout claim in the opening. The argument is worth retaining.

## Entry — 2025-02-03

The [supplied observations](results/observations.csv) now include a doubling
check. For x=(2,6), weights (1,3) give S=20 and weights (2,6) give S=40.
For the constant input x=(5,5), the same weights give S=20 and S=40.
Thus the earlier general reading of the constant-input argument cannot be right.

## Entry — 2025-02-04

The [scaling analysis](notes/scaling-analysis.md) separates the normalized-weight
result from its attempted extension. S(lambda*w,x)=lambda*S(w,x), so the desired
scale invariance does not hold for the unnormalized sum in general.

An alternative is M(w,x)=S(w,x)/(w1+w2). For nonnegative weights of positive total
weight, M preserves constant inputs and is invariant under a common positive
rescaling. These are proved identities for this two-channel model. The original
CSV still records S, not a run of a changed implementation.

## Entry — 2025-02-06

The original constant-input proof remains valid under its normalization
assumption; it did not prove the unrestricted claim. The scale-invariant
alternative answers the stated algebraic design question. An application to
noisy inputs would need a choice of noise model and intended use before its
performance could be assessed. Nothing in these examples measures robustness
to noise or establishes how a real instrument would respond.
