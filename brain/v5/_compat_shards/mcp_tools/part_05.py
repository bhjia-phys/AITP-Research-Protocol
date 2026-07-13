# Compatibility shard 5 for mcp_tools.
from __future__ import annotations

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

def aitp_v5_get_runtime_bridge_target_manifest() -> dict:
    """Return MCP-first host bridge targets with CLI fallback templates."""

    return {
        "ok": True,
        "runtime_bridge_target_manifest": require_valid_public_surface(
            "runtime_bridge_target_manifest",
            runtime_bridge_target_manifest(),
        ),
    }

def aitp_v5_audit_runtime_mcp_bridge_acceptance(
    *,
    live_manifest: dict | None = None,
    live_tool_names: list | dict | None = None,
) -> dict:
    """Compare live host MCP bridge exposure with the canonical manifest."""

    return {
        "ok": True,
        "runtime_mcp_bridge_acceptance": require_valid_public_surface(
            "runtime_mcp_bridge_acceptance",
            audit_runtime_mcp_bridge_acceptance(
                live_manifest=live_manifest,
                live_tool_names=live_tool_names,
            ),
        ),
    }

def aitp_v5_get_runtime_payload_profiles() -> dict:
    """Return host-event to AITP typed-write payload profiles."""

    return {
        "ok": True,
        "runtime_payload_profiles": require_valid_public_surface(
            "runtime_payload_profiles",
            runtime_payload_profiles(),
        ),
    }

def aitp_v5_get_curated_rag_corpus(base: str = "") -> dict:
    """Return the curated heuristic RAG corpus catalog."""

    return {
        "ok": True,
        "curated_rag_corpus": require_valid_public_surface(
            "curated_rag_corpus",
            curated_rag_corpus(base or None),
        ),
    }

def aitp_v5_search_curated_rag_corpus(query: str, *, limit: int = 5, base: str = "") -> dict:
    """Return heuristic background chunks from the curated RAG corpus."""

    return {
        "ok": True,
        "curated_rag_search_result": require_valid_public_surface(
            "curated_rag_search_result",
            search_curated_rag_corpus(query, limit=limit, base=base or None),
        ),
    }

def aitp_v5_get_curated_rag_chunk(chunk_id: str, *, base: str = "") -> dict:
    """Return one read-only curated RAG chunk identity/anchor/hash payload."""

    return {
        "ok": True,
        "curated_rag_chunk": require_valid_public_surface(
            "curated_rag_chunk",
            read_curated_rag_chunk(chunk_id, base=base or None),
        ),
    }

def aitp_v5_draft_curated_rag_promotion(
    chunk_id: str,
    *,
    base: str = "",
    topic_id: str = "",
    claim_id: str = "",
    connector_id: str = "curated_rag",
    promotion_intent: str = "claim_support_review",
) -> dict:
    """Return a read-only promotion draft for a curated RAG chunk."""

    return {
        "ok": True,
        "curated_rag_promotion_draft": require_valid_public_surface(
            "curated_rag_promotion_draft",
            draft_curated_rag_promotion(
                chunk_id,
                base=base or None,
                topic_id=topic_id,
                claim_id=claim_id,
                connector_id=connector_id,
                promotion_intent=promotion_intent,
            ),
        ),
    }

def aitp_v5_ingest_curated_rag_corpus(
    base: str,
    *,
    paths: list[str],
    corpus_id: str = "",
    tags: list[str] | None = None,
    domain_hints: list[str] | None = None,
    topic_hints: list[str] | None = None,
    language: str = "en",
    priority: str = "medium",
    chunk_token_limit: int = 220,
    title_prefix: str = "",
    asset_type: str = "",
    rebuild_index: bool = True,
) -> dict:
    """Create or refresh a file-backed curated RAG manifest/index."""

    return require_valid_public_surface(
        "curated_rag_ingest_result",
        ingest_curated_rag_corpus(
            _ws(base),
            paths=paths,
            corpus_id=corpus_id,
            tags=tags,
            domain_hints=domain_hints,
            topic_hints=topic_hints,
            language=language,
            priority=priority,
            chunk_token_limit=chunk_token_limit,
            title_prefix=title_prefix,
            asset_type=asset_type,
            rebuild_index=rebuild_index,
        ),
    )

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

def aitp_v5_build_harness_feedback_seed_bundle(base: str = "") -> dict:
    return require_valid_public_surface("harness_feedback_bundle", build_nio_harness_feedback_bundle())

def aitp_v5_plan_run_dir_provenance_extractor(
    base: str = "",
    *,
    case_id: str = "g0w0-magnetic-nio",
) -> dict:
    return require_valid_public_surface(
        "run_dir_provenance_extractor_plan",
        plan_run_dir_provenance_extractor(case_id=case_id),
    )

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
    metadata: dict | None = None, linked_records: dict | None = None, claim_id: str = "",
    status: str = "active",
) -> dict:
    links = dict(linked_records or {})
    if claim_id:
        links.setdefault("claim_id", claim_id)
    obj = record_physics_object(_ws(base), topic_id=topic_id, object_type=object_type,
        name=name, definition=definition, notation=notation, assumptions=assumptions,
        source_refs=source_refs, metadata=metadata, linked_records=links, status=status)
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

def aitp_v5_record_authority(
    base: str,
    *,
    topic_id: str,
    authority_type: str,
    authority_statement: str,
    work_package: str = "",
    claim_id: str = "",
    scope: dict | None = None,
    generator_set: str = "",
    closure_envelope: str = "",
    evidence_refs: list[str] | None = None,
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    linked_records: dict | None = None,
    limitations: list[str] | None = None,
    status: str = "research_authority_not_trust_promotion",
) -> dict:
    """Record a convention/sector/dataset/code authority without claim-trust authority."""

    record = record_authority(
        _ws(base),
        topic_id=topic_id,
        authority_type=authority_type,
        authority_statement=authority_statement,
        work_package=work_package,
        claim_id=claim_id,
        scope=scope,
        generator_set=generator_set,
        closure_envelope=closure_envelope,
        evidence_refs=evidence_refs,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        linked_records=linked_records,
        limitations=limitations,
        status=status,
    )
    return require_valid_public_surface("authority_record", authority_record_payload(record))

def aitp_v5_list_authorities(
    base: str,
    *,
    topic_id: str,
    authority_type: str = "",
    work_package: str = "",
    include_inactive: bool = False,
) -> dict:
    """Return a read-only topic authority registry view."""

    return require_valid_public_surface(
        "authority_registry",
        authority_registry_payload(
            _ws(base),
            topic_id=topic_id,
            authority_type=authority_type,
            work_package=work_package,
            include_inactive=include_inactive,
        ),
    )

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

def aitp_v5_preview_quiet_checkpoint_batch(
    base: str,
    *,
    session_id: str,
    claim_id: str = "",
    run_id: str = "",
    summary: str,
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
    """Preview a research-burst checkpoint batch without writing records."""

    return require_valid_public_surface(
        "quiet_checkpoint_preview",
        preview_quiet_checkpoint_batch(
            _ws(base),
            session_id,
            claim_id=claim_id,
            run_id=run_id,
            summary=summary,
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
        ),
    )
