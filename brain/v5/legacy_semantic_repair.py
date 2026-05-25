"""Repair planning and guarded application for reviewed legacy semantic migration gaps."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.legacy_bridge import scan_legacy_topic
from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.legacy_semantic_review_packet import build_legacy_semantic_review_packet
from brain.v5.models import ClaimRecord, LegacySemanticRepairRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records, write_record


def build_legacy_semantic_repair_plan(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
) -> dict[str, Any]:
    """Build a conservative, read-only repair plan from typed semantic reviews."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    item = _queue_item(queue, topic)
    packet = build_legacy_semantic_review_packet(ws, migration_dir=migration_dir, topic=topic)
    latest_review = item.get("latest_semantic_review") if isinstance(item.get("latest_semantic_review"), dict) else {}
    proposed_repairs = _proposed_repairs(
        legacy_root=Path(queue["legacy_root"]),
        topic=item["topic"],
        active_claim=packet.get("active_claim", {}),
        latest_review=latest_review,
    )
    return {
        "kind": "legacy_semantic_repair_plan",
        "run_id": queue["run_id"],
        "migration_dir": queue["migration_dir"],
        "topic": item["topic"],
        "active_claim_id": item["active_claim_id"],
        "repair_status": _repair_status(latest_review, proposed_repairs),
        "latest_semantic_review": latest_review,
        "proposed_repairs": proposed_repairs,
        "can_apply": False,
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "typed_review_results_and_legacy_refs",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def apply_legacy_semantic_repair(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
    repair_type: str,
    review_id: str,
) -> dict[str, Any]:
    """Apply a single guarded legacy semantic repair without changing trust."""

    plan = build_legacy_semantic_repair_plan(ws, migration_dir=migration_dir, topic=topic)
    repair = _matching_repair(plan, repair_type=repair_type)
    if repair is None:
        return _apply_payload(
            ws,
            plan,
            repair_type=repair_type,
            review_id=review_id,
            previous_value="",
            new_value="",
            basis_refs=[],
            applied=False,
            required_actions=["select_available_repair"],
        )
    if review_id != plan["latest_semantic_review"].get("review_id"):
        return _apply_payload(
            ws,
            plan,
            repair_type=repair_type,
            review_id=review_id,
            previous_value=repair["current_value"],
            new_value=repair["proposed_value"],
            basis_refs=repair["basis_refs"],
            applied=False,
            required_actions=["match_latest_needs_revision_review_id"],
        )
    claim = _claim_for_repair(ws, repair["target_ref"])
    if claim.statement != repair["current_value"]:
        return _apply_payload(
            ws,
            plan,
            repair_type=repair_type,
            review_id=review_id,
            previous_value=claim.statement,
            new_value=repair["proposed_value"],
            basis_refs=repair["basis_refs"],
            applied=False,
            required_actions=["refresh_repair_plan_for_current_claim_statement"],
        )
    updated = replace(claim, statement=repair["proposed_value"])
    _write_claim(ws, updated)
    return _apply_payload(
        ws,
        plan,
        repair_type=repair_type,
        review_id=review_id,
        previous_value=claim.statement,
        new_value=updated.statement,
        basis_refs=repair["basis_refs"],
        applied=True,
        required_actions=[],
    )


def _queue_item(queue: dict[str, Any], topic: str) -> dict[str, Any]:
    for item in queue["items"]:
        if item["topic"] == topic:
            return item
    raise ValueError(f"unknown semantic repair topic: {topic}")


def _proposed_repairs(
    *,
    legacy_root: Path,
    topic: str,
    active_claim: dict[str, Any],
    latest_review: dict[str, Any],
) -> list[dict[str, Any]]:
    if latest_review.get("status") != "needs_revision":
        return []
    claim_id = str(active_claim.get("claim_id") or "")
    if not claim_id or str(active_claim.get("statement") or ""):
        return []
    legacy_topic = legacy_root / topic
    if not (legacy_topic / "state.md").exists():
        return []
    question = scan_legacy_topic(legacy_topic).question
    if not question:
        return []
    basis_refs = _unique([
        *[str(ref) for ref in latest_review.get("reviewed_legacy_refs", []) if str(ref)],
        str(latest_review.get("review_id") or ""),
    ])
    return [
        {
            "repair_type": "claim_statement_backfill",
            "target_ref": claim_id,
            "current_value": "",
            "proposed_value": question,
            "basis_refs": basis_refs,
            "mutation_authority": "none_review_and_apply_separately",
        }
    ]


def _repair_status(latest_review: dict[str, Any], proposed_repairs: list[dict[str, Any]]) -> str:
    if proposed_repairs:
        return "proposed_repairs"
    if latest_review.get("status") != "needs_revision":
        return "awaiting_needs_revision_review"
    return "no_repair_candidates"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _matching_repair(plan: dict[str, Any], *, repair_type: str) -> dict[str, Any] | None:
    for repair in plan["proposed_repairs"]:
        if repair["repair_type"] == repair_type:
            return repair
    return None


def _claim_for_repair(ws: WorkspacePaths, claim_id: str) -> ClaimRecord:
    claims = {record.claim_id: record for record in list_records(ws.registry_dir("claims"), ClaimRecord)}
    if claim_id not in claims:
        raise ValueError(f"unknown repair target claim: {claim_id}")
    return claims[claim_id]


def _write_claim(ws: WorkspacePaths, claim: ClaimRecord) -> None:
    body = f"# Claim\n\n{claim.statement}\n"
    write_record(ws.registry_dir("claims") / f"{claim.claim_id}.md", claim, body=body)
    ledger_dir = ws.topic_dir(claim.topic_id) / "claims" / "ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    write_record(ledger_dir / f"{claim.claim_id}.md", claim, body=body)


def _apply_payload(
    ws: WorkspacePaths,
    plan: dict[str, Any],
    *,
    repair_type: str,
    review_id: str,
    previous_value: str,
    new_value: str,
    basis_refs: list[str],
    applied: bool,
    required_actions: list[str],
) -> dict[str, Any]:
    repair_id = prefixed_id(
        "legacy-semantic-repair",
        f"{plan['run_id']}:{plan['topic']}:{plan['active_claim_id']}:{repair_type}:{review_id}:{previous_value}:{new_value}:{applied}",
        max_slug=72,
    )
    record = LegacySemanticRepairRecord(
        repair_id=repair_id,
        migration_run_id=plan["run_id"],
        migration_dir=plan["migration_dir"],
        topic=plan["topic"],
        active_claim_id=plan["active_claim_id"],
        review_id=review_id,
        repair_type=repair_type,
        previous_value=previous_value,
        new_value=new_value,
        basis_refs=list(basis_refs),
        applied=applied,
        required_actions=list(required_actions),
    )
    write_record(
        ws.registry_dir("legacy_semantic_repairs") / f"{repair_id}.md",
        record,
        body=f"# Legacy Semantic Repair: {plan['topic']}\n\n**Applied:** {applied}\n\n{repair_type}\n",
    )
    return {
        "kind": "legacy_semantic_repair_apply",
        "repair_id": repair_id,
        "run_id": plan["run_id"],
        "migration_dir": plan["migration_dir"],
        "topic": plan["topic"],
        "active_claim_id": plan["active_claim_id"],
        "review_id": review_id,
        "repair_type": repair_type,
        "previous_value": previous_value,
        "new_value": new_value,
        "basis_refs": list(basis_refs),
        "applied": applied,
        "required_actions": list(required_actions),
        "semantic_lossless_proven": False,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": applied,
        "can_update_claim_trust": False,
    }
