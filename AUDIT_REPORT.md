# AITP Domain Skill Integration — Audit Report

Date: 2026-04-26
Scope: oh-my-LibRPA integration into AITP, covering domain detection, harness chain, lane/domain hierarchy, and generalization.

---

## 1. Audit Context

We integrated oh-my-LibRPA into AITP via three changes:
- `brain/state_model.py`: added `DOMAIN_ID_TO_SKILL`, `_SLUG_FALLBACK_PATTERNS`, `_detect_domains_from_contracts()`, `_detect_domains_from_state()`, `resolve_domain_prerequisites()`
- `brain/mcp_server.py`: `aitp_get_execution_brief` now returns `domain_prerequisites` in all branches
- `skills/skill-librpa.md`: domain skill file with LibRPA-specific knowledge only

Four sub-agents audited: (A) self-consistency, (B) lane vs domain hierarchy, (C) harness chain, (D) generalization.

---

## 2. Findings

### 2A. Self-Consistency Issues (Code Layer)

| ID | Severity | File | Finding |
|----|----------|------|---------|
| C1 | HIGH | `mcp_server.py` `aitp_session_resume` (line ~1858-1920) | Returns inline execution brief but does NOT call `resolve_domain_prerequisites` or include `domain_prerequisites` in its return dict. A resuming agent (post context compaction) will not know to load domain skills. Also missing `_agent_behavior_reminder`. |
| C2 | HIGH | `mcp_server.py` `aitp_get_status` (line ~380-410) | Uses old `.md`-only `_load_domain_manifest()` (line ~200). Returns `domain_skill` (a domain_id string) not `domain_prerequisites` (list of skill filenames). Misses `.json` manifests, `state.md` frontmatter `domains`, and slug fallback. |
| C3 | MEDIUM | `state_model.py` `_load_manifest()` (line ~1096-1114) | Used by `evaluate_l4_stage` for domain invariant checking. Only reads `domain-manifest.md`, not `.json`. Topics with only `.json` manifests will skip L4 domain invariant checks entirely. |
| C4 | LOW | `mcp_server.py` L4 branch (line ~1774-1803) | Duplicate dict keys: `compute_target`, `gate_status`, `required_artifact_path`, `missing_requirements`, `next_allowed_transition`, `skill`, `l3_subplane` each appear twice. Python silently takes the last value (identical), so no runtime error, but confusing. |
| C5 | LOW | `state_model.py` `resolve_domain_prerequisites` docstring (line ~112) | Says "first match wins, all sources are merged" — contradictory. Actual behavior: union with dedup; slug fallback only fires if steps 1+2 found nothing. |
| C6 | DESIGN | Three separate manifest loaders | `_detect_domains_from_contracts()` (state_model.py:48, supports .md+.json), `_load_manifest()` (state_model.py:1096, .md only), `_load_domain_manifest()` (mcp_server.py:200, .md only). The latter two should be consolidated into the first. |
| C7 | LOW | `state_model.py` `_load_manifest()` (line ~1112) | Catches `json.JSONDecodeError` but never parses JSON — dead code from copy-paste. |

### 2B. Lane vs Domain Hierarchy

| ID | Finding |
|----|---------|
| D1 | `brain/PROTOCOL.md` (the authoritative protocol doc) describes lanes, stages, postures but **never mentions domain skills** at all. An agent reading only PROTOCOL.md has no idea domains exist. |
| D2 | "domain" is overloaded: L2 knowledge graph has `DOMAIN_TAXONOMY` (physics subject areas like `electronic-structure`, `quantum-many-body`), while domain skills have IDs like `abacus-librpa`. These are completely different concepts sharing the same word. |
| D3 | Domain is de facto coupled to `code_method` lane: domain-specific directories only created for `code_method` (mcp_server.py:459), LaTeX domain context labeled "(code_method only)" (mcp_server.py:4495), all skill content targets `code_method`. This is architecturally sound but never documented as a design decision. |
| D4 | `AITP_SPEC.md` line 474 labels lane as "Research domain" (should be "Research methodology") and uses outdated lane names (`model_numeric` should be `toy_numeric`, `code_and_materials` is a legacy alias). |
| D5 | `FEATURE_DEVELOPMENT_PLAYBOOK.md` reads like a top-level protocol doc but is actually ABACUS+LibRPA specific. Its final paragraph acknowledges this, but it's easy to miss. |
| D6 | `FIRST_PRINCIPLES_LANE_PROTOCOL.md` is entirely LibRPA-specific but should be a generic template applicable to any first-principles code. |

### 2C. Harness Chain Gaps

