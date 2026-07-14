"""Trust-neutral orchestration for the v5 research-session lifecycle."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from brain.v5.lifecycle_models import CloseoutBoundaryItem
from brain.v5.mcp_base_resolution import resolve_workspace_base
from brain.v5.paths import WorkspacePaths
from brain.v5.recall_audit import RecallRequest, run_recall_audit
from brain.v5.record_envelope import RecordActor
from brain.v5.recording_batch_contracts import StagedCandidate
from brain.v5.recording_batches import (
    coalesce_recording_batch,
    recording_batch_handoff,
    stage_recording_candidate,
)
from brain.v5.session_lifecycle import (
    SessionCloseoutPlan,
    SessionCloseoutRequest,
    build_session_closeout_plan,
    record_session_closeout,
)
from brain.v5.session_resume import build_session_resume_card


PLAN_SCHEMA_VERSION = "aitp.session_closeout_plan.v1"


class LifecycleFacadeError(RuntimeError):
    """Raised when a lifecycle request cannot cross its declared boundary."""


def lifecycle_workspace(
    base: str | Path,
    *,
    require_index: bool = False,
) -> WorkspacePaths:
    """Resolve an existing workspace without creating any layout."""

    text = str(base or "").strip()
    raw = Path(text).expanduser() if text else Path(".")
    resolved = resolve_workspace_base(text)
    # Explicit paths may resolve to their store parent or nested topics root,
    # but must never fall through to an unrelated AITP_TOPICS_ROOT.
    if text not in {"", "."} and not _paths_related(raw, resolved):
        resolved = raw.parent if raw.name == ".aitp" else raw
    ws = WorkspacePaths(resolved)
    if not ws.root.is_dir():
        raise LifecycleFacadeError(f"AITP workspace does not exist: {ws.root}")
    if require_index and not (ws.root / "indexes" / "manifest.json").is_file():
        raise LifecycleFacadeError(
            f"AITP workspace has no query index: {ws.root / 'indexes' / 'manifest.json'}"
        )
    return ws


def context_transition_receipt(
    session_id: str,
    source_level: str,
    target_level: str,
) -> dict[str, Any]:
    return {
        "kind": "context_transition_receipt",
        "session_id": str(session_id or "").strip(),
        "from_disclosure_level": source_level,
        "to_disclosure_level": target_level,
        "transition": f"{source_level}->{target_level}",
        "automatic_deep_expansion": False,
        "can_update_claim_trust": False,
    }


def start_session(base: str | Path, session_id: str) -> dict[str, Any]:
    ws = lifecycle_workspace(base, require_index=True)
    clean_session = _required_text(session_id, "session_id")
    return {
        "ok": True,
        "kind": "session_start_boundary",
        "session_id": clean_session,
        "disclosure_level": "startup_orientation",
        "resume_card": build_session_resume_card(ws, clean_session),
        "context_receipt": context_transition_receipt(
            clean_session,
            "route_hint",
            "startup_orientation",
        ),
        "write_executed": False,
        "state_effect": "read_only",
        "truth_source": "typed_records_and_query_index",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def persist_recall_audit(
    base: str | Path,
    request: Mapping[str, Any],
    *,
    actor: RecordActor | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ws = lifecycle_workspace(base)
    record = run_recall_audit(
        ws,
        recall_request_from_mapping(request),
        actor=actor_from_mapping(actor, default_actor_id="lifecycle-recall"),
    )
    return {
        "ok": True,
        **asdict(record),
        "kind": "recall_audit_result",
        "audit_ref": f"recall_audit:{record.audit_id}",
        "write_executed": True,
        "state_effect": "kernel_write",
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }


def stage_candidate(
    base: str | Path,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    ws = lifecycle_workspace(base)
    staged = stage_recording_candidate(ws, staged_candidate_from_mapping(candidate))
    return {
        "ok": True,
        "kind": "recording_candidate_staging",
        **asdict(staged),
        "write_executed": True,
        "state_effect": "runtime_write",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def coalesce_candidate_batch(
    base: str | Path,
    session_id: str,
    milestone_id: str,
    *,
    actor: RecordActor | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ws = lifecycle_workspace(base)
    result = coalesce_recording_batch(
        ws,
        _required_text(session_id, "session_id"),
        _required_text(milestone_id, "milestone_id"),
        actor=actor_from_mapping(actor, default_actor_id="lifecycle-recording-batch"),
    )
    return {
        "ok": True,
        **recording_batch_handoff(result),
        "write_executed": True,
        "state_effect": "kernel_write",
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }


def plan_session_closeout(
    base: str | Path,
    request: Mapping[str, Any],
) -> dict[str, Any]:
    ws = lifecycle_workspace(base, require_index=True)
    normalized_request = closeout_request_from_mapping(request)
    plan = build_session_closeout_plan(ws, normalized_request)
    return _closeout_plan_payload(normalized_request, plan)


def apply_session_closeout(
    base: str | Path,
    plan_payload: Mapping[str, Any],
    plan_id: str,
    *,
    actor: RecordActor | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Rebuild and bind an approved plan before crossing the canonical boundary."""

    ws = lifecycle_workspace(base, require_index=True)
    declared = _require_mapping(plan_payload, "plan")
    clean_plan_id = _required_text(plan_id, "plan_id")
    if clean_plan_id != str(declared.get("plan_id") or ""):
        raise LifecycleFacadeError("plan_id does not match the reviewed plan")
    declared_core = _plan_core_from_payload(declared)
    declared_fingerprint = _fingerprint(declared_core)
    if declared_fingerprint != str(declared.get("plan_fingerprint") or ""):
        raise LifecycleFacadeError("plan_id payload fingerprint is invalid")
    if clean_plan_id != _plan_id(declared_fingerprint):
        raise LifecycleFacadeError("plan_id is not bound to the plan fingerprint")

    request = closeout_request_from_mapping(declared_core["request"])
    fresh_plan = build_session_closeout_plan(ws, request)
    fresh_payload = _closeout_plan_payload(request, fresh_plan)
    if fresh_payload["plan_fingerprint"] != declared_fingerprint:
        raise LifecycleFacadeError("plan_id is stale because closeout inputs changed")
    result = record_session_closeout(
        ws,
        fresh_plan,
        actor=actor_from_mapping(actor, default_actor_id="lifecycle-closeout"),
    )
    return {
        "ok": True,
        "kind": "session_closeout_apply",
        "plan_id": clean_plan_id,
        "plan_fingerprint": declared_fingerprint,
        "closeout_ref": result.record_ref,
        "write_status": result.status,
        "content_hash": result.content_hash,
        "write_executed": True,
        "state_effect": "kernel_write",
        "trust_update_forbidden": True,
        "summary_inputs_trusted": False,
        "orientation_only": False,
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }


