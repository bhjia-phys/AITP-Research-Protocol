"""Read-only queue for converting inconclusive legacy reviews into specific needs-revision basis."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.paths import WorkspacePaths

_DEFAULT_REQUIRED_ACTIONS = [
    "record_needs_revision_review_with_specific_repair_basis",
    "keep_semantic_review_blocking_until_typed_review_basis_exists",
]


def build_legacy_semantic_needs_revision_basis_queue(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """List inconclusive semantic reviews that need a concrete needs-revision basis."""

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    items = [
        _basis_item(ws, worklist, item)
        for item in worklist["items"]
        if item.get("review_status") == "inconclusive"
    ]
    return {
        "kind": "legacy_semantic_needs_revision_basis_queue",
        "run_id": worklist["run_id"],
        "migration_dir": worklist["migration_dir"],
        "workspace": worklist["workspace"],
        "basis_item_count": len(items),
        "status_counts": dict(Counter(item["review_status"] for item in items)),
        "required_action_counts": _required_action_counts(items),
        "items": items,
        "next_actions": [f"needs_revision_basis:{item['topic']}" for item in items],
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "legacy_semantic_review_worklist",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _basis_item(ws: WorkspacePaths, worklist: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    pass_readiness = item.get("pass_readiness") if isinstance(item.get("pass_readiness"), dict) else {}
    remaining_actions = [
        str(action) for action in pass_readiness.get("remaining_actions", []) if str(action)
    ]
    required_actions = _required_actions(item, remaining_actions)
    topic = str(item.get("topic") or "")
    return {
        "topic": topic,
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "blocking_classes": list(item.get("blocking_classes") or []),
        "pass_blockers": list(pass_readiness.get("blockers") or []),
        "remaining_actions": remaining_actions,
        "required_actions": required_actions,
        "needs_revision_result_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-review-result "
            f"--migration-dir {worklist['migration_dir']} --topic {topic} "
            "--status needs_revision "
            "--legacy-ref <reviewed-legacy-ref> --typed-ref <reviewed-typed-basis-ref> "
            "--summary <specific repair basis and remaining semantic gaps>"
        ),
        "repair_plan_cli": (
            f"aitp-v5 --base {ws.base} legacy semantic-repair-plan "
            f"--migration-dir {worklist['migration_dir']} --topic {topic}"
        ),
        "can_update_claim_trust": False,
    }


def _required_actions(item: dict[str, Any], remaining_actions: list[str]) -> list[str]:
    actions = list(_DEFAULT_REQUIRED_ACTIONS)
    text = " ".join([*remaining_actions, *[str(value) for value in item.get("blocking_classes", [])]]).lower()
    if "claim_statement" in text or "topic_question" in text:
        actions.insert(1, "supply_or_review_human_topic_question_before_claim_statement_backfill")
    return _unique(actions)


def _required_action_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for item in items:
        counts.update(item["required_actions"])
    return dict(counts)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
