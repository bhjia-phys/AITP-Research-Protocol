"""Read-only readiness audit for literature source sets."""

from __future__ import annotations

from typing import Any

from brain.v5.models import (
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    SensemakingReportRecord,
    SourceAssetRecord,
    SourceReconstructionReviewResultRecord,
)
from brain.v5.record_refs import lookup_record_refs
from brain.v5.store import list_records
from brain.v5.workspace import get_session_binding


_REQUIRED_COMPONENTS = (
    "source_asset",
    "reference_location",
    "extraction_trace",
    "source_reconstruction_review",
)
_READY_STATUSES = {"passed", "complete", "accepted", "sufficient", "reviewed"}


def build_literature_source_set_readiness(
    ws,
    *,
    session_id: str,
    source_refs: list[str],
    optional_claim_id: str = "",
    readiness_scope: str = "source_set_learning",
) -> dict[str, Any]:
    """Audit whether a source set is ready for literature synthesis."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_refs = _nonempty_unique(source_refs)
    if not normalized_refs:
        raise ValueError("source_refs is required")
    records = _record_index(ws)
    source_items = [
        _source_item(
            source_ref,
            topic_id=session.topic_id,
            claim_id=claim_id,
            records=records,
        )
        for source_ref in normalized_refs
    ]
    component_counts = _component_counts(source_items)
    missing_components = sorted(
        component
        for component, counts in component_counts.items()
        if counts["missing_count"] > 0
    )
    ready_source_count = sum(1 for item in source_items if item["readiness_status"] == "ready_for_synthesis_review")
    return {
        "ok": True,
        "kind": "literature_source_set_readiness",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "readiness_scope": readiness_scope,
        "source_refs": normalized_refs,
        "source_ref_count": len(normalized_refs),
        "source_items": source_items,
        "source_item_count": len(source_items),
        "ready_source_count": ready_source_count,
        "blocked_source_count": len(source_items) - ready_source_count,
        "component_counts": component_counts,
        "missing_components": missing_components,
        "record_ref_lookup": lookup_record_refs(ws, normalized_refs),
        "recommended_next_entrypoints": _recommended_next_entrypoints(missing_components),
        "readiness_policy": {
            "source": "typed_records_and_agent_supplied_source_refs",
            "host_may_use_for": [
                "source_set_readiness_audit",
                "literature_learning_route_planning",
                "missing_source_stack_triage",
                "next_entrypoint_selection",
            ],
            "required_components": list(_REQUIRED_COMPONENTS),
            "requires_all_sources_ready_before_synthesis": True,
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "register_source_asset",
                "record_reference_location",
                "build_literature_source_extraction_candidates",
                "record_physics_object",
                "record_object_relation",
                "create_proof_obligation",
                "record_sensemaking_report",
                "record_source_reconstruction_review_result",
                "build_literature_comparison_draft",
                "preflight_trust_update",
            ],
            "forbidden_uses": [
                "paper_summary_as_evidence",
                "source_set_synthesis_as_evidence",
                "source_support_result",
                "validation_result",
                "write_execution",
                "final_gate_satisfaction",
                "claim_trust_update",
                "trust_apply",
            ],
        },
        "read_surface_effect": "literature_source_set_readiness_only",
        "read_only": True,
        "draft_creates_records": False,
        "requires_explicit_next_action": True,
        "bridge_called": False,
        "executes_write_now": False,
        "mutates_next_payload_now": False,
        "infers_payload_values": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
        "truth_source": "typed_records_and_agent_supplied_source_refs",
    }


def _record_index(ws) -> dict[str, list[Any]]:
    return {
        "source_assets": list_records(ws.registry_dir("source_assets"), SourceAssetRecord),
        "reference_locations": list_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        "physics_objects": list_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord),
        "object_relations": list_records(ws.registry_dir("object_relations"), ObjectRelationRecord),
        "proof_obligations": list_records(ws.registry_dir("proof_obligations"), ProofObligationRecord),
        "sensemaking_reports": list_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord),
        "source_reviews": list_records(
            ws.registry_dir("source_reconstruction_reviews"),
            SourceReconstructionReviewResultRecord,
        ),
    }


def _source_item(
    source_ref: str,
    *,
    topic_id: str,
    claim_id: str,
    records: dict[str, list[Any]],
) -> dict[str, Any]:
    parsed = _parse_ref(source_ref)
    source_asset = _source_asset_for_ref(source_ref, parsed, records["source_assets"], records["reference_locations"])
    reference_locations = _reference_locations_for_ref(
        source_ref,
        parsed,
        source_asset,
        records["reference_locations"],
    )
    extraction_trace = _extraction_trace_for_ref(
        source_ref,
        source_asset,
        reference_locations,
        records,
    )
    reconstruction_review = _reconstruction_review_for_ref(
        source_ref,
        source_asset,
        reference_locations,
        extraction_trace,
        records["source_reviews"],
    )
    components = {
        "source_asset": _component(
            "source_asset",
            present=source_asset is not None,
            refs=[f"source_asset:{source_asset.asset_id}"] if source_asset else [],
            next_entrypoint="register_source_asset",
            surface="source_asset_record",
            reason="canonical source identity is required before source-set synthesis",
        ),
        "reference_location": _component(
            "reference_location",
            present=bool(reference_locations),
            refs=[f"reference_location:{item.location_id}" for item in reference_locations],
            next_entrypoint="record_reference_location",
            surface="reference_location_record",
            reason="exact anchors are required before quoting, extraction, or synthesis",
        ),
        "extraction_trace": _component(
            "extraction_trace",
            present=extraction_trace["present"],
            refs=extraction_trace["refs"],
            next_entrypoint="build_literature_source_extraction_candidates",
            surface="literature_source_extraction_candidates",
            reason="typed extracted objects, relations, gaps, or an orientation report are required before synthesis",
        ),
        "source_reconstruction_review": _component(
            "source_reconstruction_review",
            present=reconstruction_review["present"],
            refs=reconstruction_review["refs"],
            next_entrypoint="record_source_reconstruction_review_result",
            surface="source_reconstruction_review_result_record",
            reason="source reconstruction review is required before claim-sensitive use",
            status=reconstruction_review["status"],
        ),
    }
    missing = [name for name, component in components.items() if not component["present"]]
    return {
        "source_ref": source_ref,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "parsed_ref_kind": parsed[0] if parsed else "",
        "parsed_record_id": parsed[1] if parsed else "",
        "components": components,
        "missing_components": missing,
        "readiness_status": "ready_for_synthesis_review" if not missing else "blocked_missing_components",
        "recommended_next_entrypoints": _recommended_next_entrypoints(missing),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _source_asset_for_ref(
    source_ref: str,
    parsed: tuple[str, str] | None,
    source_assets: list[SourceAssetRecord],
    reference_locations: list[ReferenceLocationRecord],
) -> SourceAssetRecord | None:
    by_id = {asset.asset_id: asset for asset in source_assets}
    if parsed and parsed[0] == "source_asset":
        return by_id.get(parsed[1])
    if parsed and parsed[0] == "reference_location":
        location = next((item for item in reference_locations if item.location_id == parsed[1]), None)
        if location and location.source_ref.startswith("source_asset:"):
            return by_id.get(location.source_ref.split(":", 1)[1])
    for asset in source_assets:
        if source_ref in {f"source_asset:{asset.asset_id}", asset.uri, asset.external_id if hasattr(asset, "external_id") else ""}:
            return asset
    return None


def _reference_locations_for_ref(
    source_ref: str,
    parsed: tuple[str, str] | None,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
) -> list[ReferenceLocationRecord]:
    matches: list[ReferenceLocationRecord] = []
    if parsed and parsed[0] == "reference_location":
        matches.extend(item for item in reference_locations if item.location_id == parsed[1])
    if source_asset is not None:
        asset_ref = f"source_asset:{source_asset.asset_id}"
        matches.extend(item for item in reference_locations if item.source_ref == asset_ref)
        matches.extend(item for item in reference_locations if item.location_id in source_asset.reference_location_ids)
    matches.extend(item for item in reference_locations if item.source_ref == source_ref)
    return _unique_by(matches, "location_id")


def _extraction_trace_for_ref(
    source_ref: str,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
    records: dict[str, list[Any]],
) -> dict[str, Any]:
    candidate_refs = _candidate_source_refs(source_ref, source_asset, reference_locations)
    objects = [
        record for record in records["physics_objects"]
        if _intersects(record.source_refs, candidate_refs)
    ]
    object_ids = {record.object_id for record in objects}
    relations = [
        record for record in records["object_relations"]
        if _intersects(record.source_refs, candidate_refs)
    ]
    relation_ids = {record.relation_id for record in relations}
    obligations = [
        record for record in records["proof_obligations"]
        if _intersects(record.source_refs, candidate_refs)
    ]
    reports = [
        record for record in records["sensemaking_reports"]
        if object_ids.intersection(record.object_ids) or relation_ids.intersection(record.relation_ids)
    ]
    refs = (
        [f"physics_object:{record.object_id}" for record in objects]
        + [f"object_relation:{record.relation_id}" for record in relations]
        + [f"proof_obligation:{record.obligation_id}" for record in obligations]
        + [f"sensemaking_report:{record.report_id}" for record in reports]
    )
    return {"present": bool(refs), "refs": refs}


def _reconstruction_review_for_ref(
    source_ref: str,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
    extraction_trace: dict[str, Any],
    reviews: list[SourceReconstructionReviewResultRecord],
) -> dict[str, Any]:
    candidate_refs = set(_candidate_source_refs(source_ref, source_asset, reference_locations))
    candidate_refs.update(extraction_trace["refs"])
    location_ids = {location.location_id for location in reference_locations}
    source_reviews = []
    for review in reviews:
        review_refs = set(review.basis_refs)
        review_refs.update(f"reference_location:{item}" for item in review.reference_location_ids)
        if review_refs.intersection(candidate_refs) or location_ids.intersection(review.reference_location_ids):
            source_reviews.append(review)
    refs = [f"source_reconstruction_review:{review.result_id}" for review in source_reviews]
    ready = any(str(review.status).lower() in _READY_STATUSES for review in source_reviews)
    return {
        "present": ready,
        "refs": refs,
        "status": "ready_review_present" if ready else ("review_present_but_not_ready" if refs else "missing"),
    }


def _component(
    component: str,
    *,
    present: bool,
    refs: list[str],
    next_entrypoint: str,
    surface: str,
    reason: str,
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "component": component,
        "status": status or ("present" if present else "missing"),
        "present": bool(present),
        "refs": list(refs),
        "recommended_next_entrypoint": "" if present else next_entrypoint,
        "recommended_next_surface": "" if present else surface,
        "recommended_next_reason": "" if present else reason,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _component_counts(source_items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for name in _REQUIRED_COMPONENTS:
        components = [item["components"][name] for item in source_items]
        counts[name] = {
            "present_count": sum(1 for component in components if component["present"]),
            "missing_count": sum(1 for component in components if not component["present"]),
        }
    return counts


def _recommended_next_entrypoints(missing_components: list[str]) -> list[dict[str, str]]:
    mapping = {
        "source_asset": (
            "register_source_asset",
            "source_asset_record",
            "record canonical source identity before source-set synthesis",
        ),
        "reference_location": (
            "record_reference_location",
            "reference_location_record",
            "record exact source anchors before synthesis",
        ),
        "extraction_trace": (
            "build_literature_source_extraction_candidates",
            "literature_source_extraction_candidates",
            "plan and write typed extraction traces before synthesis",
        ),
        "source_reconstruction_review": (
            "record_source_reconstruction_review_result",
            "source_reconstruction_review_result_record",
            "review source reconstruction before claim-sensitive use",
        ),
    }
    return [
        {"entrypoint": entrypoint, "surface": surface, "reason": reason}
        for component in missing_components
        for entrypoint, surface, reason in [mapping[component]]
    ]


def _candidate_source_refs(
    source_ref: str,
    source_asset: SourceAssetRecord | None,
    reference_locations: list[ReferenceLocationRecord],
) -> list[str]:
    refs = [source_ref]
    if source_asset is not None:
        refs.append(f"source_asset:{source_asset.asset_id}")
        refs.append(source_asset.uri)
    refs.extend(f"reference_location:{location.location_id}" for location in reference_locations)
    refs.extend(location.source_ref for location in reference_locations if location.source_ref)
    return _nonempty_unique(refs)


def _parse_ref(ref: str) -> tuple[str, str] | None:
    parts = [part.strip() for part in ref.split(":")]
    if len(parts) == 3 and parts[0] == "aitp":
        _, kind, record_id = parts
    elif len(parts) == 2:
        kind, record_id = parts
    else:
        return None
    if not kind or not record_id:
        return None
    return kind.replace("-", "_"), record_id


def _intersects(values: list[str], candidates: list[str]) -> bool:
    return bool(set(values).intersection(candidates))


def _unique_by(values: list[Any], attr: str) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for value in values:
        key = str(getattr(value, attr))
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def _nonempty_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
