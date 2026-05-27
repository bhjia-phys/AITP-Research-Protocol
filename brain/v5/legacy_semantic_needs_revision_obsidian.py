"""Orientation-only Obsidian views for legacy needs-revision basis worklists."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_needs_revision import build_legacy_semantic_needs_revision_basis_queue
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths


def write_legacy_semantic_needs_revision_basis_obsidian_view(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a human-readable queue for turning inconclusive reviews into typed basis."""

    queue = build_legacy_semantic_needs_revision_basis_queue(ws, migration_dir=migration_dir)
    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "legacy_semantic_needs_revision_basis"
    worklist_path = view_dir / "Legacy Needs-Revision Basis Worklist.md"
    write_md(
        worklist_path,
        _frontmatter(queue),
        _worklist_body(queue),
    )
    items = [item for item in queue["items"] if isinstance(item, dict)]
    return {
        "ok": True,
        "kind": "legacy_semantic_needs_revision_basis_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "migration_dir": queue["migration_dir"],
        "workspace": queue["workspace"],
        "files": {
            "basis_worklist": str(worklist_path),
        },
        "basis_item_count": queue["basis_item_count"],
        "status_counts": dict(queue["status_counts"]),
        "required_action_counts": dict(queue["required_action_counts"]),
        "source_records": {
            "topics": [
                str(item.get("topic") or "")
                for item in items
                if str(item.get("topic") or "")
            ],
            "active_claim_ids": [
                str(item.get("active_claim_id") or "")
                for item in items
                if str(item.get("active_claim_id") or "")
            ],
            "latest_review_ids": [
                str(item.get("latest_review_id") or "")
                for item in items
                if str(item.get("latest_review_id") or "")
            ],
        },
        "next_actions": list(queue["next_actions"]),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "derived_from": "legacy_semantic_needs_revision_basis_queue",
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(queue: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": "legacy_semantic_needs_revision_basis_worklist",
        "source_id": queue["migration_dir"],
        "derived_from": "legacy_semantic_needs_revision_basis_queue",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_review_triage_only_use_typed_legacy_semantic_review_records_for_results",
    }


def _worklist_body(queue: dict[str, Any]) -> str:
    items = [item for item in queue["items"] if isinstance(item, dict)]
    lines = [
        "# Legacy Needs-Revision Basis Worklist",
        "",
        "This worklist is orientation-only. Use typed legacy semantic review records for needs-revision results and keep claim trust unchanged until all semantic, source, evidence, and checkpoint gates pass.",
        "",
        f"- Migration: `{queue['migration_dir']}`",
        f"- Basis items: {queue['basis_item_count']}",
        f"- Semantic lossless proven: {str(queue['semantic_lossless_proven']).lower()}",
        "",
        "## Counts",
        "",
        f"- Status: `{_counts(queue['status_counts'])}`",
        f"- Required actions: `{_counts(queue['required_action_counts'])}`",
        "",
        "## Basis Worklist",
        "",
        "| Topic | Claim | Latest Review | Required Actions | Basis Packet | Needs-Revision Result | Repair Plan |",
        "|---|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| None |  |  |  |  |  |  |")
    for item in items:
        lines.append(
            f"| `{_cell(item.get('topic'))}` | `{_cell(item.get('active_claim_id'))}` | "
            f"`{_cell(item.get('latest_review_id'))}` | "
            f"`{_cell(', '.join(item.get('required_actions') or []))}` | "
            f"`{_cell(item.get('basis_packet_cli'))}` | "
            f"`{_cell(item.get('needs_revision_result_cli'))}` | "
            f"`{_cell(item.get('repair_plan_cli'))}` |"
        )
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use typed legacy semantic review records for needs-revision results. This generated note is not evidence for semantic losslessness and cannot update claim trust.",
    ])
    return "\n".join(lines) + "\n"


def _counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _cell(value: Any) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")
