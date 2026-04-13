from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


_BOOTSTRAPPED_ARTIFACTS = [
    "topic_state_json",
    "research_question_contract_json",
    "research_question_contract_note",
    "topic_dashboard_note",
    "topic_synopsis_json",
]

_EXPLORING_ARTIFACTS = [
    *_BOOTSTRAPPED_ARTIFACTS,
    "validation_contract_json",
    "validation_contract_note",
    "validation_review_bundle_json",
    "validation_review_bundle_note",
    "idea_packet_json",
    "idea_packet_note",
    "operator_checkpoint_json",
    "operator_checkpoint_note",
    "promotion_readiness_note",
    "topic_completion_json",
    "topic_completion_note",
]

_VERIFYING_ARTIFACTS = [
    *_BOOTSTRAPPED_ARTIFACTS,
    "validation_contract_json",
    "validation_contract_note",
    "validation_review_bundle_json",
    "validation_review_bundle_note",
    "promotion_readiness_note",
    "topic_completion_json",
    "topic_completion_note",
]

_PROMOTING_ARTIFACTS = [
    *_VERIFYING_ARTIFACTS,
    "promotion_gate_json",
    "promotion_gate_note",
]

_COMPLETED_ARTIFACTS = [
    *_BOOTSTRAPPED_ARTIFACTS,
    "topic_completion_json",
    "topic_completion_note",
    "promotion_gate_json",
    "promotion_gate_note",
]

_ARTIFACT_LABELS = {
    "topic_state_json": "Topic state",
    "research_question_contract_json": "Research question contract (JSON)",
    "research_question_contract_note": "Research question contract (note)",
    "topic_dashboard_note": "Topic dashboard",
    "topic_synopsis_json": "Topic synopsis",
    "validation_contract_json": "Validation contract (JSON)",
    "validation_contract_note": "Validation contract (note)",
    "validation_review_bundle_json": "Validation review bundle (JSON)",
    "validation_review_bundle_note": "Validation review bundle (note)",
    "idea_packet_json": "Idea packet (JSON)",
    "idea_packet_note": "Idea packet (note)",
    "operator_checkpoint_json": "Operator checkpoint (JSON)",
    "operator_checkpoint_note": "Operator checkpoint (note)",
    "promotion_readiness_note": "Promotion readiness note",
    "topic_completion_json": "Topic completion (JSON)",
    "topic_completion_note": "Topic completion (note)",
    "promotion_gate_json": "Promotion gate (JSON)",
    "promotion_gate_note": "Promotion gate (note)",
}

_ARTIFACT_REASONS = {
    "topic_state_json": "Root runtime truth surface for the current stage, run, and durable pointers.",
    "research_question_contract_json": "Machine-readable contract for the bounded research question.",
    "research_question_contract_note": "Human-readable contract for scope, deliverables, and anti-proxy rules.",
    "topic_dashboard_note": "Primary human runtime dashboard for the topic.",
    "topic_synopsis_json": "Primary machine synopsis behind status and scheduler projections.",
    "validation_contract_json": "Machine-readable declaration of the active validation route.",
    "validation_contract_note": "Human-readable declaration of the active validation route.",
    "validation_review_bundle_json": "Machine-readable L4 review entry surface.",
    "validation_review_bundle_note": "Human-readable L4 review entry surface.",
    "idea_packet_json": "Machine-readable bounded idea gate for exploration work.",
    "idea_packet_note": "Human-readable bounded idea gate for exploration work.",
    "operator_checkpoint_json": "Machine-readable human checkpoint state.",
    "operator_checkpoint_note": "Human-readable checkpoint prompt and response surface.",
    "promotion_readiness_note": "Current writeback and promotion blockers.",
    "topic_completion_json": "Machine-readable topic-completion status.",
    "topic_completion_note": "Human-readable topic-completion summary.",
    "promotion_gate_json": "Machine-readable writeback gate for L2 promotion.",
    "promotion_gate_note": "Human-readable writeback gate for L2 promotion.",
}

