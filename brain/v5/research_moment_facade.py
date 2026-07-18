"""One explicit ingress for bounded Research Moment decisions and application."""

from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Mapping

from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor
from brain.v5.research_moment_contracts import ResearchEvent
from brain.v5.research_moments import (
    apply_research_moment_decision,
    decide_research_moment,
)
from brain.v5.workspace import get_session_binding


def process_research_moment_request(
    ws: WorkspacePaths,
    request: Mapping[str, Any],
    *,
    actor: RecordActor,
) -> dict[str, Any]:
    """Decide, and optionally apply, one complete host-neutral research event."""

    if not isinstance(request, Mapping):
        raise TypeError("research moment request must be a mapping")
    apply = request.get("apply", True)
    if not isinstance(apply, bool):
        raise TypeError("research moment apply must be a boolean")
    event_payload = request.get("event")
    if not isinstance(event_payload, Mapping):
        raise TypeError("research moment request.event must be a mapping")
    event = _event_from_mapping(event_payload)
    binding = get_session_binding(ws, event.session_id)
    if event.topic_id != binding.topic_id:
        raise ValueError("research event topic does not match its session binding")

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=actor) if apply else None
    return {
        "ok": True,
        "kind": "research_moment_process_result",
        "applied": apply,
        "state_effect": decision.declared_effect if apply else "read_only",
        "decision": _json_compatible(asdict(decision)),
        "receipt": _json_compatible(asdict(receipt)) if receipt is not None else None,
        "trust_effect": "none",
        "can_update_claim_trust": False,
    }


def research_event_from_mapping(payload: Mapping[str, Any]) -> ResearchEvent:
    """Build one typed event from JSON-compatible data before policy validation."""

    return _event_from_mapping(payload)


def _event_from_mapping(payload: Mapping[str, Any]) -> ResearchEvent:
    required = {
        "event_id",
        "event_type",
        "occurred_at",
        "host",
        "host_session_id",
        "session_id",
        "topic_id",
        "subject_refs",
        "objective_payload",
        "semantic_payload",
        "source_event_id",
        "recursion_origin",
    }
    missing = sorted(required - set(payload))
    extra = sorted(set(payload) - required)
    if missing:
        raise ValueError(f"research event is missing fields: {', '.join(missing)}")
    if extra:
        raise ValueError(f"research event has unsupported fields: {', '.join(extra)}")
    subject_refs = payload["subject_refs"]
    if not isinstance(subject_refs, (list, tuple)):
        raise TypeError("research event subject_refs must be a list or tuple")
    objective = payload["objective_payload"]
    semantic = payload["semantic_payload"]
    if not isinstance(objective, Mapping):
        raise TypeError("research event objective_payload must be a mapping")
    if not isinstance(semantic, Mapping):
        raise TypeError("research event semantic_payload must be a mapping")
    return ResearchEvent(
        event_id=payload["event_id"],
        event_type=payload["event_type"],
        occurred_at=payload["occurred_at"],
        host=payload["host"],
        host_session_id=payload["host_session_id"],
        session_id=payload["session_id"],
        topic_id=payload["topic_id"],
        subject_refs=tuple(subject_refs),
        objective_payload=dict(objective),
        semantic_payload=dict(semantic),
        source_event_id=payload["source_event_id"],
        recursion_origin=payload["recursion_origin"],
    )


def _json_compatible(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, ensure_ascii=True, sort_keys=True))


__all__ = ["process_research_moment_request", "research_event_from_mapping"]
