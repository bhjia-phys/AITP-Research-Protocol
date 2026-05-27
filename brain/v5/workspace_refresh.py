"""Workspace refresh bundle for host startup orientation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.legacy_human_checkpoint_obsidian import write_legacy_human_checkpoint_obsidian_view
from brain.v5.legacy_semantic_review_obsidian import write_legacy_semantic_review_obsidian_view
from brain.v5.obsidian_views import write_l2_obsidian_view
from brain.v5.paths import WorkspacePaths
from brain.v5.replay import write_workspace_replay_packet
from brain.v5.source_reconstruction_obsidian import write_source_reconstruction_obsidian_view
from brain.v5.summaries import write_workspace_summary
from brain.v5.workspace_interaction_preview import build_workspace_interaction_preview


def refresh_workspace_views(
    ws: WorkspacePaths,
    *,
    migration_dir: str | None = None,
) -> dict[str, Any]:
    """Refresh all orientation-only workspace review views.

    Host adapters can call this once at startup to get a current orientation
    packet without granting summaries or Markdown files trust authority.
    """

    summary = asdict(write_workspace_summary(ws))
    replay = asdict(write_workspace_replay_packet(ws, migration_dir=migration_dir))
    active_claims = summary.get("source_records", {}).get("claims", [])
    obsidian = write_l2_obsidian_view(
        ws,
        output_dir=str(ws.root / "surfaces" / "obsidian_l2_active"),
        claim_ids=active_claims,
    )
    source_reconstruction = write_source_reconstruction_obsidian_view(
        ws,
        output_dir=str(ws.root / "surfaces" / "source_reconstruction_active"),
    )
    workspace_interaction = build_workspace_interaction_preview(ws)
    legacy_checkpoint_view = (
        write_legacy_human_checkpoint_obsidian_view(ws, migration_dir=migration_dir)
        if migration_dir
        else None
    )
    legacy_semantic_view = (
        write_legacy_semantic_review_obsidian_view(ws, migration_dir=migration_dir)
        if migration_dir
        else None
    )
    source_records = _merge_source_records(
        summary.get("source_records", {}),
        replay.get("source_records", {}),
        obsidian.get("source_records", {}),
        source_reconstruction.get("source_records", {}),
        workspace_interaction.get("source_records", {}),
        legacy_semantic_view.get("source_records", {}) if legacy_semantic_view else {},
        legacy_checkpoint_view.get("source_records", {}) if legacy_checkpoint_view else {},
    )
    refreshed_surfaces = [
        summary["kind"],
        replay["kind"],
        obsidian["kind"],
        source_reconstruction["kind"],
        workspace_interaction["kind"],
    ]
    if legacy_semantic_view:
        refreshed_surfaces.append(legacy_semantic_view["kind"])
    if legacy_checkpoint_view:
        refreshed_surfaces.append(legacy_checkpoint_view["kind"])
    payload = {
        "kind": "workspace_refresh_bundle",
        "refreshed_surfaces": refreshed_surfaces,
        "workspace_summary": summary,
        "workspace_replay": replay,
        "l2_obsidian_view": obsidian,
        "source_reconstruction_obsidian_view": source_reconstruction,
        "workspace_interaction_preview": workspace_interaction,
        "source_records": source_records,
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if legacy_semantic_view:
        payload["legacy_semantic_review_obsidian_view"] = legacy_semantic_view
    if legacy_checkpoint_view:
        payload["legacy_human_checkpoint_obsidian_view"] = legacy_checkpoint_view
    return payload


def _merge_source_records(*records: dict[str, list[str]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    seen: dict[str, set[str]] = {}
    for record in records:
        for key, values in record.items():
            merged.setdefault(key, [])
            seen.setdefault(key, set())
            for value in values:
                if value and value not in seen[key]:
                    seen[key].add(value)
                    merged[key].append(value)
    return merged
