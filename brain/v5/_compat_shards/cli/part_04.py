# Compatibility shard 4 for cli.
from __future__ import annotations

def _dispatch_workspace_02(args, ws):
    if args.command == "knowledge" and args.knowledge_command == "bindings":
            return require_valid_public_surface(
                "knowledge_connector_binding_registry",
                list_knowledge_connector_bindings(
                    ws,
                    connector_id=args.connector_id,
                    include_connector_catalog=args.include_connectors,
                ),
            )
    if args.command == "knowledge" and args.knowledge_command == "bind":
            return require_valid_public_surface(
                "knowledge_connector_binding_registry",
                bind_knowledge_connector(
                    ws,
                    connector_id=args.connector_id,
                    root_uri=args.root_uri,
                    corpus_id=args.corpus_id,
                    label=args.label,
                    file_globs=args.file_globs,
                    domain_hints=args.domain_hints,
                    topic_hints=args.topic_hints,
                    priority=args.priority,
                    status=args.status,
                    notes=args.notes,
                ),
            )
    if args.command == "domain-pack":
            return dispatch_domain_pack_command(args, ws)
    if args.command == "curated-rag" and args.curated_rag_command == "catalog":
            return {
                "ok": True,
                "curated_rag_corpus": require_valid_public_surface("curated_rag_corpus", curated_rag_corpus(ws)),
            }
    if args.command == "curated-rag" and args.curated_rag_command == "search":
            return {
                "ok": True,
                "curated_rag_search_result": require_valid_public_surface(
                    "curated_rag_search_result",
                    search_curated_rag_corpus(args.query, limit=args.limit, base=ws),
                ),
            }
    if args.command == "curated-rag" and args.curated_rag_command == "chunk":
            return {
                "ok": True,
                "curated_rag_chunk": require_valid_public_surface(
                    "curated_rag_chunk",
                    read_curated_rag_chunk(args.chunk_id, base=ws),
                ),
            }
    if args.command == "curated-rag" and args.curated_rag_command == "promotion-draft":
            return {
                "ok": True,
                "curated_rag_promotion_draft": require_valid_public_surface(
                    "curated_rag_promotion_draft",
                    draft_curated_rag_promotion(
                        args.chunk_id,
                        base=ws,
                        topic_id=args.topic_id,
                        claim_id=args.claim_id,
                        connector_id=args.connector_id,
                        promotion_intent=args.promotion_intent,
                    ),
                ),
            }
    if args.command == "curated-rag" and args.curated_rag_command == "ingest":
            return require_valid_public_surface(
                "curated_rag_ingest_result",
                ingest_curated_rag_corpus(
                    ws,
                    paths=args.paths,
                    corpus_id=args.corpus_id,
                    tags=args.tags,
                    domain_hints=args.domain_hints,
                    topic_hints=args.topic_hints,
                    language=args.language,
                    priority=args.priority,
                    chunk_token_limit=args.chunk_token_limit,
                    title_prefix=args.title_prefix,
                    asset_type=args.asset_type,
                    rebuild_index=not args.no_rebuild_index,
                ),
            )
    if args.command == "trace" and args.trace_command == "hook-event" and args.trace_hook_event_command == "persist":
            return require_valid_public_surface("hook_trace_event_record", persist_hook_trace_event(ws, _j(args.payload_json)))
    if args.command == "reference" and args.reference_command == "location" and args.reference_location_command == "record":
            loc = record_reference_location(ws, topic_id=args.topic_id, claim_id=args.claim_id,
                connector_id=args.connector_id, location_type=args.location_type, uri=args.uri, label=args.label,
                source_ref=args.source_ref, external_id=args.external_id, status=args.status, summary=args.summary,
                metadata=_j(args.metadata_json), linked_records=_j(args.linked_records_json))
            return {"ok": True, **require_valid_public_surface("reference_location_record", {"ok": True, **asdict(loc)})}
    if args.command == "legacy":
            return dispatch_legacy_command(args, ws)
    if args.command == "interaction":
            return dispatch_interaction_command(args, ws)
    if args.command == "literature":
            return dispatch_literature_command(args, ws)
    if args.command in VNEXT_COMMANDS:
            return dispatch_vnext_command(args, ws)
    if args.command == "goal":
            return dispatch_goal_command(args, ws)
    if args.command == "harness-feedback":
            return dispatch_harness_feedback_command(args, ws)
    if args.command == "workspace" and args.workspace_command == "inventory":
            workspace_root = args.workspace_root or None
            write_json = _workspace_path_arg(args.write_json, workspace_root)
            write_report = _workspace_path_arg(args.write_report, workspace_root)
            payload = build_workspace_inventory(
                ws,
                workspace_root=workspace_root,
            )
            if write_json:
                write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
                payload = {**payload, "json_path": write_json}
            if write_report:
                payload = {
                    **payload,
                    "report_path": str(write_workspace_inventory_report(payload, write_report)),
                }
            return payload
    if args.command == "workspace" and args.workspace_command == "migration-plan":
            workspace_root = args.workspace_root or None
            inventory_json = _workspace_path_arg(args.inventory_json, workspace_root)
            write_json = _workspace_path_arg(args.write_json, workspace_root)
            write_report = _workspace_path_arg(args.write_report, workspace_root)
            payload = build_workspace_migration_plan(
                ws,
                workspace_root=workspace_root,
                inventory_path=inventory_json or None,
            )
            if write_json:
                write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
                payload = {**payload, "json_path": write_json}
            if write_report:
                payload = {
                    **payload,
                    "report_path": str(write_workspace_migration_plan_report(payload, write_report)),
                }
            return payload
    if args.command == "workspace" and args.workspace_command == "old-store-manifest":
            workspace_root = args.workspace_root or None
            write_json = _workspace_path_arg(args.write_json, workspace_root)
            write_report = _workspace_path_arg(args.write_report, workspace_root)
            payload = build_workspace_old_store_manifest(
                ws,
                workspace_root=workspace_root,
            )
            if write_json:
                write_text_atomic(write_json, json.dumps(_jsonable(payload), ensure_ascii=False, sort_keys=True, indent=2))
                payload = {**payload, "json_path": write_json}
            if write_report:
                payload = {
                    **payload,
                    "report_path": str(write_workspace_old_store_manifest_report(payload, write_report)),
                }
            return payload
    if args.command == "workspace" and args.workspace_command == "file-migration-ledger":
            workspace_root = args.workspace_root or None
            migration_plan_json = _workspace_path_arg(args.migration_plan_json, workspace_root)
            old_store_manifest_json = _workspace_path_arg(args.old_store_manifest_json, workspace_root)
            legacy_accounting_dir = _workspace_path_arg(args.legacy_accounting_dir, workspace_root)
            write_json = _workspace_path_arg(args.write_json, workspace_root)
            write_report = _workspace_path_arg(args.write_report, workspace_root)
            payload = build_workspace_file_migration_ledger(
                ws,
                workspace_root=workspace_root,
                migration_plan_path=migration_plan_json or None,
                old_store_manifest_path=old_store_manifest_json or None,
                legacy_accounting_dir=legacy_accounting_dir or None,
            )
            if write_json or write_report:
                payload = write_workspace_file_migration_ledger(
                    payload,
                    json_path=write_json or None,
                    report_path=write_report or None,
                )
            if args.compact:
                return require_valid_public_surface(
                    "workspace_file_migration_ledger_progress",
                    compact_workspace_file_migration_ledger(payload),
                )
            return require_valid_public_surface("workspace_file_migration_ledger", payload)
    if args.command == "workspace" and args.workspace_command == "migration-health":
            return require_valid_public_surface(
                "workspace_migration_health",
                build_workspace_migration_health(ws, sample_limit=args.sample_limit),
            )
    if args.command == "workspace" and args.workspace_command == "old-store-import":
            workspace_root = args.workspace_root or None
            old_store_manifest_json = _workspace_path_arg(args.old_store_manifest_json, workspace_root)
            write_json = _workspace_path_arg(args.write_json, workspace_root)
            write_report = _workspace_path_arg(args.write_report, workspace_root)
            payload = build_workspace_old_store_import_plan(
                ws,
                workspace_root=workspace_root,
                old_store_manifest_path=old_store_manifest_json or None,
                topics=args.topics,
            )
            if args.apply:
                payload = apply_workspace_old_store_import_plan(payload)
            if write_json or write_report:
                payload = write_workspace_old_store_import_result(
                    payload,
                    json_path=write_json or None,
                    report_path=write_report or None,
                )
            return require_valid_public_surface("workspace_old_store_import_result", payload)
    if args.command == "workspace" and args.workspace_command == "recovery-binding-repair":
            payload = build_workspace_recovery_binding_repair(
                ws,
                topics=args.topics,
            )
            if args.apply:
                payload = apply_workspace_recovery_binding_repair(payload, ws)
            if args.write_json or args.write_report:
                payload = write_workspace_recovery_binding_repair(
                    payload,
                    json_path=args.write_json or None,
                    report_path=args.write_report or None,
                )
            return require_valid_public_surface("workspace_recovery_binding_repair", payload)
    if args.command == "workspace" and args.workspace_command == "recovery-audit":
            payload = build_workspace_recovery_audit(
                ws,
                migration_plan_path=args.migration_plan_json or None,
                topics=args.topics,
            )
            if args.write_json or args.write_report:
                payload = write_workspace_recovery_audit(
                    payload,
                    json_path=args.write_json or None,
                    report_path=args.write_report or None,
                )
            if args.compact:
                return require_valid_public_surface(
                    "workspace_recovery_audit_progress",
                    compact_workspace_recovery_audit(payload),
                )
            return require_valid_public_surface("workspace_recovery_audit", payload)
    if args.command == "workspace" and args.workspace_command == "recording-audit":
            payload = build_workspace_recording_audit(
                ws,
                migration_plan_path=args.migration_plan_json or None,
                topics=args.topics,
                limit=args.limit,
            )
            if args.write_json or args.write_report:
                payload = write_workspace_recording_audit(
                    payload,
                    json_path=args.write_json or None,
                    report_path=args.write_report or None,
                )
            return require_valid_public_surface("workspace_recording_audit", payload)
    if args.command == "summary":
            return dispatch_summary_command(args, ws)
    if args.command == "source":
            return dispatch_source_command(args, ws)
    if args.command == "adapter":
            return dispatch_adapter_command(args, ws)
    return _CLI_UNHANDLED

