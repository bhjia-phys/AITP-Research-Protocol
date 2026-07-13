"""Codex-friendly read-only context pack over AITP v5 research state."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from brain.v5.context_profile_templates import build_context_profile_template_catalog
from brain.v5.context_profiles import builtin_context_profiles, context_profile_payload
from brain.v5.context_compiler import (
    ContextRequest,
    compile_research_context,
    estimate_context_tokens,
)
from brain.v5.context_selection import merge_not_shown_reasons, select_candidate_summaries
from brain.v5.context_pack_projection import (
    bounded_context_lines as _bounded_context_lines,
    compact_from_bundle as _compact_from_bundle,
    compiler_candidate as _compiler_candidate,
    distillation_from_candidates as _distillation_from_candidates,
    focus_reconciliation_from_bundle as _focus_reconciliation_from_bundle,
)
from brain.v5.objective_graph import build_compact_brief
from brain.v5.paths import WorkspacePaths
from brain.v5.research_distillation import build_research_distillation_candidates

_DEFAULT_MAX_LINES = 60
_DEFAULT_CANDIDATE_LIMIT = 3


def build_aitp_context_pack(
    ws: WorkspacePaths,
    session_id: str,
    *,
    max_lines: int = _DEFAULT_MAX_LINES,
    candidate_limit: int = _DEFAULT_CANDIDATE_LIMIT,
    objective_text: str = "",
    user_goal: str = "",
    task_profile: str = "",
) -> dict[str, Any]:
    """Build the bounded research-state slice intended for Codex turn input.

    This is not a memory, evidence, validation, or trust surface. It compiles the
    already-typed graph into a short, fingerprinted context fragment that a host
    runtime can inject once per changed research state and expand explicitly.
    """

    line_limit = max(12, min(int(max_lines), 80))
    candidate_limit = max(1, min(int(candidate_limit), 8))
    selected_profile = _selected_context_profile(task_profile)
    profile_template_hint = _selected_profile_template_hint(task_profile)
    profile_warning = []
    if task_profile and not selected_profile:
        profile_warning.append(f"unknown_task_profile:{task_profile}")
    max_bytes = max(1200, min(12_000, line_limit * 180))
    max_tokens = max(240, min(3000, line_limit * 32))
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id=session_id,
            objective_text=objective_text,
            user_goal=user_goal,
            max_tokens=max_tokens,
            max_bytes=max_bytes,
            record_limit=max(24, candidate_limit * 8),
            candidate_limit=max(candidate_limit * 3, 8),
        ),
    )
    compact = _compact_from_bundle(bundle)
    projected_candidates = select_candidate_summaries(
        bundle.candidate_summaries,
        limit=candidate_limit,
    )
    top_candidates = [
        _compiler_candidate(candidate)
        for candidate in projected_candidates
    ]
    projection_omitted = len(bundle.candidate_summaries) - len(projected_candidates)
    not_shown_count = bundle.not_shown_count + projection_omitted
    not_shown_reason = merge_not_shown_reasons(
        bundle.not_shown_reason,
        (("context_pack_candidate_limit",) if projection_omitted else ()),
    )
    distillation = _distillation_from_candidates(top_candidates)
    focus_reconciliation = _focus_reconciliation_from_bundle(
        bundle,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    drift_detected = focus_reconciliation["status"] == "active_claim_focus_drift_detected"
    warnings = ["active_claim_focus_drift_detected"] if drift_detected else []
    compact["not_authoritative_for_current_goal_if_rebind_needed"] = drift_detected
    compact["warnings"] = warnings
    compact["active_claim_focus_reconciliation"] = focus_reconciliation
    derived_surfaces = [
        "query_index",
        "context_compiler",
        "compiled_candidate_projection",
    ]
    if profile_template_hint:
        derived_surfaces.append("context_profile_template_catalog")
    source_records = _merge_source_records(
        compact.get("source_records") if isinstance(compact.get("source_records"), dict) else {},
        {"record_refs": list(bundle.record_refs)},
        {"derived_surfaces": derived_surfaces},
    )

    payload: dict[str, Any] = {
        "ok": True,
        "kind": "aitp_context_pack",
        "context_pack_version": "v1",
        "designed_for_host": "codex",
        "session_id": str(compact.get("session_id") or ""),
        "topic_id": str(compact.get("topic_id") or ""),
        "current_objective": compact.get("current_objective") or {},
        "active_work_package": compact.get("active_work_package") or {},
        "relevant_claims": list(compact.get("relevant_claims") or []),
        "can_say": list(compact.get("can_say") or []),
        "cannot_say": list(compact.get("cannot_say") or []),
        "blockers": list(compact.get("blockers") or []),
        "previous_failed_attempts": list(compact.get("previous_failed_attempts") or []),
        "requested_task_profile": str(task_profile or ""),
        "task_profile": selected_profile,
        "profile_template_hint": profile_template_hint,
        "next_valid_actions": list(compact.get("next_valid_actions") or []),
        "recent_relevant_artifacts": list(compact.get("recent_relevant_artifacts") or []),
        "relation_map_scope": str(compact.get("relation_map_scope") or "active_claim_only"),
        "not_authoritative_for_current_goal_if_rebind_needed": bool(
            compact.get("not_authoritative_for_current_goal_if_rebind_needed")
        ),
        "warnings": list(compact.get("warnings") or []),
        "active_claim_focus_reconciliation": compact.get("active_claim_focus_reconciliation") or {},
        "retrieval_coverage": bundle.coverage,
        "index_status": bundle.index_status,
        "source_index_generation": bundle.source_index_generation,
        "partial": bool(bundle.partial or projection_omitted),
        "not_found_refs": list(bundle.not_found_refs),
        "not_checked_families": list(bundle.not_checked_families),
        "retrieval_truncated": bundle.retrieval_truncated,
        "render_truncated": bundle.render_truncated,
        "truncated": bundle.truncated,
        "not_shown_count": not_shown_count,
        "not_shown_reason": list(not_shown_reason),
        "record_refs": list(bundle.record_refs),
        "context_budget": {
            "max_bytes": max_bytes,
            "max_tokens": max_tokens,
        },
        "distillation_status": {
            "summary": distillation.get("summary") or {},
            "top_candidates": top_candidates,
            "gate_policy": list(distillation.get("gate_policy") or []),
            "next_valid_actions": list(distillation.get("next_valid_actions") or [])[:8],
        },
        "materialization_boundary": {
            **(distillation.get("distillation_boundary") or {}),
            "can_create_skill": False,
            "can_create_l2_memory": False,
            "can_update_claim_trust": False,
            "requires_human_review_before_materialization": True,
        },
        "injection_policy": {
            "host": "codex",
            "recommended_hook": "TurnInputContributor",
            "recommended_authority": "contextual_user_fragment",
            "max_lines": line_limit,
            "max_bytes": max_bytes,
            "max_tokens": max_tokens,
            "inject_when": [
                "session is first restored",
                "pack fingerprint changes",
                "user explicitly asks to restore AITP context",
            ],
            "avoid_reinjecting_when": [
                "same pack fingerprint is already present in the current turn context",
            ],
            "requires_explicit_expand_for": [
                "claim trust updates",
                "evidence support decisions",
                "validation status decisions",
                "full research timeline and previous failed route audit",
                "full relation-map audit",
                "active claim rebind or claim split",
                "workflow or skill materialization",
                "task-profile must-verify checks",
            ],
        },
        "expand": {
            **(compact.get("expand") or {}),
            "context_pack_cli": _context_pack_cli(session_id, task_profile=task_profile),
            "context_profile_templates_cli": _context_profile_templates_cli(task_profile=task_profile),
            "distillation_candidates_cli": f"aitp-v5 status distillation-candidates {session_id}",
            "mcp_context_pack": "aitp_v5_get_context_pack",
            "mcp_context_profile_templates": "aitp_v5_get_context_profile_templates",
            "mcp_research_distillation_candidates": "aitp_v5_get_research_distillation_candidates",
            "mcp_detect_active_claim_focus_drift": "aitp_v5_detect_active_claim_focus_drift",
            "mcp_confirm_active_claim_rebind": "aitp_v5_confirm_active_claim_rebind",
            "record_refs": {
                "surface": "record_refs",
                "refs": list(bundle.record_refs),
                "page_size": bundle.expansion["page_size"],
                "requires_explicit_call": True,
            },
        },
        "source_records": source_records,
        "read_errors": list(bundle.read_errors),
        "truth_source": "typed_records_derived_context_pack_not_evidence",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_materialize_without_human_review": False,
    }
    if profile_warning:
        payload["warnings"].extend(profile_warning)
    context_lines, host_render_truncated = _bounded_context_lines(
        _context_lines(payload, compact),
        line_limit=line_limit,
        max_bytes=max_bytes,
        max_tokens=max_tokens,
    )
    payload["context_lines"] = context_lines
    payload["render_truncated"] = bool(bundle.render_truncated or host_render_truncated)
    payload["truncated"] = bool(bundle.retrieval_truncated or payload["render_truncated"])
    payload["partial"] = bool(
        bundle.partial
        or projection_omitted
        or host_render_truncated
    )
    payload["line_count"] = len(payload["context_lines"])
    payload["markdown"] = "\n".join(payload["context_lines"]) + "\n"
    payload["byte_count"] = len(payload["markdown"].encode("utf-8"))
    payload["estimated_tokens"] = estimate_context_tokens(payload["markdown"])
    payload["fingerprint"] = _fingerprint(payload)
    payload["pack_id"] = f"aitp-context-pack-{payload['session_id']}-{payload['fingerprint'][:12]}"
    return payload


def _candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "candidate_kind": str(candidate.get("candidate_kind") or ""),
        "title": str(candidate.get("title") or ""),
        "distillation_state": str(candidate.get("distillation_state") or ""),
        "can_draft_reusable_block": bool(candidate.get("can_draft_reusable_block")),
        "can_materialize_without_human_review": False,
        "can_promote_claim_trust": False,
        "missing_requirements": list(candidate.get("missing_requirements") or []),
        "trust_boundary": str(candidate.get("trust_boundary") or ""),
        "source_records": candidate.get("source_records") or {},
        "orientation_only": True,
    }


def _context_lines(payload: dict[str, Any], compact: dict[str, Any]) -> list[str]:
    objective = payload.get("current_objective") or {}
    package = payload.get("active_work_package") or {}
    profile = payload.get("task_profile") if isinstance(payload.get("task_profile"), dict) else {}
    distillation = payload.get("distillation_status") or {}
    summary = distillation.get("summary") if isinstance(distillation.get("summary"), dict) else {}
    lines = [
        "AITP context pack for Codex turn input.",
        f"Session: {payload.get('session_id')} | Topic: {payload.get('topic_id')}",
        f"Current objective: {objective.get('title') or payload.get('topic_id')}",
        f"Active work package: {package.get('title') or 'none'}",
        "Boundary: orientation-only; cannot update claim trust, evidence, validation, L2 memory, or skills.",
        "",
    ]
    if profile:
        lines.extend(
            [
                f"Task profile: {profile.get('profile_id')} ({profile.get('task_type')})",
                f"Profile purpose: {_excerpt(profile.get('purpose') or '', limit=130)}",
                f"Profile can say: {_join_items(profile.get('can_say') or [])}",
                f"Profile cannot say: {_join_items(profile.get('cannot_say') or [])}",
                f"Profile must verify: {_join_items(profile.get('must_verify') or [])}",
                "",
            ]
        )
    template_hint = (
        payload.get("profile_template_hint")
        if isinstance(payload.get("profile_template_hint"), dict)
        else {}
    )
    if template_hint:
        lines.extend(
            [
                f"Template output shape: {template_hint.get('output_shape')}",
                f"Template sections: {_join_items(template_hint.get('required_section_ids') or [], limit=5)}",
                f"Template expand surfaces: {_join_items(template_hint.get('read_only_surfaces_to_expand') or [], limit=4)}",
                "Template boundary: read-only scaffold; cannot create evidence, validation, final gates, or trust updates.",
                "",
            ]
        )
    if payload.get("not_authoritative_for_current_goal_if_rebind_needed"):
        reconciliation = payload.get("active_claim_focus_reconciliation") or {}
        lines.extend(
            [
                "WARNING: active_claim_focus_drift_detected.",
                "The active-claim relation map is scoped to active_claim_only and may be stale for the current goal.",
                "Candidate sibling claims:",
            ]
        )
        candidates = list(reconciliation.get("candidate_sibling_claims") or [])[:3]
        if candidates:
            lines.extend(
                f"- {candidate.get('claim_id')}: {_excerpt(candidate.get('statement_excerpt') or '', limit=110)}"
                for candidate in candidates
            )
        else:
            lines.append("- none")
        lines.append("")
    failed_attempts = list(payload.get("previous_failed_attempts") or [])[:4]
    if failed_attempts:
        lines.append("Previous failed or superseded routes:")
        for attempt in failed_attempts:
            lines.append(
                f"- {attempt.get('record_ref')}: {attempt.get('classification')}; "
                f"{_excerpt(attempt.get('summary') or '', limit=120)}"
            )
        lines.append("")
    lines.extend(list(compact.get("lines") or []))
    lines.append(
        "Context-pack candidate selection: "
        f"not_shown={payload.get('not_shown_count', 0)}; "
        f"reason={'+'.join(payload.get('not_shown_reason') or []) or 'none'}."
    )
    lines.append("")
    lines.append(
        "Reusable-block candidates: "
        f"{summary.get('draftable_count', 0)} draftable / "
        f"{summary.get('needs_more_records_count', 0)} need more records."
    )
    for candidate in distillation.get("top_candidates") or []:
        missing = ", ".join(candidate.get("missing_requirements") or [])
        state = candidate.get("distillation_state") or "unknown"
        lines.append(
            f"- {candidate.get('candidate_id')}: {state}; "
            f"missing={missing or 'none'}; human review required"
        )
    lines.append("Expand explicitly before trust, validation, evidence, or materialization decisions.")
    return lines


def _merge_source_records(*groups: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for group in groups:
        for key, value in group.items():
            values = value if isinstance(value, list) else [value]
            bucket = out.setdefault(str(key), [])
            for item in values:
                text = str(item or "").strip()
                if text and text not in bucket:
                    bucket.append(text)
    return out


def _fingerprint(payload: dict[str, Any]) -> str:
    fingerprint_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"fingerprint", "pack_id", "markdown", "source_index_generation"}
    }
    encoded = json.dumps(fingerprint_payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _selected_context_profile(profile_id: str) -> dict[str, Any]:
    requested = str(profile_id or "").strip()
    if not requested:
        return {}
    profile = builtin_context_profiles().get(requested)
    if profile is None:
        return {}
    return context_profile_payload(profile)


def _selected_profile_template_hint(profile_id: str) -> dict[str, Any]:
    requested = str(profile_id or "").strip()
    if not requested:
        return {}
    catalog = build_context_profile_template_catalog(profile_ids=[requested])
    templates = list(catalog.get("templates") or [])
    if not templates:
        return {}
    template = templates[0]
    report_template = template.get("report_template") if isinstance(template.get("report_template"), dict) else {}
    closeout_template = template.get("closeout_template") if isinstance(template.get("closeout_template"), dict) else {}
    trust_boundary = template.get("trust_boundary") if isinstance(template.get("trust_boundary"), dict) else {}
    required_sections = [
        str(section.get("section_id") or "")
        for section in template.get("required_sections") or []
        if isinstance(section, dict) and str(section.get("section_id") or "").strip()
    ]
    return {
        "kind": "context_profile_template_hint",
        "profile_id": str(template.get("profile_id") or ""),
        "template_id": str(template.get("template_id") or ""),
        "template_family": str(template.get("template_family") or ""),
        "output_shape": str(template.get("output_shape") or ""),
        "required_section_ids": required_sections,
        "report_section_order": list(report_template.get("section_order") or []),
        "closeout_section_order": list(closeout_template.get("section_order") or []),
        "must_verify_before_trust_or_promotion": list(
            template.get("must_verify_before_trust_or_promotion") or []
        ),
        "read_only_surfaces_to_expand": list(template.get("read_only_surfaces_to_expand") or []),
        "recommended_next_entrypoints": list(template.get("recommended_next_entrypoints") or []),
        "forbidden_uses": list(template.get("forbidden_uses") or []),
        "trust_boundary": {
            "summary_inputs_trusted": bool(trust_boundary.get("summary_inputs_trusted")),
            "claim_trust_mutation": str(trust_boundary.get("claim_trust_mutation") or ""),
            "requires_typed_followup_for_claim_support": bool(
                trust_boundary.get("requires_typed_followup_for_claim_support")
            ),
            "requires_passed_validation_for_tool_derived_support": bool(
                trust_boundary.get("requires_passed_validation_for_tool_derived_support")
            ),
            "requires_exact_source_anchors_for_literature_support": bool(
                trust_boundary.get("requires_exact_source_anchors_for_literature_support")
            ),
        },
        "template_catalog_entrypoint": "aitp-v5 status context-profile-templates",
        "read_only": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _context_pack_cli(session_id: str, *, task_profile: str = "") -> str:
    command = f"aitp-v5 status context-pack {session_id}"
    if task_profile:
        command += f" --task-profile {task_profile}"
    return command


def _context_profile_templates_cli(*, task_profile: str = "") -> str:
    command = "aitp-v5 status context-profile-templates"
    if task_profile:
        command += f" --profile {task_profile}"
    return command


def _join_items(values: list[Any], *, limit: int = 2) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    return "; ".join(items[:limit]) if items else "none"


def _excerpt(value: str, *, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
