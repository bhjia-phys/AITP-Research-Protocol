"""Per-topic packets for legacy semantic review."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review import build_legacy_semantic_review_queue
from brain.v5.models import (
    ClaimRecord,
    EvidenceRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ReferenceLocationRecord,
    SensemakingReportRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_records


def build_legacy_semantic_review_packet(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str,
) -> dict[str, Any]:
    """Build a read-only packet for actual per-topic semantic review."""

    queue = build_legacy_semantic_review_queue(ws, migration_dir=migration_dir)
    item = _queue_item(queue, topic)
    claim = _claim_payload(ws, item["active_claim_id"])
    typed = _typed_records_for_claim(ws, item["topic"], item["active_claim_id"])
    legacy_refs = _legacy_review_refs(item, typed)
    return {
        "kind": "legacy_semantic_review_packet",
        "run_id": queue["run_id"],
        "migration_dir": queue["migration_dir"],
        "topic": item["topic"],
        "queue_item": item,
        "active_claim": claim,
        "typed_records": typed,
        "legacy_review_refs": legacy_refs,
        "review_checklist": _review_checklist(item, typed, legacy_refs),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "truth_source": "migration_manifests_and_typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _queue_item(queue: dict[str, Any], topic: str) -> dict[str, Any]:
    for item in queue["items"]:
        if item["topic"] == topic:
            return item
    raise ValueError(f"unknown semantic review queue topic: {topic}")


def _claim_payload(ws: WorkspacePaths, claim_id: str) -> dict[str, Any]:
    if not claim_id:
        return {}
    claims = {claim.claim_id: claim for claim in list_records(ws.registry_dir("claims"), ClaimRecord)}
    claim = claims.get(claim_id)
    if claim is None:
        return {"claim_id": claim_id, "missing": True}
    return {
        "claim_id": claim.claim_id,
        "topic_id": claim.topic_id,
        "statement": claim.statement,
        "evidence_profile": claim.evidence_profile,
        "confidence_state": claim.confidence_state,
        "active_uncertainty": claim.active_uncertainty,
        "scope": claim.scope,
        "non_claims": claim.non_claims,
        "strongest_failure_mode": claim.strongest_failure_mode,
    }


def _typed_records_for_claim(ws: WorkspacePaths, topic: str, claim_id: str) -> dict[str, list[dict[str, Any]]]:
    return {
        "reference_locations": [
            _record_payload(record, "location_id")
            for record in list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
            if record.claim_id == claim_id
        ],
        "evidence": [
            _record_payload(record, "evidence_id")
            for record in list_records(ws.registry_dir("evidence"), EvidenceRecord)
            if record.claim_id == claim_id
        ],
        "physics_objects": [
            _record_payload(record, "object_id")
            for record in list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord)
            if record.topic_id == topic
        ],
        "object_relations": [
            _record_payload(record, "relation_id")
            for record in list_records(ws.registry_dir("object_relations"), ObjectRelationRecord)
            if record.topic_id == topic and (not record.claim_id or record.claim_id == claim_id)
        ],
        "sensemaking_reports": [
            _record_payload(record, "report_id")
            for record in list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord)
            if record.claim_id == claim_id
        ],
        "validation_results": [
            _record_payload(record, "result_id")
            for record in list_records(ws.registry_dir("validation_results"), ValidationResultRecord)
            if record.claim_id == claim_id
        ],
    }


def _record_payload(record: Any, id_attr: str) -> dict[str, Any]:
    payload = asdict(record)
    payload["record_id"] = getattr(record, id_attr)
    return payload


def _legacy_review_refs(item: dict[str, Any], typed: dict[str, list[dict[str, Any]]]) -> list[str]:
    refs = []
    refs.extend(item["source_reconstruction"].get("source_refs", []))
    for family in typed.values():
        for record in family:
            refs.extend(record.get("source_refs", []))
            source_ref = record.get("source_ref")
            if source_ref:
                refs.append(source_ref)
    return _unique(refs)


def _review_checklist(item: dict[str, Any], typed: dict[str, list[dict[str, Any]]], legacy_refs: list[str]) -> list[str]:
    checklist = [
        "compare_active_claim_statement_against_legacy_state_and_candidate_notes",
        "verify_scope_non_claims_and_failure_modes_are_preserved",
        "sample_archive_only_references_before_any_passed_review",
        "confirm_source_reconstruction_components_or_record_remaining_actions",
    ]
    if not legacy_refs:
        checklist.append("locate_legacy_source_refs_before_review_result")
    if not typed["evidence"]:
        checklist.append("record_or_link_typed_evidence_before_passed_review")
    if item["source_reconstruction"]["status"] != "complete":
        checklist.append("complete_source_reconstruction_before_trust_promotion")
    return _unique(checklist)


def _unique(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
