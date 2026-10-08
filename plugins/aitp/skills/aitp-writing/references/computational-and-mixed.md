# Computational work and theory with numerical tests

The narrative should let a reader trace the physical question through the
chosen approximation and observable to the inference the data permit. A
sequence of jobs is not a scientific argument; a method and its results must
explain why the calculation answers the question.

## Computational physics: define the experiment before interpreting it

State the model or material, reference state, physical approximation and target
observable. Identify the executed calculation, including approximations that
exclude effects the reader might otherwise assume were present. Distinguish
newly implemented options, proposed settings and settings actually used.

Define quantities before plotting or comparing them. Retain units, reference
energies, normalization, sampling domain, occupation or sector conventions,
and the order of reduction, averaging and pooling when these change the
observable. A path gap and a Brillouin-zone minimum are different quantities.
Pair-index order can change which tensor element is called direct or exchange.
Explain the convention rather than relying on a familiar symbol.

## Implementation: connect the mathematical operation to the code

Explain what each consequential component constructs, its dependencies and why
the representation is appropriate. State the transformations actually implemented
and connect them to the theory's equations, including approximations and stopping
criteria. A short construction sequence or pseudocode can clarify dependency
order; a file tree or a regression-test list cannot explain the algorithm.

Describe an interface by both format and meaning when the scientific result
depends on it: for example, which spin basis, symmetry operation, index order
or antiunitary action an exported quantity represents. Separate conventions,
selection rules and numerical evidence. Name a routine, class or file format
when it helps a reader understand or use the method. Place a relevant independent
check near the operation it tests, without turning the section into a test log.
A method paper also needs an intended domain, a useful baseline and failure
cases that delimit improvement.

## Computational setup: fix the comparison before showing results

Give a compact account of the settings actually used before interpreting a
benchmark table. Include the choices that affect the result, as applicable:

- Engine and version, functional or Hamiltonian, reference state, spin/SOC and
  magnetic configuration, basis and pseudopotential families.
- Structures, meshes, retained bands or states, occupations/smearing, mixing and
  convergence thresholds. A material catalog can collect differing settings;
  symmetry reductions may also require group conventions and irreducible counts.
- Frequency-grid type, count and range; auxiliary basis, Coulomb treatment,
  cutoffs and self-consistency/update choices for a many-body calculation.
- What is held fixed between variants: binary, input/reference states, accuracy
  targets and resource allocation. State deliberate differences explicitly and
  define the error norms used for comparison.

Do not invent missing settings or impose irrelevant catalog columns. Put lengthy
inputs in linked working assets, supplementary material or a data/code release,
so the methods and supporting material together permit reproduction. Public code
versions and meaningful script interfaces belong where needed. Local queue states,
private paths and bookkeeping do not replace methods. Hardware, parallelism and
measured timings are essential when they support a performance claim.

## Benchmark results: show the quantities behind the conclusion

How a benchmark is designed, its cases and their reasons, its tolerances and its home,
is in research's [computational work](../../aitp-research/references/computational-work.md#benchmark-suites);
this section covers how to present it. Lead with the table that carries the conclusion,
and keep the prose to what the table cannot show: the pattern, the outliers and the
conditions. Give each table one scientific question. Setup, producer-state agreement, RPA
energies and quasiparticle comparisons may need separate tables. Display the
actual values for both variants where available, with units and a defined signed
or absolute difference. If a report contains only a difference or summary norm,
identify it as such; do not reconstruct unavailable individual values.

Make captions self-contained: define symbols, error norms, comparison conditions,
tolerances and relevant exceptions. Define a speedup such as $S=t_{\rm full}/t_{\rm sym}$
only from matched measured timings. A printed zero bounds a difference at the
stated output precision; it does not establish exact equality. An independent
matrix invariant with another norm does not certify the same bound on every
displayed observable.

Cross-check every displayed value and derived difference against the underlying
data or report before using it. A link alone does not verify a number. Keep
rounding and source precision consistent, and mark unavailable quantities.
Interpret the main pattern and consequential outliers in concise prose rather
than repeating each row. Explain an outlier's cause when evidence establishes
it, including the quantitative residual; otherwise leave the cause unresolved.
Do not replace measurements with opaque PASS/FAIL labels.

Keep numerical acceptance thresholds distinct from physical accuracy. Compare
their scales only when the latter is independently supported; a discrepancy
cannot be declared physically negligible from a small number alone. Retain a
failed stricter criterion even if a looser historical criterion passes. Do not
present a threshold chosen after seeing the result as a predeclared one.

