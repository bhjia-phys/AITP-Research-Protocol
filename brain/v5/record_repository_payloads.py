"""Pure payload normalization helpers for the canonical record repository."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping

from brain.v5.legacy_record_materialization import materialize_record_class
from brain.v5.record_family_registry import RecordFamilySpec


def _frontmatter(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("record must be a dataclass or mapping")


def _persisted_frontmatter(
    frontmatter: Mapping[str, Any],
    envelope: Any,
    *,
    revision: int = 1,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    persisted = dict(frontmatter)
    persisted.update(
        {
            "record_id": envelope.record_id,
            "record_family": envelope.record_family,
            "schema_version": envelope.schema_version,
            "created_at": envelope.created_at,
            "created_by": asdict(envelope.created_by),
            "record_content_hash": envelope.content_hash,
            "revision": revision,
            "lifecycle_status": envelope.lifecycle_status,
            "supersedes": list(supersedes or envelope.supersedes),
            "trust_effect": envelope.trust_effect,
        }
    )
    return persisted


def _positive_revision(value: Any) -> int:
    if isinstance(value, bool):
        return 1
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit() and int(value) > 0:
        return int(value)
    return 1


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set, frozenset)) else [value]
    return [str(item).strip() for item in items if str(item).strip()]


def _materialize_record(
    frontmatter: Mapping[str, Any],
    spec: RecordFamilySpec,
    *,
    allow_legacy: bool = True,
) -> Any:
    if spec.record_class is None:
        return dict(frontmatter)
    return materialize_record_class(
        frontmatter,
        spec.record_class,
        id_field=spec.id_field,
        legacy_id_fields=spec.legacy_id_fields,
        allow_legacy=allow_legacy,
    )


def _validate_payload_schema(frontmatter: Mapping[str, Any], spec: RecordFamilySpec) -> None:
    kind = str(frontmatter.get("kind") or "").strip()
    if kind and kind != spec.record_kind:
        raise ValueError(
            f"record kind {kind!r} does not match family {spec.family!r}"
        )
    _materialize_record(frontmatter, spec, allow_legacy=False)
