"""Read-only materializers for task-profile report and closeout drafts."""

from __future__ import annotations

from typing import Any

from brain.v5.context_pack import build_aitp_context_pack
from brain.v5.context_profile_templates import FORBIDDEN_USES
from brain.v5.paths import WorkspacePaths


SUPPORTED_DRAFT_PROFILES = ("group_meeting_report", "closeout")


def build_context_profile_draft(
    ws: WorkspacePaths,
    session_id: str,
    *,
    profile_id: str = "closeout",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict[str, Any]:
    """Fill a report/closeout scaffold from typed-record context without writes."""

    selected_profile = _selected_profile_id(profile_id)
    context_pack = build_aitp_context_pack(
        ws,
        session_id,
        max_lines=max_lines,
        candidate_limit=candidate_limit,
        task_profile=selected_profile,
    )
    template_hint = context_pack.get("profile_template_hint") or {}
    section_ids = _section_order(selected_profile, template_hint)
    sections = [_draft_section(section_id, context_pack, template_hint) for section_id in section_ids]
    markdown = _draft_markdown(selected_profile, context_pack, sections)

    return {
        "ok": True,
        "kind": "context_profile_draft",
        "draft_version": "aitp.v5.context_profile_draft.v1",
        "requested_profile_id": str(profile_id or ""),
        "profile_id": selected_profile,
        "draft_kind": "closeout_draft" if selected_profile == "closeout" else "group_meeting_report_draft",
        "session_id": str(context_pack.get("session_id") or ""),
        "topic_id": str(context_pack.get("topic_id") or ""),
        "context_pack_id": str(context_pack.get("pack_id") or ""),
        "context_pack_fingerprint": str(context_pack.get("fingerprint") or ""),
        "context_pack_line_count": int(context_pack.get("line_count") or 0),
        "profile_template_hint": template_hint,
        "sections": sections,
        "section_count": len(sections),
        "missing_section_ids": [
            section["section_id"]
            for section in sections
            if section.get("coverage_status") == "missing_context"
        ],
        "markdown": markdown,
        "recommended_next_entrypoints": _recommended_next_entrypoints(context_pack, template_hint),
        "draft_policy": _draft_policy(),
        "source_records": {
            "derived_surfaces": [
                "aitp_context_pack",
                "context_profile_template_catalog",
                "compact_execution_brief",
            ],
            "context_pack_id": [str(context_pack.get("pack_id") or "")],
            "context_pack_fingerprint": [str(context_pack.get("fingerprint") or "")],
        },
        "read_surface_effect": "context_profile_draft_only",
        "truth_source": "typed_records_derived_context_pack_and_static_template",
        "draft_creates_records": False,
        "read_only": True,
        "requires_explicit_next_action": True,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
    }


def _selected_profile_id(profile_id: str) -> str:
    requested = str(profile_id or "").strip() or "closeout"
    if requested not in SUPPORTED_DRAFT_PROFILES:
        return "closeout"
    return requested


def _section_order(profile_id: str, template_hint: dict[str, Any]) -> list[str]:
    if profile_id == "closeout":
        section_ids = list(template_hint.get("closeout_section_order") or [])
    else:
        section_ids = list(template_hint.get("report_section_order") or [])
    return [str(section_id) for section_id in section_ids if str(section_id).strip()]


def _draft_section(section_id: str, context_pack: dict[str, Any], template_hint: dict[str, Any]) -> dict[str, Any]:
    items, source_fields = _section_items(section_id, context_pack, template_hint)
    return {
        "section_id": section_id,
        "heading": section_id.replace("_", " ").title(),
        "draft_items": items,
        "item_count": len(items),
        "source_fields": source_fields,
        "missing_inputs": [] if items else [_missing_input(section_id)],
        "coverage_status": "filled_from_context_pack" if items else "missing_context",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
    }


def _section_items(
    section_id: str,
    context_pack: dict[str, Any],
    template_hint: dict[str, Any],
) -> tuple[list[str], list[str]]:
    if section_id in {"current_focus", "active_claim"}:
        return _focus_items(context_pack), ["current_objective", "active_work_package", "relevant_claims"]
    if section_id == "verified_content":
        return _text_items(context_pack.get("can_say")), ["can_say"]
    if section_id in {"uncertainty", "non_promotable_content"}:
        return _non_promotable_items(context_pack, template_hint), ["cannot_say", "blockers", "forbidden_uses"]
    if section_id in {"records", "durable_records_created"}:
        return _record_items(context_pack), ["source_records", "recent_relevant_artifacts"]
    if section_id in {"next_actions", "safe_resume_entrypoints"}:
        return _next_action_items(context_pack, template_hint), ["next_valid_actions", "expand", "recommended_next_entrypoints"]
    if section_id == "missing_typed_records":
        return _missing_record_items(context_pack), ["blockers", "distillation_status.top_candidates.missing_requirements"]
    if section_id in {"must_verify_next", "validation_gap"}:
        return _text_items(template_hint.get("must_verify_before_trust_or_promotion")), [
            "profile_template_hint.must_verify_before_trust_or_promotion"
        ]
    return _generic_section_items(section_id, context_pack), ["context_pack"]


def _focus_items(context_pack: dict[str, Any]) -> list[str]:
    objective = context_pack.get("current_objective") if isinstance(context_pack.get("current_objective"), dict) else {}
    package = context_pack.get("active_work_package") if isinstance(context_pack.get("active_work_package"), dict) else {}
    items = [
        f"Objective: {objective.get('title') or context_pack.get('topic_id') or 'unknown'}",
        f"Active work package: {package.get('title') or 'none'}",
    ]
    for claim in list(context_pack.get("relevant_claims") or [])[:3]:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id") or "")
        statement = str(claim.get("statement") or claim.get("statement_excerpt") or "")
        if claim_id or statement:
            items.append(f"Claim {claim_id}: {statement}".strip())
    return [item for item in items if item.strip()]


def _record_items(context_pack: dict[str, Any]) -> list[str]:
    items = []
    for artifact in list(context_pack.get("recent_relevant_artifacts") or [])[:5]:
        items.append(str(artifact))
    source_records = context_pack.get("source_records") if isinstance(context_pack.get("source_records"), dict) else {}
    for key, values in source_records.items():
        if not values:
            continue
        if isinstance(values, list):
            items.append(f"{key}: {', '.join(str(value) for value in values[:4])}")
        else:
            items.append(f"{key}: {values}")
    if context_pack.get("pack_id"):
        items.append(f"context_pack: {context_pack['pack_id']}")
    return items


def _non_promotable_items(context_pack: dict[str, Any], template_hint: dict[str, Any]) -> list[str]:
    items = _text_items(context_pack.get("cannot_say")) + _text_items(context_pack.get("blockers"))
    forbidden = _text_items(template_hint.get("forbidden_uses"))[:6]
    if forbidden:
        items.append(f"Forbidden uses: {', '.join(forbidden)}")
    items.append("Draft text is not evidence, validation, final-gate satisfaction, or trust authority.")
    return items


def _next_action_items(context_pack: dict[str, Any], template_hint: dict[str, Any]) -> list[str]:
    items = _text_items(context_pack.get("next_valid_actions"))
    expand = context_pack.get("expand") if isinstance(context_pack.get("expand"), dict) else {}
    for key in ("context_pack_cli", "context_profile_templates_cli"):
        if expand.get(key):
            items.append(str(expand[key]))
    items.extend(_text_items(template_hint.get("recommended_next_entrypoints"))[:5])
    return _dedupe(items)


def _missing_record_items(context_pack: dict[str, Any]) -> list[str]:
    items = _text_items(context_pack.get("blockers"))
    distillation = context_pack.get("distillation_status") if isinstance(context_pack.get("distillation_status"), dict) else {}
    for candidate in list(distillation.get("top_candidates") or [])[:5]:
        if not isinstance(candidate, dict):
            continue
        missing = ", ".join(str(item) for item in candidate.get("missing_requirements") or [])
        if missing:
            items.append(f"{candidate.get('candidate_id')}: {missing}")
    return _dedupe(items)


def _generic_section_items(section_id: str, context_pack: dict[str, Any]) -> list[str]:
    if section_id in {"blockers", "open_gaps"}:
        return _text_items(context_pack.get("blockers"))
    if section_id == "validation_results":
        return ["Expand validation-specific surfaces before using any validation conclusion."]
    return ["Expand the named read-only surfaces before filling this section with claim-relevant details."]


def _recommended_next_entrypoints(context_pack: dict[str, Any], template_hint: dict[str, Any]) -> list[str]:
    expand = context_pack.get("expand") if isinstance(context_pack.get("expand"), dict) else {}
    entries = [
        str(expand.get("context_pack_cli") or ""),
        str(expand.get("context_profile_templates_cli") or ""),
        *[str(item) for item in template_hint.get("recommended_next_entrypoints") or []],
    ]
    return _dedupe([entry for entry in entries if entry])


def _draft_policy() -> dict[str, Any]:
    return {
        "host_may_use_for": ["human_report_draft", "session_closeout_draft", "safe_resume_planning"],
        "requires_runtime_context_pack_before_final_answer": True,
        "requires_explicit_next_entrypoint": True,
        "forbidden_uses": list(FORBIDDEN_USES),
        "records_validation_result": False,
        "source_support_result": False,
        "claim_trust_mutation": "none",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _draft_markdown(profile_id: str, context_pack: dict[str, Any], sections: list[dict[str, Any]]) -> str:
    title = "AITP Closeout Draft" if profile_id == "closeout" else "AITP Group Meeting Draft"
    lines = [
        f"# {title}",
        "",
        f"Session: {context_pack.get('session_id')} | Topic: {context_pack.get('topic_id')}",
        "Boundary: read-only draft; not evidence, validation, memory, final gate, or trust update.",
        "",
    ]
    for section in sections:
        lines.append(f"## {section['heading']}")
        if section.get("draft_items"):
            lines.extend(f"- {item}" for item in section["draft_items"])
        else:
            lines.append("- Missing typed context for this section.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _text_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        value = [value] if value else []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _missing_input(section_id: str) -> str:
    return f"no context_pack data available for {section_id}"
