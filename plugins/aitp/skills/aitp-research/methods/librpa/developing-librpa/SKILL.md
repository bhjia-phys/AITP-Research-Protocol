---
name: developing-librpa
description: Trace formulas and iteration state through LibRPA source, or modify and validate its numerical implementation. Use for source analysis and code review or development, not merely to launch an existing calculation.
---

# Develop LibRPA against a physical and numerical claim

For research-topic work, first use
[aitp-memory](../../../../aitp-memory/SKILL.md), reusing context already current.
Identify the quantity or approximation being investigated and a small comparison
that could distinguish the competing interpretations. Inspect the actual source
and callers before interpreting a result or choosing an edit; do not infer today's
interface from a historical run or another checkout.

## Establish the working code and executable

Read the project's instructions, Git status and relevant changes. Preserve dirty
work and determine which checkout is intended. Use an isolated worktree only when
the change needs it; remember that a new worktree does not contain uncommitted
edits. Never describe a test there as validating the dirty source elsewhere.

When executing a numerical check, inspect the build cache, configuration and
executable path. Use the
checkout's current CMake options and local environment guidance instead of copied
compiler paths or remembered flags. If needed, create a separate build directory
for this configuration. Establish that the executable being tested was built from
the intended source, including relevant local edits. Compilation alone does not
validate a numerical claim.
For a source-only analysis, establish what the selected code implements and what
remains unexecuted; no build is needed to complete that task.

## Keep the numerical change intelligible

Follow the relevant data through its callers. Check the conventions implicated
by the change: units, spin factors, k-point identity and weights, basis ordering,
matrix dimensions and storage order, conjugation, and MPI distribution or thread
settings. Select the ones that matter rather than turning this into a checklist
for every edit.

For a self-consistent response, follow one update through its callers: which
spectrum, occupations, eigenvectors and operator matrix elements each term uses,
what a cache retains, and when data are rebuilt or transformed. Match frequency
values as well as array lengths. Holding operator entries fixed differs from
holding an operator fixed in a changing eigenbasis. When comparing branches,
establish that they construct the same mathematical object; a shared helper or
an option name does not establish the selected driver's behavior.

For new boundaries, prefer task-specific file handling in the driver, numerical
APIs that accept numerical data rather than filenames, and reusable readers in
the existing I/O layer. Inspect the current layout; this preference does not
authorize moving unrelated code or claim the existing tree already follows it.

## Validate the behavior the change could break

Start with an independent expected value, limiting case, symmetry relation or
existing trusted numerical comparison. Inspect existing component tests before
adding a duplicate. Choose a regression exercising the changed path with the
same inputs and controls on the compared versions. A source-string assertion or
an unchanged final scalar may miss an error in the underlying matrices.

For example, a complex Hamiltonian-mixing change should preserve Hermiticity,
spin/k-point association and the intended linear update across supported matrix
layouts. The public [Hamiltonian-mixing test](https://github.com/bhjia-phys/LibRPA/blob/7f986201/src/test/test_qsgw_hamiltonian_mixing.cpp)
provides a source-reviewed example of this selection. It is a dated reference,
not evidence that a current build passed. Check current test registration and
run the relevant target before claiming execution success.

Choose parameters that expose the suspected error. Half-weight averaging cannot
distinguish swapped initial/target coefficients; retain an unequal-weight case
when testing that ordering. A layout error can also preserve Hermiticity, so
compare the complex entries rather than using Hermiticity alone as acceptance.

For input-based regressions, read the current `regression_tests/README.md` and
runner help. Resolve its working-directory assumptions and select only useful
cases. Give test outputs a fresh workspace; do not overwrite reference results
to make a comparison pass. Broaden testing when the numerical change or observed
failure warrants it, rather than imposing a full campaign on every small edit.

Keep the source location and relevant revision/local changes, build configuration,
actual command, input and output locations, and comparison tolerance in the
existing run report when needed for continuation. Use
[numerical asset guidance](../../../../aitp-memory/references/numerical-assets.md)
when those locations are not established. No additional provenance schema is
required.

## State what was established

Separate source review, successful compilation, executed component checks,
regression agreement and physical convergence. A scheduler rejection is not a
numerical failure; an unrun test is not a pass. Preserve a consequential failed
route or corrected assumption through the topic's ordinary memory decision.
Do not produce another research report for a routine successful command.

This initial Skill is grounded in source inspection and development constraints;
it has not been validated by a new LibRPA build or production calculation here.
[oh-my-LibRPA](https://github.com/AroundPeking/oh-my-LibRPA/tree/0c80d5809d82b60e31691779c2342cb0c063b548)
is a separate reference for calculation workflows and diagnostics. Its MCP
execution harness is not installed or invoked by this Skill. Any future
integration must use the actual available interface and the user's task scope;
this document does not import its admission machinery or execution defaults.
