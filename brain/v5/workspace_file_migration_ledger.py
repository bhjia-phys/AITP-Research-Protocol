"""File-level migration ledger for retiring mixed AITP workspace stores."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.workspace_migration_plan import build_workspace_migration_plan
from brain.v5.workspace_old_store_manifest import build_workspace_old_store_manifest
from brain.v5.workspace_migration_discovery import (
    latest_legacy_accounting_dir,
    latest_workspace_migration_plan,
    latest_workspace_old_store_manifest,
)


def build_workspace_file_migration_ledger(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None = None,
    migration_plan_path: str | Path | None = None,
    old_store_manifest_path: str | Path | None = None,
    legacy_accounting_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Build a no-omission file-level import/archive/review ledger.

    The ledger deliberately records decisions, not trust.  It is the bridge
    between coarse topic migration planning and the user's stronger requirement
    that every old-format file has an explicit fate before old stores are
    retired.
    """

    plan_path = Path(migration_plan_path) if migration_plan_path else latest_workspace_migration_plan(ws)
    manifest_path = Path(old_store_manifest_path) if old_store_manifest_path else latest_workspace_old_store_manifest(ws)
    legacy_dir = Path(legacy_accounting_dir) if legacy_accounting_dir else latest_legacy_accounting_dir(ws)

    plan = _load_json(plan_path) if plan_path else build_workspace_migration_plan(
        ws,
        workspace_root=workspace_root,
    )
    old_manifest = (
        _load_json(manifest_path)
        if manifest_path
        else build_workspace_old_store_manifest(ws, workspace_root=workspace_root)
    )
    topic_actions = {
        str(row.get("topic_id") or ""): str(row.get("plan_action") or "")
        for row in plan.get("topic_rows", [])
        if isinstance(row, dict)
    }

    decisions: list[dict[str, Any]] = []
    for store in old_manifest.get("stores", []):
        if not isinstance(store, dict):
            continue
        decisions.extend(_old_store_decisions(store, topic_actions))

    legacy_payload = _legacy_accounting_payload(legacy_dir)
    if legacy_payload is not None:
        decisions.extend(_legacy_accounting_decisions(legacy_payload, topic_actions))

    decision_counts = Counter(str(item["recommended_decision"]) for item in decisions)
    status_counts = Counter(str(item["review_status"]) for item in decisions)
    source_counts = Counter(str(item["source_family"]) for item in decisions)
    topic_counts = Counter(str(item.get("topic_id") or "_unassigned") for item in decisions)
    blocking = [item for item in decisions if item["blocks_old_store_retirement"]]
    root_l2_risk = _root_l2_global_memory_summary(decisions)

    expected_old = int((old_manifest.get("summary") or {}).get("file_count") or 0)
    expected_legacy = int((legacy_payload or {}).get("expected_file_count") or 0)
    expected_total = expected_old + expected_legacy
    return {
        "kind": "aitp_workspace_file_migration_ledger",
        "workspace_root": str(plan.get("workspace_root") or ""),
        "canonical_topics_root": str(plan.get("canonical_topics_root") or ws.base),
        "canonical_store": str(plan.get("canonical_store") or ws.root),
        "migration_plan_source": str(plan_path or "generated_workspace_migration_plan"),
        "old_store_manifest_source": str(manifest_path or "generated_workspace_old_store_manifest"),
        "legacy_accounting_source": str(legacy_dir or ""),
        "summary": {
            "file_decision_count": len(decisions),
            "expected_old_store_file_count": expected_old,
            "expected_legacy_file_count": expected_legacy,
            "expected_total_file_count": expected_total,
            "no_omission_check": len(decisions) == expected_total,
            "blocking_file_count": len(blocking),
            "decision_counts": dict(sorted(decision_counts.items())),
            "review_status_counts": dict(sorted(status_counts.items())),
            "source_family_counts": dict(sorted(source_counts.items())),
            "topic_file_counts": dict(sorted(topic_counts.items())),
            "old_store_retirement_safe": len(blocking) == 0,
            "semantic_review_required": any(item["review_status"] == "semantic_review_required" for item in decisions),
            "root_l2_global_memory_decision_count": root_l2_risk["decision_count"],
            "root_l2_global_memory_topic_count": root_l2_risk["topic_count"],
            "root_l2_global_memory_entries_per_topic": root_l2_risk["entries_per_topic"],
            "root_l2_global_memory_review_status_counts": root_l2_risk["review_status_counts"],
            "root_l2_global_memory_replay_key_count": root_l2_risk["replay_key_count"],
            "root_l2_global_memory_max_topic_repetition": root_l2_risk["max_topic_repetition"],
            "root_l2_global_memory_uniform_topic_copy_pattern": root_l2_risk["uniform_topic_copy_pattern"],
            "root_l2_global_memory_risk": root_l2_risk["risk"],
            "root_l2_global_memory_risk_triggers": root_l2_risk["risk_triggers"],
            "root_l2_global_memory_risk_reason": root_l2_risk["risk_reason"],
        },
        "file_decisions": decisions,
        "retirement_gate": {
            "old_store_retirement_safe": len(blocking) == 0,
            "why_not_safe_now": (
                "Root L2 memory entries show a cross-topic replay/misassignment risk; "
                "resolve or archive those entries before retiring old stores."
                if root_l2_risk["risk"]
                else "Some old-format files still require import review, semantic review, "
                "or explicit archive decisions."
                if blocking
                else "Every manifested old-format file has a non-blocking file decision."
            ),
            "blocking_decision_refs": [item["decision_ref"] for item in blocking[:200]],
            "blocking_decision_ref_count": len(blocking),
            "root_l2_global_memory_risk": root_l2_risk["risk"],
            "root_l2_global_memory_risk_summary": root_l2_risk["risk_reason"],
            "root_l2_global_memory_sample_refs": root_l2_risk["sample_decision_refs"],
        },
        "truth_source": "file_manifest_plus_topic_migration_plan",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_workspace_file_migration_ledger_markdown(payload: dict[str, Any], *, max_rows: int = 120) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# AITP File Migration Ledger",
        "",
        "This is a file-level import/archive/review ledger. It does not update claim trust.",
        "",
        f"- Workspace root: `{payload.get('workspace_root', '')}`",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- File decisions: `{summary.get('file_decision_count', 0)}`",
        f"- No-omission check: `{str(summary.get('no_omission_check', False)).lower()}`",
        f"- Blocking files: `{summary.get('blocking_file_count', 0)}`",
        f"- Old store retirement safe now: `{str(summary.get('old_store_retirement_safe', False)).lower()}`",
        "",
        "## Decision Counts",
        "",
    ]
    for key, value in (summary.get("decision_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Review Status Counts", ""])
    for key, value in (summary.get("review_status_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Root L2 Global Memory Risk", ""])
    lines.extend(
        [
            f"- Risk: `{str(summary.get('root_l2_global_memory_risk', False)).lower()}`",
            f"- Root L2 decisions: `{summary.get('root_l2_global_memory_decision_count', 0)}`",
            f"- Topics touched by root L2 entries: `{summary.get('root_l2_global_memory_topic_count', 0)}`",
            f"- Uniform entries per topic: `{summary.get('root_l2_global_memory_entries_per_topic', 0)}`",
            f"- Uniform copy pattern: `{str(summary.get('root_l2_global_memory_uniform_topic_copy_pattern', False)).lower()}`",
            f"- Replayed entry-key count: `{summary.get('root_l2_global_memory_replay_key_count', 0)}`",
            f"- Risk triggers: `{', '.join(summary.get('root_l2_global_memory_risk_triggers', []) or [])}`",
            f"- Reason: {summary.get('root_l2_global_memory_risk_reason', '')}",
        ]
    )
    lines.extend(
        [
            "",
            "## First File Decisions",
            "",
            "| Ref | Topic | Source | Path | Decision | Review Status | Blocks Retirement |",
            "|---|---|---|---|---|---|---:|",
        ]
    )
    for item in payload.get("file_decisions", [])[:max_rows]:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| {ref} | {topic} | {source} | `{path}` | {decision} | {status} | {blocks} |".format(
                ref=_cell(item.get("decision_ref", "")),
                topic=_cell(item.get("topic_id") or "_unassigned"),
                source=_cell(item.get("source_family", "")),
                path=_cell(item.get("source_path", "")),
                decision=_cell(item.get("recommended_decision", "")),
                status=_cell(item.get("review_status", "")),
                blocks=str(item.get("blocks_old_store_retirement", False)).lower(),
            )
        )
    if int(summary.get("file_decision_count") or 0) > max_rows:
        lines.extend(["", f"Showing first `{max_rows}` rows. Use the JSON ledger for the complete file list."])
    lines.extend(
        [
            "",
            "## Rule",
            "",
            "- No old store deletion is safe until every blocking file decision is resolved or explicitly archived.",
            "- File decisions are migration control records; they do not promote claims or validate evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_workspace_file_migration_ledger(
    payload: dict[str, Any],
    *,
    json_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> dict[str, Any]:
    """Write JSON and/or Markdown views for a file migration ledger."""

    result = dict(payload)
    if json_path:
        path = Path(json_path)
        write_text_atomic(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        result["json_path"] = str(path)
    if report_path:
        path = Path(report_path)
        write_text_atomic(path, render_workspace_file_migration_ledger_markdown(payload))
        result["report_path"] = str(path)
    return result


def compact_workspace_file_migration_ledger(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a compact progress payload suitable for agent startup/recovery."""

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    decisions = [item for item in payload.get("file_decisions", []) if isinstance(item, dict)]
    blockers = [item for item in decisions if item.get("blocks_old_store_retirement")]
    return {
        "kind": "aitp_workspace_file_migration_ledger_progress",
        "workspace_root": payload.get("workspace_root", ""),
        "canonical_topics_root": payload.get("canonical_topics_root", ""),
        "file_decision_count": summary.get("file_decision_count", 0),
        "expected_total_file_count": summary.get("expected_total_file_count", 0),
        "no_omission_check": summary.get("no_omission_check", False),
        "blocking_file_count": summary.get("blocking_file_count", 0),
        "decision_counts": summary.get("decision_counts", {}),
        "review_status_counts": summary.get("review_status_counts", {}),
        "top_blocking_decision_refs": [item.get("decision_ref", "") for item in blockers[:20]],
        "top_blocking_topics": _top_values(blockers, "topic_id"),
        "old_store_retirement_safe": summary.get("old_store_retirement_safe", False),
        "semantic_review_required": summary.get("semantic_review_required", False),
        "root_l2_global_memory_decision_count": summary.get("root_l2_global_memory_decision_count", 0),
        "root_l2_global_memory_topic_count": summary.get("root_l2_global_memory_topic_count", 0),
        "root_l2_global_memory_entries_per_topic": summary.get("root_l2_global_memory_entries_per_topic", 0),
        "root_l2_global_memory_replay_key_count": summary.get("root_l2_global_memory_replay_key_count", 0),
        "root_l2_global_memory_max_topic_repetition": summary.get("root_l2_global_memory_max_topic_repetition", 0),
        "root_l2_global_memory_uniform_topic_copy_pattern": summary.get("root_l2_global_memory_uniform_topic_copy_pattern", False),
        "root_l2_global_memory_risk": summary.get("root_l2_global_memory_risk", False),
        "root_l2_global_memory_risk_triggers": summary.get("root_l2_global_memory_risk_triggers", []),
        "root_l2_global_memory_risk_reason": summary.get("root_l2_global_memory_risk_reason", ""),
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _old_store_decisions(store: dict[str, Any], topic_actions: dict[str, str]) -> list[dict[str, Any]]:
    label = str(store.get("label") or "")
    base_path = str(store.get("path") or "")
    decisions: list[dict[str, Any]] = []
    for item in store.get("files", []):
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic_id") or "")
        category = str(item.get("category") or "")
        family = str(item.get("registry_family") or "")
        action = topic_actions.get(topic, "")
        recommended, status, blocks, reason, target = _old_store_file_fate(
            category=category,
            family=family,
            topic_action=action,
            has_topic=bool(topic),
        )
        path = str(item.get("path") or "")
        decisions.append(
            {
                "decision_ref": f"old_store:{label}:{path}",
                "source_family": "old_store",
                "source_store_label": label,
                "source_store_path": base_path,
                "source_path": path,
                "topic_id": topic,
                "source_category": category,
                "registry_family": family,
                "session_id": str(item.get("session_id") or ""),
                "sha256": str(item.get("sha256") or ""),
                "size_bytes": int(item.get("size_bytes") or 0),
                "recommended_decision": recommended,
                "review_status": status,
                "decision_reason": reason,
                "target_surface": target,
                "topic_plan_action": action,
                "safe_to_auto_import": False,
                "blocks_old_store_retirement": blocks,
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            }
        )
    return decisions


def _legacy_accounting_decisions(payload: dict[str, Any], topic_actions: dict[str, str]) -> list[dict[str, Any]]:
    migration_dir = str(payload.get("migration_dir") or "")
    decisions: list[dict[str, Any]] = []
    for item in payload.get("files", []):
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic") or "")
        path = str(item.get("path") or "")
        mode = str(item.get("accounting_mode") or "")
        mapped_as = str(item.get("mapped_as") or "")
        action = topic_actions.get(topic, "semantic_review_required")
        recommended = "typed_import_candidate" if mode == "typed_mapping" else "archive_reference"
        status = "semantic_review_required"
        reason = (
            "legacy file is mapped to a typed v5 surface but still requires semantic review"
            if mode == "typed_mapping"
            else "legacy file is preserved by archive reference and must remain available to semantic review"
        )
        decisions.append(
            {
                "decision_ref": f"legacy_l0_l4:{topic}:{path}",
                "source_family": "legacy_l0_l4",
                "source_store_label": "legacy_topics_root",
                "source_store_path": str(payload.get("legacy_root") or ""),
                "source_path": path,
                "topic_id": topic,
                "source_category": "legacy_topic_file",
                "registry_family": "",
                "session_id": "",
                "sha256": str(item.get("sha256") or ""),
                "size_bytes": int(item.get("size_bytes") or 0),
                "recommended_decision": recommended,
                "review_status": status,
                "decision_reason": reason,
                "target_surface": mapped_as or "legacy_archive_reference",
                "topic_plan_action": action,
                "migration_dir": migration_dir,
                "safe_to_auto_import": False,
                "blocks_old_store_retirement": True,
                "summary_inputs_trusted": False,
                "can_update_kernel_state": False,
                "can_update_claim_trust": False,
            }
        )
    return decisions


def _root_l2_global_memory_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    root_l2 = [
        item
        for item in decisions
        if item.get("source_family") == "old_store"
        and item.get("source_store_label") == "workspace_root_store"
        and item.get("source_category") == "memory_entry"
        and str(item.get("source_path") or "").startswith("memory/l2/entries/")
    ]
    topic_counts = Counter(str(item.get("topic_id") or "_unassigned") for item in root_l2)
    status_counts = Counter(str(item.get("review_status") or "") for item in root_l2)
    replay_topics: dict[str, set[str]] = defaultdict(set)
    for item in root_l2:
        replay_key = _root_l2_replay_key(str(item.get("source_path") or ""))
        if replay_key:
            replay_topics[replay_key].add(str(item.get("topic_id") or "_unassigned"))

    replayed_keys = {key: topics for key, topics in replay_topics.items() if len(topics) > 1}
    uniform_counts = set(topic_counts.values())
    entries_per_topic = next(iter(uniform_counts)) if len(uniform_counts) == 1 and topic_counts else 0
    uniform_multi_topic = len(topic_counts) > 1 and entries_per_topic > 0
    max_topic_repetition = max((len(topics) for topics in replay_topics.values()), default=0)
    risk_triggers = []
    if replayed_keys:
        risk_triggers.append("replayed_entry_keys")
    if uniform_multi_topic:
        risk_triggers.append("uniform_entries_per_topic")
    risk = bool(root_l2) and len(topic_counts) > 1 and bool(risk_triggers)
    if risk:
        risk_reason = (
            "root workspace L2 memory entries appear under multiple topic prefixes; "
            "agents must not treat them as topic-local evidence until each entry is reassigned, "
            "typed-imported, or archived."
        )
    elif root_l2:
        risk_reason = "root workspace L2 memory entries exist and still require ordinary file-level review."
    else:
        risk_reason = "no root workspace L2 memory entries were found in the old-store manifest."
    top_replayed = sorted(
        (
            {
                "entry_key": key,
                "topic_count": len(topics),
                "topics": sorted(topics)[:12],
            }
            for key, topics in replayed_keys.items()
        ),
        key=lambda row: (-int(row["topic_count"]), str(row["entry_key"])),
    )
    return {
        "decision_count": len(root_l2),
        "topic_count": len(topic_counts),
        "entries_per_topic": entries_per_topic,
        "topic_file_counts": dict(sorted(topic_counts.items())),
        "review_status_counts": dict(sorted(status_counts.items())),
        "replay_key_count": len(replayed_keys),
        "max_topic_repetition": max_topic_repetition,
        "uniform_topic_copy_pattern": uniform_multi_topic,
        "top_replayed_entry_keys": top_replayed[:12],
        "sample_decision_refs": [str(item.get("decision_ref") or "") for item in root_l2[:20]],
        "risk": risk,
        "risk_triggers": risk_triggers,
        "risk_reason": risk_reason,
    }


def _root_l2_replay_key(source_path: str) -> str:
    name = Path(source_path).name
    marker = "-l2-entries-"
    if marker in name:
        return name.split(marker, 1)[1]
    return name


def _old_store_file_fate(
    *,
    category: str,
    family: str,
    topic_action: str,
    has_topic: bool,
) -> tuple[str, str, bool, str, str]:
    if category in {"registry_record", "memory_entry"}:
        target = "canonical_memory/l2/entries" if category == "memory_entry" else (
            f"canonical_registry/{family}" if family else "canonical_registry"
        )
        if topic_action in {"root_store_import_review_required", "repair_canonical_topic_shell_and_merge_required"}:
            return (
                "typed_import_candidate",
                "import_review_required",
                True,
                "root/nested typed record is not yet represented in the canonical topic graph",
                target,
            )
        if topic_action == "duplicate_store_review_required":
            return (
                "typed_import_candidate",
                "duplicate_review_required",
                True,
                "root-local typed record must be diffed against canonical records before import or archive",
                target,
            )
        return (
            "semantic_review_basis",
            "semantic_review_required",
            True,
            "typed record belongs to a topic that still has legacy/canonical semantic-review work",
            target,
        )
    if category in {"topic_shell", "runtime_session"}:
        return (
            "archive_reference",
            "archive_decision_required",
            True,
            "topic shell or runtime session must be explicitly archived or promoted before old-store retirement",
            "archive_manifest",
        )
    if category in {"derived_surface", "migration_artifact", "runtime_artifact", "store_metadata"}:
        return (
            "archive_reference",
            "archive_decision_required" if has_topic else "archive_accounted",
            bool(has_topic),
            "noncanonical store support file is preserved by hash manifest",
            "archive_manifest",
        )
    return (
        "archive_reference",
        "archive_decision_required",
        True,
        "unclassified old-store file requires an explicit archive/import decision",
        "archive_manifest",
    )


def _legacy_accounting_payload(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    root = Path(path)
    file_manifest = _load_json(root / "file_manifest.json")
    summary_path = root / "migration_summary.json"
    summary = _load_json(summary_path) if summary_path.exists() else {}
    return {
        "migration_dir": str(root),
        "legacy_root": str(summary.get("legacy_root") or ""),
        "expected_file_count": len(file_manifest),
        "files": file_manifest,
    }


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _top_values(items: list[dict[str, Any]], key: str, *, limit: int = 12) -> list[str]:
    counts = Counter(str(item.get(key) or "_unassigned") for item in items)
    return [value for value, _count in counts.most_common(limit)]


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
