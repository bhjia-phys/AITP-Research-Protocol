"""Pure contracts for trust-neutral runtime recording candidates."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from brain.v5.research_scope_contracts import canonical_typed_ref


ACCEPTED_CANDIDATE_KINDS = frozenset(
    {
        "definition",
        "formula",
        "convention",
        "relation",
        "derivation",
        "interpretation",
        "analogy",
        "conjecture",
        "failed_route",
        "counterexample",
        "bridge",
        "open_direction",
        "workflow_candidate",
    }
)
CANDIDATE_STATUSES = frozenset(
    {"staged", "rejected", "expired", "included", "superseded"}
)
STAGING_SCHEMA_VERSION = "v1"


class RecordingBatchError(RuntimeError):
    """Raised when a candidate cannot cross the review-batch boundary."""


@dataclass(frozen=True)
class StagedCandidate:
    staging_id: str
    session_id: str
    topic_id: str
    candidate_kind: str
    semantic_key: str
    summary: str
    payload: dict[str, Any]
    source_refs: tuple[str, ...]
    source_event_refs: tuple[str, ...]
    missing_prerequisites: tuple[str, ...]
    dedup_key: str
    created_at: str
    expires_at: str
    status: str = "staged"
    supersedes: tuple[str, ...] = ()
    rejection_reason: str = ""
    trust_effect: str = "none"
    can_update_claim_trust: bool = False

    def __post_init__(self) -> None:
        if self.trust_effect != "none":
            raise ValueError("trust_effect must be none")
        if self.can_update_claim_trust is not False:
            raise ValueError("can_update_claim_trust must be false")


@dataclass(frozen=True)
class StagingDiagnostic:
    path: str
    error_type: str
    message: str


@dataclass(frozen=True)
class StagingInventory:
    candidates: tuple[StagedCandidate, ...]
    corrupt: tuple[StagingDiagnostic, ...]


def normalize_staged_candidate(
    candidate: StagedCandidate,
    *,
    now: datetime | None = None,
    existing: StagedCandidate | None = None,
) -> StagedCandidate:
    """Return one deterministic candidate identity and normalized payload."""

    if not isinstance(candidate, StagedCandidate):
        raise TypeError("candidate must be a StagedCandidate")
    session_id = _required_text(candidate.session_id, "session_id")
    topic_id = _required_text(candidate.topic_id, "topic_id")
    kind = _required_text(candidate.candidate_kind, "candidate_kind")
    if kind not in ACCEPTED_CANDIDATE_KINDS:
        raise ValueError(f"unsupported candidate_kind: {kind}")
    semantic_key = _required_text(candidate.semantic_key, "semantic_key").casefold()
    summary = _required_text(candidate.summary, "summary")
    payload = _json_object(candidate.payload)
    source_refs = normalize_source_refs(candidate.source_refs)
    if not source_refs:
        raise ValueError("source_refs must contain at least one typed ref")
    source_event_refs = _normalized_strings(
        candidate.source_event_refs, "source_event_refs"
    )
    missing = _normalized_strings(
        candidate.missing_prerequisites, "missing_prerequisites"
    )
    status = _required_text(candidate.status, "status")
    if status not in CANDIDATE_STATUSES:
        raise ValueError(f"unsupported candidate status: {status}")
    supersedes = _normalized_strings(candidate.supersedes, "supersedes")
    rejection_reason = _collapsed(candidate.rejection_reason)
    if status == "rejected" and not rejection_reason:
        raise ValueError("rejected candidates require rejection_reason")

    clock = now or datetime.now(timezone.utc)
    created_at = normalize_timestamp(
        candidate.created_at or (existing.created_at if existing else ""),
        "created_at",
        default=clock,
    )
    expires_at = normalize_timestamp(
        candidate.expires_at or (existing.expires_at if existing else ""),
        "expires_at",
        default=_parse_timestamp(created_at, "created_at") + timedelta(days=7),
    )
    normalized = replace(
        candidate,
        staging_id="",
        session_id=session_id,
        topic_id=topic_id,
        candidate_kind=kind,
        semantic_key=semantic_key,
        summary=summary,
        payload=payload,
        source_refs=source_refs,
        source_event_refs=source_event_refs,
        missing_prerequisites=missing,
        dedup_key="",
        created_at=created_at,
        expires_at=expires_at,
        status=status,
        supersedes=supersedes,
        rejection_reason=rejection_reason,
        trust_effect="none",
        can_update_claim_trust=False,
    )
    dedup_key = candidate_dedup_key(normalized)
    staging_id = deterministic_staging_id(normalized)
    if candidate.dedup_key and candidate.dedup_key != dedup_key:
        raise ValueError("candidate dedup_key does not match normalized identity")
    if candidate.staging_id and candidate.staging_id != staging_id:
        raise ValueError("candidate staging_id does not match normalized content")
    return replace(normalized, staging_id=staging_id, dedup_key=dedup_key)


def normalize_source_refs(refs: object) -> tuple[str, ...]:
    values = _string_items(refs, "source_refs")
    canonical = [canonical_typed_ref(value)[0] for value in values]
    return tuple(sorted(set(canonical)))


def candidate_dedup_key(candidate: StagedCandidate) -> str:
    payload = {
        "session_id": candidate.session_id,
        "topic_id": candidate.topic_id,
        "semantic_key": candidate.semantic_key,
        "source_refs": list(candidate.source_refs),
    }
    return _sha256(payload)


def deterministic_staging_id(candidate: StagedCandidate) -> str:
    payload = {
        "session_id": candidate.session_id,
        "topic_id": candidate.topic_id,
        "candidate_kind": candidate.candidate_kind,
        "semantic_key": candidate.semantic_key,
        "summary": candidate.summary,
        "payload": candidate.payload,
        "source_refs": list(candidate.source_refs),
        "source_event_refs": list(candidate.source_event_refs),
        "missing_prerequisites": list(candidate.missing_prerequisites),
    }
    return f"staged-{_sha256(payload)[:24]}"


def deterministic_batch_id(session_id: str, milestone_id: str) -> str:
    return f"recording-batch-{_sha256({'session_id': session_id, 'milestone_id': milestone_id})[:24]}"


def serialize_staged_candidate(candidate: StagedCandidate) -> str:
    payload = {
        "schema_version": STAGING_SCHEMA_VERSION,
        "content_fingerprint": candidate_storage_fingerprint(candidate),
        "candidate": asdict(candidate),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def deserialize_staged_candidate(path: Path) -> StagedCandidate:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise TypeError("staging document must be an object")
    if payload.get("schema_version") != STAGING_SCHEMA_VERSION:
        raise ValueError("unsupported staging schema_version")
    raw = payload.get("candidate")
    if not isinstance(raw, Mapping):
        raise TypeError("staging candidate must be an object")
    values = dict(raw)
    for field_name in (
        "source_refs",
        "source_event_refs",
        "missing_prerequisites",
        "supersedes",
    ):
        values[field_name] = tuple(values.get(field_name) or ())
    candidate = StagedCandidate(**values)
    normalized = normalize_staged_candidate(candidate)
    if candidate != normalized:
        raise ValueError("staging candidate is not normalized")
    declared = str(payload.get("content_fingerprint") or "")
    if declared != candidate_storage_fingerprint(candidate):
        raise ValueError("staging content fingerprint mismatch")
    if path.stem != candidate.dedup_key:
        raise ValueError("staging filename does not match candidate dedup_key")
    return candidate


def candidate_storage_fingerprint(candidate: StagedCandidate) -> str:
    return _sha256(asdict(candidate))


def normalize_timestamp(
    value: str,
    label: str,
    *,
    default: datetime | None = None,
) -> str:
    text = str(value or "").strip()
    parsed = _parse_timestamp(text, label) if text else default
    if parsed is None:
        raise ValueError(f"{label} must be non-empty")
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def is_expired(candidate: StagedCandidate, *, now: datetime | None = None) -> bool:
    clock = now or datetime.now(timezone.utc)
    return _parse_timestamp(candidate.expires_at, "expires_at") <= clock


def _parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed


def _required_text(value: object, label: str) -> str:
    text = _collapsed(value)
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _collapsed(value: object) -> str:
    return " ".join(str(value or "").split())


def _string_items(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list or tuple")
    items = tuple(_required_text(item, label) for item in value)
    return items


def _normalized_strings(value: object, label: str) -> tuple[str, ...]:
    return tuple(sorted(set(_string_items(value, label))))


def _json_object(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("payload must be an object")
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
        decoded = json.loads(encoded)
    except (TypeError, ValueError) as exc:
        raise ValueError("payload must be finite JSON data") from exc
    if not isinstance(decoded, dict):
        raise TypeError("payload must be an object")
    return decoded


def _sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
