"""Read-only source-stack coverage manifest for active claims."""

from __future__ import annotations

from brain.v5.evidence import required_output_coverage
from brain.v5.models import ClaimRecord, EvidenceRecord, SourceReconstructionReviewResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.risk import action_budget_for_level, assess_claim_risk
from brain.v5.source_reconstruction import audit_source_reconstruction_batch
from brain.v5.store import list_valid_records

_COVERAGE_STATUSES = (
    "complete",
    "evidence_gap",
    "reconstruction_gap",
    "review_gap",
)


def build_source_stack_coverage_manifest(ws: WorkspacePaths) -> dict:
    """Combine evidence-output, reconstruction, and review coverage for claims."""

    claims = list_valid_records(ws.registry_dir("claims"), ClaimRecord)
    audits = audit_source_reconstruction_batch(ws, [claim.claim_id for claim in claims])
    evidence_by_claim = _group_by_claim(list_valid_records(ws.registry_dir("evidence"), EvidenceRecord))
    reviews_by_claim = _group_reviews_by_claim(
        list_valid_records(ws.registry_dir("source_reconstruction_reviews"), SourceReconstructionReviewResultRecord)
    )
    items = [
        _coverage_item(
            claim,
            audit=audits[claim.claim_id],
            evidence=evidence_by_claim.get(claim.claim_id, []),
            reviews=reviews_by_claim.get(claim.claim_id, []),
        )
        for claim in claims
    ]
    items.sort(key=lambda item: (_coverage_sort_rank(item["coverage_status"]), item["topic_id"], item["claim_id"]))
    return {
        "kind": "source_stack_coverage_manifest",
        "claim_count": len(items),
        "coverage_status_counts": _status_counts(items),
        "missing_required_output_counts": _missing_required_output_counts(items),
        "source_component_gap_counts": _source_component_gap_counts(items),
        "source_review_status_counts": _review_status_counts(items),
        "items": items,
        "next_actions": [
            action
            for item in items
            if item["coverage_status"] != "complete"
            for action in item["next_actions"]
        ],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _coverage_item(
    claim: ClaimRecord,
    *,
    audit: dict,
    evidence: list[EvidenceRecord],
    reviews: list[SourceReconstructionReviewResultRecord],
) -> dict:
    risk = assess_claim_risk(claim)
    action_budget = risk.action_budget if risk.action_budget else action_budget_for_level(risk.level)
    evidence_coverage = required_output_coverage(evidence, required_outputs=action_budget.required_outputs)
    latest_review = reviews[-1] if reviews else None
    review_status = latest_review.status if latest_review else "pending"
    missing_outputs = list(evidence_coverage.missing_outputs)
    missing_components = list(audit["missing_components"])
    coverage_status = _coverage_status(
        missing_required_outputs=missing_outputs,
        source_reconstruction_complete=bool(audit["complete"]),
        source_reconstruction_review_status=review_status,
    )
    return {
        "topic_id": claim.topic_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "risk_level": action_budget.level,
        "required_outputs": list(action_budget.required_outputs),
        "satisfied_required_outputs": [
            output
            for output in action_budget.required_outputs
            if output in set(evidence_coverage.satisfied_outputs)
        ],
        "missing_required_outputs": missing_outputs,
        "evidence_ids_by_output": dict(evidence_coverage.evidence_ids_by_output),
        "source_reconstruction_complete": bool(audit["complete"]),
        "missing_source_components": missing_components,
        "source_reconstruction_review_status": review_status,
        "latest_source_review_result_id": latest_review.result_id if latest_review else "",
        "coverage_status": coverage_status,
        "next_actions": _next_actions(
            claim.claim_id,
            missing_required_outputs=missing_outputs,
            source_reconstruction_complete=bool(audit["complete"]),
            source_reconstruction_review_status=review_status,
        ),
        "can_update_claim_trust": False,
    }


def _coverage_status(
    *,
    missing_required_outputs: list[str],
    source_reconstruction_complete: bool,
    source_reconstruction_review_status: str,
) -> str:
    if missing_required_outputs:
        return "evidence_gap"
    if not source_reconstruction_complete:
        return "reconstruction_gap"
    if source_reconstruction_review_status != "passed":
        return "review_gap"
    return "complete"


def _next_actions(
    claim_id: str,
    *,
    missing_required_outputs: list[str],
    source_reconstruction_complete: bool,
    source_reconstruction_review_status: str,
) -> list[str]:
    actions: list[str] = []
    if missing_required_outputs:
        actions.append(f"record_evidence_for_required_outputs:{claim_id}")
    if not source_reconstruction_complete:
        actions.append(f"complete_source_reconstruction:{claim_id}")
    if source_reconstruction_review_status != "passed":
        actions.append(f"review_source_reconstruction:{claim_id}")
    return actions


def _group_by_claim(records: list) -> dict[str, list]:
    grouped: dict[str, list] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    return grouped


def _group_reviews_by_claim(
    records: list[SourceReconstructionReviewResultRecord],
) -> dict[str, list[SourceReconstructionReviewResultRecord]]:
    grouped: dict[str, list[SourceReconstructionReviewResultRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    for reviews in grouped.values():
        reviews.sort(key=lambda review: (review.created_at, review.result_id))
    return grouped


def _status_counts(items: list[dict]) -> dict[str, int]:
    counts = {status: 0 for status in _COVERAGE_STATUSES}
    for item in items:
        status = item["coverage_status"]
        if status in counts:
            counts[status] += 1
    return counts


def _missing_required_output_counts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for output in item["missing_required_outputs"]:
            counts[output] = counts.get(output, 0) + 1
    return dict(sorted(counts.items()))


def _source_component_gap_counts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for component in item["missing_source_components"]:
            counts[component] = counts.get(component, 0) + 1
    return dict(sorted(counts.items()))


def _review_status_counts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = item["source_reconstruction_review_status"]
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def _coverage_sort_rank(status: str) -> int:
    return {"evidence_gap": 0, "reconstruction_gap": 1, "review_gap": 2, "complete": 3}.get(status, 4)
