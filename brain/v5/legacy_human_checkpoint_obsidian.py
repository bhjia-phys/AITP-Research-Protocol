"""Orientation-only Obsidian views for legacy semantic-review checkpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_human_checkpoint_packet import build_legacy_human_checkpoint_packet
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths


def write_legacy_human_checkpoint_obsidian_view(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    topic: str = "",
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a human-readable checkpoint worklist without deciding checkpoints."""

    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "legacy_human_checkpoints"
    packet = build_legacy_human_checkpoint_packet(ws, migration_dir=migration_dir, topic=topic)
    worklist_path = view_dir / "Legacy Human Checkpoints.md"
    write_md(
        worklist_path,
        _frontmatter(packet),
        _worklist_body(packet),
    )
    checkpoint_items = [item for item in packet["checkpoint_items"] if isinstance(item, dict)]
    return {
        "ok": True,
        "kind": "legacy_human_checkpoint_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "migration_dir": packet["migration_dir"],
        "workspace": packet["workspace"],
        "topic_filter": packet["topic_filter"],
        "files": {
            "checkpoint_worklist": str(worklist_path),
        },
        "checkpoint_item_count": packet["checkpoint_item_count"],
        "open_decision_count": packet["open_decision_count"],
        "pending_request_count": packet["pending_request_count"],
        "source_records": {
            "checkpoint_ids": [
                str(item.get("checkpoint_id") or "")
                for item in checkpoint_items
                if str(item.get("checkpoint_id") or "")
            ],
            "latest_review_ids": [
                str(item.get("latest_review_id") or "")
                for item in checkpoint_items
                if str(item.get("latest_review_id") or "")
            ],
        },
        "next_actions": list(packet["next_actions"]),
        "semantic_lossless_proven": False,
        "derived_from": "legacy_human_checkpoint_packet",
        "truth_source": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": "legacy_human_checkpoint_worklist",
        "source_id": packet["migration_dir"],
        "derived_from": "legacy_human_checkpoint_packet",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_decision_triage_only_use_typed_checkpoint_records_for_decisions",
    }


def _worklist_body(packet: dict[str, Any]) -> str:
    items = [item for item in packet["checkpoint_items"] if isinstance(item, dict)]
    lines = [
        "# Legacy Human Checkpoints",
        "",
        "This worklist is orientation-only. Use typed checkpoint records for decisions and keep claim trust unchanged until a valid decision path approves promotion.",
        "",
        f"- Migration: `{packet['migration_dir']}`",
        f"- Open decisions: {packet['open_decision_count']}",
        f"- Pending requests: {packet['pending_request_count']}",
        f"- Total checkpoint items: {packet['checkpoint_item_count']}",
        "",
        "## Decision Worklist",
        "",
        "| Topic | Mode | Action | Reason | Options | Checkpoint | Latest Review |",
        "|---|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| None |  |  |  |  |  |  |")
    for item in items:
        lines.append(
            f"| `{_cell(item.get('topic'))}` | `{_cell(item.get('mode'))}` | "
            f"`{_cell(item.get('action'))}` | {_cell(item.get('reason'))} | "
            f"`{_cell(', '.join(item.get('options') or []))}` | "
            f"`{_cell(item.get('checkpoint_id'))}` | `{_cell(item.get('latest_review_id'))}` |"
        )
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use typed checkpoint records for decisions. This generated note is not evidence for semantic losslessness and cannot update claim trust.",
    ])
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    text = " ".join(str(value or "").split())
    return text.replace("|", "\\|")
