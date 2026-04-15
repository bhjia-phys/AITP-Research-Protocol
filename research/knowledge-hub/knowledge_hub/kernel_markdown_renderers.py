from __future__ import annotations

from typing import Any

from .l1_source_intake_support import (
    l1_assumption_depth_summary_lines,
    l1_concept_graph_summary_lines,
    l1_contradiction_summary_lines,
    l1_notation_tension_lines,
    l1_reading_depth_limit_lines,
)
from .runtime_read_path_support import (
    append_competing_hypotheses_markdown,
    append_route_activation_markdown,
    append_route_choice_markdown,
    append_route_handoff_markdown,
    append_route_reentry_markdown,
    append_route_transition_gate_markdown,
    append_route_transition_intent_markdown,
    append_route_transition_receipt_markdown,
    append_route_transition_resolution_markdown,
    append_route_transition_discrepancy_markdown,
    append_route_transition_repair_markdown,
    append_route_transition_escalation_markdown,
    append_route_transition_clearance_markdown,
    append_route_transition_followthrough_markdown,
    append_route_transition_resumption_markdown,
    append_route_transition_commitment_markdown,
    append_route_transition_authority_markdown,
)


def _append_l1_source_intake_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    l1_source_intake = payload.get("l1_source_intake") or {}
    lines.extend(
        [
            "",
            "## L1 source intake",
            "",
            f"- Source count: `{l1_source_intake.get('source_count') or 0}`",
            "",
            "## L1 intake summary",
            "",
        ]
    )
    for row in l1_assumption_depth_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Source-backed assumptions",
            "",
        ]
    )
    for row in l1_source_intake.get("assumption_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('assumption') or '(missing)'}"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Source-backed regimes", ""])
    for row in l1_source_intake.get("regime_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"{row.get('regime') or '(missing)'}"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading depth", ""])
    for row in l1_source_intake.get("reading_depth_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` => `{row.get('reading_depth') or 'skim'}` "
                f"(basis: `{row.get('basis') or 'summary_only'}`)"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Method specificity", ""])
    for row in l1_source_intake.get("method_specificity_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"`{row.get('method_family') or '(missing)'}` / `{row.get('specificity_tier') or '(missing)'}`"
            )
            if row.get("evidence_excerpt"):
                lines.append(f"  evidence: {row.get('evidence_excerpt')}")
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Reading-depth limits", ""])
    for row in l1_reading_depth_limit_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Notation rows", ""])
    for row in l1_source_intake.get("notation_rows") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('source_id') or '(missing)'}` [{row.get('reading_depth') or 'skim'}]: "
                f"`{row.get('symbol') or '(missing)'}` => `{row.get('meaning') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")
    lines.extend(["", "## Contradiction candidates", ""])
    for row in l1_contradiction_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Notation-alignment tension", ""])
    for row in l1_notation_tension_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Concept graph", ""])
    for row in l1_concept_graph_summary_lines(l1_source_intake) or ["(none)"]:
        lines.append(f"- {row}")


def _append_l1_vault_markdown(lines: list[str], payload: dict[str, Any]) -> None:
    l1_vault = payload.get("l1_vault") or {}
    raw = l1_vault.get("raw") or {}
    wiki = l1_vault.get("wiki") or {}
    output = l1_vault.get("output") or {}
    lines.extend(
        [
            "",
            "## L1 vault",
            "",
            f"- Status: `{l1_vault.get('status') or '(missing)'}`",
            f"- Root path: `{l1_vault.get('root_path') or '(missing)'}`",
            f"- Protocol path: `{l1_vault.get('protocol_path') or '(missing)'}`",
            "",
            "## L1 vault raw layer",
            "",
            f"- Manifest JSON: `{raw.get('manifest_path') or '(missing)'}`",
            f"- Manifest note: `{raw.get('note_path') or '(missing)'}`",
            f"- Source count: `{raw.get('source_count') or 0}`",
            "",
            "## L1 vault wiki layer",
            "",
            f"- Schema page: `{wiki.get('schema_path') or '(missing)'}`",
            f"- Home page: `{wiki.get('home_page_path') or '(missing)'}`",
            f"- Page count: `{wiki.get('page_count') or 0}`",
            "",
            "## L1 vault output layer",
            "",
            f"- Digest JSON: `{output.get('digest_path') or '(missing)'}`",
            f"- Digest note: `{output.get('digest_note_path') or '(missing)'}`",
            f"- Flowback log: `{output.get('flowback_log_path') or '(missing)'}`",
            f"- Flowback entries: `{output.get('flowback_entry_count') or 0}`",
            "",
            "## L1 vault compatibility refs",
            "",
        ]
    )
    for row in l1_vault.get("compatibility_refs") or ["(none)"]:
        if isinstance(row, dict):
            lines.append(
                f"- `{row.get('kind') or '(missing)'}` status=`{row.get('status') or 'missing'}` path=`{row.get('path') or '(missing)'}`"
            )
        else:
            lines.append(f"- {row}")


def render_operator_checkpoint_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Operator checkpoint",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Checkpoint id: `{payload.get('checkpoint_id') or '(missing)'}`",
        f"- Kind: `{payload.get('checkpoint_kind') or '(none)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Active: `{str(bool(payload.get('active'))).lower()}`",
        f"- Requested at: `{payload.get('requested_at') or '(missing)'}`",
        f"- Requested by: `{payload.get('requested_by') or '(missing)'}`",
        f"- Answered at: `{payload.get('answered_at') or '(none)'}`",
        f"- Answered by: `{payload.get('answered_by') or '(none)'}`",
        "",
        "## Question",
        "",
        payload.get("question") or "(missing)",
        "",
        "## Required response",
        "",
        payload.get("required_response") or "(missing)",
        "",
        "## Blocker summary",
        "",
    ]
    for item in payload.get("blocker_summary") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Response channels", ""])
    for item in payload.get("response_channels") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Evidence refs", ""])
    for item in payload.get("evidence_refs") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Options", ""])
    options = payload.get("options") or []
    if options:
        default_index = payload.get("default_option_index")
        for index, option in enumerate(options):
            default_marker = " default=`true`" if default_index == index else ""
            lines.append(
                f"- `{option.get('key') or f'option-{index}'}` label=`{option.get('label') or '(missing)'}`{default_marker}: {option.get('description') or '(missing)'}"
            )
    else:
        lines.append("- (none)")
    resolution = payload.get("resolution") or {}
    if resolution:
        lines.extend(["", "## Resolution", ""])
        lines.append(
            f"- Selected option index: `{resolution.get('chosen_option_index') if resolution.get('chosen_option_index') is not None else '(none)'}`"
        )
        lines.append(
            f"- Selected option key: `{resolution.get('chosen_option_key') or '(none)'}`"
        )
        lines.append(
            f"- Selected option label: `{resolution.get('chosen_option_label') or '(none)'}`"
        )
        lines.append(
            f"- Human comment: {resolution.get('human_comment') or '(none)'}"
        )
    lines.extend(["", "## Current answer", ""])
    lines.append(payload.get("answer") or "(none yet)")
    return "\n".join(lines) + "\n"


