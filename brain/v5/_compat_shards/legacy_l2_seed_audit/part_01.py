# Compatibility shard 1 for legacy_l2_seed_audit.
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

from brain.v5.store import list_valid_records as _list_valid_records, write_record

def _legacy_records(directory, cls):
    return _list_valid_records(directory, cls, operation="legacy_l2_seed_audit")

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
    group_review_results, subgroup_review_results = _latest_review_results(ws)
    groups = [
        _attach_review_results(
            group,
            group_result=group_review_results.get(str(group.get("group_id") or "")),
            subgroup_results=subgroup_review_results,
        )
        for group in groups
    ]
    groups.sort(
        key=lambda group: (
            bool(group.get("terminal_review_recorded")),
            not bool(group.get("latest_review_result") or group.get("semantic_subgroup_reviewed_count")),
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
    reviewed_subgroups = [
        subgroup
        for group in groups
        for subgroup in group.get("semantic_subgroups", [])
        if isinstance(subgroup, dict) and subgroup.get("latest_review_result")
    ]
    terminal_subgroups = [
        subgroup
        for subgroup in reviewed_subgroups
        if subgroup.get("terminal_review_recorded")
    ]
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
        "semantic_subgroup_reviewed_count": len(reviewed_subgroups),
        "semantic_subgroup_terminal_review_count": len(terminal_subgroups),
        "semantic_subgroup_open_review_count": len(reviewed_subgroups) - len(terminal_subgroups),
        "visible_review_group_count": min(len(groups), max(0, int(group_limit))),
        "topic_scope_mismatch_count": topic_mismatch_count,
        "global_l2_seed_count": global_l2_count,
        "status_counts": dict(sorted(audit["status_counts"].items())),
        "memory_kind_counts": dict(sorted(audit["memory_kind_counts"].items())),
        "review_status_counts": dict(sorted(Counter(str(group.get("review_status") or "pending") for group in groups).items())),
        "review_decision_counts": dict(sorted(Counter(str(group.get("review_decision") or "pending") for group in groups).items())),
        "semantic_subgroup_review_status_counts": dict(sorted(Counter(str(subgroup.get("review_status") or "pending") for subgroup in reviewed_subgroups).items())),
        "semantic_subgroup_review_decision_counts": dict(sorted(Counter(str(subgroup.get("review_decision") or "pending") for subgroup in reviewed_subgroups).items())),
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
