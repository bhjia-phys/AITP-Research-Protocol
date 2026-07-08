"""Read-only research timeline and continuation state for AITP v5."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.claim_relation_map import build_claim_relation_map
from brain.v5.markdown import read_md
from brain.v5.models import (
    ArtifactRecord,
    ClaimStatusRecord,
    EvidenceRecord,
    LifecycleEventRecord,
    ProofObligationRecord,
    QuietCheckpointBatchRecord,
    ResearchRouteRecord,
    ResearchRunEventRecord,
    ResearchRunRecord,
    SensemakingReportRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.recovery_session import recover_session_binding_for_read


_SUPPORT_STATUSES = {"support", "supports", "supported", "passed", "pass", "valid", "positive"}
_LIMIT_STATUSES = {"mixed", "partial", "limited", "inconclusive", "diagnostic", "unreviewed", "open"}
_CONTRADICT_STATUSES = {"negative", "failed", "fail", "invalid", "refutes", "refute", "contradicts"}
_HISTORICAL_LIFECYCLE = {"superseded", "duplicate"}
_INACTIVE_LIFECYCLE = {"misrouted", "voided"}
_WRONG_ROUTE_MARKERS = (
    "wrong",
    "incorrect",
    "deprecated",
    "superseded",
    "misrouted",
    "voided",
    "does not test",
    "does_not_test",
    "not test",
    "failed before",
    "runtime failure",
    "setup failure",
    "application failure",
)


_RECORD_SPECS: tuple[tuple[str, type[Any], str, str, tuple[str, ...]], ...] = (
    ("claim_statuses", ClaimStatusRecord, "status_id", "claim_status", ("claim_status", "scope", "risk", "next_action")),
    ("evidence", EvidenceRecord, "evidence_id", "evidence", ("summary", "status", "evidence_type")),
    ("tool_runs", ToolRunRecord, "run_id", "tool_run", ("tool_family", "tool_name", "evidence_status")),
    ("validation_results", ValidationResultRecord, "result_id", "validation_result", ("summary", "status")),
    ("proof_obligations", ProofObligationRecord, "obligation_id", "proof_obligation", ("statement", "status", "next_action")),
    ("artifacts", ArtifactRecord, "artifact_id", "artifact", ("summary", "artifact_type", "uri")),
    ("sensemaking_reports", SensemakingReportRecord, "report_id", "sensemaking_report", ("title", "summary", "validation_status")),
    ("quiet_checkpoints", QuietCheckpointBatchRecord, "checkpoint_id", "quiet_checkpoint", ("summary", "status")),
    ("routes", ResearchRouteRecord, "route_id", "research_route", ("title", "status", "rationale", "pivot_reason")),
    ("research_runs", ResearchRunRecord, "run_id", "research_run", ("title", "objective", "status", "terminal_answer_state")),
    ("research_run_events", ResearchRunEventRecord, "event_id", "research_run_event", ("event_type", "summary", "status")),
    ("lifecycle_events", LifecycleEventRecord, "event_id", "lifecycle_event", ("event_type", "reason", "lifecycle_status")),
)


def build_research_timeline(
    ws: WorkspacePaths,
    session_id: str,
    *,
    claim_id: str = "",
    limit: int = 80,
) -> dict[str, Any]:
    """Build a read-only continuation timeline from typed records.

    The timeline is for session recovery and route awareness only. It cannot
    create evidence, validate a claim, rebind a session, or change trust.
    """

    limit = max(1, min(int(limit or 80), 200))
    recovered = recover_session_binding_for_read(ws, session_id)
    session = recovered.session
    focus_claim_id = claim_id or session.active_claim
    relation_map = build_claim_relation_map(ws, session_id)
    relation_buckets = _relation_buckets(relation_map)
    events = _timeline_events(
        ws,
        topic_id=session.topic_id,
        claim_id=focus_claim_id,
        session_id=session.session_id,
        relation_buckets=relation_buckets,
    )
    events.sort(key=lambda item: (float(item.get("_sort_time") or 0.0), str(item.get("record_ref") or "")), reverse=True)
    events = [_strip_private(event) for event in events[:limit]]
    failed_attempts = _previous_failed_attempts_from_events(events, limit=12)
    wrong_routes = _wrong_or_superseded_routes(events, limit=12)
    latest_results = _latest_results_from_relation_map(relation_map)

    payload = {
        "ok": True,
        "kind": "research_timeline",
        "session_id": session.session_id,
        "requested_session_id": recovered.requested_session_id,
        "recovery_selection_source": recovered.recovery_selection_source,
        "topic_id": session.topic_id,
        "claim_id": focus_claim_id,
        "scope": "active_claim_plus_topic_process_records",
        "event_count": len(events),
        "events": events,
        "latest_results": latest_results,
        "previous_failed_attempts": failed_attempts,
        "wrong_or_superseded_routes": wrong_routes,
        "continuation_state": {
            "current_conclusion": relation_map.get("current_conclusion") or {},
            "latest_claim_status": relation_map.get("latest_claim_status") or {},
            "current_blockers": list(relation_map.get("current_blockers") or []),
            "next_valid_actions": list(relation_map.get("next_valid_actions") or []),
            "active_claim_focus_reconciliation": relation_map.get("active_claim_focus_reconciliation") or {},
            "not_authoritative_for_current_goal_if_rebind_needed": bool(
                relation_map.get("not_authoritative_for_current_goal_if_rebind_needed")
            ),
        },
        "timeline_policy": {
            "truth_source": "typed_records",
            "time_order_source": "explicit_record_time_or_file_mtime_fallback",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "can_rebind_without_confirmation": False,
            "validation_result_is_not_claim_support_by_itself": True,
            "wrong_routes_are_context_not_counterevidence_unless_typed_as_contradiction": True,
        },
        "source_records": {
            "claim_relation_map": f"claim_relation_map:{session.session_id}",
            "events": [event.get("record_ref", "") for event in events if event.get("record_ref")],
            "previous_failed_attempts": [item.get("record_ref", "") for item in failed_attempts if item.get("record_ref")],
            "wrong_or_superseded_routes": [item.get("record_ref", "") for item in wrong_routes if item.get("record_ref")],
        },
        "truth_source": "typed_records",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    return payload


def previous_failed_attempts_from_relation_map(payload: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    """Extract a compact failed-route list for execution briefs."""

    rows: list[dict[str, Any]] = []
    for bucket, classification in (
        ("not_tested_by", "failed_attempt_not_testing_claim"),
        ("contradicted_by", "contradicted_or_failed_claim_route"),
        ("historical", "superseded_or_duplicate_route"),
        ("misrouted", "misrouted_or_voided_record"),
    ):
        for entry in payload.get(bucket) or []:
            if not isinstance(entry, dict):
                continue
            rows.append(
                {
                    "record_ref": _entry_ref(entry),
                    "record_kind": str(entry.get("record_kind") or ""),
                    "record_id": str(entry.get("record_id") or ""),
                    "classification": classification,
                    "status": str(entry.get("status") or ""),
                    "summary": _short_text(entry.get("summary") or entry.get("reason") or ""),
                    "continuation_boundary": _boundary_for_classification(classification),
                    "can_update_claim_trust": False,
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def _timeline_events(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    claim_id: str,
    session_id: str,
    relation_buckets: dict[str, str],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for directory, cls, id_attr, kind, summary_fields in _RECORD_SPECS:
        for record, path, frontmatter in _records_with_paths(ws.registry_dir(directory), cls):
            if not _record_in_scope(record, topic_id=topic_id, claim_id=claim_id, session_id=session_id):
                continue
            record_id = str(getattr(record, id_attr, "") or "")
            record_ref = f"{kind}:{record_id}" if record_id else kind
            event_time, time_source, sort_time = _event_time(path, record, frontmatter)
            status = _record_status(record)
            lifecycle = str(getattr(record, "lifecycle_status", "") or "")
            text = _record_text(record, summary_fields)
            if str(getattr(record, "superseded_by", "") or "").strip():
                classification = "superseded_or_duplicate_route"
            elif relation_buckets.get(record_id):
                classification = relation_buckets[record_id]
            else:
                classification = _classify_record(
                    status=status,
                    lifecycle_status=lifecycle,
                    text=text,
                    kind=kind,
                )
            events.append(
                {
                    "record_ref": record_ref,
                    "record_kind": kind,
                    "record_id": record_id,
                    "event_time": event_time,
                    "time_source": time_source,
                    "topic_id": str(getattr(record, "topic_id", "") or topic_id),
                    "claim_id": str(getattr(record, "claim_id", "") or ""),
                    "session_id": str(getattr(record, "session_id", "") or ""),
                    "status": status,
                    "lifecycle_status": lifecycle,
                    "classification": classification,
                    "summary": _short_text(text or record_ref),
                    "refs": _record_refs(record),
                    "orientation_only": bool(getattr(record, "orientation_only", kind not in {"evidence", "validation_result"})),
                    "can_update_claim_trust": bool(getattr(record, "can_update_claim_trust", False)),
                    "_sort_time": sort_time,
                }
            )
    return events


def _records_with_paths(directory: Path, cls: type[Any]) -> list[tuple[Any, Path, dict[str, Any]]]:
    if not directory.exists():
        return []
    records: list[tuple[Any, Path, dict[str, Any]]] = []
    allowed = {field.name for field in fields(cls)} if is_dataclass(cls) else set()
    for path in sorted(directory.glob("*.md")):
        try:
            frontmatter, _ = read_md(path)
            data = {key: value for key, value in frontmatter.items() if key in allowed} if allowed else dict(frontmatter)
            records.append((cls(**data), path, frontmatter))
        except (TypeError, ValueError, OSError):
            continue
    return records


def _record_in_scope(record: Any, *, topic_id: str, claim_id: str, session_id: str) -> bool:
    record_topic = str(getattr(record, "topic_id", "") or "")
    if record_topic and record_topic != topic_id:
        return False
    record_claim = str(getattr(record, "claim_id", "") or "")
    record_session = str(getattr(record, "session_id", "") or "")
    if record_claim and record_claim == claim_id:
        return True
    if record_session and record_session == session_id:
        return True
    return not record_claim and not record_session


def _event_time(path: Path, record: Any, frontmatter: dict[str, Any]) -> tuple[str, str, float]:
    for key in ("timestamp", "updated_at", "created_at", "captured_at", "acquired_at"):
        value = _time_value(frontmatter.get(key))
        if value:
            return value, key, _sort_time(value, path)
    metadata = frontmatter.get("metadata")
    if isinstance(metadata, dict):
        for key in ("timestamp", "updated_at", "created_at", "captured_at", "acquired_at"):
            value = _time_value(metadata.get(key))
            if value:
                return value, f"metadata.{key}", _sort_time(value, path)
    runtime = frontmatter.get("runtime_environment")
    if isinstance(runtime, dict):
        for key in ("timestamp", "captured_at", "created_at"):
            value = _time_value(runtime.get(key))
            if value:
                return value, f"runtime_environment.{key}", _sort_time(value, path)
    for key in ("timestamp", "acquired_at"):
        value = _time_value(getattr(record, key, ""))
        if value:
            return value, key, _sort_time(value, path)
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, timezone.utc).isoformat(), "file_mtime", mtime


def _time_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else ""


def _sort_time(value: str, path: Path) -> float:
    text = str(value or "").strip()
    if text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _record_status(record: Any) -> str:
    for key in ("status", "evidence_status", "claim_status", "validation_status", "terminal_answer_state"):
        value = str(getattr(record, key, "") or "").strip()
        if value:
            return value
    return ""


def _record_text(record: Any, fields_: tuple[str, ...]) -> str:
    parts: list[str] = []
    for key in fields_:
        value = getattr(record, key, "")
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        elif value:
            parts.append(str(value))
    return " ".join(part.strip() for part in parts if str(part).strip())


def _classify_record(*, status: str, lifecycle_status: str, text: str, kind: str) -> str:
    lifecycle = lifecycle_status.strip().lower()
    normalized = status.strip().lower()
    lowered = " ".join([normalized, lifecycle, text.lower()])
    if lifecycle in _INACTIVE_LIFECYCLE:
        return "misrouted_or_voided_record"
    if lifecycle in _HISTORICAL_LIFECYCLE:
        return "superseded_or_duplicate_route"
    if any(marker in lowered for marker in _WRONG_ROUTE_MARKERS):
        if "does not test" in lowered or "does_not_test" in lowered or "not test" in lowered:
            return "failed_attempt_not_testing_claim"
        return "wrong_or_superseded_route"
    if normalized in _CONTRADICT_STATUSES:
        return "contradicted_or_failed_claim_route"
    if normalized in _LIMIT_STATUSES:
        return "limitation_or_open_gap"
    if normalized in _SUPPORT_STATUSES:
        return "support_or_pass"
    if kind in {"proof_obligation", "claim_status"}:
        return "continuation_boundary"
    return "context_event"


def _relation_buckets(relation_map: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for bucket, classification in (
        ("supported_by", "support_or_pass"),
        ("limited_by", "limitation_or_open_gap"),
        ("contradicted_by", "contradicted_or_failed_claim_route"),
        ("not_tested_by", "failed_attempt_not_testing_claim"),
        ("historical", "superseded_or_duplicate_route"),
        ("misrouted", "misrouted_or_voided_record"),
    ):
        for entry in relation_map.get(bucket) or []:
            if isinstance(entry, dict) and entry.get("record_id"):
                mapping[str(entry["record_id"])] = classification
    return mapping


def _latest_results_from_relation_map(relation_map: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    return {
        "supported_by": _compact_relation_entries(relation_map.get("supported_by") or []),
        "limited_by": _compact_relation_entries(relation_map.get("limited_by") or []),
        "contradicted_by": _compact_relation_entries(relation_map.get("contradicted_by") or []),
        "not_tested_by": _compact_relation_entries(relation_map.get("not_tested_by") or []),
    }


def _compact_relation_entries(entries: list[Any], *, limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries[:limit]:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "record_ref": _entry_ref(entry),
                "record_kind": str(entry.get("record_kind") or ""),
                "record_id": str(entry.get("record_id") or ""),
                "status": str(entry.get("status") or ""),
                "summary": _short_text(entry.get("summary") or entry.get("reason") or ""),
                "can_update_claim_trust": False,
            }
        )
    return rows


def _previous_failed_attempts_from_events(events: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for event in events:
        if event.get("classification") not in {
            "failed_attempt_not_testing_claim",
            "contradicted_or_failed_claim_route",
            "wrong_or_superseded_route",
            "superseded_or_duplicate_route",
            "misrouted_or_voided_record",
        }:
            continue
        rows.append(
            {
                "record_ref": str(event.get("record_ref") or ""),
                "record_kind": str(event.get("record_kind") or ""),
                "classification": str(event.get("classification") or ""),
                "status": str(event.get("status") or ""),
                "event_time": str(event.get("event_time") or ""),
                "summary": _short_text(event.get("summary") or ""),
                "continuation_boundary": _boundary_for_classification(str(event.get("classification") or "")),
                "can_update_claim_trust": False,
            }
        )
        if len(rows) >= limit:
            return rows
    return rows


def _wrong_or_superseded_routes(events: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    return [
        row
        for row in _previous_failed_attempts_from_events(events, limit=limit)
        if row["classification"]
        in {"wrong_or_superseded_route", "superseded_or_duplicate_route", "misrouted_or_voided_record"}
    ][:limit]


def _record_refs(record: Any) -> list[str]:
    refs: list[str] = []
    for key in (
        "source_refs",
        "evidence_refs",
        "validation_refs",
        "artifact_refs",
        "artifact_ids",
        "tool_run_ids",
        "validation_result_ids",
        "code_state_ids",
        "action_refs",
        "aitp_slice_refs",
    ):
        value = getattr(record, key, [])
        if isinstance(value, list):
            refs.extend(str(item) for item in value if str(item).strip())
    return _dedupe(refs)


def _entry_ref(entry: dict[str, Any]) -> str:
    kind = str(entry.get("record_kind") or "").strip()
    record_id = str(entry.get("record_id") or "").strip()
    return f"{kind}:{record_id}" if kind and record_id else record_id


def _boundary_for_classification(classification: str) -> str:
    if classification == "failed_attempt_not_testing_claim":
        return "route failed or was blocked before testing the active claim"
    if classification == "contradicted_or_failed_claim_route":
        return "typed as contradiction/failure for the scoped claim; inspect before reuse"
    if classification == "misrouted_or_voided_record":
        return "inactive lifecycle record; do not use as active conclusion"
    if classification in {"superseded_or_duplicate_route", "wrong_or_superseded_route"}:
        return "historical route; preserve as context, not current active result"
    return "continuation context only"


def _short_text(value: Any, *, limit: int = 320) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _strip_private(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if not key.startswith("_")}


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result
