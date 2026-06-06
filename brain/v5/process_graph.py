"""Read-only process graph slice over AITP v5 typed records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from brain.v5.models import (
    ClaimRecord,
    CodeStateRecord,
    EvidenceRecord,
    ExploratoryRecord,
    MemoryEntryRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    SessionBinding,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
    SensemakingReportRecord,
)
from brain.v5.moment_policy import build_host_agnostic_moment_policy
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, read_record


_CLOSED_OBLIGATION_STATUSES = {"closed", "complete", "completed", "done", "discharged", "resolved", "passed"}


def build_process_graph_slice(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Build a read-only graph slice from existing typed records."""

    limit = max(1, int(limit or 80))
    session = read_record(ws.session_path(session_id), SessionBinding)
    focus_claim_id = claim_id or session.active_claim
    topic_id = session.topic_id

    claims = _filter_claims(_records(ws, "claims", ClaimRecord), topic_id, focus_claim_id)
    claim_ids = {claim.claim_id for claim in claims}
    if focus_claim_id:
        claim_ids.add(focus_claim_id)

    references = [
        record
        for record in _records(ws, "reference_locations", ReferenceLocationRecord)
        if record.topic_id == topic_id and (not claim_ids or not record.claim_id or record.claim_id in claim_ids)
    ]
    source_assets = _filter_source_assets(_records(ws, "source_assets", SourceAssetRecord), topic_id, claim_ids)
    evidence = _filter_by_topic_and_claim(_records(ws, "evidence", EvidenceRecord), topic_id, claim_ids)
    obligations = _filter_by_topic_and_claim(_records(ws, "proof_obligations", ProofObligationRecord), topic_id, claim_ids)
    objects = [record for record in _records(ws, "physics_objects", PhysicsObjectRecord) if record.topic_id == topic_id]
    object_ids = {record.object_id for record in objects}
    relations = [
        record
        for record in _records(ws, "object_relations", ObjectRelationRecord)
        if record.topic_id == topic_id
        and (not claim_ids or record.claim_id in claim_ids or record.subject_id in object_ids or record.object_id in object_ids)
    ]
    validation_contracts = _filter_by_topic_and_claim(
        _records(ws, "validation_contracts", ValidationContractRecord),
        topic_id,
        claim_ids,
    )
    validation_results = _filter_by_topic_and_claim(
        _records(ws, "validation_results", ValidationResultRecord),
        topic_id,
        claim_ids,
    )
    tool_runs = _filter_by_topic_and_claim(_records(ws, "tool_runs", ToolRunRecord), topic_id, claim_ids)
    memory_entries = [
        record
        for record in list_valid_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
        if record.topic_id == topic_id and (not claim_ids or record.source_claim_id in claim_ids)
    ]
    sensemaking_reports = _filter_by_topic_and_claim(
        _records(ws, "sensemaking_reports", SensemakingReportRecord),
        topic_id,
        claim_ids,
    )
    exploratory_records = _filter_exploratory_records(
        _records(ws, "exploratory_records", ExploratoryRecord),
        topic_id,
        claim_ids,
        session_id,
    )
    code_state_ids = {code_id for run in tool_runs for code_id in run.code_state_ids if code_id}
    code_state_ids.update(code_id for asset in source_assets for code_id in asset.code_state_ids if code_id)
    code_state_ids.update(_linked_code_state_ids_for_claim(_records(ws, "code_states", CodeStateRecord), claim_ids))
    code_states = [
        record
        for record in _records(ws, "code_states", CodeStateRecord)
        if record.code_state_id in code_state_ids
    ]

    builder = _GraphBuilder(limit)
    builder.add_node("session", session.session_id, session, label=session.session_id)
    for record in claims:
        builder.add_node("claim", record.claim_id, record, label=record.statement)
    for record in references:
        builder.add_node("reference_location", record.location_id, record, label=record.label)
    for record in source_assets:
        builder.add_node("source_asset", record.asset_id, record, label=record.title)
    for record in evidence:
        builder.add_node("evidence", record.evidence_id, record, label=record.summary)
    for record in obligations:
        builder.add_node("proof_obligation", record.obligation_id, record, label=record.statement)
    for record in objects:
        builder.add_node("physics_object", record.object_id, record, label=record.name)
    for record in relations:
        builder.add_node("object_relation", record.relation_id, record, label=record.statement)
    for record in validation_contracts:
        builder.add_node("validation_contract", record.contract_id, record, label=record.validator_role)
    for record in validation_results:
        builder.add_node("validation_result", record.result_id, record, label=record.summary or record.status)
    for record in tool_runs:
        builder.add_node("tool_run", record.run_id, record, label=f"{record.tool_family}:{record.tool_name}")
    for record in code_states:
        builder.add_node("code_state", record.code_state_id, record, label=record.repo_id)
    for record in memory_entries:
        builder.add_node("memory_entry", record.entry_id, record, label=record.statement or record.entry_id)
    for record in sensemaking_reports:
        builder.add_node("sensemaking_report", record.report_id, record, label=record.title)
    for record in exploratory_records:
        builder.add_node("exploratory_record", record.record_id, record, label=record.title)

    for claim in claims:
        builder.add_edge("session", session.session_id, "claim", claim.claim_id, "session_focus")
    _add_edges(builder, session, claims, references, source_assets, evidence, obligations, objects, relations,
               validation_contracts, validation_results, tool_runs, code_states, memory_entries, sensemaking_reports,
               exploratory_records)

    open_obligations = [_obligation_slice(record) for record in obligations if not _closed(record.status)]
    source_backtrace = _source_backtrace(claims, references, source_assets, evidence, obligations, objects, relations, exploratory_records)
    relation_neighborhood = _relation_neighborhood(objects, relations)
    exploratory_slices = [_exploratory_slice(record) for record in exploratory_records]
    trust_boundary_reasons = [
        "process_graph_slice is orientation-only",
        "truth_source is typed_records",
        "reference_location records are pointers, not evidence",
        "this API cannot update kernel state",
        "this API cannot update claim trust",
    ]
    moment_policy = build_host_agnostic_moment_policy(
        session_id=session_id,
        topic_id=topic_id,
        claim_id=focus_claim_id,
        open_obligations=open_obligations,
        source_backtrace=source_backtrace,
        relation_neighborhood=relation_neighborhood,
        exploratory_records=exploratory_slices,
        trust_boundary_reasons=trust_boundary_reasons,
    )

    return {
        "ok": True,
        "kind": "process_graph_slice",
        "session_id": session_id,
        "topic_id": topic_id,
        "claim_id": focus_claim_id,
        "truth_source": "typed_records",
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "nodes": builder.nodes,
        "edges": builder.edges,
        "open_obligations": open_obligations,
        "source_backtrace": source_backtrace,
        "relation_neighborhood": relation_neighborhood,
        "trust_boundary_reasons": trust_boundary_reasons,
        "exploratory_records": exploratory_slices,
        "moment_policy": moment_policy,
        "recommended_moments": _recommended_moments(open_obligations, source_backtrace, relations, exploratory_records),
        "record_counts": {
            "claim": len(claims),
            "physics_object": len(objects),
            "object_relation": len(relations),
            "reference_location": len(references),
            "source_asset": len(source_assets),
            "evidence": len(evidence),
            "proof_obligation": len(obligations),
            "code_state": len(code_states),
            "tool_run": len(tool_runs),
            "validation_contract": len(validation_contracts),
            "validation_result": len(validation_results),
            "memory_entry": len(memory_entries),
            "sensemaking_report": len(sensemaking_reports),
            "exploratory_record": len(exploratory_records),
        },
        "truncation": {
            "limit": limit,
            "node_limit_reached": builder.node_limit_reached,
            "dropped_node_count": builder.dropped_node_count,
        },
    }


