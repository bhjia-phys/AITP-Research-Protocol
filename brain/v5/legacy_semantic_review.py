"""Semantic review queue for completed legacy-to-v5 migration runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dataclasses import asdict

from brain.v5.ids import prefixed_id
from brain.v5.legacy_migration_audit import audit_legacy_migration_coverage
from brain.v5.models import (
    ClaimRecord,
    EvidenceRecord,
    HumanCheckpointRecord,
    LegacySemanticReviewResultRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction import audit_source_reconstruction_batch
from brain.v5.store import list_records, write_record


def build_legacy_semantic_review_queue(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build per-topic semantic review work items for a legacy migration run.

    This is an orientation-only review queue. It turns the existing accounting
    audit into concrete human/v5 review work without claiming semantic proof.
    """

    coverage = audit_legacy_migration_coverage(ws, migration_dir=migration_dir)
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    claim_ids = [
        topic["active_claim_id"]
        for topic in coverage["topics"]
        if topic.get("active_claim_id") in claims
    ]
    source_audits = audit_source_reconstruction_batch(ws, claim_ids)
    review_results = _group_review_results(
        list_records(ws.registry_dir("legacy_semantic_reviews"), LegacySemanticReviewResultRecord),
        run_id=coverage["run_id"],
    )
    items = [
        _review_item(
            topic,
            source_audits.get(topic.get("active_claim_id", "")),
            claims,
            review_results.get(str(topic.get("topic") or ""), []),
        )
        for topic in coverage["topics"]
    ]
    priority_counts = _priority_counts(items)
    queue_status = "coverage_gaps_first" if coverage["coverage_status"] == "coverage_gaps" else "ready_for_semantic_review"

    return {
        "kind": "legacy_semantic_review_queue",
        "run_id": coverage["run_id"],
        "migration_dir": coverage["migration_dir"],
        "workspace": coverage["workspace"],
        "legacy_root": coverage["legacy_root"],
        "v5_root": coverage["v5_root"],
        "queue_status": queue_status,
        "topic_count": coverage["topic_count"],
        "legacy_file_count": coverage["legacy_file_count"],
        "review_item_count": len(items),
        "priority_counts": priority_counts,
        "items": items,
        "coverage_audit": {
            "coverage_status": coverage["coverage_status"],
            "gap_topic_count": coverage["gap_topic_count"],
            "gap_topics": coverage["gap_topics"],
            "file_preservation_ok": coverage["file_preservation"]["ok"],
            "archive_reference_coverage_ok": coverage["archive_reference_coverage"]["ok"],
            "markdown_readability_ok": coverage["markdown_readability"]["ok"],
        },
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "semantic_review_reason": (
            "This queue operationalizes semantic review; it does not prove that "
            "legacy physics claims were interpreted correctly."
        ),
        "truth_source": "migration_manifests_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _review_item(
    topic: dict[str, Any],
    source_audit: dict[str, Any] | None,
    claims: dict[str, ClaimRecord],
    review_results: list[LegacySemanticReviewResultRecord],
) -> dict[str, Any]:
    active_claim_id = str(topic.get("active_claim_id") or "")
    source_review = _source_review(active_claim_id, source_audit, claims)
    reasons = _review_reasons(topic, source_review)
    actions = _recommended_actions(topic, source_review)
    latest_review = _latest_review_payload(review_results)
    return {
        "topic": str(topic.get("topic") or ""),
        "legacy_shape": str(topic.get("legacy_shape") or ""),
        "active_claim_id": active_claim_id,
        "coverage_status": str(topic.get("coverage_status") or ""),
        "file_count": int(topic.get("file_count") or 0),
        "structured_file_count": int(topic.get("structured_file_count") or 0),
        "archive_reference_count": int(topic.get("archive_reference_count") or 0),
        "preserved_source_refs": int(topic.get("preserved_source_refs") or 0),
        "written_records": dict(topic.get("written_records") or {}),
        "source_reconstruction": source_review,
        "semantic_review_status": _semantic_review_status(latest_review),
        "semantic_review_result_ids": [record.review_id for record in review_results],
        "latest_semantic_review": latest_review,
        "semantic_review_required": True,
        "review_priority": _review_priority(topic, source_review),
        "review_reasons": reasons,
        "recommended_actions": actions,
        "can_update_claim_trust": False,
    }


