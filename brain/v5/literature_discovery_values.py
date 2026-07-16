"""Immutable JSON and URI helpers for literature discovery host values."""

from __future__ import annotations

from math import isfinite
from types import MappingProxyType
from urllib.parse import urlsplit, urlunsplit


_SAFE_URI_SCHEMES = {"http", "https"}


def _immutable(*_args, **_kwargs):
    raise TypeError("literature discovery receipt values are immutable")


class FrozenJsonDict(dict):
    """JSON-serializable dictionary that cannot change after construction."""

    __setitem__ = _immutable
    __delitem__ = _immutable
    __ior__ = _immutable
    clear = _immutable
    pop = _immutable
    popitem = _immutable
    setdefault = _immutable
    update = _immutable


class FrozenJsonList(list):
    """JSON-serializable list that cannot change after construction."""

    __setitem__ = _immutable
    __delitem__ = _immutable
    __iadd__ = _immutable
    __imul__ = _immutable
    append = _immutable
    clear = _immutable
    extend = _immutable
    insert = _immutable
    pop = _immutable
    remove = _immutable
    reverse = _immutable
    sort = _immutable


def normalize_coverage(value):
    """Materialize bounded host coverage as deeply immutable plain JSON."""

    try:
        if value is None:
            return FrozenJsonDict(), ""
        if not _is_plain_mapping(value):
            raise TypeError("coverage must be a plain JSON mapping")
        return freeze_json_value(_plain_json_value(value)), ""
    except Exception:  # noqa: BLE001 - coverage is untrusted host input.
        return FrozenJsonDict(), "coverage must contain only JSON-compatible values"


def freeze_json_value(value):
    if type(value) is dict:
        return FrozenJsonDict(
            (key, freeze_json_value(item)) for key, item in value.items()
        )
    if type(value) is list:
        return FrozenJsonList(freeze_json_value(item) for item in value)
    return value


def safe_external_uri(value: str) -> bool:
    try:
        if any(character.isspace() or ord(character) < 32 for character in value):
            return False
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in _SAFE_URI_SCHEMES or not parsed.netloc:
            return False
        if not parsed.hostname or parsed.username is not None or parsed.password is not None:
            return False
        parsed.port
        return True
    except (TypeError, ValueError):
        return False


def uri_dedup_key(value: str) -> str:
    """Normalize URI transport identity without folding path/query case."""

    parsed = urlsplit(value)
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )


def _plain_json_value(value, *, depth=0, budget=None):
    if budget is None:
        budget = [1000]
    budget[0] -= 1
    if budget[0] < 0 or depth > 8:
        raise ValueError("coverage exceeds structural budget")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value.bit_length() > 64:
            raise ValueError("coverage integer exceeds size budget")
        return value
    if isinstance(value, str):
        if len(value) > 10000:
            raise ValueError("coverage string exceeds size budget")
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("coverage float must be finite")
        return value
    if type(value) is list:
        return [
            _plain_json_value(item, depth=depth + 1, budget=budget)
            for item in value
        ]
    if _is_plain_mapping(value):
        if len(value) > 1000:
            raise ValueError("coverage mapping exceeds size budget")
        if any(not isinstance(key, str) or len(key) > 500 for key in value):
            raise TypeError("coverage keys must be bounded strings")
        return {
            key: _plain_json_value(item, depth=depth + 1, budget=budget)
            for key, item in value.items()
        }
    raise TypeError("coverage value is not JSON compatible")


def _is_plain_mapping(value) -> bool:
    return type(value) is dict or isinstance(value, MappingProxyType)


__all__ = [
    "FrozenJsonDict",
    "FrozenJsonList",
    "freeze_json_value",
    "normalize_coverage",
    "safe_external_uri",
    "uri_dedup_key",
]