class _GraphBuilder:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.nodes: list[dict[str, Any]] = []
        self.edges: list[dict[str, Any]] = []
        self.node_ids: set[str] = set()
        self.edge_ids: set[str] = set()
        self.dropped_node_count = 0

    @property
    def node_limit_reached(self) -> bool:
        return self.dropped_node_count > 0

    def add_node(self, node_type: str, record_id: str, record: Any, *, label: str = "") -> str:
        node_id = _node_id(node_type, record_id)
        if node_id in self.node_ids:
            return node_id
        if len(self.nodes) >= self.limit:
            self.dropped_node_count += 1
            return node_id
        payload = _record_payload(record)
        self.node_ids.add(node_id)
        self.nodes.append(
            {
                "id": node_id,
                "type": node_type,
                "record_id": record_id,
                "label": label,
                "topic_id": str(payload.get("topic_id") or ""),
                "claim_id": str(payload.get("claim_id") or payload.get("source_claim_id") or ""),
                "status": str(payload.get("status") or payload.get("confidence_state") or ""),
                "record": payload,
            }
        )
        return node_id

    def add_edge(self, source_type: str, source_id: str, target_type: str, target_id: str, edge_type: str) -> None:
        source = _node_id(source_type, source_id)
        target = _node_id(target_type, target_id)
        if source not in self.node_ids or target not in self.node_ids:
            return
        edge_id = f"{source}->{edge_type}->{target}"
        if edge_id in self.edge_ids:
            return
        self.edge_ids.add(edge_id)
        self.edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "source_type": source_type,
                "target_type": target_type,
            }
        )


