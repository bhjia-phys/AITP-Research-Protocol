"""Read-only migration planning for mixed AITP workspace stores."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.workspace_inventory import build_workspace_inventory


def build_workspace_migration_plan(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None = None,
    inventory_path: str | Path | None = None,
    inventory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a no-omission, read-only migration plan for a workspace.

    The plan is a coordination surface: it classifies rows from the workspace
    inventory, identifies retirement blockers for old stores, and names the
    next valid action. It never imports records, updates trust, or mutates topic
    state.
    """

    inv = _load_inventory(ws, workspace_root=workspace_root, inventory_path=inventory_path, inventory=inventory)
    stores = {str(store.get("label")): store for store in inv.get("stores", []) if isinstance(store, dict)}
    canonical_store = stores.get("canonical_topics_store", {})
    root_store = stores.get("workspace_root_store", {})
    nested_store = stores.get("workspace_root_nested_store", {})
    canonical_counts = _topic_counts(canonical_store)
    root_counts = _topic_counts(root_store)
    nested_counts = _topic_counts(nested_store)

    rows = []
    for row in inv.get("topic_migration_rows", []):
        if not isinstance(row, dict):
            continue
        rows.append(
            _plan_row(
                row,
                canonical_count=int(canonical_counts.get(str(row.get("topic_id"))) or 0),
                root_count=int(root_counts.get(str(row.get("topic_id"))) or 0),
                nested_count=int(nested_counts.get(str(row.get("topic_id"))) or 0),
            )
        )

    action_counts = dict(sorted(Counter(item["plan_action"] for item in rows).items()))
    class_counts = dict(sorted(Counter(item["review_class"] for item in rows).items()))
    outstanding = [item for item in rows if item["plan_action"] != "no_action"]
    root_record_total = int((root_store.get("registry_record_count") or 0) if isinstance(root_store, dict) else 0)
    nested_record_total = int((nested_store.get("registry_record_count") or 0) if isinstance(nested_store, dict) else 0)
    retirement_blockers = [
        {
            "topic_id": item["topic_id"],
            "plan_action": item["plan_action"],
            "reason": item["retirement_blocker_reason"],
        }
        for item in outstanding
        if item["blocks_old_store_retirement"]
    ]

    return {
        "kind": "aitp_workspace_migration_plan",
        "workspace_root": inv.get("workspace_root", ""),
        "canonical_topics_root": inv.get("canonical_topics_root", str(ws.base)),
        "canonical_store": inv.get("canonical_store", str(ws.root)),
        "inventory_source": str(inventory_path or "generated_from_workspace_inventory"),
        "topic_count": len(rows),
        "topic_rows": rows,
        "summary": {
            "topic_count": len(rows),
            "action_counts": action_counts,
            "review_class_counts": class_counts,
            "old_store_retirement_safe": False,
            "old_store_retirement_blocker_count": len(retirement_blockers),
            "root_store_registry_record_count": root_record_total,
            "nested_store_registry_record_count": nested_record_total,
            "root_store_exists": bool(root_store.get("exists")),
            "nested_store_exists": bool(nested_store.get("exists")),
            "canonical_registry_record_count": int(canonical_store.get("registry_record_count") or 0),
            "no_omission_check": len(rows) == len(inv.get("topic_migration_rows", [])),
            "manual_semantic_review_required": True,
        },
        "retirement_gate": {
            "old_store_retirement_safe": False,
            "why_not_safe_now": (
                "Root-local or nested AITP stores still contain records or topic shells that need "
                "merge, semantic review, or archival accounting before removal."
            ),
            "safe_retirement_conditions": [
                "Every import_required row has an import/review packet and either typed canonical records or an archive decision.",
                "Every duplicate_store_review row has a recorded diff decision.",
                "Every legacy_semantic_review row has a semantic review result or remains explicitly blocking.",
                "All agent configs point to the canonical topics root, not workspace-root .aitp or .aitp/.aitp.",
                "Old stores are archived with a manifest before deletion; no claim trust is updated by this plan.",
            ],
            "blocked_by": retirement_blockers,
            "recommended_retirement_mode": "archive_then_disable_entrypoints_not_direct_delete",
        },
        "agent_install_contract": {
            "canonical_topics_root": inv.get("canonical_topics_root", str(ws.base)),
            "aitp_protocol_repo": str(Path(__file__).resolve().parents[2]),
            "required_install_command": (
                "uv run --with pyyaml --with jsonschema --with fastmcp python scripts/aitp-pm.py "
                "install --agent all --scope project --target-root <workspace-root> "
                "--topics-root <workspace-root>/research/aitp-topics"
            ),
            "mcp_entrypoint": "brain/v5/native_mcp.py",
            "old_entrypoints_to_retire": [
                "workspace_root/.aitp as canonical store",
                "workspace_root/.aitp/.aitp nested store",
                "legacy L0-L4 directories as active memory",
                "old aitp-v5 MCP command aliases when native_mcp.py is available",
            ],
        },
        "truth_source": "workspace_inventory",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def render_workspace_migration_plan_markdown(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    gate = payload.get("retirement_gate") if isinstance(payload.get("retirement_gate"), dict) else {}
    lines = [
        "# AITP Workspace Migration Plan",
        "",
        "This is a read-only coordination surface. It does not import records, edit topic state, or update claim trust.",
        "",
        f"- Workspace root: `{payload.get('workspace_root', '')}`",
        f"- Canonical topics root: `{payload.get('canonical_topics_root', '')}`",
        f"- Canonical store: `{payload.get('canonical_store', '')}`",
        f"- Topic rows accounted: `{summary.get('topic_count', 0)}`",
        f"- No-omission check: `{str(summary.get('no_omission_check', False)).lower()}`",
        f"- Old store retirement safe now: `{str(summary.get('old_store_retirement_safe', False)).lower()}`",
        f"- Retirement blockers: `{summary.get('old_store_retirement_blocker_count', 0)}`",
        "",
        "## Action Counts",
        "",
    ]
    for key, value in (summary.get("action_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Topic Rows",
            "",
            "| Topic | Class | Action | Canonical Records | Root Records | Nested Records | Next Action | Blocks Retirement |",
            "|---|---|---|---:|---:|---:|---|---:|",
        ]
    )
    for row in payload.get("topic_rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {topic} | {klass} | {action} | {canonical} | {root} | {nested} | {next_action} | {blocks} |".format(
                topic=row.get("topic_id", ""),
                klass=row.get("review_class", ""),
                action=row.get("plan_action", ""),
                canonical=row.get("canonical_registry_record_count", 0),
                root=row.get("root_registry_record_count", 0),
                nested=row.get("nested_registry_record_count", 0),
                next_action=_cell(row.get("next_action", "")),
                blocks=str(row.get("blocks_old_store_retirement", False)).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Retirement Gate",
            "",
            f"- Recommended mode: `{gate.get('recommended_retirement_mode', '')}`",
            f"- Current reason: {gate.get('why_not_safe_now', '')}",
            "",
            "Safe retirement conditions:",
        ]
    )
    for item in gate.get("safe_retirement_conditions") or []:
        lines.append(f"- {item}")
    lines.extend(["", "## Agent Install Contract", ""])
    contract = payload.get("agent_install_contract") if isinstance(payload.get("agent_install_contract"), dict) else {}
    lines.append(f"- MCP entrypoint: `{contract.get('mcp_entrypoint', '')}`")
    lines.append(f"- Required install command: `{contract.get('required_install_command', '')}`")
    lines.append("- Old entrypoints to retire:")
    for item in contract.get("old_entrypoints_to_retire") or []:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_workspace_migration_plan_report(payload: dict[str, Any], path: str | Path) -> Path:
    report_path = Path(path)
    write_text_atomic(report_path, render_workspace_migration_plan_markdown(payload))
    return report_path


def _load_inventory(
    ws: WorkspacePaths,
    *,
    workspace_root: str | Path | None,
    inventory_path: str | Path | None,
    inventory: dict[str, Any] | None,
) -> dict[str, Any]:
    if inventory is not None:
        return dict(inventory)
    if inventory_path:
        return json.loads(Path(inventory_path).read_text(encoding="utf-8-sig"))
    return build_workspace_inventory(ws, workspace_root=workspace_root)


def _topic_counts(store: dict[str, Any]) -> dict[str, int]:
    raw = store.get("registry_topic_record_counts") if isinstance(store, dict) else {}
    if not isinstance(raw, dict):
        return {}
    return {str(key): int(value or 0) for key, value in raw.items()}


def _plan_row(row: dict[str, Any], *, canonical_count: int, root_count: int, nested_count: int) -> dict[str, Any]:
    topic_id = str(row.get("topic_id") or "")
    required = str(row.get("required_action") or "")
    action, review_class, next_action, blocker_reason = _classify_row(
        row,
        canonical_count=canonical_count,
        root_count=root_count,
        nested_count=nested_count,
    )
    blocks = action != "no_action"
    return {
        "topic_id": topic_id,
        "inventory_required_action": required,
        "review_class": review_class,
        "plan_action": action,
        "next_action": next_action,
        "canonical_v5_present": bool(row.get("canonical_v5_present")),
        "legacy_present": bool(row.get("legacy_present")),
        "root_store_present": bool(row.get("root_store_present")),
        "nested_root_store_present": bool(row.get("nested_root_store_present")),
        "legacy_file_count": int(row.get("legacy_file_count") or 0),
        "legacy_stage_file_counts": row.get("legacy_stage_file_counts") or {},
        "legacy_state_stage": str(row.get("legacy_state_stage") or ""),
        "legacy_state_lane": str(row.get("legacy_state_lane") or ""),
        "canonical_registry_record_count": canonical_count,
        "root_registry_record_count": root_count,
        "nested_registry_record_count": nested_count,
        "blocks_old_store_retirement": blocks,
        "retirement_blocker_reason": blocker_reason if blocks else "",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _classify_row(
    row: dict[str, Any],
    *,
    canonical_count: int,
    root_count: int,
    nested_count: int,
) -> tuple[str, str, str, str]:
    topic_id = str(row.get("topic_id") or "")
    required = str(row.get("required_action") or "")
    rootish_count = root_count + nested_count
    if required == "structurally_current":
        return "no_action", "current_v5", "keep canonical topic; no old-store action", ""
    if required == "semantic_review_legacy_vs_v5":
        return (
            "semantic_review_required",
            "legacy_vs_canonical_v5",
            f"run legacy semantic-review-packet for `{topic_id}` and record review result",
            "legacy L0-L4 files and v5 records must be reviewed before legacy surfaces can be retired",
        )
    if required == "semantic_review_duplicate_store":
        return (
            "duplicate_store_review_required",
            "duplicate_root_store_topic",
            f"diff root-local records for `{topic_id}` against canonical records, then record archive/import decision",
            "root-local duplicate store has not been diffed against canonical v5",
        )
    if required == "semantic_review_empty_registry":
        return (
            "empty_canonical_topic_review_required",
            "empty_canonical_topic",
            f"seed, archive, or delete empty canonical topic `{topic_id}` through an explicit review decision",
            "canonical topic exists without registry records; intent is not established",
        )
    if required == "migrate_legacy_topic":
        return (
            "legacy_import_packet_required",
            "legacy_only_topic",
            f"run legacy migration accounting and semantic review for `{topic_id}` before creating v5 records",
            "legacy-only topic has not been imported into canonical v5",
        )
    if required == "merge_root_store_topic":
        if canonical_count > 0 and not row.get("canonical_v5_present"):
            return (
                "repair_canonical_topic_shell_and_merge_required",
                "canonical_records_without_topic_dir",
                f"repair canonical topic shell for `{topic_id}` and review root/nested records for merge",
                "canonical registry contains topic records without a canonical topic directory",
            )
        if rootish_count > 0:
            return (
                "root_store_import_review_required",
                "root_or_nested_records_not_in_canonical_topic",
                f"build an import/review packet for `{topic_id}` from root/nested store records",
                "old root/nested store has records not represented as a canonical topic",
            )
        return (
            "root_store_shell_archive_required",
            "root_or_nested_topic_shell_only",
            f"archive topic shell `{topic_id}` with manifest or promote it through a typed topic create decision",
            "old root/nested store has a topic shell whose archival/promote decision is unrecorded",
        )
    return (
        "manual_review_required",
        "unknown_inventory_action",
        f"inspect `{topic_id}` manually; inventory action `{required}` is not recognized by the planner",
        "planner cannot classify inventory row",
    )


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
