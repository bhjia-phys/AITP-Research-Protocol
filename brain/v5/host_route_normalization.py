"""Small deterministic normalizers shared by host route contracts."""

from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Mapping

from brain.v5.record_path_safety import validate_record_id
from brain.v5.research_scope_contracts import canonical_typed_ref


def clean_text(
    value: object,
    label: str,
    *,
    max_bytes: int = 1024,
    required: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    cleaned = value.strip()
    if required and not cleaned:
        raise ValueError(f"{label} is required")
    if "\x00" in cleaned:
        raise ValueError(f"{label} must not contain NUL")
    if len(cleaned.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} must be at most {max_bytes} UTF-8 bytes")
    return cleaned


def record_id(value: object, label: str) -> str:
    cleaned = clean_text(value, label, max_bytes=512)
    return validate_record_id(cleaned) if cleaned else ""


def record_id_tuple(
    values: object,
    label: str,
    *,
    max_items: int,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{label} must be a tuple or list")
    if len(values) > max_items:
        raise ValueError(f"{label} must contain at most {max_items} items")
    cleaned = {record_id(value, label) for value in values}
    cleaned.discard("")
    return tuple(sorted(cleaned))


def bounded_text_tuple(
    values: object,
    label: str,
    *,
    max_items: int,
    max_item_bytes: int,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{label} must be a tuple or list")
    if len(values) > max_items:
        raise ValueError(f"{label} must contain at most {max_items} items")
    cleaned = {
        clean_text(value, label, max_bytes=max_item_bytes) for value in values
    }
    cleaned.discard("")
    return tuple(sorted(cleaned))


def typed_ref_tuple(
    values: object,
    label: str,
    *,
    max_items: int,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{label} must be a tuple or list")
    if len(values) > max_items:
        raise ValueError(f"{label} must contain at most {max_items} items")
    return tuple(sorted({canonical_typed_ref(str(value))[0] for value in values}))


def freeze_json_object(
    value: object,
    label: str,
    *,
    max_bytes: int,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{label} must be a mapping")
    ready = json_ready(value)
    encoded = json.dumps(
        ready,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    if len(encoded) > max_bytes:
        raise ValueError(f"{label} must be at most {max_bytes} UTF-8 bytes")
    return _freeze_json(ready)


def freeze_component_scores(value: object) -> Mapping[str, int]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError("component_scores must be a non-empty mapping")
    normalized: dict[str, int] = {}
    for raw_key, raw_score in value.items():
        key = clean_text(raw_key, "component_scores key", required=True)
        if not isinstance(raw_score, int) or not 0 <= raw_score <= 1_000_000:
            raise ValueError(
                "component_scores values must be integers between 0 and 1000000"
            )
        normalized[key] = raw_score
    return MappingProxyType(dict(sorted(normalized.items())))


def clean_text_tuple(
    values: object,
    label: str,
    *,
    required: bool,
) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise TypeError(f"{label} must be a tuple or list")
    cleaned = {clean_text(value, label, max_bytes=1024) for value in values}
    cleaned.discard("")
    if required and not cleaned:
        raise ValueError(f"{label} must not be empty")
    return tuple(sorted(cleaned))


def is_sha256(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in sorted(value.items())}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"value is not JSON-compatible: {type(value).__name__}")
