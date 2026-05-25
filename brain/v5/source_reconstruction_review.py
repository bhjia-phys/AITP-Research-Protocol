"""Typed review results for source reconstruction packets."""

from __future__ import annotations

from brain.v5.ids import prefixed_id
from brain.v5.models import (
    ClaimRecord,
    EvidenceRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ReferenceLocationRecord,
    SourceReconstructionReviewResultRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction import audit_source_reconstruction_batch
from brain.v5.store import list_records, write_record
from brain.v5.workspace import get_claim

_REVIEWABLE_COMPONENTS = {
    "definitions",
    "assumptions_or_scope",
    "source_locations",
    "dependency_graph",
    "reconstruction_path",
    "failure_conditions",
}


def build_source_reconstruction_review_manifest(ws: WorkspacePaths) -> dict:
    """Build a read-only manifest of source reconstruction review progress."""

    claims = list_records(ws.registry_dir("claims"), ClaimRecord)
    audits = audit_source_reconstruction_batch(ws, [claim.claim_id for claim in claims])
    reviews_by_claim = _group_reviews_by_claim(
        list_records(ws.registry_dir("source_reconstruction_reviews"), SourceReconstructionReviewResultRecord)
    )
    items = [
        _review_manifest_item(claim, audits[claim.claim_id], reviews_by_claim.get(claim.claim_id, []))
        for claim in claims
    ]
    items.sort(key=lambda item: (_review_sort_rank(item["review_status"]), item["topic_id"], item["claim_id"]))
    return {
        "kind": "source_reconstruction_review_manifest",
        "claim_count": len(items),
        "review_progress": _review_progress(items),
        "items": items,
        "next_actions": [
            f"source_reconstruction_review:{item['claim_id']}"
            for item in items
            if item["review_status"] in {"pending", "needs_revision", "inconclusive"}
        ],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def record_source_reconstruction_review_result(
    ws: WorkspacePaths,
    *,
    claim_id: str,
    status: str,
    reviewed_components: list[str] | None = None,
    basis_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    remaining_actions: list[str] | None = None,
    reviewer_role: str = "human_or_adversarial_reviewer",
    summary: str = "",
) -> SourceReconstructionReviewResultRecord:
    """Persist a typed basis for source reconstruction component review."""

    claim = get_claim(ws, claim_id)
    components = _clean_list(reviewed_components)
    basis = _clean_list(basis_refs)
    evidence = _clean_list(evidence_refs)
    validations = _clean_list(validation_result_ids)
    references = _clean_list(reference_location_ids)
    objects = _clean_list(object_ids)
    relations = _clean_list(relation_ids)
    actions = _clean_list(remaining_actions)
    _validate_status(status)
    _validate_components(components)
    if not summary.strip():
        raise ValueError("source reconstruction review summary must not be empty")
    if not any([basis, evidence, validations, references, objects, relations]):
        raise ValueError("source reconstruction review basis must cite source, typed, evidence, validation, object, or relation refs")
    _validate_typed_basis_refs(
        ws,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        evidence_refs=evidence,
        validation_result_ids=validations,
        reference_location_ids=references,
        object_ids=objects,
        relation_ids=relations,
    )
    result_id = prefixed_id(
        "source-reconstruction-review",
        f"{claim.claim_id}:{status}:{components}:{basis}:{evidence}:{validations}:{references}:{objects}:{relations}:{summary}",
        max_slug=72,
    )
    record = SourceReconstructionReviewResultRecord(
        result_id=result_id,
        topic_id=claim.topic_id,
        claim_id=claim.claim_id,
        status=status,
        reviewed_components=components,
        basis_refs=basis,
        evidence_refs=evidence,
        validation_result_ids=validations,
        reference_location_ids=references,
        object_ids=objects,
        relation_ids=relations,
        remaining_actions=actions,
        reviewer_role=reviewer_role,
        summary=summary,
    )
    write_record(
        ws.registry_dir("source_reconstruction_reviews") / f"{result_id}.md",
        record,
        body=f"# Source Reconstruction Review Result: {result_id}\n\n**Status:** {status}\n\n{summary}\n",
    )
    return record


def _review_manifest_item(
    claim: ClaimRecord,
    audit: dict,
    reviews: list[SourceReconstructionReviewResultRecord],
) -> dict:
    latest = _latest_review(reviews)
    review_status = latest.status if latest else "pending"
    reviewed_components = _unique([
        component for review in reviews for component in review.reviewed_components
    ])
    remaining_actions = _unique([
        action for review in reviews for action in review.remaining_actions
    ])
    return {
        "topic_id": claim.topic_id,
        "claim_id": claim.claim_id,
        "claim_statement": claim.statement,
        "source_reconstruction_status": "complete" if audit["complete"] else "incomplete",
        "missing_components": list(audit["missing_components"]),
        "review_status": review_status,
        "review_result_ids": [review.result_id for review in reviews],
        "latest_review_result": _review_payload(latest) if latest else {},
        "reviewed_components": reviewed_components,
        "remaining_actions": remaining_actions,
        "review_packet_cli": f"aitp-v5 source reconstruction-review --claim {claim.claim_id}",
        "result_cli": f"aitp-v5 source reconstruction-review-result --claim {claim.claim_id} <args>",
        "next_actions": _review_next_actions(review_status, audit, remaining_actions),
        "can_update_claim_trust": False,
    }


def _review_payload(record: SourceReconstructionReviewResultRecord) -> dict:
    return {
        "result_id": record.result_id,
        "status": record.status,
        "reviewed_components": list(record.reviewed_components),
        "basis_refs": list(record.basis_refs),
        "evidence_refs": list(record.evidence_refs),
        "validation_result_ids": list(record.validation_result_ids),
        "reference_location_ids": list(record.reference_location_ids),
        "object_ids": list(record.object_ids),
        "relation_ids": list(record.relation_ids),
        "remaining_actions": list(record.remaining_actions),
        "summary": record.summary,
        "can_update_claim_trust": False,
    }


def _review_next_actions(review_status: str, audit: dict, remaining_actions: list[str]) -> list[str]:
    actions: list[str] = []
    if review_status == "pending":
        actions.append("source_reconstruction_review")
    if review_status in {"needs_revision", "inconclusive"}:
        actions.extend(remaining_actions or ["complete_source_reconstruction_review"])
    if not audit["complete"]:
        actions.append("complete_source_reconstruction")
    return _unique(actions)


def _group_reviews_by_claim(
    records: list[SourceReconstructionReviewResultRecord],
) -> dict[str, list[SourceReconstructionReviewResultRecord]]:
    grouped: dict[str, list[SourceReconstructionReviewResultRecord]] = {}
    for record in records:
        grouped.setdefault(record.claim_id, []).append(record)
    for reviews in grouped.values():
        reviews.sort(key=lambda review: review.result_id)
    return grouped


def _latest_review(
    reviews: list[SourceReconstructionReviewResultRecord],
) -> SourceReconstructionReviewResultRecord | None:
    if not reviews:
        return None
    return reviews[-1]


def _review_progress(items: list[dict]) -> dict[str, int]:
    counts = {"passed": 0, "needs_revision": 0, "inconclusive": 0, "pending": 0}
    for item in items:
        counts[item["review_status"]] += 1
    return counts


def _review_sort_rank(status: str) -> int:
    return {"needs_revision": 0, "inconclusive": 1, "pending": 2, "passed": 3}.get(status, 4)


def _validate_status(status: str) -> None:
    if status not in {"passed", "needs_revision", "inconclusive"}:
        raise ValueError("source reconstruction review status must be passed, needs_revision, or inconclusive")


def _validate_components(components: list[str]) -> None:
    if not components:
        raise ValueError("reviewed_components must not be empty")
    unknown = [component for component in components if component not in _REVIEWABLE_COMPONENTS]
    if unknown:
        raise ValueError(f"unknown source reconstruction components: {', '.join(unknown)}")


def _validate_typed_basis_refs(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    evidence_refs: list[str],
    validation_result_ids: list[str],
    reference_location_ids: list[str],
    object_ids: list[str],
    relation_ids: list[str],
) -> None:
    _require_same_claim_refs("evidence ref", evidence_refs, list_records(ws.registry_dir("evidence"), EvidenceRecord), "evidence_id", claim_id)
    _require_same_claim_refs(
        "validation result",
        validation_result_ids,
        list_records(ws.registry_dir("validation_results"), ValidationResultRecord),
        "result_id",
        claim_id,
    )
    _require_same_claim_refs(
        "reference location",
        reference_location_ids,
        list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        "location_id",
        claim_id,
    )
    _require_topic_refs("physics object", object_ids, list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord), "object_id", topic_id)
    _require_relation_refs(
        relation_ids,
        list_records(ws.registry_dir("object_relations"), ObjectRelationRecord),
        topic_id,
        claim_id,
    )


def _require_same_claim_refs(label: str, ids: list[str], records: list, id_attr: str, claim_id: str) -> None:
    records_by_id = {getattr(record, id_attr): record for record in records}
    for ref_id in ids:
        record = records_by_id.get(ref_id)
        if record is None:
            raise ValueError(f"unknown {label}: {ref_id}")
        if record.claim_id != claim_id:
            raise ValueError(f"{label} must belong to the reviewed claim: {ref_id}")


def _require_topic_refs(label: str, ids: list[str], records: list, id_attr: str, topic_id: str) -> None:
    records_by_id = {getattr(record, id_attr): record for record in records}
    for ref_id in ids:
        record = records_by_id.get(ref_id)
        if record is None:
            raise ValueError(f"unknown {label}: {ref_id}")
        if record.topic_id != topic_id:
            raise ValueError(f"{label} must belong to the reviewed topic: {ref_id}")


def _require_relation_refs(ids: list[str], records: list[ObjectRelationRecord], topic_id: str, claim_id: str) -> None:
    records_by_id = {record.relation_id: record for record in records}
    for relation_id in ids:
        record = records_by_id.get(relation_id)
        if record is None:
            raise ValueError(f"unknown object relation: {relation_id}")
        if record.topic_id != topic_id or (record.claim_id and record.claim_id != claim_id):
            raise ValueError(f"object relation must belong to the reviewed topic and claim: {relation_id}")


def _clean_list(values: list[str] | None) -> list[str]:
    seen: set[str] = set()
    cleaned: list[str] = []
    for value in values or []:
        clean = str(value).strip()
        if clean and clean not in seen:
            seen.add(clean)
            cleaned.append(clean)
    return cleaned


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
