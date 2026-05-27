"""Orientation-only Obsidian views for legacy semantic review worklists."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_semantic_review_worklist import build_legacy_semantic_review_worklist
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths


def write_legacy_semantic_review_obsidian_view(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a human-readable semantic review backlog without changing trust."""

    worklist = build_legacy_semantic_review_worklist(ws, migration_dir=migration_dir)
    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "legacy_semantic_review"
    worklist_path = view_dir / "Legacy Semantic Review Worklist.md"
    write_md(
        worklist_path,
        _frontmatter(worklist),
        _worklist_body(worklist),
    )
    items = [item for item in worklist["items"] if isinstance(item, dict)]
    return {
        "ok": True,
        "kind": "legacy_semantic_review_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "migration_dir": worklist["migration_dir"],
        "workspace": worklist["workspace"],
        "files": {
            "review_worklist": str(worklist_path),
        },
        "work_item_count": worklist["work_item_count"],
        "status_counts": dict(worklist["status_counts"]),
        "pass_readiness_counts": dict(worklist["pass_readiness_counts"]),
        "pass_blocker_counts": dict(worklist["pass_blocker_counts"]),
        "blocking_class_counts": dict(worklist["blocking_class_counts"]),
        "open_human_checkpoint_count": worklist["open_human_checkpoint_count"],
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
        "next_actions": list(worklist["next_actions"]),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "derived_from": "legacy_semantic_review_worklist",
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(worklist: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": "legacy_semantic_review_worklist",
        "source_id": worklist["migration_dir"],
        "derived_from": "legacy_semantic_review_worklist",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_review_triage_only_use_typed_legacy_semantic_review_records_for_results",
    }


def _worklist_body(worklist: dict[str, Any]) -> str:
    items = [item for item in worklist["items"] if isinstance(item, dict)]
    lines = [
        "# Legacy Semantic Review Worklist",
        "",
        "This worklist is orientation-only. Use typed legacy semantic review records for review results and keep claim trust unchanged until all semantic, source, evidence, and checkpoint gates pass.",
        "",
        f"- Migration: `{worklist['migration_dir']}`",
        f"- Work items: {worklist['work_item_count']}",
        f"- Open human checkpoints: {worklist['open_human_checkpoint_count']}",
        f"- Semantic lossless proven: {str(worklist['semantic_lossless_proven']).lower()}",
        "",
        "## Counts",
        "",
        f"- Status: `{_counts(worklist['status_counts'])}`",
        f"- Pass readiness: `{_counts(worklist['pass_readiness_counts'])}`",
        f"- Blocking classes: `{_counts(worklist['blocking_class_counts'])}`",
        "",
        "## Review Worklist",
        "",
        "| Topic | Claim | Status | Blocking Classes | Blockers | Review Focus | Result Command |",
        "|---|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| None |  |  |  |  |  |  |")
    for item in items:
        pass_readiness = item.get("pass_readiness") if isinstance(item.get("pass_readiness"), dict) else {}
        lines.append(
            f"| `{_cell(item.get('topic'))}` | `{_cell(item.get('active_claim_id'))}` | "
            f"`{_cell(item.get('review_status'))}` | `{_cell(', '.join(item.get('blocking_classes') or []))}` | "
            f"`{_cell(', '.join(pass_readiness.get('blockers') or []))}` | "
            f"`{_cell(', '.join(item.get('review_focus') or []))}` | "
            f"`{_cell(item.get('result_cli_template'))}` |"
        )
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use typed legacy semantic review records for review results. This generated note is not evidence for semantic losslessness and cannot update claim trust.",
    ])
    return "\n".join(lines) + "\n"


def _counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _cell(value: Any) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")