def _add_edges(
    builder: _GraphBuilder,
    session: SessionBinding,
    claims: list[ClaimRecord],
    references: list[ReferenceLocationRecord],
    source_assets: list[SourceAssetRecord],
    evidence: list[EvidenceRecord],
    obligations: list[ProofObligationRecord],
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
    validation_contracts: list[ValidationContractRecord],
    validation_results: list[ValidationResultRecord],
    tool_runs: list[ToolRunRecord],
    code_states: list[CodeStateRecord],
    memory_entries: list[MemoryEntryRecord],
    sensemaking_reports: list[SensemakingReportRecord],
    exploratory_records: list[ExploratoryRecord],
) -> None:
    reference_lookup = _reference_lookup(references)
    source_asset_lookup = _source_asset_lookup(source_assets)
    object_ids = {record.object_id for record in objects}
    validation_result_ids = {record.result_id for record in validation_results}
    tool_run_ids = {record.run_id for record in tool_runs}
    code_state_ids = {record.code_state_id for record in code_states}

    for record in references:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "reference_location", record.location_id, "has_reference_location")
    for record in source_assets:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "source_asset", record.asset_id, "has_source_asset")
        for location_id in record.reference_location_ids:
            builder.add_edge("source_asset", record.asset_id, "reference_location", location_id, "has_reference_location")
        for code_state_id in record.code_state_ids:
            if code_state_id in code_state_ids:
                builder.add_edge("source_asset", record.asset_id, "code_state", code_state_id, "has_code_state")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("source_asset", record.asset_id, "reference_location", location_id, "uses_source")
        for parent_id in record.derived_from:
            builder.add_edge("source_asset", record.asset_id, "source_asset", parent_id, "derived_from")
    for record in evidence:
        builder.add_edge("claim", record.claim_id, "evidence", record.evidence_id, "has_evidence")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("evidence", record.evidence_id, "reference_location", location_id, "uses_source")
        for run_id in record.tool_run_ids:
            if run_id in tool_run_ids:
                builder.add_edge("evidence", record.evidence_id, "tool_run", run_id, "uses_tool_run")
        for result_id in record.validation_result_ids:
            if result_id in validation_result_ids:
                builder.add_edge("evidence", record.evidence_id, "validation_result", result_id, "uses_validation_result")
    for record in obligations:
        builder.add_edge("claim", record.claim_id, "proof_obligation", record.obligation_id, "has_proof_obligation")
        for evidence_id in record.evidence_refs:
            builder.add_edge("proof_obligation", record.obligation_id, "evidence", evidence_id, "supported_by_evidence")
    for record in relations:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "object_relation", record.relation_id, "has_object_relation")
        if record.subject_id in object_ids:
            builder.add_edge("object_relation", record.relation_id, "physics_object", record.subject_id, "relation_subject")
        if record.object_id in object_ids:
            builder.add_edge("object_relation", record.relation_id, "physics_object", record.object_id, "relation_object")
        for evidence_id in record.evidence_refs:
            builder.add_edge("object_relation", record.relation_id, "evidence", evidence_id, "supported_by_evidence")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("object_relation", record.relation_id, "reference_location", location_id, "uses_source")
    for record in validation_contracts:
        builder.add_edge("claim", record.claim_id, "validation_contract", record.contract_id, "has_validation_contract")
    for record in validation_results:
        builder.add_edge("claim", record.claim_id, "validation_result", record.result_id, "has_validation_result")
        builder.add_edge("validation_result", record.result_id, "validation_contract", record.contract_id, "checks_contract")
        if record.tool_run_id in tool_run_ids:
            builder.add_edge("validation_result", record.result_id, "tool_run", record.tool_run_id, "validates_tool_run")
        for evidence_id in record.evidence_refs:
            builder.add_edge("validation_result", record.result_id, "evidence", evidence_id, "has_evidence_ref")
    for record in tool_runs:
        builder.add_edge("claim", record.claim_id, "tool_run", record.run_id, "has_tool_run")
        for code_state_id in record.code_state_ids:
            if code_state_id in code_state_ids:
                builder.add_edge("tool_run", record.run_id, "code_state", code_state_id, "uses_code_state")
    for record in memory_entries:
        builder.add_edge("claim", record.source_claim_id, "memory_entry", record.entry_id, "promoted_to_memory")
        for evidence_id in record.evidence_refs:
            builder.add_edge("memory_entry", record.entry_id, "evidence", evidence_id, "derived_from_evidence")
        for result_id in record.validation_result_ids:
            builder.add_edge("memory_entry", record.entry_id, "validation_result", result_id, "derived_from_validation")
    for record in sensemaking_reports:
        builder.add_edge("claim", record.claim_id, "sensemaking_report", record.report_id, "has_sensemaking_report")
        for object_id in record.object_ids:
            builder.add_edge("sensemaking_report", record.report_id, "physics_object", object_id, "mentions_object")
        for relation_id in record.relation_ids:
            builder.add_edge("sensemaking_report", record.report_id, "object_relation", relation_id, "mentions_relation")
        for evidence_id in record.evidence_refs:
            builder.add_edge("sensemaking_report", record.report_id, "evidence", evidence_id, "mentions_evidence")
    for record in exploratory_records:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "exploratory_record", record.record_id, "has_exploratory_record")
        if record.session_id:
            builder.add_edge("session", record.session_id, "exploratory_record", record.record_id, "recorded_exploration")
        for object_id in record.object_ids:
            builder.add_edge("exploratory_record", record.record_id, "physics_object", object_id, "explores_object")
        for relation_id in record.relation_ids:
            builder.add_edge("exploratory_record", record.record_id, "object_relation", relation_id, "explores_relation")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("exploratory_record", record.record_id, "reference_location", location_id, "explores_source")
            asset_id = source_asset_lookup.get(ref)
            if asset_id:
                builder.add_edge("exploratory_record", record.record_id, "source_asset", asset_id, "explores_source_asset")
        for parent_id in record.parent_record_ids:
            builder.add_edge("exploratory_record", record.record_id, "exploratory_record", parent_id, "continues_from")
    if session.active_claim:
        for claim in claims:
            if claim.claim_id == session.active_claim:
                builder.add_edge("session", session.session_id, "claim", claim.claim_id, "active_claim")


