"""Orientation-only Obsidian worklists for legacy source reconstruction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_manifest
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths


def write_legacy_source_reconstruction_obsidian_view(
    ws: WorkspacePaths,
    *,
    migration_dir: str | Path,
    output_dir: str = "",
) -> dict[str, Any]:
    """Write a legacy-aware source reconstruction worklist without mutating trust."""

    manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=migration_dir)
    view_dir = Path(output_dir) if output_dir else ws.root / "surfaces" / "legacy_source_reconstruction"
    worklist_path = view_dir / "Legacy Source Reconstruction Worklist.md"
    write_md(
        worklist_path,
        _frontmatter(manifest),
        _worklist_body(manifest),
    )
    items = [item for item in manifest["items"] if isinstance(item, dict)]
    return {
        "ok": True,
        "kind": "legacy_source_reconstruction_obsidian_view_bundle",
        "view_dir": str(view_dir),
        "migration_dir": manifest["migration_dir"],
        "files": {
            "review_worklist": str(worklist_path),
        },
        "work_item_count": manifest["work_item_count"],
        "repair_status_counts": dict(manifest["repair_status_counts"]),
        "proposed_repair_count": manifest["proposed_repair_count"],
        "missing_component_counts": dict(manifest["missing_component_counts"]),
        "required_action_counts": dict(manifest["required_action_counts"]),
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
        "next_actions": list(manifest["next_actions"]),
        "semantic_lossless_proven": False,
        "semantic_review_required": True,
        "derived_from": "legacy_source_reconstruction_manifest",
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _frontmatter(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "derived_obsidian_view",
        "view_role": "legacy_source_reconstruction_worklist",
        "source_id": manifest["migration_dir"],
        "derived_from": "legacy_source_reconstruction_manifest",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_review_triage_only_use_typed_source_reconstruction_records_for_results",
    }


def _worklist_body(manifest: dict[str, Any]) -> str:
    items = [item for item in manifest["items"] if isinstance(item, dict)]
    lines = [
        "# Legacy Source Reconstruction Worklist",
        "",
        "This worklist is orientation-only. Use typed source reconstruction review records for review results and keep claim trust unchanged until all reconstruction, semantic, evidence, and checkpoint gates pass.",
        "",
        f"- Migration: `{manifest['migration_dir']}`",
        f"- Work items: {manifest['work_item_count']}",
        f"- Proposed repairs: {manifest['proposed_repair_count']}",
        f"- Semantic lossless proven: {str(manifest['semantic_lossless_proven']).lower()}",
        "",
        "## Counts",
        "",
        f"- Repair status: `{_counts(manifest['repair_status_counts'])}`",
        f"- Missing components: `{_counts(manifest['missing_component_counts'])}`",
        f"- Required actions: `{_counts(manifest['required_action_counts'])}`",
        "",
        "## Worklist",
        "",
        "| Topic | Claim | Repair Status | Missing Components | Required Actions | Proposed Repairs | Review Packet | Apply |",
        "|---|---|---|---|---|---|---|---|",
    ]
    if not items:
        lines.append("| None |  |  |  |  |  |  |  |")
    for item in items:
        lines.append(
            f"| `{_cell(item.get('topic'))}` | `{_cell(item.get('active_claim_id'))}` | "
            f"`{_cell(item.get('repair_status'))}` | `{_cell(', '.join(item.get('missing_components') or []))}` | "
            f"`{_cell(', '.join(item.get('required_actions') or []))}` | "
            f"`{_cell(', '.join(item.get('proposed_repair_types') or []))}` | "
            f"`{_cell(item.get('review_packet_cli'))}` | `{_cell(item.get('apply_cli'))}` |"
        )
    lines.extend([
        "",
        "## Trust Boundary",
        "",
        "Use typed source reconstruction review records and guarded repair application records for durable results. This generated note is not evidence for reconstruction completeness and cannot update claim trust.",
    ])
    return "\n".join(lines) + "\n"


def _counts(counts: dict[str, Any]) -> str:
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _cell(value: Any) -> str:
    return " ".join(str(value or "").split()).replace("|", "\\|")
