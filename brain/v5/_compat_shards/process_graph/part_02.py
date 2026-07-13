# Compatibility shard 2 for process_graph.
from __future__ import annotations

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
    authorities: list[AuthorityRecord],
    quiet_checkpoints: list[QuietCheckpointBatchRecord],
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
    for record in authorities:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "authority", record.authority_id, "has_authority")
    for record in quiet_checkpoints:
        if record.claim_id:
            builder.add_edge("claim", record.claim_id, "quiet_checkpoint", record.checkpoint_id, "has_quiet_checkpoint")
        if record.session_id:
            builder.add_edge("session", record.session_id, "quiet_checkpoint", record.checkpoint_id, "recorded_quiet_checkpoint")
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
    return list_records(ws.registry_dir(family), cls)

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

def _filter_authorities(records: list[AuthorityRecord], topic_id: str, claim_ids: set[str]) -> list[AuthorityRecord]:
    return [
        record
        for record in records
        if record.topic_id == topic_id and (not claim_ids or not record.claim_id or record.claim_id in claim_ids)
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
