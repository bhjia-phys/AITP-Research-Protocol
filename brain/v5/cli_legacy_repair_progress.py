"""Compact CLI progress payloads for legacy repair surfaces."""

from __future__ import annotations

from typing import Any


def compact_legacy_semantic_repair_plan(payload: dict[str, Any]) -> dict[str, Any]:
    repairs = [item for item in payload.get("proposed_repairs", []) if isinstance(item, dict)]
    return {
        "ok": bool(payload.get("ok", True)),
        "kind": "legacy_semantic_repair_plan_progress",
        "source_surface": "legacy_semantic_repair_plan",
        "run_id": str(payload.get("run_id") or ""),
        "migration_dir": str(payload.get("migration_dir") or ""),
        "topic": str(payload.get("topic") or ""),
        "active_claim_id": str(payload.get("active_claim_id") or ""),
        "repair_status": str(payload.get("repair_status") or ""),
        "proposed_repair_count": len(repairs),
        "proposed_repair_types": [
            str(item.get("repair_type") or "")
            for item in repairs
            if str(item.get("repair_type") or "")
        ],
        "required_actions": [str(action) for action in payload.get("required_actions", []) if str(action)],
        "semantic_lossless_proven": bool(payload.get("semantic_lossless_proven", False)),
        "semantic_review_required": bool(payload.get("semantic_review_required", True)),
        "truth_source": str(payload.get("truth_source") or ""),
        "summary_inputs_trusted": bool(payload.get("summary_inputs_trusted", False)),
        "orientation_only": bool(payload.get("orientation_only", True)),
        "can_update_kernel_state": bool(payload.get("can_update_kernel_state", False)),
        "can_update_claim_trust": bool(payload.get("can_update_claim_trust", False)),
    }
