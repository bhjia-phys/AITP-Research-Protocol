# Compatibility shard 1 for process_graph.
from __future__ import annotations

from dataclasses import asdict, is_dataclass

from typing import Any

from brain.v5.models import (
    AuthorityRecord,
    ClaimRecord,
    CodeStateRecord,
    EvidenceRecord,
    ExploratoryRecord,
    HumanCheckpointRecord,
    MemoryEntryRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ProofObligationRecord,
    QuietCheckpointBatchRecord,
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

from brain.v5.store import list_records

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
    authorities = _filter_authorities(_records(ws, "authorities", AuthorityRecord), topic_id, claim_ids)
    quiet_checkpoints = _filter_by_topic_and_claim(_records(ws, "quiet_checkpoints", QuietCheckpointBatchRecord), topic_id, claim_ids)
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
        for record in list_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
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
    for record in authorities:
        builder.add_node("authority", record.authority_id, record, label=record.authority_statement)
    for record in quiet_checkpoints:
        builder.add_node("quiet_checkpoint", record.checkpoint_id, record, label=record.summary)
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
    _add_edges(builder, session, claims, references, source_assets, evidence, obligations, authorities, quiet_checkpoints, objects, relations,
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
