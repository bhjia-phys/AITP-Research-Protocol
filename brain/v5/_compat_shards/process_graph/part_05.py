# Compatibility shard 5 for process_graph.
from __future__ import annotations

def _source_backtrace(
    claims: list[ClaimRecord],
    references: list[ReferenceLocationRecord],
    source_assets: list[SourceAssetRecord],
    evidence: list[EvidenceRecord],
    obligations: list[ProofObligationRecord],
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
    exploratory_records: list[ExploratoryRecord],
) -> list[dict[str, Any]]:
    by_claim = {claim.claim_id: claim for claim in claims}
    result = []
    for claim_id, claim in by_claim.items():
        claim_refs = [record.location_id for record in references if record.claim_id == claim_id]
        claim_assets = [
            record.asset_id
            for record in source_assets
            if record.claim_id == claim_id or _mapping_links_any(record.linked_records, {claim_id})
        ]
        claim_evidence = [record.evidence_id for record in evidence if record.claim_id == claim_id]
        claim_obligations = [record.obligation_id for record in obligations if record.claim_id == claim_id]
        claim_relations = [record.relation_id for record in relations if record.claim_id == claim_id]
        claim_backtrace_records = [
            record
            for record in exploratory_records
            if record.claim_id == claim_id and record.exploration_type in {"backtrace_step", "source_asset"}
        ]
        missing = []
        if not claim_refs:
            missing.append("reference_location")
        if not claim_evidence:
            missing.append("evidence")
        if not claim_obligations:
            missing.append("proof_obligation")
        if not objects:
            missing.append("physics_object")
        if not claim_relations:
            missing.append("object_relation")
        result.append(
            {
                "topic_id": claim.topic_id,
                "claim_id": claim_id,
                "statement": claim.statement,
                "reference_location_ids": claim_refs,
                "source_asset_ids": claim_assets,
                "evidence_ids": claim_evidence,
                "proof_obligation_ids": claim_obligations,
                "object_relation_ids": claim_relations,
                "physics_object_ids": [record.object_id for record in objects],
                "exploratory_record_ids": [record.record_id for record in claim_backtrace_records],
                "reasoning_moves": _record_values(claim_backtrace_records, "reasoning_moves"),
                "backtrace_targets": _record_values(claim_backtrace_records, "backtrace_targets"),
                "definition_boundary_questions": _record_values(
                    claim_backtrace_records,
                    "definition_boundary_questions",
                ),
                "derivation_backtrace_questions": _record_values(
                    claim_backtrace_records,
                    "derivation_backtrace_questions",
                ),
                "source_dependency_questions": _record_values(
                    claim_backtrace_records,
                    "source_dependency_questions",
                ),
                "original_question_guard": _record_values(claim_backtrace_records, "original_question_guard"),
                "missing_components": missing,
                "complete": not missing,
            }
        )
    return result

