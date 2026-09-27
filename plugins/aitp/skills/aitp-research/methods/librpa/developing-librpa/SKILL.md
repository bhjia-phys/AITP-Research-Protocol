---
name: developing-librpa
description: Review, simplify, or extend LibRPA numerical code by tracing its active GW/RPA paths, API and driver boundaries, matrix ownership, and relevant regressions. Use for LibRPA source development and PR review, not merely to launch an existing calculation.
---

# Develop LibRPA through its existing numerical path

For research-topic work, use
[aitp-memory](../../../../aitp-memory/SKILL.md), reusing current context.
Establish the requested behavior and the quantity that should change or remain
invariant. A source explanation, implementation cleanup, new feature, and change
of physical approximation need different evidence.

## Find the active implementation

Identify the intended checkout, branch, local edits, upstream target, and, when
running calculations, executable and build configuration. For a PR review,
inspect the complete change against its actual base; comparison with the remote
PR head answers only what the next update adds. Preserve unrelated work.

Read applicable repository instructions and Minye's developer guidance in
`docs/develop/develop_tips.md`. Use `driver/CMakeLists.txt` and
`src/CMakeLists.txt` to check which files execute: `driver/tasks/g0w0.cpp` and
`driver/tasks/qsgw.cpp` are distinct from older `driver/task_*.cpp` drafts.
Follow the existing GW/RPA/EXX caller before introducing a parallel mechanism.

For an unfamiliar subsystem, API change, runtime option, or build decision,
read the relevant section of the [architecture and change guide](references/architecture.md).
Resolve its source pointers against the current checkout; branch layouts evolve.

## Keep the change within its purpose

Include changes that implement the requested behavior, preserve required
compatibility, or provide its necessary validation/documentation. Judge scope
by dependencies and behavior, not file count: synchronizing a shared option
across C and Fortran is necessary work even when it touches several files.
Earlier explicit decisions, including accepted shared defaults, remain in scope.

Leave unrelated refactoring, renaming, formatting, logging redesign, new
frameworks, and changes of physical approximation out of a focused fix or
cleanup. An improvement that can stand alone and is not needed for the requested
result normally belongs in separate work. Note a consequential unrelated issue
without silently fixing it. Continue the authorized task; ask for clarification
only when an unresolved scope choice actually blocks a correct implementation.

## Place the change at the right boundary

- Keep concrete input-file selection, producer filenames, task-specific reading,
  unit decoding, and task output in the driver. Generic readers for standard
  formats, such as CSC/ELSI, may live in `src/io`. Public computation/input APIs
  accept data and do not read input files; library-generated restart files are
  the exception. Numerical operations receive matrices, conventions, and
  mean-field data rather than filenames.
- Implement new public behavior through the C API under `src/api`, with public
  declarations in `include/`; C++ and supported Fortran interfaces wrap that
  layer. Keep host-program presets in the driver and pass parsed conventions
  through the API.
- Prefer public setters and getters over mutating a handler's Dataset from the
  driver. Existing QSGW is a task prototype with internal access; keep necessary
  prototype mutations local to its task. This exception does not establish a
  general interface or require an unrelated API migration during cleanup.
- Assemble physics from existing core objects and reusable math/MPI helpers.
  Follow the developer guide's dependency rules, including the isolation of
  `src/interface`. Check ownership and actual callers before moving a helper.

Separate driver-only parameters from `LibrpaOptions`. A filename change should
not grow the public numerical options struct. A shared option needs its C,
Fortran, initializer, parser, and documentation paths checked as applicable.
Trace defaults and overrides: the shared `nfreq` default affects RPA/GW as well
as QSGW, while the driver supplies some defaults that a library caller must set.

## Trace the numerical state before simplifying it

Follow input through conversion, distribution, numerical operation, and output.
Resolve implicated units, spin/occupation normalization, k ordering and weights,
AO versus KS basis, matrix layout, conjugation, and MPI ownership. Inspect the
producer when meaning is ambiguous; a filename suffix does not establish basis.

For iteration, identify the immutable reference, live eigenpairs, operators, and
caches. Track what is invalidated and rebuilt after each update. Fixed operator
entries differ from a fixed operator represented in changing eigenstates.
Automatic frequency nodes can change with the spectrum at fixed `nfreq`.

