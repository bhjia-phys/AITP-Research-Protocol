# Domain Skill Interface Protocol

This document defines the **interface between AITP and domain-specific skills**.
Any physics-method skill (oh-my-librpa, vasp-workflow, qe-gw, pyatb-transport,
etc.) plugs into AITP through this protocol — not by embedding knowledge into
AITP itself.

**Core principle**: AITP manages the research lifecycle (projects, layers,
gates, human interaction). Domain skills provide the physics knowledge
(contracts, operations, invariants, routing). They communicate through
structured contract files on disk.

```
┌──────────────────────────────────────────────────┐
│                    AITP Core                      │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Project    │ │  L0–L4     │ │  Human       │  │
│  │  Lifecycle  │ │  Layers    │ │  Interaction  │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
│  ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │  Gate      │ │  Contract  │ │  Playbook    │  │
│  │  Engine    │ │  Validator │ │  Engine      │  │
│  └────────────┘ └────────────┘ └──────────────┘  │
│                                                    │
│  ┌────────────────────────────────────────────┐    │
│  │     Domain Skill Interface (this doc)      │    │
│  └────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │  oh-my- │   │ vasp-   │   │ (future │
    │  librpa │   │ workflow│   │  skill) │
    └─────────┘   └─────────┘   └─────────┘
```

---

## 1. What AITP provides

AITP is responsible for all **lifecycle and protocol** concerns:

| Responsibility | Description |
|---------------|-------------|
| Project setup | Create folder structure, LaTeX template, README |
| Layer management | L0–L4 directories, promotion rules, file placement |
| Gate enforcement | Check gate criteria, block progression if not met |
| Human interaction | GSD-style checkpoints, structured options, decision logging |
| Contract validation | Verify JSON contracts against schemas |
| Playbook execution | Drive the 9-phase development process |
| Topic management | AITP topic bootstrap, loop, status, promotion |

AITP does **not** know anything about specific physics codes, algorithms, or
domain invariants. That knowledge comes from the domain skill.

---

## 2. What the domain skill provides

A domain skill is responsible for all **physics and domain** knowledge:

| Responsibility | Description |
|---------------|-------------|
| Domain manifest | Declare what codes, system types, and operations the skill covers |
| Contract templates | Define the JSON schemas and contract families for this domain |
| Operation routing | Route user requests to the correct operation family |
| Invariants | Define domain-specific invariants that must pass at L4 |
| Derivation guidance | Tell AITP what equations need to be derived for a given feature |
| Implementation mapping | Map derived equations to specific code locations |
| Benchmark systems | Suggest test systems and reference values |
| Error classification | Classify domain-specific failure modes |
| Smoke test criteria | Define what constitutes a passing smoke test |

---

## 3. Communication mechanism

AITP and domain skills communicate **through contract files on disk**. There is
no API, no function calls, no IPC. The project folder is the shared state.

### 3.1 File-based protocol

```
<project-root>/
├── contracts/                    # Shared state (Markdown with YAML frontmatter)
│   ├── domain-manifest.md        # Skill registers here (§4)
│   ├── computation-workflow.*.md     # Skill writes, AITP validates
│   ├── development-task.*.md         # Skill writes, AITP validates
│   ├── benchmark-report.*.md         # Skill writes, AITP validates
│   ├── calculation-debug.*.md        # Skill writes, AITP validates
│   └── compute-resource.*.md         # Skill writes, AITP validates
└── ...
```

### 3.2 Data flow

```
AITP Core                              Domain Skill
   │                                       │
   │──── "What domain is this?" ──────────>│
   │<─── domain-manifest.md ───────────────│
   │                                       │
   │──── "Create project for <topic>" ────>│
   │<─── domain-specific dirs/files ───────│
   │                                       │
   │──── "What derivation is needed?" ────>│
   │<─── derivation guidance ──────────────│
   │                                       │
   │──── "What code maps to Eq. N?" ─────>│
   │<─── implementation mapping ───────────│
   │                                       │
   │──── "Classify this error" ──────────>│
   │<─── error classification ─────────────│
   │                                       │
   │──── "Suggest benchmark systems" ────>│
   │<─── test systems + references ────────│
```

AITP asks questions by writing a request file. The skill answers by writing a
response file or by directly modifying contract files.

### 3.3 The skill is not a library

The domain skill is an **agent-side capability**, not a Python library or a
REST API. It runs inside the agent (OpenCode skill, Claude Code skill, etc.)
and reads/writes files in the project directory. AITP's agent-side code can
invoke the skill, but the skill is not imported as a Python module.

---

## 4. Domain manifest

Every domain skill must provide a `domain-manifest.md`. This is the skill's
registration card — it tells AITP everything about the domain.

### Schema

