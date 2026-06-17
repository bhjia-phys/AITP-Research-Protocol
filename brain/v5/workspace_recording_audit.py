"""Workspace-level recording navigation audit."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.recording_navigator import build_recording_navigation_state
from brain.v5.workspace_recovery_audit import build_workspace_recovery_audit


_SHALLOW_SLOT_FAMILIES = {
    "source_asset": "source_assets",
    "reference_location": "reference_locations",
    "tool_run": "tool_runs",
    "code_state": "code_states",
    "artifact": "artifacts",
    "evidence": "evidence",
    "physics_object": "physics_objects",
    "object_relation": "object_relations",
    "research_route": "routes",
    "research_run": "research_runs",
    "research_run_event": "research_run_events",
    "proof_obligation": "proof_obligations",
    "source_reconstruction_review": "source_reconstruction_reviews",
    "validation_contract": "validation_contracts",
    "validation_result": "validation_results",
    "human_checkpoint": "checkpoints",
    "sensemaking_report": "sensemaking_reports",
}

_SHALLOW_RECOMMENDATION_ORDER = [
    "source_asset",
    "reference_location",
    "code_state",
    "artifact",
    "evidence",
    "proof_obligation",
    "source_reconstruction_review",
    "validation_contract",
    "validation_result",
    "research_run",
    "research_run_event",
]

_TOPIC_SPECIFIC_DEEP_THRESHOLD = 8


def build_workspace_recording_audit(
    ws: WorkspacePaths,
    *,
    migration_plan_path: str | Path | None = None,
    topics: list[str] | None = None,
    limit: int = 40,
) -> dict[str, Any]:
    """Return a read-only audit of per-topic progressive recording navigation."""

    selected_topics = sorted({str(topic) for topic in (topics or []) if str(topic)})
    deep_navigation = bool(selected_topics) and len(selected_topics) <= _TOPIC_SPECIFIC_DEEP_THRESHOLD
    recovery = build_workspace_recovery_audit(
        ws,
        migration_plan_path=migration_plan_path,
        topics=selected_topics,
    )
    registry_counts = _registry_slot_count_index(ws)
    rows = [
        _recording_row(
            ws,
            row,
            registry_counts=registry_counts,
            deep_navigation=deep_navigation,
            limit=limit,
        )
        for row in recovery.get("topic_rows", [])
        if isinstance(row, dict)
    ]
    status_counts = Counter(str(row["recording_status"]) for row in rows)
    recommended_slot_counts = Counter(
        slot
        for row in rows
        for slot in row.get("recommended_slots", [])
        if isinstance(slot, str) and slot
    )
    zero_slot_counts = Counter(
        slot
        for row in rows
        for slot in row.get("zero_count_slots", [])
        if isinstance(slot, str) and slot
    )
    return {
        "kind": "aitp_workspace_recording_audit",
        "canonical_topics_root": str(ws.base),
        "canonical_store": str(ws.root),
        "migration_plan_source": str(recovery.get("migration_plan_source") or ""),
        "recovery_audit_source": str(recovery.get("recovery_audit_source") or ""),
        "topics": selected_topics,
        "summary": {
            "topic_count": len(rows),
            "navigable_topic_count": sum(
                1
                for row in rows
                if row.get("recording_status") in {"navigation_ready", "navigation_ready_with_blockers"}
            ),
            "blocked_topic_count": sum(
                1
                for row in rows
                if row.get("recording_status") in {"blocked_by_recovery_gap", "navigation_error"}
            ),
            "human_review_topic_count": sum(1 for row in rows if row.get("human_review_required")),
            "status_counts": dict(sorted(status_counts.items())),
            "recommended_slot_counts": dict(sorted(recommended_slot_counts.items())),
            "zero_slot_counts": dict(sorted(zero_slot_counts.items())),
        },
        "topic_rows": rows,
        "navigation_sequence": [
            "aitp_v5_build_workspace_recording_audit",
            "aitp_v5_get_recording_navigation_state",
            "aitp_v5_expand_recording_slot",
            "existing typed write or preflight tool",
            "aitp_v5_verify_recording_effect",
        ],
        "disclosure_policy": {
            "workspace_level": "shallow_counts_by_topic",
            "topic_level": "deep_navigation_state_only_after_topic_selection",
            "deep_navigation_enabled": deep_navigation,
            "topic_specific_deep_threshold": _TOPIC_SPECIFIC_DEEP_THRESHOLD,
        },
        "write_boundary": "workspace recording audit is read-only; writes happen only after expanding one topic slot",
        "truth_source": "typed_session_bindings_relation_maps_and_recording_navigation_state",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_workspace_recording_audit_markdown(payload: dict[str, Any], *, max_rows: int = 160) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP Workspace Recording Audit",
        "",
        "This read-only audit shows which topics can enter progressive recording navigation and which first-level slots are currently recommended.",
        "",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Topics: `{summary.get('topic_count', 0)}`",
        f"- Navigable topics: `{summary.get('navigable_topic_count', 0)}`",
        f"- Blocked topics: `{summary.get('blocked_topic_count', 0)}`",
        f"- Human-review topics: `{summary.get('human_review_topic_count', 0)}`",
        "",
        "## Recommended Slot Counts",
        "",
    ]
    for key, value in (summary.get("recommended_slot_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Topic Rows",
            "",
            "| Topic | Recording Status | Recovery Status | Session | Active Claim | Next Slot | Recommended Slots | Human Review |",
            "|---|---|---|---|---|---|---|---:|",
        ]
    )
    for row in payload.get("topic_rows", [])[:max_rows]:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {topic} | {status} | {recovery} | `{session}` | `{claim}` | {next_slot} | {slots} | {human} |".format(
                topic=_cell(row.get("topic_id", "")),
                status=_cell(row.get("recording_status", "")),
                recovery=_cell(row.get("recovery_status", "")),
                session=_cell(row.get("session_id", "")),
                claim=_cell(row.get("active_claim_id", "")),
                next_slot=_cell(row.get("next_slot", "")),
                slots=_cell(", ".join(row.get("recommended_slots", []) or [])),
                human=str(bool(row.get("human_review_required"))).lower(),
            )
        )
    if int(summary.get("topic_count") or 0) > max_rows:
        lines.extend(["", f"Showing first `{max_rows}` rows. Use the JSON audit for the complete topic list."])
    lines.extend(["", "This surface is orientation-only and cannot update kernel state or claim trust.", ""])
    return "\n".join(lines)


def write_workspace_recording_audit(
    payload: dict[str, Any],
    *,
    json_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    if json_path:
        path = Path(json_path)
        write_text_atomic(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        result["json_path"] = str(path)
    if report_path:
        path = Path(report_path)
        write_text_atomic(path, render_workspace_recording_audit_markdown(payload))
        result["report_path"] = str(path)
    return result


def _recording_row(
    ws: WorkspacePaths,
    recovery_row: dict[str, Any],
    *,
    registry_counts: dict[str, dict[str, dict[str, int]]],
    deep_navigation: bool,
    limit: int,
) -> dict[str, Any]:
    topic_id = str(recovery_row.get("topic_id") or "")
    session_id = str(recovery_row.get("session_id") or "")
    active_claim_id = str(recovery_row.get("active_claim_id") or "")
    recovery_status = str(recovery_row.get("recovery_status") or "")
    base = {
        "topic_id": topic_id,
        "session_id": session_id,
        "active_claim_id": active_claim_id,
        "recovery_status": recovery_status,
        "recovery_gap": str(recovery_row.get("recovery_gap") or ""),
        "migration_review_required": bool(recovery_row.get("migration_review_required")),
        "recording_status": "blocked_by_recovery_gap",
        "first_level_slot_counts": {},
        "first_level_slots": [],
        "recommended_slots": [],
        "zero_count_slots": [],
        "next_slot": "",
        "next_read_tool": "",
        "next_verify_tool": "",
        "relation_blockers": [],
        "next_valid_action": str(recovery_row.get("next_valid_action") or ""),
        "human_review_required": True,
        "human_review_reasons": [],
        "truth_source": "workspace_recovery_audit",
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if recovery_status != "recovery_ready":
        return {
            **base,
            "human_review_reasons": _human_review_reasons(recovery_row, []),
        }
    shallow_counts = _slot_counts_for(registry_counts, topic_id, active_claim_id)
    shallow_recommended = _shallow_recommended_slots(shallow_counts)
    if not deep_navigation:
        human_reasons = _human_review_reasons(recovery_row, [])
        return {
            **base,
            "recording_status": "navigation_ready_with_blockers" if human_reasons else "navigation_ready",
            "first_level_slot_counts": shallow_counts,
            "first_level_slots": _shallow_slot_summaries(shallow_counts),
            "recommended_slots": shallow_recommended,
            "zero_count_slots": [slot for slot, count in shallow_counts.items() if count == 0],
            "next_slot": shallow_recommended[0] if shallow_recommended else "",
            "next_read_tool": "aitp_v5_get_recording_navigation_state",
            "next_verify_tool": "aitp_v5_verify_recording_effect" if shallow_recommended else "",
            "human_review_required": bool(human_reasons),
            "human_review_reasons": human_reasons,
            "truth_source": "typed_registry_shallow_counts",
        }
    try:
        state = build_recording_navigation_state(ws, session_id, claim_id=active_claim_id, limit=limit)
    except Exception as exc:  # pragma: no cover - defensive audit path
        return {
            **base,
            "recording_status": "navigation_error",
            "recovery_gap": f"{type(exc).__name__}: {exc}",
            "human_review_reasons": ["recording navigation state could not be built"],
        }
    blockers = [
        str(blocker)
        for blocker in (state.get("relation_context") or {}).get("current_blockers", [])
        if str(blocker)
    ]
    first_level_slots = _compact_first_level_slots(state.get("first_level_slots", []))
    slot_counts = {slot["slot"]: slot["current_count"] for slot in first_level_slots}
    recommended_slots = [str(slot) for slot in state.get("recommended_slots", []) if str(slot)]
    human_reasons = _human_review_reasons(recovery_row, blockers)
    status = "navigation_ready_with_blockers" if blockers or human_reasons else "navigation_ready"
    return {
        **base,
        "recording_status": status,
        "first_level_slot_counts": slot_counts,
        "first_level_slots": first_level_slots,
        "recommended_slots": recommended_slots,
        "zero_count_slots": [slot for slot, count in slot_counts.items() if count == 0],
        "next_slot": recommended_slots[0] if recommended_slots else "",
        "next_read_tool": "aitp_v5_expand_recording_slot" if recommended_slots else "",
        "next_verify_tool": "aitp_v5_verify_recording_effect" if recommended_slots else "",
        "relation_blockers": blockers,
        "next_valid_action": str(
            (
                (state.get("relation_context") or {}).get("next_valid_actions")
                or [recovery_row.get("next_valid_action") or ""]
            )[0]
        ),
        "human_review_required": bool(human_reasons),
        "human_review_reasons": human_reasons,
        "truth_source": "recording_navigation_state",
    }


def _compact_first_level_slots(items: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for item in items:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "slot": str(item.get("slot") or ""),
                "record_kind": str(item.get("record_kind") or ""),
                "current_count": int(item.get("current_count") or 0),
                "recommended_write_tool": str(item.get("recommended_write_tool") or ""),
                "expand_with": str(item.get("expand_with") or ""),
                "read_only_at_this_layer": bool(item.get("read_only_at_this_layer")),
                "can_update_claim_trust": bool(item.get("can_update_claim_trust")),
            }
        )
    return out


def _registry_slot_count_index(ws: WorkspacePaths) -> dict[str, dict[str, dict[str, int]]]:
    index: dict[str, dict[str, dict[str, int]]] = {}
    for slot, family in _SHALLOW_SLOT_FAMILIES.items():
        root = ws.registry_dir(family)
        if not root.exists():
            continue
        for path in sorted(root.glob("*.md")):
            try:
                frontmatter, _body = read_md(path)
            except (OSError, ValueError, TypeError):
                continue
            topic_id = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
            claim_id = str(
                frontmatter.get("claim_id")
                or frontmatter.get("active_claim_id")
                or frontmatter.get("source_claim_id")
                or ""
            )
            if not topic_id and slot == "code_state":
                linked = frontmatter.get("linked_records") if isinstance(frontmatter.get("linked_records"), dict) else {}
                topic_id = str(linked.get("topic_id") or linked.get("topic") or "")
                claim_id = str(claim_id or linked.get("claim_id") or linked.get("claim") or "")
            if not topic_id:
                continue
            topic_counts = index.setdefault(topic_id, {}).setdefault("", _zero_counts())
            topic_counts[slot] = topic_counts.get(slot, 0) + 1
            if claim_id:
                claim_counts = index.setdefault(topic_id, {}).setdefault(claim_id, _zero_counts())
                claim_counts[slot] = claim_counts.get(slot, 0) + 1
    return index


def _slot_counts_for(
    index: dict[str, dict[str, dict[str, int]]],
    topic_id: str,
    claim_id: str,
) -> dict[str, int]:
    topic_index = index.get(topic_id, {})
    counts = dict(topic_index.get(claim_id) or topic_index.get("") or _zero_counts())
    for slot in _SHALLOW_SLOT_FAMILIES:
        counts.setdefault(slot, 0)
    counts["trust_preflight"] = 0
    return counts


def _zero_counts() -> dict[str, int]:
    counts = {slot: 0 for slot in _SHALLOW_SLOT_FAMILIES}
    counts["trust_preflight"] = 0
    return counts


def _shallow_recommended_slots(counts: dict[str, int]) -> list[str]:
    out = [slot for slot in _SHALLOW_RECOMMENDATION_ORDER if int(counts.get(slot, 0) or 0) == 0]
    if not out and int(counts.get("sensemaking_report", 0) or 0) == 0:
        out.append("sensemaking_report")
    return out


def _shallow_slot_summaries(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "slot": slot,
            "record_kind": slot,
            "current_count": int(counts.get(slot, 0) or 0),
            "recommended_write_tool": "",
            "expand_with": "aitp_v5_get_recording_navigation_state",
            "read_only_at_this_layer": True,
            "can_update_claim_trust": False,
        }
        for slot in sorted(counts)
    ]


def _human_review_reasons(recovery_row: dict[str, Any], blockers: list[str]) -> list[str]:
    reasons: list[str] = []
    if recovery_row.get("migration_review_required"):
        reasons.append("migration review is required before treating recovery as settled")
    recovery_gap = str(recovery_row.get("recovery_gap") or "")
    if recovery_gap:
        reasons.append(recovery_gap)
    for blocker in blockers:
        lowered = blocker.lower()
        if any(token in lowered for token in ("human", "semantic", "divergence", "checkpoint", "trust")):
            reasons.append(blocker)
    return list(dict.fromkeys(reasons))


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
