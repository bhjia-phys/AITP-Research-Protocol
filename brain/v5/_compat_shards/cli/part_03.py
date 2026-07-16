# Compatibility shard 3 for cli.
from __future__ import annotations

def _dispatch_workspace_01(args, ws):
    if args.command == "policy":
            return dispatch_policy_command(args, ws)
    if args.command == "topic" and args.topic_command == "create":
            return {"ok": True, **asdict(create_topic(ws, args.topic_id, context_id=args.context_id, title=args.title))}
    if args.command == "claim" and args.claim_command == "create":
            return {"ok": True, **asdict(create_claim(ws, topic_id=args.topic_id, statement=args.statement,
                evidence_profile=args.evidence_profile, confidence_state=args.confidence_state,
                active_uncertainty=args.uncertainty, recipe_id=args.recipe_id))}
    if args.command == "session" and args.session_command == "bind":
            return {"ok": True, **asdict(bind_session(ws, args.session_id, topic_id=args.topic_id,
                context_id=args.context_id, active_claim=args.active_claim,
                interaction_profile=args.interaction_profile, interaction_steering=args.interaction_steering))}
    if args.command == "brief":
            return require_valid_public_surface("execution_brief", build_execution_brief(ws, args.session_id))
    if args.command == "relation-map":
            return require_valid_public_surface("claim_relation_map", build_claim_relation_map(ws, args.session_id))
    if args.command == "timeline":
            return require_valid_public_surface(
                "research_timeline",
                build_research_timeline(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
            )
    if args.command == "asset" and args.asset_command == "register":
            asset = register_source_asset(
                ws,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                asset_type=args.asset_type,
                uri=args.uri,
                title=args.title,
                label=args.label,
                content_hash=args.content_hash,
                hash_algorithm=args.hash_algorithm,
                version_anchor=_j(args.version_anchor_json),
                acquired_at=args.acquired_at,
                source_kind=args.source_kind,
                summary=args.summary,
                source_refs=args.source_refs,
                artifact_ids=args.artifact_ids,
                code_state_ids=args.code_state_ids,
                reference_location_ids=args.reference_location_ids,
                derived_from=args.derived_from,
                metadata=_j(args.metadata_json),
                linked_records=_j(args.linked_records_json),
            )
            return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "asset" and args.asset_command == "acquire-pdf":
            asset = acquire_pdf_source_asset(
                ws,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                asset_type=args.asset_type,
                url=args.url,
                title=args.title,
                label=args.label,
                timeout_seconds=args.timeout_seconds,
                max_bytes=args.max_bytes,
                force_refresh=args.force_refresh,
                version_anchor=_j(args.version_anchor_json),
                acquired_at=args.acquired_at,
                source_kind=args.source_kind,
                summary=args.summary,
                source_refs=args.source_refs,
                artifact_ids=args.artifact_ids,
                code_state_ids=args.code_state_ids,
                reference_location_ids=args.reference_location_ids,
                derived_from=args.derived_from,
                metadata=_j(args.metadata_json),
                linked_records=_j(args.linked_records_json),
            )
            return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "asset" and args.asset_command == "acquire-arxiv":
            asset = acquire_arxiv_source_asset(
                ws,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                arxiv_id=args.arxiv_id,
                title=args.title,
                version=args.version,
                label=args.label,
                timeout_seconds=args.timeout_seconds,
                max_bytes=args.max_bytes,
                force_refresh=args.force_refresh,
                version_anchor=_j(args.version_anchor_json),
                source_kind=args.source_kind,
                summary=args.summary,
                source_refs=args.source_refs,
                artifact_ids=args.artifact_ids,
                code_state_ids=args.code_state_ids,
                reference_location_ids=args.reference_location_ids,
                derived_from=args.derived_from,
                metadata=_j(args.metadata_json),
                linked_records=_j(args.linked_records_json),
            )
            return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "asset" and args.asset_command == "capture-auto":
            asset = capture_source_asset_from_local_path(
                ws,
                path=args.path,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                asset_type=args.asset_type,
                title=args.title,
                label=args.label,
                version_anchor=_j(args.version_anchor_json),
                acquired_at=args.acquired_at,
                source_kind=args.source_kind,
                summary=args.summary,
                source_refs=args.source_refs,
                artifact_ids=args.artifact_ids,
                code_state_ids=args.code_state_ids,
                reference_location_ids=args.reference_location_ids,
                derived_from=args.derived_from,
                metadata=_j(args.metadata_json),
                linked_records=_j(args.linked_records_json),
                copy_to_store=args.copy_to_store,
                force_refresh=args.force_refresh,
            )
            return require_valid_public_surface("source_asset_record", source_asset_payload(asset))
    if args.command == "graph" and args.graph_command == "slice":
            return require_valid_public_surface(
                "process_graph_slice",
                build_process_graph_slice(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
            )
    if args.command == "graph" and args.graph_command == "moment-policy":
            graph = build_process_graph_slice(ws, args.session_id, claim_id=args.claim_id, limit=args.limit)
            return require_valid_public_surface("host_agnostic_moment_policy", graph["moment_policy"])
    if args.command == "recording" and args.recording_command == "classify-candidate":
            return require_valid_public_surface(
                "recording_candidate_classification",
                classify_recording_candidate(
                    ws,
                    session_id=args.session_id,
                    event_type=args.event_type,
                    summary=args.summary,
                    topic_id=args.topic_id,
                    claim_id=args.claim_id,
                    touched_refs=args.touched_refs,
                    produced_artifacts=args.produced_artifacts,
                    tool_call_id=args.tool_call_id,
                    risk_hint=args.risk_hint,
                    payload=_j(args.payload_json),
                ),
            )
    if args.command == "recording" and args.recording_command == "navigation-state":
            return require_valid_public_surface(
                "recording_navigation_state",
                build_recording_navigation_state(ws, args.session_id, claim_id=args.claim_id, limit=args.limit),
            )
    if args.command == "recording" and args.recording_command == "expand-slot":
            return require_valid_public_surface(
                "recording_slot_expansion",
                expand_recording_slot(ws, args.session_id, args.slot, claim_id=args.claim_id, candidate=_j(args.candidate_json)),
            )
    if args.command == "recording" and args.recording_command == "verify-effect":
            return require_valid_public_surface(
                "recording_effect_verification",
                verify_recording_effect(
                    ws,
                    args.session_id,
                    expected_refs=args.expected_refs,
                    before_node_ids=args.before_node_ids,
                    before_edge_ids=args.before_edge_ids,
                    claim_id=args.claim_id,
                    limit=args.limit,
                ),
            )
    if args.command == "recording" and args.recording_command == "plan-lightweight-write":
            from brain.v5.lightweight_record_router import plan_lightweight_record_write
            return require_valid_public_surface(
                "lightweight_record_write_plan",
                plan_lightweight_record_write(
                    ws,
                    topic_id=args.topic_id,
                    current_session_id=args.current_session_id,
                    event_summary=args.event_summary,
                    active_claim_id=args.active_claim_id,
                    target_claim_hint=args.target_claim_hint,
                    touched_files_or_artifacts=args.touched_files_or_artifacts,
                    touched_tool_runs_or_evidence_refs=args.touched_tool_runs_or_evidence_refs,
                    risk_hint=args.risk_hint,
                ),
            )
    if args.command == "risk" and args.risk_command == "assess":
            return {"ok": True, "claim_id": args.claim_id, "risk_assessment": asdict(assess_claim_risk(get_claim(ws, args.claim_id)))}
    if args.command == "code" and args.code_command == "state" and args.code_state_command == "record":
            st = record_code_state(ws, repo_id=args.repo_id, upstream_remote=args.upstream_remote,
                upstream_branch=args.upstream_branch, upstream_commit=args.upstream_commit,
                local_branch=args.local_branch, worktree_path=args.worktree_path, dirty=args.dirty,
                patch_id=args.patch_id, diff_hash=args.diff_hash,
                build_config=_j(args.build_config_json), runtime_environment=_j(args.runtime_environment_json),
                linked_records=_j(args.linked_records_json), known_divergence=args.known_divergence)
            return {"ok": True, **require_valid_public_surface("code_state_record", {"ok": True, **asdict(st)})}
    if args.command == "code" and args.code_command == "state" and args.code_state_command == "auto":
            st = capture_code_state_from_git(
                ws,
                worktree_path=args.worktree_path,
                repo_id=args.repo_id,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                session_id=args.session_id,
                build_config=_j(args.build_config_json),
                runtime_environment=_j(args.runtime_environment_json),
                linked_records=_j(args.linked_records_json),
                known_divergence=args.known_divergence,
                write_patch_artifact=args.write_patch_artifact,
            )
            return {"ok": True, **require_valid_public_surface("code_state_record", {"ok": True, **asdict(st)})}
    if args.command == "evidence" and args.evidence_command == "record":
            return dispatch_evidence_command(args, ws)
    if args.command == "tool" and args.tool_command == "recipe" and args.tool_recipe_command == "register":
            rc = register_tool_recipe(ws, recipe_id=args.recipe_id, tool_family=args.tool_family,
                tool_name=args.tool_name, purpose=args.purpose, required_inputs=args.required_inputs,
                expected_outputs=args.expected_outputs, invariants=args.invariants)
            return {"ok": True, **require_valid_public_surface("tool_recipe_record", {"ok": True, **asdict(rc)})}
    if args.command == "tool" and args.tool_command == "run" and args.tool_run_command == "record":
            rn = record_tool_run(ws, recipe_id=args.recipe_id, tool_family=args.tool_family,
                tool_name=args.tool_name, topic_id=args.topic_id, claim_id=args.claim_id,
                inputs=_j_arg(args.inputs_json, args.inputs_json_file),
                outputs=_j_arg(args.outputs_json, args.outputs_json_file),
                environment=_j_arg(args.environment_json, args.environment_json_file),
                evidence_status=args.evidence_status,
                code_state_ids=args.code_state_ids, artifact_ids=args.artifact_ids, source_refs=args.source_refs,
                scientific_run_id=args.scientific_run_id, supersedes=args.supersedes, lane=args.lane)
            return require_valid_public_surface("tool_run_record", tool_run_payload(rn))
    if args.command == "tool" and args.tool_command == "run" and args.tool_run_command == "capture-auto":
            rn = capture_tool_run_from_local_path(
                ws,
                path=args.path,
                recipe_id=args.recipe_id,
                tool_family=args.tool_family,
                tool_name=args.tool_name,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                inputs=_j_arg(args.inputs_json, args.inputs_json_file),
                outputs=_j_arg(args.outputs_json, args.outputs_json_file),
                environment=_j_arg(args.environment_json, args.environment_json_file),
                evidence_status=args.evidence_status,
                code_state_ids=args.code_state_ids,
                artifact_ids=args.artifact_ids,
                source_refs=args.source_refs,
                scientific_run_id=args.scientific_run_id,
                supersedes=args.supersedes,
                lane=args.lane,
                summary=args.summary,
                max_preview_chars=args.max_preview_chars,
            )
            return require_valid_public_surface("tool_run_record", tool_run_payload(rn))
    if args.command == "tool" and args.tool_command == "executors":
            return require_valid_public_surface("tool_executor_catalog", describe_tool_executors())
    if args.command == "tool" and args.tool_command == "execute":
            r = execute_registered_tool_result(ws, executor_id=args.executor_id, recipe_id=args.recipe_id,
                topic_id=args.topic_id, claim_id=args.claim_id, inputs=_j_arg(args.inputs_json, args.inputs_json_file),
                evidence_status=args.evidence_status, code_state_ids=args.code_state_ids,
                artifact_ids=args.artifact_ids, source_refs=args.source_refs,
                supports_outputs=args.supports_outputs, evidence_type=args.evidence_type,
                evidence_summary=args.evidence_summary)
            p = tool_run_payload(r.run)
            if r.evidence is not None:
                p["evidence_id"] = r.evidence.evidence_id
                p["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **asdict(r.evidence)})
            return require_valid_public_surface("tool_run_record", p)
    if args.command == "knowledge" and args.knowledge_command == "connectors":
            return require_valid_public_surface("knowledge_connector_catalog", describe_knowledge_connectors())
    return _CLI_UNHANDLED
