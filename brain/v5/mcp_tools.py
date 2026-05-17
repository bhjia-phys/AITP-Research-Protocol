"""Thin MCP-facing wrappers around the AITP v5 kernel."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from brain.v5.adapters import build_adapter_packet
from brain.v5.brief import build_execution_brief
from brain.v5.code import record_code_state
from brain.v5.contracts import require_valid_execution_brief
from brain.v5.evidence import record_evidence
from brain.v5.models import CodeStateRecord
from brain.v5.risk import assess_claim_risk
from brain.v5.store import list_records
from brain.v5.summaries import write_session_summary
from brain.v5.tools import record_tool_run, register_tool_recipe
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
    return require_valid_execution_brief(build_execution_brief(ws, session_id))


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
    return {"ok": True, **asdict(state)}


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
    return {"ok": True, **asdict(evidence)}


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
    return {"ok": True, **asdict(recipe)}


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
    return {"ok": True, **asdict(run)}


def aitp_v5_write_session_summary(base: str, *, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return {"ok": True, **asdict(write_session_summary(ws, session_id))}


def aitp_v5_get_adapter_packet(base: str, *, runtime: str, session_id: str) -> dict:
    ws = init_workspace(Path(base))
    return {"ok": True, **build_adapter_packet(ws, session_id, runtime=runtime)}


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
