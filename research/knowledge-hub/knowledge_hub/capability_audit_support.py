from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from .control_plane_support import build_control_plane_audit_section
from .h_plane_support import build_h_plane_audit_section, build_h_plane_payload
from .paired_backend_support import build_paired_backend_audit_payload


_RUNTIME_AUDIT_FILENAMES = (
    "topic_state.json",
    "resume.md",
    "action_queue.jsonl",
    "agent_brief.md",
    "interaction_state.json",
    "operator_console.md",
    "conformance_state.json",
    "conformance_report.md",
    "runtime_protocol.generated.json",
    "runtime_protocol.generated.md",
    "research_question.contract.json",
    "research_question.contract.md",
    "validation_contract.active.json",
    "validation_contract.active.md",
    "idea_packet.json",
    "idea_packet.md",
    "operator_checkpoint.active.json",
    "operator_checkpoint.active.md",
    "operator_checkpoints.jsonl",
    "topic_synopsis.json",
    "topic_dashboard.md",
    "validation_review_bundle.active.json",
    "validation_review_bundle.active.md",
    "promotion_readiness.md",
    "gap_map.md",
    "promotion_gate.json",
    "promotion_gate.md",
    "skill_discovery.json",
    "skill_recommendations.md",
    "loop_state.json",
    "loop_history.jsonl",
)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _runtime_section(runtime_root: Path) -> dict[str, dict[str, str]]:
    runtime_section: dict[str, dict[str, str]] = {}
    for filename in _RUNTIME_AUDIT_FILENAMES:
        path = runtime_root / filename
        runtime_section[filename] = {
            "status": "present" if path.exists() else "missing",
            "path": str(path),
        }
    return runtime_section


def _layer_section(kernel_root: Path, topic_slug: str) -> dict[str, dict[str, str]]:
    return {
        "L0": {
            "status": "present" if (kernel_root / "source-layer" / "topics" / topic_slug).exists() else "missing",
            "path": str(kernel_root / "source-layer" / "topics" / topic_slug),
        },
        "L1": {
            "status": "present" if (kernel_root / "intake" / "topics" / topic_slug).exists() else "missing",
            "path": str(kernel_root / "intake" / "topics" / topic_slug),
        },
        "L2": {
            "status": "present" if (kernel_root / "canonical").exists() else "missing",
            "path": str(kernel_root / "canonical"),
        },
        "L3": {
            "status": "present" if (kernel_root / "feedback" / "topics" / topic_slug).exists() else "missing",
            "path": str(kernel_root / "feedback" / "topics" / topic_slug),
        },
        "L4": {
            "status": "present" if (kernel_root / "validation" / "topics" / topic_slug).exists() else "missing",
            "path": str(kernel_root / "validation" / "topics" / topic_slug),
        },
        "consultation": {
            "status": "present" if (kernel_root / "consultation" / "topics" / topic_slug).exists() else "missing",
            "path": str(kernel_root / "consultation" / "topics" / topic_slug),
        },
    }


def _integration_section() -> dict[str, dict[str, str]]:
    return {
        "aitp": {"status": "present" if shutil.which("aitp") else "missing", "path": shutil.which("aitp") or ""},
        "aitp-mcp": {"status": "present" if shutil.which("aitp-mcp") else "missing", "path": shutil.which("aitp-mcp") or ""},
        "codex": {"status": "present" if shutil.which("codex") else "missing", "path": shutil.which("codex") or ""},
        "mcporter": {"status": "present" if shutil.which("mcporter") else "missing", "path": shutil.which("mcporter") or ""},
        "opencode_config": {
            "status": "present" if (Path.home() / ".config" / "opencode" / "opencode.json").exists() else "missing",
            "path": str(Path.home() / ".config" / "opencode" / "opencode.json"),
        },
    }


