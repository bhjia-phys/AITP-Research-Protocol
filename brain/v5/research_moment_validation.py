"""Structured validation helpers for research-moment policy and application."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any, Mapping

from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.recording_batch_contracts import ACCEPTED_CANDIDATE_KINDS
from brain.v5.research_moment_contracts import ResearchEvent, normalize_timestamp
from brain.v5.research_scope_contracts import canonical_typed_ref


_MAX_DISCOVERY_RESULTS = 50
_MAX_DISCOVERY_TIMEOUT_SECONDS = 60
_MAX_DISCOVERY_TTL_SECONDS = 3600


def validated_capture_arguments(event: ResearchEvent, operation: str) -> dict[str, Any]:
    args = dict(mapping(event.objective_payload.get("arguments"), "arguments"))
    required_fields = {
        "capture_source_asset_auto": ("path",),
        "capture_code_state_auto": ("worktree_path",),
        "capture_tool_run_auto": (
            "path",
            "recipe_id",
            "tool_family",
            "tool_name",
            "claim_id",
        ),
        "attach_artifact_auto": ("path", "claim_id", "artifact_type", "summary"),
    }
    for field in required_fields.get(operation, ()):
        required_payload_text(args, field)
    if operation in {"capture_source_asset_auto", "capture_tool_run_auto", "attach_artifact_auto"}:
        _bind_scope_argument(args, "topic_id", event.topic_id)
    if operation == "capture_code_state_auto":
        _bind_scope_argument(args, "topic_id", event.topic_id)
        _bind_scope_argument(args, "session_id", event.session_id)
    if operation == "capture_source_asset_auto":
        if args.get("force_refresh") is True:
            raise ValueError("automatic source capture cannot force-refresh stored source bytes")
        args["force_refresh"] = False
    if operation == "capture_tool_run_auto":
        if str(args.get("lane") or "diagnostic") != "diagnostic":
            raise ValueError("automatic tool-run capture is restricted to the diagnostic lane")
        args["lane"] = "diagnostic"
        args["evidence_status"] = "unreviewed"
    return _finite_json_object(args, "arguments")


def validated_semantic_payload(
    event: ResearchEvent,
    source_refs: tuple[str, ...],
) -> dict[str, Any]:
    semantic = dict(event.semantic_payload)
    for field in ("candidate_kind", "semantic_key", "summary"):
        required_payload_text(semantic, field)
    if semantic["candidate_kind"] not in ACCEPTED_CANDIDATE_KINDS:
        raise ValueError("semantic candidate_kind is not supported")
    payload = mapping(semantic.get("payload"), "semantic payload")
    if not source_refs:
        raise ValueError("semantic candidates require at least one exact source ref")
    expires_at = normalize_timestamp(
        semantic.get("expires_at")
        or (datetime.fromisoformat(event.occurred_at) + timedelta(days=7)).isoformat(),
        "semantic expires_at",
    )
    missing_prerequisites = semantic.get("missing_prerequisites") or ()
    if not isinstance(missing_prerequisites, (list, tuple)):
        raise TypeError("missing_prerequisites must be a list or tuple")
    return _finite_json_object(
        {
            "candidate_kind": semantic["candidate_kind"],
            "semantic_key": semantic["semantic_key"],
            "summary": semantic["summary"],
            "payload": dict(payload),
            "source_refs": list(source_refs),
            "missing_prerequisites": [
                required_payload_text({"value": value}, "value")
                for value in missing_prerequisites
            ],
            "expires_at": expires_at,
        },
        "semantic candidate",
    )


def validated_discovery_spec(value: object) -> dict[str, Any]:
    spec = dict(mapping(value, "discovery_spec"))
    required = (
        "gap_ref",
        "prior_audit_ref",
        "framework",
        "regime",
        "required_source_types",
        "connector_allowlist",
        "max_results",
        "timeout_seconds",
        "ttl_seconds",
    )
    missing = [field for field in required if field not in spec]
    if missing:
        raise ValueError("discovery_spec is missing: " + ", ".join(missing))
    pinned_record_ref(spec["gap_ref"])
    pinned_record_ref(spec["prior_audit_ref"])
    max_results = _bounded_int(spec["max_results"], "max_results", 1, _MAX_DISCOVERY_RESULTS)
    timeout = _bounded_int(
        spec["timeout_seconds"],
        "timeout_seconds",
        1,
        _MAX_DISCOVERY_TIMEOUT_SECONDS,
    )
    ttl = _bounded_int(spec["ttl_seconds"], "ttl_seconds", 1, _MAX_DISCOVERY_TTL_SECONDS)
    return _finite_json_object(
        {
            **spec,
            "max_results": max_results,
            "timeout_seconds": timeout,
            "ttl_seconds": ttl,
        },
        "discovery_spec",
    )


def unreadable_refs(ws: WorkspacePaths, refs: tuple[str, ...]) -> list[str]:
    repository = read_repository(ws)
    missing: list[str] = []
    for ref in refs:
        result = repository.read(ref)
        if result.status != "found" or result.record is None:
            missing.append(ref)
    return missing


def stale_pins(ws: WorkspacePaths, values: object) -> list[str]:
    if values in (None, (), []):
        return []
    if not isinstance(values, (list, tuple)):
        raise TypeError("pinned_prerequisites must be a list or tuple")
    stale: list[str] = []
    for value in values:
        pin = pinned_record_ref(value)
        try:
            current = pin_current_record(ws, pin.record_ref)
            get_record_version(ws, pin)
        except Exception:  # noqa: BLE001 - any pin failure is a closed prerequisite.
            stale.append(pin.record_ref)
            continue
        if current != pin:
            stale.append(pin.record_ref)
    return stale


def is_unchanged_poll(event: ResearchEvent) -> bool:
    payload = event.objective_payload
    return payload.get("content_changed") is False and str(payload.get("poll_kind") or "") in {
        "heartbeat",
        "status_poll",
    }


def is_knowledge_discovery(event: ResearchEvent) -> bool:
    return (
        event.event_type == "FailureOrGapObserved"
        and str(event.objective_payload.get("gap_kind") or "").casefold() == "knowledge"
        and "discovery_spec" in event.objective_payload
    )


def requested_action(event: ResearchEvent) -> str:
    return " ".join(str(event.objective_payload.get("requested_action") or "").split())


def default_action(event: ResearchEvent) -> str:
    return requested_action(event) or f"process_{event.event_type}"


def claim_id(event: ResearchEvent) -> str:
    explicit = " ".join(str(event.objective_payload.get("claim_id") or "").split())
    if explicit:
        return explicit
    for ref in event.subject_refs:
        _canonical, spec, record_id = canonical_typed_ref(ref)
        if spec.family == "claims":
            return record_id
    return ""


def payload_refs(value: object) -> tuple[str, ...]:
    if value in (None, (), []):
        return ()
    if not isinstance(value, (list, tuple)):
        raise TypeError("record refs must be a list or tuple")
    return unique_refs(*(canonical_typed_ref(item)[0] for item in value))


def families_for_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({canonical_typed_ref(ref)[1].family for ref in refs}))


def unique_refs(*refs: str) -> tuple[str, ...]:
    return tuple(sorted({canonical_typed_ref(ref)[0] for ref in refs if str(ref).strip()}))


def workspace_identity(ws: WorkspacePaths) -> str:
    return os.path.normcase(str(ws.base.resolve()))


def read_repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="research-moment-controller",
            host="aitp",
        ),
    )


def required_payload_text(payload: Mapping[str, Any], field: str) -> str:
    text = " ".join(str(payload.get(field) or "").split())
    if not text:
        raise ValueError(f"{field} must be non-empty")
    return text


def mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    return value


def pinned_record_ref(value: object) -> PinnedRecordRef:
    raw = mapping(value, "pinned record ref")
    return PinnedRecordRef(
        record_ref=str(raw.get("record_ref") or ""),
        content_hash=str(raw.get("content_hash") or ""),
        revision=int(raw.get("revision") or 0),
    )


def _bind_scope_argument(args: dict[str, Any], field: str, expected: str) -> None:
    supplied = str(args.get(field) or "").strip()
    if supplied and supplied != expected:
        raise ValueError(f"capture {field} does not match event scope")
    args[field] = expected


def _finite_json_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be an object")
    try:
        encoded = json.dumps(
            dict(value),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain finite JSON values") from exc
    return decoded


def _bounded_int(value: object, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return parsed
