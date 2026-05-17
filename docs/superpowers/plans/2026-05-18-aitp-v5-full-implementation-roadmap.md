# AITP v5 Full Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build AITP v5 into a practical theoretical-physicist research harness: kernel-first state, risk-calibrated rigor, light human interaction, tool/evidence provenance, self-evolution, and legacy AITP compatibility.

**Architecture:** Keep all durable protocol semantics inside `brain/v5/`. MCP, CLI, hooks, skills, and subagents must be thin interfaces that call the kernel rather than duplicating rules. Preserve legacy AITP artifacts while gradually routing new work through v5.

**Tech Stack:** Python standard library, dataclasses, pathlib, YAML/Markdown store, pytest, optional later adapters for MCP/CLI/hooks, Git worktrees, JSONL/SQLite trace storage if needed.

---

## Current Baseline

Worktree:

```text
C:\Users\samur\.config\superpowers\worktrees\AITP-Research-Protocol\aitp-v5-kernel-mvp
```

Branch:

```text
codex/aitp-v5-kernel-mvp
```

Current v5 commits:

```text
4a84953 feat: add aitp v5 kernel mvp
4cee91b feat: add v5 risk engine action budgets
bf7de26 feat: add v5 trust card resolution
```

Current focused verification:

```bash
pytest tests/test_v5_trust_cards.py tests/test_v5_risk_engine.py tests/test_v5_kernel.py -q
```

Expected current result:

```text
13 passed
```

Current full legacy suite status:

```text
72 failed, 126 passed
```

The 72 failures are pre-existing legacy MCP/L2/visualization failures. Do not use full-suite red status as a blocker for isolated v5 work, but keep recording it as a regression baseline.

## Core Design Commitments

1. AITP v5 is a theoretical-physicist research kernel, not a generic chatbot wrapper.
2. The center of the system is the execution brief, not a fixed L0-L4 checklist.
3. L0-L4 survives as epistemic zones and evidence maturity, not as the only legal workflow.
4. Default interaction must be light; rigor is triggered by risk, not by every step.
5. "Too light" and "too heavy" are both harness failures.
6. Code provenance is physics evidence for computational theoretical physics.
7. Trust cards reduce friction only inside a recorded scope; invalidation must add risk.
8. Human checkpoints are for real research choices, not for every state transition.
9. Harness self-evolution is background, sparse, test-backed, and never another gate.
10. New topic work should default to v5 once MCP/CLI are ready; old topics remain readable through a bridge.

## File Structure Roadmap

Existing v5 package:

```text
brain/v5/
  brief.py
  code.py
  flow.py
  ids.py
  markdown.py
  models.py
  paths.py
  question_engine.py
  risk.py
  store.py
  trust.py
  workspace.py
```

Create over this roadmap:

```text
brain/v5/contracts.py
brain/v5/trace.py
brain/v5/audit.py
brain/v5/evolution.py
brain/v5/policy.py
brain/v5/interaction.py
brain/v5/question_intents.py
brain/v5/evidence.py
brain/v5/tools.py
brain/v5/cli.py
brain/v5/mcp_tools.py
brain/v5/legacy_bridge.py
brain/v5/subagents.py
```

Focused tests to create:

```text
tests/test_v5_contracts.py
tests/test_v5_trace_audit.py
tests/test_v5_evolution.py
tests/test_v5_policy.py
tests/test_v5_interaction.py
tests/test_v5_question_intents.py
tests/test_v5_evidence_tools.py
tests/test_v5_cli.py
tests/test_v5_mcp_tools.py
tests/test_v5_legacy_bridge.py
tests/test_v5_subagents.py
```

## Big Implementation Phases

### Phase 1: Contracts And Schema Validation

Purpose:

- Make AITP records machine-checkable so MCP, CLI, hooks, and subagents cannot silently pass malformed payloads.
- Validate the shape of execution briefs, risk assessments, action budgets, trust cards, code states, evidence records, harness incidents, and evolution proposals.

Deliverables:

- `brain/v5/contracts.py`
- `tests/test_v5_contracts.py`
- Brief builder returns a payload that passes `validate_execution_brief()`.

Acceptance:

- Missing `risk_assessment` in a brief is rejected.
- Action budgets with too many questions or missing required outputs are rejected.
- Valid current `build_execution_brief()` output passes.

### Phase 2: Trace Logger And Harness Audit

Purpose:

- Record minimal events without adding friction to the research flow.
- Detect both under-thinking and over-harnessing.

Deliverables:

- `brain/v5/trace.py`
- `brain/v5/audit.py`
- `tests/test_v5_trace_audit.py`

Events:

