# Human-Idea, AI-Execution, Human-Steering Protocol (vNext)

Status: implementation target

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

- `runtime/topics/<topic_slug>/idea_packet.json`
- `runtime/topics/<topic_slug>/idea_packet.md`

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

- `runtime/topics/<topic_slug>/operator_checkpoint.active.json`
- `runtime/topics/<topic_slug>/operator_checkpoint.active.md`
- `runtime/topics/<topic_slug>/operator_checkpoints.jsonl`

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

- `runtime/topics/<topic_slug>/innovation_direction.md`
- `runtime/topics/<topic_slug>/innovation_decisions.jsonl`
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

- `feedback/topics/<topic_slug>/runs/<run_id>/strategy_memory.jsonl`

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

Deliverables:

- topic dashboard/status improvements,
- operator-console improvements,
- stronger machine-readable topic-state fields for "last evidence return" and
  active checkpoint summary.

Acceptance:

- a later session can ask "why did this topic end up here?" and the answer can
  be built from current runtime artifacts without reconstructing old chat.

### Phase 4: Strategy Memory

Deliverables:

- run-local strategy-memory write path,
- queue/runtime retrieval path for bounded reuse,
- explicit non-promotional semantics.

Acceptance:

- successful and failed routes can influence later bounded steps without being
  confused with `L2` scientific truth.

### Phase 5: Lane-Specific Closure Exemplars

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
