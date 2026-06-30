---
name: aitp-runtime
description: Continue an AITP v5 theoretical-physics topic through typed claims, source provenance, artifacts, evidence, validation gates, human checkpoints, and trust-controlled memory.
---

# AITP Runtime v5

For every active AITP research iteration, restore the bounded Codex entry context first:

```text
aitp_v5_codex_enter(base="", session_id=<session-id>, request_summary=<current user request>)
```

Use `base=""` unless the user explicitly provides a topics root. The MCP server resolves the empty base through `AITP_TOPICS_ROOT`, which the plugin launcher sets from environment, AITP install records, or the default `~/.aitp/topics`.

The entry context includes the low-interruption continuation view. It is orientation-only and cannot update claim trust, evidence, validation, L2 memory, or skills. It should name the current objective, active work package, can-say/cannot-say boundaries, blockers, next actions, distillation gates, and expansion commands.

Expand explicitly before any trust-sensitive interpretation:

```text
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="brief")
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="relation_map")
```

The full brief is the execution contract. Follow `current_focus`, `flow_profile`, `risk_assessment`, `evidence_coverage`, `next_action_candidates`, `forbidden_now`, and `human_checkpoint`.

The claim relation map is the boundary layer. Read `supported_by`, `limited_by`, `not_tested_by`, `contradicted_by`, `current_conclusion.can_say`, `current_conclusion.cannot_say`, `current_blockers`, and `next_valid_actions` before interpreting the active claim.

## Typed Runtime Loop

1. Restore the Codex entry context.
2. Expand to the full brief and relation map only when the task needs audit, trust, validation, evidence, or final synthesis.
3. If a human checkpoint is needed, present it plainly and wait.
4. If policy forbids trust-changing actions, collect missing source, evidence, or validation first.
5. If evidence coverage is missing, record only the durable typed object needed: source, artifact, code state, tool recipe, tool run, evidence, validation contract, validation result, proof obligation, or sensemaking report.
6. Do the physics, code, or literature work.
7. Record durable outputs before summarizing them as research state.
8. Verify expected records with `aitp_v5_verify_recording_effect` when recording navigation is used.

## Moment Policy

AITP is not a transcript logger. Record only durable research moments:

- reusable source identity or source location,
- completed tool/code run with research-relevant output,
- artifact/report/table/plot/log/raw dump,
- result, anomaly, contradiction, negative result, or failed check,
- proof gap, validation gap, missing provenance, route blocker,
- selected, pivoted, abandoned, or split route,
- active claim scope or status change,
- final answer that depends on an active claim,
- trust update, promotion, or human decision request,
- session-end handoff with new durable state.

Do not record generic explanation, unaccepted brainstorming, repeated summaries, file scans with no research change, or setup checks with no research information.

## Progressive Recording

Use the lightest recording route:

```text
aitp_v5_codex_recording_step(base="", session_id=<session-id>, event_type=<event>, summary=<durable moment>)
aitp_v5_codex_recording_step(base="", session_id=<session-id>, event_type=<event>, summary=<durable moment>, slot=<one slot>)
<call the named typed write or preflight tool>
aitp_v5_verify_recording_effect(base="", session_id=<session-id>, expected_refs=[...])
```

If the classifier says `ignore` or `defer`, do not write. Expand one slot at a time.

## Record Boundaries

- Definitions and systems: `aitp_v5_record_physics_object`.
- Relations and equations: `aitp_v5_record_object_relation`.
- Papers, notes, and source locations: `aitp_v5_record_reference_location` or `aitp_v5_register_source`.
- Files and reports: `aitp_v5_attach_artifact`.
- Numerical or code-dependent work: code state, tool recipe, tool run, evidence, validation result.
- Open theorem or review gaps: `aitp_v5_create_proof_obligation`.
- Claim maturity/status observations: `aitp_v5_update_claim_status`.
- Interpretation: `aitp_v5_record_sensemaking_report`, marked orientation-only unless backed by typed evidence or validation.

Source references and artifacts are provenance/context by themselves. Do not treat them as claim support until typed evidence or validation links them to the claim.

## Literature And Writing

For paper learning, web references, and note/article drafting, use the Codex facade first:

```text
aitp_v5_codex_literature_step(base="", session_id=<session-id>, action="suggest", uri=<url-or-path>, label=<source label>)
aitp_v5_codex_literature_step(base="", session_id=<session-id>, action="record_reference", uri=<url-or-path>, label=<source label>)
aitp_v5_codex_expand(base="", session_id=<session-id>, expansion="note_outline", style="jhep")
```

Register references in layers: source identity, exact reference location, reading artifact, claim-linked evidence, physics object/relation, validation basis, and trust basis. A paper, web page, local note, or RAG chunk is not evidence until it is linked to a specific claim with scoped typed evidence.

For session end or discussion closeout, do not rely on a Codex stop hook. Use:

```text
aitp_v5_codex_closeout(base="", session_id=<session-id>, summary=<handoff summary>)
```

The closeout tool previews by default. Set `apply=true` only when there is a durable handoff or quiet checkpoint worth writing. It cannot update claim trust.

## Physics Validation Obligations

Before treating a result as strong, check the relevant obligations:

- dimensional and algebraic consistency,
- limiting cases and known limits,
- symmetry, Ward identity, causality, unitarity, or conservation checks where applicable,
- approximation validity and scale separation,
- numerical convergence, benchmark comparison, and error bars,
- explicit mismatch or negative-result records when a check fails.

Do not bury a failed check in prose. Record it as typed protocol state.

## Fallback Commands

```powershell
uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py doctor
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" status context-pack <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" brief <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m brain.v5.cli --base "$env:AITP_TOPICS_ROOT" relation-map <session-id>
uv run --with pyyaml --with jsonschema --with fastmcp python -m py_compile brain/v5/native_mcp.py brain/v5/mcp_tools.py brain/v5/brief.py brain/v5/context_pack.py
```