```text
session_started
brief_built
question_asked
tool_used
record_written
claim_confidence_changed
human_checkpoint_used
subagent_requested
session_stopped
```

Incidents to detect:

```text
under_thinking:
  rigorous/adversarial action without evidence_or_provenance
  code_method claim without linked code_state
  confidence change without evidence_ref
  trust card invalidated but autopilot behavior observed

over_harnessing:
  fluid mode asked more than action_budget.max_questions
  fluid mode wrote durable claim/evidence records without user intent
  subagent used when risk level was fluid
  human checkpoint used when not required
```

Acceptance:

- Trace logging is append-only and cheap.
- Audit can scan a trace and emit `HarnessIncident` records.
- Incidents include `change_direction`: `tighten`, `loosen`, `clarify`, `automate`, or `defer`.

### Phase 3: Evolution Loop

Purpose:

- Let AITP improve its harness when repeated or severe incidents show the protocol is wrong.
- Keep evolution sparse and test-backed.

Deliverables:

- `brain/v5/evolution.py`
- `tests/test_v5_evolution.py`
- Registry paths for harness incidents and proposals.

Rules:

```text
Level 0: record incident only
Level 1: generate proposal
Level 2: create worktree patch branch with test
Level 3: require human approval for core protocol changes
Level 4: require explicit approval for hooks, shell, remote execution, or destructive actions
```

Acceptance:

- Repeated incidents aggregate into one proposal.
- Proposal includes target files, required tests, change direction, and expected effect.
- No proposal can claim ready-to-merge without a regression test reference.

### Phase 4: Policy Guards

Purpose:

- Put non-negotiable safety and epistemic rules into code, not model goodwill.

Deliverables:

- `brain/v5/policy.py`
- `tests/test_v5_policy.py`

Guards:

```text
no_l2_promotion_without_evidence_ref
no_code_method_validation_without_code_state
no_expensive_compute_without_budget_or_checkpoint
no_trust_reduction_when_card_invalidated
no_harness_patch_without_test
no_core_protocol_patch_without_review
```

Acceptance:

- Policy returns structured allow/block decisions.
- Brief exposes blocked actions as `forbidden_now`.
- Hooks and CLI can call the same policy functions.

### Phase 5: Interaction Profiles

Purpose:

- Support teacher, collaborator, student, critic, seminar host, and reproducer modes without changing truth standards.

Deliverables:

- `brain/v5/interaction.py`
- `tests/test_v5_interaction.py`

Profiles:

```text
collaborator
teacher
student
critic
seminar_host
reproducer
```

Fields:

```text
role
depth
questioning_style
memory_policy
desired_friction
output_contract
truth_standard
```

Acceptance:

- Teacher mode changes explanation/question style but not risk policy.
- Student mode asks clarifying questions and mirrors the user's claim.
- Critic mode increases adversarial question priority only when risk permits.
- User steering can make interaction lighter or stricter inside policy bounds.

### Phase 6: Question Intents And LLM Expansion Boundary

Purpose:

- Separate deterministic kernel question intent from LLM-specific phrasing.

Deliverables:

- `brain/v5/question_intents.py`
- updates to `brain/v5/question_engine.py`
- `tests/test_v5_question_intents.py`

Intent examples:

```text
claim_scope_check
object_relation_check
failure_mode_check
limit_symmetry_dimension_check
finite_size_or_cutoff_check
formula_code_invariant_check
benchmark_consistency_check
literature_conflict_check
interaction_understanding_check
```

Acceptance:

- FQHE-like toy numeric claim emits sector/counting/finite-size intent.
- LibRPA/GW code claim emits formula-code/provenance/benchmark intent.
- Teacher mode can request prerequisite/misconception intents.

### Phase 7: Evidence And Tool-Run Layer

Purpose:

- Make external tools produce auditable evidence rather than chat-only output.

Deliverables:

- `brain/v5/evidence.py`
- `brain/v5/tools.py`
- `tests/test_v5_evidence_tools.py`

Records:

```text
EvidenceRecord
ToolRecipeRecord
ToolRunRecord
ArtifactRecord
BenchmarkRecord
```

Tool families:

```text
literature: arXiv, web, Zotero, local notes
formal: algebra, limit, dimension, derivation trace
numerical: toy Hamiltonian, exact diagonalization, finite-size, convergence
code: git worktree, pytest, benchmark runner, code provenance
domain: LibRPA, ABACUS, GW, QSGW
```

Acceptance:

- Tool run records include inputs, outputs, environment, linked claim, and evidence status.
- Large artifacts are stored by reference, not copied into frontmatter.
- Evidence records can satisfy action-budget required outputs.

