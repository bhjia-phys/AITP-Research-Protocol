"""Read-only profile-specific literature extraction reports."""

from __future__ import annotations

from typing import Any

from brain.v5.models import (
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    SensemakingReportRecord,
    SourceAssetRecord,
)
from brain.v5.record_refs import lookup_record_refs
from brain.v5.store import list_valid_records
from brain.v5.workspace import get_session_binding


_PROFILE_SPECS: dict[str, dict[str, Any]] = {
    "paper_learning": {
        "label": "single paper learning extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical paper or note identity"),
            ("exact_anchors", ["reference_location"], "list exact source anchors used by typed extraction"),
            ("core_definitions", ["physics_object"], "summarize extracted definitions, objects, and notation"),
            ("source_relations", ["object_relation"], "summarize source-backed relations between typed objects"),
            ("open_gaps", ["proof_obligation"], "surface derivation, source, or validation gaps"),
            ("orientation_report", ["sensemaking_report"], "connect extraction outputs in an orientation-only report"),
        ],
    },
    "paired_paper_learning": {
        "label": "paired paper learning extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical identity for both sources"),
            ("exact_anchors", ["reference_location"], "list exact source anchors before comparison"),
            ("core_definitions", ["physics_object"], "summarize comparable extracted definitions"),
            ("source_relations", ["object_relation"], "summarize relations and convention dependencies"),
            ("convention_or_scope_gaps", ["proof_obligation"], "surface gaps that block comparison"),
            ("comparison_ready_orientation", ["sensemaking_report"], "summarize extraction readiness for comparison"),
        ],
    },
    "multi_paper_learning_route": {
        "label": "multi-paper learning extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical identity for each source"),
            ("exact_anchors", ["reference_location"], "list exact source anchors before synthesis"),
            ("object_index", ["physics_object"], "summarize the extracted object index"),
            ("relation_index", ["object_relation"], "summarize source-backed relation index"),
            ("open_gaps", ["proof_obligation"], "surface gaps that block multi-source synthesis"),
            ("orientation_report", ["sensemaking_report"], "summarize extraction status without support claims"),
        ],
    },
    "qft_literature": {
        "label": "QFT literature extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical QFT source identity"),
            ("equation_and_section_anchors", ["reference_location"], "list exact equation or section anchors"),
            ("fields_operators_conventions", ["physics_object"], "summarize fields, operators, schemes, and conventions"),
            ("scheme_and_limit_relations", ["object_relation"], "summarize source-backed scheme, limit, or duality relations"),
            ("renormalization_or_scope_gaps", ["proof_obligation"], "surface assumptions and derivation gaps"),
            ("orientation_report", ["sensemaking_report"], "summarize QFT extraction boundaries"),
        ],
    },
    "quantum_gravity_literature": {
        "label": "quantum-gravity literature extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical quantum-gravity source identity"),
            ("equation_and_section_anchors", ["reference_location"], "list exact equation, section, or caveat anchors"),
            ("bulk_boundary_objects", ["physics_object"], "summarize geometries, states, algebras, and boundary data"),
            ("map_and_limit_relations", ["object_relation"], "summarize bulk-boundary, ensemble, or limit relations"),
            ("semiclassical_or_scope_gaps", ["proof_obligation"], "surface gaps around limits and interpretation"),
            ("orientation_report", ["sensemaking_report"], "summarize QG extraction boundaries"),
        ],
    },
    "gw_librpa_literature": {
        "label": "GW/LibRPA literature and notes extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical LibRPA source, note, or paper identity"),
            ("exact_anchors", ["reference_location"], "list exact anchors for method or run interpretation"),
            ("method_and_parameter_objects", ["physics_object"], "summarize methods, parameters, observables, and run states"),
            ("workflow_and_failure_relations", ["object_relation"], "summarize workflow and failure-mode relations"),
            ("validation_or_run_gaps", ["proof_obligation"], "surface validation, run, or final-lane gaps"),
            ("orientation_report", ["sensemaking_report"], "summarize extraction status without final-lane claims"),
        ],
    },
    "generic_literature_report": {
        "label": "generic literature extraction report",
        "sections": [
            ("source_identity", ["source_asset"], "confirm canonical source identity"),
            ("exact_anchors", ["reference_location"], "list exact source anchors"),
            ("typed_objects", ["physics_object"], "summarize extracted typed objects"),
            ("typed_relations", ["object_relation"], "summarize extracted typed relations"),
            ("open_gaps", ["proof_obligation"], "surface open proof or source obligations"),
            ("orientation_report", ["sensemaking_report"], "summarize extraction status as orientation only"),
        ],
    },
}

