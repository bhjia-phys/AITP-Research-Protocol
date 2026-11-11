# Writing benchmark v0.2: theory, numerical evidence and exposition

This extends [v0.1](../writing-v0.1/README.md), whose short writing checks largely
reached a scoring ceiling. The new cases require actual scientific artifacts: a
note or article, a rendered figure and generator, a focused numerical table and
connected interpretation. The inputs distribute assumptions, numerical conventions
and draft claims across a small packet rather than handing the executor an error list.
All physics data are synthetic; no private chaos manuscript or live calculation is used.

M01 asks how finite conservation, spectral and dynamical probes can be combined.
M02 asks when a perturbative approximation remains useful as a gap closes.
[M03](cases/M03/prompt.md) connects exact scalar screening, cutoff and quadrature errors,
and setup-inclusive performance; its checked caption is a preservation control.
This transfer case was authored without access to optimization results and withheld
from the optimizer until the candidate patch was frozen, then published.
Publication makes it a regression case for subsequent work, not a permanently hidden test.

Copy only one `cases/<case>/` directory into a fresh executor workspace. Provide its
prompt and the guidance allowed by the condition. Keep this README, evaluator files,
other cases and prior outputs out of that workspace. The executor may use local Python,
NumPy and Matplotlib to inspect/replot inputs and verify elementary mathematics; no
installation, network, outside research or cluster work is needed. Each case runs in
a separate fresh session. Confirm actual artifacts exist and inspect the rendered plot.

Use [the comparison isolation rules](../general-v0.1/README.md#分开测三种条件): plain,
frozen current AITP and a candidate revision under matched model, reasoning, tools,
resource bounds and case inputs. Freeze the actual dirty working-tree files. Predefine
the [seven-axis rubric](evaluator.md) and [case checks](evaluator-cases.md) before the
first run. Scores distinguish science, inference, motivation, coherence, figure, table
and reconstructibility; no weighted sum can excuse a false central claim.

Inspect current-version failures before changing the Skills. Make a narrowly justified
change in the existing owner, then repeat affected cases and the positive/negative
controls. Compare unseen transfer before making further changes; after exposure it is
no longer held out. Keep all runs, including failures, and anonymize condition labels
for the grader. Repeat a promising difference before attributing a general benefit;
without replication report only the observed difference and its uncertainty.

The acceptance target is no critical scientific error, no regression in a valid result
or already-clear passage, and a located improvement in the targeted reader operation.
If no difference appears, report the tie rather than increasing prose requirements.
If the scorer cannot distinguish a valid positive result from an unjustified claim,
repair and version the rubric before optimizing the Skill against it. No framework,
runtime service or mandatory research-note scoring protocol is introduced.

Actual results and limitations are recorded in [validation](../../docs/validation.md).
Frozen inputs, guidance, outputs and grading evidence remain outside the public tree.
The [transfer answer key](evaluator-transfer.md) is evaluator-only too. A procedural
clarification during the first evaluation renamed the reconstructibility exercise a
source-informed audit, because graders could already access the packet and key. It
changed no scoring axis or scientific answer. This run supplies no cold-reader or
human-learning evidence.

## Concrete examples

These are synthetic teaching examples, not conclusions about a researcher's system.
The executor sees only its case packet; this section is for people choosing a test.

| Case | Figure and table do this scientific work | The prose must explain |
| --- | --- | --- |
| [M01: charges, spectra and clocks](cases/M01/prompt.md) | Compare the same dynamics on physical and rescaled clocks; display the transformation of the quadratic coefficient. | Why a fixed-charge obstruction, a spectral crossover and operator change ask different questions; what their combination does establish. |
| [M02: a closing perturbative gap](cases/M02/prompt.md) | Contrast absolute and relative errors along fixed-coupling and fixed-gap-ratio paths; show the accuracy criterion quantitatively. | Why solver agreement does not control perturbation theory, and why commuting limits of energy values do not preserve a Taylor expansion. |
| [M03: screening, quadrature and reuse](cases/M03/prompt.md) | Separate the cutoff floor from grid error; tabulate raw/corrected values and compare total cost including setup. | Which positive results the exact toy model supports, which grid meets the target, and why the preferred implementation depends on workload. |

For example, M01 has the following exact transformation of the supplied coefficients:

| Coupling | Energy scale J | Coefficient of physical t² | Coefficient of rescaled τ², τ=Jt |
| --- | ---: | ---: | ---: |
| 0.1 | 1 | 4 | 4 |
| 0.4 | 3 | 9 | 1 |

A defensible result sentence is: “The larger coupling has greater initial curvature
on the common physical clock, but smaller curvature at equal rescaled time. This
comparison depends on the clock and supplies no identity relating operator change
to the obstruction for the different reference charge.” The accompanying graph must
actually apply τ=Jt; a correct caption cannot rescue an inverse transformation.

For an ordinary note, ask for a concrete review rather than a compulsory scorecard:
“Explain what the theory predicts and what the numerics test; check the comparisons
in the figures and tables; locate the first unsupported inference or missing reader
step; revise only what the evidence warrants.” For Skill development, use the full
separate scoring profile to locate a repeatable failure before changing instructions.

## Check the evaluator too

Keep an unchanged sound output as a control. In separate copies, change only a
plotted transformation while preserving its stated label, or change one decisive
table value while preserving the prose. Have an evaluator inspect the anonymized
artifacts and their data without the mutation map. Record whether it locates the
defect, recognizes its consequence and leaves the sound control alone. These are
deliberately planted scoring controls, not model-generated errors or extra executor
replicates. Retain the mutation map and original outputs outside the public tree.