def _dispatch_workspace_03(args, ws):
    if args.command == "trust":
            if args.trust_command == "audit":
                return require_valid_public_surface("claim_trust_audit", audit_claim_trust(ws, claim_id=args.claim_id))
            if args.trust_command == "update-record":
                record = get_trust_update_record(ws, args.update_id)
                return require_valid_public_surface("trust_update_record", {"ok": True, **asdict(record)})
            req = _trust_update_request_from_args(args)
            if args.trust_command == "preflight":
                return {"ok": True, **require_valid_public_surface("trust_update_preflight", preflight_trust_update(ws, req))}
            return {"ok": True, **require_valid_public_surface("trust_update_apply", apply_trust_update(ws, req))}
    if args.command == "validation":
            return dispatch_validation_command(args, ws)
    if args.command == "memory":
            return dispatch_memory_command(args, ws)
    if args.command == "research-state":
            return dispatch_research_state_command(args, ws)
    if args.command == "authority":
            return dispatch_authority_command(args, ws)
    if args.command == "object" and args.object_command == "record":
            obj = record_physics_object(ws, topic_id=args.topic_id, object_type=args.object_type,
                name=args.name, definition=args.definition, notation=args.notation, assumptions=args.assumptions,
                source_refs=args.source_refs, metadata=_j(args.metadata_json),
                linked_records=_j(args.linked_records_json), status=args.status)
            return {"ok": True, **require_valid_public_surface("physics_object_record", {"ok": True, **asdict(obj)})}
    if args.command == "relation" and args.relation_command == "record":
            rel = record_object_relation(ws, topic_id=args.topic_id, relation_type=args.relation_type,
                subject_id=args.subject_id, object_id=args.object_id, statement=args.statement,
                claim_id=args.claim_id, assumptions=args.assumptions, failure_modes=args.failure_modes,
                source_refs=args.source_refs, evidence_refs=args.evidence_refs, status=args.status)
            return {"ok": True, **require_valid_public_surface("object_relation_record", {"ok": True, **asdict(rel)})}
    if args.command == "sensemaking" and args.sensemaking_command == "report":
            rpt = record_sensemaking_report(ws, topic_id=args.topic_id, claim_id=args.claim_id,
                title=args.title, summary=args.summary, object_ids=args.object_ids,
                relation_ids=args.relation_ids, evidence_refs=args.evidence_refs,
                open_questions=args.open_questions, next_actions=args.next_actions)
            return {"ok": True, **require_valid_public_surface("sensemaking_report_record", {"ok": True, **asdict(rpt)})}
    if args.command == "exploration" and args.exploration_command == "record":
            rec = record_exploratory_record(
                ws,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                session_id=args.session_id,
                exploration_type=args.exploration_type,
                title=args.title,
                focal_question=args.focal_question,
                summary=args.summary,
                original_question=args.original_question,
                local_question=args.local_question,
                status=args.status,
                object_ids=args.object_ids,
                relation_ids=args.relation_ids,
                source_refs=args.source_refs,
                artifact_ids=args.artifact_ids,
                parent_record_ids=args.parent_record_ids,
                derived_record_ids=args.derived_record_ids,
                reasoning_moves=args.reasoning_moves,
                backtrace_targets=args.backtrace_targets,
                candidate_paths=args.candidate_paths,
                relation_path_questions=args.relation_path_questions,
                definition_boundary_questions=args.definition_boundary_questions,
                derivation_backtrace_questions=args.derivation_backtrace_questions,
                source_dependency_questions=args.source_dependency_questions,
                original_question_guard=args.original_question_guard,
                unresolved_points=args.unresolved_points,
                next_actions=args.next_actions,
                human_steering=args.human_steering,
                metadata=_j(args.metadata_json),
            )
            return require_valid_public_surface("exploratory_record", exploratory_record_payload(rec))
    if args.command == "route" and args.route_command == "record":
            route = record_research_route(
                ws,
                topic_id=args.topic_id,
                claim_id=args.claim_id,
                session_id=args.session_id,
                title=args.title,
                route_type=args.route_type,
                status=args.status,
                rationale=args.rationale,
                current_question=args.current_question,
                next_action=args.next_action,
                failure_modes=args.failure_modes,
                source_refs=args.source_refs,
                evidence_refs=args.evidence_refs,
                artifact_ids=args.artifact_ids,
                parent_route_ids=args.parent_route_ids,
                checkpoint_ids=args.checkpoint_ids,
                exploratory_record_ids=args.exploratory_record_ids,
                object_ids=args.object_ids,
                relation_ids=args.relation_ids,
                decision_rationale=args.decision_rationale,
                pivot_reason=args.pivot_reason,
                metadata=_j(args.metadata_json),
            )
            return require_valid_public_surface("research_route_record", research_route_payload(route))
    if args.command == "subagent" and args.subagent_command == "ingest-result":
            result = ingest_subagent_result(
                ws,
                _j(args.packet_json),
                topic_id=args.topic_id,
                result_payload=_j(args.result_json),
            )
            return _subagent_ingestion_payload(result)
    if args.command == "checkpoint" and args.checkpoint_command == "request":
            chk = request_human_checkpoint(ws, topic_id=args.topic_id, claim_id=args.claim_id,
                reason=args.reason, requested_by=args.requested_by, options=args.options)
            return {"ok": True, **require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(chk)})}
    if args.command == "checkpoint" and args.checkpoint_command == "decide":
            dec = decide_human_checkpoint(ws, checkpoint_id=args.checkpoint_id,
                decision=args.decision, rationale=args.rationale, decided_by=args.decided_by)
            return {"ok": True, **require_valid_public_surface("human_checkpoint_record", {"ok": True, **asdict(dec)})}
    if args.command == "checkpoint" and args.checkpoint_command == "preview-batch":
            return require_valid_public_surface("quiet_checkpoint_preview", _quiet_checkpoint_payload(args, ws, apply=False))
    if args.command == "checkpoint" and args.checkpoint_command == "apply-batch":
            return require_valid_public_surface("quiet_checkpoint_batch", _quiet_checkpoint_payload(args, ws, apply=True))
    if args.command == "promotion" and args.promotion_command == "packet" and args.promotion_packet_command == "create":
            pkt = create_promotion_packet(ws, topic_id=args.topic_id, claim_id=args.claim_id,
                proposed_memory_kind=args.proposed_memory_kind, scope=args.scope,
                evidence_refs=args.evidence_refs, validation_result_ids=args.validation_result_ids,
                non_claims=args.non_claims,
                known_failure_modes=args.known_failure_modes, failure_mode_review_checkpoint_id=args.failure_mode_review_checkpoint_id, failure_mode_review_result_id=args.failure_mode_review_result_id)
            return {"ok": True, **require_valid_public_surface("promotion_packet_record", {"ok": True, **asdict(pkt)})}
    if args.command == "promotion" and args.promotion_command == "packet" and args.promotion_packet_command == "apply":
            entry = apply_promotion_packet(ws, packet_id=args.packet_id, checkpoint_id=args.checkpoint_id)
            return {"ok": True, **require_valid_public_surface("memory_entry_record", {"ok": True, **asdict(entry)})}
    return _CLI_UNHANDLED

