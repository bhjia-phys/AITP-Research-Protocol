# Development Task Contract

**Frontmatter schema**: [`development-task.schema.json`](../schemas/development-task.schema.json)

## Purpose

Define a feature development task for ABACUS, LibRPA, LibRI, LibComm, pyatb,
or related first-principles toolchain components, including code location,
build configuration, and validation criteria.

## Required fields

| Field | Type | Values / Notes |
|-------|------|----------------|
| `task_id` | string | Unique identifier (minLength 1) |
| `target` | enum | `abacus`, `librpa`, `libri`, `libcomm`, `pyatb`, or `other` |
| `feature_description` | string | What the feature does (minLength 1) |
| `motivation` | string | Why this feature is needed (minLength 1) |
| `code_location` | object | Repository, branch, and key files |
| `build_config` | object | CMake profile, toolchain, and dependency paths |
| `validation` | object | Test suite and physical correctness criteria |

## Optional fields

| Field | Type | Description |
|-------|------|-------------|
| `topic_slug` | string | Links to an AITP research topic |
| `status` | enum | `planned`, `in_progress`, `review`, `merged`, or `blocked` |
| `related_computation` | string | `workflow_id` of a computation that motivated or will validate this feature |
| `notes` | string | Free-form notes |

## Code location

| Field | Type | Description |
|-------|------|-------------|
| `repo` | string (required) | Repository URL or path |
| `branch` | string (required) | Target branch name |
| `key_files` | string[] | Files most likely to change |
| `depends_on` | string[] | Names of other components this change depends on |

## Build configuration

| Field | Type | Description |
|-------|------|-------------|
| `cmake_profile` | string | CMake preset or profile name |
| `toolchain` | enum (required) | `gnu`, `intel`, or `intel-oneapi` |
| `dependency_paths` | object | Map of dependency name to install prefix (e.g. `{"ELPA": "/opt/elpa"}`) |
| `cmake_flags` | string[] | Additional CMake flags |

## Validation

| Field | Type | Description |
|-------|------|-------------|
| `unit_tests` | string[] | List of unit test names or paths |
| `integration_tests` | string[] | List of integration test names or paths |
| `physical_correctness` | string (required) | How to verify the feature produces physically meaningful results |
| `regression_against` | string | Baseline version or commit to compare against |

## Example

```json
{
  "task_id": "librpa-head-wing",
  "target": "librpa",
  "feature_description": "Implement head-wing contribution to the correlation self-energy in GW approximation, enabling more accurate quasiparticle energy calculations for condensed matter systems.",
  "motivation": "The head-wing term is essential for systematic convergence of GW results with respect to auxiliary basis set size. Without it, GW band gaps are systematically underestimated for solids.",
  "code_location": {
    "repo": "https://github.com/AroundPeking/LibRPA",
    "branch": "enable_head_wing",
    "key_files": [
      "src/module_gw/gw.cpp",
      "src/module_gw/head_wing.cpp",
      "src/module_gw/head_wing.h"
    ],
    "depends_on": ["ABACUS df module", "LibRI"]
  },
  "build_config": {
    "cmake_profile": "release-oneapi",
    "toolchain": "intel-oneapi",
    "dependency_paths": {
      "ELPA": "/opt/elpa/2024.05.001",
      "LibXC": "/opt/libxc/6.2.2",
      "LibRI": "/home/ghj/libri/build",
      "Cereal": "/opt/cereal"
    },
    "cmake_flags": [
      "-DENABLE_LCA=ON",
      "-DBUILD_TESTING=ON"
    ]
  },
  "validation": {
    "unit_tests": ["test_head_wing_computation", "test_chi_head"],
    "integration_tests": ["test_gw_full_silicon", "test_gw_full_n2"],
    "physical_correctness": "Compare GW band gap of bulk silicon against VASP reference (0.57 eV direct gap at Γ). Deviation must be < 0.1 eV.",
    "regression_against": "librpa v0.4.0 without head-wing"
  },
  "status": "in_progress",
  "related_computation": "gw-si-bulk-001",
  "topic_slug": "gw-head-wing-convergence",
  "notes": "Must use same LibRI version as ABACUS to avoid ABI mismatch"
}
```

## Why it matters

Feature development in scientific software couples code changes to physical
correctness. Without explicit validation criteria, a feature can compile and
pass unit tests while producing wrong physics results.
