"""Orientation-only Obsidian views for source reconstruction review."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths
from brain.v5.source_reconstruction_review import build_source_reconstruction_review_manifest


def write_source_reconstruction_obsidian_view(
    ws: WorkspacePaths,
    *,
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a Markdown worklist for source reconstruction review gaps."""

    manifest = build_source_reconstruction_review_manifest(ws)
    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "source_reconstruction"
    worklist_path = view_dir / "Source Reconstruction Review Worklist.md"
    write_md(
        worklist_path,
        _frontmatter(),
        _worklist_body(manifest),
    )
    items = [item for item in manifest["items"] if isinstance(item, dict)]
    incomplete_items = [item for item in items if item.get("source_reconstruction_status") == "incomplete"]
    return {
        "ok": True,
        "kind": "source_reconstruction_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "files": {
            "review_worklist": str(worklist_path),
        },
        "claim_count": manifest["claim_count"],
        "incomplete_claim_count": len(incomplete_items),
        "review_progress": dict(manifest["review_progress"]),
        "source_records": {
            "claim_ids": [
                str(item.get("claim_id") or "")
                for item in items
                if str(item.get("claim_id") or "")
            ],
            "review_result_ids": _unique([
                str(result_id)
                for item in items
                for result_id in (item.get("review_result_ids") or [])
                if str(result_id)
            ]),
        },
        "next_actions": list(manifest["next_actions"]),
        "derived_from": "source_reconstruction_review_manifest",
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter() -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": "source_reconstruction_review_worklist",
        "derived_from": "source_reconstruction_review_manifest",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_review_triage_only_use_typed_source_reconstruction_records_for_results",
    }


def _worklist_body(manifest: dict[str, Any]) -> str:
    items = [item for item in manifest["items"] if isinstance(item, dict)]
    active_items = [
        item for item in items if item.get("review_status") in {"pending", "needs_revision", "inconclusive"}
    ]
    lines = [
        "# Source Reconstruction Review Worklist",
        "",
        "This worklist is orientation-only. Use typed source reconstruction records for review results and keep claim trust unchanged until a valid promotion path approves it.",
        "",
        f"- Claims: {manifest['claim_count']}",
        f"- Pending: {manifest['review_progress'].get('pending', 0)}",
        f"- Inconclusive: {manifest['review_progress'].get('inconclusive', 0)}",
        f"- Needs revision: {manifest['review_progress'].get('needs_revision', 0)}",
        f"- Passed: {manifest['review_progress'].get('passed', 0)}",
        "",
        "## Review Worklist",
        "",
        "| Topic | Claim | Reconstruction | Review | Missing Components | Next Actions | Review Packet |",
        "|---|---|---|---|---|---|---|",
    ]
    if not active_items:
        lines.append("| None |  |  |  |  |  |  |")
    for item in active_items:
        lines.append(
            f"| `{_cell(item.get('topic_id'))}` | `{_cell(item.get('claim_id'))}` | "
            f"`{_cell(item.get('source_reconstruction_status'))}` | `{_cell(item.get('review_status'))}` | "
            f"`{_cell(', '.join(item.get('missing_components') or []))}` | "
            f"`{_cell(', '.join(item.get('next_actions') or []))}` | "
            f"`{_cell(item.get('review_packet_cli'))}` |"
        )
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use typed source reconstruction records for review results. This generated note is not evidence for source completeness and cannot update claim trust.",
    ])
    return "\n".join(lines) + "\n"


def _cell(value: Any) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
