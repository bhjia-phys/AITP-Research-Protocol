"""Host-neutral contracts for bounded research-moment decisions."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Mapping

from brain.v5.record_path_safety import validate_record_id
from brain.v5.research_scope_contracts import canonical_typed_ref


ALLOWED_RESEARCH_EVENT_TYPES = frozenset(
    {
        "ResearchTurnStart",
        "SourceAcquired",
        "CodeStateChanged",
        "ToolRunCompleted",
        "ArtifactProduced",
        "FailureOrGapObserved",
        "RouteChanged",
        "MajorConclusionPending",
        "ExpensiveRunPending",
        "SessionCloseout",
    }
)
RESEARCH_MOMENT_OUTCOMES = frozenset(
    {
        "ignore",
        "auto_capture_process",
        "stage_semantic_candidate",
        "coalesce_for_review",
        "require_checkpoint",
        "block_until_prerequisites",
    }
)
STATE_EFFECTS = frozenset({"read_only", "runtime_write", "kernel_write"})
RECURSIVE_AITP_ORIGINS = frozenset(
    {"aitp_context", "aitp_retrieval", "aitp_recording", "aitp_diagnostic"}
)
MOMENT_SCHEMA_VERSION = "aitp.research_moment.v1"


@dataclass(frozen=True)
class ResearchEvent:
    event_id: str
    event_type: str
    occurred_at: str
    host: str
    host_session_id: str
    session_id: str
    topic_id: str
    subject_refs: tuple[str, ...]
    objective_payload: dict[str, Any]
    semantic_payload: dict[str, Any]
    source_event_id: str
    recursion_origin: str


@dataclass(frozen=True)
class ResearchMomentDecision:
    decision_id: str
    event: ResearchEvent
    outcome: str
    reason_codes: tuple[str, ...]
    target_families: tuple[str, ...]
    minimum_refs: tuple[str, ...]
    dedup_key: str
    expires_at: str
    verification_steps: tuple[str, ...]
    required_checkpoint_action: str
    blocked_action: str
    application_operation: str
    application_payload: dict[str, Any]
    declared_effect: str
    trust_effect: str = "none"
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in RESEARCH_MOMENT_OUTCOMES:
            raise ValueError(f"unsupported research moment outcome: {self.outcome}")
        if self.declared_effect not in STATE_EFFECTS:
            raise ValueError(f"unsupported declared effect: {self.declared_effect}")
        if self.trust_effect != "none":
            raise ValueError("trust_effect must be none")
        if self.can_update_claim_trust is not False:
            raise ValueError("can_update_claim_trust must be false")


@dataclass(frozen=True)
class MomentReceipt:
    receipt_id: str
    decision_id: str
    event_id: str
    outcome: str
    status: str
    application_operation: str
    application_effect: str
    runtime_path: str
    record_refs: tuple[str, ...]
    staging_refs: tuple[str, ...]
    checkpoint_refs: tuple[str, ...]
    handoff: dict[str, Any]
    created_at: str
    trust_effect: str = "none"
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in RESEARCH_MOMENT_OUTCOMES:
            raise ValueError(f"unsupported receipt outcome: {self.outcome}")
        if self.application_effect not in STATE_EFFECTS:
            raise ValueError(f"unsupported application effect: {self.application_effect}")
        if self.trust_effect != "none":
            raise ValueError("trust_effect must be none")
        if self.can_update_claim_trust is not False:
            raise ValueError("can_update_claim_trust must be false")


def normalize_research_event(event: ResearchEvent) -> ResearchEvent:
    """Validate and canonicalize one logical host event without filesystem access."""

    if not isinstance(event, ResearchEvent):
        raise TypeError("event must be a ResearchEvent")
    event_type = _required_text(event.event_type, "event_type")
    if event_type not in ALLOWED_RESEARCH_EVENT_TYPES:
        raise ValueError(f"unsupported research event: {event_type}")
    try:
        refs = tuple(
            sorted(
                {
                    canonical_typed_ref(_required_text(ref, "subject_refs"))[0]
                    for ref in event.subject_refs
                }
            )
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"subject_refs must contain typed refs: {exc}") from exc
    return replace(
        event,
        event_id=_required_text(event.event_id, "event_id"),
        event_type=event_type,
        occurred_at=normalize_timestamp(event.occurred_at, "occurred_at"),
        host=_required_text(event.host, "host").casefold(),
        host_session_id=_required_text(event.host_session_id, "host_session_id"),
        session_id=validate_record_id(_required_text(event.session_id, "session_id")),
        topic_id=validate_record_id(_required_text(event.topic_id, "topic_id")),
        subject_refs=refs,
        objective_payload=_json_object(event.objective_payload, "objective_payload"),
        semantic_payload=_json_object(event.semantic_payload, "semantic_payload"),
        source_event_id=_clean_text(event.source_event_id),
        recursion_origin=_required_text(event.recursion_origin, "recursion_origin").casefold(),
    )


def normalize_decision(decision: ResearchMomentDecision) -> ResearchMomentDecision:
    """Validate a decision before any application side effect."""

    if not isinstance(decision, ResearchMomentDecision):
        raise TypeError("decision must be a ResearchMomentDecision")
    event = normalize_research_event(decision.event)
    refs = _canonical_ref_tuple(decision.minimum_refs, "minimum_refs")
    families = tuple(sorted({_required_text(item, "target_families") for item in decision.target_families}))
    normalized = replace(
        decision,
        decision_id=_required_text(decision.decision_id, "decision_id"),
        event=event,
        reason_codes=_clean_tuple(decision.reason_codes, "reason_codes"),
        target_families=families,
        minimum_refs=refs,
        dedup_key=_required_text(decision.dedup_key, "dedup_key"),
        expires_at=normalize_timestamp(decision.expires_at, "expires_at"),
        verification_steps=_clean_tuple(decision.verification_steps, "verification_steps"),
        required_checkpoint_action=_clean_text(decision.required_checkpoint_action),
        blocked_action=_clean_text(decision.blocked_action),
        application_operation=_clean_text(decision.application_operation),
        application_payload=_json_object(decision.application_payload, "application_payload"),
        trust_effect="none",
        can_update_claim_trust=False,
    )
    if normalized.outcome == "require_checkpoint" and not normalized.required_checkpoint_action:
        raise ValueError("checkpoint decisions require required_checkpoint_action")
    if normalized.outcome == "block_until_prerequisites" and not normalized.blocked_action:
        raise ValueError("blocked decisions require blocked_action")
    return normalized


def decision_fingerprint(
    workspace_identity: str,
    event: ResearchEvent,
    *,
    outcome: str,
    application_operation: str,
    reason_codes: tuple[str, ...] = (),
    target_families: tuple[str, ...] = (),
    minimum_refs: tuple[str, ...] = (),
    expires_at: str = "",
    verification_steps: tuple[str, ...] = (),
    required_checkpoint_action: str = "",
    blocked_action: str = "",
    application_payload: Mapping[str, Any] | None = None,
    declared_effect: str = "read_only",
) -> str:
    return _sha256(
        {
            "workspace_identity": _required_text(workspace_identity, "workspace_identity"),
            "event": asdict(normalize_research_event(event)),
            "outcome": outcome,
            "reason_codes": list(reason_codes),
            "target_families": list(target_families),
            "minimum_refs": list(minimum_refs),
            "expires_at": expires_at,
            "verification_steps": list(verification_steps),
            "required_checkpoint_action": required_checkpoint_action,
            "blocked_action": blocked_action,
            "application_operation": application_operation,
            "application_payload": dict(application_payload or {}),
            "declared_effect": declared_effect,
        }
    )


def serialize_moment_receipt(receipt: MomentReceipt) -> str:
    payload = {
        "schema_version": MOMENT_SCHEMA_VERSION,
        "receipt": asdict(receipt),
    }
    payload["content_fingerprint"] = _sha256(payload["receipt"])
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + "\n"


def deserialize_moment_receipt(text: str) -> MomentReceipt:
    payload = json.loads(text)
    if not isinstance(payload, Mapping) or payload.get("schema_version") != MOMENT_SCHEMA_VERSION:
        raise ValueError("unsupported research moment receipt schema")
    raw = payload.get("receipt")
    if not isinstance(raw, Mapping):
        raise ValueError("research moment receipt must be an object")
    if payload.get("content_fingerprint") != _sha256(raw):
        raise ValueError("research moment receipt fingerprint mismatch")
    values = dict(raw)
    for field in ("record_refs", "staging_refs", "checkpoint_refs"):
        values[field] = tuple(values.get(field) or ())
    receipt = MomentReceipt(**values)
    if serialize_moment_receipt(receipt) != text:
        raise ValueError("research moment receipt is not canonical")
    return receipt


def normalize_timestamp(value: object, label: str) -> str:
    text = _required_text(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _canonical_ref_tuple(values: object, label: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    try:
        return tuple(sorted({canonical_typed_ref(value)[0] for value in values}))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain typed refs: {exc}") from exc


def _json_object(value: object, label: str) -> dict[str, Any]:
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
    if not isinstance(decoded, dict):
        raise TypeError(f"{label} must be an object")
    return decoded


def _clean_tuple(values: object, label: str) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    return tuple(sorted({_required_text(item, label) for item in values}))


def _clean_text(value: object) -> str:
    return unicodedata.normalize("NFC", " ".join(str(value or "").split()))


def _required_text(value: object, label: str) -> str:
    text = _clean_text(value)
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "ALLOWED_RESEARCH_EVENT_TYPES",
    "MOMENT_SCHEMA_VERSION",
    "MomentReceipt",
    "RECURSIVE_AITP_ORIGINS",
    "RESEARCH_MOMENT_OUTCOMES",
    "ResearchEvent",
    "ResearchMomentDecision",
    "decision_fingerprint",
    "deserialize_moment_receipt",
    "normalize_decision",
    "normalize_research_event",
    "serialize_moment_receipt",
]
