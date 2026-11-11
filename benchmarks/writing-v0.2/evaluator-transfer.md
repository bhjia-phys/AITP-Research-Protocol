# Held-out evaluator: scalar screening note

Keep this file outside the executor's case materials. Evaluate the finished scientific argument, table, executable figure generator, and rendered PNG together. Do not reward caution that avoids the positive conclusions that this fully specified model supports. No external research or installation is needed.

## Exact solution and numerical answers

From the supplied sign convention,

\[
\Omega^2=\Delta^2+va=10,\quad
W(i\omega)=2\frac{\omega^2+4}{\omega^2+10},\quad
W_c(i\omega)=-\frac{12}{\omega^2+10}.
\]

Thus the integrand defining the positive weight is \(f(\omega)=12/[\pi(\omega^2+10)]\). Substitution \(\omega=\sqrt{10}\tan\theta\) makes its integral a constant times the interval in \(\theta\); it independently gives

\[
S=\frac6{\sqrt{10}},\qquad
S_\Lambda=\frac{12}{\pi\sqrt{10}}
\arctan\frac{12}{\sqrt{10}},\qquad
T_\Lambda=\frac{12}{\pi\sqrt{10}}
\arctan\frac{\sqrt{10}}{12}.
\]

Reference values:

- \(\Omega=3.1622776601683793319988935444327\).
- \(S=1.8973665961010275991993361266596\).
- \(S_\Lambda=1.5861324328356072845945193292001\).
- \(T_\Lambda=0.3112341632654203146048167974595\).
- \(T_\Lambda/S=0.16403480692923944\), about 16.4035 percent.

The following table uses high-precision midpoint sums. Either supplied floating-point column is allowed; they differ from these references in their final few digits.

| N | Raw Q_N | Tail-corrected Q_N | Absolute corrected error | Absolute raw error |
|---:|---:|---:|---:|---:|
| 8 | 1.586486515514629 | 1.897720678780050 | 3.540826790221e-4 | 0.310880080586 |
| 16 | 1.586222928987672 | 1.897457092253092 | 9.049615206460e-5 | 0.311143667113 |
| 32 | 1.586155075719663 | 1.897389238985084 | 2.264288405606e-5 | 0.311211520381 |
| 64 | 1.586138094736788 | 1.897372258002208 | 5.661901180316e-6 | 0.311228501364 |
| 128 | 1.586133848384702 | 1.897368011650122 | 1.415549094260e-6 | 0.311232747716 |
| 256 | 1.586132786727494 | 1.897366949992914 | 3.538918866205e-7 | 0.311233809374 |
| 512 | 1.586132521308867 | 1.897366684574288 | 8.847325998057e-8 | 0.311234074792 |

Numerical tolerances for displayed values: estimates within 5.1e-10 of the references are adequately precise, provided the separately reported errors permit the 1e-7 acceptance decision. Error entries should be within 1 percent of the reference, with an absolute allowance of 5e-13 for floating-point cancellation. Exact constants may be shown with fewer digits if their rounding is clear and the accuracy decision still uses a sufficiently precise reference. Full double-precision calculations or generator values should agree within 5e-12 absolute; for the smallest corrected error allow 1e-11 absolute. These loose computational allowances are well below the gap to the acceptance threshold and do not excuse an incorrect formula.

The largest absolute difference between the two supplied implementation columns is 1.5543122344752192e-15. Calling it order 1e-15 or machine-precision agreement is sufficient. It checks agreement of two evaluations of the same finite grid. It cannot establish convergence to either the truncated or infinite integral.

Let \(e_N=Q_N-S_\Lambda\). It is positive on every supplied grid and is also \(\widetilde Q_N-S\). The raw full-integral error is \(T_\Lambda-e_N\) for these grids, not \(e_N\), and not \(T_\Lambda+e_N\). Refinement reduces \(e_N\) while removing a small cancellation in the raw result; the raw error therefore rises slightly toward the cutoff floor. It does not converge to zero at fixed cutoff.

For the midpoint rule, the leading endpoint term gives

