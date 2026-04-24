# Benchmark Report Contract

**Frontmatter schema**: [`benchmark-report.schema.json`](../schemas/benchmark-report.schema.json)

## Purpose

Record the validation results of a new feature against known benchmark
systems, including convergence tests and pass/fail verdict.

## Required fields

| Field | Type | Values / Notes |
|-------|------|----------------|
| `report_id` | string | Unique identifier (minLength 1) |
| `feature` | string | Name of the feature being benchmarked (minLength 1) |
| `target_version` | string | Version or commit of the new code (minLength 1) |
| `baseline_version` | string | Version or commit of the reference code (minLength 1) |
| `test_systems` | array | List of test system objects (minItems 1) |
| `verdict` | enum | `pass`, `partial`, `fail`, or `blocked` |
| `ready_for_production` | boolean | Whether the feature is safe for production use |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `convergence_tests` | array | Convergence parameter sweep results |
| `topic_slug` | string | Links to an AITP research topic |
| `related_task_id` | string | `task_id` of the development task being benchmarked |
| `notes` | string | Free-form notes |

## Test systems

Each test system object contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (required) | Test system name (e.g. `"bulk Si"`) |
| `system_type` | enum (required) | `molecule`, `solid`, or `2D` |
| `results` | array (required) | List of result objects (minItems 1) |

### Results

Each result object within a test system:

| Field | Type | Description |
|-------|------|-------------|
| `observable` | string (required) | Physical quantity being measured |
| `new_value` | number (required) | Value from the new code |
| `baseline_value` | number (required) | Value from the reference code |
| `deviation` | string (required) | Human-readable deviation description |
| `pass` | boolean (required) | Whether this result meets tolerance |
| `tolerance` | string | Acceptance tolerance (e.g. `"< 0.1 eV"`) |

## Convergence tests

Each convergence test object:

| Field | Type | Description |
|-------|------|-------------|
| `parameter` | string (required) | Parameter being varied (e.g. `k_points`, `ecutwfc`) |
| `values` | number[] (required) | Tested parameter values |
| `observed_convergence` | enum | `monotonic`, `oscillating`, `non_convergent`, or `insufficient_data` |

## Example

```json
{
  "report_id": "bench-head-wing-silicon",
  "feature": "GW head-wing contribution",
  "target_version": "librpa:enable_head_wing@a3f7c21",
  "baseline_version": "librpa:v0.4.0",
  "test_systems": [
    {
      "name": "bulk Si (diamond)",
      "system_type": "solid",
      "results": [
        {
          "observable": "GW direct gap at Γ (eV)",
          "new_value": 3.41,
          "baseline_value": 3.28,
          "deviation": "+0.13 eV (head-wing correction)",
          "pass": true,
          "tolerance": "within 0.1 eV of VASP reference (3.40 eV)"
        },
        {
          "observable": "GW indirect gap Γ→X (eV)",
          "new_value": 1.24,
          "baseline_value": 1.15,
          "deviation": "+0.09 eV",
          "pass": true,
          "tolerance": "within 0.1 eV of reference (1.25 eV)"
        }
      ]
    },
    {
      "name": "N₂ molecule",
      "system_type": "molecule",
      "results": [
        {
          "observable": "HOMO energy (eV)",
          "new_value": -15.62,
          "baseline_value": -15.58,
          "deviation": "-0.04 eV",
          "pass": true,
          "tolerance": "< 0.1 eV"
        }
      ]
    }
  ],
  "convergence_tests": [
    {
      "parameter": "abfs_radius",
      "values": [6.0, 8.0, 10.0, 12.0],
      "observed_convergence": "monotonic"
    },
    {
      "parameter": "k_points",
      "values": [4, 6, 8, 12],
      "observed_convergence": "monotonic"
    }
  ],
  "verdict": "pass",
  "ready_for_production": true,
  "related_task_id": "librpa-head-wing",
  "topic_slug": "gw-head-wing-convergence",
  "notes": "Head-wing correction significantly improves agreement with VASP reference for solids. Molecular results are essentially unchanged."
}
```

## Why it matters

A new feature in a physics code is not trustworthy just because it compiles.
Benchmark reports provide the evidence chain from implementation to validated
physical correctness.
