"""Pure rendering helpers for bounded session resume cards."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Iterable

from brain.v5.context_compiler_support import bounded_markdown, estimate_context_tokens
from brain.v5.lifecycle_models import CloseoutBoundaryItem, SessionCloseoutRecord


def compact_resume_boundary(card: dict[str, Any]) -> dict[str, Any]:
    """Return the stable boundary shared by every generated startup surface."""

    coverage = card.get("coverage") or {}
    return {
        "kind": "session_resume_boundary",
        "session_id": str(card.get("session_id") or ""),
        "topic_id": str(card.get("topic_id") or ""),
        "closeout_ref": str(card.get("closeout_ref") or ""),
        "milestone_id": str(card.get("milestone_id") or ""),
        "focus_set_ref": str(card.get("focus_set_ref") or ""),
        "boundary_fingerprint": str(card.get("fingerprint") or ""),
        "current_boundary": dict(card.get("current_boundary") or {}),
        "can_say": list(card.get("can_say") or []),
        "cannot_say": list(card.get("cannot_say") or []),
        "open_gaps": list(card.get("open_gaps") or []),
        "failed_routes": list(card.get("failed_routes") or []),
        "next_actions": list(card.get("next_actions") or []),
        "coverage": {
            "content_verified": bool(coverage.get("content_verified")),
            "exhaustive": bool(coverage.get("exhaustive")),
            "relevant_stale": bool(coverage.get("relevant_stale")),
            "changed_state_families": list(coverage.get("changed_state_families") or []),
            "changed_content_families": list(
                coverage.get("changed_content_families") or []
            ),
            "dirty_families": list(coverage.get("dirty_families") or []),
            "read_errors": list(coverage.get("read_errors") or []),
        },
        "exact_expansion_refs": list(card.get("exact_expansion_refs") or []),
        "partial": bool(card.get("partial")),
        "truncated": bool(card.get("truncated")),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def canonical_resume_boundary_json(boundary: dict[str, Any]) -> str:
    return json.dumps(
        boundary,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def compact_context_from_resume(card: dict[str, Any]) -> dict[str, Any]:
    coverage = card.get("coverage") or {}
    content_verified = bool(coverage.get("content_verified"))
    exhaustive = bool(coverage.get("exhaustive"))
    relevant_stale = bool(coverage.get("relevant_stale"))
    scope_state_fresh = bool(
        coverage.get("scope_state_fresh", not relevant_stale)
    )
    scope_content_verified = bool(
        coverage.get("scope_content_verified", content_verified)
    )
    return {
        "kind": "compact_context_boundary",
        "fingerprint": str(card.get("fingerprint") or ""),
        "pack_id": str(card.get("closeout_ref") or f"resume:{card.get('session_id', '')}"),
        "index_status": "stale" if relevant_stale else "fresh",
        "source_index_generation": int(card.get("source_index_generation") or 0),
        "retrieval_coverage": {
            "exhaustive": exhaustive,
            "content_verified": content_verified,
            "relevant_stale": relevant_stale,
            "scope_state_fresh": scope_state_fresh,
            "scope_content_verified": scope_content_verified,
            "can_claim_no_result": False,
            "read_errors": list(coverage.get("read_errors") or []),
        },
        "byte_count": int(card.get("byte_count") or 0),
        "estimated_tokens": int(card.get("estimated_tokens") or 0),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_resume_boundary_section(boundary: dict[str, Any]) -> str:
    serialized = canonical_resume_boundary_json(boundary)
    return (
        "## Session Resume Boundary\n\n"
        "```json\n"
        f"{serialized}\n"
        "```\n\n"
        "Orientation only; exact-expand cited records before trust-sensitive conclusions.\n\n"
    )


def bounded_closeout_lanes(
    closeout: SessionCloseoutRecord,
) -> tuple[dict[str, list[Any]], dict[str, int]]:
    lane_values: dict[str, Iterable[Any]] = {
        "completed_work": closeout.completed_work,
        "can_say": closeout.can_say,
        "cannot_say": closeout.cannot_say,
        "open_gaps": closeout.open_gaps,
        "failed_routes": closeout.failed_routes,
        "next_actions": closeout.next_actions,
    }
    lanes: dict[str, list[Any]] = {}
    omitted: dict[str, int] = {}
    for lane, values in lane_values.items():
        rows = list(values)
        selected = rows[:12]
        lanes[lane] = [
            asdict(value) if isinstance(value, CloseoutBoundaryItem) else value
            for value in selected
        ]
        if len(rows) > len(selected):
            omitted[lane] = len(rows) - len(selected)
    return lanes, omitted


def closeout_exact_refs(
    closeout: SessionCloseoutRecord,
    closeout_ref: str,
) -> tuple[str, ...]:
    boundary_refs = [
        ref
        for lane in (
            closeout.can_say,
            closeout.cannot_say,
            closeout.open_gaps,
            closeout.failed_routes,
            closeout.unverified_notes,
        )
        for item in lane
        for ref in item.source_refs
    ]
    return tuple(
        dict.fromkeys(
            [
                closeout_ref,
                closeout.focus_set_ref,
                *closeout.objective_refs,
                *closeout.source_record_refs,
                *closeout.pending_candidate_batch_refs,
                *closeout.reusable_workflow_candidate_refs,
                *boundary_refs,
            ]
        )
    )


def finalize_resume_card(card: dict[str, Any], *, max_tokens: int) -> dict[str, Any]:
    lines = _resume_lines(card)
    markdown, render_truncated = bounded_markdown(
        lines,
        max_bytes=4000,
        max_tokens=max_tokens,
    )
    card["render_truncated"] = render_truncated
    card["truncated"] = bool(card.get("truncated") or render_truncated)
    card["partial"] = bool(card.get("partial") or render_truncated)
    card["markdown"] = markdown
    card["byte_count"] = len(markdown.encode("utf-8"))
    card["estimated_tokens"] = estimate_context_tokens(markdown)
    card["max_bytes"] = 4000
    card["max_tokens"] = max_tokens
    fingerprint_payload = {
        key: card.get(key)
        for key in (
            "session_id",
            "topic_id",
            "closeout_ref",
            "milestone_id",
            "focus_set_ref",
            "can_say",
            "cannot_say",
            "open_gaps",
            "failed_routes",
            "next_actions",
            "coverage",
            "exact_expansion_refs",
        )
    }
    card["fingerprint"] = hashlib.sha256(
        json.dumps(
            fingerprint_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    boundary = compact_resume_boundary(card)
    card["resume_boundary"] = boundary
    card["resume_boundary_json"] = canonical_resume_boundary_json(boundary)
    return card


def _resume_lines(card: dict[str, Any]) -> list[str]:
    coverage = card.get("coverage") or {}
    lines = [
        "AITP session resume.",
        f"Session: {card.get('session_id', '')} | Topic: {card.get('topic_id', '')}",
        f"Disclosure: {card.get('disclosure_level', '')}",
        f"Closeout: {card.get('closeout_ref') or 'none'}",
        (
            "Coverage: "
            f"content_verified={str(bool(coverage.get('content_verified'))).lower()}; "
            f"relevant_stale={str(bool(coverage.get('relevant_stale'))).lower()}."
        ),
        "Boundary is orientation-only; exact expansion is required before trust conclusions.",
    ]
    for label, key in (
        ("Can say", "can_say"),
        ("Cannot say", "cannot_say"),
        ("Open gaps", "open_gaps"),
        ("Failed routes", "failed_routes"),
    ):
        values = card.get(key) or []
        if values:
            lines.append(f"{label}:")
            lines.extend(f"- {value.get('text', '')}" for value in values)
    if card.get("next_actions"):
        lines.append("Next actions:")
        lines.extend(f"- {value}" for value in card["next_actions"])
    if card.get("exact_expansion_refs"):
        lines.append("Exact expansion refs: " + ", ".join(card["exact_expansion_refs"][:12]))
    return lines
