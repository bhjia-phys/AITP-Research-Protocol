"""Audit canonical memory entries that originated from legacy global L2 imports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths


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
    return {
        "entry_id": entry_id,
        "topic_id": _text(frontmatter.get("topic_id")),
        "source_topic_id": _text(frontmatter.get("source_topic_id")),
        "source_claim_id": _text(frontmatter.get("source_claim_id")),
        "status": _text(frontmatter.get("status")),
        "memory_kind": _text(frontmatter.get("memory_kind")),
        "source_packet_id": _text(frontmatter.get("source_packet_id")),
        "source_path": source_path,
        "canonical_rel_path": path.relative_to(ws.root).as_posix(),
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