`Matz` in `src/math/matrix_m.h` shares storage on ordinary copy; use its `copy()`
or an independently allocated result when mutation must not reach the input.
Check temporary reference substitutions and their restoration on error paths.
Preserve collective order and propagate a root-only failure before other ranks
enter a dependent collective.

Remove wrappers whose work is already expressed by the existing path; retain
physical conversion, projection, lifetime management, and required communication.
Use ordinary native inputs. Do not introduce manifests, hash inventories, or a
second input-description protocol for an ordinary reader change.

## Choose evidence that distinguishes the change

Follow the agreed acceptance scope. Before adding a test, identify a plausible
error introduced by the change and why the existing cases would miss it. Reuse
or extend an existing numerical end-to-end case and comparator when it can
distinguish that error. Add a small full calculation for an uncovered producer
or band path. Use a component test for a specific uncovered numerical or
distributed invariant. Do not add dedicated input/output, file-reader, parser,
log-format, source-text, invalid-input, or error-message tests. Numerical
end-to-end regressions may read output files to compare physical results;
that does not require separate tests of their I/O implementation.

Reject malformed or unsupported input directly with a useful error. Keep the
runtime checks needed to detect it before using the data, and propagate failures
across participating MPI ranks. The absence of error-path tests is not a reason
to omit those checks or silently accept invalid input. Apply the same testing
scope to generic format helpers and avoid duplicate intermediate tests around
an already validated workflow.

Omit or remove redundant test additions within the change being prepared:
checks that mirror implementation details, assert incidental output formatting,
or repeat the same failure coverage without an additional relevant invariant.
An end-to-end pass alone does not establish that every component test is
redundant. Do not expand this cleanup into deleting unrelated upstream tests or
other contributors' work. When removing an in-scope test, identify the retained
coverage or obsolete behavior, and remove its unused registration/helper only
after checking other callers. Do not add production abstractions solely to
support a test that the requested behavior does not need.

Choose controls that expose the suspected error: asymmetric mixing weights,
more than one update for reference mutation, or nontrivial complex/distributed
data for a changed matrix operation. Compare the relevant trajectory or spectrum;
a stable gap alone can hide errors in other bands. See the
[QSGW worked example](references/qsgw-cleanup.md) for these choices and their limits.

Build the affected targets using the actual CMake configuration. Select tests
from the current registrations and runner help; use a fresh output directory
and matched input, frequency settings, MPI ranks, and threads. A source-only
review needs no build, and a build or options-consistency check establishes no
numerical result. If MPI behavior changes, include representative serial and
multi-rank coverage appropriate to that path.

Preserve the baseline and original references. On a numerical mismatch,
distinguish changed controls, a new-code regression, and baseline variation;
repeat the baseline if needed. Do not replace references or relax tolerances
just to pass. Narrowing acceptance must still cover the requested behavior and
explicitly retain the excluded failure. Once required checks pass, expand them
only for a new change or unresolved concern.

## Integrate and report the reviewed behavior

When agent delegation is available and authorized, assign only independent,
bounded tasks. Give each worker the checkout/base, relevant source or Skill,
allowed files, and expected evidence. A review of input conventions can accompany
kernel work without two writers changing the same files. The coordinator reviews
the resulting diff and validates the combined tree; worker summaries alone do
not establish integration correctness.

Report the resulting behavior, the important source locations, checks actually
performed, and remaining limits. Before delivery, review the full proposed diff,
including build registrations, defaults, tests, and documentation. Remove
incidental additions from the prepared change and report consequential deferred
issues briefly; no separate audit file or checklist framework is required.
For an authorized PR update, recheck its target
and final combined tree after incorporating upstream numerical or dependency
changes. Explain net behavior and shared-default effects; separate regression
agreement from physical convergence. Keep useful evidence in the established
working location without another recording protocol.

When revising these development instructions, consult the
[Codex/Kimi source study](references/agent-development-patterns.md). It explains
the division between repository rules, task Skills, and executable checks. The
QSGW example demonstrates particular development decisions; source walkthroughs
of this Skill are not independent measurements of agent effectiveness.
