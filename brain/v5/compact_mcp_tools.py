"""Compact AITP v5 MCP wrappers without the full maintenance/migration catalog."""

from __future__ import annotations

from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.models import TrustUpdateRequest
from brain.v5.paths import WorkspacePaths
from brain.v5.pretool_policy import evaluate_context_pre_tool_policy
from brain.v5.public_surfaces import require_valid_public_surface
from brain.v5.trust_updates import preflight_trust_update


def _ws(base: str):
    return WorkspacePaths(resolve_workspace_base(base))


def aitp_v5_codex_tool_catalog(profile: str = "entry") -> dict:
    """List compact AITP tools and disclosure policy."""

    from brain.v5.codex_facade import codex_tool_catalog

    return codex_tool_catalog(profile=profile)


def aitp_v5_codex_autoroute(
    base: str,
    *,
    request_summary: str,
    session_id: str = "",
    topics: list[str] | None = None,
    visible_files: list[str] | None = None,
    recent_tool_summary: str = "",
    semantic_assessment: dict | None = None,
    route_context: dict | None = None,
) -> dict:
    """Route one request into AITP when needed."""

    from brain.v5.codex_facade import codex_autoroute

    context = _normalized_route_context(route_context)

    return codex_autoroute(
        _ws(base),
        request_summary=request_summary,
        session_id=session_id,
        topics=topics,
        visible_files=visible_files,
        recent_tool_summary=recent_tool_summary,
        semantic_assessment=semantic_assessment,
        host=context.get("host", ""),
        host_session_id=context.get("host_session_id", ""),
        project_root=context.get("project_root", ""),
        current_path=context.get("current_path", ""),
        repo_id=context.get("repo_id", ""),
        branch=context.get("branch", ""),
        exact_refs=context.get("exact_refs"),
        pinned_session_id=context.get("pinned_session_id", ""),
        routing_mode=context.get("routing_mode", "dynamic"),
    )


def _normalized_route_context(value: dict | None) -> dict:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError("route_context must be an object")
    allowed = {
        "host",
        "host_session_id",
        "project_root",
        "current_path",
        "repo_id",
        "branch",
        "exact_refs",
        "pinned_session_id",
        "routing_mode",
    }
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ValueError(f"unsupported route_context fields: {', '.join(unknown)}")
    return dict(value)


