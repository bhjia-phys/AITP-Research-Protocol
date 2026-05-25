"""Batch manifest for legacy semantic review packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_bridge import scan_legacy_topic
from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.models import ClaimRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records


def build_legacy_semantic_review_manifest(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
) -> dict[str, Any]:
    """Build a read-only manifest of per-topic semantic review work."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    migration = str(queue["migration_dir"])
    legacy_root = Path(queue["legacy_root"])
    claims_by_id = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    items = [_manifest_item(ws, migration, legacy_root, item, claims_by_id=claims_by_id) for item in queue["items"]]
    progress = _progress(items)
    return {
        "kind": "legacy_semantic_review_manifest",
        "run_id": queue["run_id"],
        "migration_dir": migration,
        "workspace": queue["workspace"],
        "topic_count": queue["topic_count"],
        "review_item_count": queue["review_item_count"],
        "priority_counts": queue["priority_counts"],
        "review_progress": progress,
        "pending_count": progress["pending"],
        "passed_count": progress["passed"],
        "needs_revision_count": progress["needs_revision"],
        "inconclusive_count": progress["inconclusive"],
        "items": items,
        "next_actions": _next_actions(items),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "migration_manifests_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _manifest_item(
    ws: WorkspacePaths,
    migration_dir: str,
    legacy_root: Path,
    item: dict[str, Any],
    *,
    claims_by_id: dict[str, ClaimRecord],
) -> dict[str, Any]:
    topic = item["topic"]
    status = item["semantic_review_status"].removeprefix("reviewed_")
    if status == item["semantic_review_status"]:
        status = "pending"
    repair_candidates = _repair_candidates(ws, migration_dir, legacy_root, item, claims_by_id=claims_by_id)
    packet_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-packet "
        f"--migration-dir {migration_dir} --topic {topic}"
    )
    result_cli = (
        f"aitp-v5 --base {ws.base} legacy semantic-review-result "
        f"--migration-dir {migration_dir} --topic {topic} --status <passed|needs_revision|inconclusive> "
        "--legacy-ref <ref> --summary <summary>"
    )
    return {
        "topic": topic,
        "active_claim_id": item["active_claim_id"],
        "review_status": status,
        "review_priority": item["review_priority"],
        "review_reasons": item["review_reasons"],
        "recommended_actions": item["recommended_actions"],
        "missing_source_components": list(item.get("source_reconstruction", {}).get("missing_components", [])),
        "source_reconstruction": item.get("source_reconstruction", {}),
        "latest_semantic_review": item.get("latest_semantic_review", {}),
        "packet_cli": packet_cli,
        "result_cli_template": result_cli,
        "packet_mcp": "aitp_v5_build_legacy_semantic_review_packet",
        "result_mcp": "aitp_v5_record_legacy_semantic_review_result",
        "repair_candidate_count": len(repair_candidates),
        "repair_candidates": repair_candidates,
        "can_update_claim_trust": False,
    }


def _progress(items: list[dict[str, Any]]) -> dict[str, int]:
    progress = {"passed": 0, "inconclusive": 0, "needs_revision": 0, "pending": 0}
    for item in items:
        progress[item["review_status"]] += 1
    return progress


def _next_actions(items: list[dict[str, Any]]) -> list[str]:
    actions = [
        f"review_packet:{item['topic']}"
        for item in items
        if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
    ]
    actions.extend(
        f"repair_candidate:{item['topic']}:{candidate['repair_type']}"
        for item in items
        for candidate in item.get("repair_candidates", [])
    )
    return actions


def _repair_candidates(
    ws: WorkspacePaths,
    migration_dir: str,
    legacy_root: Path,
    item: dict[str, Any],
    *,
    claims_by_id: dict[str, ClaimRecord],
) -> list[dict[str, Any]]:
    topic = item["topic"]
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    if latest_review.get("status") != "needs_revision":
        return []
    actions = _action_tokens(latest_review.get("remaining_actions", []))
    review_id = str(latest_review.get("review_id") or "")
    candidates: list[dict[str, Any]] = []
    active_claim = claims_by_id.get(str(item.get("active_claim_id") or ""))
    if (
        "backfill_active_claim_statement_from_legacy_state_question" in actions
        and active_claim is not None
        and not active_claim.statement.strip()
        and _legacy_state_question(legacy_root, topic)
    ):
        candidates.append(
            _candidate(
                ws,
                migration_dir,
                topic,
                review_id,
                surface="legacy_semantic_repair_apply",
                command="semantic-repair-apply",
                repair_type="claim_statement_backfill",
            )
        )
    missing_components = set(item.get("source_reconstruction", {}).get("missing_components", []))
    if (
        "complete_source_reconstruction" in actions
        and "reconstruction_path" in missing_components
        and _reviewed_reconstruction_refs(latest_review)
    ):
        candidates.append(
            _candidate(
                ws,
                migration_dir,
                topic,
                review_id,
                surface="legacy_source_reconstruction_apply",
                command="source-reconstruction-apply",
                repair_type="reconstruction_path_evidence_backfill",
            )
        )
    return candidates


def _candidate(
    ws: WorkspacePaths,
    migration_dir: str,
    topic: str,
    review_id: str,
    *,
    surface: str,
    command: str,
    repair_type: str,
) -> dict[str, Any]:
    return {
        "repair_surface": surface,
        "repair_type": repair_type,
        "review_id": review_id,
        "apply_cli": (
            f"aitp-v5 --base {ws.base} legacy {command} "
            f"--migration-dir {migration_dir} --topic {topic} "
            f"--repair-type {repair_type} --review-id {review_id}"
        ),
        "can_update_claim_trust": False,
    }


def _action_tokens(raw_actions: list[str] | None) -> set[str]:
    tokens: set[str] = set()
    for action in raw_actions or []:
        text = str(action).strip()
        if not text:
            continue
        tokens.add(text)
        normalized = " ".join(text.lower().replace("_", " ").split())
        if "backfill" in normalized and "claim statement" in normalized and "research question" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_state_question")
        if "source reconstruction" in normalized or "reconstruction path" in normalized:
            tokens.add("complete_source_reconstruction")
    return tokens


def _reviewed_reconstruction_refs(latest_review: dict[str, Any]) -> list[str]:
    return [
        ref
        for ref in (str(value).strip() for value in latest_review.get("reviewed_legacy_refs", []))
        if ref.startswith(("legacy_candidate:", "legacy_l3_process:"))
    ]


def _legacy_state_question(legacy_root: Path, topic: str) -> str:
    legacy_topic = legacy_root / topic
    if not (legacy_topic / "state.md").exists():
        return ""
    return scan_legacy_topic(legacy_topic).question
