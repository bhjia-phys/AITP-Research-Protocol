"""Input normalization for exact evidence basis references."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from brain.v5.pinned_record_refs import PinnedRecordRef


def coerce_pinned_record_refs(
    values: Sequence[Mapping[str, Any]] | None,
    *,
    field_name: str,
) -> list[PinnedRecordRef] | None:
    if values is None:
        return None
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a list of exact pin objects")

    pins: list[PinnedRecordRef] = []
    for index, value in enumerate(values):
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name}[{index}] must be an exact pin object")
        record_ref = str(value.get("record_ref") or "").strip()
        content_hash = str(value.get("content_hash") or "").strip()
        raw_revision = value.get("revision")
        if isinstance(raw_revision, bool) or not isinstance(raw_revision, int):
            raise ValueError(f"{field_name}[{index}].revision must be an integer")
        revision = raw_revision
        if not record_ref or not content_hash or revision < 1:
            raise ValueError(
                f"{field_name}[{index}] requires record_ref, content_hash, and revision >= 1"
            )
        pins.append(
            PinnedRecordRef(
                record_ref=record_ref,
                content_hash=content_hash,
                revision=revision,
            )
        )
    return pins


def load_pinned_record_refs_file(path: str, *, field_name: str) -> list[PinnedRecordRef] | None:
    if not str(path or "").strip():
        return None
    source = Path(path).expanduser()
    try:
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"could not read {field_name} file {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {field_name} file {source}: {exc}") from exc
    if not isinstance(payload, list):
        raise ValueError(f"{field_name} file must contain a JSON array")
    return coerce_pinned_record_refs(payload, field_name=field_name)
