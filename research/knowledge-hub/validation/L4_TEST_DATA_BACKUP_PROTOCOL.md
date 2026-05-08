# L4 Test Data Backup Protocol

Status: draft
Domain: L4 execution plane
Scope: All L4 validation runs that produce numerical, symbolic, or formal test data

## Overview

When AITP L4 runs validation tests (benchmarks, numerical checks, formal
verifications, symbolic cross-checks), the produced data must be backed up
in a curated, reproducible form. Raw compute directories are not backups.

This protocol defines what to keep, what to discard, and how to package L4
test results for long-term storage, paper reproducibility, and audit.

The goal is NOT "keep everything." The goal IS "keep files that carry
reproducible or interpretive value."

## When to Apply

Apply this protocol:

- After any L4 validation run that produces numerical benchmark data
- After completing a formal verification lane that generates proof artifacts
- After symbolic cross-checks that produce verification evidence
- Before archiving a topic or promoting results to L2
- When packaging results for a paper figure, Overleaf project, or reproducibility bundle

Do NOT apply to:
- Live-running jobs
- Incomplete or in-progress validation tasks
- Source code repositories (handled separately)
- Raw exploration that never entered L4

## Core Principle

For each L4 test run, preserve four classes only:

1. **Test definition** — what was tested and why
2. **Key inputs** — the minimal set needed to reproduce the test
3. **Final outputs** — the results that carry scientific meaning
4. **Provenance record** — how and when the result was produced

Everything else is removable by default unless explicitly preserved.

## L4 Test Data Classes

### Class 1: Test Definition (Always Keep)

These define what the test is and what it means:

- `validation_plan.md` — what is being validated and how
- `validation_contract.md` — mandatory checks, pass/fail criteria
- `execution-tasks/<task_id>.json` — task definition, inputs, expected outputs
- `promotion_decisions.jsonl` — the final adjudication record

### Class 2: Key Inputs (Keep When Present)

Minimal inputs needed to reproduce the test:

- `INPUT` / `STRU` / `KPT` — ABACUS input files
- `librpa.in` — LibRPA input
- `run_*.sh` — execution scripts
- Active pseudopotential and basis files: `.upf`, `.orb`, `.abfs`
- `band_kpath_info` — k-point path definition
- `convention_snapshot.md` — units, sign conventions, notation

For formal theory lane:
- `*_statement.lean` — Lean theorem statements
- `*_proof.lean` — Lean proof scripts

For symbolic lane:
- `*_verify.py` — SymPy verification scripts
- `known_result_reference.json` — reference values for comparison

### Class 3: Final Outputs (Keep Meaningful Results)

Numerical lane:
- `GW_band_spin_*.dat` — final GW band structures
- `KS_band_spin_*.dat` — KS/PBE reference bands
- `EXX_band_spin_*.dat` — EXX bands (if computed)
- `band_gap_data.csv` — compiled gap data
- `convergence_check.csv` — convergence test results
- `benchmark_comparison.csv` — comparison against known benchmarks

Formal lane:
- `proof_check_result.json` — Lean proof check output
- `verification_evidence.json` — formal verification evidence

Symbolic lane:
- `dimension_check_result.json` — dimensional analysis output
- `algebra_verify_result.json` — algebraic verification output
- `limit_check_result.json` — limiting case verification

### Class 4: Key Logs (Keep Main Stage Only)

- `abacus*.out` — ABACUS main output
- `LibRPA*.out` — LibRPA main output (not MPI fragments)
- `slurm*.out` — Slurm job output
- `validation.log` — L4 validation execution log

## Delete Rules

### Always Delete

- `.DS_Store`, `._*`, `__pycache__`
- `running.log`, `running_scf.log`, `running_nscf.log`
- `warning.log` (unless it contains unique diagnostic information)
- `INFO.txt`
- `LibRPA.done`, `SYNC_FROM_PARALLEL`
- `jobid.txt`, `*jobid*.txt`
- Plotting `.log` files
- `*.bak`, `*.tmp`

### Delete These Directory Classes

- `*_parallel/` — parallel scratch directories
- `Out/` — ABACUS scratch output
- `OUT.ABACUS/` — ABACUS formatted output directory
- `pyatb_librpa_df/` — PYATB intermediate files

### Delete Numeric Shards (Unless Referenced by a Kept Table)

- `band_KS_eigenvalue_k_*`
- `band_KS_eigenvector_k_*`
- `band_vxc_k_*`
- `KS_eigenvector_*`
- `librpa_para_nprocs_*`
- `local_*_freq_points.dat`
- `local_*_time_points.dat`
- `*_freq2time_grid_*.txt`
- `*_time2freq_grid_*.txt`

Important exception: Do NOT delete final GW/KS/EXX band data files even
though they are numeric text files. They are the primary scientific output.

