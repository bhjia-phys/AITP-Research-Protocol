# Compute Resource Contract

**Frontmatter schema**: [`compute-resource.schema.json`](../schemas/compute-resource.schema.json)

## Purpose

Declare where and how a computation runs — local machine or remote server with
specific module, MPI, and Slurm configurations.

## Required fields

| Field | Type | Values / Notes |
|-------|------|----------------|
| `resource_id` | string | Unique identifier (minLength 1) |
| `location` | enum | `local` or `server` |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `alias` | string | Human-readable alias matching SSH config |
| `host` | string | Server hostname or IP |
| `description` | string | Free-form description of the resource |
| `environment` | enum | `production`, `staging`, `test`, or `development` |
| `modules` | string[] | Environment modules to load (e.g. `oneapi`, `intelmpi`) |
| `abacus_path` | string | Path to ABACUS executable |
| `librpa_path` | string | Path to LibRPA executable or library |
| `libri_path` | string | Path to LibRI (must be same version as linked by ABACUS and LibRPA) |
| `slurm_defaults` | object | Default Slurm resource settings |
| `conda_env` | string | Default conda environment for pyatb and other Python tools |
| `scratch_dir` | string | Fast storage path for I/O-heavy calculations |

## Slurm defaults

| Field | Type | Description |
|-------|------|-------------|
| `partition` | string | Default Slurm partition |
| `cpus_per_task` | integer (min 1) | Default CPUs per MPI task |
| `omp_num_threads` | integer (min 1) | Default OpenMP threads per process |
| `mem_per_cpu` | string | Memory per CPU (e.g. `"4G"`) |
| `time_limit` | string | Wall time limit (e.g. `"24:00:00"`) |

## Server constraints

Server constraints that must be declared:

- `batch_no_bashrc`: Slurm batch must not use `source ~/.bashrc` as entrypoint
- `full_node_threads`: Default `cpus_per_task` to full node core count for 1 MPI
  rank/node
- `explicit_modules`: Prefer explicit `module load` over shell profile injection

## Example — local workstation

```json
{
  "resource_id": "local-applesilicon",
  "location": "local",
  "description": "MacBook Pro M3 Max, used for light testing only",
  "environment": "development",
  "abacus_path": "/usr/local/bin/ABACUS.mpi",
  "librpa_path": "/usr/local/lib/librpa.so",
  "scratch_dir": "/tmp/abacus-scratch"
}
```

## Example — remote server

```json
{
  "resource_id": "df-iopcas",
  "location": "server",
  "alias": "df",
  "host": "df.iopcas.cn",
  "description": "Production cluster with Intel oneAPI and Infiniband",
  "environment": "production",
  "modules": ["oneapi/2024.2", "intelmpi/2021.13"],
  "abacus_path": "/data/home/df_iopcas_ghj/abacus/build/ABACUS.mpi",
  "librpa_path": "/data/home/df_iopcas_ghj/librpa/build/librpa.so",
  "libri_path": "/data/home/df_iopcas_ghj/libri/build/libri.so",
  "slurm_defaults": {
    "partition": "cpu",
    "cpus_per_task": 4,
    "omp_num_threads": 4,
    "mem_per_cpu": "4G",
    "time_limit": "72:00:00"
  },
  "conda_env": "base",
  "scratch_dir": "/work/ssd/work/df_iopcas_ghj"
}
```

## Why it matters

Server environment differences are the single largest source of silent failures
in computational physics. Explicit resource declarations prevent profile
injection issues, conda path conflicts, and mismatched toolchains.