The manifest is stored as a Markdown file (`domain-manifest.md`) with YAML
frontmatter. The JSON Schema below describes the required frontmatter fields.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DomainManifest",
  "type": "object",
  "required": ["domain_id", "display_name", "version", "target_codes",
               "system_types", "operations", "contracts", "invariants"],
  "properties": {
    "domain_id": {
      "type": "string",
      "description": "Unique domain identifier, lowercase, hyphen-separated"
    },
    "display_name": {
      "type": "string",
      "description": "Human-readable name"
    },
    "version": {
      "type": "string",
      "description": "Skill version (semver)"
    },
    "description": {
      "type": "string",
      "description": "One-sentence description of what this domain covers"
    },
    "target_codes": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Software packages this domain covers"
    },
    "system_types": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Supported system types"
    },
    "computation_types": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Supported computation types (e.g., gw, rpa, dft, md)"
    },
    "operations": {
      "type": "array",
      "items": {
        "type": "object",
          "required": ["name", "family", "description", "phases"],
          "properties": {
            "name": {"type": "string"},
            "family": {"type": "string", "enum": ["computation", "development"]},
            "description": {"type": "string"},
            "phases": {"type": "array", "items": {"type": "string"}},
            "required_contracts": {"type": "array", "items": {"type": "string"}},
            "spec_required": {"type": "boolean", "description": "Whether this operation requires an externalized spec before implementation"},
            "min_path": {"type": "string", "enum": ["zero_shot", "spec_guided", "derive_first"], "description": "Minimum recommended path: zero_shot (no spec), spec_guided (spec but no derivation), derive_first (full derive-first)"}
          }
      }
    },
    "contracts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "schema_path", "purpose"],
        "properties": {
          "name": {"type": "string"},
          "schema_path": {"type": "string"},
          "purpose": {"type": "string"},
          "used_in_phases": {"type": "array", "items": {"type": "integer"}}
        }
      }
    },
    "invariants": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "description", "failure_mode", "check_method"],
        "properties": {
          "id": {"type": "string"},
          "description": {"type": "string"},
          "failure_mode": {"type": "string"},
          "check_method": {"type": "string"}
        }
      }
    },
    "reproducibility": {
      "type": "object",
      "description": "Reproducibility and externalized-spec configuration",
      "properties": {
        "recommended_model_combos": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "spec_model": {"type": "string", "description": "Model recommended for spec generation (Phase 1)"},
              "code_model": {"type": "string", "description": "Model recommended for code generation (Phase 3)"},
              "typical_hitl_rounds": {"type": "integer", "description": "Expected human feedback rounds"},
              "notes": {"type": "string"}
            }
          }
        },
        "conversation_archive": {
          "type": "object",
          "properties": {
            "directory": {"type": "string", "description": "Project-relative path for conversation archives", "default": "archive/"},
            "naming_convention": {"type": "string", "description": "Pattern: {artifact}-{model1}-{model2}#{round}-{status}.{ext}"}
          }
        }
      }
    },
    "routing": {
      "type": "object",
      "properties": {
        "intent_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "pattern": {"type": "string"},
              "operation": {"type": "string"},
              "subdomain": {"type": "string"}
            }
          }
        },
        "input_patterns": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "file_pattern": {"type": "string"},
              "subdomain": {"type": "string"}
            }
          }
        }
      }
    }
  }
}
```

### Minimal example

A minimal manifest for a hypothetical VASP workflow skill:

```json
{
  "domain_id": "vasp-gw",
  "display_name": "VASP GW Workflow",
  "version": "0.1.0",
  "target_codes": ["vasp"],
  "system_types": ["molecule", "solid"],
  "computation_types": ["gw", "rpa"],
  "operations": [
    {"name": "gw_workflow", "family": "computation", "description": "GW band structure", "phases": ["4", "5"]}
  ],
  "contracts": [
    {"name": "computation-workflow", "schema_path": "schemas/computation-workflow.schema.json", "purpose": "Track GW stages"}  # schema defines frontmatter shape
  ],
  "invariants": [
    {"id": "encut_convergence", "description": "ENCUT must be converged before GW", "failure_mode": "Incorrect QP energies", "check_method": "Compare ENCUT series"}
  ],
  "routing": {
    "intent_patterns": [
      {"pattern": "Run GW with VASP", "operation": "gw_workflow", "subdomain": "computation"}
    ]
  }
}
```

---

## 5. Skill hooks

A domain skill should be able to respond to these hooks from AITP. The hooks
are invoked by the agent (not by AITP Python code) when the playbook engine
reaches a specific phase or gate.

| Hook | When called | What the skill returns |
|------|------------|----------------------|
| `register` | Phase P (project setup) | `domain-manifest.md`, domain-specific subdirectories, initial README content |
| `on_scope` | Phase 0 | Suggested system types, reference data sources, success criteria template |
| `on_derivation_required` | Phase 1 | List of equations to derive, starting references, assumptions to document |
| `on_implementation_map` | Phase 1 (after derivation) | Mapping from equations to code locations, branch names |
| `on_plan` | Phase 2 | `development-task` contract template, build configuration suggestions |
| `on_smoke_system` | Phase 4 | Minimal test system (STRU, INPUT, KPT), expected stage sequence |
| `on_benchmark_systems` | Phase 5 | List of test systems with reference values, convergence parameters |
| `on_error_classify` | Phase 6 | Error classification (category, root cause, suggested fix actions) |
| `on_l2_artifacts` | Phase 7 | List of artifacts to promote to L2 (experience cards, reference data) |
| `on_spec_quality_check` | Phase 1 | Spec quality criteria and minimum pass threshold for the domain |

### Hook invocation

The agent invokes hooks through the skill system of the runtime (OpenCode
skill, Claude Code skill, etc.). AITP does not call hooks directly — it
signals the agent that a hook is needed, and the agent delegates to the skill.

```
AITP Playbook Engine
  → "Phase 1 reached. Need derivation guidance for <topic>."
    → Agent reads domain-manifest.md
    → Agent invokes oh-my-librpa skill with derivation request
    → Skill returns equation list, references, assumptions
    → Agent writes guidance into project docs/