_STATE_REQUIREMENTS = {
    "bootstrapped": {
        "summary": "Core runtime state has been materialized and the topic can be resumed deterministically.",
        "artifact_ids": _BOOTSTRAPPED_ARTIFACTS,
    },
    "exploring": {
        "summary": "The topic is in bounded exploration and must expose execution plus validation-contract surfaces.",
        "artifact_ids": _EXPLORING_ARTIFACTS,
    },
    "verifying": {
        "summary": "The topic claims verification mode and must expose explicit validation and review surfaces.",
        "artifact_ids": _VERIFYING_ARTIFACTS,
    },
    "promoting": {
        "summary": "The topic is at the promotion boundary and must expose writeback gate surfaces explicitly.",
        "artifact_ids": _PROMOTING_ARTIFACTS,
    },
    "completed": {
        "summary": "The topic claims a promoted or completed outcome and must preserve completion plus promotion records.",
        "artifact_ids": _COMPLETED_ARTIFACTS,
    },
}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _dedupe_strings(values: list[str] | None) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def protocol_manifest_paths(service: Any, topic_slug: str) -> dict[str, Path]:
    runtime_root = service._runtime_root(topic_slug)
    return {
        "json": runtime_root / "protocol_manifest.active.json",
        "note": runtime_root / "protocol_manifest.active.md",
    }


def _artifact_paths(service: Any, *, topic_slug: str, shell_surfaces: dict[str, Any]) -> dict[str, str]:
    promotion_gate_paths = service._promotion_gate_paths(topic_slug)
    return {
        "topic_state_json": service._relativize(service._runtime_root(topic_slug) / "topic_state.json"),
        "research_question_contract_json": service._relativize(Path(shell_surfaces["research_question_contract_path"])),
        "research_question_contract_note": service._relativize(Path(shell_surfaces["research_question_contract_note_path"])),
        "topic_dashboard_note": service._relativize(Path(shell_surfaces["topic_dashboard_path"])),
        "topic_synopsis_json": service._relativize(service._topic_synopsis_path(topic_slug)),
        "validation_contract_json": service._relativize(Path(shell_surfaces["validation_contract_path"])),
        "validation_contract_note": service._relativize(Path(shell_surfaces["validation_contract_note_path"])),
        "validation_review_bundle_json": service._relativize(Path(shell_surfaces["validation_review_bundle_path"])),
        "validation_review_bundle_note": service._relativize(Path(shell_surfaces["validation_review_bundle_note_path"])),
        "idea_packet_json": service._relativize(Path(shell_surfaces["idea_packet_path"])),
        "idea_packet_note": service._relativize(Path(shell_surfaces["idea_packet_note_path"])),
        "operator_checkpoint_json": service._relativize(Path(shell_surfaces["operator_checkpoint_path"])),
        "operator_checkpoint_note": service._relativize(Path(shell_surfaces["operator_checkpoint_note_path"])),
        "promotion_readiness_note": service._relativize(Path(shell_surfaces["promotion_readiness_path"])),
        "topic_completion_json": service._relativize(Path(shell_surfaces["topic_completion_path"])),
        "topic_completion_note": service._relativize(Path(shell_surfaces["topic_completion_note_path"])),
        "promotion_gate_json": service._relativize(promotion_gate_paths["json"]),
        "promotion_gate_note": service._relativize(promotion_gate_paths["note"]),
    }


def _path_exists(service: Any, relative_path: str) -> bool:
    return (service.kernel_root / relative_path).exists()


def _artifact_states(artifact_id: str) -> list[str]:
    states: list[str] = []
    for state_name, config in _STATE_REQUIREMENTS.items():
        if artifact_id in config["artifact_ids"]:
            states.append(state_name)
    return states


def _derive_declared_state(
    *,
    topic_state: dict[str, Any],
    runtime_mode: str | None,
    promotion_gate: dict[str, Any],
    topic_completion: dict[str, Any],
) -> tuple[str, str]:
    gate_status = str(promotion_gate.get("status") or "").strip()
    completion_status = str(topic_completion.get("status") or "").strip()
    normalized_mode = str(runtime_mode or "").strip()

    if completion_status in {"promoted", "completed"} or gate_status == "promoted":
        return "completed", "Topic completion or promotion gate already claims a promoted/completed outcome."
    if gate_status in {"requested", "approved", "pending_human_approval"} or normalized_mode == "promote":
        return "promoting", "Promotion gate or runtime mode places the topic at the L2 writeback boundary."
    if normalized_mode == "verify":
        return "verifying", "Runtime mode claims the topic is in verification."
    if topic_state:
        return "exploring", "Runtime state exists and no promotion/completion boundary is currently active."
    return "bootstrapped", "Only the minimal runtime state is available."