def record_legacy_semantic_review_result(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
    status: str,
    summary: str,
    active_claim_id: str = "",
    reviewed_legacy_refs: list[str] | None = None,
    reviewed_typed_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    remaining_actions: list[str] | None = None,
    checkpoint_id: str = "",
    reviewer_role: str = "human_or_adversarial_reviewer",
) -> LegacySemanticReviewResultRecord:
    """Persist a per-topic semantic review result for a legacy migration run."""

    coverage = audit_legacy_migration_coverage(ws, migration_dir=migration_dir)
    topic_payload = _topic_payload(coverage, topic)
    explicit_claim_id = active_claim_id.strip()
    claim_id = explicit_claim_id or str(topic_payload.get("active_claim_id") or "")
    legacy_refs = _clean_list(reviewed_legacy_refs)
    typed_refs = _clean_list(reviewed_typed_refs)
    evidence = _clean_list(evidence_refs)
    validations = _clean_list(validation_result_ids)
    actions = _clean_list(remaining_actions)
    if explicit_claim_id:
        _require_claim(ws, explicit_claim_id, topic=str(topic_payload["topic"]))
    elif evidence or validations:
        _require_claim(ws, claim_id, topic=str(topic_payload["topic"]))
    if status not in {"passed", "needs_revision", "inconclusive"}:
        raise ValueError("legacy semantic review status must be passed, needs_revision, or inconclusive")
    if not summary.strip():
        raise ValueError("legacy semantic review summary must not be empty")
    if not any([legacy_refs, typed_refs, evidence, validations]):
        raise ValueError("legacy semantic review basis must cite legacy refs, typed refs, evidence, or validation results")
    _validate_basis_refs(ws, claim_id=claim_id, evidence_refs=evidence, validation_result_ids=validations)
    if checkpoint_id:
        _require_semantic_review_checkpoint(ws, checkpoint_id, claim_id=claim_id, topic=str(topic_payload["topic"]))
    review_id = prefixed_id(
        "legacy-semantic-review",
        f"{coverage['run_id']}:{topic_payload['topic']}:{claim_id}:{status}:{legacy_refs}:{typed_refs}:{evidence}:{validations}:{summary}",
        max_slug=72,
    )
    record = LegacySemanticReviewResultRecord(
        review_id=review_id,
        migration_run_id=coverage["run_id"],
        migration_dir=coverage["migration_dir"],
        topic=str(topic_payload["topic"]),
        active_claim_id=claim_id,
        status=status,
        summary=summary,
        reviewer_role=reviewer_role,
        reviewed_legacy_refs=legacy_refs,
        reviewed_typed_refs=typed_refs,
        evidence_refs=evidence,
        validation_result_ids=validations,
        remaining_actions=actions,
        checkpoint_id=checkpoint_id,
    )
    write_record(
        ws.registry_dir("legacy_semantic_reviews") / f"{review_id}.md",
        record,
        body=f"# Legacy Semantic Review: {topic_payload['topic']}\n\n**Status:** {status}\n\n{summary}\n",
    )
    return record


def _source_review(
    claim_id: str,
    source_audit: dict[str, Any] | None,
    claims: dict[str, ClaimRecord],
) -> dict[str, Any]:
    if not claim_id:
        return {
            "status": "missing_claim_id",
            "complete": False,
            "missing_components": ["active_claim_id"],
            "source_refs": [],
        }
    if claim_id not in claims:
        return {
            "status": "missing_claim_record",
            "complete": False,
            "missing_components": ["claim_record"],
            "source_refs": [],
        }
    if source_audit is None:
        return {
            "status": "not_audited",
            "complete": False,
            "missing_components": ["source_reconstruction_audit"],
            "source_refs": [],
        }
    complete = bool(source_audit.get("complete") is True)
    return {
        "status": "complete" if complete else "incomplete",
        "complete": complete,
        "missing_components": [
            str(component) for component in source_audit.get("missing_components", []) if str(component)
        ],
        "source_refs": [str(ref) for ref in source_audit.get("source_refs", []) if str(ref)],
    }


def _topic_payload(coverage: dict[str, Any], topic: str) -> dict[str, Any]:
    target = topic.strip()
    for item in coverage["topics"]:
        if item["topic"] == target:
            return item
    raise ValueError(f"unknown legacy migration topic: {topic}")


def _require_claim(ws: WorkspacePaths, claim_id: str, *, topic: str) -> None:
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    claim = claims.get(claim_id)
    if claim is None:
        raise ValueError(f"unknown active_claim_id: {claim_id}")
    if claim.topic_id != topic:
        raise ValueError(f"active_claim_id must belong to migrated topic {topic}: {claim_id}")


def _validate_basis_refs(
    ws: WorkspacePaths,
    *,
    claim_id: str,
    evidence_refs: list[str],
    validation_result_ids: list[str],
) -> None:
    if not claim_id and (evidence_refs or validation_result_ids):
        raise ValueError("typed evidence/validation review refs require active_claim_id")
    _require_same_claim_refs(
        "evidence ref",
        evidence_refs,
        list_records(ws.registry_dir("evidence"), EvidenceRecord),
        "evidence_id",
        claim_id,
    )
    _require_same_claim_refs(
        "validation result",
        validation_result_ids,
        list_records(ws.registry_dir("validation_results"), ValidationResultRecord),
        "result_id",
        claim_id,
    )


