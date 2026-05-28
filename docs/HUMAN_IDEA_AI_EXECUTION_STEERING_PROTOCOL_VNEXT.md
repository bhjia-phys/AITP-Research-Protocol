# Human-Idea, AI-Execution, Human-Steering Protocol (vNext)

Status: **control plane implemented** on branch `codex/aitp-v5-kernel-mvp`;
content migration is not complete until the legacy semantic review backlog is
human-reviewed.
Control-plane status: `ready`. Covered exemplar lanes: `toy_numeric`,
`semi_formal_theory`, `code_backed_algorithm`.
Blocking content backlog: `legacy_semantic_review_backlog`. Trust update
forbidden from orientation surfaces: true. Human output stability: implemented.

Scope: next-stage protocol and runtime hardening on top of existing AITP
`L0 -> L1 -> L3 -> L4 -> L2`

## 1) Goal

The near-term goal is not "full autonomous AITP".
The near-term goal is a stronger human-AI research operating model:

- the human can start from a vague but meaningful research idea,
- AITP can turn that idea into durable topic state and keep working,
- AITP pauses only at explicit human checkpoints instead of forcing constant
  supervision,
- later sessions can ask what happened, why a route was chosen, and what the
  current topic status is, using durable protocol records instead of chat
  memory.

This proposal does not replace AITP's layer ontology.
It upgrades the outer control logic and the operator-facing runtime surfaces so
AITP behaves more like a persistent theoretical-physics collaborator.

## 2) Current State

The current repository already provides:

- `L0/L1/L3/L4/L2` as the public research model,
- durable runtime topic state,
- current-topic memory and session-start routing,
- operator-facing surfaces such as `operator_console.md`,
- promotion gates, conformance audits, and gap recovery,
- Superpowers-style outer bootstrap for Codex, OpenCode, and Claude Code.

What is still missing or only partially hard-coded:

- a first-class research-intent gate for vague new ideas,
- a first-class operator-checkpoint / question surface,
- a fully unified steering surface that survives chat-native redirects,
- a stable "why is this topic in this state?" answer surface,
- stronger run-local strategy memory and later retrieval,
- lane-specific exemplar closure for numerics, semi-formal theory, and
  code-backed algorithm development.

## 3) External Design Logic To Absorb

AITP should absorb three external design lessons without replacing its own core:

### A. From Superpowers

- force the agent into the right workflow before any substantive response,
- make clarification and stop/ask behavior a hard gate rather than a style
  preference,
- use platform-native bootstrap instead of extra wrapper rituals.

### B. From get-physics-done and similar scientific workflows

- keep the local micro loop predictable:
  `discuss -> plan -> execute -> verify -> record outcome`,
- preserve benchmark and validation discipline,
- productize the runtime/install experience instead of treating it as internal
  glue.

### C. From personal literature and notebook automation

- reduce intake cold-start,
- keep source grounding explicit before idea evaluation,
- preserve notes, run artifacts, and reusable workflows as durable memory.

## 4) Compatibility Principle

Keep existing AITP core unchanged:

- layer model (`L0/L1/L3/L4/L2`),
- promotion gates,
- conformance audits,
- runtime control surfaces,
- current-topic memory,
- gap recovery and consultation.

Do not collapse AITP into a generic software-development workflow.

Absorb Superpowers at the outer discipline layer:

- gatekeeper-first startup,
- hard clarification gates,
- hard stop/ask rules,
- native plugin/bootstrap surfaces.

Keep AITP-specific research state in the inner runtime:

- topic state,
- runtime protocol bundle,
- operator console,
- promotion and consultation artifacts,
- gap, follow-up, and reintegration surfaces.

Topic-owned research state should converge on the topic-owned truth root:

- `topics/<topic_slug>/...`

Within that truth root, Markdown is the human authority for operator-facing
state, steering, review, and continuation surfaces. JSON remains the machine-facing companion for structured runtime payloads, ledgers, schemas, and adapter/resolver inputs.

For run-local `L3 -> L4 -> L3` iteration loops, one research `run` may contain
multiple plan/execute/return/synthesis cycles. Human review should follow a
Markdown-first journal and per-iteration Markdown records, while JSON remains a
thin companion for status, paths, replay, and machine routing.

## 5) Required Workstreams

### 5.1 Research Intent Gate

Objective: allow humans to start from natural-language ideas without forcing
them to manually define the whole topic shell upfront.

Required behavior:

- if the request is a new topic or a vague research idea, AITP must not jump
  straight into `L3/L4` execution;
- it must first clarify novelty target, scope, non-goals, and initial evidence
  bar;
- only after that gate passes should the topic be treated as execution-ready.

Required artifacts:

- `topics/<topic_slug>/runtime/idea_packet.json`
- `topics/<topic_slug>/runtime/idea_packet.md`

Minimum contents:

- initial idea statement,
- novelty target,
- non-goals,
- required first validation route,
- initial evidence bar,
- status: `needs_clarification | approved_for_execution | deferred`.

Routing rule:

- current-topic continuation should bypass this gate unless the operator has
  explicitly reopened the topic definition;
- new-topic or idea-first requests should enter this gate before the normal
  bounded loop continues.

### 5.2 Operator Checkpoint Protocol

Objective: make "what AITP needs from the human right now" a first-class
protocol surface.

Required behavior:

- when the runtime hits a true human checkpoint, it should produce a durable
  operator question instead of leaving the need scattered across queue text,
  control notes, or prose;
- the operator question should survive restarts and be answerable later.

Required artifacts:

- `topics/<topic_slug>/runtime/operator_checkpoint.active.json`
- `topics/<topic_slug>/runtime/operator_checkpoint.active.md`
- `topics/<topic_slug>/runtime/operator_checkpoints.jsonl`

Checkpoint kinds must at minimum include:

- scope ambiguity,
- novelty-direction choice,
- benchmark or validation-route choice,
- resource/risk limit choice,
- contradiction adjudication choice,
- promotion approval,
- stop/continue/branch/redirect decision.

Required answer statuses:

- `requested`
- `answered`
- `superseded`
- `cancelled`

### 5.3 Steering Surface Hardening

Objective: make human steering durable and authoritative before the loop
continues.

Required behavior:

- natural-language steering such as "继续这个 topic，但方向改成 X" must materialize
  durable steering state before deeper execution;
- `innovation_direction.md` and `control_note` should not remain optional hints
  when steering materially changes the route;
- the runtime should refuse to continue deeper work when a steering redirect has
  been detected but not yet materialized.

Required artifacts:

- `topics/<topic_slug>/runtime/innovation_direction.md`
- `topics/<topic_slug>/runtime/innovation_decisions.jsonl`
- existing `control_note.*`

Division of responsibility:

- `innovation_direction.md`
  - long-lived novelty target, scope, and acceptance posture
- `innovation_decisions.jsonl`
  - append-only steering history
- `control_note`
  - immediate bounded redirect, pause, or override instruction

### 5.4 Explainability And Topic Status Surface

Objective: make it easy for a later human or agent to ask "what happened, why,
and what is the topic status now?"

Required behavior:

- topic runtime surfaces must answer, without reverse engineering logs:
  - where the topic currently is,
  - why it is there,
  - what the last meaningful evidence return was,
  - what the next bounded action is,
  - what AITP still needs from the human.

Required surfaces:

- existing `topic_state.json`
- existing `operator_console.md`
- existing `topic_dashboard.md`
- existing `runtime_protocol.generated.md`
- existing `session_start.generated.md`

Required hardening:

- `topic_dashboard.md` should explicitly expose last evidence return, current
  route choice, blocker summary, and active human checkpoint when present;
- `session_start.generated.md` should render the active final-output profile,
  strategy-memory next-time rules, lane exemplar trust boundaries, and any
  required operator checkpoint as a stable resume-first handoff surface;
- compact status calls should return a small continuation payload while still
  writing the full topic-status files, so chat-native hosts do not need to
  ingest the entire machine `topic_state.json`;
- `topic_state.json` should remain the machine-readable answer surface;
- `operator_console.md` should remain the human-facing action and checkpoint
  surface.

### 5.5 Strategy Memory

Objective: keep route memory from each run without confusing it with validated
scientific knowledge.

Required behavior:

- each meaningful run may record what route helped, failed, or was neutral;
- future queue selection may consult this memory;
- strategy memory must remain non-promotional unless separately adjudicated.

Required artifacts:

- `topics/<topic_slug>/L3/runs/<run_id>/strategy_memory.jsonl`

Minimum strategy types:

- `search_route`
- `verification_guardrail`
- `debug_pattern`
- `resource_plan`
- `scope_control`

### 5.6 Adapter And Bootstrap Conformance

Objective: make Codex, OpenCode, and Claude Code all feel like "AITP just
knows how to start correctly".

