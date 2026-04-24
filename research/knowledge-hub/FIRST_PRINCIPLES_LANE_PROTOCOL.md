# First-Principles Domain Specialization

This document defines the **ABACUS+LibRPA domain specialization** within the
`code_method` lane of AITP. It covers both sub-domains (computation and
development), their interaction loop, routing strategy, invariants, and
validation standards.

This is not an independent lane. It is a domain-specific protocol layer that
sits inside the existing `code_method` lane, following the same L0→L4
layer model and promotion rules. The domain knowledge here was extracted from
the `oh-my-librpa` OpenCode skill and formalized into AITP contracts.

## 1. Domain identity

| Attribute | Value |
|---|---|
| Parent lane | `code_method` |
| Domain | ABACUS + LibRPA first-principles calculations |
| Sub-domains | `computation`, `development` |
| System types | `molecule`, `solid`, `2D` |
| Default route | `L0 → L1 → L3 → L4 → L2` |

## 2. Sub-domains

### 2.1 Computation sub-domain

Physics calculations following well-defined workflows: SCF → density
functional → (optional NSCF) → LibRPA post-processing.

**Typical user entries:**

- "Run a GW calculation on bulk silicon"
- "Calculate RPA correlation energy for H₂O molecule"
- "My LibRPA run crashed with a stod error"
- "Check if my librpa.in is consistent with my INPUT"

### 2.2 Development sub-domain

Software feature implementation, build configuration, and numerical validation
for ABACUS, LibRPA, LibRI, LibComm, pyatb, and related toolchain components.

**Typical user entries:**

- "Add head-wing contribution to LibRPA's GW module"
- "Build ABACUS with Intel oneAPI on the new server"
- "Benchmark the new exchange-correlation functional"
- "Fix the compilation error with ELPA 2024.05.001"

## 3. Sub-domain interaction loop

Development and computation are not independent. New features must be validated
through computation before entering production, and computation failures often
reveal code bugs.