### Phase 8: CLI Entry Point

Purpose:

- Provide stable commands for humans, hooks, CI, and scripts.

Deliverables:

- `brain/v5/cli.py`
- `tests/test_v5_cli.py`

Commands:

```text
aitp-v5 init <base>
aitp-v5 topic create <topic-id> --context <context-id> --title <title>
aitp-v5 session bind <session-id> --topic <topic-id> --context <context-id>
aitp-v5 claim create --topic <topic-id> --statement <text> --evidence-profile <profile>
aitp-v5 brief <session-id>
aitp-v5 risk assess <claim-id>
aitp-v5 code-state record ...
aitp-v5 trace audit <session-id>
```

Acceptance:

- CLI returns JSON for machine consumption.
- CLI uses kernel functions only.
- CLI does not import legacy MCP monolith.

### Phase 9: MCP Tool Surface

Purpose:

- Let Codex/Claude/OpenCode call v5 kernel state without reading files manually.

Deliverables:

- `brain/v5/mcp_tools.py`
- `tests/test_v5_mcp_tools.py`

Tools:

```text
aitp_v5_init_workspace
aitp_v5_bind_session
aitp_v5_create_topic
aitp_v5_create_claim
aitp_v5_get_execution_brief
aitp_v5_assess_risk
aitp_v5_record_code_state
aitp_v5_record_evidence
aitp_v5_log_trace_event
aitp_v5_audit_trace
aitp_v5_query_l2_memory
```

Acceptance:

- MCP tool functions are thin wrappers.
- All returned payloads pass contract validation.
- Old MCP tools remain available for legacy topics.

### Phase 10: Hooks

Purpose:

- Add lightweight lifecycle enforcement without turning self-evolution into another gate.

Deliverables:

- hook specs under `docs/`
- optional scripts under `scripts/`
- tests for hook decision functions in `tests/test_v5_policy.py` or `tests/test_v5_trace_audit.py`

Hooks:

```text
SessionStart:
  bind or resume session
  build brief

PreToolUse:
  check policy for expensive compute, code mutation, L2 promotion, harness patch

PostToolUse:
  record tool run and evidence

Stop:
  write lightweight trace summary
  audit incidents in background

PreCommit:
  if harness files changed, require tests and evolution note
```

Acceptance:

- Hooks default to logging, not blocking.
- Blocking only occurs for explicit high-risk policy violations.
- Hook output stays short.

### Phase 11: Subagent Packets

Purpose:

- Use subagents for bounded critic/reproducer/literature/code-review tasks only when risk warrants it.

Deliverables:

- `brain/v5/subagents.py`
- `tests/test_v5_subagents.py`

Packets:

```text
CriticPacket
ReproducerPacket
LiteratureScoutPacket
CodeReviewerPacket
TeacherAssistantPacket
```

Acceptance:

- Packet includes claim, risk signals, evidence refs, code state refs, expected output.
- Packet excludes noisy unrelated topic history.
- Subagent results return as evidence/proposal records, never direct L2 promotion.

### Phase 12: Legacy Bridge

Purpose:

- Preserve old topic content while allowing v5 execution briefs over legacy topics.

Deliverables:

- `brain/v5/legacy_bridge.py`
- `tests/test_v5_legacy_bridge.py`

Mapping:

```text
old L0 sources -> v5 evidence/source records
old L1 question/source artifacts -> v5 topic framing and source basis
old L3 ideas/candidates -> v5 idea/claim records
old L4 reviews -> v5 validation evidence
old L2 entries -> v5 memory/l2
old runtime logs -> v5 trace summaries
```

Acceptance:

- Bridge reads legacy artifacts but does not rewrite them unless explicitly requested.
- A legacy topic can produce a v5 execution brief.
- Migration preserves source paths and provenance.

### Phase 13: Domain Packs

Purpose:

- Encode reusable theoretical-physics workflows without hard-coding user-facing topic types.

Deliverables:

- domain pack records under `.aitp/tools/domain_packs/`
- optional Python helpers under `brain/v5/domain_packs/`

Initial packs:

```text
formal_theory:
  definitions, assumptions, derivation trace, counterexample, literature consistency

fqhe_topological_order:
  sector, filling, counting, CFT/ED comparison, finite-size, quasiparticle data

gw_librpa:
  self-energy, frequency grid, basis cutoff, Coulomb singularity, commit/build/runtime, benchmark recipe

toy_numerics:
  Hamiltonian definition, symmetry sector, finite-size scan, convergence, negative control
```

Acceptance:

- Domain packs suggest question intents, risk signals, tool recipes, and trust-card templates.
- Domain packs do not override global truth standards.

