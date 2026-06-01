"""Workspace-level research cockpit surfaces.

The cockpit is an orientation layer over existing AITP v5 records. It helps a
researcher decide what to work on next, but it never becomes a truth source and
never updates claim trust.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from brain.v5.interaction_worklist import build_interaction_recording_worklist
from brain.v5.models import ClaimRecord, EvidenceRecord, MemoryEntryRecord, ReferenceLocationRecord, SessionBinding
from brain.v5.operator_checkpoint import load_operator_checkpoint
from brain.v5.paths import WorkspacePaths
from brain.v5.source_stack_coverage import build_source_stack_coverage_manifest
from brain.v5.store import read_record
from brain.v5.topic_status import write_topic_status_surfaces
from brain.v5.workspace_refresh import refresh_workspace_views

_MANIFEST_VERSION = "research-cockpit-v1"
_QUEUE_LIMIT = 12
_TOPIC_STATUS_FALLBACK_LIMIT = 5


def safe_research_cockpit_refresh(ws: WorkspacePaths) -> dict[str, Any]:
    """Return a full refresh bundle, or a degraded best-effort bundle."""

    try:
        return refresh_workspace_views(ws)
    except Exception as exc:  # noqa: BLE001 - cockpit must survive legacy dirty records.
        return _degraded_refresh_bundle(ws, error=_format_error("workspace_refresh_bundle", exc))


def write_research_cockpit_surfaces(ws: WorkspacePaths) -> dict[str, Any]:
    """Write workspace-level research cockpit files and return the bundle."""

    refresh = safe_research_cockpit_refresh(ws)
    manifest = build_research_cockpit_manifest(ws, refresh_bundle=refresh)
    surface_dir = ws.root / "surfaces" / "research_cockpit"
    surface_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "manifest": str(surface_dir / "research_cockpit_manifest.json"),
        "dashboard": str(surface_dir / "Research Cockpit.md"),
        "queue": str(surface_dir / "Research Queue.md"),
    }
    _write_json(Path(files["manifest"]), manifest)
    Path(files["dashboard"]).write_text(_render_dashboard(manifest), encoding="utf-8")
    Path(files["queue"]).write_text(_render_queue(manifest), encoding="utf-8")
    return {
        "kind": "research_cockpit_bundle",
        "manifest_version": _MANIFEST_VERSION,
        "files": files,
        "manifest": manifest,
        "source_records": _source_records(manifest),
        "derived_from": "workspace_refresh_bundle",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def build_research_cockpit_manifest(
    ws: WorkspacePaths,
    *,
    refresh_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the conservative workspace cockpit manifest."""

    refresh = refresh_bundle or safe_research_cockpit_refresh(ws)
    topic_status_bundles = [
        bundle for bundle in refresh.get("topic_status_bundles", []) if isinstance(bundle, dict)
    ]
    coverage = refresh.get("source_stack_coverage") if isinstance(refresh.get("source_stack_coverage"), dict) else {}
    interaction_worklist = (
        refresh.get("interaction_recording_worklist")
        if isinstance(refresh.get("interaction_recording_worklist"), dict)
        else {}
    )
    references, reference_errors = _safe_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
    learning_gaps = _learning_gaps(coverage)
    reading_queue = _reading_queue(references, learning_gaps)
    operator_queue = _operator_queue(topic_status_bundles)
    today_queue = _today_queue(
        topic_status_bundles,
        learning_gaps=learning_gaps,
        interaction_items=interaction_worklist.get("items") or [],
    )
    return {
        "kind": "research_cockpit_manifest",
        "manifest_version": _MANIFEST_VERSION,
        "degraded_mode": bool(refresh.get("degraded_mode", False) or reference_errors),
        "read_errors": _read_errors(refresh, extra_errors=reference_errors),
        "workspace_summary": _workspace_summary(refresh),
        "today_queue": today_queue,
        "operator_queue": operator_queue,
        "learning_gaps": learning_gaps,
        "reading_queue": reading_queue,
        "topic_overview": _topic_overview(topic_status_bundles),
        "source_stack_coverage": {
            "claim_count": int(coverage.get("claim_count") or 0),
            "coverage_status_counts": dict(coverage.get("coverage_status_counts") or {}),
            "missing_required_output_counts": dict(coverage.get("missing_required_output_counts") or {}),
            "source_component_gap_counts": dict(coverage.get("source_component_gap_counts") or {}),
            "source_review_status_counts": dict(coverage.get("source_review_status_counts") or {}),
        },
        "interaction_worklist": {
            "work_item_count": int(interaction_worklist.get("work_item_count") or 0),
            "required_now_count": int(interaction_worklist.get("required_now_count") or 0),
            "decision_mode_counts": dict(interaction_worklist.get("decision_mode_counts") or {}),
        },
        "refresh_policy": dict(refresh.get("topic_status_refresh_policy") or {}),
        "source_surface_refs": {
            "workspace_refresh": "workspace_refresh_bundle",
            "topic_status": [f"topic_status_bundle:{item.get('session_id')}" for item in topic_status_bundles],
            "source_stack_coverage": "source_stack_coverage_manifest",
            "interaction_worklist": "interaction_recording_worklist",
        },
        "trust_update_forbidden": True,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def compact_research_cockpit_bundle(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a small host-friendly cockpit projection."""

    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), dict) else {}
    today = [item for item in manifest.get("today_queue", []) if isinstance(item, dict)]
    operator_queue = [item for item in manifest.get("operator_queue", []) if isinstance(item, dict)]
    learning_gaps = [item for item in manifest.get("learning_gaps", []) if isinstance(item, dict)]
    reading_queue = [item for item in manifest.get("reading_queue", []) if isinstance(item, dict)]
    coverage = manifest.get("source_stack_coverage") if isinstance(manifest.get("source_stack_coverage"), dict) else {}
    return {
        "kind": "research_cockpit_bundle_progress",
        "source_surface": "research_cockpit_bundle",
        "manifest_version": str(payload.get("manifest_version") or manifest.get("manifest_version") or ""),
        "files": dict(payload.get("files") or {}),
        "degraded_mode": bool(manifest.get("degraded_mode", False)),
        "read_error_count": len([item for item in manifest.get("read_errors", []) if isinstance(item, dict)]),
        "today_queue_count": len(today),
        "top_topics": [str(item.get("topic_id") or "") for item in today[:5] if item.get("topic_id")],
        "top_recommended_actions": [
            str(item.get("recommended_action") or "") for item in today[:5] if item.get("recommended_action")
        ],
        "operator_checkpoint_count": len(operator_queue),
        "learning_gap_count": len(learning_gaps),
        "reading_queue_count": len(reading_queue),
        "coverage_status_counts": dict(coverage.get("coverage_status_counts") or {}),
        "missing_required_output_counts": dict(coverage.get("missing_required_output_counts") or {}),
        "trust_update_forbidden": True,
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _degraded_refresh_bundle(ws: WorkspacePaths, *, error: dict[str, str]) -> dict[str, Any]:
    sessions, session_errors = _safe_records(ws.root / "runtime" / "sessions", SessionBinding)
    claims, claim_errors = _safe_records(ws.registry_dir("claims"), ClaimRecord)
    _evidence, evidence_errors = _safe_records(ws.registry_dir("evidence"), EvidenceRecord)
    memory_entries, memory_errors = _safe_records(ws.root / "memory" / "l2" / "entries", MemoryEntryRecord)
    coverage, coverage_errors = _safe_surface(
        "source_stack_coverage_manifest",
        lambda: build_source_stack_coverage_manifest(ws),
        fallback=_empty_source_stack_coverage(),
    )
    interaction_worklist, interaction_errors = _safe_surface(
        "interaction_recording_worklist",
        lambda: build_interaction_recording_worklist(ws),
        fallback=_empty_interaction_worklist(sessions),
    )
    topic_status_bundles, topic_status_errors = _best_effort_topic_status_bundles(ws, sessions)
    active_claim_ids = _unique([session.active_claim for session in sessions if session.active_claim])
    known_claim_ids = {claim.claim_id for claim in claims}
    active_claim_count = len([claim_id for claim_id in active_claim_ids if claim_id in known_claim_ids])
    active_memory_entries = [
        entry
        for entry in memory_entries
        if entry.status == "active" and entry.source_claim_id in active_claim_ids
    ]
    read_errors = [
        error,
        *session_errors,
        *claim_errors,
        *evidence_errors,
        *memory_errors,
        *coverage_errors,
        *interaction_errors,
        *topic_status_errors,
    ]
    return {
        "kind": "workspace_refresh_bundle",
        "degraded_mode": True,
        "degraded_reason": "full_workspace_refresh_failed",
        "read_errors": read_errors,
        "refreshed_surfaces": [
            "workspace_summary_bundle",
            coverage.get("kind", "source_stack_coverage_manifest"),
            interaction_worklist.get("kind", "interaction_recording_worklist"),
            "topic_status_bundle",
        ],
        "workspace_summary": {
            "kind": "workspace_summary_bundle",
            "session_count": len(sessions),
            "active_claim_count": active_claim_count,
            "memory_entry_count": len(active_memory_entries),
            "source_records": {
                "sessions": [session.session_id for session in sessions],
                "topics": _unique([session.topic_id for session in sessions if session.topic_id]),
                "claims": [claim_id for claim_id in active_claim_ids if claim_id in known_claim_ids],
                "memory_entries": [entry.entry_id for entry in active_memory_entries],
            },
            "truth_source": False,
            "orientation_only": True,
            "summary_inputs_trusted": False,
        },
        "source_stack_coverage": coverage,
        "interaction_recording_worklist": interaction_worklist,
        "topic_status_bundles": topic_status_bundles,
        "topic_status_refresh_policy": {
            "selection": "degraded_recent_sessions",
            "max_session_count": _TOPIC_STATUS_FALLBACK_LIMIT,
            "candidate_session_count": len(sessions),
            "refreshed_session_count": len(topic_status_bundles),
            "skipped_session_count": len(topic_status_errors),
            "degraded_mode": True,
        },
        "source_records": {
            "sessions": [session.session_id for session in sessions],
            "topics": _unique([session.topic_id for session in sessions if session.topic_id]),
            "claims": [claim.claim_id for claim in claims],
        },
        "derived_from": "kernel_state_best_effort",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _best_effort_topic_status_bundles(
    ws: WorkspacePaths,
    sessions: list[SessionBinding],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    bundles: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    claims, claim_errors = _safe_records(ws.registry_dir("claims"), ClaimRecord)
    claims_by_id = {claim.claim_id: claim for claim in claims}
    errors.extend(claim_errors)
    for session in sorted(sessions, key=lambda item: _session_mtime(ws, item.session_id), reverse=True):
        if len(bundles) >= _TOPIC_STATUS_FALLBACK_LIMIT:
            break
        try:
            bundles.append(write_topic_status_surfaces(ws, session_id=session.session_id))
        except Exception as exc:  # noqa: BLE001 - preserve other sessions in degraded mode.
            errors.append(_format_error(f"topic_status_bundle:{session.session_id}", exc))
            bundles.append(_minimal_topic_status_bundle(ws, session, claims_by_id))
    return bundles, errors


def _minimal_topic_status_bundle(
    ws: WorkspacePaths,
    session: SessionBinding,
    claims_by_id: dict[str, ClaimRecord],
) -> dict[str, Any]:
    claim = claims_by_id.get(session.active_claim) if session.active_claim else None
    checkpoint = _safe_operator_checkpoint(ws, session.topic_id)
    human_needed = bool(checkpoint.get("active"))
    topic_state = {
        "kind": "topic_state",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "context_id": session.context_id,
        "active_claim_id": session.active_claim,
        "claim_statement": claim.statement if claim else "",
        "confidence_state": claim.confidence_state if claim else "",
        "current_route_choice": session.active_route or "degraded_best_effort",
        "why_here": "full topic status failed; built from session and claim records only",
        "last_evidence_return": {},
        "next_bounded_action": {
            "action": "repair_or_refresh_topic_records",
            "why": "strict topic status could not read one or more records",
        },
        "blocker_summary": {
            "missing_outputs": [],
            "forbidden_now": ["update_claim_trust_from_degraded_cockpit"],
            "human_checkpoint_needed": human_needed,
            "human_checkpoint_reason": "active operator checkpoint detected" if human_needed else "",
        },
        "active_operator_checkpoint": checkpoint,
        "final_output_profile": {},
        "strategy_memory": {},
        "run_iterations": {},
        "lane_exemplars": {},
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "degraded_mode": True,
    }
    return {
        "kind": "topic_status_bundle",
        "topic_id": session.topic_id,
        "session_id": session.session_id,
        "files": {},
        "topic_state": topic_state,
        "source_records": {
            "topics": [session.topic_id],
            "sessions": [session.session_id],
            "claims": [session.active_claim] if session.active_claim else [],
        },
        "derived_from": "session_binding_best_effort",
        "truth_source": False,
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "degraded_mode": True,
    }


def _safe_operator_checkpoint(ws: WorkspacePaths, topic_id: str) -> dict[str, Any]:
    try:
        return load_operator_checkpoint(ws, topic_id)
    except Exception:  # noqa: BLE001 - absence or malformed checkpoint should not block degraded status.
        return {"present": False, "active": False, "summary_inputs_trusted": False, "can_update_claim_trust": False}


def _safe_records(directory: Path, cls: type) -> tuple[list[Any], list[dict[str, str]]]:
    if not directory.exists():
        return [], []
    records: list[Any] = []
    errors: list[dict[str, str]] = []
    for path in sorted(directory.glob("*.md")):
        try:
            records.append(read_record(path, cls))
        except Exception as exc:  # noqa: BLE001 - collect malformed legacy records for manifest diagnostics.
            errors.append(_format_error(str(path), exc))
    return records, errors


def _safe_surface(
    surface: str,
    build,
    *,
    fallback: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    try:
        return build(), []
    except Exception as exc:  # noqa: BLE001 - cockpit remains orientation-only under partial failure.
        payload = dict(fallback)
        payload["degraded_mode"] = True
        return payload, [_format_error(surface, exc)]


def _empty_source_stack_coverage() -> dict[str, Any]:
    return {
        "kind": "source_stack_coverage_manifest",
        "claim_count": 0,
        "coverage_status_counts": {},
        "missing_required_output_counts": {},
        "source_component_gap_counts": {},
        "source_review_status_counts": {},
        "items": [],
        "next_actions": [],
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _empty_interaction_worklist(sessions: list[SessionBinding]) -> dict[str, Any]:
    return {
        "kind": "interaction_recording_worklist",
        "session_count": len(sessions),
        "work_item_count": 0,
        "required_now_count": 0,
        "decision_mode_counts": {},
        "items": [],
        "source_preview_refs": [],
        "source_records": {
            "sessions": [session.session_id for session in sessions],
            "topics": _unique([session.topic_id for session in sessions if session.topic_id]),
            "claims": [session.active_claim for session in sessions if session.active_claim],
        },
        "derived_from": "workspace_interaction_preview_bundle",
        "truth_source": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "adapter_rule": "read_for_orientation_then_call_kernel_before_trust_updates",
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _read_errors(
    refresh: dict[str, Any],
    *,
    extra_errors: list[dict[str, str]],
) -> list[dict[str, str]]:
    errors = [
        item
        for item in refresh.get("read_errors", [])
        if isinstance(item, dict)
    ]
    errors.extend(item for item in extra_errors if isinstance(item, dict))
    return errors


def _format_error(source: str, exc: Exception) -> dict[str, str]:
    return {
        "source": source,
        "error_type": type(exc).__name__,
        "message": _excerpt(str(exc), limit=360),
    }


def _session_mtime(ws: WorkspacePaths, session_id: str) -> float:
    try:
        return ws.session_path(session_id).stat().st_mtime
    except OSError:
        return 0.0


def _workspace_summary(refresh: dict[str, Any]) -> dict[str, int]:
    summary = refresh.get("workspace_summary") if isinstance(refresh.get("workspace_summary"), dict) else {}
    return {
        "session_count": int(summary.get("session_count") or 0),
        "active_claim_count": int(summary.get("active_claim_count") or 0),
        "memory_entry_count": int(summary.get("memory_entry_count") or 0),
    }


def _today_queue(
    topic_status_bundles: list[dict[str, Any]],
    *,
    learning_gaps: list[dict[str, Any]],
    interaction_items: list[Any],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    learning_by_topic: dict[str, list[dict[str, Any]]] = {}
    for gap in learning_gaps:
        learning_by_topic.setdefault(str(gap.get("topic_id") or ""), []).append(gap)
    interaction_by_topic: dict[str, list[dict[str, Any]]] = {}
    for item in interaction_items:
        if isinstance(item, dict):
            interaction_by_topic.setdefault(str(item.get("topic_id") or ""), []).append(item)
    for bundle in topic_status_bundles:
        state = bundle.get("topic_state") if isinstance(bundle.get("topic_state"), dict) else {}
        topic_id = str(bundle.get("topic_id") or state.get("topic_id") or "")
        blocker = state.get("blocker_summary") if isinstance(state.get("blocker_summary"), dict) else {}
        next_action = state.get("next_bounded_action") if isinstance(state.get("next_bounded_action"), dict) else {}
        checkpoint = state.get("active_operator_checkpoint") if isinstance(state.get("active_operator_checkpoint"), dict) else {}
        human_needed = bool(blocker.get("human_checkpoint_needed")) or bool(checkpoint.get("active"))
        missing_outputs = list(blocker.get("missing_outputs") or [])
        topic_learning = learning_by_topic.get(topic_id, [])
        recommended = "answer_operator_checkpoint" if human_needed else str(next_action.get("action") or "")
        if not recommended and topic_learning:
            recommended = "close_learning_or_source_gap"
        if not recommended:
            recommended = "inspect_topic_status"
        items.append(
            {
                "topic_id": topic_id,
                "session_id": str(bundle.get("session_id") or state.get("session_id") or ""),
                "active_claim_id": str(state.get("active_claim_id") or ""),
                "claim_statement_excerpt": _excerpt(state.get("claim_statement") or ""),
                "confidence_state": str(state.get("confidence_state") or ""),
                "current_route_choice": str(state.get("current_route_choice") or ""),
                "recommended_action": recommended,
                "why": _queue_reason(human_needed, missing_outputs, topic_learning, next_action),
                "human_checkpoint_needed": human_needed,
                "missing_output_count": len(missing_outputs),
                "learning_gap_count": len(topic_learning),
                "interaction_recording_items": len(interaction_by_topic.get(topic_id, [])),
                "source_surface_ref": f"topic_status_bundle:{bundle.get('session_id')}",
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    items.sort(key=_today_sort_key)
    return items[:_QUEUE_LIMIT]


def _queue_reason(
    human_needed: bool,
    missing_outputs: list[str],
    topic_learning: list[dict[str, Any]],
    next_action: dict[str, Any],
) -> str:
    if human_needed:
        return "human/operator checkpoint blocks safe continuation"
    if missing_outputs:
        return "required evidence outputs are missing"
    if topic_learning:
        return "source reconstruction or literature learning gap is open"
    return str(next_action.get("why") or "topic has a bounded next action")


def _today_sort_key(item: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        0 if item["human_checkpoint_needed"] else 1,
        -int(item["missing_output_count"]),
        -int(item["learning_gap_count"]),
        str(item["topic_id"]),
    )


def _operator_queue(topic_status_bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for bundle in topic_status_bundles:
        state = bundle.get("topic_state") if isinstance(bundle.get("topic_state"), dict) else {}
        checkpoint = state.get("active_operator_checkpoint") if isinstance(state.get("active_operator_checkpoint"), dict) else {}
        if not checkpoint.get("active"):
            continue
        items.append(
            {
                "topic_id": str(bundle.get("topic_id") or state.get("topic_id") or ""),
                "session_id": str(bundle.get("session_id") or state.get("session_id") or ""),
                "active_claim_id": str(state.get("active_claim_id") or checkpoint.get("claim_id") or ""),
                "checkpoint_id": str(checkpoint.get("checkpoint_id") or ""),
                "checkpoint_kind": str(checkpoint.get("checkpoint_kind") or ""),
                "question_excerpt": _excerpt(checkpoint.get("question") or ""),
                "options": list(checkpoint.get("options") or []),
                "required_next_action": str(checkpoint.get("required_next_action") or "answer_operator_checkpoint"),
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    return items


def _learning_gaps(coverage: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in coverage.get("items", []):
        if not isinstance(item, dict) or item.get("coverage_status") == "complete":
            continue
        missing_outputs = list(item.get("missing_required_outputs") or [])
        missing_components = list(item.get("missing_source_components") or [])
        if missing_outputs:
            gap_kind = "evidence_output_gap"
        elif missing_components:
            gap_kind = "source_reconstruction_gap"
        elif str(item.get("source_reconstruction_review_status") or "") != "passed":
            gap_kind = "source_review_gap"
        else:
            gap_kind = "learning_gap"
        items.append(
            {
                "topic_id": str(item.get("topic_id") or ""),
                "claim_id": str(item.get("claim_id") or ""),
                "claim_statement_excerpt": _excerpt(item.get("claim_statement") or ""),
                "gap_kind": gap_kind,
                "coverage_status": str(item.get("coverage_status") or ""),
                "risk_level": str(item.get("risk_level") or ""),
                "missing_required_outputs": missing_outputs,
                "missing_source_components": missing_components,
                "source_reconstruction_review_status": str(item.get("source_reconstruction_review_status") or ""),
                "recommended_action": _learning_action(gap_kind),
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    return items[:_QUEUE_LIMIT]


def _learning_action(gap_kind: str) -> str:
    if gap_kind == "evidence_output_gap":
        return "record_or_collect_required_evidence"
    if gap_kind == "source_reconstruction_gap":
        return "complete_source_reconstruction"
    if gap_kind == "source_review_gap":
        return "review_source_reconstruction"
    return "clarify_learning_gap"


def _reading_queue(
    references: list[ReferenceLocationRecord],
    learning_gaps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    gaps_by_claim = {str(gap.get("claim_id") or ""): gap for gap in learning_gaps if gap.get("claim_id")}
    items: list[dict[str, Any]] = []
    for reference in references:
        gap = gaps_by_claim.get(reference.claim_id, {})
        if not gap and reference.status not in {"candidate", "located"}:
            continue
        items.append(
            {
                "topic_id": reference.topic_id,
                "claim_id": reference.claim_id,
                "reference_location_id": reference.location_id,
                "label": reference.label,
                "uri": reference.uri,
                "status": reference.status,
                "why_read": _why_read(reference, gap),
                "serves_gap_kind": str(gap.get("gap_kind") or ""),
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    items.sort(key=lambda item: (0 if item["serves_gap_kind"] else 1, item["topic_id"], item["label"]))
    return items[:_QUEUE_LIMIT]


def _why_read(reference: ReferenceLocationRecord, gap: dict[str, Any]) -> str:
    if gap:
        return f"serves {gap.get('gap_kind')} for active claim"
    if reference.summary:
        return reference.summary
    return "candidate literature/source location; record intake before treating as evidence"


def _topic_overview(topic_status_bundles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for bundle in topic_status_bundles:
        state = bundle.get("topic_state") if isinstance(bundle.get("topic_state"), dict) else {}
        blocker = state.get("blocker_summary") if isinstance(state.get("blocker_summary"), dict) else {}
        items.append(
            {
                "topic_id": str(bundle.get("topic_id") or state.get("topic_id") or ""),
                "session_id": str(bundle.get("session_id") or state.get("session_id") or ""),
                "active_claim_id": str(state.get("active_claim_id") or ""),
                "confidence_state": str(state.get("confidence_state") or ""),
                "current_route_choice": str(state.get("current_route_choice") or ""),
                "missing_outputs": list(blocker.get("missing_outputs") or []),
                "forbidden_now": list(blocker.get("forbidden_now") or []),
                "human_checkpoint_needed": bool(blocker.get("human_checkpoint_needed")),
            }
        )
    return items


def _source_records(manifest: dict[str, Any]) -> dict[str, list[str]]:
    topics = _unique(
        [
            *[str(item.get("topic_id") or "") for item in manifest.get("topic_overview", []) if isinstance(item, dict)],
            *[str(item.get("topic_id") or "") for item in manifest.get("reading_queue", []) if isinstance(item, dict)],
        ]
    )
    sessions = _unique(
        [
            str(item.get("session_id") or "")
            for item in manifest.get("topic_overview", [])
            if isinstance(item, dict)
        ]
    )
    claims = _unique(
        [
            *[str(item.get("active_claim_id") or "") for item in manifest.get("topic_overview", []) if isinstance(item, dict)],
            *[str(item.get("claim_id") or "") for item in manifest.get("learning_gaps", []) if isinstance(item, dict)],
        ]
    )
    references = _unique(
        [
            str(item.get("reference_location_id") or "")
            for item in manifest.get("reading_queue", [])
            if isinstance(item, dict)
        ]
    )
    return {
        "topics": [item for item in topics if item],
        "sessions": [item for item in sessions if item],
        "claims": [item for item in claims if item],
        "reference_locations": [item for item in references if item],
    }


def _render_dashboard(manifest: dict[str, Any]) -> str:
    summary = manifest["workspace_summary"]
    coverage = manifest["source_stack_coverage"]
    return (
        "# AITP Research Cockpit\n\n"
        "This cockpit is orientation-only. Refresh typed records before any trust-changing action.\n\n"
        "## Workspace\n\n"
        f"- Sessions: {summary['session_count']}\n"
        f"- Active claims: {summary['active_claim_count']}\n"
        f"- L2 memory entries: {summary['memory_entry_count']}\n\n"
        "## Do Now\n\n"
        f"{_bullets(_queue_lines(manifest.get('today_queue', [])))}\n\n"
        "## Operator Decisions\n\n"
        f"{_bullets(_operator_lines(manifest.get('operator_queue', [])))}\n\n"
        "## Learning / Literature Gaps\n\n"
        f"{_bullets(_learning_lines(manifest.get('learning_gaps', [])))}\n\n"
        "## Coverage\n\n"
        f"- Claims: {coverage['claim_count']}\n"
        f"- Coverage statuses: {coverage['coverage_status_counts']}\n"
        f"- Missing outputs: {coverage['missing_required_output_counts']}\n\n"
        "Do not promote, update claim trust, or treat this Markdown as evidence.\n"
    )


def _render_queue(manifest: dict[str, Any]) -> str:
    return (
        "# Research Queue\n\n"
        "## Today Queue\n\n"
        f"{_bullets(_queue_lines(manifest.get('today_queue', [])))}\n\n"
        "## Reading Queue\n\n"
        f"{_bullets(_reading_lines(manifest.get('reading_queue', [])))}\n\n"
        "## Learning Gaps\n\n"
        f"{_bullets(_learning_lines(manifest.get('learning_gaps', [])))}\n"
    )


def _queue_lines(items: list[Any]) -> list[str]:
    return [
        f"{item.get('topic_id')}: {item.get('recommended_action')} - {item.get('why')}"
        for item in items
        if isinstance(item, dict)
    ]


def _operator_lines(items: list[Any]) -> list[str]:
    return [
        f"{item.get('topic_id')}: {item.get('question_excerpt')}"
        for item in items
        if isinstance(item, dict)
    ]


def _learning_lines(items: list[Any]) -> list[str]:
    return [
        f"{item.get('topic_id')}: {item.get('gap_kind')} for {item.get('claim_id')}"
        for item in items
        if isinstance(item, dict)
    ]


def _reading_lines(items: list[Any]) -> list[str]:
    return [
        f"{item.get('topic_id')}: {item.get('label')} - {item.get('why_read')}"
        for item in items
        if isinstance(item, dict)
    ]


def _bullets(values: list[str]) -> str:
    items = [str(value) for value in values if str(value)]
    return "\n".join(f"- {value}" for value in items) if items else "- None"


def _excerpt(value: Any, *, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