def _capability_specific(
    self,
    *,
    topic_slug: str,
    topic_state: dict[str, Any] | None,
    latest_run_id: str | None,
    runtime_root: Path,
    protocol_manifest: dict[str, Any] | None,
) -> dict[str, dict[str, str]]:
    trust_audit_path = (
        self._trust_audit_path(topic_slug, latest_run_id)
        if latest_run_id
        else runtime_root / "missing-trust-audit.json"
    )
    missing_paths = ", ".join(str(item) for item in ((protocol_manifest or {}).get("missing_paths") or []) if str(item).strip())
    manifest_detail = str((protocol_manifest or {}).get("summary") or "protocol manifest not materialized")
    if missing_paths:
        manifest_detail = f"{manifest_detail} Missing: {missing_paths}."
    return {
        "latest_run": {
            "status": "present" if latest_run_id else "missing",
            "detail": latest_run_id or "No latest_run_id is currently recorded.",
        },
        "operation_trust": {
            "status": "present" if latest_run_id and trust_audit_path.exists() else "missing",
            "path": str(trust_audit_path),
        },
        "topic_state_resume_stage": {
            "status": "present" if topic_state else "missing",
            "detail": str((topic_state or {}).get("resume_stage")) if topic_state else "topic_state.json missing",
        },
        "protocol_manifest": {
            "status": str((protocol_manifest or {}).get("overall_status") or "missing"),
            "detail": manifest_detail,
            "path": str((protocol_manifest or {}).get("path") or ""),
        },
    }


def _capability_recommendations(
    *,
    runtime_section: dict[str, dict[str, str]],
    layer_section: dict[str, dict[str, str]],
    capability_specific: dict[str, dict[str, str]],
    control_plane_section: dict[str, dict[str, Any]],
    h_plane_section: dict[str, dict[str, Any]],
    paired_backend_section: dict[str, dict[str, Any]],
    latest_run_id: str | None,
) -> list[str]:
    recommendations: list[str] = []
    if runtime_section["topic_state.json"]["status"] != "present":
        recommendations.append("Run `aitp bootstrap ...` or `aitp resume ...` to materialize runtime state.")
    if layer_section["L2"]["status"] != "present":
        recommendations.append("Restore `canonical/` so the formal Layer 2 surface exists in this kernel.")
    if runtime_section["conformance_report.md"]["status"] != "present":
        recommendations.append("Run `aitp audit --topic-slug <topic_slug> --phase entry` to restore conformance visibility.")
    if capability_specific["operation_trust"]["status"] != "present" and latest_run_id:
        recommendations.append("Run `aitp trust-audit --topic-slug <topic_slug> --run-id <run_id>` after creating operation manifests.")
    if capability_specific["protocol_manifest"]["status"] == "fail":
        recommendations.append(
            "Repair protocol-manifest drift so the declared runtime state and required artifact surfaces agree again."
        )
    if control_plane_section["status"]["status"] != "present":
        recommendations.append("Refresh topic status so the unified control-plane projection is materialized.")
    if h_plane_section["status"]["status"] != "present":
        recommendations.append("Run `aitp h-plane-audit --topic-slug <topic_slug>` after steering or approval artifacts are materialized.")
    if paired_backend_section["status"]["status"] == "missing":
        recommendations.append("Run `aitp paired-backend-audit --topic-slug <topic_slug>` after paired backend bridges are declared.")
    if runtime_section["skill_discovery.json"]["status"] != "present":
        recommendations.append("If a capability gap exists, run `aitp loop ... --skill-query ...` to materialize skill discovery.")
    return recommendations


def _overall_status(
    *,
    runtime_section: dict[str, dict[str, str]],
    layer_section: dict[str, dict[str, str]],
    capability_specific: dict[str, dict[str, str]],
    control_plane_section: dict[str, dict[str, Any]],
    h_plane_section: dict[str, dict[str, Any]],
    paired_backend_section: dict[str, dict[str, Any]],
) -> str:
    if runtime_section["topic_state.json"]["status"] != "present":
        return "missing_runtime"
    if control_plane_section["status"]["status"] != "present":
        return "missing_runtime"
    if h_plane_section["status"]["status"] != "present":
        return "missing_runtime"
    if layer_section["L2"]["status"] != "present":
        return "missing_layers"
    if capability_specific["operation_trust"]["status"] != "present":
        return "missing_trust"
    if capability_specific["protocol_manifest"]["status"] == "fail":
        return "drift_detected"
    return "ready"