Required behavior:

- `using-aitp` must remain the total entry gate for theory-governed work;
- the adapter must inject it before substantive responses;
- if a vague idea might require the research-intent gate, the adapter must not
  let the runtime skip directly to execution.

Required install behavior:

- Codex: skill discovery
- OpenCode: plugin bootstrap
- Claude Code: SessionStart bootstrap

Compatibility behavior:

- old wrappers and command bundles remain fallback-only,
- public docs should keep teaching natural-language-first behavior.

## 6) Ordered Implementation Sequence

Implementation should proceed in this order.
Do not start with strategy memory or lane exemplars before the control logic is
hard enough to support them.

### Phase 1: Research Intent Gate + Steering Hardening

Status: **implemented.** `aitp_v5_record_research_intent_packet` and
`aitp_v5_materialize_steering_redirect` are production surfaces with
CLI/MCP/runtime entrypoints. Runtime entrypoint catalog validates all
entrypoints against real CLI/MCP targets.

Deliverables:

- `idea_packet` artifacts,
- durable innovation-direction materialization,
- runtime rule that steering redirects must land on disk before loop
  continuation.

Acceptance:

- a new vague idea request does not jump directly to execution;
- a redirect request auto-updates steering artifacts before the next bounded
  step;
- current-topic continuation still feels natural-language first.

### Phase 2: Operator Checkpoint Protocol

Status: **implemented.** `aitp_v5_request_operator_checkpoint` and
`aitp_v5_answer_operator_checkpoint` are production surfaces.
`session_start.generated.md` renders active checkpoint as stable resume handoff.

Deliverables:

- active operator checkpoint artifact,
- checkpoint ledger,
- runtime selection logic that surfaces a checkpoint instead of silently
  guessing when a true human choice is required.

Acceptance:

- the runtime can answer "what do you need from me right now?" from durable
  files;
- a checkpoint can be answered later without losing continuity.

### Phase 3: Explainability And Status Hardening

Status: **implemented.** `topic_state.json`, `operator_console.md`,
`topic_dashboard.md`, `runtime_protocol.generated.md`,
`session_start.generated.md` are production surfaces.
`aitp-v5 status topic <session-id> --compact` returns compact
`topic_status_bundle_progress` while writing full files on disk.
`workspace_refresh_progress` returns lightweight chat output.
Goal continuation audit packets (`aitp-v5 goal write/latest/list`) enable
cross-session context recovery.

Deliverables:

- topic dashboard/status improvements,
- operator-console improvements,
- stronger machine-readable topic-state fields for "last evidence return" and
  active checkpoint summary.

Acceptance:

- a later session can ask "why did this topic end up here?" and the answer can
  be built from current runtime artifacts without reconstructing old chat.

### 5.4.1 Run-local iteration continuity

Objective: make one research run inspectable when `L3` and `L4` iterate more
than once before a staging or promotion decision.

Required behavior:

- one `run` may include multiple `L3 plan -> L4 execution -> L3 synthesis`
  cycles;
- the human should be able to review that whole run without reverse
  engineering multiple unrelated machine artifacts;
- the review surface should not flatten all cycles into one blob.

Preferred artifacts:

- `topics/<topic_slug>/L3/runs/<run_id>/iteration_journal.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iteration_journal.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/plan.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/plan.contract.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l4_return.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l4_return.json`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l3_synthesis.md`
- `topics/<topic_slug>/L3/runs/<run_id>/iterations/<iteration_id>/l3_synthesis.json`

Rule:

- Markdown owns the review narrative.
- JSON stores only thin machine contracts for status, artifact refs, replay,
  and later automation.

### Phase 4: Strategy Memory

Status: **implemented.** `aitp_v5_record_strategy_memory` and
`session_start.generated.md` strategy-rules section are production surfaces.
Strategy types include scope_control, verification_guardrail, resource_plan,
search_route, debug_pattern.

Deliverables:

- run-local strategy-memory write path,
- queue/runtime retrieval path for bounded reuse,
- explicit non-promotional semantics.

Acceptance:

- successful and failed routes can influence later bounded steps without being
  confused with `L2` scientific truth.

### Phase 5: Lane-Specific Closure Exemplars

Status: **implemented.** Covered lanes: `toy_numeric`, `semi_formal_theory`,
`code_backed_algorithm`. `aitp_v5_record_lane_exemplar` and
`aitp_v5_build_lane_exemplar_manifest` are production surfaces.
`session_start.generated.md` renders lane exemplars with trust boundaries.

Deliverables:

- one stronger toy-model numeric exemplar,
- one semi-formal theory exemplar with explicit trust boundary,
- one code-backed algorithm-development exemplar with reusable workflow
  writeback.

Acceptance:

- each lane has at least one bounded exemplar that shows how the new gates and
  operator surfaces behave in practice.

## 7) Mandatory Gates

Gate `G0` Research intent gate:

- required for new or materially redefined topics.

Gate `G1` Source grounding gate:

- nontrivial claims require `L0/L1` anchors before deeper execution.

Gate `G2` Executability gate:

- selected bounded action must declare deliverables, checks, and stop rules.

Gate `G3` Verification gate:

- execution results must carry method checks and confidence bounds.

Gate `G4` Human steering gate:

- explicit continue, branch, redirect, or stop decision when a true operator
  choice is needed.

Gate `G5` Promotion gate:

- only after `L4` adjudication and promotion policy compliance.

## 8) Success Criteria

This vNext work is successful when:

- humans can start from ideas instead of fully specified topics,
- AITP can continue bounded research work without constant supervision,
- human checkpoints are durable and visible rather than implicit,
- later status questions can be answered from topic runtime artifacts,
- natural-language runtime entry remains as smooth as Superpowers,
- AITP still preserves its own research-state model instead of collapsing into
  a generic coding workflow.

## 9) Non-goals

- replacing AITP layers with generic milestone software,
- treating design/spec/plan docs as sufficient replacement for research runtime
  state,
- auto-promoting high-impact theory claims without explicit gates,
- hiding checkpoint or steering logic inside opaque orchestration code,
- claiming full autonomous AITP before the human-checkpoint loop is robust.

## 10) Relation To Existing AITP Docs

This document extends, and does not replace:

- `research/knowledge-hub/AUTONOMY_AND_OPERATOR_MODEL.md`
- `research/knowledge-hub/RESEARCH_EXECUTION_GUARDRAILS.md`
- `research/knowledge-hub/runtime/CONTROL_NOTE_CONTRACT.md`
- `research/knowledge-hub/runtime/README.md`
- `docs/LESSONS_FROM_GET_PHYSICS_DONE.md`

## 11) Post-Implementation Status (2026-05-28)

All five control-plane phases are implemented and tested on branch
`codex/aitp-v5-kernel-mvp`; this does not prove migrated legacy content is
semantically lossless.

### Implemented additional surfaces beyond original spec

- **Goal continuation audit packets** (`aitp-v5 goal write/latest/list`):
  cross-session context recovery via local `.aitp/surfaces/goal_continuation/`
  JSON+Markdown packets. Packets include structured commit ranges, commit
  metadata, changed files, verification, smoke runs, audit commands, next
  actions, trust boundaries, and blocking backlog. Orientation-only, no kernel
  state mutation.
- **Compact session-start refresh** (`workspace_refresh_progress`):
  Claude/Kimi SessionStart hooks return lightweight projection instead of
  full `workspace_refresh_bundle`. Full topic-status files still written to disk.
- **Compact topic status handoff** (`aitp-v5 status topic --compact`):
  returns `topic_status_bundle_progress` with handoff paths, not full state.
- **Legacy semantic review backlog system**:
  full backlog triage, repair, review queue, needs-revision basis,
  source reconstruction, and human checkpoint backlog surfaces.
  All reviewed via typed records with explicit review basis.
  Remains blocking until human-reviewed.

### Current blocking state

- `completion_status`: `kernel_ready_content_backlog`
- `blocking_gaps`: `["legacy_semantic_review_backlog"]`
- `can_update_claim_trust`: false
- `semantic_lossless_proven`: false
- `control_plane_status`: ready
- `adapter_bootstrap_conformance`: `priority_hosts_ready_opencode_deferred`

### Known remaining work

1. **Legacy semantic review backlog** (18 topics, 16 needs_revision, 2 inconclusive):
   each item requires human-reviewed typed semantic review result before
   the backlog clears. This cannot be automated away.
2. **Theory workspace AITP update**: sync kernel worktree changes to
   `D:/BaiduSyncdisk/Theoretical-Physics` AITP installation.
3. **Literature intake optimization for qsgw dual-lane workflow**:
   ensure literature intake templates correctly reference final/diagnostic
   lane boundaries and usable_for_final provenance guards.
4. **OpenCode adapter**: deferred until OpenCode hook model stabilizes.