def aitp_v5_codex_enter(
    base: str,
    *,
    session_id: str = "",
    topics: list[str] | None = None,
    request_summary: str = "",
    process_mode: str = "auto",
    payload_profile: str = "minimal",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict:
    """Enter AITP with bounded context."""

    from brain.v5.codex_facade import codex_enter_context

    return codex_enter_context(
        _ws(base),
        session_id=session_id,
        topics=topics,
        request_summary=request_summary,
        process_mode=process_mode,
        payload_profile=payload_profile,
        max_lines=max_lines,
        candidate_limit=candidate_limit,
    )


def aitp_v5_codex_expand(
    base: str,
    *,
    session_id: str,
    expansion: str,
    claim_id: str = "",
    max_lines: int = 60,
    limit: int = 60,
    style: str = "jhep",
    objective_text: str = "",
    user_goal: str = "",
    record_refs: list[str] | None = None,
    offset: int = 0,
) -> dict:
    """Expand one context family explicitly."""

    from brain.v5.codex_facade import codex_expand_context

    return codex_expand_context(
        _ws(base),
        session_id=session_id,
        expansion=expansion,
        claim_id=claim_id,
        max_lines=max_lines,
        limit=limit,
        style=style,
        objective_text=objective_text,
        user_goal=user_goal,
        record_refs=record_refs,
        offset=offset,
    )


def aitp_v5_codex_recording_step(
    base: str,
    *,
    session_id: str,
    event_type: str,
    summary: str = "",
    topic_id: str = "",
    claim_id: str = "",
    touched_refs: list[str] | None = None,
    produced_artifacts: list[str] | None = None,
    tool_call_id: str = "",
    risk_hint: str = "",
    slot: str = "",
    candidate: dict | None = None,
    expected_refs: list[str] | None = None,
) -> dict:
    """Classify or stage one durable research moment."""

    from brain.v5.codex_facade import codex_recording_step

    return codex_recording_step(
        _ws(base),
        session_id=session_id,
        event_type=event_type,
        summary=summary,
        topic_id=topic_id,
        claim_id=claim_id,
        touched_refs=touched_refs,
        produced_artifacts=produced_artifacts,
        tool_call_id=tool_call_id,
        risk_hint=risk_hint,
        slot=slot,
        candidate=candidate,
        expected_refs=expected_refs,
    )


def aitp_v5_codex_record_apply(
    base: str,
    *,
    session_id: str,
    slot: str,
    payload: dict | None = None,
    event_type: str = "",
    summary: str = "",
    claim_id: str = "",
    expected_refs: list[str] | None = None,
) -> dict:
    """Apply one reviewed recording action."""

    from brain.v5.codex_facade import codex_record_apply

    return codex_record_apply(
        _ws(base),
        session_id=session_id,
        slot=slot,
        payload=payload,
        event_type=event_type,
        summary=summary,
        claim_id=claim_id,
        expected_refs=expected_refs,
    )


def aitp_v5_codex_literature_step(
    base: str,
    *,
    session_id: str,
    uri: str,
    label: str,
    action: str = "suggest",
    external_id: str = "",
    short_summary: str = "",
    detected_relevance: str = "",
    optional_claim_id: str = "",
    scoped_output: str = "",
    reviewed_refs: list[str] | None = None,
    comparison_question: str = "",
    source_refs: list[str] | None = None,
    dimensions: list[str] | None = None,
    rationale: str = "",
    asset_type: str = "",
) -> dict:
    """Run one literature workflow step."""

    from brain.v5.codex_facade import codex_literature_step

    return codex_literature_step(
        _ws(base),
        session_id=session_id,
        uri=uri,
        label=label,
        action=action,
        external_id=external_id,
        short_summary=short_summary,
        detected_relevance=detected_relevance,
        optional_claim_id=optional_claim_id,
        scoped_output=scoped_output,
        reviewed_refs=reviewed_refs,
        comparison_question=comparison_question,
        source_refs=source_refs,
        dimensions=dimensions,
        rationale=rationale,
        asset_type=asset_type,
    )


def aitp_v5_codex_closeout(
    base: str,
    *,
    session_id: str,
    summary: str,
    apply: bool = False,
    claim_id: str = "",
    run_id: str = "",
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    changed_files: list[str] | None = None,
    generated_artifacts: list[dict] | None = None,
    validation_commands: list[str] | None = None,
    durable_observations: list[str] | None = None,
    claim_boundary: dict | None = None,
    next_blockers: list[str] | None = None,
    artifact_specs: list[dict] | None = None,
    source_specs: list[dict] | None = None,
    tool_run_specs: list[dict] | None = None,
    sensemaking_summary: str = "",
    source_refs: list[str] | None = None,
    lifecycle_request: dict | None = None,
    lifecycle_plan: dict | None = None,
    lifecycle_plan_id: str = "",
) -> dict:
    """Plan or apply a trust-neutral closeout."""

    from brain.v5.codex_facade import codex_closeout

    return codex_closeout(
        _ws(base),
        session_id=session_id,
        summary=summary,
        apply=apply,
        claim_id=claim_id,
        run_id=run_id,
        inputs=inputs,
        outputs=outputs,
        changed_files=changed_files,
        generated_artifacts=generated_artifacts,
        validation_commands=validation_commands,
        durable_observations=durable_observations,
        claim_boundary=claim_boundary,
        next_blockers=next_blockers,
        artifact_specs=artifact_specs,
        source_specs=source_specs,
        tool_run_specs=tool_run_specs,
        sensemaking_summary=sensemaking_summary,
        source_refs=source_refs,
        lifecycle_request=lifecycle_request,
        lifecycle_plan=lifecycle_plan,
        lifecycle_plan_id=lifecycle_plan_id,
    )


def aitp_v5_evaluate_pre_tool_policy(
    base: str,
    *,
    session_id: str,
    action: str,
    claim_id: str = "",
    evidence_refs: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    validation_contract_ids: list[str] | None = None,
    tool_run_ids: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    known_failure_modes: list[str] | None = None,
    recipe_id: str = "",
    executor_id: str = "",
    source_kind: str = "",
    source_ref: str = "",
    orientation_only: bool = False,
    risk_level: str = "guided",
    human_checkpoint_id: str = "",
    failure_mode_review_checkpoint_id: str = "",
    failure_mode_review_result_id: str = "",
) -> dict:
    return require_valid_public_surface(
        "pre_tool_policy_decision",
        evaluate_context_pre_tool_policy(
            _ws(base),
            session_id=session_id,
            action=action,
            claim_id=claim_id,
            evidence_refs=evidence_refs,
            code_state_ids=code_state_ids,
            validation_contract_ids=validation_contract_ids,
            tool_run_ids=tool_run_ids,
            validation_result_ids=validation_result_ids,
            known_failure_modes=known_failure_modes,
            recipe_id=recipe_id,
            executor_id=executor_id,
            source_kind=source_kind,
            source_ref=source_ref,
            orientation_only=orientation_only,
            risk_level=risk_level,
            human_checkpoint_id=human_checkpoint_id,
            failure_mode_review_checkpoint_id=failure_mode_review_checkpoint_id,
            failure_mode_review_result_id=failure_mode_review_result_id,
        ),
    )


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
    preflight_token: str = "",
) -> dict:
    request = TrustUpdateRequest(
        request_id=request_id or f"trust-request-{session_id}-{claim_id}-{action}",
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
        preflight_token=preflight_token,
    )
    return {
        "ok": True,
        **require_valid_public_surface(
            "trust_update_preflight",
            preflight_trust_update(_ws(base), request),
        ),
    }