_PROFILE_ALIASES = {
    "single": "paper_learning",
    "single_paper": "paper_learning",
    "paper": "paper_learning",
    "paper_learning": "paper_learning",
    "paired": "paired_paper_learning",
    "paired_paper": "paired_paper_learning",
    "paired_paper_learning": "paired_paper_learning",
    "multi": "multi_paper_learning_route",
    "multi_paper": "multi_paper_learning_route",
    "multi_paper_learning": "multi_paper_learning_route",
    "multi_paper_learning_route": "multi_paper_learning_route",
    "qft": "qft_literature",
    "qft_literature": "qft_literature",
    "quantum_gravity": "quantum_gravity_literature",
    "quantum_gravity_literature": "quantum_gravity_literature",
    "qg": "quantum_gravity_literature",
    "librpa": "gw_librpa_literature",
    "gw_librpa": "gw_librpa_literature",
    "gw_librpa_literature": "gw_librpa_literature",
    "generic": "generic_literature_report",
    "generic_literature_report": "generic_literature_report",
}

_FORBIDDEN_USES = [
    "paper_summary_as_evidence",
    "extraction_report_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
]


def build_literature_extraction_report(
    ws,
    *,
    session_id: str,
    source_refs: list[str],
    report_profile: str = "paper_learning",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
) -> dict[str, Any]:
    """Compile profile-specific extraction status from existing typed records."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_refs = _nonempty_unique(source_refs)
    if not normalized_refs:
        raise ValueError("source_refs is required")
    normalized_focus_terms = _nonempty_unique(focus_terms or [])
    profile_id = _normalize_profile(report_profile)
    profile_spec = _PROFILE_SPECS[profile_id]
    records = _record_index(ws)
    source_reports = [
        _source_report(
            source_ref,
            topic_id=session.topic_id,
            claim_id=claim_id,
            profile_id=profile_id,
            profile_spec=profile_spec,
            records=records,
        )
        for source_ref in normalized_refs
    ]
    aggregate_counts = _aggregate_counts(source_reports)
    covered_source_count = sum(1 for item in source_reports if item["coverage_status"] == "profile_ready")
    missing_section_ids = sorted(
        {
            section
            for item in source_reports
            for section in item["missing_section_ids"]
        }
    )
    return {
        "ok": True,
        "kind": "literature_extraction_report",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "requested_report_profile": report_profile,
        "report_profile": profile_id,
        "report_profile_label": profile_spec["label"],
        "source_refs": normalized_refs,
        "source_ref_count": len(normalized_refs),
        "focus_terms": normalized_focus_terms,
        "focus_term_count": len(normalized_focus_terms),
        "profile_sections": _profile_sections(profile_spec),
        "profile_section_count": len(profile_spec["sections"]),
        "source_reports": source_reports,
        "source_report_count": len(source_reports),
        "covered_source_count": covered_source_count,
        "blocked_source_count": len(source_reports) - covered_source_count,
        "missing_section_ids": missing_section_ids,
        "aggregate_counts": aggregate_counts,
        "record_ref_lookup": lookup_record_refs(ws, normalized_refs),
        "recommended_next_entrypoints": _recommended_next_entrypoints(missing_section_ids),
        "report_policy": {
            "source": "typed_records_and_agent_supplied_source_refs",
            "host_may_use_for": [
                "profile_specific_literature_extraction_report",
                "paper_learning_progress_audit",
                "typed_extraction_status_summary",
                "next_entrypoint_selection",
            ],
            "requires_existing_typed_records": True,
            "requires_explicit_next_entrypoint": True,
            "allowed_next_entrypoints": [
                "register_source_asset",
                "record_reference_location",
                "record_physics_object",
                "record_object_relation",
                "create_proof_obligation",
                "record_sensemaking_report",
                "build_literature_source_set_readiness",
                "build_literature_comparison_draft",
                "preflight_trust_update",
            ],
            "forbidden_uses": list(_FORBIDDEN_USES),
        },
        "read_surface_effect": "literature_extraction_report_only",
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
        "source_assets": list_valid_records(ws.registry_dir("source_assets"), SourceAssetRecord),
        "reference_locations": list_valid_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord),
        "physics_objects": list_valid_records(ws.registry_dir("physics_objects"), PhysicsObjectRecord),
        "object_relations": list_valid_records(ws.registry_dir("object_relations"), ObjectRelationRecord),
        "proof_obligations": list_valid_records(ws.registry_dir("proof_obligations"), ProofObligationRecord),
        "sensemaking_reports": list_valid_records(ws.registry_dir("sensemaking_reports"), SensemakingReportRecord),
    }


def _source_report(
    source_ref: str,
    *,
    topic_id: str,
    claim_id: str,
    profile_id: str,
    profile_spec: dict[str, Any],
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
    candidate_refs = _candidate_source_refs(source_ref, source_asset, reference_locations)
    objects = [
        record for record in records["physics_objects"]
        if record.topic_id == topic_id and _intersects(record.source_refs, candidate_refs)
    ]
    object_ids = {record.object_id for record in objects}
    relations = [
        record for record in records["object_relations"]
        if record.topic_id == topic_id
        and (
            _intersects(record.source_refs, candidate_refs)
            or record.subject_id in object_ids
            or record.object_id in object_ids
        )
    ]
    relation_ids = {record.relation_id for record in relations}
    obligations = [
        record for record in records["proof_obligations"]
        if record.topic_id == topic_id
        and (not claim_id or record.claim_id == claim_id)
        and _intersects(record.source_refs, candidate_refs)
    ]
    reports = [
        record for record in records["sensemaking_reports"]
        if record.topic_id == topic_id
        and (not claim_id or record.claim_id == claim_id)
        and (object_ids.intersection(record.object_ids) or relation_ids.intersection(record.relation_ids))
    ]
    section_context = {
        "source_asset": [f"source_asset:{source_asset.asset_id}"] if source_asset else [],
        "reference_location": [f"reference_location:{item.location_id}" for item in reference_locations],
        "physics_object": [f"physics_object:{item.object_id}" for item in objects],
        "object_relation": [f"object_relation:{item.relation_id}" for item in relations],
        "proof_obligation": [f"proof_obligation:{item.obligation_id}" for item in obligations],
        "sensemaking_report": [f"sensemaking_report:{item.report_id}" for item in reports],
    }
    sections = [
        _section_report(section_id, target_records, purpose, section_context)
        for section_id, target_records, purpose in profile_spec["sections"]
    ]
    missing_section_ids = [
        section["section_id"]
        for section in sections
        if section["coverage_status"] == "missing_typed_records"
    ]
    return {
        "source_ref": source_ref,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "report_profile": profile_id,
        "parsed_ref_kind": parsed[0] if parsed else "",
        "parsed_record_id": parsed[1] if parsed else "",
        "source_identity_refs": section_context["source_asset"],
        "reference_location_refs": section_context["reference_location"],
        "extracted_object_refs": section_context["physics_object"],
        "extracted_relation_refs": section_context["object_relation"],
        "proof_obligation_refs": section_context["proof_obligation"],
        "sensemaking_report_refs": section_context["sensemaking_report"],
        "extracted_objects": [_object_summary(item) for item in objects],
        "extracted_relations": [_relation_summary(item) for item in relations],
        "proof_obligations": [_obligation_summary(item) for item in obligations],
        "sensemaking_reports": [_sensemaking_summary(item) for item in reports],
        "sections": sections,
        "section_count": len(sections),
        "missing_section_ids": missing_section_ids,
        "coverage_status": "profile_ready" if not missing_section_ids else "missing_typed_records",
        "recommended_next_entrypoints": _recommended_next_entrypoints(missing_section_ids),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _section_report(
    section_id: str,
    target_records: list[str],
    purpose: str,
    section_context: dict[str, list[str]],
) -> dict[str, Any]:
    item_refs = _nonempty_unique([
        ref
        for target in target_records
        for ref in section_context.get(target, [])
    ])
    missing_record_kinds = [target for target in target_records if not section_context.get(target)]
    return {
        "section_id": section_id,
        "purpose": purpose,
        "target_records": list(target_records),
        "item_refs": item_refs,
        "item_count": len(item_refs),
        "missing_record_kinds": missing_record_kinds,
        "coverage_status": "covered" if not missing_record_kinds else "missing_typed_records",
        "recommended_next_entrypoint": _next_entrypoint_for_missing(missing_record_kinds),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _profile_sections(profile_spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "section_id": section_id,
            "target_records": list(target_records),
            "purpose": purpose,
            "requires_existing_typed_records": True,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        }
        for section_id, target_records, purpose in profile_spec["sections"]
    ]


def _object_summary(record: PhysicsObjectRecord) -> dict[str, Any]:
    return {
        "record_ref": f"physics_object:{record.object_id}",
        "object_id": record.object_id,
        "object_type": record.object_type,
        "name": record.name,
        "notation": record.notation,
        "definition": record.definition,
        "assumptions": list(record.assumptions),
        "source_refs": list(record.source_refs),
        "status": record.status,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _relation_summary(record: ObjectRelationRecord) -> dict[str, Any]:
    return {
        "record_ref": f"object_relation:{record.relation_id}",
        "relation_id": record.relation_id,
        "relation_type": record.relation_type,
        "subject_id": record.subject_id,
        "object_id": record.object_id,
        "statement": record.statement,
        "assumptions": list(record.assumptions),
        "failure_modes": list(record.failure_modes),
        "source_refs": list(record.source_refs),
        "status": record.status,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _obligation_summary(record: ProofObligationRecord) -> dict[str, Any]:
    return {
        "record_ref": f"proof_obligation:{record.obligation_id}",
        "obligation_id": record.obligation_id,
        "statement": record.statement,
        "obligation_type": record.obligation_type,
        "status": record.status,
        "maturity_level": record.maturity_level,
        "next_action": record.next_action,
        "source_refs": list(record.source_refs),
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _sensemaking_summary(record: SensemakingReportRecord) -> dict[str, Any]:
    return {
        "record_ref": f"sensemaking_report:{record.report_id}",
        "report_id": record.report_id,
        "title": record.title,
        "summary": record.summary,
        "object_ids": list(record.object_ids),
        "relation_ids": list(record.relation_ids),
        "open_questions": list(record.open_questions),
        "next_actions": list(record.next_actions),
        "validation_status": record.validation_status,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _aggregate_counts(source_reports: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "source_asset_count": _unique_count(source_reports, "source_identity_refs"),
        "reference_location_count": _unique_count(source_reports, "reference_location_refs"),
        "physics_object_count": _unique_count(source_reports, "extracted_object_refs"),
        "object_relation_count": _unique_count(source_reports, "extracted_relation_refs"),
        "proof_obligation_count": _unique_count(source_reports, "proof_obligation_refs"),
        "sensemaking_report_count": _unique_count(source_reports, "sensemaking_report_refs"),
    }


def _unique_count(source_reports: list[dict[str, Any]], key: str) -> int:
    return len({ref for report in source_reports for ref in report.get(key, [])})


def _recommended_next_entrypoints(missing_section_ids: list[str]) -> list[dict[str, str]]:
    record_kinds = _missing_record_kinds_for_sections(missing_section_ids)
    return [
        {
            "entrypoint": _ENTRYPOINT_BY_RECORD_KIND[record_kind][0],
            "surface": _ENTRYPOINT_BY_RECORD_KIND[record_kind][1],
            "reason": _ENTRYPOINT_BY_RECORD_KIND[record_kind][2],
        }
        for record_kind in record_kinds
    ]


def _missing_record_kinds_for_sections(missing_section_ids: list[str]) -> list[str]:
    result: list[str] = []
    for section_id in missing_section_ids:
        if "source_identity" == section_id:
            result.append("source_asset")
        elif "anchor" in section_id:
            result.append("reference_location")
        elif any(token in section_id for token in ("object", "definition", "operator", "field", "method", "parameter")):
            result.append("physics_object")
        elif any(token in section_id for token in ("relation", "workflow", "map", "scheme", "limit")):
            result.append("object_relation")
        elif "gap" in section_id:
            result.append("proof_obligation")
        elif "report" in section_id or "orientation" in section_id:
            result.append("sensemaking_report")
    return _nonempty_unique(result)


_ENTRYPOINT_BY_RECORD_KIND = {
    "source_asset": (
        "register_source_asset",
        "source_asset_record",
        "record canonical source identity",
    ),
    "reference_location": (
        "record_reference_location",
        "reference_location_record",
        "record exact source anchors",
    ),
    "physics_object": (
        "record_physics_object",
        "physics_object_record",
        "write source-backed definitions, objects, notation, or conventions",
    ),
    "object_relation": (
        "record_object_relation",
        "object_relation_record",
        "write source-backed relations after object endpoints exist",
    ),
    "proof_obligation": (
        "create_proof_obligation",
        "proof_obligation_record",
        "preserve source, derivation, or validation gaps",
    ),
    "sensemaking_report": (
        "record_sensemaking_report",
        "sensemaking_report_record",
        "summarize extraction status as orientation only",
    ),
}


def _next_entrypoint_for_missing(missing_record_kinds: list[str]) -> str:
    if not missing_record_kinds:
        return ""
    record_kind = missing_record_kinds[0]
    return _ENTRYPOINT_BY_RECORD_KIND.get(record_kind, ("", "", ""))[0]


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
        candidate_values = {f"source_asset:{asset.asset_id}", asset.uri}
        if source_ref in candidate_values:
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


def _normalize_profile(value: str) -> str:
    normalized = str(value or "paper_learning").strip().lower().replace("-", "_")
    return _PROFILE_ALIASES.get(normalized, "generic_literature_report")


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
