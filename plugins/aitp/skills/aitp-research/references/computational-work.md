# Computational work: experiments, code, debugging and benchmarks

A calculation starts from a question and ends as an implication in the main note. This
guide covers how to design, implement, debug, benchmark and compare. Where files live is
in [numerical assets](../../aitp-memory/references/numerical-assets.md); how results are
written up is in [computational writing](../../aitp-writing/references/computational-and-mixed.md);
batch jobs follow the [Slurm guide](slurm.md); a field's own conventions and checks are in
its [domain methods](../SKILL.md#domain-methods).

## Design the experiment before running it

Before execution, write in the experiment's note (an existing derivation or report when
it already carries these facts):

- the question and the observable, with its conventions;
- the hypotheses or competing mechanisms, and what each outcome would mean;
- the inputs held fixed and those varied, and the approximation in use;
- the comparison that decides the question, and the acceptance condition, fixed before
  any result is seen;
- the expected cost and the stopping evidence.

Explain why each chosen case exposes the physical or numerical issue. Use the smallest
informative case first, unless it removes the very obstruction under study. Preparing this
account is not authorization to run it; a substantial campaign goes through a reviewed
[plan](../../aitp-memory/references/plans.md).

## Trace the formulation into the code

Follow equation → representation and approximation → active routine → source and build →
executed inputs → output → analysis → claim. Record the source revision and local
changes, build options, the executable actually used and the command, in ordinary prose
or the run script; no AITP identifiers or hashes are needed. A build proves that a target
builds, not that the method is correct.

## Develop a feature

Specify the scientific behaviour the feature should have, choose a test that could expose
its failure, implement it, and check the affected existing behaviour against preserved
baselines. Separate a change to the physical equation from a change to how it is solved:
a new equation is a research choice that needs agreement, unless already authorized.

When changing code that others maintain, validate the intended change and that required
existing behaviour is preserved. Prepare a minimal reproduction when useful, excluding
private research material. Publish upstream or merge only within authorization already
given; otherwise report the prepared change locally.

## Debug a discrepancy

Reproduce the problem under matched conditions with the preserved baseline. Locate the
first meaningful divergence: input or convention, state or representation, numerical
operation, solver, analysis, or physical or model assumption. Reduce the case while
keeping the failing mechanism; a real-valued or zero-effect example cannot validate a
failure that involves complex phases. Correct the responsible code or premise, rerun the
affected controls and inspect the combined result. Keep the failed run and explain how its
interpretation changed.

In an iteration, distinguish the physical approximation, the nonlinear equation, the
solver and the stopping test. A smaller step can hide a large unmixed residual. Repeated
runs without a new discriminating question call for revisiting the method, not a larger scan.

## Benchmark suites

A benchmark answers a stated question about correctness, numerical accuracy, transfer,
physical adequacy or cost. Give each suite one supporting note, linked from the question
it serves, that records:

- its purpose and the question it serves;
- the cases, and the physical reason for each;
- the settings and approximations, with the reason for each choice;
- the tolerances and error definitions, set before results were examined, and any later
  change with its reason;
- the results with units and uncertainty, including failed criteria;
- links to the runs that produced them;
- how to extend the suite to a new case.

| Comparison | Why choose it | What a pass does not establish |
| --- | --- | --- |
| Analytic limit or a nontrivial exact small case | Exposes sign, normalization, symmetry or representation errors | General accuracy or large-system convergence |
| Independent formulation at matched inputs | Separates implementation defects from a shared numerical path; state what is still shared | Correctness of the shared integrals, model or physical input |
| Refinement sequence: basis, mesh, frequency, size, sampling, iteration | Bounds the sensitivity of the claimed observable | Untested limits, or a rigorous bound from an empirical envelope |
| Published result or experiment | Tests compatible observables in an explicitly matched setting | Reproduction when reference states or definitions differ |
| Positive and negative controls | Tests whether the inference accepts what it should and rejects a plausible false positive | A universal classifier from a few examples |
| Performance comparison | Measured cost at matched work, accuracy and hardware | A speedup inferred from smaller matrices or fewer points alone |

If the diagnostic itself fails, repair or qualify the inference before expanding the
campaign. A code revision may need a regression; a revised physical claim may need a
different observable. Neither justifies further testing after the question is settled.

## Reproduce a paper's result

- **Targets.** List each result to reproduce, such as a figure, table, equation or number,
  with its location in the paper and the tolerance that would count as agreement.
- **Inputs.** For each target, list the model, parameters, conventions, basis or mesh and
  code it needs, marked as stated in the paper, found elsewhere (with the source) or
  missing. Record the assumption made for each missing input, and plan a sensitivity check
  when the result could depend on it.
- **Order.** Start with the smallest target that exercises the method. Where the paper
  derives its method, read it with
  [close reading](../../aitp-writing/references/learning.md#read-a-source-closely) first.
- **Outcome.** Classify each target: reproduced within tolerance; reproduced under a stated
  assumption about a missing input; not reproduced, with the diagnosis so far; or a checked
  error in the paper, confirmed by an independent route. Keep the comparison in a
  supporting note and the outcome with its conditions in the main note. A failure to
  reproduce is a result too; record what it rules out.

## Compare with earlier results

Before reporting a changed value, compare it with the applicable earlier result under
matched definitions, units and conditions: an earlier run report, a table in a main note,
a delivered PDF or a published value. Identify the earlier result's source and checks,
keep both locations, and explain a discrepancy. Distinguish the researcher's acceptance
from numerical agreement. Keep superseded measurements unchanged in their original
reports; add a later qualification as a dated note beside them, and explain why the
comparison changed.

## Environments, caches and resumed work

Before building or installing, read the project's environment instructions and look for
an existing suitable environment. Use the established, authorized code, development or environment location for a tool
environment and its caches, which may lie beneath a topic; do not create one in a
prose-only reading or note folder merely because it is the current directory. Record
its requirements and invocation where the experiment or build is described. Installing
needs its own authorization. Use a temporary location only within the
given permission; when no adequate environment or installation authority exists, prepare
the setup and name the missing action.

Before resuming execution, inspect known jobs and outputs, so that work is not duplicated.
A scheduler's success is not a scientific result, and a historical permission never
authorizes a new submission.
