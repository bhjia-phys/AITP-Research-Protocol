---
name: aitp-runtime
description: Codex app runtime skill for continuing an AITP v5 theoretical-physics topic through typed claims, evidence, validation gates, and trust-controlled memory.
---

# AITP Runtime v5 In Codex App

## Mandatory First Step

For every AITP research iteration, restore the bounded Codex entry context first:

```text
aitp_v5_codex_enter(base="{{TOPICS_ROOT}}", session_id=<session-id>, request_summary=<current user request>)
aitp_v5_codex_expand(base="{{TOPICS_ROOT}}", session_id=<session-id>, expansion="brief")
aitp_v5_codex_expand(base="{{TOPICS_ROOT}}", session_id=<session-id>, expansion="relation_map")
```

The brief is the immediate execution contract. Follow `current_focus`,
`flow_profile`, `risk_assessment`, `evidence_coverage`,
`next_action_candidates`, `forbidden_now`, and `human_checkpoint`.

The claim relation map is the recovery boundary layer. Read `supported_by`,
`limited_by`, `not_tested_by`, `contradicted_by`,
`current_conclusion.can_say`, `current_conclusion.cannot_say`,
`current_blockers`, and `next_valid_actions` before deciding what the active
claim means.

Legacy stage briefs from `aitp_get_execution_brief` are compatibility
orientation only. If you are looking at `stage=L3` or `gate_status=L4`, migrate
or bind a v5 session before making scientific progress.

## Interaction Modes And Lifecycle

Use the lightest mode that preserves truth:

- Progress or prior-topic status questions are read-only. Restore the brief and
  relation map, summarize current claims, blockers, and next valid actions, and
  do not write unless the user asks for a durable handoff or resolves a human
  checkpoint.
- Generic old-knowledge or textbook questions stay outside AITP unless they
  name or affect an existing topic, claim, source, route, or gap. Topic-linked
  answers restore context first, then write only durable corrections, sources,
  gaps, or route changes.
- Light exploratory discussion is read-mostly. Do not create a topic, claim,
  or record just because an idea is interesting; wait until a route, question,
  source, artifact, result, or gap becomes durable.
- Active continuation, derivation, source reading, code/numerical execution,
  validation, contradiction handling, final synthesis, trust update, and L2
  promotion use the full typed runtime loop below.

At session start, first locate the topic/session/claim with recovery tools or a
known session id. The start itself is normally read-only; run recording
navigation only if continuation creates a durable start marker, route choice,
or handoff state that future agents must recover.

At session end, write a handoff only when new durable state exists. The handoff
should name the active claim, typed refs just created or relied on, open proof
or validation gaps, human gates, and the next valid action. Verify the handoff
or typed refs with `aitp_v5_verify_recording_effect`.

## Typed Runtime Loop

Use this loop conceptually, with the actual Codex tool names exposed in the
session:

```text
while topic is active:
  entry = aitp_v5_codex_enter(base="{{TOPICS_ROOT}}", session_id=<session-id>, request_summary=<current user request>)
  brief = aitp_v5_codex_expand(base="{{TOPICS_ROOT}}", session_id=<session-id>, expansion="brief")
  relation_map = aitp_v5_codex_expand(base="{{TOPICS_ROOT}}", session_id=<session-id>, expansion="relation_map")

  if relation_map.not_tested_by is non-empty:
    do not treat those failures as algorithm or claim evidence
    report the boundary from relation_map.current_conclusion.cannot_say
    use relation_map.current_blockers and relation_map.next_valid_actions

  if brief.human_checkpoint.needed:
    present the checkpoint plainly and wait for the user's explicit answer
    resolve it through the appropriate v5 checkpoint/trust/promotion tool
    continue

  if "policy:" or trust-changing actions appear in brief.forbidden_now:
    do not change confidence or L2 memory; collect evidence or validation first
    continue

  if evidence_coverage.missing_outputs is non-empty:
    record sources, artifacts, code state, tool runs, evidence, or validation results
    continue

  choose the top safe action from next_action_candidates
  do the physics, code, or literature work
  record durable typed results before summarizing to the user
```

## Moment Policy

AITP runtime is not a transcript logger. Record only durable research moments:

