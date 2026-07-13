# Compatibility shard 2 for mcp_tools.
from __future__ import annotations

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
    """Run a layered literature/reference workflow step from Codex."""

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
) -> dict:
    """Preview or apply a quiet closeout checkpoint without trust mutation."""

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
    )

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
    requested_session_id = session_id
    safe_session_id = _safe_bind_session_id(session_id, topic_id=topic_id)
    session = bind_session(_ws(base), safe_session_id, topic_id=topic_id, context_id=context_id,
        active_claim=active_claim, interaction_profile=interaction_profile,
        interaction_steering=interaction_steering)
    return {"ok": True, "requested_session_id": requested_session_id, **asdict(session)}

def aitp_v5_get_execution_brief(base: str, *, session_id: str) -> dict:
    try:
        brief = build_execution_brief(_ws(base), session_id)
    except TypeError as error:
        if "SessionBinding.__init__()" not in str(error):
            raise
        brief = _unbound_session_execution_brief(session_id)
    return require_valid_public_surface("execution_brief", brief)

def aitp_v5_get_claim_relation_map(
    base: str,
    *,
    session_id: str,
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return the derived relation map and conclusion boundary for the active claim."""

    try:
        relation_map = build_claim_relation_map(
            _ws(base),
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
        )
    except TypeError as error:
        if "SessionBinding.__init__()" not in str(error):
            raise
        relation_map = empty_claim_relation_map(
            topic_id="unbound-session",
            session_id=session_id,
            reason="session binding is missing or malformed",
        )
    return require_valid_public_surface(
        "claim_relation_map",
        relation_map,
    )

def aitp_v5_get_research_timeline(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    limit: int = 80,
) -> dict:
    """Return a read-only continuation timeline with failed and superseded routes."""

    return require_valid_public_surface(
        "research_timeline",
        build_research_timeline(_ws(base), session_id, claim_id=claim_id, limit=limit),
    )

def aitp_v5_get_objective_graph(base: str, *, session_id: str) -> dict:
    """Return a read-only objective/work-package projection for the session."""

    return require_valid_public_surface("objective_graph", build_objective_graph(_ws(base), session_id))

def aitp_v5_get_compact_brief(
    base: str,
    *,
    session_id: str,
    max_lines: int = 40,
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a short continuation brief; full brief/relation-map remain explicit."""

    return require_valid_public_surface(
        "compact_execution_brief",
        build_compact_brief(
            _ws(base),
            session_id,
            max_lines=max_lines,
            objective_text=objective_text,
            user_goal=user_goal,
        ),
    )

def aitp_v5_get_context_pack(
    base: str,
    *,
    session_id: str,
    max_lines: int = 60,
    candidate_limit: int = 3,
    objective_text: str = "",
    user_goal: str = "",
    task_profile: str = "",
) -> dict:
    """Return a Codex-friendly bounded context pack for turn-input injection."""

    return require_valid_public_surface(
        "aitp_context_pack",
        build_aitp_context_pack(
            _ws(base),
            session_id,
            max_lines=max_lines,
            candidate_limit=candidate_limit,
            objective_text=objective_text,
            user_goal=user_goal,
            task_profile=task_profile,
        ),
    )

def aitp_v5_get_context_profile_templates(
    base: str = "",
    *,
    profile_ids: list[str] | None = None,
) -> dict:
    """Return read-only report and closeout templates for task context profiles."""

    _ = base
    return require_valid_public_surface(
        "context_profile_template_catalog",
        build_context_profile_template_catalog(profile_ids=profile_ids),
    )

def aitp_v5_build_context_profile_draft(
    base: str,
    *,
    session_id: str,
    profile_id: str = "closeout",
    max_lines: int = 60,
    candidate_limit: int = 3,
) -> dict:
    """Return a read-only group-meeting or closeout draft from context profile templates."""

    return require_valid_public_surface(
        "context_profile_draft",
        build_context_profile_draft(
            _ws(base),
            session_id,
            profile_id=profile_id,
            max_lines=max_lines,
            candidate_limit=candidate_limit,
        ),
    )

def aitp_v5_detect_active_claim_focus_drift(
    base: str,
    *,
    session_id: str,
    objective_text: str = "",
    user_goal: str = "",
    candidate_limit: int = 5,
) -> dict:
    """Detect active-claim focus drift without changing any binding or trust state."""

    return require_valid_public_surface(
        "active_claim_focus_reconciliation",
        detect_active_claim_focus_drift(
            _ws(base),
            session_id,
            objective_text=objective_text,
            user_goal=user_goal,
            candidate_limit=candidate_limit,
        ),
    )

def aitp_v5_propose_active_claim_rebind(
    base: str,
    *,
    session_id: str,
    candidate_claim_id: str = "",
    reason: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a read-only active-claim rebind proposal requiring confirmation."""

    return require_valid_public_surface(
        "active_claim_rebind_proposal",
        propose_active_claim_rebind(
            _ws(base),
            session_id,
            candidate_claim_id=candidate_claim_id,
            reason=reason,
            objective_text=objective_text,
            user_goal=user_goal,
        ),
    )

def aitp_v5_confirm_active_claim_rebind(
    base: str,
    *,
    session_id: str,
    new_claim_id: str,
    reason: str,
    user_confirmation: str,
    operator: str = "human",
) -> dict:
    """Explicitly rebind the session active claim and write an audit record."""

    return require_valid_public_surface(
        "active_claim_rebind_confirmation",
        confirm_active_claim_rebind(
            _ws(base),
            session_id,
            new_claim_id=new_claim_id,
            reason=reason,
            user_confirmation=user_confirmation,
            operator=operator,
        ),
    )

def aitp_v5_get_research_distillation_candidates(base: str, *, session_id: str, limit: int = 8) -> dict:
    """Return read-only reusable-block candidates and missing gates for a session."""

    return require_valid_public_surface(
        "research_distillation_candidates",
        build_research_distillation_candidates(_ws(base), session_id, limit=limit),
    )

def aitp_v5_compile_note_outline(
    base: str,
    *,
    session_id: str,
    style: str = "jhep",
    candidate_limit: int = 8,
) -> dict:
    """Return a read-only research-note outline coverage surface."""

    return require_valid_public_surface(
        "note_outline",
        compile_note_outline(_ws(base), session_id, style=style, candidate_limit=candidate_limit),
    )

def aitp_v5_build_workspace_file_migration_ledger(
    base: str,
    *,
    workspace_root: str = "",
    migration_plan_json: str = "",
    old_store_manifest_json: str = "",
    legacy_accounting_dir: str = "",
    compact: bool = False,
) -> dict:
    """Return the file-level import/archive/review ledger for old AITP stores."""

    payload = build_workspace_file_migration_ledger(
        _ws(base),
        workspace_root=workspace_root or None,
        migration_plan_path=migration_plan_json or None,
        old_store_manifest_path=old_store_manifest_json or None,
        legacy_accounting_dir=legacy_accounting_dir or None,
    )
    if compact:
        return require_valid_public_surface(
            "workspace_file_migration_ledger_progress",
            compact_workspace_file_migration_ledger(payload),
        )
    return require_valid_public_surface("workspace_file_migration_ledger", payload)

def aitp_v5_write_workspace_file_migration_ledger(
    base: str,
    *,
    workspace_root: str = "",
    migration_plan_json: str = "",
    old_store_manifest_json: str = "",
    legacy_accounting_dir: str = "",
    write_json: str = "",
    write_report: str = "",
    compact: bool = True,
) -> dict:
    """Write JSON/Markdown file-level migration ledger views for old AITP stores."""

    payload = build_workspace_file_migration_ledger(
        _ws(base),
        workspace_root=workspace_root or None,
        migration_plan_path=migration_plan_json or None,
        old_store_manifest_path=old_store_manifest_json or None,
        legacy_accounting_dir=legacy_accounting_dir or None,
    )
    payload = write_workspace_file_migration_ledger(
        payload,
        json_path=write_json or None,
        report_path=write_report or None,
    )
    if compact:
        progress = compact_workspace_file_migration_ledger(payload)
        return {"ok": True, **require_valid_public_surface("workspace_file_migration_ledger_progress", progress)}
    return {"ok": True, **require_valid_public_surface("workspace_file_migration_ledger", payload)}

def aitp_v5_get_workspace_migration_health(
    base: str,
    *,
    sample_limit: int = 5,
) -> dict:
    """Return compact migration/recovery boundary status for the canonical store."""

    return require_valid_public_surface(
        "workspace_migration_health",
        build_workspace_migration_health(_ws(base), sample_limit=sample_limit),
    )

def aitp_v5_build_workspace_old_store_import_plan(
    base: str,
    *,
    workspace_root: str = "",
    old_store_manifest_json: str = "",
    topics: list[str] | None = None,
) -> dict:
    """Return a conflict-checked plan for importing old-store typed files."""

    payload = build_workspace_old_store_import_plan(
        _ws(base),
        workspace_root=workspace_root or None,
        old_store_manifest_path=old_store_manifest_json or None,
        topics=topics or [],
    )
    return require_valid_public_surface("workspace_old_store_import_result", payload)

def aitp_v5_apply_workspace_old_store_import(
    base: str,
    *,
    workspace_root: str = "",
    old_store_manifest_json: str = "",
    topics: list[str] | None = None,
    write_json: str = "",
    write_report: str = "",
) -> dict:
    """Apply a conflict-checked import of old-store typed files into canonical AITP."""

    payload = build_workspace_old_store_import_plan(
        _ws(base),
        workspace_root=workspace_root or None,
        old_store_manifest_path=old_store_manifest_json or None,
        topics=topics or [],
    )
    payload = apply_workspace_old_store_import_plan(payload)
    if write_json or write_report:
        payload = write_workspace_old_store_import_result(
            payload,
            json_path=write_json or None,
            report_path=write_report or None,
        )
    return {"ok": True, **require_valid_public_surface("workspace_old_store_import_result", payload)}

def aitp_v5_build_workspace_recovery_binding_repair(
    base: str,
    *,
    topics: list[str] | None = None,
    session_id: str = "",
    objective_text: str = "",
    user_goal: str = "",
) -> dict:
    """Return a conservative active-claim binding repair plan for recovery gaps."""

    payload = build_workspace_recovery_binding_repair(
        _ws(base),
        topics=topics or [],
        session_id=session_id,
        objective_text=objective_text,
        user_goal=user_goal,
    )
    return require_valid_public_surface("workspace_recovery_binding_repair", payload)