def render_research_question_contract_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Active research question contract",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Question id: `{payload['question_id']}`",
        f"- Title: `{payload['title']}`",
        f"- Status: `{payload['status']}`",
        f"- Template mode: `{payload.get('template_mode') or '(missing)'}`",
        f"- Research mode: `{payload.get('research_mode') or '(missing)'}`",
        "",
        "## Question",
        "",
        payload["question"],
        "",
        "## Scope",
        "",
    ]
    for item in payload.get("scope") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Assumptions", ""])
    for item in payload.get("assumptions") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Non-goals", ""])
    for item in payload.get("non_goals") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Context intake", ""])
    for item in payload.get("context_intake") or ["(missing)"]:
        lines.append(f"- {item}")
    _append_l1_source_intake_markdown(lines, payload)
    _append_l1_vault_markdown(lines, payload)
    lines.extend(["", "## Source basis refs", ""])
    for item in payload.get("source_basis_refs") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Interpretation focus", ""])
    for item in payload.get("interpretation_focus") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Open ambiguities", ""])
    for item in payload.get("open_ambiguities") or ["(none)"]:
        lines.append(f"- {item}")
    append_competing_hypotheses_markdown(lines, payload)
    append_route_activation_markdown(lines, payload)
    append_route_reentry_markdown(lines, payload)
    append_route_handoff_markdown(lines, payload)
    append_route_choice_markdown(lines, payload)
    append_route_transition_gate_markdown(lines, payload)
    append_route_transition_intent_markdown(lines, payload)
    append_route_transition_receipt_markdown(lines, payload)
    append_route_transition_resolution_markdown(lines, payload)
    append_route_transition_discrepancy_markdown(lines, payload)
    append_route_transition_repair_markdown(lines, payload)
    append_route_transition_escalation_markdown(lines, payload)
    append_route_transition_clearance_markdown(lines, payload)
    append_route_transition_followthrough_markdown(lines, payload)
    append_route_transition_resumption_markdown(lines, payload)
    append_route_transition_commitment_markdown(lines, payload)
    append_route_transition_authority_markdown(lines, payload)
    lines.extend(["", "## Formalism and notation", ""])
    for item in payload.get("formalism_and_notation") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Observables", ""])
    for item in payload.get("observables") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Target claims", ""])
    for item in payload.get("target_claims") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Deliverables", ""])
    for item in payload.get("deliverables") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Acceptance tests", ""])
    for item in payload.get("acceptance_tests") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden proxies", ""])
    for item in payload.get("forbidden_proxies") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Uncertainty markers", ""])
    for item in payload.get("uncertainty_markers") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Target layers", ""])
    for item in payload.get("target_layers") or ["(missing)"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_validation_contract_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Active validation contract",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Validation id: `{payload['validation_id']}`",
        f"- Status: `{payload['status']}`",
        f"- Template mode: `{payload.get('template_mode') or '(missing)'}`",
        f"- Validation mode: `{payload.get('validation_mode') or '(missing)'}`",
        f"- Verification focus: `{payload.get('verification_focus') or '(missing)'}`",
        f"- Confidence cap: `{payload.get('confidence_cap') or '(missing)'}`",
        f"- Primary review bundle: `{payload.get('primary_review_bundle_path') or '(missing)'}`",
        "",
        "## Acceptance rule",
        "",
        payload["acceptance_rule"],
        "",
        "## Rejection rule",
        "",
        payload["rejection_rule"],
        "",
        "## Target claim ids",
        "",
    ]
    for item in payload.get("target_claim_ids") or ["(missing)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Required checks", ""])
    for item in payload.get("required_checks") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Oracle artifacts", ""])
    for item in payload.get("oracle_artifacts") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Review focus", ""])
    lines.append(payload.get("review_focus") or "(missing)")
    lines.extend(["", "## Open review questions", ""])
    for item in payload.get("open_review_questions") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Executed evidence", ""])
    for item in payload.get("executed_evidence") or ["(none yet)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Gap followups", ""])
    for item in payload.get("gap_followups") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Failure modes", ""])
    for item in payload.get("failure_modes") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Artifact lanes", ""])
    for item in payload.get("artifacts") or ["(missing)"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_idea_packet_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Idea packet",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        "",
        "## Gate summary",
        "",
        payload.get("status_reason") or "(missing)",
        "",
        "## Initial idea",
        "",
        payload.get("initial_idea") or "(missing)",
        "",
        "## Novelty target",
        "",
        payload.get("novelty_target") or "(missing)",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or ["(missing)"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## First validation route",
            "",
            payload.get("first_validation_route") or "(missing)",
            "",
            "## Initial evidence bar",
            "",
            payload.get("initial_evidence_bar") or "(missing)",
            "",
            "## Missing fields",
            "",
        ]
    )
    for item in payload.get("missing_fields") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Clarification questions", ""])
    for item in payload.get("clarification_questions") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Execution context signals", ""])
    for item in payload.get("execution_context_signals") or ["(none)"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_topic_skill_projection_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Topic skill projection",
        "",
        f"- Projection id: `{payload.get('id') or '(missing)'}`",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Source topic slug: `{payload.get('source_topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Lane: `{payload.get('lane') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Candidate id: `{payload.get('candidate_id') or '(none)'}`",
        f"- Intended L2 target: `{payload.get('intended_l2_target') or '(none)'}`",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Status reason",
        "",
        payload.get("status_reason") or "(missing)",
        "",
        "## Entry signals",
        "",
    ]
    for item in payload.get("entry_signals") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Required first reads", ""])
    for item in payload.get("required_first_reads") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Required first routes", ""])
    for item in payload.get("required_first_routes") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Benchmark-first rules", ""])
    for item in payload.get("benchmark_first_rules") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Operator checkpoint rules", ""])
    for item in payload.get("operator_checkpoint_rules") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Operation trust requirements", ""])
    for item in payload.get("operation_trust_requirements") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Strategy guidance", ""])
    for item in payload.get("strategy_guidance") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Forbidden proxies", ""])
    for item in payload.get("forbidden_proxies") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Derived from artifacts", ""])
    for item in payload.get("derived_from_artifacts") or ["(none)"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_promotion_readiness_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Promotion readiness",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Latest run id: `{payload.get('latest_run_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Gate status: `{payload.get('gate_status') or '(missing)'}`",
        f"- Ready candidate count: `{len(payload.get('ready_candidate_ids') or [])}`",
        f"- Blocker count: `{payload.get('blocker_count') or 0}`",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Ready candidates",
        "",
    ]
    for item in payload.get("ready_candidate_ids") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blockers", ""])
    for item in payload.get("blockers") or ["(none)"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def render_gap_map_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Gap map",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Gap count: `{payload.get('gap_count') or 0}`",
        f"- Requires L0 return: `{str(bool(payload.get('requires_l0_return'))).lower()}`",
        f"- Capability gap active: `{str(bool(payload.get('capability_gap_active'))).lower()}`",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Blockers",
        "",
    ]
    for item in payload.get("blockers") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Follow-up gap ids", ""])
    for item in payload.get("followup_gap_ids") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Follow-up gap writeback", ""])
    lines.append(f"- Count: `{payload.get('followup_gap_writeback_count') or 0}`")
    for item in payload.get("followup_gap_writeback_child_topics") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Pending action summaries", ""])
    for item in payload.get("pending_action_summaries") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "- When a blocker is really a missing citation, definition, derivation, or prior-work comparison, return to L0 and write back the recovery path instead of hiding it inside prose.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_proof_obligations_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Proof obligations",
        "",
        f"- Obligation count: `{len(rows)}`",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## `{row.get('obligation_id') or '(missing)'}`",
                "",
                f"- Category: `{row.get('category') or '(missing)'}`",
                f"- Status: `{row.get('status') or '(missing)'}`",
                f"- Claim: {row.get('claim') or '(missing)'}",
                f"- Prerequisites: `{', '.join(row.get('prerequisite_ids') or []) or '(none)'}`",
                f"- Equation labels: `{', '.join(row.get('equation_labels') or []) or '(none)'}`",
                f"- Source anchors: `{', '.join(row.get('source_anchor_ids') or []) or '(none)'}`",
                f"- Required logical move: {row.get('required_logical_move') or '(missing)'}",
                f"- Expected output: {row.get('expected_output_statement') or '(missing)'}",
                "",
            ]
        )
    if not rows:
        lines.append("- No proof obligations are currently registered.")
        lines.append("")
    return "\n".join(lines) + "\n"


