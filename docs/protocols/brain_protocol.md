# Brain Protocol

Domain: Brain
Authority: subordinate to AITP SPEC S4.
Merges: AUTONOMY_AND_OPERATOR_MODEL, SESSION_CHRONICLE_PROTOCOL,
TOPIC_COMPLETION_PROTOCOL, PROGRESSIVE_DISCLOSURE_PROTOCOL,
MODE_AND_LAYER_OPERATING_MODEL, LIGHTWEIGHT_RUNTIME_PROFILE.

---

## B1. Role

The Brain is the global orchestrator that the AI agent permanently resides in.
It is NOT a content layer. It does not store knowledge. It routes, coordinates,
and manages the lifecycle of topics across the content layers (L0-L4).

The Brain owns:

1. topic lifecycle management,
2. cross-topic scheduling and dependency routing,
3. human interaction gates (popups, decisions, checkpoints),
4. session continuity and handoff,
5. collaborator memory and strategy memory,
6. the control plane (pause, redirect, scope changes),
7. progressive disclosure of protocol surfaces.

## B2. Topic Lifecycle

Every topic follows the same lifecycle:

```
bootstrap -> loop -> status -> verify -> promote -> complete
```

### bootstrap

- Receive the human's initial request.
- Run clarification if scope, assumptions, or target claims are vague.
- Create the topic shell: research question contract, topic state, operator
  console, control note, runtime bundle.
- Register L0 sources if provided.
- Determine initial mode (discussion by default).

Clarification rules:
- Currently implemented as a one-shot model: `needs_clarification` or
  `approved_for_execution`.
- Multi-round clarification (at most 3 rounds, 1-3 questions per round) is
  a target enhancement.
- Prefer questions that remove the biggest ambiguity first.
- If the human says "just go" or "skip clarification", proceed and mark
  missing fields as `clarification_deferred: true`.

### loop

The loop stage is driven by the mode envelope (see `mode_envelope_protocol.md`).
The Brain dispatches to L layers based on the current mode:

**When mode = explore:**
- Dispatch to L0 (source discovery), L1 (reading notes), L3-I (idea recording).
- Compare ideas with L2 knowledge to assess novelty.
- Produce at least one L3-I idea record per cycle.
- Transition to `learn` when ideas are ready for deep study.

**When mode = learn:**
- Dispatch to L0/L1 (deep reading), L3-P (reproduction/derivation plan),
  L3-A (execute plan), L4 (validate).
- The L3-A <-> L4 loop drives verification of known results.
- Verified results promote to L2.
- Transition to `implement` when understanding is sufficient for new work,
  or back to `explore` if gaps are found.

**When mode = implement:**
- Dispatch to L3-I (refine idea), L3-P (create plan), L3-A (execute),
  L4 (validate).
- The L3-A <-> L4 loop drives discovery.
- New conclusions stay in L3 for human review.
- Transition to `explore` when results suggest new questions,
  or back to `learn` if knowledge gaps are revealed.

General loop rules:
- Execute the closed-loop cycle: select_route -> materialize_task ->
  ingest_result -> await_external_result.
- Respect the current mode envelope.
- Produce at least one durable artifact per cycle.
- Detect stuckness and escalate rather than silently retry.
- Re-checkpoint when the plan boundary is reached.

### status

- At any point, the operator may request a status snapshot.
- The Brain produces: topic dashboard, promotion readiness report, gap map,
  unfinished work index, pending decisions.

### verify

- When the mode is `verify`, the Brain enters L4 validation.
- L4 results return through L3-R (never directly to L2).
- Validation may trigger follow-up sub-topics for missing gaps.

### promote

- When candidates pass validation, the Brain enters the promotion pipeline.
- The 4-stage counting state machine governs advancement.
- Stage 4 (promoted) always requires human approval.

### complete

- A topic is complete when:
  - the research question is answered, or
  - the topic ends with a durable deferred/rejected conclusion, or
  - a hard blocker requires a human checkpoint that the human declines to
    resolve.

Completion requirements:
- a source-map or topic-charter backbone,
- stable regression suite manifest,
- recent regression run logs,
- durable writeback from non-pass results,
- session chronicle for the final session.

Completion states:

| State | Meaning |
|-------|---------|
| `not_assessed` | No completion judgment yet |
| `gap-aware` | Branch can state what is missing |
| `regression-seeded` | Branch owns stable question/oracle surface |
| `regression-stable` | Flagship questions pass without hidden collapse |
| `promotion-ready` | Regression surface is recent and blocker-clear |
| `promotion-blocked` | Candidate carries blocker or split debt |

## B3. Multi-Topic Management

### Topic Index

The Brain maintains a global topic registry (`topic_index.jsonl`) and an active
topics list (`active_topics.json`).

### Topic Dependency DAG

Topics may have dependencies on each other:

- Topic A blocks Topic B when B cannot proceed until A delivers a result.
- The Brain must respect blocking relationships when scheduling.
- Cycles in the dependency graph are a protocol violation. Cycle detection
  is required but not yet implemented — currently only `dependency_blocked`
  status is computed.

### Current Topic Resolution

When the human says "continue this topic" or "current topic", the Brain resolves:

1. explicit topic slug if provided,
2. current_topic.json if it exists,
3. most recently active topic if no explicit pointer.

### Multi-Topic Scheduling

- Active topics may run in parallel if they do not block each other.
- The Brain may switch between topics within a session when the human requests
  it or when one topic is awaiting external results.
- Topic switches must preserve the state of the paused topic.

## B4. Session Continuity

### Session Chronicle

Every session produces a chronicle: a human-readable narrative summary.

The chronicle answers: "what happened, why, and what is next?"

Required sections:
- Summary (2-3 sentences),
- Starting State,
- Actions Taken,
- Decisions Made,
- Problems Encountered,
- Ending State,
- Next Steps,
- Open Decision Points.

Chronicles are stored at:
`runtime/topics/<topic_slug>/chronicles/<chronicle_id>.md`
with a JSON companion.

### Resume State

When a session resumes a topic, the Brain loads:
- topic_state.json,
- operator_console.md,
- unfinished_work.json,
- pending_decisions.json,
- the latest session chronicle,
- the runtime bundle.

The operator_console.md is the immediate execution contract: "do now / do not /
escalate."

### Trajectory Memory

The Brain maintains cross-session research trajectory tracking:
- momentum signals (progress is being made),
- stuckness signals (repeated failures without progress),
- surprise signals (unexpected results that change direction).

These signals shape future routing without replacing human judgment.

## B5. Collaborator Memory

### Collaborator Profile

The Brain maintains a profile that learns from the human collaborator over time:
- research taste and preferred formalisms,
- physical intuition patterns,
- which validation approaches they prefer,
- what counts as "interesting" vs "pedantic",
- which research modes they actually use in practice.

### Strategy Memory

The Brain maintains a record of helpful and harmful patterns:
- approaches that succeeded in past topics,
- approaches that failed and should be avoided,
- domain-specific patterns that transfer across topics.

Strategy memory entries follow the pattern:
- situation description,
- what was tried,
- outcome (helpful / harmful / neutral),
- transferability assessment.

### Mode Learning

The Brain tracks which mode transitions and route patterns work best for
the current collaborator. Over time, this shapes default routing without
removing the human's ability to override.

## B6. Control Plane

The human may intervene at any point through the control plane:

### Control Note

The human may issue a control note that:
- redirects research direction,
- changes scope or assumptions,
- pauses the topic,
- tightens or loosens validation criteria.

Control notes override heuristic routing. When a control note is present,
the Brain must load it before selecting the next action.

### Innovation Direction

The human may update the innovation direction:
- novelty level (incremental / moderate / breakthrough),
- scope expansion or contraction,
- acceptance criteria changes.

### Popup Gate Protocol

At the start of every topic interaction, the Brain checks for active popups:

1. Call the popup gate for the current topic.
2. If no popup is active, continue normally.
3. If a popup is active, STOP all other work and present it to the human.
4. The human chooses an option, the Brain resolves the popup, and only then
   continues.

This applies:
- at the very start of every topic-bound interaction,
- after any loop, next, or status return,
- whenever the user says anything that might advance or alter topic state.

## B7. Progressive Disclosure

The Brain does not load all protocol surfaces at once. It uses lossless
progressive disclosure: defer detail, but never weaken or hide governance.

### Four Execution Tiers

