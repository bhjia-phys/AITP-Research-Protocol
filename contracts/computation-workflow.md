# Computation Workflow Contract

**Frontmatter schema**: [`computation-workflow.schema.json`](../schemas/computation-workflow.schema.json)

## Purpose

Define the stages, status, and invariants of a first-principles computation
chain (GW or RPA) from structure input through LibRPA output.

## Required fields

| Field | Type | Values / Notes |
|-------|------|----------------|
| `workflow_id` | string | Unique identifier (minLength 1) |
| `computation_type` | enum | `gw` or `rpa` |
| `system_type` | enum | `molecule`, `solid`, or `2D` |
| `structure_file` | string | Path to structure input (minLength 1) |
| `stages` | array | Ordered list of stage objects (minItems 1) |
| `basis_integrity` | object | Pseudopotential, NAO, and ABFS orbital file lists |
| `compute` | object | Execution location and parallelism settings |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `topic_slug` | string | Links to an AITP research topic |
| `notes` | string | Free-form notes |

## Stages

Each stage object contains:

| Field | Type | Values / Notes |
|-------|------|----------------|
| `name` | enum (required) | `scf`, `df`, `nscf`, `librpa`, or `postprocess` |
| `status` | enum (required) | `pending`, `running`, `completed`, `failed`, or `skipped` |
| `input_files` | string[] (required) | Paths consumed by this stage |
| `output_artifacts` | string[] (required) | Paths produced by this stage |
| `depends_on` | string[] | Upstream stage names |
| `validation` | string | Validation description or criterion |

### Stage-specific validations

- **scf**: convergence_reached, energy_change_below_threshold
- **df**: coulomb_matrices_exist, shrink_consistency
- **nscf** (GW only): band_structure_readable
- **librpa**: gw_band_output_exists (GW) or rpa_converged (RPA)
- **postprocess**: pyatb_transport_output or custom post-processing validation

## Basis integrity

| Field | Type | Description |
|-------|------|-------------|
| `pseudopotentials` | string[] (required) | UPF/psp8 file paths |
| `nao_orbitals` | string[] (required) | Numerical atomic orbital file paths |
| `abfs_orbitals` | string[] | Auxiliary basis function file paths |
| `shrink_invariant` | boolean | True if ABFS_ORBITAL presence matches `use_shrink_abfs` in `librpa.in` |

## Compute

| Field | Type | Description |
|-------|------|-------------|
| `location` | enum (required) | `local` or `server` |
| `server_alias` | string | Human-readable server alias matching SSH config |
| `host` | string | Server hostname or IP |
| `mpi_np` | integer (min 1) | Number of MPI processes |
| `cpus_per_task` | integer (min 1) | CPUs per MPI task |
| `omp_num_threads` | integer (min 1) | OpenMP threads per process |

## Example

```json
{
  "workflow_id": "gw-si-bulk-001",
  "computation_type": "gw",
  "system_type": "solid",
  "structure_file": "Si.cif",
  "stages": [
    {
      "name": "scf",
      "status": "completed",
      "input_files": ["STRU", "KPT", "INPUT_scf"],
      "output_artifacts": ["OUT.ABACUS/running_scf.log", "OUT.ABACUS/charge_density"],
      "depends_on": [],
      "validation": "convergence_reached and energy_change < 1e-6 eV"
    },
    {
      "name": "df",
      "status": "completed",
      "input_files": ["INPUT_df"],
      "output_artifacts": ["OUT.ABACUS/Coulomb_Matrices"],
      "depends_on": ["scf"],
      "validation": "coulomb_matrices_exist and shrink_consistency"
    },
    {
      "name": "nscf",
      "status": "completed",
      "input_files": ["INPUT_nscf", "KPT_nscf"],
      "output_artifacts": ["OUT.ABACUS/running_nscf.log", "OUT.ABACUS/BANDS.dat"],
      "depends_on": ["scf"],
      "validation": "band_structure_readable"
    },
    {
      "name": "librpa",
      "status": "running",
      "input_files": ["librpa.in"],
      "output_artifacts": ["gw_band.dat"],
      "depends_on": ["df", "nscf"],
      "validation": "gw_band_output_exists"
    },
    {
      "name": "postprocess",
      "status": "pending",
      "input_files": ["gw_band.dat"],
      "output_artifacts": ["band_structure_comparison.png"],
      "depends_on": ["librpa"],
      "validation": "pyatb_transport_output"
    }
  ],
  "basis_integrity": {
    "pseudopotentials": ["Si.upf"],
    "nao_orbitals": ["Si_gga_8au_100Ry_2s2p1d.orb"],
    "abfs_orbitals": ["Si_gga_8au_100Ry_2s2p1d.abfs", "Si_gga_abfs_shrink.abfs"],
    "shrink_invariant": true
  },
  "compute": {
    "location": "server",
    "server_alias": "df",
    "host": "df.iopcas.cn",
    "mpi_np": 64,
    "cpus_per_task": 4,
    "omp_num_threads": 4
  },
  "topic_slug": "gw-bulk-silicon",
  "notes": "GW band structure of bulk silicon with HSE06 starting point"
}
```

## Why it matters

GW/RPA computations involve chained dependent stages where each stage's output
feeds the next. Without explicit stage tracking, failures propagate silently
and diagnosis becomes guesswork.