def _source_asset_index(
    source_assets: list[SourceAssetRecord],
    references: list[ReferenceLocationRecord],
    provenance_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    references_by_id = {record.location_id: record for record in references}
    hashed_derivatives_by_parent = _hashed_source_asset_derivatives_by_parent(source_assets)
    result: list[dict[str, Any]] = []
    for record in source_assets:
        duplicate = record.metadata.get("duplicate_hash_diagnostics", {})
        if not isinstance(duplicate, dict):
            duplicate = {}
        target_ref = f"source_asset:{record.asset_id}"
        asset_gaps = [
            gap
            for gap in provenance_gaps
            if gap.get("target_type") == "source_asset"
            and (
                gap.get("target_id") == record.asset_id
                or target_ref in list(gap.get("target_refs") or [])
            )
        ]
        reference_items = [
            {
                "reference_location_id": reference.location_id,
                "uri": reference.uri,
                "label": reference.label,
                "connector_id": reference.connector_id,
                "location_type": reference.location_type,
                "status": reference.status,
            }
            for reference_id in record.reference_location_ids
            for reference in [references_by_id.get(reference_id)]
            if reference is not None
        ]
        hash_status = "present" if record.content_hash else "missing"
        hash_resolution_refs = []
        if not record.content_hash and record.asset_id in hashed_derivatives_by_parent:
            hash_status = "resolved_by_derived_asset"
            hash_resolution_refs = [
                f"source_asset:{asset.asset_id}"
                for asset in hashed_derivatives_by_parent[record.asset_id]
            ]
        if duplicate.get("duplicate_hash"):
            hash_status = "duplicate"
        result.append(
            {
                "asset_id": record.asset_id,
                "topic_id": record.topic_id,
                "claim_id": record.claim_id,
                "asset_type": record.asset_type,
                "uri": record.uri,
                "title": record.title,
                "label": record.label,
                "summary": record.summary,
                "source_kind": record.source_kind,
                "content_hash": record.content_hash,
                "hash_algorithm": record.hash_algorithm,
                "hash_status": hash_status,
                "hash_resolution_refs": hash_resolution_refs,
                "version_anchor": dict(record.version_anchor),
                "acquired_at": record.acquired_at,
                "source_refs": list(record.source_refs),
                "artifact_ids": list(record.artifact_ids),
                "code_state_ids": list(record.code_state_ids),
                "reference_location_ids": list(record.reference_location_ids),
                "reference_locations": reference_items,
                "derived_from": list(record.derived_from),
                "linked_records": dict(record.linked_records),
                "metadata": dict(record.metadata),
                "duplicate_hash_diagnostics": dict(duplicate),
                "provenance_gap_ids": [str(gap.get("gap_id") or gap.get("id") or "") for gap in asset_gaps if gap.get("gap_id") or gap.get("id")],
                "provenance_gap_types": [str(gap.get("gap_type") or "") for gap in asset_gaps if gap.get("gap_type")],
                "target_refs": [target_ref, record.uri, *record.source_refs],
                "orientation_only": record.orientation_only,
                "can_update_claim_trust": record.can_update_claim_trust,
            }
        )
    return result

def _hashed_source_asset_derivatives_by_parent(
    source_assets: list[SourceAssetRecord],
) -> dict[str, list[SourceAssetRecord]]:
    by_parent: dict[str, list[SourceAssetRecord]] = {}
    asset_ids = {record.asset_id for record in source_assets}
    for record in source_assets:
        if not record.content_hash:
            continue
        for parent in record.derived_from:
            parent_id = _normalize_source_asset_ref(parent)
            if parent_id in asset_ids:
                by_parent.setdefault(parent_id, []).append(record)
    return by_parent

def _normalize_source_asset_ref(value: str) -> str:
    text = str(value or "").strip()
    if text.startswith("source_asset:"):
        return text.split(":", 1)[1]
    return text

def _relation_neighborhood(
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
    exploratory_records: list[ExploratoryRecord],
) -> list[dict[str, Any]]:
    object_names = {record.object_id: record.name for record in objects}
    result = []
    for record in relations:
        relation_explorations = [
            item
            for item in exploratory_records
            if item.exploration_type == "relation_path_brainstorm" and record.relation_id in item.relation_ids
        ]
        result.append(
            {
            "topic_id": record.topic_id,
            "relation_id": record.relation_id,
            "claim_id": record.claim_id,
            "status": record.status,
            "relation_type": record.relation_type,
            "subject_id": record.subject_id,
            "subject_name": object_names.get(record.subject_id, ""),
            "object_id": record.object_id,
            "object_name": object_names.get(record.object_id, ""),
            "failure_modes": list(record.failure_modes),
            "exploratory_record_ids": [item.record_id for item in relation_explorations],
            "reasoning_moves": _record_values(relation_explorations, "reasoning_moves"),
            "candidate_paths": _record_values(relation_explorations, "candidate_paths"),
            "relation_path_questions": _record_values(relation_explorations, "relation_path_questions"),
            "definition_boundary_questions": _record_values(
                relation_explorations,
                "definition_boundary_questions",
            ),
            "original_question_guard": _record_values(relation_explorations, "original_question_guard"),
        }
        )
    return result

def _exploratory_slice(record: ExploratoryRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "exploration_type": record.exploration_type,
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "session_id": record.session_id,
        "title": record.title,
        "focal_question": record.focal_question,
        "original_question": record.original_question,
        "local_question": record.local_question,
        "status": record.status,
        "object_ids": list(record.object_ids),
        "relation_ids": list(record.relation_ids),
        "source_refs": list(record.source_refs),
        "reasoning_moves": list(record.reasoning_moves),
        "backtrace_targets": list(record.backtrace_targets),
        "candidate_paths": list(record.candidate_paths),
        "relation_path_questions": list(record.relation_path_questions),
        "definition_boundary_questions": list(record.definition_boundary_questions),
        "derivation_backtrace_questions": list(record.derivation_backtrace_questions),
        "source_dependency_questions": list(record.source_dependency_questions),
        "original_question_guard": list(record.original_question_guard),
        "unresolved_points": list(record.unresolved_points),
        "next_actions": list(record.next_actions),
    }

def _route_state(session: SessionBinding, routes: list[ResearchRouteRecord]) -> dict[str, Any]:
    route_slices = [_route_slice(record, active=record.route_id == session.active_route) for record in routes]
    return {
        "active_route_id": session.active_route,
        "routes": route_slices,
        "live_route_ids": [record.route_id for record in routes if record.status in {"live", "selected"}],
        "blocked_route_ids": [record.route_id for record in routes if record.status == "blocked"],
        "abandoned_route_ids": [record.route_id for record in routes if record.status == "abandoned"],
        "pivot_required_route_ids": [
            record.route_id
            for record in routes
            if record.parent_route_ids or record.pivot_reason or record.checkpoint_ids
        ],
        "orientation_only": True,
        "can_update_claim_trust": False,
    }

def _route_slice(record: ResearchRouteRecord, *, active: bool) -> dict[str, Any]:
    return {
        "route_id": record.route_id,
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "session_id": record.session_id,
        "title": record.title,
        "route_type": record.route_type,
        "status": record.status,
        "active": active,
        "rationale": record.rationale,
        "current_question": record.current_question,
        "next_action": record.next_action,
        "failure_modes": list(record.failure_modes),
        "source_refs": list(record.source_refs),
        "evidence_refs": list(record.evidence_refs),
        "artifact_ids": list(record.artifact_ids),
        "parent_route_ids": list(record.parent_route_ids),
        "checkpoint_ids": list(record.checkpoint_ids),
        "exploratory_record_ids": list(record.exploratory_record_ids),
        "object_ids": list(record.object_ids),
        "relation_ids": list(record.relation_ids),
        "decision_rationale": record.decision_rationale,
        "pivot_reason": record.pivot_reason,
        "orientation_only": record.orientation_only,
        "can_update_claim_trust": record.can_update_claim_trust,
    }

def _record_values(records: list[ExploratoryRecord], field_name: str) -> list[str]:
    values: list[str] = []
    for record in records:
        for value in getattr(record, field_name, []):
            text = str(value)
            if text and text not in values:
                values.append(text)
    return values

def _recommended_moments(
    open_obligations: list[dict[str, Any]],
    source_backtrace: list[dict[str, Any]],
    relations: list[ObjectRelationRecord],
    exploratory_records: list[ExploratoryRecord],
    route_state: dict[str, Any],
    provenance_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    moments: list[dict[str, Any]] = []
    for obligation in open_obligations:
        moments.append(
            _moment(
                "record_or_validate_open_obligation",
                reason="open proof obligation requires typed evidence or validation",
                target_type="proof_obligation",
                target_id=obligation["obligation_id"],
                priority=obligation.get("severity", "recommended"),
                timing="before_final_or_promotion",
                trust_boundary=obligation.get("trust_boundary", "before_final_or_promotion"),
            )
        )
    for item in source_backtrace:
        if item["missing_components"]:
            moments.append(
                _moment(
                    "backtrace_source_reconstruction",
                    reason="missing source reconstruction components",
                    target_type="claim",
                    target_id=item["claim_id"],
                    priority="high",
                    timing="before_using_as_support",
                    trust_boundary="source_support",
                    missing_components=list(item["missing_components"]),
                )
            )
    for relation in relations:
        if relation.status.strip().lower() == "hypothesis":
            moments.append(
                _moment(
                    "brainstorm_relation_path",
                    reason="object relation is still a hypothesis",
                    target_type="object_relation",
                    target_id=relation.relation_id,
                    priority="high",
                    timing="before_using_relation_as_claim",
                    trust_boundary="hypothesis_relation",
                )
            )
    for record in exploratory_records:
        if record.exploration_type == "question_decomposition" and record.status in {"open", "active"}:
            moments.append(
                _moment(
                    "direction.brainstorm",
                    reason="open question decomposition should steer the next local analysis",
                    target_type="exploratory_record",
                    target_id=record.record_id,
                    priority="high",
                    timing="before_next_local_step",
                    trust_boundary="exploratory_direction",
                )
            )
        if record.exploration_type == "relation_path_brainstorm" and record.status in {"open", "active"}:
            moments.append(
                _moment(
                    "brainstorm_relation_path",
                    reason="relation path brainstorming is open",
                    target_type="exploratory_record",
                    target_id=record.record_id,
                    priority="high",
                    timing="before_using_relation_as_claim",
                    trust_boundary="exploratory_relation_path",
                )
            )
        if record.exploration_type in {"source_asset", "backtrace_step"} and record.status in {"open", "active"}:
            moments.append(
                _moment(
                    "backtrace_source_reconstruction",
                    reason="exploratory source/backtrace record is still open",
                    target_type="exploratory_record",
                    target_id=record.record_id,
                    priority="high",
                    timing="before_following_source_chain",
                    trust_boundary="source_backtrace",
                )
            )
        if record.original_question and record.local_question and record.status in {"open", "active"}:
            moments.append(
                _moment(
                    "audit_original_question_drift",
                    reason="exploratory local question must stay tied to the original question",
                    target_type="exploratory_record",
                    target_id=record.record_id,
                    priority="high",
                    timing="during_backtrace_loop",
                    trust_boundary="question_continuity",
                )
            )
    for route in route_state.get("routes", []):
        if route.get("status") in {"live", "selected"}:
            moments.append(
                _moment(
                    "record_route_choice",
                    reason="live research route should preserve route-choice rationale",
                    target_type="research_route",
                    target_id=str(route.get("route_id") or ""),
                    priority="normal",
                    timing="before_route_dependent_work",
                    trust_boundary="route_continuity",
                )
            )
        if route.get("status") in {"blocked", "abandoned"}:
            moments.append(
                _moment(
                    "record_failed_route_lesson",
                    reason="blocked or abandoned research route should preserve failure-mode lesson",
                    target_type="research_route",
                    target_id=str(route.get("route_id") or ""),
                    priority="high",
                    timing="before_retry_or_pivot",
                    trust_boundary="failed_route_memory",
                )
            )
        if route.get("checkpoint_ids") or route.get("pivot_reason"):
            moments.append(
                _moment(
                    "checkpoint_before_route_switch",
                    reason="route switch or pivot has checkpoint/pivot metadata",
                    target_type="research_route",
                    target_id=str(route.get("route_id") or ""),
                    priority="high",
                    timing="before_switching_route",
                    trust_boundary="route_switch_checkpoint",
                )
            )
    for gap in provenance_gaps:
        moments.append(
            _moment(
                "capture_source_or_code_provenance",
                reason=str(gap.get("reason") or "source/code provenance gap"),
                target_type=str(gap.get("target_type") or "claim"),
                target_id=str(gap.get("target_id") or ""),
                priority=str(gap.get("severity") or "normal"),
                timing="before_using_as_evidence_or_validation",
                trust_boundary="provenance_before_reuse",
                missing_components=[str(gap.get("gap_type") or "provenance_gap")],
            )
        )
    return _dedupe_moments(moments)

def _moment(
    moment: str,
    *,
    reason: str,
    target_type: str,
    target_id: str,
    priority: str,
    timing: str,
    trust_boundary: str,
    missing_components: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "moment": moment,
        "priority": _moment_priority(priority),
        "reason": reason,
        "target_type": target_type,
        "target_id": target_id,
        "target_refs": [f"{target_type}:{target_id}"],
        "timing": timing,
        "trust_boundary": trust_boundary,
    }
    if missing_components:
        payload["missing_components"] = missing_components
    return payload

def _moment_priority(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"blocking", "high", "normal", "low"}:
        return normalized
    if normalized == "recommended":
        return "high"
    if normalized == "advisory":
        return "normal"
    return "normal"