def _records(ws: WorkspacePaths, family: str, cls: type) -> list:
    return list_valid_records(ws.registry_dir(family), cls)


def _filter_claims(records: list[ClaimRecord], topic_id: str, claim_id: str) -> list[ClaimRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id and (not claim_id or record.claim_id == claim_id)
    ]


def _filter_by_topic_and_claim(records: list, topic_id: str, claim_ids: set[str]) -> list:
    return [
        record
        for record in records
        if getattr(record, "topic_id", "") == topic_id
        and (not claim_ids or getattr(record, "claim_id", "") in claim_ids)
    ]


def _filter_source_assets(records: list[SourceAssetRecord], topic_id: str, claim_ids: set[str]) -> list[SourceAssetRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id and (not claim_ids or not record.claim_id or record.claim_id in claim_ids)
    ]


def _filter_exploratory_records(
    records: list[ExploratoryRecord],
    topic_id: str,
    claim_ids: set[str],
    session_id: str,
) -> list[ExploratoryRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id
        and (
            not claim_ids
            or record.claim_id in claim_ids
            or not record.claim_id
            or record.session_id == session_id
        )
    ]


def _linked_code_state_ids_for_claim(records: list[CodeStateRecord], claim_ids: set[str]) -> set[str]:
    result = set()
    for record in records:
        if _mapping_links_any(record.linked_records, claim_ids):
            result.add(record.code_state_id)
    return result


def _mapping_links_any(value: Any, targets: set[str]) -> bool:
    if isinstance(value, dict):
        return any(_mapping_links_any(item, targets) for item in value.values())
    if isinstance(value, list):
        return any(_mapping_links_any(item, targets) for item in value)
    return isinstance(value, str) and value in targets


