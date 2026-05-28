"""Batch triage manifest for legacy semantic repair planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_repair_actions import required_repair_actions
from brain.v5.legacy_semantic_review_manifest import build_legacy_semantic_review_manifest
from brain.v5.paths import WorkspacePaths


_REPAIR_STATUSES = (
    "proposed_repairs",
    "external_evidence_required",
    "awaiting_needs_revision_review",
    "no_repair_candidates",
)


def build_legacy_semantic_repair_manifest(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Build a read-only batch triage view for semantic repair follow-up."""

    manifest = build_legacy_semantic_review_manifest(ws, migration_dir=migration_dir)
    items = [
        _repair_item(ws, manifest, item)
        for item in manifest["items"]
        if item.get("review_status") in {"pending", "needs_revision", "inconclusive"}
    ]
    return {
        "kind": "legacy_semantic_repair_manifest",
        "run_id": manifest["run_id"],
        "migration_dir": manifest["migration_dir"],
        "workspace": manifest["workspace"],
        "work_item_count": len(items),
        "repair_status_counts": _repair_status_counts(items),
        "proposed_repair_count": sum(int(item["proposed_repair_count"]) for item in items),
        "required_action_counts": _required_action_counts(items),
        "items": items,
        "next_actions": _next_actions(items),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "legacy_semantic_review_manifest",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _repair_item(ws: WorkspacePaths, manifest: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    repairs = [repair for repair in item.get("repair_candidates", []) if isinstance(repair, dict)]
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    active_claim = {
        "claim_id": str(item.get("active_claim_id") or ""),
        "statement": "present" if item.get("active_claim_statement_present") else "",
    }
    actions = required_repair_actions(
        active_claim=active_claim,
        latest_review=latest_review,
        proposed_repairs=repairs,
    )
    topic = str(item.get("topic") or "")
    repair_status = _repair_status(latest_review, repairs)
    repair_plan_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-repair-plan "
        f"--migration-dir {manifest['migration_dir']} --topic {topic}"
    )
    return {
        "topic": topic,
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "latest_review_id": str(latest_review.get("review_id") or ""),
        "repair_status": repair_status,
        "proposed_repair_count": len(repairs),
        "proposed_repair_types": [
            str(repair.get("repair_type") or "")
            for repair in repairs
            if str(repair.get("repair_type") or "")
        ],
        "required_actions": actions,
        "repair_plan_cli": repair_plan_cli,
        "repair_plan_mcp": "aitp_v5_build_legacy_semantic_repair_plan",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _repair_status(latest_review: dict[str, Any], repairs: list[dict[str, Any]]) -> str:
    if repairs:
        if all(bool(repair.get("requires_external_evidence") is True) for repair in repairs):
            return "external_evidence_required"
        return "proposed_repairs"
    if latest_review.get("status") != "needs_revision":
        return "awaiting_needs_revision_review"
    return "no_repair_candidates"


def _repair_status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in _REPAIR_STATUSES}
    for item in items:
        status = item["repair_status"]
        if status in counts:
            counts[status] += 1
    return counts


def _required_action_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for action in item.get("required_actions", []):
            if action:
                counts[action] = counts.get(action, 0) + 1
    return dict(sorted(counts.items()))


def _next_actions(items: list[dict[str, Any]]) -> list[str]:
    actions: list[str] = []
    for item in items:
        topic = item["topic"]
        if item["repair_status"] == "proposed_repairs":
            actions.append(f"review_repair_plan:{topic}")
        else:
            for required in item.get("required_actions", []):
                actions.append(f"repair_basis:{topic}:{required}")
    return actions
