"""Backlog summaries rendered into workspace replay packets."""

from __future__ import annotations

from typing import Any

from brain.v5.legacy_semantic_repair_manifest import build_legacy_semantic_repair_manifest
from brain.v5.legacy_source_reconstruction import build_legacy_source_reconstruction_manifest
from brain.v5.paths import WorkspacePaths
from brain.v5.replay_legacy_backlog_summary import (
    LegacyBacklogContext,
    legacy_executable_evidence_summary,
    legacy_human_checkpoint_summary,
    legacy_needs_revision_basis_summary,
    legacy_semantic_review_summary,
)
from brain.v5.source_stack_coverage import build_source_stack_coverage_manifest

def build_workspace_backlog_summary(
    ws: WorkspacePaths,
    entries: list[dict[str, Any]],
    *,
    migration_dir: str | None = None,
) -> dict[str, Any]:
    complete_entries = [entry for entry in entries if entry["claim_id"] and entry["source_reconstruction_complete"]]
    incomplete_entries = [
        entry for entry in entries if entry["claim_id"] and not entry["source_reconstruction_complete"]
    ]
    attention_entries = _prioritized_attention_entries([entry for entry in entries if entry["attention_reasons"]])
    summary = {
        "active_session_count": len(entries),
        "active_topic_count": len(_unique([entry["topic_id"] for entry in entries if entry["topic_id"]])),
        "active_claim_count": len(_unique([entry["claim_id"] for entry in entries if entry["claim_id"]])),
        "attention_count": len(attention_entries),
        "source_reconstruction": {
            "surface": "source_reconstruction_manifest",
            "complete_claim_count": len(complete_entries),
            "incomplete_claim_count": len(incomplete_entries),
            "review_status_counts": _review_status_counts(entries),
            "missing_component_counts": _missing_component_counts(incomplete_entries),
            "top_incomplete_claims": [_source_backlog_item(entry) for entry in incomplete_entries[:5]],
        },
        "resume_attention": {
            "attention_count": len(attention_entries),
            "top_items": [_attention_item(entry) for entry in attention_entries[:5]],
        },
        "truth_source": "kernel_state",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    _maybe_add(summary, "source_stack_coverage", _source_stack_coverage_summary(ws))
    legacy_context = LegacyBacklogContext(ws, migration_dir)
    _maybe_add(summary, "legacy_semantic_review", legacy_semantic_review_summary(legacy_context))
    _maybe_add(summary, "legacy_source_reconstruction", _legacy_source_reconstruction_summary(ws, migration_dir))
    _maybe_add(summary, "legacy_semantic_repair", _legacy_semantic_repair_summary(ws, migration_dir))
    _maybe_add(summary, "legacy_semantic_needs_revision_basis", legacy_needs_revision_basis_summary(legacy_context))
    _maybe_add(summary, "legacy_executable_evidence", legacy_executable_evidence_summary(legacy_context))
    _maybe_add(summary, "legacy_human_checkpoints", legacy_human_checkpoint_summary(legacy_context))
    return summary

def workspace_replay_body(entries: list[dict[str, Any]], workspace_backlog_summary: dict[str, Any]) -> str:
    lines = [
        "# Workspace Replay Packet",
        "",
        "This file is regenerated from typed AITP kernel records. Use it for orientation only.",
        "",
        "## Cross-Topic Backlog",
        "",
        f"- Active sessions: {workspace_backlog_summary['active_session_count']}",
        f"- Active topics: {workspace_backlog_summary['active_topic_count']}",
        f"- Active claims: {workspace_backlog_summary['active_claim_count']}",
        f"- Attention items: {workspace_backlog_summary['attention_count']}",
        f"- Source reconstruction incomplete: {workspace_backlog_summary['source_reconstruction']['incomplete_claim_count']}",
        f"- Source review pending: {workspace_backlog_summary['source_reconstruction']['review_status_counts'].get('pending', 0)}",
        "",
    ]
    for item in workspace_backlog_summary["source_reconstruction"]["top_incomplete_claims"]:
        lines.append(
            f"- `{item['claim_id']}` in `{item['topic_id']}`: missing "
            f"{', '.join(item['missing_components']) or 'none'}; review via `{item['review_packet_cli']}`"
        )
    if workspace_backlog_summary["source_reconstruction"]["top_incomplete_claims"]:
        lines.append("")
    _extend_source_stack(lines, workspace_backlog_summary)
    _extend_legacy_semantic_review(lines, workspace_backlog_summary)
    _extend_legacy_source_reconstruction(lines, workspace_backlog_summary)
    _extend_legacy_semantic_repair(lines, workspace_backlog_summary)
    _extend_legacy_needs_revision_basis(lines, workspace_backlog_summary)
    _extend_legacy_executable_evidence(lines, workspace_backlog_summary)
    _extend_legacy_human_checkpoints(lines, workspace_backlog_summary)
    if not entries:
        lines.append("- No active session bindings are recorded.")
        return "\n".join(lines) + "\n"
    for entry in entries:
        lines.append(f"## `{entry['session_id']}`")
        lines.append("")
        lines.append(f"- Topic: `{entry['topic_id']}`")
        lines.append(f"- Claim: `{entry['claim_id']}`")
        lines.append(f"- Confidence: `{entry['confidence_state']}`")
        lines.append(f"- Risk: `{entry['risk_level']}`")
        lines.append(f"- Missing evidence outputs: {', '.join(entry['missing_outputs']) or 'none'}")
        lines.append(f"- Missing source components: {', '.join(entry['missing_source_components']) or 'none'}")
        lines.append(f"- Source review: `{entry['source_reconstruction_review_status']}`")
        lines.append(f"- Attention: {', '.join(entry['attention_reasons']) or 'none'}")
        lines.append(f"- Next actions: {', '.join(entry['next_actions']) or 'none'}")
        lines.append("")
    return "\n".join(lines)

def _maybe_add(summary: dict[str, Any], key: str, value: dict[str, Any] | None) -> None:
    if value is not None:
        summary[key] = value

def _extend_source_stack(lines: list[str], summary: dict[str, Any]) -> None:
    source_stack = summary.get("source_stack_coverage")
    if not isinstance(source_stack, dict):
        return
    lines.extend([
        "## Source Stack Coverage",
        "",
        f"- Claims: {source_stack['claim_count']}",
        f"- Coverage status: `{source_stack['coverage_status_counts']}`",
        f"- Missing required outputs: `{source_stack['missing_required_output_counts']}`",
        "",
    ])
    for item in source_stack["top_gap_items"]:
        lines.append(
            f"- `{item['claim_id']}` in `{item['topic_id']}`: {item['coverage_status']}; missing outputs "
            f"{', '.join(item['missing_required_outputs']) or 'none'}"
        )
    lines.append("")

def _extend_legacy_semantic_review(lines: list[str], summary: dict[str, Any]) -> None:
    legacy = summary.get("legacy_semantic_review")
    if not isinstance(legacy, dict):
        return
    lines.extend([
        "## Legacy Semantic Review Backlog",
        "",
        f"- Migration dir: `{legacy['migration_dir']}`",
        f"- Review items: {legacy['review_item_count']}",
        f"- Review progress: `{legacy['review_progress']}`",
        f"- Open human checkpoints: {legacy.get('open_human_checkpoint_count', 0)}",
        f"- semantic lossless proven: {legacy['semantic_lossless_proven']}",
        "",
    ])
    for checkpoint in legacy.get("open_human_checkpoints", []):
        lines.append(
            f"- Open checkpoint `{checkpoint['checkpoint_id']}` for `{checkpoint['topic']}`: "
            f"{checkpoint['action']}; decide via `{checkpoint['decision_cli']}`"
        )
    if legacy.get("open_human_checkpoints"):
        lines.append("")
    for item in legacy["top_backlog_items"]:
        lines.append(
            f"- `{item['topic']}`: {item['review_status']} priority {item['review_priority']}; "
            f"review via `{item['packet_cli']}`"
        )
    lines.append("")

def _extend_legacy_source_reconstruction(lines: list[str], summary: dict[str, Any]) -> None:
    legacy_source = summary.get("legacy_source_reconstruction")
    if not isinstance(legacy_source, dict):
        return
    lines.extend([
        "## Legacy Source Reconstruction Backlog",
        "",
        f"- Migration dir: `{legacy_source['migration_dir']}`",
        f"- Source reconstruction items: {legacy_source['work_item_count']}",
        f"- Repair status: `{legacy_source['repair_status_counts']}`",
        f"- Proposed repairs: {legacy_source['proposed_repair_count']}",
        "",
    ])
    for item in legacy_source["top_backlog_items"]:
        lines.append(
            f"- `{item['topic']}`: {item['repair_status']}; missing "
            f"{', '.join(item['missing_components']) or 'none'}; review via `{item['review_packet_cli']}`"
        )
    lines.append("")

def _extend_legacy_semantic_repair(lines: list[str], summary: dict[str, Any]) -> None:
    legacy_repair = summary.get("legacy_semantic_repair")
    if not isinstance(legacy_repair, dict):
        return
    lines.extend([
        "## Legacy Semantic Repair Triage",
        "",
        f"- Migration dir: `{legacy_repair['migration_dir']}`",
        f"- Semantic repair items: {legacy_repair['work_item_count']}",
        f"- Repair status: `{legacy_repair['repair_status_counts']}`",
        f"- Proposed semantic repairs: {legacy_repair['proposed_repair_count']}",
        "",
    ])
    for item in legacy_repair["top_repair_items"]:
        lines.append(
            f"- `{item['topic']}`: {item['repair_status']}; required "
            f"{', '.join(item['required_actions']) or 'none'}; plan via `{item['repair_plan_cli']}`"
        )
    lines.append("")


def _extend_legacy_needs_revision_basis(lines: list[str], summary: dict[str, Any]) -> None:
    legacy_basis = summary.get("legacy_semantic_needs_revision_basis")
    if not isinstance(legacy_basis, dict):
        return
    lines.extend([
        "## Legacy Needs-Revision Basis",
        "",
        f"- Migration dir: `{legacy_basis['migration_dir']}`",
        f"- Needs-revision basis items: {legacy_basis['basis_item_count']}",
        f"- Required actions: `{legacy_basis['required_action_counts']}`",
        "",
    ])
    for item in legacy_basis["top_basis_items"]:
        lines.append(
            f"- `{item['topic']}`: required {', '.join(item['required_actions']) or 'none'}; "
            f"record via `{item['needs_revision_result_cli']}`"
        )
    lines.append("")


def _extend_legacy_executable_evidence(lines: list[str], summary: dict[str, Any]) -> None:
    legacy_executable = summary.get("legacy_executable_evidence")
    if not isinstance(legacy_executable, dict):
        return
    lines.extend([
        "## Legacy Executable Evidence",
        "",
        f"- Migration dir: `{legacy_executable['migration_dir']}`",
        f"- Executable evidence items: {legacy_executable['evidence_item_count']}",
        f"- Executable actions: {legacy_executable['executable_action_count']}",
        "",
    ])
    for item in legacy_executable["top_evidence_items"]:
        lines.append(
            f"- `{item['topic']}`: {', '.join(item['executable_actions']) or 'none'}; "
            f"follow up via `{item['followup_result_cli']}`"
        )
    lines.append("")

def _extend_legacy_human_checkpoints(lines: list[str], summary: dict[str, Any]) -> None:
    legacy_checkpoints = summary.get("legacy_human_checkpoints")
    if not isinstance(legacy_checkpoints, dict):
        return
    lines.extend([
        "## Legacy Human Checkpoints",
        "",
        f"- Migration dir: `{legacy_checkpoints['migration_dir']}`",
        (
            "- Checkpoint decisions: "
            f"{legacy_checkpoints['open_decision_count']} open, "
            f"{legacy_checkpoints['pending_request_count']} pending request"
        ),
        f"- Next actions: {legacy_checkpoints['next_action_count']}",
        "",
    ])
    for item in legacy_checkpoints["top_checkpoint_items"]:
        lines.append(f"- `{item['topic']}`: {item['action']} via `{item['cli']}`")
    lines.append("")

def _source_stack_coverage_summary(ws: WorkspacePaths) -> dict[str, Any]:
    manifest = build_source_stack_coverage_manifest(ws)
    gap_items = [item for item in manifest["items"] if item.get("coverage_status") != "complete"]
    return {
        "surface": "source_stack_coverage_manifest",
        "claim_count": int(manifest["claim_count"]),
        "coverage_status_counts": dict(manifest["coverage_status_counts"]),
        "missing_required_output_counts": dict(manifest["missing_required_output_counts"]),
        "source_component_gap_counts": dict(manifest["source_component_gap_counts"]),
        "source_review_status_counts": dict(manifest["source_review_status_counts"]),
        "top_gap_items": [_source_stack_coverage_item(item) for item in gap_items[:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_source_reconstruction_summary(ws: WorkspacePaths, migration_dir: str | None) -> dict[str, Any] | None:
    if not migration_dir:
        return None
    manifest = build_legacy_source_reconstruction_manifest(ws, migration_dir=migration_dir)
    return {
        "surface": "legacy_source_reconstruction_manifest",
        "migration_dir": manifest["migration_dir"],
        "work_item_count": manifest["work_item_count"],
        "repair_status_counts": dict(manifest["repair_status_counts"]),
        "proposed_repair_count": int(manifest["proposed_repair_count"]),
        "top_backlog_items": [_legacy_source_backlog_item(item) for item in manifest["items"][:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _legacy_semantic_repair_summary(ws: WorkspacePaths, migration_dir: str | None) -> dict[str, Any] | None:
    if not migration_dir:
        return None
    manifest = build_legacy_semantic_repair_manifest(ws, migration_dir=migration_dir)
    return {
        "surface": "legacy_semantic_repair_manifest",
        "migration_dir": manifest["migration_dir"],
        "work_item_count": int(manifest["work_item_count"]),
        "repair_status_counts": dict(manifest["repair_status_counts"]),
        "proposed_repair_count": int(manifest["proposed_repair_count"]),
        "required_action_counts": dict(manifest["required_action_counts"]),
        "top_repair_items": [_legacy_semantic_repair_item(item) for item in manifest["items"][:5]],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _source_stack_coverage_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic_id": str(item.get("topic_id") or ""),
        "claim_id": str(item.get("claim_id") or ""),
        "risk_level": str(item.get("risk_level") or ""),
        "coverage_status": str(item.get("coverage_status") or ""),
        "missing_required_outputs": list(item.get("missing_required_outputs") or []),
        "missing_source_components": list(item.get("missing_source_components") or []),
        "source_reconstruction_review_status": str(item.get("source_reconstruction_review_status") or ""),
        "next_actions": list(item.get("next_actions") or []),
        "can_update_claim_trust": False,
    }


def _legacy_source_backlog_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "repair_status": str(item.get("repair_status") or ""),
        "missing_components": list(item.get("missing_components") or []),
        "required_actions": list(item.get("required_actions") or []),
        "review_packet_cli": str(item.get("review_packet_cli") or ""),
        "can_update_claim_trust": False,
    }


def _legacy_semantic_repair_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic": str(item.get("topic") or ""),
        "active_claim_id": str(item.get("active_claim_id") or ""),
        "latest_review_id": str(item.get("latest_review_id") or ""),
        "review_status": str(item.get("review_status") or ""),
        "repair_status": str(item.get("repair_status") or ""),
        "proposed_repair_count": int(item.get("proposed_repair_count") or 0),
        "proposed_repair_types": list(item.get("proposed_repair_types") or []),
        "required_actions": list(item.get("required_actions") or []),
        "repair_plan_cli": str(item.get("repair_plan_cli") or ""),
        "can_update_claim_trust": False,
    }


def _source_backlog_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": entry["session_id"],
        "topic_id": entry["topic_id"],
        "claim_id": entry["claim_id"],
        "review_status": entry["source_reconstruction_review_status"],
        "missing_components": list(entry["missing_source_components"]),
        "next_actions": list(entry["next_actions"]),
        "review_packet_cli": f"aitp-v5 source reconstruction-review --claim {entry['claim_id']}",
        "can_update_claim_trust": False,
    }


def _attention_item(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "session_id": entry["session_id"],
        "topic_id": entry["topic_id"],
        "claim_id": entry["claim_id"],
        "attention_reasons": list(entry["attention_reasons"]),
        "next_actions": list(entry["next_actions"]),
    }


def _prioritized_attention_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=_attention_priority)


def _attention_priority(entry: dict[str, Any]) -> tuple[int, int, str, str]:
    reasons = set(entry["attention_reasons"])
    severity = 0
    if "missing_claim_record" in reasons:
        severity -= 100
    if "missing_source_reconstruction" in reasons:
        severity -= 50
    if "source_reconstruction_review_pending" in reasons:
        severity -= 25
    if "missing_evidence_outputs" in reasons:
        severity -= 10
    return (severity, -len(reasons), entry["topic_id"], entry["session_id"])


def _review_status_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        if entry["claim_id"]:
            status = entry["source_reconstruction_review_status"] or "pending"
            counts[status] = counts.get(status, 0) + 1
    return counts


def _missing_component_counts(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        for component in entry["missing_source_components"]:
            counts[component] = counts.get(component, 0) + 1
    return counts


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
