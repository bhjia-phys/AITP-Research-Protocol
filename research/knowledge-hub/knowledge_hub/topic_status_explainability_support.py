from __future__ import annotations

from datetime import datetime
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def derive_topic_status_explainability(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any],
    interaction_state: dict[str, Any],
    selected_pending_action: dict[str, Any] | None,
    idea_packet: dict[str, Any],
    operator_checkpoint: dict[str, Any],
    open_gap_summary: dict[str, Any],
    validation_contract: dict[str, Any],
) -> dict[str, Any]:
    decision_surface = interaction_state.get("decision_surface") or {}
    queue_surface = interaction_state.get("action_queue_surface") or {}
    pointers = topic_state.get("pointers") or {}
    selected_action_summary = str((selected_pending_action or {}).get("summary") or "").strip()
    selected_action_type = str((selected_pending_action or {}).get("action_type") or "").strip()
    selected_action_id = str((selected_pending_action or {}).get("action_id") or "").strip()
    selected_action_auto_runnable = bool((selected_pending_action or {}).get("auto_runnable"))
    current_route_choice = {
        "resume_stage": str(topic_state.get("resume_stage") or ""),
        "decision_source": str(decision_surface.get("decision_source") or ""),
        "queue_source": str(queue_surface.get("queue_source") or ""),
        "selected_action_id": selected_action_id or None,
        "selected_action_type": selected_action_type or None,
        "selected_action_summary": selected_action_summary or None,
        "selected_action_auto_runnable": selected_action_auto_runnable,
        "selected_validation_route_path": self._normalize_artifact_path(
            pointers.get("selected_validation_route_path")
        ),
        "next_action_decision_note_path": self._normalize_artifact_path(
            pointers.get("next_action_decision_note_path")
            or decision_surface.get("next_action_decision_note_path")
        ),
    }
    last_evidence_return = self._derive_last_evidence_return(
        topic_state=topic_state,
        validation_contract=validation_contract,
    )

    active_human_need: dict[str, Any]
    blocker_summary: list[str]
    if str(operator_checkpoint.get("status") or "").strip() == "requested":
        blocker_summary = self._dedupe_strings(list(operator_checkpoint.get("blocker_summary") or []))
        active_human_need = {
            "status": "requested",
            "kind": str(operator_checkpoint.get("checkpoint_kind") or ""),
            "path": self._normalize_artifact_path(operator_checkpoint.get("note_path")),
            "summary": str(operator_checkpoint.get("question") or ""),
        }
        why_this_topic_is_here = (
            (blocker_summary[0] if blocker_summary else "")
            or str(operator_checkpoint.get("question") or "").strip()
            or "AITP paused at an active operator checkpoint."
        )
    elif str(idea_packet.get("status") or "").strip() == "needs_clarification":
        blocker_summary = self._dedupe_strings(
            list(idea_packet.get("clarification_questions") or [])
            or [f"Missing idea-packet fields: {', '.join(idea_packet.get('missing_fields') or []) or '(none)'}"]
        )
        active_human_need = {
            "status": "requested",
            "kind": "idea_packet_clarification",
            "path": self._normalize_artifact_path(idea_packet.get("note_path")),
            "summary": str(idea_packet.get("status_reason") or ""),
        }
        why_this_topic_is_here = (
            (blocker_summary[0] if blocker_summary else "")
            or str(idea_packet.get("status_reason") or "").strip()
            or "AITP is holding at the research-intent gate."
        )
    else:
        blocker_summary = self._dedupe_strings(list(open_gap_summary.get("blockers") or []))
        active_human_need = {
            "status": "none",
            "kind": "none",
            "path": None,
            "summary": "No active human checkpoint is currently blocking the bounded loop.",
        }
        why_this_topic_is_here = (
            (blocker_summary[0] if blocker_summary else "")
            or (
                f"The topic is currently following `{selected_action_summary}` at stage "
                f"`{topic_state.get('resume_stage') or '(missing)'}`."
                if selected_action_summary
                else ""
            )
            or str(topic_state.get("resume_reason") or "").strip()
            or "AITP is holding the current bounded route defined by the runtime state."
        )

    next_bounded_action = {
        "status": "selected" if selected_action_summary else "missing",
        "action_id": selected_action_id or None,
        "action_type": selected_action_type or None,
        "summary": selected_action_summary or "No bounded action is currently selected.",
        "auto_runnable": selected_action_auto_runnable,
    }
    return {
        "topic_slug": topic_slug,
        "current_status_summary": (
            f"Stage `{topic_state.get('resume_stage') or '(missing)'}`; "
            f"next `{next_bounded_action['summary']}`; "
            f"human need `{active_human_need['kind']}`; "
            f"last evidence `{last_evidence_return['kind']}`."
        ),
        "why_this_topic_is_here": why_this_topic_is_here,
        "current_route_choice": current_route_choice,
        "last_evidence_return": last_evidence_return,
        "active_human_need": active_human_need,
        "blocker_summary": blocker_summary,
        "next_bounded_action": next_bounded_action,
        "updated_at": _now_iso(),
    }
