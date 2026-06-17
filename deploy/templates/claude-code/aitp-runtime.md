---
name: aitp-runtime
description: Use after AITP v5 routing has claimed a theoretical-physics task; continue through typed records, validation gates, and trust-controlled memory.
---

# AITP Runtime v5 - Claude Code

## Runtime Loop

Every real research turn starts by restoring typed state:

```text
brief = mcp__aitp__aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
relation_map = mcp__aitp__aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
```

Then decide the next action from the brief:

- `current_focus`: active claim, confidence state, evidence profile, uncertainty
- `flow_profile`: fluid/guided/rigorous/adversarial route
- `risk_assessment` and `action_budget`: how heavy evidence must be
- `evidence_coverage`: missing required outputs
- `next_action_candidates`: safe next actions
- `forbidden_now`: actions blocked until evidence, validation, or a human gate

Use the claim relation map as the conclusion-boundary layer. Read
`supported_by`, `limited_by`, `not_tested_by`, `contradicted_by`,
`current_conclusion.can_say`, `current_conclusion.cannot_say`,
`current_blockers`, and `next_valid_actions` before deciding whether a failure
supports, limits, or does not test the active claim.

If the only available packet is a legacy stage brief, migrate or bind a v5
session first. Legacy stages are historical orientation, not the runtime loop.

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
or typed refs with `mcp__aitp__aitp_v5_verify_recording_effect`.

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
mcp__aitp__aitp_v5_classify_recording_candidate(...)
mcp__aitp__aitp_v5_get_recording_navigation_state(base="{{TOPICS_ROOT}}", session_id=<session-id>, claim_id=<claim-id>)
mcp__aitp__aitp_v5_expand_recording_slot(base="{{TOPICS_ROOT}}", session_id=<session-id>, slot=<slot>, claim_id=<claim-id>)
<existing typed write or preflight tool named by the slot expansion>
mcp__aitp__aitp_v5_verify_recording_effect(base="{{TOPICS_ROOT}}", session_id=<session-id>, expected_refs=[...])
```

If the classifier says `ignore` or `defer`, do not write. If a live host does
not expose the recording navigator MCP tools, use the CLI fallback for read-only
navigation and mutate only through existing v5 typed write tools.

The first navigation answer should reveal only topic/session/claim position,
first-level slots, blockers, and recommended moments. Expand exactly one slot
at a time. The slot expansion must name an existing typed write or preflight
tool, the minimum fields, known values, unknown values, and the verification
step.

`recording_navigation_state` is intentionally lightweight first-level
navigation. It uses slot counts and relation-boundary hints; it does not replace
`execution_brief` or `process_graph_slice`. Call those separately only when the
next action really needs full context.

## Typed Record Boundaries

- `execution_brief` is the working control panel.
- `claim_relation_map` is a read-only recovery boundary; it is not evidence by
  itself and cannot update claim trust.
- Reference locations and summaries are orientation until linked to evidence.
- Source assets and reference locations are provenance/context, not claim
  support by themselves.
- A validation result supports only the exact checks and failure modes it covers.
- Partial validation should be narrow, not a broad pass.
- Claim confidence, trust updates, and L2 memory require explicit v5 gates.

## Legacy Topics

For older Markdown topics:

1. Use legacy aliases only to discover the slug.
2. Prefer `mcp__aitp__aitp_v5_migrate_curated_legacy_topic_to_v5` for known
   curated topics.
3. Use `mcp__aitp__aitp_v5_migrate_legacy_topic_to_v5` for generic
   preservation.
4. Continue from the v5 session id returned by migration.

## Physics Validation Discipline

Before treating a result as strong, check dimensional consistency, algebraic
consistency, limiting cases, symmetry or Ward identities, conservation laws,
approximation validity, numerical convergence, benchmarks, and explicit failure
modes where applicable.

Do not bury a failed check in prose. Record it as typed state.
