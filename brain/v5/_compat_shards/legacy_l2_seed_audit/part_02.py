# Compatibility shard 2 for legacy_l2_seed_audit.
from __future__ import annotations

def _seed_group_payload(
    key: tuple[str, str, str, str],
    seeds: list[dict[str, Any]],
    *,
    ws: WorkspacePaths,
    sample_limit: int,
) -> dict[str, Any]:
    topic_id, target_topic_id, source_claim_id, memory_role = key
    kind_counts = Counter(str(seed.get("memory_kind") or "_missing") for seed in seeds)
    source_topic_counts = Counter(str(seed.get("source_topic_id") or "_missing") for seed in seeds)
    scoped_topic_counts = Counter(str(seed.get("scoped_topic_id") or "_missing") for seed in seeds)
    source_family_counts = Counter(str(seed.get("source_family") or "_missing") for seed in seeds)
    semantic_subgroups = _semantic_subgroups(seeds)
    blocking_classes = _group_blocking_classes(seeds, topic_id=topic_id, target_topic_id=target_topic_id)
    if len(semantic_subgroups) > 1 and "semantic_subgroup_split_required" not in blocking_classes:
        blocking_classes.append("semantic_subgroup_split_required")
    priority_score = _group_priority_score(memory_role=memory_role, blocking_classes=blocking_classes, count=len(seeds))
    return {
        "group_id": _group_id(topic_id, target_topic_id, source_claim_id, memory_role),
        "topic_id": topic_id,
        "target_topic_id": target_topic_id,
        "source_claim_id": source_claim_id,
        "memory_role": memory_role,
        "seed_count": len(seeds),
        "priority_score": priority_score,
        "blocking_classes": blocking_classes,
        "review_focus": _group_review_focus(memory_role=memory_role, blocking_classes=blocking_classes),
        "memory_kind_counts": dict(sorted(kind_counts.items())),
        "source_topic_counts": dict(sorted(source_topic_counts.items())),
        "scoped_topic_counts": dict(sorted(scoped_topic_counts.items())),
        "source_family_counts": dict(sorted(source_family_counts.items())),
        "semantic_mix_detected": len(semantic_subgroups) > 1,
        "semantic_subgroup_count": len(semantic_subgroups),
        "semantic_subgroups": semantic_subgroups,
        "topic_scope_mismatch_count": sum(1 for seed in seeds if seed.get("topic_scope_mismatch")),
        "sample_entries": seeds[:sample_limit],
        "review_actions": _group_review_actions(
            ws,
            group_id=_group_id(topic_id, target_topic_id, source_claim_id, memory_role),
            topic_id=topic_id,
            target_topic_id=target_topic_id,
            source_claim_id=source_claim_id,
            memory_role=memory_role,
        ),
        "review_status": "pending",
        "review_decision": "pending",
        "latest_review_result": {},
        "terminal_review_recorded": False,
        "can_update_claim_trust": False,
    }

def _group_id_for_seed(seed: dict[str, Any]) -> str:
    topic_id, target_topic_id, source_claim_id, memory_role = _group_key(seed)
    return _group_id(topic_id, target_topic_id, source_claim_id, memory_role)

def _target_topic_id(seed: dict[str, Any]) -> str:
    scoped = str(seed.get("scoped_topic_id") or "")
    source = str(seed.get("source_topic_id") or "")
    topic = str(seed.get("topic_id") or "")
    if scoped:
        return scoped
    if source and source != "L2":
        return source
    return topic

def _memory_role(memory_kind: str) -> str:
    if ":" in memory_kind:
        return memory_kind.split(":", 1)[1]
    return memory_kind or "_missing"

def _group_blocking_classes(seeds: list[dict[str, Any]], *, topic_id: str, target_topic_id: str) -> list[str]:
    classes: list[str] = []

    def add(value: str) -> None:
        if value not in classes:
            classes.append(value)

    if topic_id == "L2":
        add("global_l2_topic_reassignment_required")
    if target_topic_id and topic_id and target_topic_id != topic_id:
        add("topic_scope_alignment_required")
    if any(seed.get("topic_scope_mismatch") for seed in seeds):
        add("source_topic_scope_mismatch")
    if any(str(seed.get("status") or "") == "active" for seed in seeds):
        add("active_seed_leak")
    if any(str(seed.get("memory_kind") or "").startswith("legacy_l2_graph_edge:") for seed in seeds):
        add("legacy_graph_edge_relation_review_required")
    if any(str(seed.get("memory_kind") or "").startswith("legacy_l2_graph_node:") for seed in seeds):
        add("legacy_graph_node_object_review_required")
    if any(str(seed.get("memory_kind") or "").startswith("legacy_l2_entry:claim") for seed in seeds):
        add("claim_statement_evidence_review_required")
    return classes or ["semantic_l2_reassignment_required"]