```

---

## 6. Multiple skills

A project can have **more than one domain skill** registered. This happens
when a feature spans multiple domains (e.g., ABACUS+LibRPA for GW, then
pyatb for transport properties).

### Rules

1. Each skill registers its own `domain-manifest.md` in
   `contracts/domain-manifest.<domain_id>.md`.
2. Contract schemas from different skills coexist in `schemas/`.
3. Invariants from all registered skills are checked at L4.
4. Routing is tried in registration order; first match wins.
5. A skill may declare dependencies on other skills in its manifest.

### Example: multi-skill project

```
contracts/
├── domain-manifest.abacus-librpa.md    # GW calculation
├── domain-manifest.pyatb.md            # Transport properties
├── computation-workflow.gw-al-001.md
├── computation-workflow.transport-al-001.md
└── ...
```

---

## 7. Skill qualification

Not every OpenCode skill qualifies as a domain skill for AITP. To qualify, a
skill must:

1. **Provide a `domain-manifest.md`** conforming to the schema in §4.
2. **Implement at least the `register` and `on_scope` hooks** (§5).
3. **Use AITP contract schemas** for any data that passes through gates.
4. **Respect the derive-first workflow** — no code suggestions before
   derivation approval.
5. **Follow the project structure convention** — all files in the project
   folder, LaTeX for derivations.
6. **Use the human interaction protocol** — structured options at gates,
   no implicit decisions.

### Skill discovery

When a new project is created, the agent:

1. Reads the topic description.
2. Scans available domain skills for matching `routing.intent_patterns`.
3. Presents matching skills to the human: "This project matches these skills:
   [oh-my-librpa]. Register them?"
4. Human confirms. Skill manifests are copied into `contracts/`.

---

## 8. Relationship to existing documents

| Document | Role | Changes |
|----------|------|---------|
| `FIRST_PRINCIPLES_LANE_PROTOCOL.md` | Domain-specific protocol | Becomes the **oh-my-librpa domain implementation** of this interface, not AITP core |
| `FEATURE_DEVELOPMENT_PLAYBOOK.md` | Generic playbook | Stays generic; domain-specific details come from the skill hooks |
| `PROJECT_STRUCTURE_CONVENTION.md` | Generic structure | Unchanged; all skills follow this |
| This document | Interface specification | New; defines the contract between AITP and skills |
| `domain-manifest.*.md` | Skill registration | New; per-skill, stored in project `contracts/` |

### Migration path

The current ABACUS+LibRPA domain knowledge in `FIRST_PRINCIPLES_LANE_PROTOCOL.md`
does not disappear — it becomes the content of the `oh-my-librpa` domain
manifest. The protocol document is refactored to reference this interface
instead of embedding the domain knowledge directly.

---

## 9. Summary

| Concept | Owned by |
|---------|---------|
| Project lifecycle, layers, gates | AITP core |
| Human interaction protocol | AITP core |
| Contract validation framework | AITP core |
| Playbook phases (P, 0–7) | AITP core |
| Folder structure, LaTeX convention | AITP core |
| **Domain manifest** | **Domain skill** |
| **Contract schemas** (what fields) | **Domain skill** |
| **Operation routing** (what → where) | **Domain skill** |
| **Invariants** (physics checks) | **Domain skill** |
| **Derivation guidance** (what equations) | **Domain skill** |
| **Implementation mapping** (formula → code) | **Domain skill** |
| **Error classification** (failure modes) | **Domain skill** |
| **Benchmark systems** (test + reference) | **Domain skill** |

The boundary is simple: AITP manages **how** research happens. The domain
skill manages **what** the research is about. They meet at the contract files
in the project directory.

---

## 10. Reproducibility and externalized specs

AITP formalizes two principles inspired by the DMRG-LLM study
([arXiv:2604.04089](https://arxiv.org/abs/2604.04089)):

1. **Externalized specifications** — intermediate technical specs that capture
   implementation-critical knowledge absent from source literature. These are
   first-class artifacts, not summaries.
2. **Absolute reproducibility** — every conversation, every spec version, every
   code version is preserved with structured naming in the project archive.

The domain skill participates in reproducibility by:

- Declaring `recommended_model_combos` in its manifest (§4 schema)
- Marking each operation with `spec_required` and `min_path`
- Providing quality criteria via the `on_spec_quality_check` hook (§5)

The full protocol is documented in
[`EXTERNALIZED_SPEC_PROTOCOL.md`](EXTERNALIZED_SPEC_PROTOCOL.md).
