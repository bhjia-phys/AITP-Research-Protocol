# Closed-Loop Protocol

Domain: Point (Closed-Loop State Machine)
Authority: subordinate to AITP SPEC S7.
Merges: ROUTING_POLICY.md, RESEARCH_EXECUTION_GUARDRAILS.md.

---

## CL1. Role

The closed-loop state machine is the execution engine within each topic loop.
It implements the cycle: select_route -> materialize_task -> ingest_result ->
dispatch_execution_task -> await_external_result.

Every cycle must produce at least one durable artifact. The loop may not run
indefinitely without a human checkpoint.

## CL2. Cycle Phases

### select_route

Inputs:
- topic state,
- research question contract,
- control note (if present),
- pending decisions,
- mode envelope constraints,
- unfinished work index.

Process:
1. Load runtime contract (`runtime_protocol.generated.json`) for mode-based
   action type preferences.
2. Load any frozen decision contract (`next_action_decision.contract.json`)
   that may override heuristic routing.
3. Check for active popups (popup gate protocol).
4. Load control note if present — control note overrides heuristic routing.
5. Determine current mode and allowed transitions.
6. Evaluate unfinished work items.
7. Select route: what mode, what layer, what action type, what rationale.

Output:
- route decision with: mode, layer, action, rationale,
- trigger state for progressive disclosure,
- any mandatory deeper reads.

Routing modes:
- `heuristic` — Brain selects based on topic state and research judgment.
- `control_note` — human override through control note.
- `declared_contract` — declarative action contract specifies the action.
- `decision_contract` — frozen next-action decision contract overrides routing.

### materialize_task

Inputs:
- route decision from select_route,
- source material (L0 sources, L1 analysis, L3 candidates),
- previous results,
- validation plan if entering verify mode.

Process:
1. Translate route decision into a concrete action.
2. Resolve research mode profile: `research_mode`, `executor_kind`,
   `reasoning_profile` (see CL8).
3. Prepare inputs: gather source material, load context.
4. Set up validation plan with pass/failure criteria.
5. Determine if the action is auto-runnable or needs human approval.

Output:
- materialized task: action description, inputs, expected outputs,
- research mode profile fields,
- execution plan if entering L4 (lane, runtime target, resource scale),
- auto-runnable flag.

Guardrails:
- Do not materialize tasks that violate the current mode envelope.
- Do not skip required writeback from the previous cycle.
- Do not create tasks that depend on unresolved blockers.

### ingest_result

Inputs:
- task result (from agent execution or external backend),
- validation criteria from materialize_task.

Process:
1. Receive the result.
2. Classify result status:
   - `success` — action completed, result usable.
   - `partial` — action produced usable fragments but gaps remain.
   - `failed` — action did not produce usable results.
   - Additionally, `contradiction_detected` may be set as a boolean flag on
     any result status.
3. Determine routing decision:
   - `keep` — result is good, continue to next cycle or promotion.
   - `revise` — result needs revision, return to L3-A.
   - `discard` — result is not usable, remove and re-plan.
   - `defer` — result cannot be acted on now, buffer for later.
4. Produce at least one durable artifact from the result.
5. If `contradiction_detected`: route to gap writeback (CL5) and gap recovery.

Output:
- classified result with status and optional flags,
- routing decision (keep / revise / discard / defer),
- durable artifacts (L3 run records, L4 trust audits, gap records, etc.),
- updated unfinished work index.

### dispatch_execution_task

Inputs:
- materialized task ready for execution,
- execution target (local agent or external backend).

Process:
1. Dispatch the task to the execution target.
2. Record dispatch state.

Output:
- dispatch receipt.

### await_external_result

Inputs:
- external execution task description,
- timeout and failure conditions.

Process:
1. Suspend the loop.
2. Track timeout, failure, and re-entry conditions.
3. When result arrives: return to ingest_result.
4. On timeout: classify as timeout, return to ingest_result.

Output:
- external result or timeout/failure classification.

## CL3. Loop Constraints

- Each cycle produces at least one durable artifact.
- The loop may not run indefinitely without a human checkpoint.
- Stuckness detection triggers escalation, not silent retry.
- The loop respects the current mode envelope.
- Control notes override heuristic routing within the cycle.
- No cycle may skip required writeback from the previous cycle.

## CL4. Research Execution Guardrails

### Bounded Action Packets

Every action in the loop must be bounded:
- clear scope (what is being done),
- clear deliverables (what will be produced),
- clear exit conditions (when the action is done),
- clear resource limits (how much time/computation is allowed).

### Forbidden Proxies

The loop must not use the following as evidence:
- LLM confidence as a substitute for validation,
- coverage as a substitute for correctness,
- narrative plausibility as a substitute for proof,
- source count as a substitute for source quality,
- past success as a guarantee of current validity.

### Stuckness Detection

The loop monitors for:
- repeated failures on the same action (threshold: 3),
- no durable artifact produced in N cycles (threshold: configurable),
- unresolved blockers that persist across sessions,
- mode transitions that cycle without progress.

