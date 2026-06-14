"""Read-only process graph slice over AITP v5 typed records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from brain.v5.models import (
    ClaimRecord,
    CodeStateRecord,
    EvidenceRecord,
    ExploratoryRecord,
    HumanCheckpointRecord,
    MemoryEntryRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    ReferenceLocationRecord,
    ResearchRouteRecord,
    ResearchRunEventRecord,
    ResearchRunRecord,
    SessionBinding,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
    SensemakingReportRecord,
)
from brain.v5.moment_policy import build_host_agnostic_moment_policy
from brain.v5.paths import WorkspacePaths
from brain.v5.payload_hints import with_draft_schema
from brain.v5.recovery_session import recover_session_binding_for_read
from brain.v5.source_reconstruction_review import build_source_reconstruction_review_slice
from brain.v5.source_stack_coverage import build_source_stack_coverage_slice
from brain.v5.store import list_valid_records
from brain.v5.workspace_migration_health import build_workspace_migration_health


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
    try:
        recovered = recover_session_binding_for_read(ws, session_id)
    except (FileNotFoundError, TypeError, ValueError, OSError) as error:
        return _unbound_process_graph_slice(
            ws,
            requested_session_id=session_id,
            claim_id=claim_id,
            limit=limit,
            reason=str(error) or error.__class__.__name__,
        )
    session = recovered.session
    requested_session_id = recovered.requested_session_id
    recovery_selection_source = recovered.recovery_selection_source
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
    routes = _filter_research_routes(
        _records(ws, "routes", ResearchRouteRecord),
        topic_id,
        claim_ids,
        session_id,
        session.active_route,
    )
    research_runs = _filter_research_runs(
        _records(ws, "research_runs", ResearchRunRecord),
        topic_id,
        claim_ids,
        session_id,
    )
    research_run_ids = {record.run_id for record in research_runs}
    research_run_events = _filter_research_run_events(
        _records(ws, "research_run_events", ResearchRunEventRecord),
        topic_id,
        claim_ids,
        session_id,
        research_run_ids,
    )
    route_checkpoint_ids = {checkpoint_id for route in routes for checkpoint_id in route.checkpoint_ids}
    checkpoints = _filter_human_checkpoints(
        _records(ws, "checkpoints", HumanCheckpointRecord),
        topic_id,
        claim_ids,
        route_checkpoint_ids,
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
    for record in checkpoints:
        builder.add_node("human_checkpoint", record.checkpoint_id, record, label=record.reason)
    for record in routes:
        builder.add_node("research_route", record.route_id, record, label=record.title)
    for record in research_runs:
        builder.add_node("research_run", record.run_id, record, label=record.title or record.objective)
    for record in research_run_events:
        builder.add_node("research_run_event", record.event_id, record, label=record.event_type)

    for claim in claims:
        builder.add_edge("session", session.session_id, "claim", claim.claim_id, "session_focus")
    _add_edges(builder, session, claims, references, source_assets, evidence, obligations, objects, relations,
               validation_contracts, validation_results, tool_runs, code_states, memory_entries, sensemaking_reports,
               exploratory_records, checkpoints, routes, research_runs, research_run_events)

    open_obligations = [_obligation_slice(record) for record in obligations if not _closed(record.status)]
    source_backtrace = _source_backtrace(claims, references, source_assets, evidence, obligations, objects, relations, exploratory_records)
    relation_neighborhood = _relation_neighborhood(objects, relations, exploratory_records)
    exploratory_slices = [_exploratory_slice(record) for record in exploratory_records]
    route_state = _route_state(session, routes)
    provenance_gaps = _provenance_gaps(
        claims=claims,
        references=references,
        source_assets=source_assets,
        evidence=evidence,
        validation_contracts=validation_contracts,
        validation_results=validation_results,
        tool_runs=tool_runs,
        code_states=code_states,
    )
    source_asset_index = _source_asset_index(source_assets, references, provenance_gaps)
    source_stack_coverage = build_source_stack_coverage_slice(
        ws,
        topic_id=topic_id,
        claim_ids=claim_ids,
    )
    source_reconstruction_review = build_source_reconstruction_review_slice(
        ws,
        topic_id=topic_id,
        claim_ids=claim_ids,
    )
    migration_health = build_workspace_migration_health(ws, sample_limit=3)
    trust_boundary_reasons = [
        "process_graph_slice is orientation-only",
        "truth_source is typed_records",
        "reference_location records are pointers, not evidence",
        "this API cannot update kernel state",
        "this API cannot update claim trust",
    ]
    if migration_health["status"] != "clear":
        trust_boundary_reasons.append(
            "workspace migration health is not clear; legacy migration surfaces are orientation-only and cannot update claim trust",
        )
    if migration_health["canonical_legacy_seed_count"] > 0:
        trust_boundary_reasons.append(
            "canonical legacy L2 seed memory must not be treated as active claim support until reviewed/reassigned/promoted",
        )
    moment_policy = build_host_agnostic_moment_policy(
        session_id=session.session_id,
        topic_id=topic_id,
        claim_id=focus_claim_id,
        open_obligations=open_obligations,
        source_backtrace=source_backtrace,
        relation_neighborhood=relation_neighborhood,
        exploratory_records=exploratory_slices,
        route_state=route_state,
        trust_boundary_reasons=trust_boundary_reasons,
    )

    return {
        "ok": True,
        "kind": "process_graph_slice",
        "session_id": session.session_id,
        "requested_session_id": requested_session_id,
        "recovery_selection_source": recovery_selection_source,
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
        "source_asset_index": source_asset_index,
        "source_stack_coverage": source_stack_coverage,
        "source_reconstruction_review": source_reconstruction_review,
        "migration_health": migration_health,
        "relation_neighborhood": relation_neighborhood,
        "trust_boundary_reasons": trust_boundary_reasons,
        "exploratory_records": exploratory_slices,
        "route_state": route_state,
        "provenance_gaps": provenance_gaps,
        "moment_policy": moment_policy,
        "recommended_moments": _recommended_moments(
            open_obligations,
            source_backtrace,
            relations,
            exploratory_records,
            route_state,
            provenance_gaps,
        ),
        "record_counts": {
            "claim": len(claims),
            "physics_object": len(objects),
            "object_relation": len(relations),
            "reference_location": len(references),
            "source_asset": len(source_assets),
            "source_asset_index": len(source_asset_index),
            "source_stack_coverage": len(source_stack_coverage["items"]),
            "source_reconstruction_review": len(source_reconstruction_review["items"]),
            "evidence": len(evidence),
            "proof_obligation": len(obligations),
            "code_state": len(code_states),
            "tool_run": len(tool_runs),
            "validation_contract": len(validation_contracts),
            "validation_result": len(validation_results),
            "memory_entry": len(memory_entries),
            "sensemaking_report": len(sensemaking_reports),
            "exploratory_record": len(exploratory_records),
            "human_checkpoint": len(checkpoints),
            "research_route": len(routes),
            "research_run": len(research_runs),
            "research_run_event": len(research_run_events),
            "provenance_gap": len(provenance_gaps),
        },
        "truncation": {
            "limit": limit,
            "node_limit_reached": builder.node_limit_reached,
            "dropped_node_count": builder.dropped_node_count,
        },
    }


def _unbound_process_graph_slice(
    ws: WorkspacePaths,
    *,
    requested_session_id: str,
    claim_id: str,
    limit: int,
    reason: str,
) -> dict[str, Any]:
    migration_health = build_workspace_migration_health(ws, sample_limit=3)
    trust_boundary_reasons = [
        "process_graph_slice is orientation-only",
        "requested session binding is missing or malformed",
        "truth_source is typed_records",
        "reference_location records are pointers, not evidence",
        "this API cannot update kernel state",
        "this API cannot update claim trust",
    ]
    if migration_health["status"] != "clear":
        trust_boundary_reasons.append(
            "workspace migration health is not clear; legacy migration surfaces are orientation-only and cannot update claim trust",
        )
    if migration_health["canonical_legacy_seed_count"] > 0:
        trust_boundary_reasons.append(
            "canonical legacy L2 seed memory must not be treated as active claim support until reviewed/reassigned/promoted",
        )
    route_state = _empty_route_state()
    moment_policy = build_host_agnostic_moment_policy(
        session_id=requested_session_id,
        topic_id="unbound-session",
        claim_id=claim_id,
        open_obligations=[],
        source_backtrace=[],
        relation_neighborhood=[],
        exploratory_records=[],
        route_state=route_state,
        trust_boundary_reasons=trust_boundary_reasons,
    )
    return {
        "ok": True,
        "kind": "process_graph_slice",
        "session_id": requested_session_id or "unbound-session",
        "requested_session_id": requested_session_id,
        "recovery_selection_source": "unbound_session",
        "topic_id": "unbound-session",
        "claim_id": claim_id,
        "truth_source": "typed_records",
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "nodes": [],
        "edges": [],
        "open_obligations": [],
        "source_backtrace": [],
        "source_asset_index": [],
        "source_stack_coverage": _empty_source_stack_coverage(),
        "source_reconstruction_review": _empty_source_reconstruction_review(),
        "migration_health": migration_health,
        "relation_neighborhood": [],
        "trust_boundary_reasons": trust_boundary_reasons,
        "exploratory_records": [],
        "route_state": route_state,
        "provenance_gaps": [
            {
                "gap_id": "unbound-session",
                "gap_type": "session_binding_missing",
                "provenance_kind": "session_binding",
                "reason": reason or "requested session binding is missing or malformed",
                "topic_id": "unbound-session",
                "claim_id": claim_id,
                "target_type": "session",
                "target_id": requested_session_id or "unbound-session",
                "target_refs": [f"session:{requested_session_id or 'unbound-session'}"],
                "recommended_actions": ["bind_session"],
                "recommended_entrypoints": ["aitp_v5_bind_session"],
                "payload_hints": [],
                "severity": "recommended",
                "required_now": False,
                "required_before_trust_change": False,
                "strict_boundary": "read-only recovery surface",
                "blocking_when_used_as": ["claim_support", "trust_update", "old_store_retirement"],
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        ],
        "moment_policy": moment_policy,
        "recommended_moments": [],
        "record_counts": {
            "claim": 0,
            "physics_object": 0,
            "object_relation": 0,
            "reference_location": 0,
            "source_asset": 0,
            "source_asset_index": 0,
            "source_stack_coverage": 0,
            "source_reconstruction_review": 0,
            "evidence": 0,
            "proof_obligation": 0,
            "code_state": 0,
            "tool_run": 0,
            "validation_contract": 0,
            "validation_result": 0,
            "memory_entry": 0,
            "sensemaking_report": 0,
            "exploratory_record": 0,
            "human_checkpoint": 0,
            "research_route": 0,
            "research_run": 0,
            "research_run_event": 0,
            "provenance_gap": 1,
        },
        "truncation": {
            "limit": limit,
            "node_limit_reached": False,
            "dropped_node_count": 0,
        },
    }


def _empty_source_stack_coverage() -> dict[str, Any]:
    return {
        "kind": "source_stack_coverage_manifest",
        "claim_count": 0,
        "coverage_status_counts": {},
        "missing_required_output_counts": {},
        "source_component_gap_counts": {},
        "source_review_status_counts": {},
        "items": [],
        "next_actions": [],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _empty_source_reconstruction_review() -> dict[str, Any]:
    return {
        "kind": "source_reconstruction_review_manifest",
        "claim_count": 0,
        "review_progress": {
            "passed": 0,
            "needs_revision": 0,
            "inconclusive": 0,
            "pending": 0,
        },
        "items": [],
        "next_actions": [],
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _empty_route_state() -> dict[str, Any]:
    return {
        "active_route_id": "",
        "routes": [],
        "live_routes": [],
        "blocked_routes": [],
        "abandoned_routes": [],
        "pivot_routes": [],
        "live_route_ids": [],
        "blocked_route_ids": [],
        "abandoned_route_ids": [],
        "pivot_route_ids": [],
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
    checkpoints: list[HumanCheckpointRecord],
    routes: list[ResearchRouteRecord],
    research_runs: list[ResearchRunRecord],
    research_run_events: list[ResearchRunEventRecord],
) -> None:
    reference_lookup = _reference_lookup(references)
    source_asset_lookup = _source_asset_lookup(source_assets)
    object_ids = {record.object_id for record in objects}
    validation_result_ids = {record.result_id for record in validation_results}
    tool_run_ids = {record.run_id for record in tool_runs}
    code_state_ids = {record.code_state_id for record in code_states}
    exploratory_ids = {record.record_id for record in exploratory_records}
    checkpoint_ids = {record.checkpoint_id for record in checkpoints}
    route_ids = {record.route_id for record in routes}
    evidence_ids = {record.evidence_id for record in evidence}
    research_run_ids = {record.run_id for record in research_runs}

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
    for record in routes:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "research_route", record.route_id, "has_research_route")
        if record.session_id:
            builder.add_edge("session", record.session_id, "research_route", record.route_id, "recorded_route")
        for parent_id in record.parent_route_ids:
            if parent_id in route_ids:
                builder.add_edge("research_route", record.route_id, "research_route", parent_id, "branches_from")
        for checkpoint_id in record.checkpoint_ids:
            if checkpoint_id in checkpoint_ids:
                builder.add_edge("research_route", record.route_id, "human_checkpoint", checkpoint_id, "requires_checkpoint")
        for exploratory_id in record.exploratory_record_ids:
            if exploratory_id in exploratory_ids:
                builder.add_edge("research_route", record.route_id, "exploratory_record", exploratory_id, "uses_exploration")
        for object_id in record.object_ids:
            builder.add_edge("research_route", record.route_id, "physics_object", object_id, "route_mentions_object")
        for relation_id in record.relation_ids:
            builder.add_edge("research_route", record.route_id, "object_relation", relation_id, "route_mentions_relation")
        for evidence_id in record.evidence_refs:
            if evidence_id in evidence_ids:
                builder.add_edge("research_route", record.route_id, "evidence", evidence_id, "uses_evidence")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("research_route", record.route_id, "reference_location", location_id, "uses_source")
            asset_id = source_asset_lookup.get(ref)
            if asset_id:
                builder.add_edge("research_route", record.route_id, "source_asset", asset_id, "uses_source_asset")
    for record in research_runs:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "research_run", record.run_id, "has_research_run")
        if record.session_id:
            builder.add_edge("session", record.session_id, "research_run", record.run_id, "recorded_research_run")
        for event_id in record.event_ids:
            builder.add_edge("research_run", record.run_id, "research_run_event", event_id, "has_run_event")
        for evidence_id in record.evidence_refs:
            if evidence_id in evidence_ids:
                builder.add_edge("research_run", record.run_id, "evidence", evidence_id, "uses_evidence")
        for result_id in record.validation_refs:
            if result_id in validation_result_ids:
                builder.add_edge("research_run", record.run_id, "validation_result", result_id, "uses_validation_result")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("research_run", record.run_id, "reference_location", location_id, "uses_source")
            asset_id = source_asset_lookup.get(ref)
            if asset_id:
                builder.add_edge("research_run", record.run_id, "source_asset", asset_id, "uses_source_asset")
    for record in research_run_events:
        if record.run_id in research_run_ids:
            builder.add_edge("research_run", record.run_id, "research_run_event", record.event_id, "has_run_event")
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "research_run_event", record.event_id, "has_research_run_event")
        if record.session_id:
            builder.add_edge("session", record.session_id, "research_run_event", record.event_id, "recorded_research_run_event")
        for evidence_id in record.evidence_refs:
            if evidence_id in evidence_ids:
                builder.add_edge("research_run_event", record.event_id, "evidence", evidence_id, "mentions_evidence")
        for result_id in record.validation_refs:
            if result_id in validation_result_ids:
                builder.add_edge("research_run_event", record.event_id, "validation_result", result_id, "mentions_validation")
        for ref in record.source_refs:
            location_id = reference_lookup.get(ref)
            if location_id:
                builder.add_edge("research_run_event", record.event_id, "reference_location", location_id, "mentions_source")
            asset_id = source_asset_lookup.get(ref)
            if asset_id:
                builder.add_edge("research_run_event", record.event_id, "source_asset", asset_id, "mentions_source_asset")
    if session.active_claim:
        for claim in claims:
            if claim.claim_id == session.active_claim:
                builder.add_edge("session", session.session_id, "claim", claim.claim_id, "active_claim")
    if session.active_route:
        builder.add_edge("session", session.session_id, "research_route", session.active_route, "active_route")


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


def _filter_research_routes(
    records: list[ResearchRouteRecord],
    topic_id: str,
    claim_ids: set[str],
    session_id: str,
    active_route: str,
) -> list[ResearchRouteRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id
        and (
            not claim_ids
            or record.claim_id in claim_ids
            or not record.claim_id
            or record.session_id == session_id
            or record.route_id == active_route
        )
    ]


def _filter_human_checkpoints(
    records: list[HumanCheckpointRecord],
    topic_id: str,
    claim_ids: set[str],
    checkpoint_ids: set[str],
) -> list[HumanCheckpointRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id
        and (record.checkpoint_id in checkpoint_ids or not claim_ids or record.claim_id in claim_ids)
    ]


def _filter_research_runs(
    records: list[ResearchRunRecord],
    topic_id: str,
    claim_ids: set[str],
    session_id: str,
) -> list[ResearchRunRecord]:
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


def _filter_research_run_events(
    records: list[ResearchRunEventRecord],
    topic_id: str,
    claim_ids: set[str],
    session_id: str,
    research_run_ids: set[str],
) -> list[ResearchRunEventRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id
        and (
            record.run_id in research_run_ids
            or not claim_ids
            or record.claim_id in claim_ids
            or not record.claim_id
            or record.session_id == session_id
        )
    ]


def _provenance_gaps(
    *,
    claims: list[ClaimRecord],
    references: list[ReferenceLocationRecord],
    source_assets: list[SourceAssetRecord],
    evidence: list[EvidenceRecord],
    validation_contracts: list[ValidationContractRecord],
    validation_results: list[ValidationResultRecord],
    tool_runs: list[ToolRunRecord],
    code_states: list[CodeStateRecord],
) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = claim.claim_id
        claim_refs = [record for record in references if record.claim_id == claim_id]
        claim_assets = [
            record
            for record in source_assets
            if record.claim_id == claim_id or _mapping_links_any(record.linked_records, {claim_id})
        ]
        claim_runs = [record for record in tool_runs if record.claim_id == claim_id]
        claim_contracts = [record for record in validation_contracts if record.claim_id == claim_id]
        claim_results = [record for record in validation_results if record.claim_id == claim_id]
        claim_code_state_ids = {
            code_id
            for run in claim_runs
            for code_id in run.code_state_ids
            if code_id
        }
        claim_code_state_ids.update(
            code_id
            for asset in claim_assets
            for code_id in asset.code_state_ids
            if code_id
        )
        claim_code_states = [
            record
            for record in code_states
            if record.code_state_id in claim_code_state_ids or _mapping_links_any(record.linked_records, {claim_id})
        ]
        if not claim_refs:
            gaps.append(
                _provenance_gap(
                    gap_type="reference_location_missing",
                    reason="claim has no typed source/reference pointer",
                    topic_id=claim.topic_id,
                    claim_id=claim_id,
                    target_type="claim",
                    target_id=claim_id,
                    recommended_actions=["aitp.record_reference_location"],
                    recommended_entrypoints=["aitp_v5_record_reference_location"],
                    severity="high",
                    provenance_kind="source",
                    target_record=claim,
                )
            )
        if not claim_assets:
            gaps.append(
                _provenance_gap(
                    gap_type="source_asset_missing",
                    reason="claim has no canonical source asset identity",
                    topic_id=claim.topic_id,
                    claim_id=claim_id,
                    target_type="claim",
                    target_id=claim_id,
                    recommended_actions=["aitp.capture_source_asset_auto", "aitp.register_source_asset"],
                    recommended_entrypoints=[
                        "aitp_v5_capture_source_asset_auto",
                        "aitp_v5_register_source_asset",
                    ],
                    severity="high",
                    provenance_kind="source",
                    target_record=claim,
                )
            )
        for asset in claim_assets:
            if not asset.content_hash:
                gaps.append(
                    _provenance_gap(
                        gap_type="source_asset_hash_missing",
                        reason="source asset identity lacks a stable content hash",
                        topic_id=asset.topic_id,
                        claim_id=asset.claim_id or claim_id,
                        target_type="source_asset",
                        target_id=asset.asset_id,
                        recommended_actions=["aitp.capture_source_asset_auto", "aitp.register_source_asset"],
                        recommended_entrypoints=[
                            "aitp_v5_capture_source_asset_auto",
                            "aitp_v5_register_source_asset",
                        ],
                        severity="normal",
                        provenance_kind="source",
                        target_record=asset,
                    )
                )
            duplicate = asset.metadata.get("duplicate_hash_diagnostics", {})
            if isinstance(duplicate, dict) and duplicate.get("duplicate_hash"):
                gaps.append(
                    _provenance_gap(
                        gap_type="source_asset_duplicate_hash",
                        reason="source asset content hash matches another registered asset",
                        topic_id=asset.topic_id,
                        claim_id=asset.claim_id or claim_id,
                        target_type="source_asset",
                        target_id=asset.asset_id,
                        recommended_actions=["aitp.review_source_asset_duplicate"],
                        recommended_entrypoints=["aitp_v5_register_source_asset"],
                        severity="normal",
                        provenance_kind="source",
                        target_record=asset,
                    )
                )
        if _claim_needs_code_provenance(claim):
            if not claim_code_states:
                gaps.append(
                    _provenance_gap(
                        gap_type="code_state_missing",
                        reason="code-dependent claim has no captured git code state",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.capture_code_state_auto", "aitp.record_code_state"],
                        recommended_entrypoints=["aitp_v5_capture_code_state_auto", "aitp_v5_record_code_state"],
                        severity="high",
                        provenance_kind="code",
                        target_record=claim,
                    )
                )
            if not claim_runs:
                gaps.append(
                    _provenance_gap(
                        gap_type="tool_run_missing",
                        reason="code-dependent claim has no typed tool-run provenance",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.capture_tool_run_auto", "aitp.record_tool_run"],
                        recommended_entrypoints=["aitp_v5_capture_tool_run_auto", "aitp_v5_record_tool_run"],
                        severity="high",
                        provenance_kind="tool_run",
                        target_record=claim,
                    )
                )
            if not claim_contracts:
                gaps.append(
                    _provenance_gap(
                        gap_type="validation_contract_missing",
                        reason="code/benchmark-dependent claim has no validation contract",
                        topic_id=claim.topic_id,
                        claim_id=claim_id,
                        target_type="claim",
                        target_id=claim_id,
                        recommended_actions=["aitp.create_validation_contract"],
                        recommended_entrypoints=["aitp_v5_create_validation_contract"],
                        severity="normal",
                        provenance_kind="validation",
                        target_record=claim,
                    )
                )
        for run in claim_runs:
            if _tool_run_needs_code_state(run) and not run.code_state_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="tool_run_code_state_missing",
                        reason="tool run looks code-backed but is not linked to a code state",
                        topic_id=run.topic_id,
                        claim_id=run.claim_id,
                        target_type="tool_run",
                        target_id=run.run_id,
                        recommended_actions=["aitp.capture_code_state_auto", "aitp.record_tool_run"],
                        recommended_entrypoints=["aitp_v5_capture_code_state_auto", "aitp_v5_record_tool_run"],
                        severity="high",
                        provenance_kind="code",
                        target_record=run,
                    )
                )
            if _tool_run_needs_artifact(run) and not run.artifact_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="benchmark_artifact_missing",
                        reason="benchmark/result-like tool run has no artifact reference",
                        topic_id=run.topic_id,
                        claim_id=run.claim_id,
                        target_type="tool_run",
                        target_id=run.run_id,
                        recommended_actions=["aitp.attach_artifact_auto", "aitp.attach_artifact", "aitp.record_tool_run"],
                        recommended_entrypoints=[
                            "aitp_v5_attach_artifact_auto",
                            "aitp_v5_attach_artifact",
                            "aitp_v5_record_tool_run",
                        ],
                        severity="normal",
                        provenance_kind="artifact",
                        target_record=run,
                    )
                )
        for result in claim_results:
            if _validation_result_needs_artifact(result) and not result.artifact_ids:
                gaps.append(
                    _provenance_gap(
                        gap_type="validation_result_artifact_missing",
                        reason="validation result has no artifact reference for its checked output",
                        topic_id=result.topic_id,
                        claim_id=result.claim_id,
                        target_type="validation_result",
                        target_id=result.result_id,
                        recommended_actions=[
                            "aitp.attach_artifact_auto",
                            "aitp.attach_artifact",
                            "aitp.record_validation_result",
                        ],
                        recommended_entrypoints=[
                            "aitp_v5_attach_artifact_auto",
                            "aitp_v5_attach_artifact",
                            "aitp_v5_record_validation_result",
                        ],
                        severity="normal",
                        provenance_kind="artifact",
                        target_record=result,
                    )
                )
    return _dedupe_gaps(gaps)


def _provenance_gap(
    *,
    gap_type: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    recommended_actions: list[str],
    recommended_entrypoints: list[str],
    severity: str,
    provenance_kind: str,
    target_record: Any | None = None,
) -> dict[str, Any]:
    target_payload = _record_payload(target_record) if target_record is not None else {}
    return {
        "gap_id": f"provenance-gap:{gap_type}:{target_type}:{target_id}",
        "gap_type": gap_type,
        "provenance_kind": provenance_kind,
        "reason": reason,
        "topic_id": topic_id,
        "claim_id": claim_id,
        "target_type": target_type,
        "target_id": target_id,
        "target_refs": [f"{target_type}:{target_id}"],
        "recommended_actions": list(recommended_actions),
        "recommended_entrypoints": list(recommended_entrypoints),
        "payload_hints": _provenance_payload_hints(
            recommended_entrypoints=recommended_entrypoints,
            gap_type=gap_type,
            provenance_kind=provenance_kind,
            reason=reason,
            topic_id=topic_id,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
            target_record=target_payload,
        ),
        "severity": severity,
        "required_now": False,
        "required_before_trust_change": False,
        "strict_boundary": "before_using_as_evidence_validation_benchmark_memory_or_checked_conclusion",
        "blocking_when_used_as": [
            "evidence",
            "validation_input",
            "benchmark_basis",
            "memory_promotion_input",
            "human_facing_checked_conclusion",
        ],
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _claim_needs_code_provenance(claim: ClaimRecord) -> bool:
    text = " ".join(
        [
            claim.evidence_profile,
            claim.statement,
            claim.active_uncertainty,
            claim.recipe_id,
            claim.scope,
        ]
    ).lower()
    return any(token in text for token in ("code", "benchmark", "git", "repo", "tool", "run", "numerical"))


def _tool_run_needs_code_state(record: ToolRunRecord) -> bool:
    text = " ".join([record.recipe_id, record.tool_family, record.tool_name]).lower()
    return any(token in text for token in ("code", "python", "git", "benchmark", "runner", "numeric"))


def _tool_run_needs_artifact(record: ToolRunRecord) -> bool:
    text = " ".join(
        [
            record.recipe_id,
            record.tool_family,
            record.tool_name,
            str(record.outputs),
            record.evidence_status,
        ]
    ).lower()
    return any(token in text for token in ("benchmark", "result", "stdout", "log", "artifact", "plot", "json"))


def _validation_result_needs_artifact(record: ValidationResultRecord) -> bool:
    text = " ".join([record.summary, " ".join(record.checked_outputs)]).lower()
    return any(token in text for token in ("benchmark", "result", "log", "plot", "artifact", "json"))


def _dedupe_gaps(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("gap_type"), item.get("target_type"), item.get("target_id"))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _provenance_payload_hints(
    *,
    recommended_entrypoints: list[str],
    gap_type: str,
    provenance_kind: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    target_record: dict[str, Any],
) -> list[dict[str, Any]]:
    hints: list[dict[str, Any]] = []
    for entrypoint in recommended_entrypoints:
        hint = _provenance_payload_hint(
            entrypoint=entrypoint,
            gap_type=gap_type,
            provenance_kind=provenance_kind,
            reason=reason,
            topic_id=topic_id,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
            target_record=target_record,
        )
        if hint is not None:
            hints.append(with_draft_schema(hint))
    return hints


def _provenance_payload_hint(
    *,
    entrypoint: str,
    gap_type: str,
    provenance_kind: str,
    reason: str,
    topic_id: str,
    claim_id: str,
    target_type: str,
    target_id: str,
    target_record: dict[str, Any],
) -> dict[str, Any] | None:
    base = {
        "entrypoint": entrypoint,
        "action_kind": "capture_provenance_gap",
        "target_type": target_type,
        "target_id": target_id,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        **_provenance_lifecycle(
            entrypoint=entrypoint,
            gap_type=gap_type,
            reason=reason,
            claim_id=claim_id,
            target_type=target_type,
            target_id=target_id,
        ),
    }
    if entrypoint == "aitp_v5_record_reference_location":
        return {
            **base,
            "record_action": "record_reference_location",
            "required_fields": ["topic_id", "connector_id", "location_type", "uri", "label"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "connector_id": _placeholder("connector id"),
                    "location_type": "paper_section",
                    "uri": _placeholder("source URI"),
                    "label": _placeholder("source label"),
                    "source_ref": _source_ref_for_target(target_type, target_id),
                    "status": "located",
                    "summary": reason,
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_register_source_asset":
        return {
            **base,
            "record_action": "register_source_asset",
            "required_fields": ["topic_id", "asset_type", "uri", "title"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "asset_type": target_record.get("asset_type") or "paper",
                    "uri": target_record.get("uri") or _placeholder("source URI"),
                    "title": target_record.get("title") or target_record.get("label") or _placeholder("source title"),
                    "label": target_record.get("label") or "",
                    "content_hash": target_record.get("content_hash") or _placeholder("content hash if known"),
                    "hash_algorithm": target_record.get("hash_algorithm") or "sha256",
                    "version_anchor": target_record.get("version_anchor") or {},
                    "source_kind": target_record.get("source_kind") or "literature",
                    "summary": reason,
                    "source_refs": _string_list(target_record.get("source_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "reference_location_ids": _string_list(target_record.get("reference_location_ids")),
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_capture_source_asset_auto":
        return {
            **base,
            "record_action": "capture_source_asset_auto",
            "required_fields": ["path", "topic_id"],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local source file path"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "asset_type": target_record.get("asset_type") or "",
                    "title": target_record.get("title") or target_record.get("label") or "",
                    "label": target_record.get("label") or "",
                    "version_anchor": target_record.get("version_anchor") or {},
                    "source_kind": target_record.get("source_kind") or "local_file_auto",
                    "summary": reason,
                    "source_refs": _string_list(target_record.get("source_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "reference_location_ids": _string_list(target_record.get("reference_location_ids")),
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                }
            ),
        }
    if entrypoint in {"aitp_v5_capture_code_state_auto", "aitp_v5_record_code_state"}:
        return {
            **base,
            "record_action": "capture_code_state_auto",
            "required_fields": ["worktree_path"],
            "draft": _clean_mapping(
                {
                    "worktree_path": _placeholder("local worktree path"),
                    "repo_id": target_record.get("recipe_id") or target_record.get("tool_name") or _placeholder("repo id"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "linked_records": _linked_records(target_type, target_id, claim_id),
                    "known_divergence": reason,
                    "write_patch_artifact": True,
                }
            ),
        }
    if entrypoint == "aitp_v5_record_tool_run":
        return {
            **base,
            "record_action": "record_tool_run",
            "required_fields": ["recipe_id", "tool_family", "tool_name", "topic_id", "claim_id"],
            "draft": _clean_mapping(
                {
                    "recipe_id": target_record.get("recipe_id") or _placeholder("tool recipe id"),
                    "tool_family": target_record.get("tool_family") or _tool_family_for_gap(provenance_kind, gap_type),
                    "tool_name": target_record.get("tool_name") or _placeholder("tool name"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "inputs": target_record.get("inputs") or {},
                    "outputs": target_record.get("outputs") or {},
                    "environment": target_record.get("environment") or {},
                    "evidence_status": target_record.get("evidence_status") or "unreviewed",
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "source_refs": _source_refs_for_record(target_record, target_type, target_id),
                }
            ),
        }
    if entrypoint == "aitp_v5_capture_tool_run_auto":
        return {
            **base,
            "record_action": "capture_tool_run_auto",
            "required_fields": [
                "path",
                "recipe_id",
                "tool_family",
                "tool_name",
                "topic_id",
                "claim_id",
            ],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local tool transcript or result file path"),
                    "recipe_id": target_record.get("recipe_id") or _placeholder("tool recipe id"),
                    "tool_family": target_record.get("tool_family") or _tool_family_for_gap(provenance_kind, gap_type),
                    "tool_name": target_record.get("tool_name") or _placeholder("tool name"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "inputs": target_record.get("inputs") or {},
                    "outputs": target_record.get("outputs") or {},
                    "environment": target_record.get("environment") or {},
                    "evidence_status": target_record.get("evidence_status") or "unreviewed",
                    "code_state_ids": _string_list(target_record.get("code_state_ids")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                    "source_refs": _source_refs_for_record(target_record, target_type, target_id),
                    "summary": reason,
                }
            ),
        }
    if entrypoint == "aitp_v5_create_validation_contract":
        return {
            **base,
            "record_action": "create_validation_contract",
            "required_fields": ["topic_id", "claim_id", "required_checks", "failure_modes", "required_evidence_outputs"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "required_checks": _validation_required_checks(gap_type),
                    "failure_modes": _validation_failure_modes(gap_type),
                    "required_evidence_outputs": _validation_required_outputs(target_record, gap_type),
                    "tool_recipe_ids": _string_list(target_record.get("tool_recipe_ids")),
                    "executor_ids": _string_list(target_record.get("executor_ids")),
                    "validator_role": "adversarial_reviewer",
                }
            ),
        }
    if entrypoint == "aitp_v5_record_validation_result":
        return {
            **base,
            "record_action": "record_validation_result",
            "required_fields": ["topic_id", "claim_id", "contract_id", "tool_run_id", "status", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "contract_id": target_record.get("contract_id") or _placeholder("validation contract id"),
                    "tool_run_id": target_record.get("tool_run_id") or _placeholder("tool run id"),
                    "status": target_record.get("status") or "partial",
                    "summary": target_record.get("summary") or reason,
                    "checked_outputs": _string_list(target_record.get("checked_outputs")),
                    "covered_failure_modes": _string_list(target_record.get("covered_failure_modes")),
                    "failure_modes_observed": _string_list(target_record.get("failure_modes_observed")),
                    "evidence_refs": _string_list(target_record.get("evidence_refs")),
                    "artifact_ids": _string_list(target_record.get("artifact_ids")),
                }
            ),
        }
    if entrypoint == "aitp_v5_attach_artifact":
        return {
            **base,
            "record_action": "attach_artifact",
            "required_fields": ["topic_id", "claim_id", "artifact_type", "uri", "summary"],
            "draft": _clean_mapping(
                {
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "artifact_type": _artifact_type_for_gap(gap_type),
                    "uri": _placeholder("artifact URI"),
                    "summary": reason,
                    "metadata": {
                        "target_type": target_type,
                        "target_id": target_id,
                        "provenance_kind": provenance_kind,
                    },
                }
            ),
        }
    if entrypoint == "aitp_v5_attach_artifact_auto":
        return {
            **base,
            "record_action": "attach_artifact_auto",
            "required_fields": ["path", "topic_id", "claim_id", "artifact_type", "summary"],
            "draft": _clean_mapping(
                {
                    "path": _placeholder("local artifact file path"),
                    "topic_id": topic_id,
                    "claim_id": claim_id,
                    "artifact_type": _artifact_type_for_gap(gap_type),
                    "summary": reason,
                    "metadata": {
                        "target_type": target_type,
                        "target_id": target_id,
                        "provenance_kind": provenance_kind,
                    },
                }
            ),
        }
    return None


def _provenance_lifecycle(
    *,
    entrypoint: str,
    gap_type: str,
    reason: str,
    claim_id: str,
    target_type: str,
    target_id: str,
) -> dict[str, Any]:
    return {
        "lifecycle_phases": ["pre_action"],
        "trigger_conditions": [
            reason,
            "before using the target as evidence, validation input, benchmark basis, memory promotion input, or checked conclusion",
        ],
        "recording_threshold": "recommended_before_provenance_dependent_reuse",
        "trust_boundary_inputs": {
            "target_refs": [f"{target_type}:{target_id}"],
            "claim_id": claim_id,
            "entrypoints": [entrypoint],
            "required_before_trust_change": [],
            "requires_preflight": False,
            "final_gate_required": False,
        },
        "recommended_host_behavior": [
            "surface this provenance payload hint as an orientation-only AITP write draft",
            f"call {entrypoint} only after replacing placeholders with real typed provenance",
        ],
    }


def _linked_records(target_type: str, target_id: str, claim_id: str) -> dict[str, str]:
    result = {"target_type": target_type, "target_id": target_id}
    if claim_id:
        result["claim_id"] = claim_id
    return result


def _source_ref_for_target(target_type: str, target_id: str) -> str:
    return f"{target_type}:{target_id}" if target_type and target_id else ""


def _source_refs_for_record(record: dict[str, Any], target_type: str, target_id: str) -> list[str]:
    refs = _string_list(record.get("source_refs"))
    target_ref = _source_ref_for_target(target_type, target_id)
    if target_ref and target_ref not in refs:
        refs.append(target_ref)
    return refs


def _tool_family_for_gap(provenance_kind: str, gap_type: str) -> str:
    if "benchmark" in gap_type:
        return "benchmark"
    if provenance_kind == "code":
        return "code"
    return "research_tool"


def _validation_required_checks(gap_type: str) -> list[str]:
    if "code" in gap_type or "benchmark" in gap_type or "validation_contract" in gap_type:
        return ["reproduce command/run provenance", "check expected outputs", "capture artifact or log"]
    return ["check required outputs", "check source/provenance basis"]


def _validation_failure_modes(gap_type: str) -> list[str]:
    if "code" in gap_type or "benchmark" in gap_type or "validation_contract" in gap_type:
        return ["uncaptured code state", "missing benchmark artifact", "unreviewed tool output"]
    return ["missing evidence output", "unreviewed validation basis"]


def _validation_required_outputs(record: dict[str, Any], gap_type: str) -> list[str]:
    checked = _string_list(record.get("checked_outputs"))
    if checked:
        return checked
    if "benchmark" in gap_type:
        return ["benchmark result artifact", "tool-run transcript"]
    return ["typed evidence output"]


def _artifact_type_for_gap(gap_type: str) -> str:
    if "benchmark" in gap_type:
        return "benchmark_log"
    if "validation" in gap_type:
        return "validation_artifact"
    return "provenance_artifact"


def _placeholder(label: str) -> str:
    return f"<{label}>"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _clean_mapping(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if item is None or item == "" or item == [] or item == {}:
            continue
        result[key] = item
    return result


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
        "topic_id": record.topic_id,
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
