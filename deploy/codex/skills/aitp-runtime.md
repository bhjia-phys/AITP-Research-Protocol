---
name: aitp-runtime
description: Codex app runtime skill for continuing an AITP v5 theoretical-physics topic through typed claims, evidence, validation gates, and trust-controlled memory.
---

# AITP Runtime v5 In Codex App

## Mandatory First Step

For every AITP research iteration, restore the v5 typed execution brief:

```text
aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)
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

## Typed Runtime Loop

Use this loop conceptually, with the actual Codex tool names exposed in the
session:

```text
while topic is active:
  brief = aitp_v5_get_execution_brief(base="{{TOPICS_ROOT}}", session_id=<session-id>)
  relation_map = aitp_v5_get_claim_relation_map(base="{{TOPICS_ROOT}}", session_id=<session-id>)

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

## Record Boundaries

- Definitions and systems: `aitp_v5_record_physics_object`.
- Relations or equations: `aitp_v5_record_object_relation`.
- Papers, notes, and locations: `aitp_v5_record_reference_location` or
  `aitp_v5_register_source`.
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