\[
e_N=-\frac{h^2}{24}[f'(\Lambda)-f'(0)]+O(h^4)
=\frac{\Lambda^3}{\pi(\Lambda^2+10)^2}\frac1{N^2}+O(N^{-4}).
\]

The coefficient is 0.023192759458829072. At N=512 the exact error divided by this leading prediction is 0.9999989136918966. The observed orders \(\log_2(e_N/e_{2N})\) are approximately 1.96816, 1.99880, 1.99970, 1.999925, 1.999981, and 1.999995. A numerical second-order argument based on error ratios, a correctly normalized guide, or the endpoint expansion is acceptable. An unsupported word such as "converged" is not an adequate explanation.

Only the corrected N=512 estimate passes absolute error at most 1e-7 among the supplied grids. N=256 misses it by a factor of about 3.54. None of the raw estimates passes. Do not require a claim that 512 is the smallest integer grid in principle; that claim is not established and is false. The exact tail permits a real positive validation result for this model, not just an inconclusive report.

## Model interpretation

Supported exact statements include \(W(0)=0.8\), \(W_c(0)=-1.2\), and \(W/v=0.4\) at zero frequency: a 60 percent reduction relative to the bare scalar interaction. For all finite \(\omega\ge0\), \(0.8\le W(i\omega)<2\), and W increases monotonically to 2 as frequency tends to infinity. The denominator is positive on the stated domain. The analytic integrated weight S is positive.

One quantitative, exact screening statement with its model scope is enough; the article need not list all these properties. The numerical experiment validates quadrature and exact-tail restoration for this defined scalar response. It does not establish material accuracy, a self-consistent GW solution, a universal efficiency result, a real-frequency spectral conclusion, or that the defined S is an energy. The evaluator should not demand these unrelated results.

## Performance answers

Columnwise medians, in milliseconds:

| Implementation | Setup | Per evaluation |
|---|---:|---:|
| Loop | 0.05 | 0.160 |
| Cached | 1.80 | 0.006 |

Both paths at N=512 include the same exact tail and meet the same requested accuracy. Under the given convention,

\[
C_{\rm loop}(R)=0.05+0.160R,\qquad
C_{\rm cached}(R)=1.80+0.006R.
\]

- Steady evaluation cost ratio: 26.6667 in favor of the cached path. This is not a setup-inclusive speedup for every workload.
- Continuous crossing: \(R=(1.80-0.05)/(0.160-0.006)=11.363636\ldots\).
- First positive integer with strictly lower cached total cost: R=12.
- At R=11: loop 1.810 ms, cached 1.866 ms; loop still wins.
- At R=12: loop 1.970 ms, cached 1.872 ms.
- At R=1: loop 0.210 ms, cached 1.806 ms; select the loop for the one-shot workload. Cached is 8.6 times as costly.
- At R=100: loop 16.050 ms, cached 2.400 ms; select cached for the repeated workload. The setup-inclusive ratio is 6.6875 in favor of cached.
- At R=1000: loop 160.050 ms, cached 7.800 ms, if those endpoint values are mentioned or plotted.

Allow 0.005 ms absolute for displayed costs, 0.5 percent for rounded ratios, and 0.02 for the continuous crossing. The integer crossover and two implementation choices must be exact. Plotted cost values should follow the stated formulas to floating-point precision.

Synthetic timing provenance must be explicit in the article or figure caption and must not be contradicted elsewhere. This task supplies no real-machine measured performance. It also specifies no extrapolation of timing to N other than 512, no parameter-dependent speed claims, and no statistical interval. The five batches do not license an empirical uncertainty claim about numerical accuracy.

## Deliverable and visual checks

The output must contain article.md, convergence.png, and plot_convergence.py. The numerical table must be actual Markdown text with all seven grids, not only a picture of a table. article.md must embed convergence.png by a valid relative image link. The generator must accept --data-dir and --output-dir and reproduce the figure from a directory containing the two CSV files without new packages or a web connection. It may use equations embedded in the script; it must not depend on an unprovided hidden file or a preexisting output artifact. A byte-identical PNG is not required across library versions.

