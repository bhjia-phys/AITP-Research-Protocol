from __future__ import annotations

from typing import Any


def build_control_plane_payload(
    *,
    topic_state: dict[str, Any] | None,
    topic_synopsis: dict[str, Any] | None,
    runtime_mode: str | None,
    active_submode: str | None,
    transition_posture: dict[str, Any] | None,
    operator_checkpoint: dict[str, Any] | None,
    decision_override_active: bool = False,
) -> dict[str, Any]:
    topic_state = topic_state or {}
    topic_synopsis = topic_synopsis or {}
    transition_posture = transition_posture or {}
    operator_checkpoint = operator_checkpoint or {}
    runtime_focus = topic_synopsis.get("runtime_focus") or {}

    task_type = str(
        topic_state.get("task_type")
        or topic_synopsis.get("task_type")
        or runtime_focus.get("task_type")
        or "unspecified"
    )
    lane = str(
        topic_synopsis.get("lane")
        or topic_state.get("lane")
        or "unspecified"
    )
    layer = str(
        topic_state.get("resume_stage")
        or runtime_focus.get("resume_stage")
        or topic_synopsis.get("resume_stage")
        or "unspecified"
    )
    mode = str(runtime_mode or "unspecified")
    checkpoint_status = str(operator_checkpoint.get("status") or "missing")

    return {
        "task_type": task_type,
        "lane": lane,
        "layer": layer,
        "mode": mode,
        "active_submode": active_submode,
        "transition": {
            "transition_kind": str(transition_posture.get("transition_kind") or "unspecified"),
            "transition_reason": str(transition_posture.get("transition_reason") or ""),
            "allowed_targets": list(transition_posture.get("allowed_targets") or []),
        },
        "h_plane": {
            "checkpoint_status": checkpoint_status,
            "checkpoint_kind": operator_checkpoint.get("checkpoint_kind"),
            "requires_human_checkpoint": bool(transition_posture.get("requires_human_checkpoint")),
            "decision_override_active": bool(decision_override_active),
        },
    }


def build_runtime_bundle_control_plane(
    *,
    topic_state: dict[str, Any] | None,
    topic_synopsis: dict[str, Any] | None,
    runtime_mode_payload: dict[str, Any],
    operator_checkpoint: dict[str, Any] | None,
    decision_override_active: bool = False,
) -> dict[str, Any]:
    return build_control_plane_payload(
        topic_state=topic_state,
        topic_synopsis=topic_synopsis,
        runtime_mode=runtime_mode_payload.get("runtime_mode"),
        active_submode=runtime_mode_payload.get("active_submode"),
        transition_posture=runtime_mode_payload.get("transition_posture"),
        operator_checkpoint=operator_checkpoint,
        decision_override_active=decision_override_active,
    )


def control_note_override_active(decision_surface: dict[str, Any] | None) -> bool:
    decision_surface = decision_surface or {}
    control_note_status = str(decision_surface.get("control_note_status") or "missing")
    decision_contract_status = str(decision_surface.get("decision_contract_status") or "missing")
    return control_note_status in {"active_redirect", "stop"} or decision_contract_status != "missing"


def control_plane_markdown_lines(control_plane: dict[str, Any] | None) -> list[str]:
    control_plane = control_plane or {}
    h_plane = control_plane.get("h_plane") or {}
    return [
        "## Control plane",
        "",
        f"- Task type: `{control_plane.get('task_type') or '(missing)'}`",
        f"- Lane: `{control_plane.get('lane') or '(missing)'}`",
        f"- Layer: `{control_plane.get('layer') or '(missing)'}`",
        f"- Mode: `{control_plane.get('mode') or '(missing)'}`",
        f"- Active submode: `{control_plane.get('active_submode') or '(none)'}`",
        f"- H-plane checkpoint status: `{h_plane.get('checkpoint_status') or '(missing)'}`",
        f"- H-plane checkpoint kind: `{h_plane.get('checkpoint_kind') or '(none)'}`",
        f"- Decision override active: `{str(bool(h_plane.get('decision_override_active'))).lower()}`",
        "",
    ]


def build_control_plane_audit_section(control_plane: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    control_plane = control_plane or {}
    status = "present" if control_plane else "missing"
    transition = control_plane.get("transition") or {}
    h_plane = control_plane.get("h_plane") or {}

    return {
        "status": {
            "status": status,
            "detail": "Unified control-plane projection is available." if control_plane else "Control-plane projection missing.",
        },
        "task_type": {
            "status": "present" if control_plane.get("task_type") else "missing",
            "detail": str(control_plane.get("task_type") or ""),
        },
        "lane": {
            "status": "present" if control_plane.get("lane") else "missing",
            "detail": str(control_plane.get("lane") or ""),
        },
        "layer": {
            "status": "present" if control_plane.get("layer") else "missing",
            "detail": str(control_plane.get("layer") or ""),
        },
        "mode": {
            "status": "present" if control_plane.get("mode") else "missing",
            "detail": str(control_plane.get("mode") or ""),
        },
        "transition": {
            "status": "present" if transition.get("transition_kind") else "missing",
            "detail": str(transition.get("transition_kind") or ""),
        },
        "h_plane": {
            "status": "present" if h_plane.get("checkpoint_status") else "missing",
            "detail": str(h_plane.get("checkpoint_status") or ""),
        },
    }
