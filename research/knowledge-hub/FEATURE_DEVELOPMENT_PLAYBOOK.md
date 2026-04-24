# Feature Development Playbook

A step-by-step protocol for developing new physics features in ABACUS, LibRPA,
LibRI, LibComm, pyatb, and related first-principles toolchain components — from
idea to production readiness, deeply integrated with the AITP research layer
model.

**Walkthrough example**: implementing GW quasiparticle band structure for metals
(metal GW).

---

## Overview

Feature development in computational physics is not just coding. It is a loop
where physics correctness, numerical stability, and software engineering
converge. This playbook defines **9 phases**, each with explicit inputs,
outputs, decision gates, and AITP layer mapping.

**Prerequisite**: Read [PROJECT_STRUCTURE_CONVENTION.md](./PROJECT_STRUCTURE_CONVENTION.md)
first. Every project must follow the folder structure, LaTeX documentation,
and derive-first workflow defined there.

```
Phase P: Project Setup            ←→  Folder creation + AITP bootstrap (L0)
Phase 0: Feature Scoping          ←→  AITP topic scoping (L0)
Phase 1: Theory & Derivation      ←→  AITP L0 source → L1 derivation (LATEX)
         *** GATE G0: Human approves derivation ***
Phase 2: Development Planning      ←→  AITP L1 provisional understanding
Phase 3: Implementation            ←→  AITP L3 exploratory outputs (CODE FOLLOWS DERIVATION)
Phase 4: Build & Smoke Test        ←→  AITP L3 + L4 validation
Phase 5: Benchmark Campaign        ←→  AITP L4 validation gate
Phase 6: Debug Loop                ←→  AITP L4 → L3 feedback
Phase 7: Production Readiness      ←→  AITP L2 trusted memory
```

### Contracts used

| Phase | Primary contract | Supporting contracts |
|-------|-----------------|---------------------|
| P | — | PROJECT_STRUCTURE_CONVENTION |
| 0 | AITP topic shell | — |
| 1 | AITP topic shell + LaTeX derivation | — |
| 2 | `development-task` | `compute-resource` |
| 3 | `development-task` | `computation-workflow` |
| 4 | `computation-workflow` | `compute-resource`, `development-task` |
| 5 | `benchmark-report` | `computation-workflow`, `development-task` |
| 6 | `calculation-debug` | `computation-workflow` |
| 7 | `benchmark-report` | `development-task` |

### Decision gates

| Gate | Between phases | Pass criteria | Fail action |
|------|---------------|---------------|-------------|
| G0: Derivation approved | 1→2 | LaTeX derivation complete, human reviewed and approved | Revise derivation |
| G1: Scope clear | 0→1 | Physics question bounded, system types identified | Refine scope |
| G2: Plan approved | 2→3 | `development-task` contract filled, build config known | Revise plan |
| G3: Compiles + passes smoke | 4→5 | Clean build, smoke test passes on ≥1 system | Debug loop (Phase 6) |
| G4: Benchmarks pass | 5→7 | `benchmark-report` verdict = `pass` or `partial` | Debug loop (Phase 6) |
| G5: Production ready | 7→done | All invariants satisfied, human approval | Back to Phase 6 |

---

## Phase P: Project Setup

**Goal**: Create the project folder with full directory structure, LaTeX
template, and AITP topic bootstrap. Every project starts here — no exceptions.

**AITP layer**: L0 — project initialization.

### Steps

1. **Ask the human for the project folder location.** The agent proposes a
   default (e.g., `~/projects/<topic-slug>/`), the human confirms or overrides.
2. **Create the full directory structure** following
   [PROJECT_STRUCTURE_CONVENTION.md](./PROJECT_STRUCTURE_CONVENTION.md):
   ```
   <project-root>/
   ├── L0_source/ref/
   ├── L1_intake/
   ├── L2_canonical/
   ├── L3_exploratory/
   ├── L4_validation/
   ├── docs/sections/
   ├── docs/figures/
   ├── code/patches/
   ├── computation/smoke_test/
   ├── computation/benchmark/
   ├── contracts/
   ├── build/cmake/
   └── README.md
   ```
3. **Create `docs/main.tex`** with the standard LaTeX template (see
   PROJECT_STRUCTURE_CONVENTION.md §5).
4. **Create `docs/preamble.sty`** with physics macros.
5. **Create stub `.tex` files** in `docs/sections/`.
6. **Bootstrap the AITP topic** and record the topic slug in `README.md`.
7. **Verify LaTeX compiles** — run `latexmk -pdf main.tex` in `docs/`.

### Walkthrough: metal GW

```bash
# Human chooses location
mkdir -p ~/projects/metal-gw/{L0_source/ref,L1_intake,L2_canonical,L3_exploratory,L4_validation}
mkdir -p ~/projects/metal-gw/docs/{sections,figures}
mkdir -p ~/projects/metal-gw/{code/patches,computation/{smoke_test,benchmark},contracts,build/cmake}

# Create LaTeX template
# (agent generates main.tex, preamble.sty, section stubs)

# Verify
cd ~/projects/metal-gw/docs && latexmk -pdf main.tex

# Bootstrap AITP topic
aitp bootstrap --topic "metal-gw" --statement "Enable GW for metallic systems."
```