def _require_same_claim_refs(
    label: str,
    ids: list[str],
    records: list,
    id_attr: str,
    claim_id: str,
) -> None:
    records_by_id = {getattr(record, id_attr): record for record in records}
    for ref_id in ids:
        record = records_by_id.get(ref_id)
        if record is None:
            raise ValueError(f"unknown {label}: {ref_id}")
        if record.claim_id != claim_id:
            raise ValueError(f"{label} must belong to the reviewed claim: {ref_id}")


def _require_semantic_review_checkpoint(
    ws: WorkspacePaths,
    checkpoint_id: str,
    *,
    claim_id: str,
    topic: str,
) -> None:
    checkpoints = list_records(ws.registry_dir("checkpoints"), HumanCheckpointRecord)
    checkpoint = next((item for item in checkpoints if item.checkpoint_id == checkpoint_id), None)
    if checkpoint is None:
        raise ValueError(f"unknown legacy semantic review checkpoint: {checkpoint_id}")
    if checkpoint.topic_id != topic or checkpoint.claim_id != claim_id:
        raise ValueError("legacy semantic review checkpoint must belong to the reviewed topic and claim")
    if checkpoint.status != "decided" or checkpoint.decision not in {"approve", "approve_semantic_review"}:
        raise ValueError("legacy semantic review checkpoint must be decided with approve or approve_semantic_review")


def _group_review_results(
    records: list[LegacySemanticReviewResultRecord],
    *,
    run_id: str,
) -> dict[str, list[LegacySemanticReviewResultRecord]]:
    grouped: dict[str, list[LegacySemanticReviewResultRecord]] = {}
    for record in records:
        if record.migration_run_id != run_id:
            continue
        grouped.setdefault(record.topic, []).append(record)
    for results in grouped.values():
        results.sort(key=lambda record: record.review_id)
    return grouped


def _latest_review_payload(records: list[LegacySemanticReviewResultRecord]) -> dict[str, Any]:
    if not records:
        return {}
    record = records[-1]
    payload = asdict(record)
    payload["orientation_only"] = True
    return payload


def _semantic_review_status(latest_review: dict[str, Any]) -> str:
    status = latest_review.get("status")
    if status == "passed":
        return "reviewed_passed"
    if status == "needs_revision":
        return "reviewed_needs_revision"
    if status == "inconclusive":
        return "reviewed_inconclusive"
    return "pending"


def _review_priority(topic: dict[str, Any], source_review: dict[str, Any]) -> str:
    if topic.get("coverage_status") == "coverage_gaps" or int(topic.get("unaccounted_file_count") or 0) > 0:
        return "critical"
    if source_review["status"] in {"missing_claim_id", "missing_claim_record"}:
        return "critical"
    if topic.get("legacy_shape") != "canonical_topic" or not source_review["complete"]:
        return "high"
    if int(topic.get("archive_reference_count") or 0) > 0:
        return "medium"
    return "low"


def _review_reasons(topic: dict[str, Any], source_review: dict[str, Any]) -> list[str]:
    reasons = ["semantic_lossless_not_proven"]
    if topic.get("coverage_status") == "coverage_gaps":
        reasons.append("coverage_gaps")
    if topic.get("legacy_shape") != "canonical_topic":
        reasons.append("noncanonical_legacy_seed")
    if int(topic.get("archive_reference_count") or 0) > 0:
        reasons.append("archive_only_records_require_sampling")
    if source_review["status"] != "complete":
        reasons.append(f"source_reconstruction_{source_review['status']}")
    return _unique(reasons)


def _recommended_actions(topic: dict[str, Any], source_review: dict[str, Any]) -> list[str]:
    actions = ["review_claim_statement_against_legacy_sources"]
    if topic.get("coverage_status") == "coverage_gaps":
        actions.append("resolve_file_accounting_or_archive_reference_gaps")
    if topic.get("legacy_shape") != "canonical_topic":
        actions.append("classify_noncanonical_seed_before_promotion")
    if int(topic.get("archive_reference_count") or 0) > 0:
        actions.append("sample_archive_reference_readback")
    if not source_review["complete"]:
        actions.append("complete_source_reconstruction")
    actions.extend([
        "record_validation_or_failure_modes",
        "decide_human_checkpoint_before_promotion",
    ])
    return _unique(actions)


def _priority_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for item in items:
        counts[item["review_priority"]] += 1
    return counts


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _clean_list(values: list[str] | None) -> list[str]:
    return [value.strip() for value in values or [] if value.strip()]
