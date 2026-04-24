# Calculation Debug Contract

**Frontmatter schema**: [`calculation-debug.schema.json`](../schemas/calculation-debug.schema.json)

## Purpose

Record the diagnosis and fix of a failed first-principles computation,
capturing error classification, root cause, and learned knowledge for future
reuse.

## Required fields

| Field | Type | Values / Notes |
|-------|------|----------------|
| `debug_id` | string | Unique identifier (minLength 1) |
| `original_workflow_id` | string | `workflow_id` of the failed computation (minLength 1) |
| `failure_stage` | enum | `scf`, `df`, `nscf`, `librpa`, or `postprocess` |
| `error_classification` | object | Category and root cause of the error |
| `fix_actions` | array | List of corrective actions taken (minItems 1) |
| `verification` | object | Re-run status and smoke test results |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `learned_knowledge` | object | Structured experience for future reuse |
| `topic_slug` | string | Links to an AITP research topic |
| `notes` | string | Free-form notes |

## Error classification

| Field | Type | Description |
|-------|------|-------------|
| `category` | enum (required) | `convergence_failure`, `input_mismatch`, `resource_exhaustion`, `numerical_instability`, `basis_incompatibility`, `toolchain_error`, or `unknown` |
| `root_cause` | string (required) | Human-readable root cause explanation |
| `error_log_excerpt` | string | Relevant excerpt from the error log |

## Fix actions

Each fix action object:

| Field | Type | Description |
|-------|------|-------------|
| `action` | enum (required) | `parameter_change`, `input_correction`, `resource_adjustment`, `code_patch`, or `workflow_restart` |
| `target` | string (required) | What was changed (file, parameter, resource) |
| `details` | string (required) | Description of the change |

## Verification

| Field | Type | Description |
|-------|------|-------------|
| `re_run_status` | enum (required) | `passed`, `failed`, or `not_yet_run` |
| `smoke_test_passed` | boolean | Whether a quick sanity check passed |
| `deviation_from_expected` | string | Residual deviation after fix |

## Learned knowledge

| Field | Type | Description |
|-------|------|-------------|
| `summary` | string | Concise lesson learned |
| `applicable_contexts` | string[] | Scenarios where this knowledge applies |
| `avoid_patterns` | string[] | Patterns to avoid in the future |

## Example

```json
{
  "debug_id": "debug-stod-librpa-001",
  "original_workflow_id": "gw-si-bulk-001",
  "failure_stage": "librpa",
  "error_classification": {
    "category": "input_mismatch",
    "root_cause": "librpa.in specifies nspin=2 but ABACUS SCF was run with nspin=1. The spin configuration mismatch causes a stod (string-to-double) parse error when LibRPA reads the density matrix.",
    "error_log_excerpt": "Error: stod: cannot convert '********' to double. At line 47 of source/module_io/read_rho.cpp"
  },
  "fix_actions": [
    {
      "action": "input_correction",
      "target": "librpa.in",
      "details": "Changed nspin from 2 to 1 to match the ABACUS SCF output"
    },
    {
      "action": "workflow_restart",
      "target": "librpa stage",
      "details": "Restarted LibRPA from the df stage output with corrected input"
    }
  ],
  "verification": {
    "re_run_status": "passed",
    "smoke_test_passed": true,
    "deviation_from_expected": "GW gap now within 0.05 eV of reference"
  },
  "learned_knowledge": {
    "summary": "LibRPA nspin must match ABACUS SCF nspin. Mismatched spin config causes cryptic stod errors.",
    "applicable_contexts": [
      "All GW/RPA workflows where LibRPA reads ABACUS outputs",
      "Spin-polarized vs non-spin-polarized calculations"
    ],
    "avoid_patterns": [
      "Copying librpa.in templates without verifying nspin against SCF input",
      "Assuming default nspin values across different tools"
    ]
  },
  "topic_slug": "gw-head-wing-convergence",
  "notes": "This is a common pitfall when switching between spin-polarized and non-spin-polarized systems. Added to the oh-my-librpa pre-flight checklist."
}
```

## Why it matters

Debug knowledge is the most frequently lost asset in computational physics.
Recording error patterns and fixes creates reusable experience that accelerates
future debugging and prevents repeated mistakes.