When stuckness is detected:
1. Record the stuckness signal.
2. Attempt one focused diagnosis (identify root cause).
3. If the root cause is fixable within the loop, fix it.
4. If not, escalate to the human with a clear summary.

## CL5. Follow-up Gap Writeback System

When a gap is discovered during result ingestion or contradiction detection:

1. Normalize the gap entry:
   - `gap_kind` — missing_source / missing_derivation / missing_capability /
     contradiction.
   - `return_to_stage` — which loop phase to resume from.
   - `reopen_conditions` — conditions under which this gap should be reopened.
   - `suggested_queries` — search queries for follow-up investigation.
   - `theorem_family_ids` — affected theorem families.
   - `affected_unit_ids` — affected L2/L3 units.

2. Validate the gap entry against the schema.

3. Persist to the follow-up gap register.

4. Route the gap:
   - `missing_source` -> spawn literature follow-up query (CL6) or child topic.
   - `missing_derivation` -> queue derivation action.
   - `missing_capability` -> enter capability loop.
   - `contradiction` -> open conflict record, route to gap recovery.

This system ensures that gaps discovered during execution are never silently
lost and always have a clear re-entry path.

## CL6. Literature Follow-up Query System

When a gap requires new source material or a contradiction suggests missing
literature:

1. Build a follow-up query:
   - `query_text` — search terms.
   - `priority` — urgency relative to other pending queries.
   - `target_source_type` — what kind of source is needed.
   - `trigger_flags` — conditions that activate this query.

2. Persist the query to the literature follow-up register.

3. Results may:
   - enrich the current topic's L0 source layer,
   - spawn a child topic for deeper investigation,
   - resolve a contradiction and close the gap.

## CL7. Decision Contract System

Two contract mechanisms override heuristic routing:

### Declared Action Contract
A declarative contract that specifies the exact next action to take. Used when
the routing is known in advance (e.g., control note specifies "run L4 validation
on candidate X").

### Frozen Decision Contract
A `next_action_decision.contract.json` file that persists a routing decision
across cycles. Used when:
- a decision was made in a previous cycle but execution was deferred,
- a control note or human directive needs to survive across sessions,
- a specific action ordering must be maintained.

Frozen contracts take precedence over heuristic routing but yield to control
notes.

## CL8. Research Mode Profiles

Every route and task carries a resolved research mode profile:

| Field | Purpose |
|-------|---------|
| `research_mode` | Core mode from the mode envelope |
| `executor_kind` | Execution target (local, external, hybrid) |
| `reasoning_profile` | Depth of reasoning required |
| `research_mode_profile_path` | Path to the full profile definition |

Research mode profiles are resolved during materialize_task via
`resolve_task_research_profile()`. They shape:
- which actions are preferred in the current mode,
- how deep the agent should reason,
- what execution target to use.

The runtime contract (`runtime_protocol.generated.json`) specifies
`runtime_mode`, `active_submode`, and `transition_posture` which feed into
action type preferences during select_route.

## CL9. Post-Promotion Lifecycle

After a candidate is promoted, the orchestrator handles post-promotion
follow-up:

1. **Post-promotion formalization followup** — if the promoted content has
   theory-packet artifacts, schedule formalization work.

2. **Blocker route choices** — resolve any blockers that were waiting on the
   promotion.

3. **Proof repair reviews** — if the promotion involved proof-level content,
   schedule a proof repair review.

4. **Return to loop** — continue the topic lifecycle with updated state.

This ensures promotion is not a terminal event but a lifecycle transition
that triggers follow-up work.

## CL10. Implementation Status

### Currently implemented
- Core 5-phase cycle structure (select_route, materialize_task, ingest_result,
  dispatch_execution_task, await_external_result).
- Result classification (success/failed/partial + contradiction_detected flag).
- Ingest routing (keep/revise/discard/defer).
- Routing modes (heuristic, control_note, declared_contract, decision_contract).
- Follow-up gap writeback system (CL5).
- Literature follow-up query system (CL6).
- Decision contract system (CL7).
- Runtime contract mode-based action preferences.
- Research mode profiles (CL8).
- Post-promotion lifecycle (CL9).
- Compatibility projection path system (runtime/topics/ <-> topics/runtime/).

### Not yet implemented
- Popup gate check at select_route (step 3).
- Mode envelope validation at materialize_task.
- Previous-cycle writeback enforcement.
- Stuckness detection system (CL4).
- await_external_result timeout tracking.
- Forbidden proxies guardrail enforcement (CL4).
- Human checkpoint cycle limit enforcement.

## CL11. Script Boundary

The closed-loop cycle is implemented in:
- `runtime/scripts/orchestrate_topic.py` — master orchestrator,
- `runtime/scripts/decide_next_action.py` — next-action decision,
- `runtime/scripts/closed_loop_v1.py` — closed-loop state machine.

Scripts may:
- materialize state, build projections, compute triggers.
- determine auto-runnable status for actions.
- apply heuristic routing when no control note exists.

Scripts may NOT:
- decide that validation is complete without declared criteria being met,
- silently weaken validation criteria,
- override a human decision,
- skip required writeback.