def _record_payload(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    return dict(record)


def _node_id(node_type: str, record_id: str) -> str:
    return f"{node_type}:{record_id}"


def _reference_lookup(records: list[ReferenceLocationRecord]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record in records:
        for value in (
            record.location_id,
            f"reference_location:{record.location_id}",
            f"reference-location:{record.location_id}",
            record.source_ref,
            record.uri,
            record.label,
        ):
            if value:
                lookup[value] = record.location_id
    return lookup


def _source_asset_lookup(records: list[SourceAssetRecord]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for record in records:
        for value in (
            record.asset_id,
            f"source_asset:{record.asset_id}",
            f"source-asset:{record.asset_id}",
            record.uri,
            record.title,
            record.label,
            *record.source_refs,
        ):
            if value:
                lookup[value] = record.asset_id
    return lookup


def _closed(status: str) -> bool:
    return status.strip().lower().replace("-", "_") in _CLOSED_OBLIGATION_STATUSES


def _obligation_slice(record: ProofObligationRecord) -> dict[str, Any]:
    suggested_moments = _suggested_moments_for_obligation(record)
    return {
        "obligation_id": record.obligation_id,
        "claim_id": record.claim_id,
        "status": record.status,
        "obligation_type": record.obligation_type,
        "statement": record.statement,
        "severity": _obligation_severity(record),
        "target_node_id": f"proof_obligation:{record.obligation_id}",
        "suggested_moments": suggested_moments,
        "source_refs": list(record.source_refs),
        "trust_boundary": "before_final_or_promotion" if record.human_gate_required else "before_validation",
        "next_action": record.next_action,
        "required_evidence": list(record.required_evidence),
    }


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
            record.record_id
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
                "claim_id": claim_id,
                "statement": claim.statement,
                "reference_location_ids": claim_refs,
                "source_asset_ids": claim_assets,
                "evidence_ids": claim_evidence,
                "proof_obligation_ids": claim_obligations,
                "object_relation_ids": claim_relations,
                "physics_object_ids": [record.object_id for record in objects],
                "exploratory_record_ids": claim_backtrace_records,
                "missing_components": missing,
                "complete": not missing,
            }
        )
    return result


def _relation_neighborhood(
    objects: list[PhysicsObjectRecord],
    relations: list[ObjectRelationRecord],
) -> list[dict[str, Any]]:
    object_names = {record.object_id: record.name for record in objects}
    return [
        {
            "relation_id": record.relation_id,
            "claim_id": record.claim_id,
            "status": record.status,
            "relation_type": record.relation_type,
            "subject_id": record.subject_id,
            "subject_name": object_names.get(record.subject_id, ""),
            "object_id": record.object_id,
            "object_name": object_names.get(record.object_id, ""),
            "failure_modes": list(record.failure_modes),
        }
        for record in relations
    ]


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
        "candidate_paths": list(record.candidate_paths),
        "unresolved_points": list(record.unresolved_points),
        "next_actions": list(record.next_actions),
    }


def _recommended_moments(
    open_obligations: list[dict[str, Any]],
    source_backtrace: list[dict[str, Any]],
    relations: list[ObjectRelationRecord],
    exploratory_records: list[ExploratoryRecord],
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


def _obligation_severity(record: ProofObligationRecord) -> str:
    text = " ".join(
        [
            record.obligation_type,
            record.maturity_level,
            record.statement,
            record.next_action,
            " ".join(record.required_evidence),
        ]
    ).lower()
    if record.human_gate_required and any(
        token in text
        for token in ("validation", "human", "final", "promotion", "publish", "trust", "theorem", "proof_gap")
    ):
        return "blocking"
    if any(token in text for token in ("source", "proof", "derive", "definition", "failure", "limit")):
        return "recommended"
    return "advisory"


def _suggested_moments_for_obligation(record: ProofObligationRecord) -> list[str]:
    text = " ".join(
        [
            record.obligation_type,
            record.statement,
            record.next_action,
            " ".join(record.required_evidence),
            " ".join(record.source_refs),
        ]
    ).lower()
    result = ["aitp.create_open_obligation"]
    if any(token in text for token in ("source", "citation", "reference", "provenance")):
        result.append("trace.follow_source_dependency")
    if any(token in text for token in ("definition", "define", "term", "notation")):
        result.append("trace.reconstruct_definition")
    if any(token in text for token in ("relation", "bridge", "connect", "path")):
        result.append("physics.brainstorm_relation_path")
    return result


def _dedupe_moments(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for item in items:
        key = (item.get("moment"), item.get("target_type"), item.get("target_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
