# Compatibility shard 4 for mcp_tools.
from __future__ import annotations

def aitp_v5_register_source_asset(
    base: str,
    *,
    topic_id: str,
    asset_type: str,
    uri: str,
    title: str,
    claim_id: str = "",
    label: str = "",
    content_hash: str = "",
    hash_algorithm: str = "",
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "manual",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    record = register_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        uri=uri,
        title=title,
        label=label,
        content_hash=content_hash,
        hash_algorithm=hash_algorithm,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))

def aitp_v5_capture_source_asset_auto(
    base: str,
    *,
    path: str,
    topic_id: str,
    claim_id: str = "",
    asset_type: str = "",
    title: str = "",
    label: str = "",
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "local_file_auto",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
    copy_to_store: bool = False,
    force_refresh: bool = False,
) -> dict:
    """Inspect a local file and register it as an AITP source asset."""

    record = capture_source_asset_from_local_path(
        _ws(base),
        path=path,
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        title=title,
        label=label,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
        copy_to_store=copy_to_store,
        force_refresh=force_refresh,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))

def aitp_v5_acquire_pdf_source_asset(
    base: str,
    *,
    topic_id: str,
    url: str,
    title: str,
    claim_id: str = "",
    asset_type: str = "paper",
    label: str = "",
    timeout_seconds: int = 120,
    max_bytes: int = 200 * 1024 * 1024,
    force_refresh: bool = False,
    version_anchor: dict | None = None,
    acquired_at: str = "",
    source_kind: str = "literature_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    """Acquire a PDF into the topic-scoped v5 source blob store."""

    record = acquire_pdf_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        asset_type=asset_type,
        url=url,
        title=title,
        label=label,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        force_refresh=force_refresh,
        version_anchor=version_anchor,
        acquired_at=acquired_at,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))

def aitp_v5_acquire_arxiv_source_asset(
    base: str,
    *,
    topic_id: str,
    arxiv_id: str,
    title: str = "",
    claim_id: str = "",
    version: str = "",
    label: str = "",
    timeout_seconds: int = 120,
    max_bytes: int = 200 * 1024 * 1024,
    force_refresh: bool = False,
    version_anchor: dict | None = None,
    source_kind: str = "arxiv_pdf",
    summary: str = "",
    source_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    code_state_ids: list[str] | None = None,
    reference_location_ids: list[str] | None = None,
    derived_from: list[str] | None = None,
    metadata: dict | None = None,
    linked_records: dict | None = None,
) -> dict:
    """Acquire an arXiv PDF into the topic-scoped v5 source blob store."""

    record = acquire_arxiv_source_asset(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        arxiv_id=arxiv_id,
        title=title,
        version=version,
        label=label,
        timeout_seconds=timeout_seconds,
        max_bytes=max_bytes,
        force_refresh=force_refresh,
        version_anchor=version_anchor,
        source_kind=source_kind,
        summary=summary,
        source_refs=source_refs,
        artifact_ids=artifact_ids,
        code_state_ids=code_state_ids,
        reference_location_ids=reference_location_ids,
        derived_from=derived_from,
        metadata=metadata,
        linked_records=linked_records,
    )
    return require_valid_public_surface("source_asset_record", source_asset_payload(record))

def aitp_v5_record_research_route(
    base: str,
    *,
    topic_id: str,
    title: str,
    route_type: str,
    status: str,
    rationale: str,
    claim_id: str = "",
    session_id: str = "",
    current_question: str = "",
    next_action: str = "",
    failure_modes: list[str] | None = None,
    source_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    artifact_ids: list[str] | None = None,
    parent_route_ids: list[str] | None = None,
    checkpoint_ids: list[str] | None = None,
    exploratory_record_ids: list[str] | None = None,
    object_ids: list[str] | None = None,
    relation_ids: list[str] | None = None,
    decision_rationale: str = "",
    pivot_reason: str = "",
    metadata: dict | None = None,
) -> dict:
    record = record_research_route(
        _ws(base),
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        title=title,
        route_type=route_type,
        status=status,
        rationale=rationale,
        current_question=current_question,
        next_action=next_action,
        failure_modes=failure_modes,
        source_refs=source_refs,
        evidence_refs=evidence_refs,
        artifact_ids=artifact_ids,
        parent_route_ids=parent_route_ids,
        checkpoint_ids=checkpoint_ids,
        exploratory_record_ids=exploratory_record_ids,
        object_ids=object_ids,
        relation_ids=relation_ids,
        decision_rationale=decision_rationale,
        pivot_reason=pivot_reason,
        metadata=metadata,
    )
    return require_valid_public_surface("research_route_record", research_route_payload(record))

_LEGACY_MCP_MODULE = ".".join(("brain", "mcp_" + "server"))

def _legacy_mcp_tool(tool_name: str):
    return getattr(import_module(_LEGACY_MCP_MODULE), tool_name)

def _legacy_list_topics_alias(topics_root: str) -> list[dict]:
    """Legacy discovery alias only; migrate/bind a v5 session before real work."""
    return _legacy_mcp_tool("aitp_" + "list_topics")(topics_root)

def _legacy_execution_brief_alias(topics_root: str, topic_slug: str) -> dict:
    """Legacy stage brief alias only; prefer aitp_v5_get_execution_brief."""
    return _legacy_mcp_tool("aitp_" + "get_execution_brief")(topics_root, topic_slug)

def _legacy_bootstrap_topic_alias(
    topics_root: str,
    topic_slug: str,
    title: str,
    question: str,
    lane: str = "unspecified",
    research_intensity: str = "standard",
    interaction_level: str = "collaborative",
) -> dict:
    """Legacy topic bootstrap alias; prefer v5 topic/claim/session records."""
    result = _legacy_mcp_tool("aitp_" + "bootstrap_topic")(
        topics_root,
        topic_slug,
        title,
        question,
        lane=lane,
        research_intensity=research_intensity,
        interaction_level=interaction_level,
    )
    if isinstance(result, dict):
        return result
    return {"ok": True, "message": str(result), "topic_slug": topic_slug}

aitp_list_topics = _legacy_list_topics_alias

aitp_list_topics.__name__ = "aitp_" + "list_topics"

globals()["aitp_" + "get_execution_brief"] = _legacy_execution_brief_alias

_legacy_execution_brief_alias.__name__ = "aitp_" + "get_execution_brief"

globals()["aitp_" + "bootstrap_topic"] = _legacy_bootstrap_topic_alias

_legacy_bootstrap_topic_alias.__name__ = "aitp_" + "bootstrap_topic"

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

def aitp_v5_capture_code_state_auto(
    base: str,
    *,
    worktree_path: str,
    repo_id: str = "",
    topic_id: str = "",
    claim_id: str = "",
    session_id: str = "",
    build_config: dict | None = None,
    runtime_environment: dict | None = None,
    linked_records: dict | None = None,
    known_divergence: str = "",
    write_patch_artifact: bool = False,
) -> dict:
    state = capture_code_state_from_git(
        _ws(base),
        worktree_path=worktree_path,
        repo_id=repo_id,
        topic_id=topic_id,
        claim_id=claim_id,
        session_id=session_id,
        build_config=build_config,
        runtime_environment=runtime_environment,
        linked_records=linked_records,
        known_divergence=known_divergence,
        write_patch_artifact=write_patch_artifact,
    )
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
    scientific_run_id: str = "", supersedes: str = "", lane: str = "diagnostic",
) -> dict:
    run = record_tool_run(_ws(base), recipe_id=recipe_id, tool_family=tool_family,
        tool_name=tool_name, topic_id=topic_id, claim_id=claim_id, inputs=inputs,
        outputs=outputs, environment=environment, evidence_status=evidence_status,
        code_state_ids=code_state_ids, artifact_ids=artifact_ids, source_refs=source_refs,
        scientific_run_id=scientific_run_id, supersedes=supersedes, lane=lane)
    return require_valid_public_surface("tool_run_record", tool_run_payload(run))

def aitp_v5_capture_tool_run_auto(
    base: str,
    *,
    path: str,
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
    scientific_run_id: str = "",
    supersedes: str = "",
    lane: str = "diagnostic",
    summary: str = "",
    max_preview_chars: int = 1200,
) -> dict:
    """Inspect a local transcript/result file and record tool-run provenance."""

    run = capture_tool_run_from_local_path(
        _ws(base),
        path=path,
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
        scientific_run_id=scientific_run_id,
        supersedes=supersedes,
        lane=lane,
        summary=summary,
        max_preview_chars=max_preview_chars,
    )
    return require_valid_public_surface("tool_run_record", tool_run_payload(run))

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
    payload = tool_run_payload(result.run)
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
            project_root=str(ws.base),
            topics_root=str(ws.base),
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
            project_root=str(ws.base),
            topics_root=str(ws.base),
        ),
    }
    return require_valid_public_surface("opencode_plugin_bridge", bridge)
