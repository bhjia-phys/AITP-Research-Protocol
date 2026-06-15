"""Audit canonical memory entries that originated from legacy global L2 imports."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import read_md
from brain.v5.models import LegacyL2SeedGroupReviewResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.store import list_valid_records, write_record


_TERMINAL_REVIEW_DECISIONS = {
    "archive",
    "reassign",
    "promote_candidate",
    "already_represented",
    "irrelevant",
}
_REVIEW_STATUSES = {"passed", "needs_revision", "inconclusive"}
_REVIEW_DECISIONS = _TERMINAL_REVIEW_DECISIONS | {
    "needs_source_reconstruction",
    "needs_topic_alignment",
}


def audit_canonical_legacy_l2_seeds(
    ws: WorkspacePaths,
    *,
    sample_limit: int = 50,
) -> dict[str, Any]:
    """Scan canonical L2 memory for legacy seeds without changing memory state."""

    memory_dir = ws.root / "memory" / "l2" / "entries"
    all_files = sorted(memory_dir.glob("*.md")) if memory_dir.exists() else []
    seeds: list[dict[str, Any]] = []
    for path in all_files:
        frontmatter = _read_frontmatter(path)
        if not _is_legacy_l2_seed(path, frontmatter):
            continue
        seeds.append(_seed_entry(path, frontmatter, ws=ws))

    status_counts = Counter(str(item["status"] or "_missing") for item in seeds)
    topic_counts = Counter(str(item["topic_id"] or "_missing") for item in seeds)
    kind_counts = Counter(str(item["memory_kind"] or "_missing") for item in seeds)
    active_seed_count = status_counts.get("active", 0)
    return {
        "kind": "canonical_legacy_l2_seed_audit",
        "canonical_store": str(ws.root),
        "memory_entries_dir": str(memory_dir),
        "total_memory_file_count": len(all_files),
        "legacy_seed_count": len(seeds),
        "active_legacy_seed_count": active_seed_count,
        "legacy_seed_topic_count": len(topic_counts),
        "status_counts": dict(sorted(status_counts.items())),
        "topic_counts": dict(sorted(topic_counts.items())),
        "memory_kind_counts": dict(sorted(kind_counts.items())),
        "sample_entries": seeds[:sample_limit],
        "quarantine_status": (
            "active_seed_leak_detected"
            if active_seed_count
            else "canonical_legacy_l2_seeds_require_review"
            if seeds
            else "no_canonical_legacy_l2_seeds"
        ),
        "next_actions": _next_actions(seeds=seeds, active_seed_count=active_seed_count),
        "truth_source": "canonical_memory_l2_seed_scan",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def build_canonical_legacy_l2_seed_review_worklist(
    ws: WorkspacePaths,
    *,
    group_limit: int = 50,
    sample_limit: int = 5,
) -> dict[str, Any]:
    """Group canonical legacy L2 seeds into reviewable, non-trusting batches."""

    audit = audit_canonical_legacy_l2_seeds(ws, sample_limit=0)
    memory_dir = ws.root / "memory" / "l2" / "entries"
    seed_entries: list[dict[str, Any]] = []
    if memory_dir.exists():
        for path in sorted(memory_dir.glob("*.md")):
            frontmatter = _read_frontmatter(path)
            if _is_legacy_l2_seed(path, frontmatter):
                seed_entries.append(_seed_entry(path, frontmatter, ws=ws))
    groups = _seed_groups(
        seed_entries,
        ws=ws,
        sample_limit=max(0, int(sample_limit)),
    )
    review_results = _latest_group_review_results(ws)
    groups = [
        _attach_group_review_result(group, review_results.get(str(group.get("group_id") or "")))
        for group in groups
    ]
    groups.sort(
        key=lambda group: (
            bool(group.get("terminal_review_recorded")),
            not bool(group.get("latest_review_result")),
            -int(group.get("priority_score") or 0),
            str(group.get("topic_id") or ""),
            str(group.get("target_topic_id") or ""),
            str(group.get("source_claim_id") or ""),
            str(group.get("memory_role") or ""),
        )
    )
    blocking_counts = Counter(
        blocking_class
        for group in groups
        if not group.get("terminal_review_recorded")
        for blocking_class in group.get("blocking_classes", [])
    )
    open_groups = [group for group in groups if not group.get("terminal_review_recorded")]
    reviewed_groups = [group for group in groups if group.get("latest_review_result")]
    terminal_groups = [group for group in groups if group.get("terminal_review_recorded")]
    open_group_ids = {str(group.get("group_id") or "") for group in open_groups}
    topic_mismatch_count = sum(
        1
        for seed in seed_entries
        if seed.get("topic_scope_mismatch") and _group_id_for_seed(seed) in open_group_ids
    )
    global_l2_count = sum(
        1
        for seed in seed_entries
        if seed.get("topic_id") == "L2" and _group_id_for_seed(seed) in open_group_ids
    )
    return {
        "kind": "canonical_legacy_l2_seed_review_worklist",
        "canonical_store": str(ws.root),
        "memory_entries_dir": str(memory_dir),
        "legacy_seed_count": audit["legacy_seed_count"],
        "active_legacy_seed_count": audit["active_legacy_seed_count"],
        "legacy_seed_topic_count": audit["legacy_seed_topic_count"],
        "review_group_count": len(groups),
        "open_review_group_count": len(open_groups),
        "reviewed_group_count": len(reviewed_groups),
        "terminal_review_group_count": len(terminal_groups),
        "visible_review_group_count": min(len(groups), max(0, int(group_limit))),
        "topic_scope_mismatch_count": topic_mismatch_count,
        "global_l2_seed_count": global_l2_count,
        "status_counts": dict(sorted(audit["status_counts"].items())),
        "memory_kind_counts": dict(sorted(audit["memory_kind_counts"].items())),
        "review_status_counts": dict(sorted(Counter(str(group.get("review_status") or "pending") for group in groups).items())),
        "review_decision_counts": dict(sorted(Counter(str(group.get("review_decision") or "pending") for group in groups).items())),
        "review_group_blocking_class_counts": dict(sorted(blocking_counts.items())),
        "review_groups": groups[: max(0, int(group_limit))],
        "next_actions": _review_worklist_next_actions(seed_entries, groups),
        "promotion_policy": {
            "legacy_seed_status": "orientation_only",
            "promotion_requires": [
                "semantic_topic_claim_alignment_review",
                "evidence_backed_promotion_packet",
                "passed_failure_mode_review_when_required",
                "approved_human_checkpoint",
            ],
            "forbidden_shortcuts": [
                "do_not_change_legacy_seed_status_to_active",
                "do_not_treat_legacy_l2_refs_as_evidence_refs",
                "do_not_use_topic_level_passed_review_as_per_seed_trust",
            ],
            "can_update_claim_trust": False,
        },
        "truth_source": "canonical_memory_l2_seed_scan_grouped_for_review",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def record_legacy_l2_seed_group_review_result(
    ws: WorkspacePaths,
    *,
    group_id: str,
    status: str,
    decision: str,
    summary: str,
    source_family: str = "",
    source_object_id: str = "",
    reviewed_seed_entry_ids: list[str] | None = None,
    reviewed_seed_refs: list[str] | None = None,
    reviewed_typed_refs: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    validation_result_ids: list[str] | None = None,
    remaining_actions: list[str] | None = None,
    checkpoint_id: str = "",
    reviewer_role: str = "human_or_adversarial_reviewer",
) -> LegacyL2SeedGroupReviewResultRecord:
    """Persist a typed review result for one canonical legacy L2 seed group."""

    target_group_id = _text(group_id)
    if not target_group_id:
        raise ValueError("legacy L2 seed group review requires group_id")
    status = _text(status)
    decision = _text(decision)
    summary = _text(summary)
    source_family = _text(source_family)
    source_object_id = _text(source_object_id)
    if status not in _REVIEW_STATUSES:
        raise ValueError("legacy L2 seed group review status must be passed, needs_revision, or inconclusive")
    if decision not in _REVIEW_DECISIONS:
        raise ValueError("legacy L2 seed group review decision is not allowed")
    if not summary:
        raise ValueError("legacy L2 seed group review summary must not be empty")

    worklist = build_canonical_legacy_l2_seed_review_worklist(
        ws,
        group_limit=1000000,
        sample_limit=1000000,
    )
    group = next((item for item in worklist["review_groups"] if item["group_id"] == target_group_id), None)
    if group is None:
        raise ValueError(f"unknown legacy L2 seed review group: {target_group_id}")

    seed_ids = _clean_list(reviewed_seed_entry_ids)
    seed_refs = _clean_list(reviewed_seed_refs)
    typed_refs = _clean_list(reviewed_typed_refs)
    evidence = _clean_list(evidence_refs)
    validations = _clean_list(validation_result_ids)
    actions = _clean_list(remaining_actions)
    group_seed_ids = {
        str(entry.get("entry_id") or "")
        for entry in group.get("sample_entries", [])
        if str(entry.get("entry_id") or "")
    }
    subgroup_seed_ids = {
        str(entry.get("entry_id") or "")
        for entry in group.get("sample_entries", [])
        if str(entry.get("entry_id") or "")
        and str(entry.get("source_family") or "_missing") == source_family
        and str(entry.get("source_object_id") or "_missing") == source_object_id
    }
    if (source_family or source_object_id) and not subgroup_seed_ids:
        raise ValueError("legacy L2 seed subgroup review requires a known source_family/source_object_id pair")
    if seed_ids and group_seed_ids and not set(seed_ids).issubset(group_seed_ids):
        raise ValueError("reviewed seed entry ids must belong to the reviewed group")
    if seed_ids and subgroup_seed_ids and not set(seed_ids).issubset(subgroup_seed_ids):
        raise ValueError("reviewed seed entry ids must belong to the reviewed semantic subgroup")
    if not any([seed_ids, seed_refs, typed_refs, evidence, validations]):
        raise ValueError("legacy L2 seed group review basis must cite seed ids, seed refs, typed refs, evidence, or validation results")
    if decision == "promote_candidate" and not any([typed_refs, evidence, validations]):
        raise ValueError("promote_candidate review requires typed, evidence, or validation basis")
    if decision in {"archive", "irrelevant", "already_represented"} and not any([seed_ids, seed_refs, typed_refs]):
        raise ValueError("terminal archive/irrelevant/already_represented reviews require seed or typed basis")

    review_id = prefixed_id(
        "legacy-l2-seed-group-review",
        f"{target_group_id}:{source_family}:{source_object_id}:{status}:{decision}:{seed_ids}:{seed_refs}:{typed_refs}:{evidence}:{validations}:{summary}",
        max_slug=72,
    )
    record = LegacyL2SeedGroupReviewResultRecord(
        review_id=review_id,
        group_id=target_group_id,
        topic_id=str(group.get("topic_id") or ""),
        target_topic_id=str(group.get("target_topic_id") or ""),
        source_claim_id=str(group.get("source_claim_id") or ""),
        memory_role=str(group.get("memory_role") or ""),
        source_family=source_family,
        source_object_id=source_object_id,
        status=status,
        decision=decision,
        summary=summary,
        reviewer_role=reviewer_role,
        reviewed_seed_entry_ids=seed_ids,
        reviewed_seed_refs=seed_refs,
        reviewed_typed_refs=typed_refs,
        evidence_refs=evidence,
        validation_result_ids=validations,
        remaining_actions=actions,
        checkpoint_id=_text(checkpoint_id),
        created_at=_now_utc(),
    )
    write_record(
        ws.registry_dir("legacy_l2_seed_group_reviews") / f"{review_id}.md",
        record,
        body=f"# Legacy L2 Seed Group Review: {target_group_id}\n\n**Decision:** {decision}\n\n{summary}\n",
    )
    return record


def _read_frontmatter(path: Path) -> dict[str, Any]:
    try:
        frontmatter, _body = read_md(path)
    except UnicodeDecodeError:
        return {}
    return frontmatter if isinstance(frontmatter, dict) else {}


def _is_legacy_l2_seed(path: Path, frontmatter: dict[str, Any]) -> bool:
    status = _text(frontmatter.get("status"))
    memory_kind = _text(frontmatter.get("memory_kind"))
    source_packet = _text(frontmatter.get("source_packet_id"))
    return (
        path.name.startswith("memory-legacy-l2-")
        or status == "legacy_seed"
        or memory_kind.startswith("legacy_l2_entry")
        or source_packet.startswith("legacy_l2:")
    )


def _seed_entry(path: Path, frontmatter: dict[str, Any], *, ws: WorkspacePaths) -> dict[str, Any]:
    entry_id = _text(frontmatter.get("entry_id")) or path.stem
    source_path = _source_path(frontmatter)
    topic_id = _text(frontmatter.get("topic_id"))
    source_topic_id = _text(frontmatter.get("source_topic_id"))
    scoped_topic_id = _scoped_topic_id(frontmatter)
    source_object_id = _source_object_id(source_path)
    source_family = _source_family(source_object_id)
    return {
        "entry_id": entry_id,
        "topic_id": topic_id,
        "source_topic_id": source_topic_id,
        "scoped_topic_id": scoped_topic_id,
        "source_object_id": source_object_id,
        "source_family": source_family,
        "source_claim_id": _text(frontmatter.get("source_claim_id")),
        "status": _text(frontmatter.get("status")),
        "memory_kind": _text(frontmatter.get("memory_kind")),
        "scope": _text(frontmatter.get("scope")),
        "source_packet_id": _text(frontmatter.get("source_packet_id")),
        "source_path": source_path,
        "canonical_rel_path": path.relative_to(ws.root).as_posix(),
        "topic_scope_mismatch": _topic_scope_mismatch(topic_id, source_topic_id, scoped_topic_id),
        "requires_semantic_l2_reassignment": True,
        "can_update_claim_trust": False,
    }


def _source_path(frontmatter: dict[str, Any]) -> str:
    evidence_refs = frontmatter.get("evidence_refs")
    if isinstance(evidence_refs, list):
        for item in evidence_refs:
            text = _text(item)
            if text.startswith("legacy_l2:"):
                return text.removeprefix("legacy_l2:")
    source_packet = _text(frontmatter.get("source_packet_id"))
    if source_packet.startswith("legacy_l2:"):
        return source_packet.removeprefix("legacy_l2:")
    return ""


def _source_object_id(source_path: str) -> str:
    if not source_path:
        return ""
    return Path(source_path.replace("\\", "/")).stem


def _source_family(source_object_id: str) -> str:
    if not source_object_id:
        return "_missing"
    for prefix in ("claim-", "system-", "method-", "pitfall-", "question-"):
        if source_object_id.startswith(prefix):
            return prefix[:-1]
    if source_object_id.startswith("e-"):
        return "relation"
    return "other"


def _scoped_topic_id(frontmatter: dict[str, Any]) -> str:
    scope = _text(frontmatter.get("scope"))
    for token in scope.replace(",", " ").split():
        if token.startswith("topic:"):
            return token.removeprefix("topic:").strip()
    return ""


def _topic_scope_mismatch(topic_id: str, source_topic_id: str, scoped_topic_id: str) -> bool:
    visible_topics = {value for value in (topic_id, source_topic_id) if value and value != "L2"}
    if scoped_topic_id and visible_topics and scoped_topic_id not in visible_topics:
        return True
    if topic_id == "L2" and scoped_topic_id:
        return True
    return False


def _seed_groups(
    seeds: list[dict[str, Any]],
    *,
    ws: WorkspacePaths,
    sample_limit: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for seed in seeds:
        grouped[_group_key(seed)].append(seed)
    groups = [
        _seed_group_payload(key, group_seeds, ws=ws, sample_limit=sample_limit)
        for key, group_seeds in grouped.items()
    ]
    groups.sort(
        key=lambda group: (
            -group["priority_score"],
            group["topic_id"],
            group["target_topic_id"],
            group["source_claim_id"],
            group["memory_role"],
        )
    )
    return groups


def _group_key(seed: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(seed.get("topic_id") or ""),
        _target_topic_id(seed),
        str(seed.get("source_claim_id") or ""),
        _memory_role(str(seed.get("memory_kind") or "")),
    )


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


def _latest_group_review_results(ws: WorkspacePaths) -> dict[str, LegacyL2SeedGroupReviewResultRecord]:
    records = list_valid_records(
        ws.registry_dir("legacy_l2_seed_group_reviews"),
        LegacyL2SeedGroupReviewResultRecord,
    )
    latest: dict[str, LegacyL2SeedGroupReviewResultRecord] = {}
    for record in records:
        current = latest.get(record.group_id)
        if current is None or _review_sort_key(record) > _review_sort_key(current):
            latest[record.group_id] = record
    return latest


def _attach_group_review_result(
    group: dict[str, Any],
    result: LegacyL2SeedGroupReviewResultRecord | None,
) -> dict[str, Any]:
    if result is None:
        return group
    payload = dict(group)
    review = asdict(result)
    review["orientation_only"] = True
    terminal = result.status == "passed" and result.decision in _TERMINAL_REVIEW_DECISIONS
    payload["review_status"] = result.status
    payload["review_decision"] = result.decision
    payload["latest_review_result"] = review
    payload["terminal_review_recorded"] = terminal
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