## Detailed First Implementation Sequence

### Task 1: Contracts

**Files:**

- Create: `brain/v5/contracts.py`
- Test: `tests/test_v5_contracts.py`
- Modify: `brain/v5/brief.py` only if needed to ensure its payload passes validation.

- [ ] **Step 1: Write failing tests**

Create tests:

```python
def test_execution_brief_contract_accepts_current_brief(tmp_path):
    ...

def test_execution_brief_contract_rejects_missing_risk_assessment():
    ...

def test_action_budget_contract_rejects_unbounded_questions():
    ...
```

Run:

```bash
pytest tests/test_v5_contracts.py -q
```

Expected:

```text
FAIL: No module named 'brain.v5.contracts'
```

- [ ] **Step 2: Implement minimal validation**

Implement:

```text
ContractIssue
ContractResult
validate_action_budget(payload)
validate_risk_assessment(payload)
validate_execution_brief(payload)
require_valid_execution_brief(payload)
```

- [ ] **Step 3: Verify**

Run:

```bash
pytest tests/test_v5_contracts.py tests/test_v5_kernel.py tests/test_v5_risk_engine.py tests/test_v5_trust_cards.py -q
python -m compileall -q brain/v5
git diff --check -- .
```

Expected:

```text
all focused tests pass
```

- [ ] **Step 4: Commit and push**

```bash
git add brain/v5/contracts.py tests/test_v5_contracts.py brain/v5/brief.py docs/superpowers/plans/2026-05-18-aitp-v5-full-implementation-roadmap.md
git commit -m "feat: add v5 contract validation"
git push origin codex/aitp-v5-kernel-mvp
git push origin HEAD:main
```

### Task 2: Trace And Audit

**Files:**

- Create: `brain/v5/trace.py`
- Create: `brain/v5/audit.py`
- Test: `tests/test_v5_trace_audit.py`

Implement after Task 1 is pushed.

Acceptance tests:

```python
def test_trace_logger_appends_jsonl_events(tmp_path):
    ...

def test_audit_detects_underthinking_when_rigorous_action_lacks_evidence():
    ...

def test_audit_detects_overharnessing_when_fluid_mode_asks_too_many_questions():
    ...
```

### Task 3: Evolution Proposals

**Files:**

- Create: `brain/v5/evolution.py`
- Test: `tests/test_v5_evolution.py`

Implement after Task 2 is pushed.

Acceptance tests:

```python
def test_repeated_incidents_aggregate_into_one_proposal():
    ...

def test_proposal_requires_regression_test_for_harness_patch():
    ...

def test_core_protocol_change_requires_human_review():
    ...
```

### Task 4: Policy Guards

**Files:**

- Create: `brain/v5/policy.py`
- Test: `tests/test_v5_policy.py`

Implement after Task 3 is pushed.

Acceptance tests:

```python
def test_policy_blocks_code_method_validation_without_code_state():
    ...

def test_policy_blocks_l2_promotion_without_evidence_ref():
    ...

def test_policy_allows_fluid_discussion_without_durable_records():
    ...
```

### Task 5: Interaction Profiles

**Files:**

- Create: `brain/v5/interaction.py`
- Test: `tests/test_v5_interaction.py`

Implement after Task 4 is pushed.

Acceptance tests:

```python
def test_teacher_profile_changes_question_style_without_lowering_truth_standard():
    ...

def test_student_profile_prefers_clarifying_questions_and_mirroring():
    ...

def test_user_steering_can_lighten_friction_inside_policy_bounds():
    ...
```

### Task 6: Interfaces And Legacy Integration

Split into smaller plans before implementation:

```text
2026-05-18-aitp-v5-cli-mcp-plan.md
2026-05-18-aitp-v5-hooks-plan.md
2026-05-18-aitp-v5-legacy-bridge-plan.md
2026-05-18-aitp-v5-domain-tools-plan.md
```

Do not implement all interface layers in one commit.

## Self-Review

Spec coverage:

- Big-step architecture is covered by the 13 phases.
- Detailed immediate implementation is covered by Tasks 1-5.
- MCP, CLI, hooks, skills, subagents, legacy bridge, and domain tools are represented.
- Human interaction and teacher/student/collaborator modes are represented by Phase 5.
- Self-evolution and over-harnessing are represented by Phases 2-3.

Placeholder scan:

- No `TBD` or `TODO` remains.
- Later broad phases intentionally defer implementation by requiring separate plans before code, because implementing all interfaces in one plan would be too large and risky.

Type consistency:

- Execution brief, risk assessment, action budget, and trust cards use existing v5 names.
- New names are introduced as future modules and test files.
