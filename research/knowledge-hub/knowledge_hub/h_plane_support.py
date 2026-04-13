from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _control_note_details(control_note_path: Path, innovation_direction_path: Path, innovation_decisions_path: Path) -> dict[str, Any]:
    directive = ""
    summary = ""
    if control_note_path.exists():
        text = control_note_path.read_text(encoding="utf-8")
        directive_match = re.search(r"^directive:\s*(?P<value>.+)$", text, flags=re.MULTILINE)
        summary_match = re.search(r"^summary:\s*(?P<value>.+)$", text, flags=re.MULTILINE)
        directive = str((directive_match.group("value") if directive_match else "")).strip()
        summary = str((summary_match.group("value") if summary_match else "")).strip()
    latest_decision = (_read_jsonl(innovation_decisions_path) or [{}])[-1]
    decision = str(latest_decision.get("decision") or "").strip()
    if directive == "human_redirect":
        status = "active_redirect"
    elif directive in {"pause", "stop"}:
        status = "paused_by_control_note"
    elif directive:
        status = f"active_{directive}"
    elif decision:
        status = f"{decision}_recorded"
    else:
        status = "none"
    return {
        "status": status,
        "directive": directive or None,
        "summary": summary or str(latest_decision.get("summary") or "").strip(),
        "control_note_path": str(control_note_path) if control_note_path.exists() else "",
        "innovation_direction_path": str(innovation_direction_path) if innovation_direction_path.exists() else "",
        "innovation_decisions_path": str(innovation_decisions_path) if innovation_decisions_path.exists() else "",
    }


def _registry_details(self, topic_slug: str) -> dict[str, Any]:
    registry = self._load_active_topics_registry()
    if not registry:
        return {
            "focus_state": "unknown",
            "operator_status": "unknown",
            "active_topics_path": str(self._active_topics_registry_paths()["json"]),
        }
    row = next(
        (item for item in (registry.get("topics") or []) if str(item.get("topic_slug") or "").strip() == topic_slug),
        {},
    )
    return {
        "focus_state": str(row.get("focus_state") or "background"),
        "operator_status": str(row.get("operator_status") or row.get("status") or "unknown"),
        "active_topics_path": str(self._active_topics_registry_paths()["json"]),
    }


def build_h_plane_payload(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
    operator_checkpoint: dict[str, Any] | None,
    promotion_gate: dict[str, Any] | None,
    updated_by: str,
) -> dict[str, Any]:
    topic_state = topic_state or {}
    operator_checkpoint = operator_checkpoint or {}
    promotion_gate = promotion_gate or {}
    runtime_root = self._runtime_root(topic_slug)
    control_note_path = runtime_root / "control_note.md"
    innovation_direction_path = runtime_root / "innovation_direction.md"
    innovation_decisions_path = runtime_root / "innovation_decisions.jsonl"
    steering = _control_note_details(control_note_path, innovation_direction_path, innovation_decisions_path)
    checkpoint = {
        "status": str(operator_checkpoint.get("status") or "missing"),
        "checkpoint_kind": operator_checkpoint.get("checkpoint_kind"),
        "active": bool(operator_checkpoint.get("active")),
        "note_path": str(operator_checkpoint.get("note_path") or ""),
    }
    approval = {
        "status": str(promotion_gate.get("status") or "not_requested"),
        "candidate_id": str(promotion_gate.get("candidate_id") or ""),
        "backend_id": str(promotion_gate.get("backend_id") or ""),
        "gate_path": str(self._promotion_gate_paths(topic_slug)["json"]) if self._promotion_gate_paths(topic_slug)["json"].exists() else "",
        "gate_note_path": str(self._promotion_gate_paths(topic_slug)["note"]) if self._promotion_gate_paths(topic_slug)["note"].exists() else "",
        "approved_by": str(promotion_gate.get("approved_by") or ""),
    }
    registry = _registry_details(self, topic_slug)
    blocking_steering_statuses = {
        "active_redirect",
        "paused_by_control_note",
        "active_pause",
        "active_stop",
    }
    active_human_control = (
        steering["status"] in blocking_steering_statuses
        or checkpoint["status"] == "requested"
        or approval["status"] in {"pending_human_approval", "approved"}
        or registry["operator_status"] == "paused"
    )
    return {
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "overall_status": "active_human_control" if active_human_control else "steady",
        "steering": steering,
        "checkpoint": checkpoint,
        "approval": approval,
        "registry": registry,
    }


def build_h_plane_audit_section(payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    payload = payload or {}
    steering = payload.get("steering") or {}
    checkpoint = payload.get("checkpoint") or {}
    approval = payload.get("approval") or {}
    registry = payload.get("registry") or {}
    return {
        "status": {"status": "present" if payload else "missing", "detail": str(payload.get("overall_status") or "")},
        "steering": {"status": "present" if steering else "missing", "detail": str(steering.get("status") or "")},
        "checkpoint": {"status": "present" if checkpoint else "missing", "detail": str(checkpoint.get("status") or "")},
        "approval": {"status": "present" if approval else "missing", "detail": str(approval.get("status") or "")},
        "registry": {"status": "present" if registry else "missing", "detail": str(registry.get("operator_status") or "")},
    }


def h_plane_audit_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# H-plane audit",
            "",
            f"- Topic slug: `{payload['topic_slug']}`",
            f"- Overall status: `{payload['overall_status']}`",
            "",
            "## Steering",
            "",
            f"- Status: `{payload['steering']['status']}`",
            f"- Directive: `{payload['steering'].get('directive') or '(none)'}`",
            f"- Summary: `{payload['steering'].get('summary') or '(none)'}`",
            "",
            "## Checkpoint",
            "",
            f"- Status: `{payload['checkpoint']['status']}`",
            f"- Kind: `{payload['checkpoint'].get('checkpoint_kind') or '(none)'}`",
            "",
            "## Approval",
            "",
            f"- Status: `{payload['approval']['status']}`",
            f"- Candidate id: `{payload['approval'].get('candidate_id') or '(none)'}`",
            "",
            "## Registry",
            "",
            f"- Focus state: `{payload['registry'].get('focus_state') or '(none)'}`",
            f"- Operator status: `{payload['registry'].get('operator_status') or '(none)'}`",
            "",
        ]
    )


def h_plane_audit(self, *, topic_slug: str, updated_by: str = "aitp-cli") -> dict[str, Any]:
    runtime_root = self._ensure_runtime_root(topic_slug)
    topic_state = _read_json(runtime_root / "topic_state.json") or {}
    operator_checkpoint = _read_json(self._operator_checkpoint_paths(topic_slug)["json"]) or {}
    promotion_gate = self._load_promotion_gate(topic_slug) or {}
    payload = build_h_plane_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        operator_checkpoint=operator_checkpoint,
        promotion_gate=promotion_gate,
        updated_by=updated_by,
    )
    json_path = runtime_root / "h_plane.audit.json"
    note_path = runtime_root / "h_plane.audit.md"
    _write_json(json_path, payload)
    _write_text(note_path, h_plane_audit_markdown(payload))
    return {
        **payload,
        "audit_path": str(json_path),
        "audit_note_path": str(note_path),
    }