def render_proof_state_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Proof state",
        "",
        f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Total obligations: `{payload.get('obligation_count') or 0}`",
        "",
        "## Status counts",
        "",
    ]
    for key, value in sorted((payload.get("status_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Obligation ids", ""])
    for item in payload.get("obligation_ids") or ["(none)"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_statement_compilation_packet_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Statement compilation packet",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
        f"- Candidate type: `{payload.get('candidate_type') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Primary statement kind: `{payload.get('primary_statement_kind') or '(missing)'}`",
        f"- Primary identifier: `{payload.get('primary_identifier') or '(missing)'}`",
        f"- Proof repair plan: `{payload.get('proof_repair_plan_path') or '(missing)'}`",
        "",
        "## Assistant targets",
        "",
    ]
    for row in payload.get("assistant_targets") or []:
        lines.append(
            f"- `{row.get('assistant') or '(missing)'}` kind=`{row.get('kind') or '(missing)'}` status=`{row.get('status') or '(missing)'}`"
        )
        if row.get("reason"):
            lines.append(f"  reason: {row.get('reason')}")
    if not payload.get("assistant_targets"):
        lines.append("- (none)")
    lines.extend(["", "## Declarations", ""])
    for row in payload.get("declarations") or []:
        lines.append(
            f"- `{row.get('identifier') or '(missing)'}` kind=`{row.get('statement_kind') or '(missing)'}` role=`{row.get('declaration_role') or '(missing)'}`"
        )
        lines.append(f"  - signature: `{row.get('signature') or '(missing)'}`")
        lines.append(f"  - statement: {row.get('natural_language_statement') or '(missing)'}")
        lines.append(f"  - holes: `{', '.join(row.get('temporary_proof_holes') or []) or '(none)'}`")
    if not payload.get("declarations"):
        lines.append("- (none)")
    lines.extend(["", "## Theory packet refs", ""])
    for key, value in sorted((payload.get("theory_packet_refs") or {}).items()):
        lines.append(f"- `{key}`: `{value or '(missing)'}`")
    return "\n".join(lines) + "\n"


def render_proof_repair_plan_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Proof repair plan",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Compilation packet: `{payload.get('compilation_path') or '(missing)'}`",
        "",
        "## Repair stages",
        "",
    ]
    for row in payload.get("repair_stages") or []:
        lines.append(
            f"- `{row.get('stage_name') or '(missing)'}` status=`{row.get('status') or '(missing)'}`"
        )
        lines.append(f"  - {row.get('summary') or '(missing)'}")
    if not payload.get("repair_stages"):
        lines.append("- (none)")
    lines.extend(["", "## Proof holes", ""])
    for row in payload.get("proof_holes") or []:
        lines.append(
            f"- `{row.get('hole_id') or '(missing)'}` category=`{row.get('category') or '(missing)'}` status=`{row.get('status') or '(missing)'}`"
        )
        lines.append(f"  - claim: {row.get('claim') or '(missing)'}")
        lines.append(f"  - verifiers: `{', '.join(row.get('verifier_targets') or []) or '(none)'}`")
        lines.append(f"  - close condition: {row.get('close_condition') or '(missing)'}")
    if not payload.get("proof_holes"):
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def render_statement_compilation_index_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Statement compilation",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Packet count: `{payload.get('packet_count') or 0}`",
        f"- Ready packet count: `{payload.get('ready_packet_count') or 0}`",
        f"- Needs repair count: `{payload.get('needs_repair_count') or 0}`",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Packets",
        "",
    ]
    for row in payload.get("packets") or []:
        lines.append(
            f"- `{row.get('candidate_id') or '(missing)'}` kind=`{row.get('statement_kind') or '(missing)'}` status=`{row.get('status') or '(missing)'}` holes=`{row.get('proof_hole_count') or 0}` packet=`{row.get('packet_path') or '(missing)'}`"
        )
    if not payload.get("packets"):
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def render_lean_bridge_packet_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Lean-ready bridge packet",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Candidate id: `{payload.get('candidate_id') or '(missing)'}`",
        f"- Candidate type: `{payload.get('candidate_type') or '(missing)'}`",
        f"- Declaration kind: `{payload.get('declaration_kind') or '(missing)'}`",
        f"- Namespace: `{payload.get('namespace') or '(missing)'}`",
        f"- Declaration name: `{payload.get('declaration_name') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        "",
        "## Statement",
        "",
        payload.get("statement_text") or "(missing)",
        "",
        "## Dependency ids",
        "",
    ]
    for item in payload.get("dependency_ids") or ["(none)"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Notation bindings", ""])
    for row in payload.get("notation_bindings") or []:
        lines.append(f"- `{row.get('symbol') or '(missing)'}` := {row.get('meaning') or '(missing)'}")
    if not payload.get("notation_bindings"):
        lines.append("- (none)")
    lines.extend(["", "## Proof obligations", ""])
    for item in payload.get("proof_obligations") or ["(none)"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Proof-state bridge", ""])
    lines.append(f"- Obligation count: `{payload.get('proof_obligation_count') or 0}`")
    lines.append(f"- Proof obligations JSON: `{payload.get('proof_obligations_path') or '(missing)'}`")
    lines.append(f"- Proof state JSON: `{payload.get('proof_state_path') or '(missing)'}`")
    lines.extend(["", "## Theory packet refs", ""])
    for key, value in sorted((payload.get("theory_packet_refs") or {}).items()):
        lines.append(f"- `{key}`: `{value or '(missing)'}`")
    lines.extend(
        [
            "",
            "## Upstream statement compilation",
            "",
            f"- Statement compilation packet: `{payload.get('statement_compilation_path') or '(missing)'}`",
            f"- Proof repair plan: `{payload.get('proof_repair_plan_path') or '(missing)'}`",
        ]
    )
    lines.extend(["", "## Skeleton", ""])
    lines.append("```lean")
    lines.extend(payload.get("lean_skeleton_lines") or ["-- no skeleton available"])
    lines.append("```")
    return "\n".join(lines) + "\n"


def render_lean_bridge_index_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Lean bridge",
        "",
        f"- Topic slug: `{payload['topic_slug']}`",
        f"- Run id: `{payload.get('run_id') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Packet count: `{payload.get('packet_count') or 0}`",
        f"- Ready packet count: `{payload.get('ready_packet_count') or 0}`",
        "",
        "## Summary",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Packets",
        "",
    ]
    for row in payload.get("packets") or []:
        lines.append(
            f"- `{row.get('candidate_id') or '(missing)'}` kind=`{row.get('declaration_kind') or '(missing)'}` "
            f"status=`{row.get('status') or '(missing)'}` obligations=`{row.get('proof_obligation_count') or 0}` "
            f"packet=`{row.get('packet_path') or '(missing)'}`"
        )
    if not payload.get("packets"):
        lines.append("- (none)")
    return "\n".join(lines) + "\n"


def render_control_note_markdown(
    *,
    topic_slug: str,
    run_id: str | None,
    updated_by: str,
    updated_at: str,
    steering: dict[str, Any],
    innovation_direction_path: str,
    innovation_decisions_path: str,
    steering_contract: dict[str, Any] | None,
) -> str:
    summary = str(steering.get("summary") or "Persist the latest operator steering for this topic.")
    direction = str(steering.get("direction") or "").strip()
    directive = str(steering.get("directive") or "").strip()
    decision = str(steering.get("decision") or "").strip()
    target_action_id = str((steering_contract or {}).get("action_id") or "").strip()
    target_action_summary = str((steering_contract or {}).get("summary") or "").strip()
    target_artifacts = [
        innovation_direction_path,
        innovation_decisions_path,
    ]
    contract_path = str((steering_contract or {}).get("path") or "").strip()
    if contract_path:
        target_artifacts.append(contract_path)

    lines = [
        "---",
        f"topic_slug: {topic_slug}",
        f"updated_by: {updated_by}",
        f"updated_at: {updated_at}",
        f"run_id: {run_id or '(none)'}",
        f"summary: {summary}",
    ]
    if directive:
        lines.append(f"directive: {directive}")
    if decision in {"redirect", "branch"}:
        lines.append("allow_override_unfinished: true")
        lines.append("allow_override_decision_contract: true")
    if target_action_id:
        lines.append(f"target_action_id: {target_action_id}")
    if target_action_summary:
        lines.append(f"target_action_summary: {target_action_summary}")
    if target_artifacts:
        lines.extend(["target_artifacts:"] + [f"  - {artifact}" for artifact in target_artifacts])
    stop_conditions = []
    if decision in {"pause", "stop"}:
        stop_conditions.append("Resume only after the operator records a new continue or redirect decision.")
    elif decision in {"redirect", "branch"}:
        stop_conditions.append("Replace this steering redirect once the ordinary queue and contracts absorb the new direction.")
    if stop_conditions:
        lines.extend(["stop_conditions:"] + [f"  - {condition}" for condition in stop_conditions])
    lines.extend(
        [
            "---",
            "",
            "# Control note",
            "",
            f"- Decision: `{decision or '(missing)'}`",
            f"- Direction: `{direction or '(unchanged)'}`",
            f"- Innovation direction note: `{innovation_direction_path}`",
            f"- Innovation decisions log: `{innovation_decisions_path}`",
            f"- Raw operator request: {steering.get('raw_request') or '(missing)'}",
            "",
            "If this steering changes scope, observables, deliverables, or acceptance checks, update the matching research-question or validation contract in the same step.",
        ]
    )
    if contract_path:
        lines.extend(["", f"- Declared next-actions contract: `{contract_path}`"])
    return "\n".join(lines) + "\n"


def render_topic_family_reuse_note(payload: dict[str, Any]) -> str:
    lines = [
        "# Topic family reuse",
        "",
        f"- Protocol version: `{payload.get('protocol_version') or '(missing)'}`",
        f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
        f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
        f"- Family count: `{payload.get('family_count') or 0}`",
        "",
        "This surface is protocol-native route reuse.",
        "It is not adapter-specific skill generation and it does not bypass trust gates.",
        "",
        "## Families",
        "",
    ]
    for family in payload.get("families") or []:
        lines.extend(
            [
                f"### `{family.get('family_id') or '(missing)'}`",
                "",
                f"- Lane: `{family.get('lane') or '(missing)'}`",
                f"- Status: `{family.get('status') or '(missing)'}`",
                f"- Reuse mode: `{family.get('reuse_mode') or '(missing)'}`",
                f"- Topic count: `{family.get('topic_count') or 0}`",
                "",
                f"{family.get('summary') or '(missing)'}",
                "",
                "#### Capsules",
                "",
            ]
        )
        for capsule in family.get("capsules") or []:
            lines.append(
                f"- `{capsule.get('topic_slug') or '(missing)'}` note=`{capsule.get('note_path') or '(missing)'}`"
            )
            if str(capsule.get("summary") or "").strip():
                lines.append(f"  - Summary: {capsule.get('summary')}")
        if not family.get("capsules"):
            lines.append("- `(none)`")
        if family.get("family_rules"):
            lines.extend(["", "#### Family rules", ""])
            for item in family.get("family_rules") or []:
                lines.append(f"- {item}")
        if family.get("forbidden_proxies"):
            lines.extend(["", "#### Forbidden proxies", ""])
            for item in family.get("forbidden_proxies") or []:
                lines.append(f"- {item}")
        lines.append("")
    if not payload.get("families"):
        lines.append("- `(none)`")
    return "\n".join(lines).rstrip() + "\n"


def render_current_topic_note(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Current topic memory",
            "",
            f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
            f"- Updated at: `{payload.get('updated_at') or '(missing)'}`",
            f"- Updated by: `{payload.get('updated_by') or '(missing)'}`",
            f"- Source: `{payload.get('source') or '(missing)'}`",
            f"- Resume stage: `{payload.get('resume_stage') or '(missing)'}`",
            f"- Latest run id: `{payload.get('run_id') or '(none)'}`",
            f"- Runtime root: `{payload.get('runtime_root') or '(missing)'}`",
            f"- Human request: {payload.get('human_request') or '(missing)'}",
            f"- Summary: {payload.get('summary') or '(missing)'}",
            f"- Collaborator profile status: `{payload.get('collaborator_profile_status') or '(missing)'}`",
            f"- Collaborator profile note: `{payload.get('collaborator_profile_note_path') or '(none)'}`",
            f"- Collaborator profile summary: {payload.get('collaborator_profile_summary') or '(none)'}",
            f"- Research trajectory status: `{payload.get('research_trajectory_status') or '(missing)'}`",
            f"- Research trajectory note: `{payload.get('research_trajectory_note_path') or '(none)'}`",
            f"- Research trajectory summary: {payload.get('research_trajectory_summary') or '(none)'}",
            f"- Mode learning status: `{payload.get('mode_learning_status') or '(missing)'}`",
            f"- Mode learning note: `{payload.get('mode_learning_note_path') or '(none)'}`",
            f"- Mode learning summary: {payload.get('mode_learning_summary') or '(none)'}",
            "",
            "This is the workspace-facing memory used to resolve natural-language requests such as `继续这个 topic` before falling back to the latest topic index.",
            "",
        ]
    )
