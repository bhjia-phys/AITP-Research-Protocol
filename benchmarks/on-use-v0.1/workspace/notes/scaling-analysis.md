# Scaling test and the normalized alternative

Analysis completed 2025-02-04 for the [two-channel study](../research.md).

The original question asks for invariance under multiplying both weights by a
common positive number. Keep the inputs fixed and let lambda>0. Directly,

    S(lambda*w,x) = lambda*w1*x1 + lambda*w2*x2
                  = lambda*S(w,x).

Hence the unnormalized weighted sum is not scale invariant in general. A zero
sum S is an exceptional input, not a general invariance theorem.

The [original observations](../results/observations.csv) give a concrete failure:
S((1,3),(2,6))=20 while S((2,6),(2,6))=40. For constant input (5,5), the outputs
are 20 and 40 rather than 5. The [earlier derivation](constant-input-derivation.md)
is still valid because its last equality required w1+w2=1. Applying it outside
that condition was the error.

For nonnegative weights with w1+w2>0, define instead

    M(w,x) = (w1*x1+w2*x2)/(w1+w2).

The common factor cancels, giving M(lambda*w,x)=M(w,x) for lambda>0. For a
constant input, M(w,(c,c))=c*(w1+w2)/(w1+w2)=c. These algebraic identities supply
the desired properties within the defined model. Zero total weight is excluded.

For the supplied arithmetic examples, evaluating this formula gives M=5 for
both weight scales with x=(2,6), and M=5 for both weight scales with x=(5,5).
These are mathematical evaluations of M using the given inputs. They are not
new observations, a new software run or replacements for the CSV's S outputs.

The stated algebraic question is resolved. Whether this normalized quantity is
useful with noisy measurements depends on an unspecified noise model and an
intended application. No noise calculation, data collection or application has
been performed. That possible research direction remains a proposal.