def _add_trust_request_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("action"); p.add_argument("--session", required=True, dest="session_id")
    p.add_argument("--topic", required=True, dest="topic_id"); p.add_argument("--claim", required=True, dest="claim_id")
    p.add_argument("--requested-state", default=""); p.add_argument("--source-kind", default="")
    p.add_argument("--source-ref", default="")
    p.add_argument("--evidence-ref", action="append", default=[], dest="evidence_refs")
    p.add_argument("--code-state-id", action="append", default=[], dest="code_state_ids")
    p.add_argument("--preflight-token", default="")
    p.add_argument("--rationale", default=""); p.add_argument("--request-id", default="")

def _add_quiet_checkpoint_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("session_id")
    p.add_argument("--claim", default="", dest="claim_id")
    p.add_argument("--run", default="", dest="run_id")
    p.add_argument("--summary", required=True)
    p.add_argument("--input", action="append", default=[], dest="inputs")
    p.add_argument("--output", action="append", default=[], dest="outputs")
    p.add_argument("--changed-file", action="append", default=[], dest="changed_files")
    p.add_argument("--generated-artifact-json", action="append", default=[], dest="generated_artifact_json")
    p.add_argument("--validation-command", action="append", default=[], dest="validation_commands")
    p.add_argument("--observation", action="append", default=[], dest="durable_observations")
    p.add_argument("--claim-boundary-json", default="{}")
    p.add_argument("--next-blocker", action="append", default=[], dest="next_blockers")
    p.add_argument("--artifact-json", action="append", default=[], dest="artifact_json")
    p.add_argument("--source-json", action="append", default=[], dest="source_json")
    p.add_argument("--tool-run-json", action="append", default=[], dest="tool_run_json")
    p.add_argument("--sensemaking-summary", default="")
    p.add_argument("--source-ref", action="append", default=[], dest="source_refs")

