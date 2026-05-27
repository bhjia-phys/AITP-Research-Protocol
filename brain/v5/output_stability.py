"""Stable final-output profile records for topic continuation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths


@dataclass
class FinalOutputProfileRecord:
    profile_id: str
    topic_id: str
    output_version: str
    audience: str
    stable_sections: list[str] = field(default_factory=list)
    flexible_sections: list[str] = field(default_factory=list)
    change_policy: str = ""
    compatibility_note: str = ""
    status: str = "active"
    summary_inputs_trusted: bool = False
    can_update_claim_trust: bool = False
    kind: str = "final_output_profile"


def record_final_output_profile(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    output_version: str,
    audience: str,
    stable_sections: list[str] | None = None,
    flexible_sections: list[str] | None = None,
    change_policy: str = "",
    compatibility_note: str = "",
    status: str = "active",
) -> FinalOutputProfileRecord:
    """Materialize a versioned final-output profile without claim-trust authority."""

    if status not in {"active", "superseded", "draft"}:
        raise ValueError("final output profile status must be active, superseded, or draft")
    profile = FinalOutputProfileRecord(
        profile_id=prefixed_id("final-output-profile", f"{topic_id}:{output_version}", max_slug=72),
        topic_id=topic_id,
        output_version=output_version,
        audience=audience,
        stable_sections=stable_sections or [],
        flexible_sections=flexible_sections or [],
        change_policy=change_policy,
        compatibility_note=compatibility_note,
        status=status,
    )
    runtime_dir = _topic_runtime_dir(ws, topic_id)
    payload = asdict(profile)
    _write_json(runtime_dir / "final_output_profile.json", payload)
    write_md(runtime_dir / "final_output_profile.md", payload, _final_output_profile_body(profile))
    _append_jsonl(runtime_dir / "final_output_profiles.jsonl", payload)
    return profile


def load_final_output_profile(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    """Return the brief-facing final-output profile if the topic defines one."""

    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    path = runtime_dir / "final_output_profile.json"
    if not path.exists():
        return {"present": False, "summary_inputs_trusted": False, "can_update_claim_trust": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "present": True,
        "profile_id": str(data.get("profile_id") or ""),
        "topic_id": topic_id,
        "output_version": str(data.get("output_version") or ""),
        "audience": str(data.get("audience") or ""),
        "stable_sections": list(data.get("stable_sections") or []),
        "flexible_sections": list(data.get("flexible_sections") or []),
        "change_policy": str(data.get("change_policy") or ""),
        "compatibility_note": str(data.get("compatibility_note") or ""),
        "artifact_path": str(runtime_dir / "final_output_profile.md"),
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _topic_runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    runtime_dir = ws.topic_dir(topic_id) / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _final_output_profile_body(profile: FinalOutputProfileRecord) -> str:
    stable = "\n".join(f"- {section}" for section in profile.stable_sections) or "- None"
    flexible = "\n".join(f"- {section}" for section in profile.flexible_sections) or "- None"
    return (
        "# Final Output Profile\n\n"
        f"Output version: {profile.output_version}\n\n"
        f"Audience: {profile.audience}\n\n"
        f"Stable sections:\n{stable}\n\n"
        f"Flexible sections:\n{flexible}\n\n"
        f"Change policy: {profile.change_policy}\n\n"
        f"Compatibility note: {profile.compatibility_note}\n"
    )