## Figure and Plot Rules

If the L4 test produces figures:

1. Keep only figures referenced by the paper or explicitly tagged as final
2. Keep the plotting script that generates each kept figure
3. Delete exploratory plots, trial figures, alternate fit windows
4. If a figure is kept, its generating script must be kept alongside it

## Semantic Naming for Backup Bundles

When packaging L4 test data for backup:

- Prefer readable directory names: `qho_benchmark/`, `si_band_gap_g0w0/`
- Include the run ID: `qho_benchmark__run-2026-04-20-a/`
- For shared inputs (same pseudopotentials, same structure), de-duplicate
  into a `shared_inputs/` directory

## External `input_dir` Rule

If a kept `librpa.in` contains `input_dir = ...` pointing outside the
current run directory, back up that referenced directory too:

- Store once under `shared_input_<basename>/`
- De-duplicate by resolved absolute path
- Apply producer-side keep rules, not raw mirror

## Backup Directory Layout

```
backups/l4/
├── <topic_slug>/
│   ├── <run_id>/
│   │   ├── README.md              # Human-readable description
│   │   ├── manifest.json           # Machine-readable inventory
│   │   ├── validation_contract.md  # Class 1
│   │   ├── execution-tasks/        # Class 1
│   │   ├── inputs/                 # Class 2
│   │   ├── outputs/                # Class 3
│   │   ├── logs/                   # Class 4
│   │   └── figures/                # Kept figures + scripts
│   └── shared_inputs/              # De-duplicated shared inputs
```

## `manifest.json` Format

Every backup bundle must include a manifest:

```json
{
  "backup_version": "1.0",
  "topic_slug": "qho-benchmark",
  "run_id": "run-2026-04-20-a",
  "backup_date": "2026-04-20T15:00:00Z",
  "l4_outcome": "pass",
  "lane": "toy_numeric",
  "contents": {
    "validation_plan": "validation_contract.md",
    "execution_tasks": ["execution-tasks/benchmark.json"],
    "inputs": ["inputs/INPUT", "inputs/STRU", "inputs/KPT", "inputs/librpa.in"],
    "outputs": ["outputs/GW_band_spin_1.dat", "outputs/band_gap_data.csv"],
    "figures": ["figures/gap_comparison.pdf"],
    "plot_scripts": ["figures/plot_gap.py"],
    "logs": ["logs/slurm-47281.out"]
  },
  "removed_classes": [
    "OUT.ABACUS/", "running.log", "band_KS_eigenvalue_k_*",
    "librpa_para_nprocs_*"
  ],
  "original_size_mb": 2450,
  "backup_size_mb": 12
}
```

## Workflow

1. Wait for L4 validation run to complete (outcome recorded)
2. Verify the run produced all expected output artifacts
3. Apply Class 1 (Test Definition): copy all validation plans, contracts, tasks
4. Apply Class 2 (Key Inputs): copy only the minimal reproducible inputs
5. Apply Class 3 (Final Outputs): copy meaningful final results
6. Apply Class 4 (Key Logs): copy main-stage logs only
7. Apply Delete Rules: remove junk, shards, scratch, parallel leftovers
8. Resolve external `input_dir` references: copy and de-duplicate
9. Prune empty directories
10. Generate `manifest.json`
11. Report: what was kept, what was removed, final size

## Reporting Template

When finishing a backup, report:

```
L4 Backup Summary
=================
Topic:       <topic_slug>
Run:         <run_id>
Outcome:     <pass|partial_pass|fail|contradiction|stuck|timeout>
Lane:        <lane>

Kept:
  - Validation plan: <count> files
  - Execution tasks: <count> files
  - Inputs:          <count> files
  - Outputs:         <count> files
  - Figures:         <count> files + <count> scripts
  - Logs:            <count> files

Removed:
  - <class 1>: <count> files
  - <class 2>: <count> files

Size: <original> → <backup> (<reduction>%)
```

## Common Mistakes

1. Keeping every file under a file-size threshold
2. Keeping all figures instead of only paper-used figures
3. Deleting `LibRPA*.out` because "it's just a log"
4. Deleting final band data because "it looks numeric"
5. Preserving `*_parallel` directories when canonical results exist
6. Treating runtime noise logs as scientific outputs
7. Backing up before the L4 outcome is recorded (incomplete runs)
8. Forgetting to resolve external `input_dir` references

## Relationship to ghj-compute-backup-curation

This protocol is the L4-specific subset of the general `ghj-compute-backup-curation`
skill. When an L4 test involves ABACUS/LibRPA computation:

1. Apply the general backup skill for the compute directory curation
2. Then apply this protocol for the L4-specific artifacts (validation plans,
   contracts, execution tasks, promotion decisions)
3. Merge both into a single backup bundle under `backups/l4/<topic_slug>/<run_id>/`
