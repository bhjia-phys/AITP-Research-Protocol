"""Shared repair candidate helpers for legacy semantic review surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.models import ValidationResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records

VALIDATION_RESULT_REVISION_PROPOSED_VALUE = (
    "Record a revised validation result after repairing or replacing the failed validation surface."
)


def validation_results_by_id(ws: WorkspacePaths) -> dict[str, ValidationResultRecord]:
    return {
        record.result_id: record
        for record in list_records(ws.registry_dir("validation_results"), ValidationResultRecord)
    }


def validation_result_revision_repairs(
    latest_review: dict[str, Any],
    results_by_id: dict[str, ValidationResultRecord],
) -> list[dict[str, Any]]:
    review_id = str(latest_review.get("review_id") or "")
    repairs: list[dict[str, Any]] = []
    for result_id in _unique([str(value) for value in latest_review.get("validation_result_ids", [])]):
        result = results_by_id.get(result_id)
        if result is None or result.status != "failed":
            continue
        repairs.append({
            "repair_type": "validation_result_revision",
            "target_ref": result.result_id,
            "current_value": result.status,
            "proposed_value": VALIDATION_RESULT_REVISION_PROPOSED_VALUE,
            "basis_refs": _unique([result.result_id, review_id]),
            "mutation_authority": "none_review_and_apply_separately",
            "requires_external_evidence": True,
        })
    return repairs


def failed_validation_result_ids(
    latest_review: dict[str, Any],
    results_by_id: dict[str, ValidationResultRecord],
) -> list[str]:
    result_ids: list[str] = []
    for result_id in (str(value).strip() for value in latest_review.get("validation_result_ids", [])):
        result = results_by_id.get(result_id)
        if result is not None and result.status == "failed":
            result_ids.append(result_id)
    return _unique(result_ids)


def non_claim_repair_actions(repair_type: str) -> list[str]:
    if repair_type == "validation_result_revision":
        return ["record_revised_validation_result_before_semantic_pass"]
    return ["perform_manual_non_claim_repair"]


def semantic_action_tokens(raw_actions: list[str] | None) -> set[str]:
    tokens: set[str] = set()
    for action in raw_actions or []:
        text = str(action).strip()
        if not text:
            continue
        tokens.add(text)
        normalized = " ".join(text.lower().replace("_", " ").split())
        if "backfill" in normalized and "claim statement" in normalized and "research question" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_state_question")
        if "l3" in normalized and "distilled claim" in normalized and "claim statement" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_l3_distilled_claim")
        if "l1" in normalized and "bounded question" in normalized and "claim statement" in normalized:
            tokens.add("backfill_active_claim_statement_from_legacy_l1_bounded_question")
        if "scope" in normalized and "question contract" in normalized:
            tokens.add("backfill_active_claim_scope_from_legacy_l1_question_contract")
        if "scope" in normalized and "candidate" in normalized and "regime" in normalized:
            tokens.add("backfill_active_claim_scope_from_legacy_candidate_regime")
        if "failure" in normalized and "non success" in normalized:
            tokens.add("backfill_active_claim_failure_mode_from_legacy_l1_non_success_conditions")
        if "failure" in normalized and "legacy review" in normalized:
            tokens.add("backfill_active_claim_failure_mode_from_legacy_review")
    return tokens


def manifest_repair_candidate(
    ws: WorkspacePaths,
    migration_dir: str,
    topic: str,
    review_id: str,
    *,
    surface: str,
    command: str,
    repair_type: str,
    requires_external_evidence: bool = False,
) -> dict[str, Any]:
    payload = {
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
    if requires_external_evidence:
        payload["requires_external_evidence"] = True
    return payload


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
