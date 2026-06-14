"""Current recovery focus for legacy semantic review packets."""

from __future__ import annotations

from typing import Any

from brain.v5.paths import WorkspacePaths
from brain.v5.workspace_recovery_audit import build_workspace_recovery_audit


def build_legacy_recovery_focus_index(
    ws: WorkspacePaths,
    *,
    topics: list[str],
) -> dict[str, dict[str, Any]]:
    payload = build_workspace_recovery_audit(ws, topics=topics)
    rows = payload.get("topic_rows") if isinstance(payload.get("topic_rows"), list) else []
    return {
        str(row.get("topic_id") or ""): compact_legacy_recovery_focus(row)
        for row in rows
        if isinstance(row, dict) and str(row.get("topic_id") or "")
    }


def compact_legacy_recovery_focus(
    row: dict[str, Any] | None,
    *,
    migration_active_claim_id: str = "",
) -> dict[str, Any]:
    row = row if isinstance(row, dict) else {}
    active_claim_id = str(row.get("active_claim_id") or "")
    migration_claim = str(migration_active_claim_id or "")
    return {
        "kind": "legacy_current_recovery_focus",
        "topic": str(row.get("topic_id") or row.get("topic") or ""),
        "recovery_status": str(row.get("recovery_status") or "not_audited"),
        "session_id": str(row.get("session_id") or ""),
        "active_claim_id": active_claim_id,
        "migration_active_claim_id": migration_claim,
        "active_claim_divergence": bool(active_claim_id and migration_claim and active_claim_id != migration_claim),
        "has_relation_map": bool(row.get("has_relation_map")),
        "recovery_selection_source": str(row.get("recovery_selection_source") or ""),
        "next_valid_action": str(row.get("next_valid_action") or ""),
        "recovery_gap": str(row.get("recovery_gap") or ""),
        "truth_source": "workspace_recovery_audit",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
