"""Thin MCP-facing wrappers around the AITP v5 kernel."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.adapter_protocols import adapter_protocol_registry
from brain.v5.adapters import build_adapter_packet
from brain.v5.brief import build_execution_brief
from brain.v5.code import record_code_state
from brain.v5.evidence import record_evidence
from brain.v5.knowledge_connectors import describe_knowledge_connectors
from brain.v5.models import CodeStateRecord, TrustUpdateRequest
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.references import record_reference_location
from brain.v5.risk import assess_claim_risk
from brain.v5.store import list_records
from brain.v5.summaries import read_summary_orientation, write_session_summary
from brain.v5.tool_executors import describe_tool_executors, execute_registered_tool_result
from brain.v5.tools import record_tool_run, register_tool_recipe
from brain.v5.trust_updates import apply_trust_update, preflight_trust_update
from brain.v5.workspace import (
    bind_session,
    create_claim,
    create_topic,
    get_claim,
    init_workspace,
)


def aitp_v5_init_workspace(base: str) -> dict:
    ws = init_workspace(Path(base))
    return {"ok": True, "workspace_root": str(ws.root)}


def aitp_v5_create_topic(base: str, *, topic_id: str, context_id: str, title: str) -> dict:
    ws = init_workspace(Path(base))
    return {"ok": True, **asdict(create_topic(ws, topic_id, context_id=context_id, title=title))}


def aitp_v5_create_claim(
    base: str,
    *,
    topic_id: str,
    statement: str,
    evidence_profile: str,
    confidence_state: str,
    active_uncertainty: str,
    recipe_id: str = "",
    scope: str = "",
    non_claims: str = "",
    strongest_failure_mode: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    claim = create_claim(
        ws,
        topic_id=topic_id,
        statement=statement,
        evidence_profile=evidence_profile,
        confidence_state=confidence_state,
        active_uncertainty=active_uncertainty,
        recipe_id=recipe_id,
        scope=scope,
        non_claims=non_claims,
        strongest_failure_mode=strongest_failure_mode,
    )
    return {"ok": True, **asdict(claim)}


def aitp_v5_bind_session(
    base: str,
    *,
    session_id: str,
    topic_id: str,
    context_id: str,
    active_claim: str = "",
    interaction_profile: str = "collaborator",
    interaction_steering: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    session = bind_session(
        ws,
        session_id,
        topic_id=topic_id,
        context_id=context_id,
        active_claim=active_claim,
        interaction_profile=interaction_profile,
        interaction_steering=interaction_steering,
    )
    return {"ok": True, **asdict(session)}


def aitp_v5_get_execution_brief(base: str, *, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return require_valid_public_surface("execution_brief", build_execution_brief(ws, session_id))


def aitp_v5_assess_risk(base: str, *, claim_id: str) -> dict:
    ws = init_workspace(Path(base))
    claim = get_claim(ws, claim_id)
    assessment = assess_claim_risk(claim, code_states=_linked_code_states(ws, claim_id))
    return {"ok": True, "claim_id": claim_id, "risk_assessment": asdict(assessment)}


def aitp_v5_record_code_state(
    base: str,
    *,
    repo_id: str,
    upstream_remote: str,
    upstream_branch: str,
    upstream_commit: str,
    local_branch: str,
    worktree_path: str,
    dirty: bool,
    patch_id: str = "",
    diff_hash: str = "",
    build_config: dict | None = None,
    runtime_environment: dict | None = None,
    linked_records: dict | None = None,
    known_divergence: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    state = record_code_state(
        ws,
        repo_id=repo_id,
        upstream_remote=upstream_remote,
        upstream_branch=upstream_branch,
        upstream_commit=upstream_commit,
        local_branch=local_branch,
        worktree_path=worktree_path,
        dirty=dirty,
        patch_id=patch_id,
        diff_hash=diff_hash,
        build_config=build_config,
        runtime_environment=runtime_environment,
        linked_records=linked_records,
        known_divergence=known_divergence,
    )
    return require_valid_public_surface("code_state_record", {"ok": True, **asdict(state)})


def aitp_v5_record_evidence(
    base: str,
    *,
    topic_id: str,
    claim_id: str,
    evidence_type: str,
    status: str,
    summary: str,
    supports_outputs: list[str] | None = None,
    source_refs: list[str] | None = None,
    tool_run_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
) -> dict:
    ws = init_workspace(Path(base))
    evidence = record_evidence(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        evidence_type=evidence_type,
        status=status,
        summary=summary,
        supports_outputs=supports_outputs,
        source_refs=source_refs,
        tool_run_ids=tool_run_ids,
        artifact_ids=artifact_ids,
    )
    return require_valid_public_surface("evidence_record", {"ok": True, **asdict(evidence)})


def aitp_v5_register_tool_recipe(
    base: str,
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    purpose: str,
    required_inputs: list[str] | None = None,
    expected_outputs: list[str] | None = None,
    invariants: list[str] | None = None,
) -> dict:
    ws = init_workspace(Path(base))
    recipe = register_tool_recipe(
        ws,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        purpose=purpose,
        required_inputs=required_inputs,
        expected_outputs=expected_outputs,
        invariants=invariants,
    )
    return require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(recipe)})


def aitp_v5_record_tool_run(
    base: str,
    *,
    recipe_id: str,
    tool_family: str,
    tool_name: str,
    topic_id: str,
    claim_id: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
    environment: dict | None = None,
    evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> dict:
    ws = init_workspace(Path(base))
    run = record_tool_run(
        ws,
        recipe_id=recipe_id,
        tool_family=tool_family,
        tool_name=tool_name,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        outputs=outputs,
        environment=environment,
        evidence_status=evidence_status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
    )
    return require_valid_public_surface("tool_run_record", {"ok": True, **asdict(run)})


def aitp_v5_execute_tool(
    base: str,
    *,
    executor_id: str,
    recipe_id: str,
    topic_id: str,
    claim_id: str,
    inputs: dict,
    evidence_status: str = "",
    code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
    supports_outputs: list[str] | None = None,
    evidence_type: str = "tool_run",
    evidence_summary: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    result = execute_registered_tool_result(
        ws,
        executor_id=executor_id,
        recipe_id=recipe_id,
        topic_id=topic_id,
        claim_id=claim_id,
        inputs=inputs,
        evidence_status=evidence_status,
        code_state_ids=code_state_ids,
        artifact_ids=artifact_ids,
        source_refs=source_refs,
        supports_outputs=supports_outputs,
        evidence_type=evidence_type,
        evidence_summary=evidence_summary,
    )
    payload = {"ok": True, **asdict(result.run)}
    if result.evidence is not None:
        evidence = require_valid_public_surface("evidence_record", {"ok": True, **asdict(result.evidence)})
        payload["evidence_id"] = result.evidence.evidence_id
        payload["evidence"] = evidence
    return require_valid_public_surface("tool_run_record", payload)


def aitp_v5_list_tool_executors() -> dict:
    return require_valid_public_surface("tool_executor_catalog", describe_tool_executors())


def aitp_v5_list_knowledge_connectors() -> dict:
    return require_valid_public_surface("knowledge_connector_catalog", describe_knowledge_connectors())


def aitp_v5_record_reference_location(
    base: str,
    *,
    topic_id: str,
    connector_id: str,
    location_type: str,
    uri: str,
    label: str,
    claim_id: str = "",
    source_ref: str = "",
    external_id: str = "",
    status: str = "located",
    summary: str = "",
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    ws = init_workspace(Path(base))
    location = record_reference_location(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        connector_id=connector_id,
        location_type=location_type,
        uri=uri,
        label=label,
        source_ref=source_ref,
        external_id=external_id,
        status=status,
        summary=summary,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("reference_location_record", {"ok": True, **asdict(location)})


def aitp_v5_write_session_summary(base: str, *, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return {
        "ok": True,
        **require_valid_public_surface(
            "session_summary_bundle",
            asdict(write_session_summary(ws, session_id)),
        ),
    }


def aitp_v5_read_summary_orientation(base: str, *, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return {"ok": True, **require_valid_public_surface("summary_orientation", read_summary_orientation(ws, session_id))}


def aitp_v5_get_adapter_packet(base: str, *, runtime: str, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return {
        "ok": True,
        **require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime=runtime)),
    }


def aitp_v5_get_adapter_protocol_registry() -> dict:
    return {
        "ok": True,
        "adapter_protocol_registry": require_valid_public_surface(
            "adapter_protocol_registry",
            adapter_protocol_registry(),
        ),
    }


def aitp_v5_describe_public_surfaces() -> dict:
    return {"ok": True, "public_surfaces": describe_public_surfaces()}


def aitp_v5_record_physics_object(
    base: str,
    *,
    topic_id: str,
    object_type: str,
    name: str,
    definition: str,
    notation: str = "",
    assumptions: list[str] | None = None,
    source_refs: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    status: str = "active",
) -> dict:
    ws = init_workspace(Path(base))
    obj = record_physics_object(
        ws,
        topic_id=topic_id,
        object_type=object_type,
        name=name,
        definition=definition,
        notation=notation,
        assumptions=assumptions,
        source_refs=source_refs,
        metadata=metadata,
        linked_records=linked_records,
        status=status,
    )
    return require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})


def aitp_v5_record_object_relation(
    base: str,
    *,
    topic_id: str,
    relation_type: str,
    subject_id: str,
    object_id: str,
    statement: str,
    claim_id: str = "",
    assumptions: list[str] | None = None,
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    metadata: dict | None = None,
    status: str = "hypothesis",
) -> dict:
    ws = init_workspace(Path(base))
    rel = record_object_relation(
        ws, topic_id=topic_id, relation_type=relation_type, subject_id=subject_id,
        object_id=object_id, statement=statement, claim_id=claim_id, assumptions=assumptions,
        failure_modes=failure_modes, source_refs=source_refs, evidence_refs=evidence_refs,
        metadata=metadata, status=status,
    )
    return require_valid_public_surface("object_relation_record", {"ok": True, **asdict(rel)})


def aitp_v5_preflight_trust_update(
    base: str,
    *,
    action: str,
    session_id: str,
    topic_id: str,
    claim_id: str,
    requested_state: str = "",
    source_kind: str = "",
    source_ref: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    rationale: str = "",
    request_id: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    resolved_request_id = request_id or f"trust-request-{session_id}-{claim_id}-{action}"
    request = TrustUpdateRequest(
        request_id=resolved_request_id,
        action=action,
        session_id=session_id,
        topic_id=topic_id,
        claim_id=claim_id,
        requested_state=requested_state,
        source_kind=source_kind,
        source_ref=source_ref,
        evidence_refs=evidence_refs or [],
        code_state_ids=code_state_ids or [],
        rationale=rationale,
    )
    return {"ok": True, **require_valid_public_surface("trust_update_preflight", preflight_trust_update(ws, request))}


def aitp_v5_apply_trust_update(
    base: str,
    *,
    action: str,
    session_id: str,
    topic_id: str,
    claim_id: str,
    requested_state: str = "",
    source_kind: str = "",
    source_ref: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    rationale: str = "",
    request_id: str = "",
) -> dict:
    ws = init_workspace(Path(base))
    resolved_request_id = request_id or f"trust-request-{session_id}-{claim_id}-{action}"
    request = TrustUpdateRequest(
        request_id=resolved_request_id,
        action=action,
        session_id=session_id,
        topic_id=topic_id,
        claim_id=claim_id,
        requested_state=requested_state,
        source_kind=source_kind,
        source_ref=source_ref,
        evidence_refs=evidence_refs or [],
        code_state_ids=code_state_ids or [],
        rationale=rationale,
    )
    return {"ok": True, **require_valid_public_surface("trust_update_apply", apply_trust_update(ws, request))}


def _linked_code_states(ws, claim_id: str) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [state for state in states if _record_links_to_claim(state.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id:
            return True
        if isinstance(value, list) and claim_id in value:
            return True
    return False