def capability_audit(
    self,
    *,
    topic_slug: str,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    runtime_root = self._ensure_runtime_root(topic_slug)
    topic_state = _read_json(runtime_root / "topic_state.json")
    latest_run_id = self._resolve_run_id(topic_slug, None)
    runtime_section = _runtime_section(runtime_root)
    layer_section = _layer_section(self.kernel_root, topic_slug)
    integration_section = _integration_section()
    control_plane_payload: dict[str, Any] = {}
    protocol_manifest: dict[str, Any] = {}
    if runtime_section["topic_state.json"]["status"] == "present":
        try:
            status_payload = self.topic_status(topic_slug=topic_slug, updated_by=updated_by)
            control_plane_payload = status_payload.get("control_plane") or {}
            protocol_manifest = status_payload.get("protocol_manifest") or {}
        except FileNotFoundError:
            control_plane_payload = {}
            protocol_manifest = {}
    control_plane_section = build_control_plane_audit_section(control_plane_payload)
    h_plane_payload = build_h_plane_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        operator_checkpoint=(status_payload.get("operator_checkpoint") or {}) if runtime_section["topic_state.json"]["status"] == "present" else {},
        promotion_gate=self._load_promotion_gate(topic_slug) or {},
        updated_by=updated_by,
    )
    h_plane_section = build_h_plane_audit_section(h_plane_payload)
    paired_backend_payload = build_paired_backend_audit_payload(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        backend_id="backend:theoretical-physics-knowledge-network",
        updated_by=updated_by,
    )
    paired_backend_section = {
        "status": {
            "status": "present" if paired_backend_payload.get("pairing_status") else "missing",
            "detail": str(paired_backend_payload.get("pairing_status") or ""),
        },
        "drift_status": {
            "status": "present" if paired_backend_payload.get("drift_status") else "missing",
            "detail": str(paired_backend_payload.get("drift_status") or ""),
        },
        "backend_debt_status": {
            "status": "present" if paired_backend_payload.get("backend_debt_status") else "missing",
            "detail": str(paired_backend_payload.get("backend_debt_status") or ""),
        },
        "pair_contract": {
            "status": "present" if paired_backend_payload.get("pair_contract_path") else "missing",
            "path": paired_backend_payload.get("pair_contract_path") or "",
        },
        "maintenance_protocol": {
            "status": "present" if paired_backend_payload.get("maintenance_protocol_path") else "missing",
            "path": paired_backend_payload.get("maintenance_protocol_path") or "",
        },
    }
    capability_specific = _capability_specific(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        latest_run_id=latest_run_id,
        runtime_root=runtime_root,
        protocol_manifest=protocol_manifest,
    )
    recommendations = _capability_recommendations(
        runtime_section=runtime_section,
        layer_section=layer_section,
        capability_specific=capability_specific,
        control_plane_section=control_plane_section,
        h_plane_section=h_plane_section,
        paired_backend_section=paired_backend_section,
        latest_run_id=latest_run_id,
    )
    payload = {
        "topic_slug": topic_slug,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
        "overall_status": _overall_status(
            runtime_section=runtime_section,
            layer_section=layer_section,
            capability_specific=capability_specific,
            control_plane_section=control_plane_section,
            h_plane_section=h_plane_section,
            paired_backend_section=paired_backend_section,
        ),
        "sections": {
            "runtime": runtime_section,
            "layers": layer_section,
            "integrations": integration_section,
            "control_plane": control_plane_section,
            "h_plane": h_plane_section,
            "paired_backends": paired_backend_section,
            "capabilities": capability_specific,
        },
        "recommendations": recommendations,
    }
    registry_path = self._capability_registry_path(topic_slug)
    report_path = self._capability_report_path(topic_slug)
    _write_json(registry_path, payload)
    _write_text(report_path, self._capability_report_markdown(payload))
    return {
        **payload,
        "capability_registry_path": str(registry_path),
        "capability_report_path": str(report_path),
    }
