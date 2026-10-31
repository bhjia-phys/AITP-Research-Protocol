# LibRPA architecture and change guide

Use only the sections implicated by the task. Paths below are relative to the
LibRPA checkout, not this Skill. Later task paths refer to the functional PR
branches and may not yet be on upstream master. Recheck build registrations
and the actual branch rather than applying a historical prototype map.
The maintained starting points are Minye Zhang's
[development tips](https://github.com/AESM-Group/LibRPA/blob/master/docs/develop/develop_tips.md),
`docs/user_guide/api_usage.md`, and `docs/develop/dataset_format.md` in the actual
checkout. The map locates implementations; developer rules and the agreed scope
determine which boundaries a change may alter.

## Find a change through its caller

| Concern | Start reading | Boundary or question to resolve |
| --- | --- | --- |
| Driver input and task dispatch | `driver/main.cpp`, `driver/inputfile.cpp`, `driver/driver.h`, `driver/driver.cpp`, `driver/task.cpp` | `DriverParams` selects files/tasks; `LibrpaOptions` controls library computation. |
| Producer data | `driver/read_data.cpp`, `driver/reader/read_data.cpp`, `driver/reader/reader_basis.cpp`, `driver/reader/reader_eigenvec.cpp`, `driver/reader/reader_coulomb.cpp`, `driver/reader/reader_lri.cpp` | Decode file conventions before API calls. Basis producer presets become explicit convention values. |
| Public API | `include/librpa_input.h`, `include/librpa_compute.h`, `include/librpa_options.h`; `src/api/input.cpp`, `src/api/compute_*.cpp`, `src/api/options.cpp` | Shapes, units, index ranges, rank participation, and ownership are part of the interface. |
| API instance and computed state | `src/api/instance_manager.*`, `src/api/dataset.*`, `src/api/dataset_helper.*`, `src/api/compute_helper.*` | Dataset owns mean fields, grids, distributed descriptors, and computation objects/caches. |
| GW/RPA/EXX physics | `src/core/chi0.*`, `src/core/gw.*`, `src/core/exx.*`, `src/core/epsilon.*`, `src/core/meanfield.*`, `src/core/timefreq.*` | RPA correlation goes through `src/api/compute_rpa.cpp` into `compute_RPA_correlation*` in `epsilon.*`; follow the caller and routing. |
| Matrix and distribution mechanics | `src/math/matrix_m.h`, `src/mpi/base_blacs.*`, `src/mpi/kpoint_blacs_parallel_context.*` | Distinguish local storage from a global matrix and trace communicator/descriptor ownership. |
| QSGW task | `driver/tasks/qsgw.cpp`, `src/api/compute_qsgw.cpp`, `src/core/qsgw/` | Core owns iterations, live/reference state and checkpoints; the API borrows Dataset objects; driver handles inputs and presentation. |
| cRPA task and coupling | `driver/tasks/crpa.cpp`, `src/api/compute_crpa.cpp`, `src/core/crpa_task.*` | Separate local-frame construction, response model, screened interaction and QSGW task coupling; check actual filenames in the branch. |
| Existing validation | `src/test/CMakeLists.txt`, `driver/test/CMakeLists.txt`, `binding/fortran/test/`, `regression_tests/testsuite.xml` | Determine enabled targets and what each case actually measures. |

The active standalone path is:

```text
driver/main.cpp: MPI -> parse options -> initialize LibRPA -> common input -> task
driver/tasks/g0w0.cpp: task input -> h.build_g0w0_sigma(opts) -> retrieve/output
src/api/librpa.cpp: C++ wrapper -> librpa_build_g0w0_sigma
src/api/compute_g0w0.cpp: Dataset/grid/routing -> chi0, EXX, screened W, Sigma
src/core + src/math + src/mpi: numerical objects and distributed operations
```

Check build registration before reading an old task as the implementation.
`driver/CMakeLists.txt` selects `tasks/qsgw.cpp`; older `task_qsgw*.cpp` files
are not its active sources. `src/CMakeLists.txt` registers the newer
`core/qsgw` task sources and helpers. An old `src/qsgw` path belongs to its dated worked example.

## Public API and lifetime

The ordinary lifecycle is MPI initialization, `librpa_init_global`, handler
creation, options/input setup, compute/retrieve, handler destruction,
`librpa_finalize_global`, then MPI finalization. Consult `include/librpa_global.h`
and `librpa_handler.h` for exceptions such as version queries. Keep the owning
communicator and pointed-to buffers valid for their documented use.

Implement new public behavior in C, then add the C++ interface in
`include/librpa.hpp`/`src/api/librpa.cpp` and the intended Fortran support.
Follow the nearest analogous setter or compute/getter pair, including units,
complex-number representation, index base, collective behavior, and buffer size.
Do not duplicate the physics in wrappers. Check whether the corresponding
existing API is actually exposed in Fortran before assuming parity.

Minye's intended dependency rules keep `src/` independent of the driver and
host program. Core-header access outside core is reserved for API/dataset glue;
`src/interface` wraps external libraries without importing other internal layers.
Concrete input-file reading and producer-specific orchestration belong in the
driver. Generic standard-format readers, including CSC/ELSI decoding, may live
under `src/io`. Public input/computation APIs receive data rather than reading
input files; library-generated restart files are the documented exception.
Reject invalid input directly, retaining necessary runtime validation and MPI
failure propagation. Do not add dedicated I/O or error-path tests, including
for generic readers; use the agreed numerical regressions for calculation
acceptance.

For the functional QSGW/cRPA branches, numerical tasks live in core and borrow
API-owned mean-field/response objects through small adapters. Existing G0W0/RPA
assembly, Dataset and output helpers remain in their established locations.
Extending a new peer task does not require migrating the existing G0W0 workflow.
Check the actual owner when invalidating a cache or temporarily substituting
reference eigenvectors. A historical driver prototype is not authority to add
direct handler mutation in a new driver implementation.

## Apply public review requirements across a change

Read the discussion, submitted reviews and inline threads as well as the diff.
Compare the reviewed change with upstream and each declared predecessor. A
comment on a shared API, fixture or algorithm also matters to dependent stages;
an unresolved thread may already have its source correction. Verify that
correction rather than treating thread state as a numerical verdict.
When the request covers all submitted work, enumerate the author's open and
closed PRs, including the earlier upstream/fork, and finish pagination. Search
text is useful for discovery but can omit a PR whose title uses another method
name. Distinguish maintainer requirements, bot findings, author explanations
and a notice that no review ran. Assess each against the current source; do not
revive removed prototypes or equate a merged PR with a resolved defect.

The [API review on #70](https://github.com/AESM-Group/LibRPA/pull/70#discussion_r4360014222)
requires one responsibility-based public surface: inputs/setters in
`librpa_input.h`, computations/result access in `librpa_compute.h`, options in
`librpa_options.h`. Keep numerical definitions visible to C callers, with
complex packing, dimensions, rank participation, pointer lifetime and deletion
specified. Prefer existing caller-owned output buffers; if a concrete owning
result is needed, define its public layout rather than hiding it behind an
unrelated feature header. Distinguish an intentionally opaque task/handler from
a concrete result. Check direct C/C++ inclusion, wrappers and the installed
header list when moving declarations. Do not duplicate types to escape a
header dependency cycle.

The [Padé review](https://github.com/AESM-Group/LibRPA/pull/70#discussion_r4360014237)
distinguishes barycentric rational interpolation from Thiele continued
fractions. Each algorithm gets its own implementation behind `AnalyCont`;
fallback is explicit composition. A source refactor preserves selected nodes,
rational degree, derivatives and fallback trigger policy. Direct analytic tests
of each algorithm and tests of dispatch answer different questions. Passing a
sample fit does not establish real-axis accuracy or causality.

The [fixture review](https://github.com/AESM-Group/LibRPA/pull/70#discussion_r4360014232)
requires task/producer/system-or-model names. Inspect archived structure and
the actual generator before saying a misleading name is a material change.
A NumPy/SciPy four-state model written in ABACUS format remains a synthetic
Python-generated model. Backend requirements belong in suite build metadata;
new names omit `_libri`. Rename testcase and references together, then update
all fixture users, preserving payloads and numerical tolerances. The resolved
[BN/AlAs discussion](https://github.com/AESM-Group/LibRPA/pull/69#discussion_r4343494302)
shows why a directory label alone cannot establish the material's identity.

The [documentation and verification requests on #67](https://github.com/AESM-Group/LibRPA/pull/67#pullrequestreview-5595284726)
put theory in source-only `docs/theory`, excluded from Sphinx until ready for
publication. Keep task guides below the existing driver/user-guide parent.
Keep only `run_regression.py` at the regression root; companion numerical
verification scripts belong in a subdirectory, with fixture-root and CI
commands adjusted together.

The [scope review](https://github.com/AESM-Group/LibRPA/pull/70#pullrequestreview-5628867342)
asks future submissions to separate a feature from unrelated fixes, while
keeping relevant tests, reference updates and documentation with each change.
Apply this when choosing a new PR scope; preserve an already agreed dependent
stack unless changing it is authorized. After predecessor merges, update the
next stage against the new master without reintroducing its prerequisite diff.
After a squash merge, compare the merged source with the reviewed predecessor:
different commit ancestry alone does not identify a new numerical change.
Preserve maintainer edits in that comparison when carrying the next stage
forward, then verify its focused diff and the combined tree. A merge strategy
that favors the local side can silently drop those edits even without conflicts.
Read back published descriptions and focused file sets. Fixing code is distinct
from obtaining maintainer approval; do not infer permission to close review
threads or merge a PR.

### Earlier QSGW comments: check the convention before accepting the suggestion

The earlier reviews in
[minyez/LibRPA #6](https://github.com/minyez/LibRPA/pull/6) and
[#7](https://github.com/minyez/LibRPA/pull/7) contain bot findings, not new
maintainer policy. They expose several checks that remain useful after source
reorganization:

- [Occupation scaling](https://github.com/minyez/LibRPA/pull/7#discussion_r3643671245):
  recover the stored k weight and spin degeneracy before writing physical
  occupations. With the reviewed uniform-grid convention, the writer multiplies
  stored weights by the number of k points, not additionally by the number of
  independent spin channels. Check a fully occupied collinear channel and the
  total electron count; do not transplant that factor to a different weighting
  convention.
- [Complex rotation](https://github.com/minyez/LibRPA/pull/6#discussion_r3543241359):
  a nearby adjoint is not evidence that every transpose must conjugate. If
  columns of `U` expand new states in the old basis and stored coefficient rows
  are `C[n, mu]`, then `C_new = U^T C_ref`, while operator matrices transform
  as `U^dagger O U`. Recover these definitions from the actual reader and
  eigensolver. Exercise a genuinely complex rotation and an independent
  reconstruction; real-valued cases cannot decide between the two.
- [MPI support](https://github.com/minyez/LibRPA/pull/7#discussion_r3643671280):
  the distributed-matrix test exercises main-thread collectives, so requiring
  MULTIPLE needlessly rejects a FUNNELED implementation. Request and check the
  minimum required by that test. The
  [MPI thread contract](https://docs.open-mpi.org/en/v5.0.0/man-openmpi/man3/MPI_Init_thread.3.html)
  permits `provided < required`; checking the return remains necessary.
  A successful run on a MULTIPLE-capable runtime alone does not exercise this
  portability issue. This conclusion does not lower requirements of threaded
  production communication.
- [Task-name normalization](https://github.com/minyez/LibRPA/pull/7#discussion_r3643671303):
  trace parsing, dispatch and parameter reporting together. An accepted spelling
  should describe the same selected behavior at each boundary. Reuse the
  existing normalization; this does not justify a separate log-format suite.
- [Direct standard includes](https://github.com/minyez/LibRPA/pull/6#discussion_r3543241259)
  and [string facilities](https://github.com/minyez/LibRPA/pull/6#discussion_r3543241305):
  include the declaring standard header in changed translation units rather
  than relying on transitive includes. If the reviewed file was removed, inspect
  its active replacement instead of restoring it.
- [Diagnostic output](https://github.com/minyez/LibRPA/pull/6#discussion_r3543241332)
  and [directory creation](https://github.com/minyez/LibRPA/pull/6#discussion_r3543241389):
  use the existing output-level/rank controls and filesystem helper. A suggestion
  to add an environment variable is one proposed remedy, not a requirement;
  avoid a second logging switch or shell command when the existing facility
  already supplies the behavior.

These are conditional checks of active code. A request to review LibRPA source
does not require editing obsolete PR branches or a separate workflow plugin.
Producer identity should be established from its export/generator and explicit
input conventions, not inferred from one shared filename or from the absence
of another producer's marker.

## Runtime option or default

First determine whether the value is driver policy or library computation.

| Kind of change | Locations to inspect or update as needed |
| --- | --- |
| Driver filename, producer selection, task-only control | `DriverParams` in `driver/driver.h`; constructor/format in `driver/driver.cpp`; parse/validation in `driver/inputfile.cpp`; reader/task caller. |
| Shared numerical option | `include/librpa_options.h`; initializer in `src/api/options.cpp`; driver parsing/formatting if exposed; `LibrpaOptions_c`, high-level `LibrpaOptions`, and `sync_opts` in `binding/fortran/librpa_f03.f90`. |
| New public enum | `include/librpa_enums.h`, its actual wrappers, and the nearest existing enum's conversion/printing paths. |
| Runtime documentation | Doxygen on the owning field in `driver/driver.h` or `include/librpa_options.h`; grouping in `docs/user_guide/runtime_parameters.yml`. |

A field addition requires matching C/Fortran layout and synchronization. A
default-only edit normally changes the initializer and default documentation;
it does not require adding fields or inventing a C++ options structure.
`librpa_init_options` sets `nfreq = 16` in the reviewed tree. Its `tfgrids_type`
starts `UNSET`; the driver selects minimax when omitted. Thus omitting an option
in a driver input is not always equivalent to an unconfigured library call.

Use the existing checker after affected option/documentation edits:

```bash
python3 utilities/check_librpa_options.py
```

If `librpa_f03.f90` changes, follow the documented stub generation from
`binding/fortran`:

```bash
../../utilities/convert_fortran_module_to_stub.py librpa_f03.f90 librpa_f03_stubs.f90
```

Review the generated diff and compile the affected binding when it changes.
The options checker does not prove ABI compatibility or numerical correctness.

## Input or numerical kernel

For producer input, inspect the appropriate section of `dataset_format.md` and
the producer's export implementation when needed. Pass units, basis order,
Bloch phase, and spherical-harmonic conventions as data. For example,
`driver/reader/reader_basis.cpp` translates presets before `h.set_basis_convention`.
Avoid host-name branches in kernels or inferring AO/KS basis from a filename.
Check the selected producer through an existing or small new numerical case.

For kernel or iteration changes, start at the API/driver call and identify the
live input, output storage, invalidated caches, and numerical invariant. QSGW
reuses the ordinary GW build each iteration, then projects into its fixed
reference basis. Preserving only eigenvalues can still leave stale wavefunction,
head/wing, exchange, or band caches. The precise rebuild policy comes from the
active branch, not from the method name alone.

For MPI/layout changes, trace global-to-local indices, empty rank contributions,
matrix descriptors, reductions, and collective order. A local exception before
a collective can strand other ranks. Select an existing MPI test for the
specific invariant and a relevant full calculation if output can change.

For performance changes, measure the same physical input and numerical settings
with matched ranks/threads; inspect the existing profiler before adding timers.
The developer guide recommends `output_level = critical` for profiling to reduce
output overhead. Retain numerical agreement alongside the timing comparison.

## Build and select validation

Inspect `CMakeCache.txt` for its source directory, compiler, MPI and dependency
paths. A copied build tree may still refer to the old checkout. Current options
include `LIBRPA_USE_LIBRI`, `LIBRPA_ENABLE_DRIVER`, `LIBRPA_ENABLE_TEST`,
`LIBRPA_ENABLE_CPP_TEST`, and `LIBRPA_ENABLE_FORTRAN_BIND`. Do not substitute the
obsolete `USE_LIBRI` spelling. Build targets include `rpa_lib` and `rpa_exe`;
the executable output name is set through `LIBRPA_DRIVER_NAME` (currently
`chi0_main.exe`). Configure with the project's applicable `examples/build`
recipe and actual dependencies, rather than assuming a universal toolchain.

Use `cmake --build` for the affected target and `ctest --test-dir ... -N` to
inspect registrations before selecting a component test with `-R`. Some CTest
entries already launch four MPI ranks; do not wrap the entire CTest invocation
in another MPI launcher. Fortran bindings/tests must be enabled to exercise them.

From `regression_tests`, inspect current CLI help and list the desired cases
before execution. This command selects a case without running it:

```bash
python3 run_regression.py list --use-libri -n 4 --nthreads 1 \
  --only qsgw_aims_mole_H2O_libri
```

For an actual run, use `full` with the chosen executable, the same applicable
build/runtime flags, selected cases, and a fresh `-d` workspace. Keep reports
with that run using `-o`; avoid `--force` over original outputs. Reuse
`testsuite.xml` comparators and inspect their current argument syntax before
copying a documentation example. Test selection, build success, numerical
agreement, and physical convergence are separate claims.