def actor_from_mapping(
    actor: RecordActor | Mapping[str, Any] | None,
    *,
    default_actor_id: str,
) -> RecordActor:
    if isinstance(actor, RecordActor):
        return actor
    if actor is None:
        return RecordActor(
            actor_type="tool",
            actor_id=default_actor_id,
            host="aitp-v5",
        )
    values = _require_mapping(actor, "actor")
    try:
        return RecordActor(
            actor_type=_required_text(values.get("actor_type"), "actor.actor_type"),
            actor_id=_required_text(values.get("actor_id"), "actor.actor_id"),
            host=_required_text(values.get("host"), "actor.host"),
        )
    except TypeError as exc:
        raise LifecycleFacadeError(f"invalid actor: {exc}") from exc


def recall_request_from_mapping(value: Mapping[str, Any]) -> RecallRequest:
    raw = _require_mapping(value, "request")
    return RecallRequest(
        session_id=str(raw.get("session_id") or ""),
        query_text=str(raw.get("query_text") or ""),
        normalized_intent=str(raw.get("normalized_intent") or ""),
        required_families=_string_tuple(raw.get("required_families", ()), "required_families"),
        exact_refs=_string_tuple(raw.get("exact_refs", ()), "exact_refs"),
        focus_set_ref=str(raw.get("focus_set_ref") or ""),
        include_program_scope=raw.get("include_program_scope", True),
        include_discovery=raw.get("include_discovery", False),
        top_k=raw.get("top_k", 20),
    )