Open the PNG to check that it is a real, readable two-panel figure. The first panel needs N on its horizontal axis and errors against the infinite integral for both raw and corrected estimates, with the analytic tail magnitude as a horizontal reference. A log scale is expected to show the very different magnitudes clearly, but another genuinely readable treatment can be accepted. If a discretization curve is also drawn, it coincides with the corrected error, and must not be presented as independent evidence. If a second-order guide is drawn, the reference and normalization should be clear. Labels must identify absolute errors and distinguish the raw and corrected estimates.

The second panel must use total cost in milliseconds, including setup, over R=1 to 1000, and match the two formulas above. It should make the workload dependence and crossover legible; it must not plot only evaluation time and label it total time. Do not require specific colors, dimensions, panel letters, or typography.

Negative control: the supplied caption fragment is already correct and directly applies to the requested convergence panel:

> The horizontal cutoff line is the analytic contribution from frequencies above the cutoff. It is independent of the number of midpoint cells, so refinement at fixed cutoff cannot remove it.

Its retention is expected. A needless paraphrase or "correction" is a narrative/preservation issue, not automatically a scientific fatality. Changing it to assert that refinement removes the tail is a fatal scientific error. An actual figure-design reason to revise the wording is acceptable only if the requested reference remains represented and the reasoning is explained.

## Fatal issues versus narrative issues

A fatal issue defeats the core scientific or deliverable task. Examples are:

- Wrong sign, screening denominator, analytic reference, or tail normalization that changes the result or conclusion.
- Presenting the raw finite-cutoff value as satisfying the full-integral accuracy target; selecting N=256 as passing; or claiming that agreement between implementations proves physical or continuum accuracy.
- Claiming a tail-corrected result is invalid or inconclusive despite the exact supplied model and independent reference, so that the requested positive numerical conclusion is never made.
- Mixing corrected and raw estimators in the performance comparison, omitting setup while calling the cost total, asserting that cached wins at R=1, or otherwise reversing the required implementation choices.
- Reporting the synthetic timing fixture as newly measured real-machine evidence or inventing external performance or physics evidence.
- Missing any of the three required deliverables, no actual usable PNG, no numerical Markdown table, or a generator that cannot produce the plotted data because of a substantive defect or hidden dependency.
- A plot or table that materially contradicts the correct prose, particularly at the accuracy threshold or crossover.

Narrative issues lower writing quality without necessarily invalidating the core result. Examples are a disconnected derivation and results section; repeated caveats that hide the positive result; an unmotivated dump of formulas; failing to explain why the exact-tail correction changes acceptance; opaque figure labels; excessive precision; an arbitrary benchmark-style checklist in the article; needless rewriting of the negative-control caption; and moderate word-count drift. Omission of a requested physical interpretation, convergence rationale, or fair-cost explanation is a major narrative incompleteness even when the remaining numbers are correct. Such omissions should be distinguished from positively false claims.

Judge whether result prose actually interprets the table and figure. A reader should understand which error is removed by which operation and why a fast evaluation does not automatically make the first solve fast. The note should make a definite, scoped recommendation for both supplied workloads.

## Fixture verification and ambiguities

The CSV midpoint values were generated with plain double-precision scalar accumulation and an independently evaluated NumPy array reduction. All rows were then independently recomputed with Python Decimal at 70 decimal digits. The arctangent in the independent reference was evaluated from its alternating power series at sqrt(10)/12 with 200 terms, rather than calling the floating-point arctangent used for a separate exploratory check. Both supplied implementations agree with every high-precision midpoint sum to less than 5e-15. The original response definition was also checked directly against the reduced rational W_c at six frequencies, including zero and the cutoff. The high-precision errors bracket the 1e-7 threshold as stated, and the asymptotic coefficient agrees with the finest-grid error. Median costs and integer crossover were independently evaluated from the timing CSV.

There is no material unresolved ambiguity. Either raw numerical column is explicitly allowed. The performance aggregation rule, timing inclusions, repeated-input semantics, strict crossover rule, fixed grid for timing, accuracy threshold, output-location fallback, and synthetic status are specified. Display rounding and alternative but readable figure styles should be judged by the tolerances and scientific meaning above, not by exact textual equality except for the requested caption preservation.
