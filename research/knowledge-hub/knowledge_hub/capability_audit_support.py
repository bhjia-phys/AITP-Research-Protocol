from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


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
) -> dict[str, dict[str, str]]:
    trust_audit_path = (
        self._trust_audit_path(topic_slug, latest_run_id)
        if latest_run_id
        else runtime_root / "missing-trust-audit.json"
    )
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
    }


def _capability_recommendations(
    *,
    runtime_section: dict[str, dict[str, str]],
    layer_section: dict[str, dict[str, str]],
    capability_specific: dict[str, dict[str, str]],
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
    if runtime_section["skill_discovery.json"]["status"] != "present":
        recommendations.append("If a capability gap exists, run `aitp loop ... --skill-query ...` to materialize skill discovery.")
    return recommendations


def _overall_status(
    *,
    runtime_section: dict[str, dict[str, str]],
    layer_section: dict[str, dict[str, str]],
    capability_specific: dict[str, dict[str, str]],
) -> str:
    if runtime_section["topic_state.json"]["status"] != "present":
        return "missing_runtime"
    if layer_section["L2"]["status"] != "present":
        return "missing_layers"
    if capability_specific["operation_trust"]["status"] != "present":
        return "missing_trust"
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
    capability_specific = _capability_specific(
        self,
        topic_slug=topic_slug,
        topic_state=topic_state,
        latest_run_id=latest_run_id,
        runtime_root=runtime_root,
    )
    recommendations = _capability_recommendations(
        runtime_section=runtime_section,
        layer_section=layer_section,
        capability_specific=capability_specific,
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
        ),
        "sections": {
            "runtime": runtime_section,
            "layers": layer_section,
            "integrations": integration_section,
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