| ID | Severity | Location | Gap |
|----|----------|----------|-----|
| H1 | CRITICAL | `deploy/templates/claude-code/using-aitp.md` + `deploy/templates/kimi-code/using-aitp.md` | No instruction to check `domain_prerequisites` and load domain skills. The using-aitp skill is the primary entry procedure for agents — if it doesn't mention domain skills, agents won't load them. |
| H2 | CRITICAL | `deploy/templates/claude-code/aitp-runtime.md` + `deploy/templates/kimi-code/aitp-runtime.md` | Decision loop matches on `brief.stage` and loads stage skill, but never checks `brief.domain_prerequisites`. |
| H3 | CRITICAL | `hooks/session_start.py` (or equivalent in deploy/) | Prints stage skill instruction at session start but never calls `resolve_domain_prerequisites` or mentions domain skills. |
| H4 | MEDIUM | `mcp_server.py` `aitp_bootstrap_topic` (line ~437) | Returns plain string with no domain info. If slug matches a legacy pattern, agent won't know until next `aitp_get_execution_brief` call. |

**Impact of H1+H2+H3**: The only mechanism telling agents to load domain skills is a single sentence in `_AGENT_BEHAVIOR_REMINDER` (mcp_server.py line ~112) embedded in the execution brief response. This is easily ignored. The deploy templates — the actual instructions agents follow — are completely silent on domain skills. **This means the domain skill system is effectively non-functional in practice.**

### 2D. Generalization Assessment

| Component | Status | Action |
|-----------|--------|--------|
| `brain/state_model.py` registration | Generalizable | Add `DOMAIN_ID_TO_SKILL` entry per domain. No structural change needed. |
| `DOMAIN_SKILL_INTERFACE_PROTOCOL.md` | Already general | Relax `operation.family` enum from `["computation", "development"]` to open string. |
| `EXTERNALIZED_SPEC_PROTOCOL.md` | Already general | No changes needed. |
| `computation-workflow.schema.json` | **Hardcoded LibRPA** | `computation_type` enum: `["gw", "rpa"]` — missing dft, hf, md, relax, phonon, bse, td-dft. `stages[].name` enum: `["scf", "df", "nscf", "librpa", "postprocess"]` — `df` and `librpa` are ABACUS-specific. `basis_integrity.shrink_invariant` and `nao_orbitals` are ABACUS-NAO concepts. |
| `compute-resource.schema.json` | **Hardcoded LibRPA** | `abacus_path`, `librpa_path`, `libri_path` are code-specific. Should be generic `executable_paths: { [code_name]: string }`. |
| `development-task.schema.json` | **Hardcoded LibRPA** | `target` enum: `["abacus", "librpa", "libri", "libcomm", "pyatb", "other"]`. `build_config.toolchain` missing llvm, nvhpc, cray. |
| `calculation-debug.schema.json` | **Hardcoded LibRPA** | `failure_stage` enum: `["scf", "df", "nscf", "librpa", "postprocess"]`. |
| `benchmark-report.schema.json` | Mostly general | `system_type` could expand beyond `["molecule", "solid", "2D"]`. |
| 5 contract Markdown files | **LibRPA-specific** | All examples and field descriptions reference ABACUS/LibRPA file paths (STRU, KPT, INPUT_scf, librpa.in, OUT.ABACUS/). |
| `FEATURE_DEVELOPMENT_PLAYBOOK.md` | Mixed | 9-phase structure is universal. Walkthrough examples are LibRPA-specific. Needs split: generic template + domain appendix. |
| `FIRST_PRINCIPLES_LANE_PROTOCOL.md` | LibRPA-specific | Needs generic template version. Current content becomes domain appendix. |
| `PROJECT_STRUCTURE_CONVENTION.md` | Mostly general | Remove ABACUS+LibRPA name drops. Generalize build system (not just CMake). |
| `skills/skill-librpa.md` patterns | Correctly scoped | Smoke test framework, invariant checking framework, escape hatch patterns are universal and should be promoted to protocol level. Specific instances remain domain-specific. |

**Blocker for new domains**: Adding a VASP or QE domain would be blocked by the hardcoded enums in 4 contract schemas — they would reject valid data from other codes.

---

## 3. Recommended Modification Plan

### Batch 1: Fix Harness (Priority: URGENT)

Without these fixes, the domain skill system is non-functional.

- **1.1** Update deploy templates to include domain skill loading
- **1.2** Add `domain_prerequisites` to `aitp_session_resume`
- **1.3** Consolidate manifest loaders (unify `.md`+`.json` support)
- **1.4** Update `aitp_get_status` to use `resolve_domain_prerequisites`
- **1.5** Add domain section to `PROTOCOL.md`

### Batch 2: Generalize Schemas and Docs (Priority: HIGH)

- **2.1** Generalize 4 contract JSON schemas (open enums)
- **2.2** Split `FEATURE_DEVELOPMENT_PLAYBOOK.md` into generic template + domain appendix
- **2.3** Create generic `FIRST_PRINCIPLES_LANE_PROTOCOL` template
- **2.4** Fix `AITP_SPEC.md` lane labels and names
- **2.5** Generalize contract Markdown files

### Batch 3: Promote Universal Patterns (Priority: MEDIUM)

- **3.1** Promote smoke test framework to protocol level
- **3.2** Promote invariant checking framework to protocol level
- **3.3** Promote escape hatch patterns to protocol level
- **3.4** Clean up `PROJECT_STRUCTURE_CONVENTION.md` naming