```
feature_development → build_workflow → benchmark_workflow → computation →
    ↓                                                                    ↑
debug_workflow ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

**Rules:**

1. New features **must** pass benchmark validation (`benchmark_workflow`) before
   entering production computation.
2. Physics computation failures **must** be diagnosed through `debug_workflow`
   before retrying.
3. Debug results that reveal code bugs feed back into `feature_development`.

## 4. Operation families

### 4.1 Computation operations

| Family | Description | Typical L0 inputs | Typical L2 outputs |
|---|---|---|---|
| `gw_workflow` | SCF → DF → NSCF → LibRPA GW chain | STRU, INPUT chain, basis assets | Validated quasiparticle bands |
| `rpa_workflow` | SCF → DF → LibRPA RPA chain | Same | Trusted RPA total/correlation energies |
| `debug_workflow` | Failure diagnosis and repair | Failed logs + input files | Fix records + experience knowledge cards |

### 4.2 Development operations

| Family | Description | Typical L0 inputs | Typical L2 outputs |
|---|---|---|---|
| `feature_development` | New feature in ABACUS/LibRPA/LibRI | Algorithm reference + upstream code | Reusable feature module |
| `build_workflow` | Compilation and toolchain setup | CMake config + dependency paths | Reusable build configuration |
| `benchmark_workflow` | Numerical validation of new features | New feature code + benchmark systems | Trusted validation report |

## 5. L0 knowledge classification

| Category | Contents | File patterns |
|---|---|---|
| `structure` | Crystal/molecular geometry | `STRU`, `*.cif`, `*.xyz`, `geometry.in` |
| `input_bundle` | Calculation parameters | `INPUT`, `KPT`, `librpa.in`, `*.upf` |
| `basis_assets` | Numerical basis sets | `*.orb`, `*.abfs`, `*.upf` |
| `symmetry_sidecars` | Symmetry reduction data | `symrot_*.txt`, `irreducible_sector.txt` |
| `workflow_scripts` | Automation scripts | `get_diel.py`, `perform.sh`, `env.sh` |
| `logs_results` | Output data | `OUT.ABACUS/`, `LibRPA*.out`, `band_out` |
| `source_code` | Source directories, diffs | `src/`, `*.diff`, `*.patch` |
| `build_config` | Build system files | `CMakeLists.txt`, `*.cmake`, `toolchain.*` |
| `algorithm_reference` | Papers, derivations | `*.pdf`, `*.tex`, `*.bib` |
| `benchmark_reference` | Known reference values | `ref_*.dat`, `benchmark_*.json` |

## 6. Routing strategy

The domain routes requests through three mechanisms:

### 6.1 Intent routing

| User intent pattern | Sub-domain | Operation family |
|---|---|---|
| "Run/Calculate/Compute/Perform" | computation | `gw_workflow` or `rpa_workflow` |
| "Debug/Fix/Why did" | computation | `debug_workflow` |
| "Add/Implement/Develop" | development | `feature_development` |
| "Build/Compile/Install" | development | `build_workflow` |
| "Benchmark/Validate/Test" | development | `benchmark_workflow` |

### 6.2 Input-based routing

When intent is ambiguous, inspect the provided files:

| Provided input | Sub-domain |
|---|---|
| STRU + INPUT only | computation |
| librpa.in + INPUT | computation (consistency check) |
| Source code diff or PR | development |
| CMakeLists or build logs | development |
| Error log + INPUT | computation → `debug_workflow` |

### 6.3 Mode routing

| Mode | Behavior |
|---|---|
| `protocol_check` | Validate inputs without executing. Return consistency report. |
| `prepare` | Generate all input files for a workflow. No execution. |
| `execute` | Full execution: prepare, run, validate. Requires compute resource. |
| `audit` | Review completed workflow. Check reproducibility and correctness. |

## 7. Invariants

These invariants are checked at L4 validation for every computation workflow:

### 7.1 `shrink_consistency`

ABFS_ORBITAL files must be present in the run directory if and only if
`use_shrink_abfs` is set to `true` in `librpa.in`. A mismatch causes an
immediate L4 failure.

### 7.2 `same_libri`

`abacus_work` and `librpa_work` must be compiled against the same LibRI version.
The protocol checks `LibRI_VERSION` in both build logs.

### 7.3 `keyword_compat`

Deprecated ABACUS keywords (e.g., old naming conventions that changed across
versions) must not appear in INPUT files. The protocol maintains a deprecated
keyword list per ABACUS version.

### 7.4 `smoke_first`

Before any expensive computation (GW/RPA), a minimal smoke test must pass:
SCF converges within `ecutwfc` cutoff on a 1×1×1 k-grid. This catches
misconfigurations early.

### 7.5 `toolchain_consistency`

The build toolchain (compiler, MPI, BLAS/LAPACK) used at compile time must
match the runtime environment. Checked via module list and `ldd` on the
executables.

## 8. Contract index

| Contract | Schema | Purpose |
|---|---|---|
| `computation-workflow` | `schemas/computation-workflow.schema.json` | Full computation workflow definition |
| `compute-resource` | `schemas/compute-resource.schema.json` | Compute resource specification |
| `development-task` | `schemas/development-task.schema.json` | Software development task tracking |
| `benchmark-report` | `schemas/benchmark-report.schema.json` | Benchmark results and verdict |
| `calculation-debug` | `schemas/calculation-debug.schema.json` | Failure diagnosis and fix record |

All contracts live under `contracts/` with matching JSON schemas under
`schemas/`.

### Supporting documents

| Document | Purpose |
|---|---|
| [PROJECT_STRUCTURE_CONVENTION.md](./PROJECT_STRUCTURE_CONVENTION.md) | Mandatory folder layout, LaTeX documentation, derive-first workflow |
| [FEATURE_DEVELOPMENT_PLAYBOOK.md](./FEATURE_DEVELOPMENT_PLAYBOOK.md) | Phase-by-phase feature development process |

## 9. Layer mapping

### 9.0 Project structure

Every feature project must follow the directory structure defined in
[PROJECT_STRUCTURE_CONVENTION.md](./PROJECT_STRUCTURE_CONVENTION.md). Layers
map to concrete filesystem directories within the project folder:

| AITP layer | Directory | Purpose |
|---|---|---|
| L0 | `L0_source/` (with `ref/` for papers) | Source acquisition |
| L1 | `L1_intake/` | Provisional understanding |
| L3 | `L3_exploratory/` | Exploratory outputs |
| L4 | `L4_validation/` | Validation and trust audit |
| L2 | `L2_canonical/` | Trusted memory |
| — | `docs/` (LaTeX) | Derivations, implementation mapping, results |
| — | `code/` | Source code changes |
| — | `computation/` | Computation outputs |
| — | `contracts/` | AITP contract instances |

### 9.1 Computation sub-domain

| Layer | Phase | Artifacts |
|---|---|---|
| **L0** | Source acquisition | STRU, INPUT, KPT, basis files, reference papers |
| **L1** | Provisional understanding | Input consistency report, workflow plan |
| **L3** | Exploratory outputs | SCF results, DF results, intermediate energies |
| **L4** | Validation | Convergence check, invariant verification, energy comparison |
| **L2** | Trusted memory | Validated quasiparticle bands, RPA energies, debug experience cards |

### 9.2 Development sub-domain

| Layer | Phase | Artifacts |
|---|---|---|
| **L0** | Source acquisition | Algorithm reference, upstream code, existing test cases, papers in `L0_source/ref/` |
| **L1** | Provisional understanding | LaTeX derivation (`docs/sections/02_derivation.tex`), implementation plan, code location analysis |
| **L3** | Exploratory outputs | Feature branch code (with equation references), build output, initial test results |
| **L4** | Validation | Benchmark report, regression check, code review, derivation-code traceability |
| **L2** | Trusted memory | Merged feature, approved derivation PDF, reusable build config, benchmark reference data |

## 10. Relationship to oh-my-librpa

This document formalizes the knowledge from the `oh-my-librpa` OpenCode skill
into AITP protocol contracts under the `code_method` lane. The mapping:

| oh-my-librpa concept | AITP artifact |
|---|---|
| System type classification (molecule/solid/2D) | `computation-workflow.system_type` |
| Input file consistency checks | `computation-workflow.basis_integrity` + invariants |
| Remote vs local execution routing | `computation-workflow.compute` + `compute-resource` |
| Workflow chaining (SCF→DF→NSCF→LibRPA) | `computation-workflow.stages` |
| Debugging expertise (stod errors, convergence) | `calculation-debug.error_classification` |
| Build configuration knowledge | `development-task.build_config` |
| Smoke test before expensive runs | `smoke_first` invariant |
| Server-specific toolchain paths | `compute-resource` contract |

## 11. Validation standards

### 11.1 Computation-side L4 gate

A computation workflow passes L4 validation when:

1. **All stages completed** — every stage in `stages` has status `completed`.
2. **Basis integrity confirmed** — `basis_integrity` passes all checks.
3. **All invariants satisfied** — the five invariants (§7) all pass.
4. **Convergence acceptable** — energy changes are within tolerance for the
   last two iterations.
5. **Smoke test passed** — a minimal test ran before the full calculation.

### 11.2 Development-side L4 gate

A development task passes L4 validation when:

1. **Build succeeds** — clean compilation with zero errors and zero warnings
   (warnings allowed only if documented as known and acceptable).
2. **Unit tests pass** — all existing and new unit tests pass.
3. **Physical correctness verified** — the feature produces physically
   meaningful results on at least one test system.
4. **Benchmark report approved** — `benchmark-report` contract with
   `verdict: pass` or `verdict: partial` with documented remaining gaps.
5. **No regression** — existing test systems show no unexpected deviation
   from baseline values.

## 12. SOC and symmetry constraints

### 12.1 Spin-orbit coupling (SOC)

When SOC is enabled (`calculation: nscf` with `soc: 1` in INPUT):

- The NSCF stage must use the same number of bands as the DF stage.
- LibRPA must receive SOC-aware wavefunctions.
- The `basis_integrity` check must verify that pseudopotentials include
  relativistic versions (e.g., `*_ONCV_PBE-1.2.upf` vs `*_ONCV_PBE-1.2.rel.upf`).

### 12.2 Symmetry reduction

When symmetry sidecar files are present:

- `symrot_*.txt` rotation matrices must be consistent with the lattice vectors
  in STRU.
- `irreducible_sector.txt` k-point counts must match the KPT file.
- Symmetry-reduced calculations must reproduce full-grid results within
   numerical tolerance before L2 promotion.

## 13. Rules for future changes

1. **New operation families** require a matching contract schema and an update
   to this protocol document.
2. **New invariants** must be added with a clear failure mode and a description
   of how to check them at L4.
3. **New system types** (e.g., `nanotube`, `surface`) require updating the
   `system_type` enum in all affected schemas simultaneously.
4. **Breaking schema changes** must increment a `schema_version` field. Old
   versions must remain parseable.
5. **Protocol changes** must be reflected in this document and in the
   corresponding contract and schema files.

---

This document is the authoritative reference for the ABACUS+LibRPA domain
specialization within the `code_method` lane. When in doubt, this
document takes precedence over individual contract files or schema comments.