def protocol_manifest_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Protocol manifest",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Declared state: `{payload.get('declared_state') or '(missing)'}`",
        f"- Overall status: `{payload.get('overall_status') or '(missing)'}`",
        f"- Missing artifact count: `{payload.get('missing_artifact_count') or 0}`",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## State inputs",
        "",
    ]
    for key, value in (payload.get("state_inputs") or {}).items():
        lines.append(f"- `{key}`: `{value or '(none)'}`")
    lines.extend(["", "## Active requirements", ""])
    for row in payload.get("active_requirements") or []:
        lines.append(
            f"- `{row.get('artifact_id') or '(missing)'}` status=`{row.get('status') or '(missing)'}` "
            f"path=`{row.get('path') or '(missing)'}` reason=`{row.get('reason') or '(missing)'}`"
        )
    lines.extend(["", "## Missing paths", ""])
    for row in payload.get("missing_paths") or ["(none)"]:
        lines.append(f"- `{row}`" if row != "(none)" else "- (none)")
    lines.extend(["", "## State catalog", ""])
    for state_name, config in (payload.get("state_catalog") or {}).items():
        lines.extend(
            [
                f"### {state_name}",
                "",
                config.get("summary") or "(missing)",
                "",
            ]
        )
        for artifact_id in config.get("required_artifact_ids") or []:
            lines.append(f"- `{artifact_id}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def protocol_manifest_must_read_entry(payload: dict[str, Any]) -> dict[str, str] | None:
    if str(payload.get("overall_status") or "").strip() != "fail":
        return None
    note_path = str(payload.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": (
            f"Manifest drift detected: declared `{payload.get('declared_state') or 'unknown'}` state "
            "is missing required protocol artifacts."
        ),
    }


def materialize_protocol_manifest(
    service: Any,
    *,
    topic_slug: str,
    topic_state: dict[str, Any],
    runtime_mode: str | None,
    active_submode: str | None,
    promotion_gate: dict[str, Any],
    topic_completion: dict[str, Any],
    active_research_contract: dict[str, Any],
    shell_surfaces: dict[str, Any],
    updated_by: str,
) -> dict[str, Any]:
    declared_state, declared_state_reason = _derive_declared_state(
        topic_state=topic_state,
        runtime_mode=runtime_mode,
        promotion_gate=promotion_gate,
        topic_completion=topic_completion,
    )
    artifact_paths = _artifact_paths(service, topic_slug=topic_slug, shell_surfaces=shell_surfaces)
    active_artifact_ids = list(_STATE_REQUIREMENTS[declared_state]["artifact_ids"])
    active_requirements: list[dict[str, Any]] = []
    missing_artifact_ids: list[str] = []
    missing_paths: list[str] = []

    for artifact_id in active_artifact_ids:
        path = artifact_paths[artifact_id]
        status = "present" if _path_exists(service, path) else "missing"
        if status == "missing":
            missing_artifact_ids.append(artifact_id)
            missing_paths.append(path)
        active_requirements.append(
            {
                "artifact_id": artifact_id,
                "label": _ARTIFACT_LABELS[artifact_id],
                "path": path,
                "status": status,
                "reason": _ARTIFACT_REASONS[artifact_id],
                "required_in_states": _artifact_states(artifact_id),
            }
        )

    overall_status = "pass" if not missing_artifact_ids else "fail"
    summary = (
        f"Manifest requirements satisfied for declared `{declared_state}` state."
        if overall_status == "pass"
        else (
            f"Manifest drift detected for declared `{declared_state}` state: "
            f"{len(missing_artifact_ids)} required artifact(s) are missing."
        )
    )
    state_catalog = {
        state_name: {
            "summary": str(config["summary"]),
            "required_artifact_ids": list(config["artifact_ids"]),
        }
        for state_name, config in _STATE_REQUIREMENTS.items()
    }
    paths = protocol_manifest_paths(service, topic_slug)
    payload = {
        "manifest_version": 1,
        "topic_slug": topic_slug,
        "declared_state": declared_state,
        "declared_state_reason": declared_state_reason,
        "overall_status": overall_status,
        "missing_artifact_count": len(missing_artifact_ids),
        "missing_artifact_ids": missing_artifact_ids,
        "missing_paths": _dedupe_strings(missing_paths),
        "active_requirements": active_requirements,
        "state_catalog": state_catalog,
        "state_inputs": {
            "resume_stage": str(topic_state.get("resume_stage") or ""),
            "last_materialized_stage": str(topic_state.get("last_materialized_stage") or ""),
            "runtime_mode": str(runtime_mode or ""),
            "active_submode": str(active_submode or ""),
            "promotion_gate_status": str(promotion_gate.get("status") or ""),
            "topic_completion_status": str(topic_completion.get("status") or ""),
            "research_mode": str(topic_state.get("research_mode") or active_research_contract.get("research_mode") or ""),
        },
        "summary": summary,
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }
    _write_json(paths["json"], payload)
    _write_text(paths["note"], protocol_manifest_markdown(payload))
    return payload
