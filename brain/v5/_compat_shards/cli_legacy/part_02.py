# Compatibility shard 2 for cli_legacy.
from __future__ import annotations

def dispatch_legacy_command(args, ws) -> dict:
    if args.legacy_command == "migrate":
        result = migrate_legacy_topic_to_v5(
            ws,
            args.topic_dir,
            context_id=args.context_id,
            session_id=args.session_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_migration_result", result)}
    if args.legacy_command == "curated-migrate":
        result = migrate_curated_legacy_topic_to_v5(
            ws,
            args.topic_dir,
            context_id=args.context_id,
            session_id=args.session_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_migration_result", result)}
    if args.legacy_command == "curated-known-topics":
        return {
            "ok": True,
            "kind": "curated_legacy_topic_catalog",
            "topics": known_curated_legacy_topics(),
            "summary_inputs_trusted": False,
        }
    if args.legacy_command == "migration-audit":
        audit = audit_legacy_migration_coverage(ws, migration_dir=args.migration_dir or None)
        payload = {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", audit)}
        if getattr(args, "compact", False):
            return compact_legacy_migration_coverage_audit(payload)
        return payload
    if args.legacy_command == "migration-accounting-run":
        run_dir = write_legacy_migration_accounting_run(
            ws,
            legacy_root=args.legacy_root or None,
            run_id=args.run_id,
        )
        audit = audit_legacy_migration_coverage(ws, migration_dir=run_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_migration_coverage_audit", audit)}
        if getattr(args, "compact", False):
            return compact_legacy_migration_coverage_audit(payload)
        return payload
    if args.legacy_command == "l2-graph-manifest":
        manifest = build_legacy_l2_graph_manifest(ws, legacy_l2_dir=args.legacy_l2_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_graph_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_graph_manifest(payload)
        return payload
    if args.legacy_command == "l2-typed-migration-packet":
        packet = build_legacy_l2_typed_migration_packet(ws, legacy_l2_dir=args.legacy_l2_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_typed_migration_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_typed_migration_packet(payload)
        return payload
    if args.legacy_command == "l2-seed-audit":
        audit = audit_canonical_legacy_l2_seeds(ws, sample_limit=args.sample_limit)
        payload = {"ok": True, **require_valid_public_surface("canonical_legacy_l2_seed_audit", audit)}
        if getattr(args, "compact", False):
            return compact_canonical_legacy_l2_seed_audit(payload)
        return payload
    if args.legacy_command == "l2-seed-review-worklist":
        worklist = build_canonical_legacy_l2_seed_review_worklist(
            ws,
            group_limit=args.group_limit,
            sample_limit=args.sample_limit,
        )
        payload = {
            "ok": True,
            **require_valid_public_surface("canonical_legacy_l2_seed_review_worklist", worklist),
        }
        if getattr(args, "compact", False):
            return compact_canonical_legacy_l2_seed_review_worklist(
                payload,
                sample_limit=args.sample_limit,
            )
        return payload
    if args.legacy_command == "l2-seed-review-result":
        result = record_legacy_l2_seed_group_review_result(
            ws,
            group_id=args.group_id,
            status=args.status,
            decision=args.decision,
            summary=args.summary,
            source_family=args.source_family,
            source_object_id=args.source_object_id,
            reviewed_seed_entry_ids=_merge_inline_and_file_values(
                args.reviewed_seed_entry_ids,
                args.reviewed_seed_entry_id_files,
            ),
            reviewed_seed_refs=_merge_inline_and_file_values(
                args.reviewed_seed_refs,
                args.reviewed_seed_ref_files,
            ),
            reviewed_typed_refs=_merge_inline_and_file_values(
                args.reviewed_typed_refs,
                args.reviewed_typed_ref_files,
            ),
            evidence_refs=_merge_inline_and_file_values(
                args.evidence_refs,
                args.evidence_ref_files,
            ),
            validation_result_ids=_merge_inline_and_file_values(
                args.validation_result_ids,
                args.validation_result_id_files,
            ),
            remaining_actions=_merge_inline_and_file_values(
                args.remaining_actions,
                args.remaining_action_files,
            ),
            checkpoint_id=args.checkpoint_id,
            reviewer_role=args.reviewer_role,
        )
        return {
            "ok": True,
            **require_valid_public_surface(
                "legacy_l2_seed_group_review_result_record",
                {"ok": True, **result.__dict__},
            ),
        }
    if args.legacy_command == "l2-obsidian-view":
        bundle = write_legacy_l2_obsidian_view(
            ws,
            legacy_l2_dir=args.legacy_l2_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_l2_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_l2_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "runtime-log-marker-audit":
        audit = build_legacy_runtime_log_marker_audit(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            markers=args.markers,
            expected_min_count=args.expected_min_count,
            raw_log_files=args.raw_log_files,
            orientation_log_files=args.orientation_log_files,
        )
        return {"ok": True, **require_valid_public_surface("legacy_runtime_log_marker_audit", audit)}
    if args.legacy_command == "semantic-review-queue":
        queue = build_legacy_semantic_review_queue(ws, migration_dir=args.migration_dir or None)
        return {"ok": True, **require_valid_public_surface("legacy_semantic_review_queue", queue)}
    if args.legacy_command == "semantic-review-manifest":
        manifest = build_legacy_semantic_review_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_manifest(payload)
        return payload
    if args.legacy_command == "semantic-review-worklist":
        worklist = build_legacy_semantic_review_worklist(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_worklist", worklist)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_worklist(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis":
        queue = build_legacy_semantic_needs_revision_basis_queue(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_needs_revision_basis_queue", queue)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_queue(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis-packet":
        packet = build_legacy_semantic_needs_revision_basis_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {
            "ok": True,
            **require_valid_public_surface("legacy_semantic_needs_revision_basis_packet", packet),
        }
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_packet(payload)
        return payload
    if args.legacy_command == "semantic-needs-revision-basis-obsidian-view":
        bundle = write_legacy_semantic_needs_revision_basis_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {
            "ok": True,
            **require_valid_public_surface("legacy_semantic_needs_revision_basis_obsidian_view_bundle", bundle),
        }
        if getattr(args, "compact", False):
            return compact_legacy_semantic_needs_revision_basis_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "semantic-review-obsidian-view":
        bundle = write_legacy_semantic_review_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "semantic-review-packet":
        packet = build_legacy_semantic_review_packet(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_review_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_review_packet(payload)
        return payload
    if args.legacy_command == "semantic-repair-plan":
        plan = build_legacy_semantic_repair_plan(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_repair_plan", plan)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_repair_plan(payload)
        return payload
    if args.legacy_command == "semantic-repair-manifest":
        manifest = build_legacy_semantic_repair_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_semantic_repair_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_semantic_repair_manifest(payload)
        return payload
    if args.legacy_command == "semantic-repair-apply":
        result = apply_legacy_semantic_repair(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            repair_type=args.repair_type,
            review_id=args.review_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_semantic_repair_apply", result)}
    if args.legacy_command == "source-reconstruction-plan":
        plan = build_legacy_source_reconstruction_plan(ws, migration_dir=args.migration_dir, topic=args.topic)
        return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_plan", plan)}
    if args.legacy_command == "source-reconstruction-manifest":
        manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_manifest", manifest)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_manifest(payload)
        return payload
    if args.legacy_command == "source-reconstruction-obsidian-view":
        bundle = write_legacy_source_reconstruction_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "source-reconstruction-review":
        packet = build_legacy_source_reconstruction_review_packet(ws, migration_dir=args.migration_dir, topic=args.topic)
        payload = {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_review_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_source_reconstruction_review_packet(payload)
        return payload
    if args.legacy_command == "source-metadata-repair-packet":
        packet = build_legacy_source_metadata_repair_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_source_metadata_repair_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_source_metadata_repair_packet(payload)
        return payload
    if args.legacy_command == "executable-evidence-packet":
        packet = build_legacy_executable_evidence_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_executable_evidence_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_executable_evidence_packet(payload)
        return payload
    if args.legacy_command == "human-checkpoint-packet":
        packet = build_legacy_human_checkpoint_packet(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_human_checkpoint_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_human_checkpoint_packet(payload)
        return payload
    if args.legacy_command == "topic-question-backfill-packet":
        packet = build_legacy_topic_question_backfill_packet(ws, migration_dir=args.migration_dir)
        payload = {"ok": True, **require_valid_public_surface("legacy_topic_question_backfill_packet", packet)}
        if getattr(args, "compact", False):
            return compact_legacy_topic_question_backfill_packet(payload)
        return payload
    if args.legacy_command == "human-checkpoint-obsidian-view":
        bundle = write_legacy_human_checkpoint_obsidian_view(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            output_dir=args.output_dir,
        )
        payload = {"ok": True, **require_valid_public_surface("legacy_human_checkpoint_obsidian_view_bundle", bundle)}
        if getattr(args, "compact", False):
            return compact_legacy_human_checkpoint_obsidian_view_bundle(payload)
        return payload
    if args.legacy_command == "source-reconstruction-apply":
        result = apply_legacy_source_reconstruction_repair(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            repair_type=args.repair_type,
            review_id=args.review_id,
        )
        return {"ok": True, **require_valid_public_surface("legacy_source_reconstruction_apply", result)}
    if args.legacy_command == "semantic-review-result":
        result = record_legacy_semantic_review_result(
            ws,
            migration_dir=args.migration_dir,
            topic=args.topic,
            status=args.status,
            summary=args.summary,
            active_claim_id=args.active_claim_id,
            reviewed_legacy_refs=_merge_inline_and_file_values(
                args.reviewed_legacy_refs,
                args.reviewed_legacy_ref_files,
            ),
            reviewed_typed_refs=_merge_inline_and_file_values(
                args.reviewed_typed_refs,
                args.reviewed_typed_ref_files,
            ),
            evidence_refs=_merge_inline_and_file_values(
                args.evidence_refs,
                args.evidence_ref_files,
            ),
            validation_result_ids=_merge_inline_and_file_values(
                args.validation_result_ids,
                args.validation_result_id_files,
            ),
            remaining_actions=_merge_inline_and_file_values(
                args.remaining_actions,
                args.remaining_action_files,
            ),
            checkpoint_id=args.checkpoint_id,
            reviewer_role=args.reviewer_role,
        )
        return {
            "ok": True,
            **require_valid_public_surface(
                "legacy_semantic_review_result_record",
                {"ok": True, **result.__dict__},
            ),
        }
    raise ValueError(f"unsupported legacy command: {args.legacy_command}")

def _merge_inline_and_file_values(inline_values: list[str], file_paths: list[str]) -> list[str]:
    values = [value for value in inline_values if str(value).strip()]
    for path in file_paths:
        values.extend(_read_value_file(path))
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        clean = str(value).strip()
        if clean and clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return unique

def _read_value_file(path: str) -> list[str]:
    target = Path(path)
    text = target.read_text(encoding="utf-8-sig")
    stripped = text.strip().lstrip("\ufeff")
    if not stripped:
        return []
    if stripped.startswith("["):
        payload = json.loads(stripped)
        if not isinstance(payload, list) or not all(isinstance(value, str) for value in payload):
            raise ValueError(f"value file must contain a JSON string array: {path}")
        return payload
    return [line.strip().lstrip("\ufeff") for line in text.splitlines() if line.strip()]
