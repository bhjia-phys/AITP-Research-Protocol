# LibRPA architecture and change guide

Use only the sections implicated by the task. Paths below are relative to the
LibRPA checkout, not this Skill. They were checked against the QSGW PR tree at
[e2d2700d](https://github.com/bhjia-phys/LibRPA/tree/e2d2700dbd89d1937e9ef86799819008496b45e6).
The maintained starting points are Minye Zhang's
[development tips](https://github.com/bhjia-phys/LibRPA/blob/e2d2700dbd89d1937e9ef86799819008496b45e6/docs/develop/develop_tips.md),
`docs/user_guide/api_usage.md`, and `docs/develop/dataset_format.md` in the actual
checkout. The map describes this implementation; developer dependency rules
describe the intended architecture, which existing prototypes do not fully meet.

## Find a change through its caller

| Concern | Start reading | Boundary or question to resolve |
| --- | --- | --- |
| Driver input and task dispatch | `driver/main.cpp`, `driver/inputfile.cpp`, `driver/driver.h`, `driver/driver.cpp`, `driver/task.cpp` | `DriverParams` selects files/tasks; `LibrpaOptions` controls library computation. |
| Producer data | `driver/read_data.cpp`, `driver/reader_basis.cpp`, `driver/reader_eigenvec.cpp`, `driver/reader_coulomb.cpp`, `driver/reader_lri.cpp` | Decode file conventions before API calls. Basis producer presets become explicit convention values. |
| Public API | `include/librpa_input.h`, `include/librpa_compute.h`, `include/librpa_options.h`; `src/api/input.cpp`, `src/api/compute_*.cpp`, `src/api/options.cpp` | Shapes, units, index ranges, rank participation, and ownership are part of the interface. |
| API instance and computed state | `src/api/instance_manager.*`, `src/api/dataset.*`, `src/api/dataset_helper.*`, `src/api/compute_helper.*` | Dataset owns mean fields, grids, distributed descriptors, and computation objects/caches. |
| GW/RPA/EXX physics | `src/core/chi0.*`, `src/core/gw.*`, `src/core/exx.*`, `src/core/epsilon.*`, `src/core/meanfield.*`, `src/core/timefreq.*` | RPA correlation goes through `src/api/compute_rpa.cpp` into `compute_RPA_correlation*` in `epsilon.*`; follow the caller and routing. |
| Matrix and distribution mechanics | `src/math/matrix_m.h`, `src/mpi/base_blacs.*`, `src/mpi/kpoint_blacs_parallel_context.*` | Distinguish local storage from a global matrix and trace communicator/descriptor ownership. |
| QSGW prototype | `driver/tasks/qsgw.cpp`, `driver/qsgw/`, `src/qsgw/` | Driver coordinates iteration/I/O; numerical helpers assemble, project, mix, and diagonalize matrices. |
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
are not its active sources. `src/qsgw/CMakeLists.txt` adds helpers to `rpa_lib`.

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

QSGW currently accesses Dataset directly, invalidates compute objects, invokes
the GW build, and temporarily substitutes reference eigenvectors for projection.
That is an existing prototype, not a public QSGW API. Keep a cleanup local to the
authorized task; adding a public API is a distinct change when required. New
prototype helpers that mutate internals should remain local to its driver task
as the developer guide specifies, rather than becoming general mutator APIs.

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
`driver/reader_basis.cpp` translates presets before `h.set_basis_convention`.
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
