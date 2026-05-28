"""Required-action hints for conservative legacy semantic repairs."""

from __future__ import annotations

from typing import Any


def required_repair_actions(
    *,
    active_claim: dict[str, Any],
    latest_review: dict[str, Any],
    proposed_repairs: list[dict[str, Any]],
) -> list[str]:
    if proposed_repairs:
        actions: list[str] = []
        if any(not _requires_external_evidence(repair) for repair in proposed_repairs):
            actions.append("review_proposed_repairs_before_apply")
        for repair in proposed_repairs:
            if _requires_external_evidence(repair):
                repair_type = str(repair.get("repair_type") or "")
                if repair_type == "validation_result_revision":
                    actions.append("record_revised_validation_result_before_semantic_pass")
                else:
                    actions.append("perform_manual_non_claim_repair")
        return _unique(actions)
    actions: list[str] = []
    if not latest_review:
        actions.append("record_initial_semantic_review_result")
    elif latest_review.get("status") != "needs_revision":
        actions.append("record_needs_revision_review_with_specific_repair_basis")
    else:
        actions.append("record_more_specific_repair_basis_or_keep_blocking")
    action_text = " ".join(str(action) for action in latest_review.get("remaining_actions", [])).lower()
    if not str(active_claim.get("statement") or "") and (
        "topic_question" in action_text
        or "claim_statement" in action_text
        or "statement" in action_text
    ):
        actions.append("supply_or_review_human_topic_question_before_claim_statement_backfill")
    actions.append("keep_semantic_review_blocking_until_typed_review_basis_exists")
    return _unique(actions)


def _requires_external_evidence(repair: dict[str, Any]) -> bool:
    return bool(repair.get("requires_external_evidence") is True)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