def staged_candidate_from_mapping(value: Mapping[str, Any]) -> StagedCandidate:
    raw = _require_mapping(value, "candidate")
    payload = _require_mapping(raw.get("payload", {}), "candidate.payload")
    return StagedCandidate(
        staging_id=str(raw.get("staging_id") or ""),
        session_id=str(raw.get("session_id") or ""),
        topic_id=str(raw.get("topic_id") or ""),
        candidate_kind=str(raw.get("candidate_kind") or ""),
        semantic_key=str(raw.get("semantic_key") or ""),
        summary=str(raw.get("summary") or ""),
        payload=dict(payload),
        source_refs=_string_tuple(raw.get("source_refs", ()), "source_refs"),
        source_event_refs=_string_tuple(
            raw.get("source_event_refs", ()), "source_event_refs"
        ),
        missing_prerequisites=_string_tuple(
            raw.get("missing_prerequisites", ()), "missing_prerequisites"
        ),
        dedup_key=str(raw.get("dedup_key") or ""),
        created_at=str(raw.get("created_at") or ""),
        expires_at=str(raw.get("expires_at") or ""),
        status=str(raw.get("status") or "staged"),
        supersedes=_string_tuple(raw.get("supersedes", ()), "supersedes"),
        rejection_reason=str(raw.get("rejection_reason") or ""),
        trust_effect=str(raw.get("trust_effect") or "none"),
        can_update_claim_trust=raw.get("can_update_claim_trust", False),
    )


def closeout_request_from_mapping(value: Mapping[str, Any]) -> SessionCloseoutRequest:
    raw = _require_mapping(value, "request")
    return SessionCloseoutRequest(
        session_id=str(raw.get("session_id") or ""),
        milestone_id=str(raw.get("milestone_id") or ""),
        completed_work=_string_tuple(raw.get("completed_work", ()), "completed_work"),
        can_say=_boundary_tuple(raw.get("can_say", ()), "can_say"),
        cannot_say=_boundary_tuple(raw.get("cannot_say", ()), "cannot_say"),
        open_gaps=_boundary_tuple(raw.get("open_gaps", ()), "open_gaps"),
        failed_routes=_boundary_tuple(raw.get("failed_routes", ()), "failed_routes"),
        next_actions=_string_tuple(raw.get("next_actions", ()), "next_actions"),
        source_record_refs=_string_tuple(
            raw.get("source_record_refs", ()), "source_record_refs"
        ),
        pending_candidate_batch_refs=_string_tuple(
            raw.get("pending_candidate_batch_refs", ()),
            "pending_candidate_batch_refs",
        ),
        reusable_workflow_candidate_refs=_string_tuple(
            raw.get("reusable_workflow_candidate_refs", ()),
            "reusable_workflow_candidate_refs",
        ),
    )


def _closeout_plan_payload(
    request: SessionCloseoutRequest,
    plan: SessionCloseoutPlan,
) -> dict[str, Any]:
    core = {
        "request": _json_value(asdict(request)),
        "record": _json_value(asdict(plan.record)),
        "missing_requirements": list(plan.missing_requirements),
        "unresolved_refs": list(plan.unresolved_refs),
        "allowed": plan.allowed,
        "can_update_claim_trust": False,
    }
    fingerprint = _fingerprint(core)
    return {
        "ok": True,
        "kind": "session_closeout_plan",
        "schema_version": PLAN_SCHEMA_VERSION,
        **core,
        "plan_id": _plan_id(fingerprint),
        "plan_fingerprint": fingerprint,
        "write_executed": False,
        "state_effect": "read_only",
        "human_review_required": True,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
    }


def _plan_core_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise LifecycleFacadeError("unsupported closeout plan schema_version")
    return {
        "request": _json_value(_require_mapping(payload.get("request"), "plan.request")),
        "record": _json_value(_require_mapping(payload.get("record"), "plan.record")),
        "missing_requirements": list(
            _string_tuple(payload.get("missing_requirements", ()), "missing_requirements")
        ),
        "unresolved_refs": list(
            _string_tuple(payload.get("unresolved_refs", ()), "unresolved_refs")
        ),
        "allowed": payload.get("allowed"),
        "can_update_claim_trust": payload.get("can_update_claim_trust"),
    }


def _boundary_tuple(value: Any, label: str) -> tuple[CloseoutBoundaryItem, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    items: list[CloseoutBoundaryItem] = []
    for item in value:
        if isinstance(item, CloseoutBoundaryItem):
            items.append(item)
        else:
            items.append(CloseoutBoundaryItem(**dict(_require_mapping(item, label))))
    return tuple(items)


def _string_tuple(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    return tuple(str(item) for item in value)


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    return dict(value)


def _required_text(value: Any, label: str) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _json_value(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False))


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan_id(fingerprint: str) -> str:
    return f"closeout-plan-{fingerprint[:24]}"


def _paths_related(left: Path, right: Path) -> bool:
    try:
        left_resolved = left.resolve()
        right_resolved = right.resolve()
    except OSError:
        left_resolved = left.absolute()
        right_resolved = right.absolute()
    return (
        left_resolved == right_resolved
        or left_resolved in right_resolved.parents
        or right_resolved in left_resolved.parents
    )
