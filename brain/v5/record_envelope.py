"""Compatibility envelope and canonical hashing for AITP records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from brain.v5.markdown import read_md
from brain.v5.record_family_registry import RecordFamilySpec, record_family_specs


_ACTOR_TYPES = {"human", "model", "tool", "migration"}
_TRUST_EFFECTS = {"none", "candidate_only", "trust_path_input"}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RecordActor:
    actor_type: str
    actor_id: str
    host: str


@dataclass(frozen=True)
class RecordEnvelope:
    record_id: str
    record_family: str
    schema_version: str
    created_at: str
    created_by: RecordActor
    content_hash: str
    trust_effect: str
    session_id: str = ""
    topic_id: str = ""
    program_id: str = ""
    scope_refs: tuple[str, ...] = ()
    source_record_refs: tuple[str, ...] = ()
    revision: int = 1
    lifecycle_status: str = "active"
    supersedes: tuple[str, ...] = ()
    creation_time_source: str = "record"
    record_id_source: str = "canonical_field"
    compatibility_sources: tuple[str, ...] = ()


class EnvelopeValidationError(ValueError):
    """Raised when a record envelope violates the kernel metadata contract."""

    def __init__(self, errors: tuple[str, ...]):
        self.errors = errors
        super().__init__("; ".join(errors))


def canonical_record_hash(frontmatter: Mapping[str, Any], body: str) -> str:
    """Return a stable SHA-256 over all payload fields except the hash itself."""

    payload = {str(key): value for key, value in frontmatter.items() if key != "content_hash"}
    normalized = _json_compatible(payload)
    serialized = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    normalized_body = str(body or "").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(f"{serialized}\n---body---\n{normalized_body}".encode("utf-8")).hexdigest()


def envelope_for_record(
    record: Any,
    *,
    family: str,
    actor: RecordActor | Mapping[str, Any],
    timestamp: str | None = None,
    body: str = "",
    source_record_refs: list[str] | tuple[str, ...] | None = None,
) -> RecordEnvelope:
    """Build and validate an envelope for a new canonical record payload."""

    specs = record_family_specs()
    if family not in specs:
        raise ValueError(f"unknown AITP record family: {family}")
    spec = specs[family]
    frontmatter = asdict(record) if is_dataclass(record) else dict(record)
    created_at = str(timestamp or frontmatter.get("created_at") or "").strip()
    time_source = "explicit" if timestamp else "record"
    if not created_at:
        created_at = datetime.now(timezone.utc).isoformat()
        time_source = "generated_utc"
    envelope = RecordEnvelope(
        record_id=str(frontmatter.get(spec.id_field) or ""),
        record_family=family,
        schema_version=str(frontmatter.get("schema_version") or spec.schema_version),
        created_at=created_at,
        created_by=_actor_from_value(actor),
        content_hash=canonical_record_hash(frontmatter, body),
        trust_effect=str(frontmatter.get("trust_effect") or spec.trust_effect),
        session_id=str(frontmatter.get("session_id") or ""),
        topic_id=str(frontmatter.get("topic_id") or ""),
        program_id=str(frontmatter.get("program_id") or ""),
        scope_refs=_scope_refs(frontmatter, own_id_field=spec.id_field),
        source_record_refs=_merge_string_tuples(
            frontmatter.get("source_record_refs"), source_record_refs
        ),
        revision=_revision_value(frontmatter.get("revision")),
        lifecycle_status=str(frontmatter.get("lifecycle_status") or "active"),
        supersedes=_string_tuple(frontmatter.get("supersedes")),
        creation_time_source=time_source,
        record_id_source=f"canonical_field:{spec.id_field}",
    )
    errors = validate_record_envelope(envelope)
    if errors:
        raise EnvelopeValidationError(errors)
    return envelope


def validate_record_envelope(envelope: RecordEnvelope) -> tuple[str, ...]:
    """Return stable field-qualified errors for a record envelope."""

    errors: list[str] = []
    if not envelope.record_id:
        errors.append("record_id must be non-empty")
    if envelope.record_family not in record_family_specs():
        errors.append("record_family must be registered")
    if not envelope.schema_version:
        errors.append("schema_version must be non-empty")
    if not envelope.created_at:
        errors.append("created_at must be non-empty")
    if envelope.created_by.actor_type not in _ACTOR_TYPES:
        errors.append("created_by.actor_type must be human, model, tool, or migration")
    if not envelope.created_by.actor_id:
        errors.append("created_by.actor_id must be non-empty")
    if not envelope.created_by.host:
        errors.append("created_by.host must be non-empty")
    if not _SHA256_RE.fullmatch(envelope.content_hash):
        errors.append("content_hash must be a lowercase SHA-256 hex digest")
    if not isinstance(envelope.revision, int) or isinstance(envelope.revision, bool) or envelope.revision < 1:
        errors.append("revision must be a positive integer")
    if envelope.trust_effect not in _TRUST_EFFECTS:
        errors.append("trust_effect must be none, candidate_only, or trust_path_input")
    if not envelope.lifecycle_status:
        errors.append("lifecycle_status must be non-empty")
    for field_name, refs in (
        ("scope_refs", envelope.scope_refs),
        ("source_record_refs", envelope.source_record_refs),
        ("supersedes", envelope.supersedes),
        ("compatibility_sources", envelope.compatibility_sources),
    ):
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"{field_name} must contain non-empty strings")
    return tuple(errors)


def read_envelope_compat(
    frontmatter: Mapping[str, Any],
    family_spec: RecordFamilySpec,
    path: str | Path,
    *,
    body: str | None = None,
) -> RecordEnvelope:
    """Derive a non-writing envelope for a schema-v1 or envelope-aware record."""

    record_path = Path(path)
    resolved_body = body
    if resolved_body is None and record_path.exists():
        _stored_frontmatter, resolved_body = read_md(record_path)
    created_at, time_source = _compat_created_at(frontmatter, record_path)
    actor = _actor_from_value(frontmatter.get("created_by"))
    record_id, record_id_source = _compat_record_id(frontmatter, family_spec)
    topic_id, topic_id_source = _compat_string(frontmatter, "topic_id", "topic")
    compatibility_sources = []
    if record_id_source.startswith("legacy_field:"):
        compatibility_sources.append(f"record_id:{record_id_source}")
    if topic_id_source.startswith("legacy_field:"):
        compatibility_sources.append(f"topic_id:{topic_id_source}")
    envelope = RecordEnvelope(
        record_id=record_id,
        record_family=family_spec.family,
        schema_version=str(frontmatter.get("schema_version") or "v1-compat"),
        created_at=created_at,
        created_by=actor,
        content_hash=canonical_record_hash(frontmatter, resolved_body or ""),
        trust_effect=str(frontmatter.get("trust_effect") or family_spec.trust_effect),
        session_id=str(frontmatter.get("session_id") or ""),
        topic_id=topic_id,
        program_id=str(frontmatter.get("program_id") or ""),
        scope_refs=_scope_refs(
            frontmatter,
            own_id_field=family_spec.id_field,
            topic_id=topic_id,
        ),
        source_record_refs=_string_tuple(frontmatter.get("source_record_refs")),
        revision=_revision_value(frontmatter.get("revision")),
        lifecycle_status=str(frontmatter.get("lifecycle_status") or "active"),
        supersedes=_string_tuple(frontmatter.get("supersedes")),
        creation_time_source=time_source,
        record_id_source=record_id_source,
        compatibility_sources=tuple(compatibility_sources),
    )
    errors = validate_record_envelope(envelope)
    if errors:
        raise EnvelopeValidationError(errors)
    return envelope


def _compat_created_at(frontmatter: Mapping[str, Any], path: Path) -> tuple[str, str]:
    created_at = str(frontmatter.get("created_at") or "").strip()
    if created_at:
        return created_at, "record"
    if path.exists():
        timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return timestamp.isoformat(), "file_mtime_fallback"
    return "unknown", "missing_path"


def _compat_record_id(
    frontmatter: Mapping[str, Any],
    family_spec: RecordFamilySpec,
) -> tuple[str, str]:
    canonical = str(frontmatter.get(family_spec.id_field) or "").strip()
    if canonical:
        return canonical, f"canonical_field:{family_spec.id_field}"
    for field in family_spec.legacy_id_fields:
        value = str(frontmatter.get(field) or "").strip()
        if value:
            return value, f"legacy_field:{field}"
    return "", "missing"


def _compat_string(
    frontmatter: Mapping[str, Any],
    canonical_field: str,
    *legacy_fields: str,
) -> tuple[str, str]:
    for field in (canonical_field, *legacy_fields):
        value = str(frontmatter.get(field) or "").strip()
        if value:
            source = "canonical_field" if field == canonical_field else "legacy_field"
            return value, f"{source}:{field}"
    return "", "missing"


def _actor_from_value(value: Any) -> RecordActor:
    if isinstance(value, RecordActor):
        return value
    if isinstance(value, Mapping):
        return RecordActor(
            actor_type=str(value.get("actor_type") or ""),
            actor_id=str(value.get("actor_id") or ""),
            host=str(value.get("host") or ""),
        )
    return RecordActor(actor_type="migration", actor_id="v1-compat", host="migration")


def _scope_refs(
    frontmatter: Mapping[str, Any],
    *,
    own_id_field: str = "",
    topic_id: str = "",
) -> tuple[str, ...]:
    refs = set(_string_tuple(frontmatter.get("scope_refs")))
    if topic_id:
        refs.add(f"topic:{topic_id}")
    for field, prefix in (("topic_id", "topic"), ("claim_id", "claim"), ("session_id", "session")):
        if field == own_id_field:
            continue
        value = str(frontmatter.get(field) or "").strip()
        if value:
            refs.add(f"{prefix}:{value}")
    return tuple(sorted(refs))


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    items = value if isinstance(value, (list, tuple, set, frozenset)) else [value]
    return tuple(str(item).strip() for item in items if str(item).strip())


def _merge_string_tuples(*values: Any) -> tuple[str, ...]:
    merged: set[str] = set()
    for value in values:
        merged.update(_string_tuple(value))
    return tuple(sorted(merged))


def _revision_value(value: Any) -> int:
    if value is None or value == "":
        return 1
    if isinstance(value, bool):
        raise EnvelopeValidationError(("revision must be a positive integer",))
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.isdigit():
        parsed = int(value)
    else:
        raise EnvelopeValidationError(("revision must be a positive integer",))
    if parsed < 1:
        raise EnvelopeValidationError(("revision must be a positive integer",))
    return parsed


def _json_compatible(value: Any) -> Any:
    if is_dataclass(value):
        return _json_compatible(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_compatible(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_json_compatible(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Enum):
        return _json_compatible(value.value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"record payload contains non-JSON-compatible value: {type(value).__name__}")
