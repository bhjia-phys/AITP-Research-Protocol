"""Read-only session recovery helpers for AITP v5 surfaces."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from brain.v5.models import SessionBinding
from brain.v5.workspace import get_session_binding

_TOPIC_TOKEN_PREFIXES = ("topic:", "aitp:topic:")
_SAFE_TOPIC_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,160}$")


@dataclass(frozen=True)
class RecoveredSessionBinding:
    session: SessionBinding
    requested_session_id: str
    recovery_selection_source: str


def recover_session_binding_for_read(ws, session_id: str) -> RecoveredSessionBinding:
    """Resolve a session or topic token for read-only recovery surfaces.

    `topic:<topic-id>` is a virtual session token.  It lets hosts that only know
    the topic ask AITP to recover the current runtime focus from topic_state
    without guessing a concrete session filename.  A bare topic id is accepted
    as the same read-only recovery convenience when it names an existing topic.
    """

    requested_session_id = session_id
    try:
        session = get_session_binding(ws, session_id)
        source = "session_binding"
    except (FileNotFoundError, TypeError, ValueError):
        session, source = _virtual_session_from_recovery_token(ws, session_id)
        if session is None:
            raise

    recovery_session = _fallback_session_from_topic_state(ws, session)
    if recovery_session is not None:
        session = recovery_session
        if source == "session_binding":
            source = "runtime_topic_state"
        elif source == "bare_topic":
            source = "bare_topic_runtime_topic_state"
        else:
            source = "topic_token_runtime_topic_state"
    return RecoveredSessionBinding(
        session=session,
        requested_session_id=requested_session_id,
        recovery_selection_source=source,
    )


def _virtual_session_from_topic_token(ws, session_id: str) -> SessionBinding | None:
    topic_id = _topic_id_from_token(session_id)
    if topic_id is None:
        return None
    return _virtual_session_from_topic_id(ws, session_id=session_id, topic_id=topic_id)


def _virtual_session_from_recovery_token(ws, session_id: str) -> tuple[SessionBinding | None, str]:
    token_session = _virtual_session_from_topic_token(ws, session_id)
    if token_session is not None:
        return token_session, "topic_token"
    topic_session = _virtual_session_from_bare_topic(ws, session_id)
    if topic_session is not None:
        return topic_session, "bare_topic"
    return None, ""


def _virtual_session_from_bare_topic(ws, session_id: str) -> SessionBinding | None:
    topic_id = str(session_id or "").strip()
    if not _SAFE_TOPIC_ID.match(topic_id):
        return None
    return _virtual_session_from_topic_id(ws, session_id=session_id, topic_id=topic_id)


def _virtual_session_from_topic_id(ws, *, session_id: str, topic_id: str) -> SessionBinding | None:
    topic_dir = ws.topic_dir(topic_id)
    if not topic_dir.exists():
        return None
    return SessionBinding(
        session_id=session_id,
        topic_id=topic_id,
        context_id=topic_id,
    )


def _topic_id_from_token(value: str) -> str | None:
    token = str(value or "").strip()
    for prefix in _TOPIC_TOKEN_PREFIXES:
        if token.startswith(prefix):
            topic_id = token[len(prefix):].strip()
            return topic_id if _SAFE_TOPIC_ID.match(topic_id) else None
    return None


def _fallback_session_from_topic_state(ws, session: SessionBinding) -> SessionBinding | None:
    if not session.topic_id:
        return None
    path = ws.topic_dir(session.topic_id) / "runtime" / "topic_state.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("kind") != "topic_state":
        return None
    payload_topic = str(payload.get("topic_id") or "")
    if payload_topic and payload_topic != session.topic_id:
        return None
    focus_claim = str(payload.get("active_claim_id") or "")
    if not focus_claim:
        return None
    focus_session_id = str(payload.get("session_id") or "") or session.session_id
    focus_context_id = str(payload.get("context_id") or "") or session.context_id
    if session.active_claim == focus_claim and session.session_id == focus_session_id:
        return None
    try:
        focus_session = get_session_binding(ws, focus_session_id)
    except (FileNotFoundError, TypeError, ValueError):
        focus_session = None
    if focus_session is not None and focus_session.topic_id == session.topic_id and focus_session.active_claim == focus_claim:
        return focus_session
    return SessionBinding(
        session_id=focus_session_id,
        topic_id=session.topic_id,
        context_id=focus_context_id,
        runtime=session.runtime,
        interaction_profile=session.interaction_profile,
        interaction_steering=session.interaction_steering,
        active_cycle=session.active_cycle,
        active_claim=focus_claim,
        active_route=session.active_route,
        write_scope=list(session.write_scope),
        lock_level=session.lock_level,
    )
