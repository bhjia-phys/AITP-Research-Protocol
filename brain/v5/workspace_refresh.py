"""Workspace refresh bundle for host startup orientation."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.legacy_human_checkpoint_obsidian import write_legacy_human_checkpoint_obsidian_view
from brain.v5.legacy_semantic_needs_revision_obsidian import write_legacy_semantic_needs_revision_basis_obsidian_view
from brain.v5.legacy_semantic_review_obsidian import write_legacy_semantic_review_obsidian_view
from brain.v5.legacy_source_reconstruction_obsidian import write_legacy_source_reconstruction_obsidian_view
from brain.v5.obsidian_views import write_l2_obsidian_view
from brain.v5.paths import WorkspacePaths
from brain.v5.replay import write_workspace_replay_packet
from brain.v5.source_stack_coverage import build_source_stack_coverage_manifest
from brain.v5.source_reconstruction_obsidian import write_source_reconstruction_obsidian_view
from brain.v5.summaries import write_workspace_summary
from brain.v5.interaction_worklist import build_interaction_recording_worklist
from brain.v5.topic_status import write_topic_status_surfaces
from brain.v5.workspace_interaction_preview import build_workspace_interaction_preview


_TOPIC_STATUS_REFRESH_SESSION_LIMIT = 5


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
    source_stack_coverage = build_source_stack_coverage_manifest(ws)
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
    interaction_worklist = build_interaction_recording_worklist(ws)
    topic_status_candidates = _topic_status_candidate_session_ids(summary, replay)
    topic_status_session_ids = _select_topic_status_session_ids(
        ws,
        topic_status_candidates,
        replay,
        limit=_TOPIC_STATUS_REFRESH_SESSION_LIMIT,
    )
    topic_status_bundles = [
        write_topic_status_surfaces(ws, session_id=session_id)
        for session_id in topic_status_session_ids
    ]
    topic_status_refresh_policy = {
        "selection": "recent_attention_sessions",
        "max_session_count": _TOPIC_STATUS_REFRESH_SESSION_LIMIT,
        "candidate_session_count": len(topic_status_candidates),
        "refreshed_session_count": len(topic_status_bundles),
    }
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
    legacy_needs_revision_view = (
        write_legacy_semantic_needs_revision_basis_obsidian_view(ws, migration_dir=migration_dir)
        if migration_dir
        else None
    )
    legacy_source_reconstruction_view = (
        write_legacy_source_reconstruction_obsidian_view(ws, migration_dir=migration_dir)
        if migration_dir
        else None
    )
    source_records = _merge_source_records(
        summary.get("source_records", {}),
        replay.get("source_records", {}),
        _source_records_from_coverage(source_stack_coverage),
        obsidian.get("source_records", {}),
        source_reconstruction.get("source_records", {}),
        workspace_interaction.get("source_records", {}),
        interaction_worklist.get("source_records", {}),
        *(bundle.get("source_records", {}) for bundle in topic_status_bundles),
        legacy_source_reconstruction_view.get("source_records", {}) if legacy_source_reconstruction_view else {},
        legacy_semantic_view.get("source_records", {}) if legacy_semantic_view else {},
        legacy_needs_revision_view.get("source_records", {}) if legacy_needs_revision_view else {},
        legacy_checkpoint_view.get("source_records", {}) if legacy_checkpoint_view else {},
    )
    refreshed_surfaces = [
        summary["kind"],
        replay["kind"],
        source_stack_coverage["kind"],
        obsidian["kind"],
        source_reconstruction["kind"],
        workspace_interaction["kind"],
        interaction_worklist["kind"],
    ]
    if topic_status_bundles:
        refreshed_surfaces.append("topic_status_bundle")
    if legacy_source_reconstruction_view:
        refreshed_surfaces.append(legacy_source_reconstruction_view["kind"])
    if legacy_semantic_view:
        refreshed_surfaces.append(legacy_semantic_view["kind"])
    if legacy_needs_revision_view:
        refreshed_surfaces.append(legacy_needs_revision_view["kind"])
    if legacy_checkpoint_view:
        refreshed_surfaces.append(legacy_checkpoint_view["kind"])
    payload = {
        "kind": "workspace_refresh_bundle",
        "refreshed_surfaces": refreshed_surfaces,
        "workspace_summary": summary,
        "workspace_replay": replay,
        "source_stack_coverage": source_stack_coverage,
        "l2_obsidian_view": obsidian,
        "source_reconstruction_obsidian_view": source_reconstruction,
        "workspace_interaction_preview": workspace_interaction,
        "interaction_recording_worklist": interaction_worklist,
        "topic_status_bundles": topic_status_bundles,
        "topic_status_refresh_policy": topic_status_refresh_policy,
        "source_records": source_records,
        "derived_from": "kernel_state",
        "truth_source": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    if legacy_source_reconstruction_view:
        payload["legacy_source_reconstruction_obsidian_view"] = legacy_source_reconstruction_view
    if legacy_semantic_view:
        payload["legacy_semantic_review_obsidian_view"] = legacy_semantic_view
    if legacy_needs_revision_view:
        payload["legacy_semantic_needs_revision_basis_obsidian_view"] = legacy_needs_revision_view
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


def _source_records_from_coverage(payload: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "claims": [
            str(item.get("claim_id") or "")
            for item in payload.get("items", [])
            if isinstance(item, dict) and str(item.get("claim_id") or "")
        ],
        "topics": [
            str(item.get("topic_id") or "")
            for item in payload.get("items", [])
            if isinstance(item, dict) and str(item.get("topic_id") or "")
        ],
    }


def _topic_status_candidate_session_ids(summary: dict[str, Any], replay: dict[str, Any]) -> list[str]:
    return _unique_strings([
        *[
            str(session_id or "")
            for session_id in summary.get("source_records", {}).get("sessions", [])
        ],
        *[
            str(session_id or "")
            for session_id in replay.get("source_records", {}).get("sessions", [])
        ],
    ])


def _select_topic_status_session_ids(
    ws: WorkspacePaths,
    session_ids: list[str],
    replay: dict[str, Any],
    *,
    limit: int,
) -> list[str]:
    entries = {
        str(entry.get("session_id") or ""): entry
        for entry in replay.get("entries", [])
        if isinstance(entry, dict) and str(entry.get("session_id") or "")
    }
    return sorted(
        session_ids,
        key=lambda session_id: (
            bool(entries.get(session_id, {}).get("attention_reasons")),
            _session_mtime(ws, session_id),
            session_id,
        ),
        reverse=True,
    )[:limit]


def _session_mtime(ws: WorkspacePaths, session_id: str) -> float:
    try:
        return ws.session_path(session_id).stat().st_mtime
    except OSError:
        return 0.0


def _unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
