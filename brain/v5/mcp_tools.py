"""Thin MCP-facing wrappers around the AITP v5 kernel."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.adapter_protocols import adapter_protocol_registry, record_gate_coverage_audit
from brain.v5.adapter_runtime import evaluate_platform_pre_tool_event
from brain.v5.adapters import build_adapter_packet
from brain.v5.brief import build_execution_brief
from brain.v5.code import record_code_state
from brain.v5.final_readiness import audit_final_engineering_readiness
from brain.v5.hook_install_audit import audit_hook_installation
from brain.v5.hook_install_paths import discover_hook_install_paths
from brain.v5.hook_install_templates import (
    install_claude_code_hook_settings,
    write_claude_code_hook_settings,
    write_codex_hook_bridge,
    write_opencode_plugin_bridge,
)
from brain.v5.mcp_kimi_hooks import aitp_v5_install_kimi_code_hook_config, aitp_v5_write_kimi_code_hook_config
from brain.v5.mcp_legacy import aitp_v5_apply_legacy_semantic_repair, aitp_v5_audit_legacy_migration_coverage, aitp_v5_build_legacy_l2_graph_manifest, aitp_v5_build_legacy_semantic_repair_plan, aitp_v5_build_legacy_semantic_review_manifest, aitp_v5_build_legacy_semantic_review_packet, aitp_v5_build_legacy_semantic_review_queue, aitp_v5_migrate_legacy_topic_to_v5, aitp_v5_record_legacy_semantic_review_result
from brain.v5.hook_smoke_coverage import runtime_hook_smoke_coverage_report
from brain.v5.knowledge_connectors import describe_knowledge_connectors
from brain.v5.models import CodeStateRecord, TrustUpdateRequest
from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
from brain.v5.public_surfaces import describe_public_surfaces, require_valid_public_surface
from brain.v5.physics_objects import record_object_relation, record_physics_object
from brain.v5.references import record_reference_location
from brain.v5.sensemaking import record_sensemaking_report
from brain.v5.validation import create_validation_contract, record_validation_result
from brain.v5.checkpoints import decide_human_checkpoint, request_human_checkpoint
from brain.v5.memory import apply_promotion_packet, create_promotion_packet
from brain.v5.mcp_evidence import aitp_v5_record_evidence
from brain.v5.mcp_host_readiness import aitp_v5_audit_runtime_host_lifecycle, aitp_v5_audit_runtime_host_readiness
from brain.v5.mcp_hook_install import aitp_v5_install_codex_hook_fixture, aitp_v5_install_opencode_hook_fixture
from brain.v5.mcp_interaction import aitp_v5_preview_interaction_recording
from brain.v5.mcp_memory import aitp_v5_audit_failure_mode_coverage, aitp_v5_audit_l2_memory_context, aitp_v5_build_failure_mode_review_packet, aitp_v5_record_failure_mode_review_result, aitp_v5_request_failure_mode_review_checkpoint, aitp_v5_write_l2_obsidian_view
from brain.v5.mcp_source import aitp_v5_audit_source_reconstruction, aitp_v5_build_source_reconstruction_manifest
from brain.v5.mcp_summaries import aitp_v5_read_summary_orientation, aitp_v5_refresh_workspace_views, aitp_v5_write_session_summary, aitp_v5_write_workspace_replay_packet, aitp_v5_write_workspace_summary
from brain.v5.mcp_trust_audit import aitp_v5_audit_claim_trust
from brain.v5.risk import assess_claim_risk
from brain.v5.store import list_records
from brain.v5.subagents import ingest_subagent_result
from brain.v5.tool_executors import describe_tool_executors, execute_registered_tool_result
from brain.v5.tools import record_tool_run, register_tool_recipe
from brain.v5.trace import persist_hook_trace_event
from brain.v5.trust_updates import apply_trust_update, get_trust_update_record, preflight_trust_update
from brain.v5.workspace import bind_session, create_claim, create_topic, get_claim, init_workspace


def _ws(base: str):
    return init_workspace(Path(base))


def aitp_v5_init_workspace(base: str) -> dict:
    return {"ok": True, "workspace_root": str(_ws(base).root)}


def aitp_v5_create_topic(base: str, *, topic_id: str, context_id: str, title: str) -> dict:
    return {"ok": True, **asdict(create_topic(_ws(base), topic_id, context_id=context_id, title=title))}


def aitp_v5_create_claim(
    base: str, *, topic_id: str, statement: str, evidence_profile: str,
    confidence_state: str, active_uncertainty: str, recipe_id: str = "",
    scope: str = "", non_claims: str = "", strongest_failure_mode: str = "",
) -> dict:
    claim = create_claim(_ws(base), topic_id=topic_id, statement=statement,
        evidence_profile=evidence_profile, confidence_state=confidence_state,
        active_uncertainty=active_uncertainty, recipe_id=recipe_id,
        scope=scope, non_claims=non_claims, strongest_failure_mode=strongest_failure_mode)
    return {"ok": True, **asdict(claim)}


def aitp_v5_bind_session(
    base: str, *, session_id: str, topic_id: str, context_id: str,
    active_claim: str = "", interaction_profile: str = "collaborator", interaction_steering: str = "",
) -> dict:
    session = bind_session(_ws(base), session_id, topic_id=topic_id, context_id=context_id,
        active_claim=active_claim, interaction_profile=interaction_profile,
        interaction_steering=interaction_steering)
    return {"ok": True, **asdict(session)}


def aitp_v5_get_execution_brief(base: str, *, session_id: str) -> dict:
    return require_valid_public_surface("execution_brief", build_execution_brief(_ws(base), session_id))


def aitp_v5_assess_risk(base: str, *, claim_id: str) -> dict:
    ws = _ws(base); claim = get_claim(ws, claim_id)
    return {"ok": True, "claim_id": claim_id, "risk_assessment": asdict(assess_claim_risk(claim, code_states=_linked_code_states(ws, claim_id)))}


def aitp_v5_record_code_state(
    base: str, *, repo_id: str, upstream_remote: str, upstream_branch: str,
    upstream_commit: str, local_branch: str, worktree_path: str, dirty: bool,
    patch_id: str = "", diff_hash: str = "", build_config: dict | None = None,
    runtime_environment: dict | None = None, linked_records: dict | None = None,
    known_divergence: str = "",
) -> dict:
    state = record_code_state(_ws(base), repo_id=repo_id, upstream_remote=upstream_remote,
        upstream_branch=upstream_branch, upstream_commit=upstream_commit,
        local_branch=local_branch, worktree_path=worktree_path, dirty=dirty,
        patch_id=patch_id, diff_hash=diff_hash, build_config=build_config,
        runtime_environment=runtime_environment, linked_records=linked_records,
        known_divergence=known_divergence)
    return require_valid_public_surface("code_state_record", {"ok": True, **asdict(state)})


def aitp_v5_register_tool_recipe(
    base: str, *, recipe_id: str, tool_family: str, tool_name: str, purpose: str,
    required_inputs: list[str] | None = None, expected_outputs: list[str] | None = None,
    invariants: list[str] | None = None,
) -> dict:
    recipe = register_tool_recipe(_ws(base), recipe_id=recipe_id, tool_family=tool_family,
        tool_name=tool_name, purpose=purpose, required_inputs=required_inputs,
        expected_outputs=expected_outputs, invariants=invariants)
    return require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(recipe)})


def aitp_v5_record_tool_run(
    base: str, *, recipe_id: str, tool_family: str, tool_name: str, topic_id: str,
    claim_id: str, inputs: dict | None = None, outputs: dict | None = None,
    environment: dict | None = None, evidence_status: str = "unreviewed",
    code_state_ids: list[str] | None = None, artifact_ids: list[str] | None = None,
    source_refs: list[str] | None = None,
) -> dict:
    run = record_tool_run(_ws(base), recipe_id=recipe_id, tool_family=tool_family,
        tool_name=tool_name, topic_id=topic_id, claim_id=claim_id, inputs=inputs,
        outputs=outputs, environment=environment, evidence_status=evidence_status,
        code_state_ids=code_state_ids, artifact_ids=artifact_ids, source_refs=source_refs)
    return require_valid_public_surface("tool_run_record", {"ok": True, **asdict(run)})


def aitp_v5_execute_tool(
    base: str, *, executor_id: str, recipe_id: str, topic_id: str, claim_id: str,
    inputs: dict, evidence_status: str = "", code_state_ids: list[str] | None = None,
    artifact_ids: list[str] | None = None, source_refs: list[str] | None = None,
    supports_outputs: list[str] | None = None, evidence_type: str = "tool_run",
    evidence_summary: str = "",
) -> dict:
    result = execute_registered_tool_result(_ws(base), executor_id=executor_id,
        recipe_id=recipe_id, topic_id=topic_id, claim_id=claim_id, inputs=inputs,
        evidence_status=evidence_status, code_state_ids=code_state_ids,
        artifact_ids=artifact_ids, source_refs=source_refs, supports_outputs=supports_outputs,
        evidence_type=evidence_type, evidence_summary=evidence_summary)
    payload = {"ok": True, **asdict(result.run)}
    if result.evidence is not None:
        payload["evidence_id"] = result.evidence.evidence_id
        payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **asdict(result.evidence)})
    return require_valid_public_surface("tool_run_record", payload)


def aitp_v5_list_tool_executors() -> dict:
    return require_valid_public_surface("tool_executor_catalog", describe_tool_executors())


def aitp_v5_list_knowledge_connectors() -> dict:
    return require_valid_public_surface("knowledge_connector_catalog", describe_knowledge_connectors())

def aitp_v5_persist_hook_trace_event(base: str, *, hook_payload: dict) -> dict:
    return require_valid_public_surface("hook_trace_event_record", persist_hook_trace_event(_ws(base), hook_payload))


def aitp_v5_record_reference_location(
    base: str, *, topic_id: str, connector_id: str, location_type: str, uri: str,
    label: str, claim_id: str = "", source_ref: str = "", external_id: str = "",
    status: str = "located", summary: str = "", metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    loc = record_reference_location(_ws(base), topic_id=topic_id, claim_id=claim_id,
        connector_id=connector_id, location_type=location_type, uri=uri, label=label,
        source_ref=source_ref, external_id=external_id, status=status, summary=summary,
        metadata=metadata, linked_records=linked_records)
    return require_valid_public_surface("reference_location_record", {"ok": True, **asdict(loc)})


def aitp_v5_get_adapter_packet(base: str, *, runtime: str, session_id: str) -> dict:
    return {"ok": True, **require_valid_public_surface("adapter_packet", build_adapter_packet(_ws(base), session_id, runtime=runtime))}


def aitp_v5_write_codex_hook_bridge(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="codex"))
    bridge = {
        "ok": True,
        **write_codex_hook_bridge(
            output_path,
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
            session_id=session_id,
        ),
    }
    return require_valid_public_surface("codex_hook_bridge", bridge)


def aitp_v5_write_opencode_plugin_bridge(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="opencode"))
    bridge = {
        "ok": True,
        **write_opencode_plugin_bridge(
            output_path,
            packet["runtime_hook_installation"],
            packet["runtime_gate_protocols"],
            session_id=session_id,
        ),
    }
    return require_valid_public_surface("opencode_plugin_bridge", bridge)


def aitp_v5_write_claude_code_hook_settings(base: str, *, session_id: str, output_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="claude_code"))
    settings = {"ok": True, **write_claude_code_hook_settings(
        output_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("claude_code_hook_settings", settings)


def aitp_v5_evaluate_adapter_pre_tool_event(
    base: str, *, bridge_payload: dict, platform_event: dict,
) -> dict:
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_platform_pre_tool_event(_ws(base), bridge_payload, platform_event),
    )


def aitp_v5_install_claude_code_hook_settings(base: str, *, session_id: str, settings_path: str) -> dict:
    ws = _ws(base)
    packet = require_valid_public_surface("adapter_packet", build_adapter_packet(ws, session_id, runtime="claude_code"))
    installed = {"ok": True, **install_claude_code_hook_settings(
        settings_path, packet["runtime_hook_installation"], workspace_base=str(ws.base), session_id=session_id)}
    return require_valid_public_surface("claude_code_hook_installation", installed)


def aitp_v5_get_adapter_protocol_registry() -> dict:
    return {"ok": True, "adapter_protocol_registry": require_valid_public_surface("adapter_protocol_registry", adapter_protocol_registry())}


def aitp_v5_audit_record_gate_coverage() -> dict:
    return {
        "ok": True,
        "record_gate_coverage_audit": require_valid_public_surface(
            "record_gate_coverage_audit",
            record_gate_coverage_audit(),
        ),
    }


def aitp_v5_audit_hook_installation(
    base: str,
    *,
    runtime: str,
    settings_path: str = "",
    plugin_path: str = "",
    output_path: str = "",
) -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "runtime_hook_installation_audit",
            audit_hook_installation(
                _ws(base),
                runtime=runtime,
                settings_path=settings_path,
                plugin_path=plugin_path,
                output_path=output_path,
            ),
        ),
    }


def aitp_v5_discover_hook_install_paths(base: str) -> dict:
    return {
        "ok": True,
        **require_valid_public_surface("runtime_hook_installation_paths", discover_hook_install_paths(_ws(base))),
    }


def aitp_v5_report_hook_smoke_coverage() -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "runtime_hook_smoke_coverage",
            runtime_hook_smoke_coverage_report(),
        ),
    }


def aitp_v5_audit_final_engineering_readiness(base: str, *, migration_dir: str = "") -> dict:
    return {
        "ok": True,
        **require_valid_public_surface(
            "final_engineering_readiness_audit",
            audit_final_engineering_readiness(_ws(base), migration_dir=migration_dir or None),
        ),
    }


def aitp_v5_describe_public_surfaces() -> dict:
    return {"ok": True, "public_surfaces": describe_public_surfaces()}


def aitp_v5_evaluate_pre_tool_policy(
    base: str, *, session_id: str, action: str, claim_id: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    validation_contract_ids: list[str] | None = None,
    tool_run_ids: list[str] | None = None, validation_result_ids: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
    recipe_id: str = "", executor_id: str = "",
    source_kind: str = "", source_ref: str = "", orientation_only: bool = False,
    risk_level: str = "guided", human_checkpoint_id: str = "",
    failure_mode_review_checkpoint_id: str = "", failure_mode_review_result_id: str = "",
) -> dict:
    return require_valid_public_surface("pre_tool_policy_decision", evaluate_context_pre_tool_policy(
        _ws(base), session_id=session_id, action=action, claim_id=claim_id,
        evidence_refs=evidence_refs, code_state_ids=code_state_ids,
        validation_contract_ids=validation_contract_ids,
        tool_run_ids=tool_run_ids, validation_result_ids=validation_result_ids,
        known_failure_modes=known_failure_modes,
        recipe_id=recipe_id, executor_id=executor_id,
        source_kind=source_kind, source_ref=source_ref, orientation_only=orientation_only,
        risk_level=risk_level, human_checkpoint_id=human_checkpoint_id,
        failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id, failure_mode_review_result_id=failure_mode_review_result_id))


def aitp_v5_record_physics_object(
    base: str, *, topic_id: str, object_type: str, name: str, definition: str,
    notation: str = "", assumptions: list[str] | None = None, source_refs: list[str] | None = None,
    metadata: dict | None = None, linked_records: dict | None = None, status: str = "active",
) -> dict:
    obj = record_physics_object(_ws(base), topic_id=topic_id, object_type=object_type,
        name=name, definition=definition, notation=notation, assumptions=assumptions,
        source_refs=source_refs, metadata=metadata, linked_records=linked_records, status=status)
    return require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})


def aitp_v5_record_object_relation(
    base: str, *, topic_id: str, relation_type: str, subject_id: str, object_id: str,
    statement: str, claim_id: str = "", assumptions: list[str] | None = None,
    failure_modes: list[str] | None = None, source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None, metadata: dict | None = None, status: str = "hypothesis",
) -> dict:
    rel = record_object_relation(_ws(base), topic_id=topic_id, relation_type=relation_type,
        subject_id=subject_id, object_id=object_id, statement=statement, claim_id=claim_id,
        assumptions=assumptions, failure_modes=failure_modes, source_refs=source_refs,
        evidence_refs=evidence_refs, metadata=metadata, status=status)
    return require_valid_public_surface("object_relation_record", {"ok": True, **asdict(rel)})


def aitp_v5_record_sensemaking_report(
    base: str, *, topic_id: str, claim_id: str, title: str, summary: str,
    object_ids: list[str] | None = None, relation_ids: list[str] | None = None,
    evidence_refs: list[str] | None = None, open_questions: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> dict:
    report = record_sensemaking_report(_ws(base), topic_id=topic_id, claim_id=claim_id,
        title=title, summary=summary, object_ids=object_ids, relation_ids=relation_ids,
        evidence_refs=evidence_refs, open_questions=open_questions, next_actions=next_actions)
    return require_valid_public_surface("sensemaking_report_record", {"ok": True, **asdict(report)})


def aitp_v5_ingest_subagent_result(
    base: str, *, topic_id: str, packet: dict, result_payload: dict,
) -> dict:
    result = ingest_subagent_result(
        _ws(base),
        packet,
        topic_id=topic_id,
        result_payload=result_payload,
    )
    payload = result.to_payload()
    payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **payload["evidence"]})
    payload["proposal"] = require_valid_public_surface("sensemaking_report_record", {"ok": True, **payload["proposal"]})
    return {"ok": True, **payload}


def aitp_v5_create_validation_contract(
    base: str, *, topic_id: str, claim_id: str,
    required_checks: list[str] | None = None, failure_modes: list[str] | None = None,
    required_evidence_outputs: list[str] | None = None,
    tool_recipe_ids: list[str] | None = None, executor_ids: list[str] | None = None,
    validator_role: str = "adversarial_reviewer",
) -> dict:
    contract = create_validation_contract(_ws(base), topic_id=topic_id, claim_id=claim_id,
        required_checks=required_checks, failure_modes=failure_modes,
        required_evidence_outputs=required_evidence_outputs,
        tool_recipe_ids=tool_recipe_ids, executor_ids=executor_ids,
        validator_role=validator_role)
    return require_valid_public_surface("validation_contract_record", {"ok": True, **asdict(contract)})


def aitp_v5_record_validation_result(
    base: str, *, topic_id: str, claim_id: str, contract_id: str, tool_run_id: str,
    status: str, checked_outputs: list[str] | None = None, summary: str = "",
    evidence_refs: list[str] | None = None, artifact_ids: list[str] | None = None,
    covered_failure_modes: list[str] | None = None,
    failure_modes_observed: list[str] | None = None,
) -> dict:
    result = record_validation_result(_ws(base), topic_id=topic_id, claim_id=claim_id,
        contract_id=contract_id, tool_run_id=tool_run_id, status=status,
        checked_outputs=checked_outputs, summary=summary, evidence_refs=evidence_refs,
        artifact_ids=artifact_ids, covered_failure_modes=covered_failure_modes,
        failure_modes_observed=failure_modes_observed)
    return require_valid_public_surface("validation_result_record", {"ok": True, **asdict(result)})


def aitp_v5_request_human_checkpoint(
    base: str, *, topic_id: str, claim_id: str, reason: str, requested_by: str,
    options: list[str] | None = None,
) -> dict:
    chk = request_human_checkpoint(_ws(base), topic_id=topic_id, claim_id=claim_id,
        reason=reason, requested_by=requested_by, options=options)
    return require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(chk)})


def aitp_v5_decide_human_checkpoint(
    base: str, *, checkpoint_id: str, decision: str, rationale: str, decided_by: str,
) -> dict:
    dec = decide_human_checkpoint(_ws(base), checkpoint_id=checkpoint_id,
        decision=decision, rationale=rationale, decided_by=decided_by)
    return require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(dec)})


def aitp_v5_create_promotion_packet(
    base: str, *, topic_id: str, claim_id: str, proposed_memory_kind: str = "scoped_claim",
    scope: str = "", evidence_refs: list[str] | None = None, non_claims: list[str] | None = None,
    known_failure_modes: list[str] | None = None, validation_result_ids: list[str] | None = None,
    failure_mode_review_checkpoint_id: str = "", failure_mode_review_result_id: str = "",
) -> dict:
    pkt = create_promotion_packet(_ws(base), topic_id=topic_id, claim_id=claim_id,
        proposed_memory_kind=proposed_memory_kind, scope=scope, evidence_refs=evidence_refs,
        validation_result_ids=validation_result_ids, non_claims=non_claims,
        known_failure_modes=known_failure_modes, failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id, failure_mode_review_result_id=failure_mode_review_result_id)
    return require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(pkt)})


def aitp_v5_apply_promotion_packet(
    base: str, *, packet_id: str, checkpoint_id: str,
) -> dict:
    entry = apply_promotion_packet(_ws(base), packet_id=packet_id, checkpoint_id=checkpoint_id)
    return require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})


def aitp_v5_preflight_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_preflight",
        preflight_trust_update(_ws(base), _trust_request(locals())))}


def aitp_v5_apply_trust_update(
    base: str, *, action: str, session_id: str, topic_id: str, claim_id: str,
    requested_state: str = "", source_kind: str = "", source_ref: str = "",
    evidence_refs: list[str] | None = None, code_state_ids: list[str] | None = None,
    rationale: str = "", request_id: str = "", preflight_token: str = "",
) -> dict:
    return {"ok": True, **require_valid_public_surface("trust_update_apply",
        apply_trust_update(_ws(base), _trust_request(locals())))}


def aitp_v5_get_trust_update_record(base: str, *, update_id: str) -> dict:
    record = get_trust_update_record(_ws(base), update_id)
    return require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})


def _trust_request(ns: dict) -> TrustUpdateRequest:
    rid = ns.get("request_id") or f"trust-request-{ns['session_id']}-{ns['claim_id']}-{ns['action']}"
    return TrustUpdateRequest(request_id=rid, action=ns["action"], session_id=ns["session_id"],
        topic_id=ns["topic_id"], claim_id=ns["claim_id"], requested_state=ns.get("requested_state", ""),
        source_kind=ns.get("source_kind", ""), source_ref=ns.get("source_ref", ""),
        evidence_refs=ns.get("evidence_refs") or [], code_state_ids=ns.get("code_state_ids") or [],
        rationale=ns.get("rationale", ""), preflight_token=ns.get("preflight_token", ""))


def _linked_code_states(ws, claim_id: str) -> list[CodeStateRecord]:
    states = list_records(ws.registry_dir("code_states"), CodeStateRecord)
    return [s for s in states if _record_links_to_claim(s.linked_records, claim_id)]


def _record_links_to_claim(linked_records: dict, claim_id: str) -> bool:
    for value in linked_records.values():
        if value == claim_id or (isinstance(value, list) and claim_id in value):
            return True
    return False