def _semantic_subgroups(seeds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for seed in seeds:
        key = (
            str(seed.get("source_family") or "_missing"),
            str(seed.get("source_object_id") or "_missing"),
        )
        grouped[key].append(seed)
    subgroups: list[dict[str, Any]] = []
    for (source_family, source_object_id), group_seeds in grouped.items():
        memory_kind_counts = Counter(str(seed.get("memory_kind") or "_missing") for seed in group_seeds)
        source_paths = sorted({str(seed.get("source_path") or "") for seed in group_seeds if str(seed.get("source_path") or "")})
        subgroups.append(
            {
                "source_family": source_family,
                "source_object_id": source_object_id,
                "seed_count": len(group_seeds),
                "memory_kind_counts": dict(sorted(memory_kind_counts.items())),
                "source_paths": source_paths[:5],
                "sample_entry_ids": [
                    str(seed.get("entry_id") or "")
                    for seed in group_seeds[:5]
                    if str(seed.get("entry_id") or "")
                ],
                "review_hint": _semantic_subgroup_review_hint(
                    source_family=source_family,
                    source_object_id=source_object_id,
                    seeds=group_seeds,
                ),
                "review_status": "pending",
                "review_decision": "pending",
                "latest_review_result": {},
                "terminal_review_recorded": False,
                "can_update_claim_trust": False,
            }
        )
    subgroups.sort(
        key=lambda item: (
            str(item.get("source_family") or ""),
            str(item.get("source_object_id") or ""),
        )
    )
    return subgroups

def _semantic_subgroup_review_hint(*, source_family: str, source_object_id: str, seeds: list[dict[str, Any]]) -> str:
    if source_family == "relation":
        return "review_relation_edge_for_typed_relation_or_archive"
    if source_family == "claim":
        return "review_claim_scope_and_evidence_before_promotion"
    if source_family in {"system", "method", "pitfall", "question"}:
        return f"review_{source_family}_object_for_topic_reassignment_or_archive"
    if source_object_id and source_object_id != "_missing":
        return "review_source_object_for_topic_reassignment_or_archive"
    if any(str(seed.get("source_path") or "") for seed in seeds):
        return "review_source_path_for_missing_object_id"
    return "reconstruct_missing_source_before_review"

def _group_review_focus(*, memory_role: str, blocking_classes: list[str]) -> list[str]:
    focus: list[str] = []
    if "semantic_subgroup_split_required" in blocking_classes:
        focus.append("split_mixed_seed_group_by_source_object_before_terminal_review")
    if "global_l2_topic_reassignment_required" in blocking_classes:
        focus.append("assign_global_l2_seed_to_target_topic_or_archive")
    if "topic_scope_alignment_required" in blocking_classes or "source_topic_scope_mismatch" in blocking_classes:
        focus.append("verify_topic_scope_source_claim_alignment")
    if "claim" in memory_role:
        focus.append("verify_claim_statement_scope_and_evidence_basis")
        focus.append("promote_only_with_evidence_backed_promotion_packet")
    elif "edge" in memory_role:
        focus.append("convert_valid_relation_edges_to_object_relation_records_or_archive")
    elif "node" in memory_role:
        focus.append("convert_valid_objects_to_physics_object_records_or_archive")
    else:
        focus.append("classify_seed_as_background_method_pitfall_question_or_archive")
    focus.append("keep_legacy_seed_orientation_only_until_review_result")
    return _unique(focus)

def _group_priority_score(*, memory_role: str, blocking_classes: list[str], count: int) -> int:
    score = min(count, 200)
    if "active_seed_leak" in blocking_classes:
        score += 1000
    if "global_l2_topic_reassignment_required" in blocking_classes:
        score += 250
    if "topic_scope_alignment_required" in blocking_classes:
        score += 200
    if "semantic_subgroup_split_required" in blocking_classes:
        score += 90
    if "claim" in memory_role:
        score += 120
    if "edge" in memory_role:
        score += 80
    if "node" in memory_role:
        score += 60
    return score

def _group_id(topic_id: str, target_topic_id: str, source_claim_id: str, memory_role: str) -> str:
    return "legacy-l2-seed-review:" + ":".join(
        _slug(part) for part in (topic_id or "missing-topic", target_topic_id or "missing-target", source_claim_id or "missing-claim", memory_role or "missing-role")
    )

def _group_review_actions(
    ws: WorkspacePaths,
    *,
    group_id: str,
    topic_id: str,
    target_topic_id: str,
    source_claim_id: str,
    memory_role: str,
) -> list[dict[str, Any]]:
    audit_cli = f"aitp-v5 --base {ws.base} legacy l2-seed-review-worklist --group-limit 50 --sample-limit 5"
    memory_audit_cli = (
        f"aitp-v5 --base {ws.base} memory audit --claim {source_claim_id}"
        if source_claim_id
        else ""
    )
    promotion_safe = (
        bool(source_claim_id)
        and "claim" in memory_role
        and bool(target_topic_id)
        and target_topic_id != "L2"
        and target_topic_id == topic_id
    )
    promotion_cli = (
        f"aitp-v5 --base {ws.base} promotion packet create --topic {target_topic_id or topic_id} "
        f"--claim {source_claim_id} --proposed-kind scoped_claim --scope <reviewed-scope> "
        "--evidence-ref <typed-evidence-ref> --failure-mode <failure-mode>"
        if promotion_safe
        else ""
    )
    actions = [
        {
            "action": "review_seed_group",
            "cli": audit_cli,
            "mcp": "aitp_v5_build_canonical_legacy_l2_seed_review_worklist",
            "surface": "canonical_legacy_l2_seed_review_worklist",
            "effect": "orientation_only",
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
        },
        {
            "action": "record_seed_group_review_result",
            "cli": (
                f"aitp-v5 --base {ws.base} legacy l2-seed-review-result "
                f"--group-id {group_id} --status <passed|needs_revision|inconclusive> "
                "--decision <archive|reassign|promote_candidate|already_represented|irrelevant|needs_source_reconstruction|needs_topic_alignment> "
                "--summary <review-summary> --source-family <source-family> "
                "--source-object-id <source-object-id> --seed-entry-id <seed-entry-id-or-ref>"
            ),
            "mcp": "aitp_v5_record_legacy_l2_seed_group_review_result",
            "surface": "legacy_l2_seed_group_review_result_record",
            "effect": "typed_record_write_without_claim_trust",
            "can_update_kernel_state": True,
            "can_update_claim_trust": False,
        }
    ]
    if memory_audit_cli:
        actions.append(
            {
                "action": "audit_current_l2_memory_for_source_claim",
                "cli": memory_audit_cli,
                "mcp": "aitp_v5_audit_l2_memory_context",
                "surface": "l2_memory_audit",
                "effect": "orientation_only",
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            }
        )
    if promotion_cli:
        actions.append(
            {
                "action": "create_reviewed_promotion_packet_after_typed_evidence_exists",
                "cli": promotion_cli,
                "mcp": "aitp_v5_create_promotion_packet",
                "surface": "promotion_packet_record",
                "effect": "typed_record_write_requires_evidence_and_human_gate",
                "can_update_kernel_state": True,
                "can_update_claim_trust": False,
            }
        )
    elif source_claim_id and "claim" in memory_role:
        actions.append(
            {
                "action": "resolve_target_topic_and_claim_before_promotion",
                "cli": audit_cli,
                "mcp": "aitp_v5_build_canonical_legacy_l2_seed_review_worklist",
                "surface": "canonical_legacy_l2_seed_review_worklist",
                "effect": "orientation_only",
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            }
        )
    return actions

def _review_worklist_next_actions(seeds: list[dict[str, Any]], groups: list[dict[str, Any]]) -> list[str]:
    open_groups = [group for group in groups if not group.get("terminal_review_recorded")]
    if not seeds or not open_groups:
        return ["no_canonical_legacy_l2_seed_review_needed"]
    actions = [
        "review_high_priority_seed_groups_before_treating_legacy_l2_as_memory",
        "resolve_global_l2_and_topic_scope_mismatch_groups_first",
        "archive_or_promote_each_group_with_explicit_review_basis",
        "keep_all_legacy_seed_entries_orientation_only_until_reviewed",
    ]
    actions.extend(f"review_group:{group['group_id']}" for group in open_groups[:10])
    return actions

def _latest_review_results(
    ws: WorkspacePaths,
) -> tuple[
    dict[str, LegacyL2SeedGroupReviewResultRecord],
    dict[tuple[str, str, str], LegacyL2SeedGroupReviewResultRecord],
]:
    records = _legacy_records(
        ws.registry_dir("legacy_l2_seed_group_reviews"),
        LegacyL2SeedGroupReviewResultRecord,
    )
    latest_groups: dict[str, LegacyL2SeedGroupReviewResultRecord] = {}
    latest_subgroups: dict[tuple[str, str, str], LegacyL2SeedGroupReviewResultRecord] = {}
    for record in records:
        if record.source_family or record.source_object_id:
            key = (record.group_id, record.source_family, record.source_object_id)
            current = latest_subgroups.get(key)
            if current is None or _review_sort_key(record) > _review_sort_key(current):
                latest_subgroups[key] = record
            continue
        current = latest_groups.get(record.group_id)
        if current is None or _review_sort_key(record) > _review_sort_key(current):
            latest_groups[record.group_id] = record
    return latest_groups, latest_subgroups

def _attach_review_results(
    group: dict[str, Any],
    *,
    group_result: LegacyL2SeedGroupReviewResultRecord | None,
    subgroup_results: dict[tuple[str, str, str], LegacyL2SeedGroupReviewResultRecord],
) -> dict[str, Any]:
    payload = dict(group)
    reviewed_subgroup_count = 0
    terminal_subgroup_count = 0
    status_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    subgroups: list[dict[str, Any]] = []
    group_id = str(group.get("group_id") or "")
    for subgroup in group.get("semantic_subgroups", []):
        if not isinstance(subgroup, dict):
            continue
        next_subgroup = dict(subgroup)
        result = subgroup_results.get(
            (
                group_id,
                str(subgroup.get("source_family") or ""),
                str(subgroup.get("source_object_id") or ""),
            )
        )
        if result is not None:
            review = asdict(result)
            review["orientation_only"] = True
            terminal = result.status == "passed" and result.decision in _TERMINAL_REVIEW_DECISIONS
            next_subgroup["review_status"] = result.status
            next_subgroup["review_decision"] = result.decision
            next_subgroup["latest_review_result"] = review
            next_subgroup["terminal_review_recorded"] = terminal
            reviewed_subgroup_count += 1
            if terminal:
                terminal_subgroup_count += 1
            status_counts[result.status] += 1
            decision_counts[result.decision] += 1
        subgroups.append(next_subgroup)
    payload["semantic_subgroups"] = subgroups
    payload["semantic_subgroup_reviewed_count"] = reviewed_subgroup_count
    payload["semantic_subgroup_terminal_review_count"] = terminal_subgroup_count
    payload["semantic_subgroup_open_review_count"] = reviewed_subgroup_count - terminal_subgroup_count
    payload["semantic_subgroup_review_status_counts"] = dict(sorted(status_counts.items()))
    payload["semantic_subgroup_review_decision_counts"] = dict(sorted(decision_counts.items()))
    if group_result is not None:
        review = asdict(group_result)
        review["orientation_only"] = True
        terminal = group_result.status == "passed" and group_result.decision in _TERMINAL_REVIEW_DECISIONS
        payload["review_status"] = group_result.status
        payload["review_decision"] = group_result.decision
        payload["latest_review_result"] = review
        payload["terminal_review_recorded"] = terminal
        payload["terminal_review_basis"] = "group_review" if terminal else "none"
    if (
        subgroups
        and reviewed_subgroup_count == len(subgroups)
        and terminal_subgroup_count == len(subgroups)
    ):
        payload["terminal_review_recorded"] = True
        payload["terminal_review_basis"] = "semantic_subgroups"
    elif "terminal_review_basis" not in payload:
        payload["terminal_review_basis"] = "none"
    return payload

def _review_sort_key(record: LegacyL2SeedGroupReviewResultRecord) -> tuple[str, str]:
    return (record.created_at or "", record.review_id)

def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def _next_actions(*, seeds: list[dict[str, Any]], active_seed_count: int) -> list[str]:
    if not seeds:
        return ["no_legacy_l2_seed_quarantine_needed"]
    actions: list[str] = []
    if active_seed_count:
        actions.append("demote_or_quarantine_active_legacy_l2_seed_entries_before_agent_recovery")
    actions.extend(
        [
            "keep_legacy_l2_seeds_orientation_only_until_reviewed",
            "review_each_seed_source_claim_topic_alignment",
            "promote_only_reviewed_items_through_evidence_backed_promotion_packets",
            "archive_or_reassign_legacy_l2_seeds_before_retiring_old_stores",
        ]
    )
    return actions

def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_text(item) for item in value if _text(item))
    return " ".join(str(value).split())

def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result

def _clean_list(values: list[str] | None) -> list[str]:
    return [value.strip() for value in values or [] if value.strip()]

def _slug(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value))
    while "--" in text:
        text = text.replace("--", "-")
    return text.strip("-")[:80] or "missing"
