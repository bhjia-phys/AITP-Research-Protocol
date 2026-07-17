"""Detect and plan reviewed replacement of stale full-context host injection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


LEGACY_INJECTION_PLAN_SCHEMA_VERSION = "aitp.host_install_replacement_plan.v1"
_SYSTEM_TRANSFORM = "experimental.chat.system.transform"


def detect_legacy_injection_conflicts(text: str) -> tuple[str, ...]:
    """Return deterministic conflict codes without executing host configuration."""

    if not isinstance(text, str):
        raise TypeError("host configuration text must be a string")
    folded = text.casefold()
    conflicts: list[str] = []
    if _SYSTEM_TRANSFORM in folded and any(
        marker in folded
        for marker in (
            "full content of your using-aitp skill",
            "runtime skill content (auto-injected)",
        )
    ):
        conflicts.append("full_skill_system_injection")
    if _SYSTEM_TRANSFORM in folded and "readfilesync(gateway_skill" in folded:
        conflicts.append("gateway_skill_file_injection")
    if _SYSTEM_TRANSFORM in folded and "memory.md" in folded and "readfilesync" in folded:
        conflicts.append("complete_memory_body_injection")
    if _SYSTEM_TRANSFORM in folded and any(
        marker in folded
        for marker in ("l0-l4", "stage l0", "stage guidance")
    ):
        conflicts.append("legacy_stage_guidance_injection")
    return tuple(conflicts)


def build_legacy_injection_replacement_plan(
    path: str | Path,
    *,
    runtime: str,
) -> dict[str, Any]:
    """Build a read-only plan bound to the exact current file and conflict set."""

    target = Path(path).resolve()
    if not target.is_file():
        raise ValueError(f"legacy injection target does not exist: {target}")
    current = target.read_text(encoding="utf-8")
    conflicts = detect_legacy_injection_conflicts(current)
    if not conflicts:
        raise ValueError("host configuration has no recognized legacy injection conflict")
    current_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
    normalized_runtime = _runtime(runtime)
    basis = {
        "schema_version": LEGACY_INJECTION_PLAN_SCHEMA_VERSION,
        "runtime": normalized_runtime,
        "target_path": str(target),
        "current_content_sha256": current_hash,
        "conflicts": list(conflicts),
        "operation": "replace_legacy_injection_with_bounded_host_configuration",
    }
    fingerprint = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "kind": "reviewed_host_install_replacement_plan",
        **basis,
        "plan_id": f"host-install-plan-{fingerprint}",
        "plan_fingerprint": fingerprint,
        "automatic_apply": False,
        "human_review_required": True,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def require_matching_legacy_injection_replacement_plan(
    path: str | Path,
    *,
    runtime: str,
    reviewed_plan_id: str,
) -> dict[str, Any]:
    """Rebuild the plan and require an explicit exact-id review acknowledgement."""

    if not isinstance(reviewed_plan_id, str) or not reviewed_plan_id.strip():
        raise ValueError(
            "legacy injection replacement requires a reviewed host-install replacement plan"
        )
    plan = build_legacy_injection_replacement_plan(path, runtime=runtime)
    if reviewed_plan_id != plan["plan_id"]:
        raise ValueError(
            "reviewed replacement plan id does not match current legacy injection content"
        )
    return plan


def _runtime(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("runtime must be a string")
    normalized = value.strip().lower().replace("-", "_")
    if normalized == "claude":
        normalized = "claude_code"
    if normalized == "kimi":
        normalized = "kimi_code"
    if normalized not in {"claude_code", "codex", "kimi_code", "opencode"}:
        raise ValueError(f"unsupported runtime: {value}")
    return normalized


__all__ = [
    "LEGACY_INJECTION_PLAN_SCHEMA_VERSION",
    "build_legacy_injection_replacement_plan",
    "detect_legacy_injection_conflicts",
    "require_matching_legacy_injection_replacement_plan",
]