| Tier | What It Contains |
|------|-----------------|
| `minimal_execution_brief` | Current stage, selected action, allowed/blocked work, files to open now |
| `trigger_rules` | Which situations require deeper reads, which files become mandatory |
| `protocol_slice` | Smallest deeper subset relevant to the current trigger |
| `full_governance` | Complete contract surface for disputes, audits, edge cases |

### Canonical Triggers

| Trigger | When It Fires | Mandatory Deeper Reads |
|---------|---------------|----------------------|
| `decision_override_present` | Control note overrides heuristic routing | Control note, next-action decision, queue contract |
| `promotion_intent` | Work could create/revise L2 writeback | Promotion gate, coverage artifacts, validation surface |
| `non_trivial_consultation` | L2 consultation changes terminology or shape | Consultation protocol, topic consultation index |
| `capability_gap_blocker` | Missing workflows block continuation | Capability protocol, skill discovery, queue/follow-up surfaces |
| `trust_missing` | Operation reused without satisfied trust gate | Trust audit, baseline artifacts, operation manifests |
| `contradiction_detected` | Validation or fusion exposes contradiction | Validation decisions, conflict records, gap recovery protocol |
| `proof_completion_review` | Proof-heavy work has theory-packet artifacts | Theory-packet surfaces, proof obligation protocol |
| `verification_route_selection` | Selecting closed-loop validation route | Validation route, execution task, verification bridge |

### Mandatory Top-Level Fields

The top disclosure tier must always include:
- current stage,
- selected action or declared absence,
- immediate allowed work,
- immediate blocked work,
- visible research-flow guardrails,
- active hard constraints,
- declared escalation triggers,
- exact deeper file paths.

If these are missing, the summary is too compressed to count as safe AITP
runtime guidance.

## B8. Lightweight Runtime Profile

When the Brain detects that a topic does not need the full protocol surface,
it may activate a lightweight profile:

- reduced artifact footprint,
- simplified mode transitions,
- abbreviated validation requirements,
- but still respecting core Charter constraints (evidence discipline, no
  silent promotion, human gates at L2).

The lightweight profile is NOT a shortcut around the Charter. It is a
proportional response to topic complexity.

## B9. Capability Loop

The Brain may improve its own working surface when a missing capability is
the actual blocker.

Allowed self-modification targets:
- `research/knowledge-hub/runtime/`
- `research/knowledge-hub/validation/`
- `research/adapters/`
- reviewed local skills.

Required rule:
- every capability change must leave a durable artifact on disk,
- every change must be summarized in the final output or handoff note,
- silent framework drift is not allowed.

## B10. Output Contract

The Brain does not promise that every run ends in L2.

A valid final output may land in:
- L1 when the work is still source-bound,
- L2 when the result is reusable and validated,
- L3 when the run remains exploratory,
- L4 when the main value is an execution-backed adjudication.

The final response should state:
1. which layer(s) were updated,
2. key artifact paths or the topic dashboard (which reports target layers),
3. why the output belongs there instead of a higher layer.

Currently, the topic dashboard reports target layers. An explicit per-layer
artifact path contract per B10 is a target enhancement.

## B11. Human Edit Rights

The human may edit any layer at any time:
- L0 to add or remove sources,
- L1 to refine source-bound understanding,
- L2 to correct or refine reusable memory,
- L3 to reshape questions, conjectures, and next actions,
- L4 control notes to tighten adjudication criteria,
- runtime artifacts to clarify operator-facing intent.

The Brain treats these edits as first-class inputs, not anomalies.

## B12. Safety Boundary

The Brain may NOT silently do the following without a human checkpoint:
- redefine the layer model,
- change L2 object-family semantics,
- promote a high-impact scientific claim with unresolved scope,
- install third-party capabilities into global paths,
- perform irreversible external actions not requested by the human.

## B13. Script Boundary

Scripts may:
- materialize state artifacts,
- compute trigger state from durable artifacts,
- generate projections, indexes, and dashboard renders,
- scaffold follow-up return packets,
- gate auto-promotion against declared policy.

Scripts may NOT decide:
- whether a proof is genuinely complete,
- whether two theorem families are truly identical,
- whether a gap is substantively resolved,
- whether proxy evidence is good enough to count as validation,
- whether a candidate is scientifically mature merely because it was generated.

Those judgments remain protocol-governed research work.