---

## Phase 0: Feature Scoping

**Goal**: Turn a vague idea into a bounded feature request with clear physics
scope, target systems, and success criteria.

**AITP layer**: L0 — topic bootstrap.

### Steps

1. **State the physics need** in one sentence.
2. **Identify target codes**: which component(s) need changes?
3. **Identify system types**: molecule, solid, 2D — or all?
4. **Identify reference data**: what known results must we reproduce?
5. **State what "done" looks like**: quantitative success criteria.

### Gate G1 (Scope clear)

- [ ] Physics question is bounded (not "improve GW" but "enable GW for metallic
  systems with partial occupancies")
- [ ] Target code identified (e.g., LibRPA + ABACUS)
- [ ] System types listed (e.g., bulk Al, bulk Cu, Na cluster)
- [ ] At least one quantitative reference exists (e.g., VASP GW gap for Al =
  0.0 eV, or experimental work function)
- [ ] Success criteria stated (e.g., "GW quasiparticle energies for metals
  within 0.2 eV of VASP reference")

### Walkthrough: metal GW

- **Physics need**: ABACUS+LibRPA cannot currently compute GW for metallic
  systems because the NSCF stage assumes insulating band gaps (no Fermi-level
  smearing, no partial occupancies).
- **Target codes**: ABACUS (NSCF with smearing), LibRPA (polarizability with
  partial occupancies).
- **System types**: solid (bulk Al, bulk Cu, Na).
- **Reference data**: VASP GW quasiparticle band structures for Al and Cu;
  experimental work functions.
- **Done means**: GW band structure for bulk Al within 0.2 eV of VASP
  reference, convergence with respect to k-points demonstrated.

### AITP integration

Bootstrap an AITP topic:

```bash
aitp bootstrap \
  --topic "metal-gw" \
  --statement "Enable GW quasiparticle calculations for metallic systems in ABACUS+LibRPA by adding Fermi-level smearing and partial occupancy support to the NSCF and polarizability stages."
```

---

## Phase 1: Theory & Derivation

**Goal**: Gather the formalism, derive the working equations in LaTeX, and get
human approval before any code is written.

**AITP layer**: L0→L1 — source acquisition and provisional understanding.

### Steps

1. **Collect primary references**: papers that define the algorithm. Download
   PDFs and TeX sources into `L0_source/ref/`.
2. **Study existing implementations**: how do VASP, QE, BerkeleyGW handle this?
3. **Identify known pitfalls** for the specific physics problem.
4. **Derive the working equations in LaTeX**: write `docs/sections/02_derivation.tex`
   with:
   - Starting equations (with literature citations)
   - Assumptions and approximations
   - Step-by-step algebra
   - Final formula(s) that will be implemented in code
   - Domain of validity
5. **Write the implementation mapping**: `docs/sections/03_implementation.tex`
   mapping each derived equation to the code location where it will be
   implemented.
6. **Compile LaTeX** and present the PDF to the human.

### Walkthrough: metal GW

**Primary references** (downloaded to `L0_source/ref/`):
- `Hybertsen_Louie_PRB34_5390_1986.pdf` — GW formalism
- `Shishkin_Kresse_PRB75_235102_2007.pdf` — metal GW with analytic continuation
- `Bruneval_Gonze_PRB79_115117_2009.pdf` — smearing in GW

**Derivation** (`docs/sections/02_derivation.tex`):

The key derivation covers the polarizability with partial occupancies:

$$\chi^0_{GG'}(q, i\omega) = \frac{1}{\Omega} \sum_{k} \sum_{n,m}
\frac{(f_{nk} - f_{m,k+q})\, M_{nmk}(G,q)\, M_{nmk}^*(G',q)}
{\epsilon_{nk} - \epsilon_{m,k+q} + i\omega + i\eta\,\text{sgn}(\epsilon_{nk} - \epsilon_{m,k+q})}$$

where $f_{nk}$ is the Fermi-Dirac occupation:

$$f_{nk} = \frac{1}{1 + \exp\left(\frac{\epsilon_{nk} - E_F}{\sigma}\right)}$$

The derivation then covers:
1. How $E_F$ is determined from the NSCF band structure
2. How the smearing width $\sigma$ affects convergence
3. The limit $\sigma \to 0$ recovers the insulator formula
4. Implementation in the existing LibRPA $\chi^0$ loop structure

**Implementation mapping** (`docs/sections/03_implementation.tex`):

| Equation | Code location | Change |
|----------|--------------|--------|
| Fermi-Dirac $f_{nk}$ | ABACUS `write_wfc_nao.cpp` | Compute and write to NSCF output |
| $\chi^0$ with occupations | LibRPA `gw.cpp:compute_chi0()` | Replace `if(occupied)` with `weight = f_nk * (1 - f_mk)` |
| $E_F$ determination | LibRPA `read_abacus_output.cpp` | Parse Fermi level from NSCF output |

### Gate G0: Derivation approved

**This is the most critical gate. No code may be written until this gate passes.**

- [ ] `docs/sections/02_derivation.tex` is complete with all elements:
  starting equations, assumptions, steps, final formula, validity domain
- [ ] LaTeX compiles without errors
- [ ] Human has reviewed the compiled PDF and explicitly approved the derivation
- [ ] Human has confirmed the implementation mapping makes sense

If the human requests modifications → update the derivation, recompile,
re-present. **Do not proceed to Phase 2 until the human says "approved".**

### AITP integration

```bash
aitp loop --topic-slug metal-gw \
  --human-request "Collect references on GW for metallic systems and derive the polarizability formula with Fermi-Dirac occupations in docs/sections/02_derivation.tex."
```

---

## Phase 2: Development Planning

**Goal**: Create a concrete plan — where in the code, which branch, what build
config, what tests.

**AITP layer**: L1 — provisional understanding.

### Steps

1. **Locate the code**: identify exact source files that need changes.
2. **Choose the branch strategy**: feature branch off main? Fork?
3. **Define build configuration**: toolchain, dependencies, cmake flags.
4. **Plan test strategy**: unit tests, integration tests, physical correctness
   checks.
5. **Fill a `development-task` contract**.
6. **Declare compute resources** via `compute-resource` contracts.

### Walkthrough: metal GW

**Code locations**:

| Code | Files | Change type |
|------|-------|-------------|
| ABACUS | `src/module_io/write_wfc_nao.cpp`, `src/module_io/input.cpp` | Write band occupancies to NSCF output |
| LibRPA | `src/module_pw/pw_basis.cpp`, `src/module_gw/gw.cpp` | Read fractional occupations, compute polarizability with smearing |

**`development-task` contract**:

```json
{
  "task_id": "metal-gw-abacus-librpa",
  "target": "abacus",
  "feature_description": "Add Fermi-level smearing support to ABACUS NSCF output and LibRPA polarizability computation, enabling GW calculations for metallic systems.",
  "motivation": "Metallic systems have partial band occupancies near the Fermi level. Current ABACUS NSCF output assumes integer occupations, causing LibRPA to produce incorrect polarizability matrices for metals.",
  "code_location": {
    "repo": "https://github.com/deepmodeling/ABACUS",
    "branch": "feature/metal-gw-nscf",
    "key_files": [
      "src/module_io/write_wfc_nao.cpp",
      "src/module_cell/module_symmetry/symmetry.cpp",
      "src/module_io/input.cpp"
    ],
    "depends_on": ["LibRPA metal-gw branch"]
  },
  "build_config": {
    "toolchain": "intel-oneapi",
    "cmake_flags": ["-DENABLE_LCA=ON", "-DBUILD_TESTING=ON"]
  },
  "validation": {
    "unit_tests": ["test_nscf_occupancy_output", "test_smearing_fermi_dirac"],
    "integration_tests": ["test_gw_bulk_al_smearing"],
    "physical_correctness": "GW quasiparticle band structure of bulk Al within 0.2 eV of VASP reference. Work function within 0.3 eV of experimental value (4.08 eV for Al(111)).",
    "regression_against": "ABACUS develop branch, LibRPA main branch"
  },
  "status": "planned",
  "related_computation": "gw-al-bulk-001",
  "topic_slug": "metal-gw",
  "notes": "ABACUS changes must be backwards-compatible — integer occupations still work for insulators."
}
```

A second `development-task` for LibRPA:

```json
{
  "task_id": "metal-gw-librpa",
  "target": "librpa",
  "feature_description": "Read fractional band occupations from ABACUS NSCF output and compute the polarizability with Fermi-Dirac smearing for metallic GW.",
  "motivation": "The polarizability χ₀ for metals requires integrating over partially occupied bands. Current LibRPA assumes all bands are either fully occupied or empty.",
  "code_location": {
    "repo": "https://github.com/AroundPeking/LibRPA",
    "branch": "feature/metal-gw",
    "key_files": [
      "src/module_pw/pw_basis.cpp",
      "src/module_gw/gw.cpp",
      "src/module_io/read_abacus_output.cpp"
    ],
    "depends_on": ["ABACUS feature/metal-gw-nscf branch"]
  },
  "build_config": {
    "toolchain": "intel-oneapi",
    "cmake_flags": ["-DENABLE_LCA=ON"]
  },
  "validation": {
    "physical_correctness": "Polarizability eigenvalues converge monotonically with smearing width. GW gap for Al ≈ 0 eV (metal). GW gap for Si unchanged from insulator reference."
  },
  "status": "planned",
  "related_computation": "gw-al-bulk-001",
  "topic_slug": "metal-gw"
}
```

### Gate G2 (Plan approved)

- [ ] `development-task` contracts filled for each affected code
- [ ] Branch names chosen
- [ ] Build configuration verified on target compute resource
- [ ] Test systems identified with reference values
- [ ] Human approves the plan

### AITP integration

```bash
aitp loop --topic-slug metal-gw \
  --human-request "Create development task contracts for ABACUS and LibRPA changes needed for metal GW support."
```

The `development-task` contracts become L1 artifacts in the topic.

---

## Phase 3: Implementation

**Goal**: Write the code that implements the approved derivation — strictly
following the equations in `docs/sections/02_derivation.tex`.

**AITP layer**: L3 — exploratory outputs.

**Prerequisite**: Gate G0 must have passed. The derivation in
`docs/sections/02_derivation.tex` has been human-approved. Code must implement
exactly what the derivation says — no deviations.

### Steps

1. **Create feature branch** on each target repository.
2. **Implement changes** — following the implementation mapping in
   `docs/sections/03_implementation.tex`. Every code block must reference the
   specific equation number from the derivation.
3. **Write unit tests** — test the new functions in isolation, using values
   computed from the derivation formulas.
4. **Update `development-task.status`** to `in_progress`.
5. **Record progress notes** in the AITP topic.

### Rules

- **Code follows derivation.** Every function that implements physics must have
  a comment referencing the equation: `// Implements Eq. (12) from
  docs/sections/02_derivation.tex`.
- **No derivation deviations.** If the code needs a different formula than what
  was derived, stop. Go back to Phase 1, update the derivation, get human
  approval, then return to implementation.
- **One concern per commit** — do not mix smearing logic with refactoring.
- **Backwards compatibility** — existing insulator workflows must still work.
- **No suppressed errors** — no `#pragma`, no `try/catch {}`, no `as any`.

### Walkthrough: metal GW

**ABACUS changes** (implements derivation Eqs. 2–4):
1. Add `smearing_method` and `smearing_sigma` keywords to `INPUT` parsing.
2. In NSCF run, compute Fermi-Dirac occupations (Eq. 2 in derivation):
   `// Implements Eq. (2): Fermi-Dirac distribution from 02_derivation.tex`
3. Write `occupancy` field to NSCF output (new section, backwards-compatible).
4. Unit test: verify `f(E) = 1/(1+exp((E-Ef)/sigma))` for known values
   (computed from the derivation formula).

**LibRPA changes** (implements derivation Eq. 1):
1. Read occupancy data from ABACUS NSCF output (new parser).
2. In `χ₀` computation, weight each band pair by `f_nk × (1 - f_mk')`.
3. Add `smearing` section to `librpa.in` schema.
4. Unit test: verify `χ₀` reduces to insulator formula when all occupations
   are 0 or 1.

### AITP integration

```bash
aitp loop --topic-slug metal-gw \
  --human-request "Implementing NSCF smearing in ABACUS. Key files: write_wfc_nao.cpp, input.cpp. Unit tests added."
```

---

## Phase 4: Build & Smoke Test

**Goal**: Compile on the target platform and run a minimal test case.

**AITP layer**: L3→L4 — first validation gate.

### Steps

1. **Build on target resource** — use `compute-resource` to select the machine.
2. **Run smoke test** — the smallest possible test case:
   - For metal GW: bulk Al, 2×2×2 k-grid, low ecutwfc, 2 bands
   - Must complete all stages: SCF → DF → NSCF → LibRPA
   - SCF must converge, NSCF must produce fractional occupations, LibRPA must
     not crash
3. **Check invariants** from the protocol document (§7):
   - `shrink_consistency`: ABFS files match `librpa.in`
   - `same_libri`: ABACUS and LibRPA linked against same LibRI
   - `keyword_compat`: no deprecated keywords
   - `smoke_first`: minimal test passed before full calculation
   - `toolchain_consistency`: build and run environments match
4. **Fill a `computation-workflow` contract** for the smoke test.

### Walkthrough: metal GW

**Smoke test computation-workflow**:

```json
{
  "workflow_id": "gw-al-smoke-001",
  "computation_type": "gw",
  "system_type": "solid",
  "structure_file": "Al.cif",
  "stages": [
    {
      "name": "scf",
      "status": "completed",
      "input_files": ["STRU", "KPT", "INPUT_scf"],
      "output_artifacts": ["OUT.ABACUS/running_scf.log"],
      "depends_on": [],
      "validation": "convergence_reached, E_change < 1e-5 Ry"
    },
    {
      "name": "df",
      "status": "completed",
      "input_files": ["INPUT_df"],
      "output_artifacts": ["OUT.ABACUS/Coulomb_Matrices"],
      "depends_on": ["scf"],
      "validation": "coulomb_matrices_exist"
    },
    {
      "name": "nscf",
      "status": "completed",
      "input_files": ["INPUT_nscf", "KPT_nscf"],
      "output_artifacts": ["OUT.ABACUS/running_nscf.log"],
      "depends_on": ["scf"],
      "validation": "fractional_occupancies_present"
    },
    {
      "name": "librpa",
      "status": "completed",
      "input_files": ["librpa.in"],
      "output_artifacts": ["gw_band.dat"],
      "depends_on": ["df", "nscf"],
      "validation": "gw_band_output_exists, no NaN in eigenvalues"
    }
  ],
  "basis_integrity": {
    "pseudopotentials": ["Al.upf"],
    "nao_orbitals": ["Al_gga_8au_100Ry_2s2p1d.orb"],
    "abfs_orbitals": [],
    "shrink_invariant": true
  },
  "compute": {
    "location": "server",
    "server_alias": "df",
    "mpi_np": 16,
    "cpus_per_task": 4,
    "omp_num_threads": 4
  },
  "topic_slug": "metal-gw",
  "notes": "Smoke test: 2x2x2 k-grid, low ecutwfc. Purpose is to verify no crashes, not physical accuracy."
}
```

### Gate G3 (Compiles + passes smoke)

- [ ] Clean build (zero errors, zero new warnings)
- [ ] All unit tests pass
- [ ] Smoke computation completes all 4 stages
- [ ] No NaN in output
- [ ] Fractional occupancies visible in NSCF output
- [ ] All 5 protocol invariants pass

If gate fails → **Phase 6: Debug Loop**.

---

## Phase 5: Benchmark Campaign

**Goal**: Validate physical correctness against known reference values across
multiple test systems.

**AITP layer**: L4 — validation and trust audit.

### Steps

1. **Select benchmark systems** — at least 2, covering edge cases:
   - Primary: bulk Al (simple metal, Fermi surface)
   - Secondary: bulk Cu (d-band metal, more complex)
   - Regression: bulk Si (insulator — must still work)
2. **Define convergence tests** — vary key parameters:
   - k-points: 4×4×4 → 8×8×8 → 12×12×12 → 16×16×16
   - smearing width: 0.01 → 0.05 → 0.10 → 0.20 Ry
   - ecutwfc: 40 → 60 → 80 Ry
3. **Run production calculations** — use full k-grids and converged parameters.
4. **Compare against references** — VASP GW, experimental data.
5. **Fill a `benchmark-report` contract**.

### Walkthrough: metal GW

**Benchmark systems**:

| System | Type | Observable | Reference | Tolerance |
|--------|------|-----------|-----------|-----------|
| Bulk Al | solid | GW QP band width (eV) | VASP: 11.6 | < 0.3 |
| Bulk Al | solid | Work function (eV) | Expt: 4.08 | < 0.3 |
| Bulk Cu | solid | GW QP band width (eV) | VASP: 8.2 | < 0.3 |
| Bulk Si | solid | GW direct gap at Γ (eV) | VASP: 3.40 | < 0.1 (regression) |
| Bulk Si | solid | GW indirect gap (eV) | VASP: 1.25 | < 0.1 (regression) |

**Convergence tests**:

| Parameter | Values | Expected behavior |
|-----------|--------|-------------------|
| k-points | 4, 8, 12, 16 | monotonic convergence of band width |
| smearing σ | 0.01, 0.05, 0.10, 0.20 Ry | QP energies stable for σ < 0.10 |
| ecutwfc | 40, 60, 80 Ry | monotonic convergence |

**`benchmark-report` contract** (example outcome):

```json
{
  "report_id": "bench-metal-gw-v1",
  "feature": "Metal GW with Fermi-Dirac smearing",
  "target_version": "ABACUS:feature/metal-gw-nscf@c5ea507 + LibRPA:feature/metal-gw@b3f7c21",
  "baseline_version": "ABACUS:develop@a1b2c3d + LibRPA:main@e4f5g6h",
  "test_systems": [
    {
      "name": "bulk Al",
      "system_type": "solid",
      "results": [
        {
          "observable": "GW QP band width (eV)",
          "new_value": 11.45,
          "baseline_value": null,
          "deviation": "N/A (new feature)",
          "pass": true,
          "tolerance": "within 0.3 eV of VASP reference (11.6 eV)"
        },
        {
          "observable": "Work function (eV)",
          "new_value": 4.12,
          "baseline_value": null,
          "deviation": "N/A (new feature)",
          "pass": true,
          "tolerance": "within 0.3 eV of experimental value (4.08 eV)"
        }
      ]
    },
    {
      "name": "bulk Si (regression)",
      "system_type": "solid",
      "results": [
        {
          "observable": "GW direct gap at Γ (eV)",
          "new_value": 3.39,
          "baseline_value": 3.41,
          "deviation": "-0.02 eV (within noise)",
          "pass": true,
          "tolerance": "< 0.1 eV from baseline"
        }
      ]
    }
  ],
  "convergence_tests": [
    {
      "parameter": "k_points",
      "values": [4, 8, 12, 16],
      "observed_convergence": "monotonic"
    },
    {
      "parameter": "smearing_sigma",
      "values": [0.01, 0.05, 0.10, 0.20],
      "observed_convergence": "monotonic"
    }
  ],
  "verdict": "pass",
  "ready_for_production": true,
  "related_task_id": "metal-gw-abacus-librpa",
  "topic_slug": "metal-gw",
  "notes": "Metal GW results agree with VASP within tolerance. Insulator regression shows no degradation. k-point convergence is slower for metals as expected."
}
```

### Gate G4 (Benchmarks pass)

- [ ] All primary test systems meet tolerance
- [ ] Regression tests show no degradation
- [ ] Convergence tests show `monotonic` behavior
- [ ] No NaN or unphysical values in any test
- [ ] `benchmark-report` verdict is `pass` or `partial` with documented gaps

If gate fails → **Phase 6: Debug Loop**.

---

## Phase 6: Debug Loop

**Goal**: Diagnose and fix failures from Phase 4 or Phase 5.

**AITP layer**: L4 → L3 feedback loop.

### Steps

1. **Classify the failure** using `calculation-debug.error_classification`:
   - `convergence_failure`: SCF didn't converge, or GW didn't converge
   - `input_mismatch`: parameters inconsistent between stages
   - `resource_exhaustion`: OOM, walltime exceeded
   - `numerical_instability`: NaN, Inf, oscillating energies
   - `basis_incompatibility`: orbital/pseudopotential mismatch
   - `toolchain_error`: compilation or linking failure
   - `unknown`: none of the above
2. **Record the debug session** in a `calculation-debug` contract.
3. **Apply fix** — one fix at a time, test after each.
4. **Verify fix** — re-run the failed test.
5. **Capture learned knowledge** for future reuse.
6. **Return to the failing phase** (Phase 4 or Phase 5).

### Rules

- **Fix root causes**, not symptoms.
- **One fix per iteration** — do not shotgun-debug.
- **After 3 consecutive failures on the same issue**, stop and escalate to
  human.
- **Never delete failing tests** to make them "pass".

### Walkthrough: metal GW

Common metal GW failures:

| Failure | Category | Typical fix |
|---------|----------|-------------|
| NaN in χ₀ eigenvalues | `numerical_instability` | Reduce smearing width, increase k-points |
| Band occupancies all 0 or 1 | `input_mismatch` | Check `smearing_method` in INPUT, verify Fermi level computed correctly |
| LibRPA crashes reading NSCF | `input_mismatch` | ABACUS branch doesn't have occupancy output — wrong branch |
| SCF doesn't converge for Cu | `convergence_failure` | Increase mixing parameter, reduce `scf_nmax` tolerance |
| GW gap for Si changed | `basis_incompatibility` | Smearing code path accidentally triggers for insulators — add guard |

**Example debug contract**:

```json
{
  "debug_id": "debug-metal-gw-nan-001",
  "original_workflow_id": "gw-al-smoke-001",
  "failure_stage": "librpa",
  "error_classification": {
    "category": "numerical_instability",
    "root_cause": "Polarizability χ₀ produced NaN eigenvalues when Fermi-Dirac smearing was applied to a 2×2×2 k-grid. The coarse k-grid causes the Fermi level to sit exactly on a band, producing f_nk ≈ 0.5 with poor Brillouin zone sampling.",
    "error_log_excerpt": "NaN detected in chi0_eigenvectors at k-point 3"
  },
  "fix_actions": [
    {
      "action": "parameter_change",
      "target": "KPT (k-grid)",
      "details": "Increased k-grid from 2×2×2 to 4×4×4 for smoke test"
    }
  ],
  "verification": {
    "re_run_status": "passed",
    "smoke_test_passed": true,
    "deviation_from_expected": "No NaN, χ₀ eigenvalues finite"
  },
  "learned_knowledge": {
    "summary": "Metal GW smoke tests must use at least 4×4×4 k-grids. 2×2×2 is too coarse for Fermi-surface sampling.",
    "applicable_contexts": [
      "All metallic system GW calculations",
      "Smoke tests for metal features"
    ],
    "avoid_patterns": [
      "Using 2×2×2 k-grids for metal smoke tests",
      "Assuming coarse grids are sufficient just because the test is 'minimal'"
    ]
  },
  "topic_slug": "metal-gw"
}
```

### AITP integration

```bash
aitp loop --topic-slug metal-gw \
  --human-request "Debug NaN in LibRPA polarizability for bulk Al at 2x2x2 k-grid."
```

Debug records become L4 artifacts. When the fix succeeds and the result is
validated, the learned knowledge can be promoted to L2 as an experience card.

---

## Phase 7: Production Readiness

**Goal**: Finalize the feature — merge code, update documentation, declare
production readiness.

**AITP layer**: L2 — trusted memory promotion.

### Steps

1. **Update `development-task.status`** to `review`.
2. **Verify all contracts are complete**:
   - `development-task`: all fields filled, status = `review`
   - `computation-workflow`: all benchmark workflows completed
   - `benchmark-report`: verdict = `pass` or `partial`
   - `calculation-debug`: all debug sessions closed with fixes verified
   - `compute-resource`: all used resources documented
3. **Human review gate**:
   - Code review on the PR
   - Physics review: does the benchmark report tell a convincing story?
   - Regression check: no degradation on insulator tests
4. **Merge** — update `development-task.status` to `merged`.
5. **Promote to L2**:
   - Benchmark reference data → reusable knowledge
   - Debug experience cards → reusable experience
   - Build configuration → reusable template
   - Convergence patterns → reusable guidelines

### Gate G5 (Production ready)

- [ ] All `development-task` contracts have status `merged`
- [ ] `benchmark-report` verdict = `pass` (not just `partial`)
- [ ] No open `calculation-debug` sessions with `re_run_status: failed`
- [ ] All protocol invariants (§7) pass on every test system
- [ ] Code merged to target branch (not just feature branch)
- [ ] Human explicitly approves L2 promotion

### Walkthrough: metal GW

**L2 promotion checklist**:

| Artifact | L2 destination | Content |
|----------|---------------|---------|
| Reference data | Benchmark reference | Al GW band structure, Cu GW band structure |
| Convergence data | Reusable guidelines | Metal GW k-point convergence guide |
| Debug experience | Experience cards | "Use ≥4×4×4 for metal smoke tests", "Smearing width must be < 0.10 Ry for converged QP energies" |
| Build config | Reusable template | Intel oneAPI + ELPA + LibXC build for ABACUS metal GW |
| Input templates | Reusable workflows | `librpa.in` template for metals, `INPUT` template for metal NSCF |

### AITP integration

```bash
aitp request-promotion --topic-slug metal-gw --candidate-id metal-gw-feature
# Human reviews and approves:
aitp approve-promotion --topic-slug metal-gw --candidate-id metal-gw-feature
aitp promote --topic-slug metal-gw --candidate-id metal-gw-feature --target-backend-root ./research/knowledge-hub
```

---

## Human Interaction Protocol

Every gate in this playbook is a **structured checkpoint** with the human — not
an open-ended conversation. The agent follows the GSD-style interaction pattern:
concise status → clear options → wait for explicit decision.

### General rules

1. **Never proceed past a gate without explicit human approval.** No implicit
   "seems good, moving on."
2. **Present status, not questions.** At each gate, show what was done, what
   was found, and what the options are. Let the human choose.
3. **Give options, not open questions.** Wrong: "What do you think?" Right:
   "Here are 3 options with tradeoffs. My recommendation is A. Proceed with A
   or choose differently?"
4. **Adaptive questioning.** If the human has already provided context (files,
   constraints, preferences), don't re-ask. Skip what's known.
5. **Be concise.** Status summaries should fit on one screen. Derivation
   reviews use the compiled PDF, not terminal dumps.
6. **Record every decision.** Human decisions at gates are logged in the
   project `README.md` or the relevant contract's `notes` field.

### Gate interaction templates

At each gate, the agent presents a structured summary using this template:

```
## Gate GX: <gate name>

### What was done
- <bullet list of completed work>

### What was found
- <key findings, issues, or decisions made>

### What's next (if approved)
- <what happens in the next phase>

### Options
1. **Approve and continue** — proceed to Phase N
2. **Revise** — <specific revision needed>
3. **Block** — stop work, document reason

### Recommendation
<agent's recommendation with reasoning>

Proceed?
```

### Phase-specific interaction patterns

#### Phase P → Phase 0: Project location

```
## Project Setup

I'll create the project folder. Default location:
  ~/projects/<topic-slug>/

Options:
1. Use default: ~/projects/<topic-slug>/
2. Custom path: <tell me where>

Where should I create the project?
```

The agent does **not** create anything until the human confirms the location.

#### G0: Derivation review

```
## Gate G0: Derivation Review

### What was done
- Collected N references in L0_source/ref/
- Derived working equations in docs/sections/02_derivation.tex
- Compiled to docs/main.pdf

### Key derivation results
- Starting from: <equation reference>
- Assumptions: <list>
- Final formula: Eq. (N) — <brief description>
- Domain of validity: <conditions>

### Implementation mapping
- Eq. (N) → <code location> — <what changes>
- Eq. (M) → <code location> — <what changes>

Please review docs/main.pdf (sections 1-2).

Options:
1. **Approve** — derivation is correct, proceed to planning
2. **Modify** — tell me what to change
3. **Reject** — fundamental issue, go back to literature
```

The agent compiles the LaTeX and presents the PDF path. The human reviews the
PDF, not terminal text. **No code is written until the human picks option 1.**

#### G2: Plan review

```
## Gate G2: Development Plan Review

### What was done
- Located code changes in N files across M repositories
- Created development-task contracts (see contracts/)
- Verified build config on compute resource

### Plan summary
| What | Where | Branch |
|------|-------|--------|
| <change 1> | <repo>:<file> | <branch> |
| <change 2> | <repo>:<file> | <branch> |

### Test strategy
- Unit tests: <list>
- Integration tests: <list>
- Physical correctness: <description>

### Estimated effort
- Implementation: <estimate>
- Testing: <estimate>
- Benchmarking: <estimate>

Options:
1. **Approve plan** — start implementation
2. **Adjust scope** — modify the plan
3. **Add test systems** — suggest additional benchmarks
```

#### G3: Smoke test result

```
## Gate G3: Build & Smoke Test

### Build result
- Status: ✅ clean / ❌ N errors, N warnings
- Platform: <compute-resource>
- Toolchain: <toolchain>

### Smoke test result
| Stage | Status | Time |
|-------|--------|------|
| SCF   | ✅ completed | Xm Xs |
| DF    | ✅ completed | Xm Xs |
| NSCF  | ✅ completed | Xm Xs |
| LibRPA| ✅ completed | Xm Xs |

### Key observations
- <anything notable>

### Invariants
- [x] shrink_consistency
- [x] same_libri
- [x] keyword_compat
- [x] smoke_first
- [x] toolchain_consistency

Options:
1. **Proceed to benchmark campaign** (Phase 5)
2. **Debug first** (Phase 6) — <reason>
```

#### G4: Benchmark results

```
## Gate G4: Benchmark Results

### Summary
| System | Observable | New | Reference | Deviation | Pass? |
|--------|-----------|-----|-----------|-----------|-------|
| <sys1> | <obs1>   | <v> | <ref>     | <dev>     | ✅/❌ |
| <sys2> | <obs2>   | <v> | <ref>     | <dev>     | ✅/❌ |

### Convergence
- k-points: <monotonic/oscillating/non_convergent>
- <other params>: <status>

### Regression
- <insulator test>: <passed/failed> — <details>

### Verdict: <pass/partial/fail>

Options:
1. **Approve** — ready for production (Phase 7)
2. **Run more tests** — specify additional systems/parameters
3. **Debug** — investigate failures (Phase 6)
```

### Debug escalation pattern

When Phase 6 fails repeatedly, escalate to the human:

```
## Debug Escalation: <issue>

### Failed attempts
1. <attempt 1> — <result>
2. <attempt 2> — <result>
3. <attempt 3> — <result>

### Analysis
<root cause hypothesis>

### I'm stuck. Options:
1. **Re-derive** — go back to Phase 1, update derivation with new understanding
2. **Change approach** — <alternative strategy>
3. **Consult literature** — look for <specific topic> in papers
4. **Human take over** — you investigate manually, I'll assist

What would you like to do?
```

---

## Quick Reference: Failure Recovery

| Symptom | Phase | Likely cause | Action |
|---------|-------|-------------|--------|
| Won't compile | 4 | `toolchain_error` | Check dependency versions, cmake flags |
| Unit test fails | 4 | Logic error | Fix the code, re-run |
| SCF diverges | 4 | `convergence_failure` | Adjust mixing, check STRU |
| NaN in LibRPA | 4–5 | `numerical_instability` | Increase k-points, check smearing |
| GW gap wrong | 5 | `input_mismatch` or algorithm bug | Debug loop, compare with VASP step-by-step |
| Insulator regression | 5 | Smearing code path triggered incorrectly | Add insulator/metal guard in code |
| Benchmark doesn't converge | 5 | `convergence_failure` | More k-points, higher ecutwfc |

## Quick Reference: Contract Checklist

Before declaring the feature done, verify every contract:

- [ ] **Project structure**: follows PROJECT_STRUCTURE_CONVENTION.md (L0–L4 dirs, docs/, code/)
- [ ] **LaTeX derivation**: `docs/sections/02_derivation.tex` complete, compiled, human-approved (G0)
- [ ] **`development-task`**: status = `merged`, all fields complete
- [ ] **`computation-workflow`**: ≥1 smoke test + ≥1 production run, all stages `completed`
- [ ] **`benchmark-report`**: verdict = `pass`, convergence = `monotonic`, regression clear
- [ ] **`calculation-debug`**: all debug sessions closed, `re_run_status` = `passed`
- [ ] **`compute-resource`**: all resources used are documented
- [ ] **Protocol invariants**: all 5 pass (shrink_consistency, same_libri, keyword_compat, smoke_first, toolchain_consistency)
- [ ] **Code-equation traceability**: every physics function references its derivation equation

---

This playbook is the authoritative reference for the feature development
lifecycle within the `code_method` lane's ABACUS+LibRPA domain
specialization. It works with — not replaces — the
[FIRST_PRINCIPLES_LANE_PROTOCOL.md](./FIRST_PRINCIPLES_LANE_PROTOCOL.md) and
the five domain contracts under `contracts/`.