def _quiet_checkpoint_payload(args: argparse.Namespace, ws, *, apply: bool) -> dict[str, Any]:
    fn = apply_quiet_checkpoint_batch if apply else preview_quiet_checkpoint_batch
    return fn(
        ws,
        args.session_id,
        claim_id=args.claim_id,
        run_id=args.run_id,
        summary=args.summary,
        inputs=args.inputs,
        outputs=args.outputs,
        changed_files=args.changed_files,
        generated_artifacts=_json_object_list(args.generated_artifact_json),
        validation_commands=args.validation_commands,
        durable_observations=args.durable_observations,
        claim_boundary=_j(args.claim_boundary_json),
        next_blockers=args.next_blockers,
        artifact_specs=_json_object_list(args.artifact_json),
        source_specs=_json_object_list(args.source_json),
        tool_run_specs=_json_object_list(args.tool_run_json),
        sensemaking_summary=args.sensemaking_summary,
        source_refs=args.source_refs,
    )

def _trust_update_request_from_args(args: argparse.Namespace) -> TrustUpdateRequest:
    return TrustUpdateRequest(
        request_id=args.request_id or f"trust-request-{args.session_id}-{args.claim_id}-{args.action}",
        action=args.action, session_id=args.session_id, topic_id=args.topic_id, claim_id=args.claim_id,
        requested_state=args.requested_state, source_kind=args.source_kind, source_ref=args.source_ref,
        evidence_refs=args.evidence_refs, code_state_ids=args.code_state_ids, rationale=args.rationale,
        preflight_token=args.preflight_token,
    )

def _j(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("expected a JSON object")
    return payload

def _j_arg(raw: str, json_file: str = "") -> dict[str, Any]:
    if str(json_file or "").strip():
        path = Path(json_file).expanduser()
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise SystemExit(f"could not read JSON file {path}: {exc}") from exc
    return _j(raw)

def _json_object_list(raw_values: list[str]) -> list[dict[str, Any]]:
    return [_j(raw) for raw in raw_values]

def _subagent_ingestion_payload(result) -> dict[str, Any]:
    payload = result.to_payload()
    payload["evidence"] = require_valid_public_surface("evidence_record", {"ok": True, **payload["evidence"]})
    payload["proposal"] = require_valid_public_surface("sensemaking_report_record", {"ok": True, **payload["proposal"]})
    return {"ok": True, **payload}