- source identity or source location becomes reusable,
- tool/code run completes and produced research-relevant output,
- artifact/report/table/plot/log/raw dump is produced,
- result, anomaly, contradiction, negative result, or failed check is observed,
- proof gap, validation gap, missing provenance, or route blocker is found,
- route is selected, pivoted, abandoned, or split,
- active claim scope/status changes are proposed,
- final answer depends on an active claim,
- trust update, promotion, or human decision is requested,
- session-end handoff creates durable state.

Do not record generic explanation, unaccepted brainstorming, repeated
summaries, tool calls that only inspect files, failed setup checks with no
research information, or old-knowledge answers that do not affect a topic.
Those remain conversation or read-only context.

Use this trigger rule:

```text
research-relevant fact changed or became durable -> classify and navigate
only the agent's local reasoning changed -> do not write
```

For those moments, use progressive navigation:

```text
aitp_v5_codex_recording_step(base="{{TOPICS_ROOT}}", session_id=<session-id>, event_type=<event>, summary=<durable moment>)
aitp_v5_codex_recording_step(base="{{TOPICS_ROOT}}", session_id=<session-id>, event_type=<event>, summary=<durable moment>, slot=<slot>)
aitp_v5_codex_record_apply(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, payload=<typed slot payload>)
```

If the classifier says `ignore` or `defer`, do not write. If the live Codex MCP
surface is stale and does not expose the recording navigator tools, use the CLI
fallback for read-only navigation and mutate only through available v5 typed
write tools.

The first navigation answer should reveal only topic/session/claim position,
first-level slots, blockers, and recommended moments. Expand exactly one slot
at a time. The slot expansion must name an existing typed write or preflight
tool, the minimum fields, known values, unknown values, and the verification
step.

`recording_navigation_state` is intentionally lightweight first-level
navigation. It uses slot counts and relation-boundary hints; it does not replace
`execution_brief` or `process_graph_slice`. Call those separately only when the
next action really needs full context.

## Record Boundaries

- Definitions and systems: `aitp_v5_record_physics_object`.
- Relations or equations: `aitp_v5_record_object_relation`.
- Papers, notes, and locations: `aitp_v5_record_reference_location` or
  `aitp_v5_register_source`.
- Source assets and reference locations are provenance/context, not claim
  support by themselves.
- Files and reports: `aitp_v5_attach_artifact`.
- Numerical or code-dependent work: code state, tool recipe, tool run, evidence.
- Checks and reviews: validation contract plus validation result when a tool run
  or explicit check exists.
- Recovery boundaries: read the claim relation map; do not write relation-map
  conclusions back as evidence unless a typed source, tool run, or validation
  result already supports that claim.
- Open theorem or review gaps: `aitp_v5_create_proof_obligation`.
- Maturity/status observations: `aitp_v5_update_claim_status`.
- Interpretation: `aitp_v5_record_sensemaking_report`, marked as orientation
  unless backed by evidence/validation.

## Legacy Topics

For older Markdown topics:

1. Use legacy aliases only to discover the slug or preserve an old topic.
2. Prefer `aitp_v5_migrate_curated_legacy_topic_to_v5` for curated known topics.
3. Use `aitp_v5_migrate_legacy_topic_to_v5` for generic preservation.
4. Continue from the v5 session id returned by migration.

Known curated migrations can be listed with:

```text
aitp_v5_list_curated_legacy_topics()
```

## Codex-Specific Interaction Rules

- Ask through Codex's normal conversation surface unless a structured
  user-input tool is explicitly available.
- Map Claude-only examples such as `AskUserQuestion` or `ToolSearch` to the
  tools actually available in Codex.
- If AITP tools are unavailable, diagnose setup before mutating topic state.

## Physics Validation Obligations

Before treating a result as strong, check whether the active claim needs:

- dimensional consistency,
- algebraic consistency,
- limiting cases and known limits,
- symmetry or Ward identity checks,
- causality, unitarity, and conservation laws where applicable,
- approximation validity and scale separation,
- numerical convergence, benchmark comparison, and error bars for computation,
- explicit mismatch or negative-result records when the result fails.

Do not bury a failed check in prose. Record it as typed protocol state.

## Fallback Diagnostics

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" brief <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "{{TOPICS_ROOT}}" relation-map <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m py_compile brain/v5/native_mcp.py brain/v5/mcp_tools.py brain/v5/brief.py
```