## Tell the reader what each check establishes

Keep these claims separate in ordinary prose:

| Evidence | What it can establish |
| --- | --- |
| Execution ended and produced expected files | An operational result exists |
| A new implementation agrees with a retained implementation | Agreement under the matched inputs and approximations |
| A known limit or independently controlled example agrees | A specified part of the algorithm or physical limit is reproduced |
| Mesh, basis, cutoff, frequency or iteration variations stabilize an observable | Numerical control over those tested directions and ranges |
| A comparison with experiment or another theory is meaningful | Physical agreement for compatible observables and conditions, subject to their uncertainties |

One row does not automatically imply the next. For a comparison, identify what
is held fixed and what changes. A claim of acceleration needs comparable work,
accuracy, hardware and measured cost; a reduced matrix or k-point count alone
does not supply a timing result.

Report uncertainty that was actually estimated. Distinguish statistical error,
systematic sensitivity, truncation/discretization error and model error. Specify
independent samples, correlations and the averaging convention when relevant.
Do not invent error bars or describe untested convergence as achieved. For an
unconverged study, report the observed changes and the conclusion they allow.

Organize parameter studies around competing explanations. A numerical failure
may reveal an invalid approximation or an ill-conditioned representation; show
the diagnostic that distinguishes it from a solver or input error. Preserve a
useful negative outcome without treating every failed command as a result.

## Theory with numerical verification: write the connection explicitly

State the analytic claim and then derive the measurable or computable test.
Explain whether the test is necessary, sufficient, or only suggestive. Give the
expected scaling, sign, symmetry, nullity, or limiting behavior before discussing
agreement, with the conditions needed for that expectation.

For example, a first-order obstruction predicts a linear residual in a defined
small parameter. Specify the operator normalization, energy projection and
parameter convention before comparing a fitted slope with that coefficient.
Small defining-relation residuals need not imply conserved generators: algebra
closure and conservation test different equations. A finite-size calculation
cannot silently supply a missing all-size proof.

Separate analytic, discretization and statistical limits. State the order of
limits when it matters, such as taking a perturbation to zero at fixed size
versus increasing size at fixed perturbation. An apparent exponent requires
a fit window, alternative corrections and sensitivity checks appropriate to
the inference; a visually straight line is not by itself an asymptotic law.

For spectral statistics, specify the resolved symmetry blocks, multiplicities,
energy window and repeated-level rule. Form spacings within the intended blocks
before aggregation. State whether means are block-, sample- or spin-weighted.
For unfolding, describe the block-local procedure, fit/trim choices, retained
levels and relevant sensitivities. Analytic reference curves and finite
matched references answer different questions. A ratio near a reference mean
does not alone establish chaos or integrability.

Structure mixed sections around the scientific step: derive the prediction,
show the corresponding controlled comparison, interpret agreement or failure,
then advance the argument. A completed small test may motivate a larger
question while leaving it open. Do not make a theoretical section claim more
than the accompanying computation can actually check.

## Figures and their underlying evidence

A figure should discriminate an interpretation, expose a mechanism, or summarize
a result. Define axes, units, normalization, parameters, sample/sector selection,
error representation and comparison curves in the caption or nearby text.
State the relevant observation; avoid captions that only repeat the title.

In a research note, connect the displayed figure to its generating analysis
and source data or run report. For a paper, provide the methodological detail
and appropriate data/code citation or supplementary location. Preserve original
arrays and clearly distinguish a new analysis from new physical calculations.
Replotting a retained spectrum can validate the plotting chain, but does not
rerun the eigensolver or establish physical convergence.

Keep scripts in their established primary location and link them with the data and the
figure; preserve useful existing filenames and earlier deliverables. When the researcher
asks to see results, reuse an existing figure if it represents the requested data,
settings and analysis; regenerate it when it is missing, stale or the comparison changed.
Inspect the rendered figure, and give an accessible link with a one-line reading. Label
axes with quantities and units, keep colours and markers consistent across related
figures, and plot the comparison the claim needs; a difference or ratio is often clearer
than two overlapping curves. Check the field's
[domain methods](../../aitp-research/SKILL.md#domain-methods) before polishing, such as
unfolding and symmetry sectors for level statistics or the path and Fermi level for band
structures. A polished figure of an unchecked quantity is worse than a plain figure of a
checked one.
