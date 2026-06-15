"""Read-only workspace migration health surface for agent recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.legacy_l2_seed_audit import (
    audit_canonical_legacy_l2_seeds,
    build_canonical_legacy_l2_seed_review_worklist,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.workspace_file_migration_ledger import compact_workspace_file_migration_ledger
from brain.v5.workspace_migration_discovery import latest_workspace_file_migration_ledger


def build_workspace_migration_health(ws: WorkspacePaths, *, sample_limit: int = 5) -> dict[str, Any]:
    """Build a compact, read-only migration boundary summary for recovery UIs."""

    ledger_path = latest_workspace_file_migration_ledger(ws)
    ledger_progress = _ledger_progress(ledger_path)
    seed_audit = audit_canonical_legacy_l2_seeds(ws, sample_limit=sample_limit)
    seed_worklist = build_canonical_legacy_l2_seed_review_worklist(
        ws,
        group_limit=sample_limit,
        sample_limit=1,
    )
    status = _migration_status(
        ledger_progress=ledger_progress,
        seed_audit=seed_audit,
        seed_worklist=seed_worklist,
    )
    return {
        "kind": "aitp_workspace_migration_health",
        "status": status,
        "canonical_store": str(ws.root),
        "ledger_path": str(ledger_path or ""),
        "ledger_status": "ready" if ledger_progress else "missing",
        "file_decision_count": _int(ledger_progress.get("file_decision_count") if ledger_progress else 0),
        "expected_total_file_count": _int(
            ledger_progress.get("expected_total_file_count") if ledger_progress else 0,
        ),
        "no_omission_check": _bool(ledger_progress.get("no_omission_check") if ledger_progress else False),
        "blocking_file_count": _int(ledger_progress.get("blocking_file_count") if ledger_progress else 0),
        "old_store_retirement_safe": _bool(
            ledger_progress.get("old_store_retirement_safe") if ledger_progress else False,
        ),
        "semantic_review_required": _bool(
            ledger_progress.get("semantic_review_required") if ledger_progress else False,
        ),
        "root_l2_global_memory_risk": _bool(
            ledger_progress.get("root_l2_global_memory_risk") if ledger_progress else False,
        ),
        "root_l2_global_memory_decision_count": _int(
            ledger_progress.get("root_l2_global_memory_decision_count") if ledger_progress else 0,
        ),
        "root_l2_global_memory_topic_count": _int(
            ledger_progress.get("root_l2_global_memory_topic_count") if ledger_progress else 0,
        ),
        "root_l2_global_memory_risk_reason": _text(
            ledger_progress.get("root_l2_global_memory_risk_reason") if ledger_progress else "",
        ),
        "canonical_legacy_seed_count": _int(seed_audit.get("legacy_seed_count")),
        "active_legacy_seed_count": _int(seed_audit.get("active_legacy_seed_count")),
        "legacy_seed_topic_count": _int(seed_audit.get("legacy_seed_topic_count")),
        "legacy_seed_quarantine_status": _text(seed_audit.get("quarantine_status")),
        "legacy_seed_next_actions": _string_list(seed_audit.get("next_actions")),
        "legacy_seed_samples": seed_audit.get("sample_entries") if isinstance(seed_audit.get("sample_entries"), list) else [],
        "legacy_seed_review_group_count": _int(seed_worklist.get("review_group_count")),
        "legacy_seed_open_review_group_count": _int(seed_worklist.get("open_review_group_count")),
        "legacy_seed_reviewed_group_count": _int(seed_worklist.get("reviewed_group_count")),
        "legacy_seed_terminal_review_group_count": _int(seed_worklist.get("terminal_review_group_count")),
        "legacy_seed_topic_scope_mismatch_count": _int(seed_worklist.get("topic_scope_mismatch_count")),
        "legacy_seed_global_l2_count": _int(seed_worklist.get("global_l2_seed_count")),
        "legacy_seed_review_status_counts": (
            seed_worklist.get("review_status_counts")
            if isinstance(seed_worklist.get("review_status_counts"), dict)
            else {}
        ),
        "legacy_seed_review_decision_counts": (
            seed_worklist.get("review_decision_counts")
            if isinstance(seed_worklist.get("review_decision_counts"), dict)
            else {}
        ),
        "legacy_seed_review_blocking_class_counts": (
            seed_worklist.get("review_group_blocking_class_counts")
            if isinstance(seed_worklist.get("review_group_blocking_class_counts"), dict)
            else {}
        ),
        "legacy_seed_review_groups": (
            seed_worklist.get("review_groups")
            if isinstance(seed_worklist.get("review_groups"), list)
            else []
        ),
        "next_actions": _next_actions(
            ledger_progress=ledger_progress,
            seed_audit=seed_audit,
            seed_worklist=seed_worklist,
            status=status,
        ),
        "summary_lines": _summary_lines(
            ledger_progress=ledger_progress,
            seed_audit=seed_audit,
            seed_worklist=seed_worklist,
            status=status,
        ),
        "truth_source": "workspace_migration_ledgers_and_canonical_l2_seed_scan",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _ledger_progress(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("kind") == "aitp_workspace_file_migration_ledger_progress":
        return payload
    if payload.get("kind") == "aitp_workspace_file_migration_ledger":
        return compact_workspace_file_migration_ledger(payload)
    return {}


def _migration_status(
    *,
    ledger_progress: dict[str, Any],
    seed_audit: dict[str, Any],
    seed_worklist: dict[str, Any],
) -> str:
    if not ledger_progress:
        return "unknown"
    if _int(seed_audit.get("active_legacy_seed_count")) > 0:
        return "blocked"
    if not _bool(ledger_progress.get("old_store_retirement_safe")):
        return "blocked"
    if _int(seed_worklist.get("open_review_group_count")) > 0:
        return "review_required"
    return "clear"


def _next_actions(
    *,
    ledger_progress: dict[str, Any],
    seed_audit: dict[str, Any],
    seed_worklist: dict[str, Any],
    status: str,
) -> list[str]:
    actions: list[str] = []
    if not ledger_progress:
        actions.append("build_workspace_file_migration_ledger_before_old_store_retirement")
    if ledger_progress and not _bool(ledger_progress.get("old_store_retirement_safe")):
        actions.append("resolve_blocking_file_decisions_before_old_store_retirement")
    if _bool(ledger_progress.get("root_l2_global_memory_risk")):
        actions.append("review_reassign_or_archive_root_l2_global_memory_entries")
    if _int(seed_audit.get("active_legacy_seed_count")) > 0 or _int(seed_worklist.get("open_review_group_count")) > 0:
        actions.extend(_string_list(seed_audit.get("next_actions")))
    if _int(seed_worklist.get("open_review_group_count")) > 0:
        actions.append("use_legacy_l2_seed_review_worklist_for_grouped_semantic_reassignment")
    if status != "clear":
        actions.append("do_not_treat_legacy_seed_memory_as_active_claim_support")
    return _unique(actions)


def _summary_lines(
    *,
    ledger_progress: dict[str, Any],
    seed_audit: dict[str, Any],
    seed_worklist: dict[str, Any],
    status: str,
) -> list[str]:
    lines = [
        (
            "AITP migration health: "
            f"status={status}, "
            f"old_store_retirement_safe={str(_bool(ledger_progress.get('old_store_retirement_safe'))).lower()}, "
            f"blocking_files={_int(ledger_progress.get('blocking_file_count'))}, "
            f"no_omission_check={str(_bool(ledger_progress.get('no_omission_check'))).lower()}."
        )
    ]
    if _bool(ledger_progress.get("root_l2_global_memory_risk")):
        reason = _text(ledger_progress.get("root_l2_global_memory_risk_reason"))
        lines.append(
            "Root L2 migration risk: "
            f"decisions={_int(ledger_progress.get('root_l2_global_memory_decision_count'))}, "
            f"topics={_int(ledger_progress.get('root_l2_global_memory_topic_count'))}. "
            f"{reason}"
        )
    if _int(seed_audit.get("legacy_seed_count")) > 0:
        lines.append(
            "Canonical legacy L2 seeds: "
            f"count={_int(seed_audit.get('legacy_seed_count'))}, "
            f"active={_int(seed_audit.get('active_legacy_seed_count'))}, "
            f"status={_text(seed_audit.get('quarantine_status'))}; "
            "legacy_seed memory is recovery orientation only until reviewed/reassigned/promoted."
        )
        lines.append(
            "Legacy L2 seed review groups: "
            f"groups={_int(seed_worklist.get('review_group_count'))}, "
            f"open={_int(seed_worklist.get('open_review_group_count'))}, "
            f"reviewed={_int(seed_worklist.get('reviewed_group_count'))}, "
            f"terminal={_int(seed_worklist.get('terminal_review_group_count'))}, "
            f"global_l2_seeds={_int(seed_worklist.get('global_l2_seed_count'))}, "
            f"topic_scope_mismatches={_int(seed_worklist.get('topic_scope_mismatch_count'))}; "
            "topic-level semantic review can be complete while open per-seed L2 review remains required."
        )
    return lines


def _int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _bool(value: Any) -> bool:
    return value is True


def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
