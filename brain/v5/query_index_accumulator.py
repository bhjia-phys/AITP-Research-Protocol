"""Rebuildable O(1)-updatable strong family content accumulators."""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, Mapping

from brain.v5.query_index_documents import _hash_json


_ALGORITHM = "dual-sha256-additive-multiset-v1"
_MODULUS = 1 << 256
_ZERO = "0" * 64


def empty_content_accumulator() -> dict[str, int | str]:
    return {
        "algorithm": _ALGORITHM,
        "count": 0,
        "sum_a": _ZERO,
        "sum_b": _ZERO,
    }


def content_accumulator_from_pairs(
    pairs: Iterable[tuple[str, str] | list[str]],
) -> dict[str, int | str]:
    state = empty_content_accumulator()
    for key, value in pairs:
        state = _replace(state, str(key), "", str(value))
    return state


def replace_content_accumulator_pair(
    accumulator: Mapping[str, object],
    *,
    key: str,
    previous_value: str,
    current_value: str,
) -> dict[str, int | str]:
    if not key.strip() or not current_value.strip():
        raise ValueError("content accumulator replacement requires key and current_value")
    return _replace(
        _validated_state(accumulator),
        key.strip(),
        previous_value.strip(),
        current_value.strip(),
    )


def content_accumulator_watermark(accumulator: Mapping[str, object]) -> str:
    return _hash_json(_validated_state(accumulator))


def _replace(
    accumulator: Mapping[str, object],
    key: str,
    previous_value: str,
    current_value: str,
) -> dict[str, int | str]:
    state = _validated_state(accumulator)
    count = int(state["count"])
    sum_a = int(str(state["sum_a"]), 16)
    sum_b = int(str(state["sum_b"]), 16)
    if previous_value:
        old_a, old_b = _element_hashes(key, previous_value)
        count -= 1
        sum_a = (sum_a - old_a) % _MODULUS
        sum_b = (sum_b - old_b) % _MODULUS
    if current_value:
        new_a, new_b = _element_hashes(key, current_value)
        count += 1
        sum_a = (sum_a + new_a) % _MODULUS
        sum_b = (sum_b + new_b) % _MODULUS
    if count < 0:
        raise ValueError("content accumulator count cannot be negative")
    return {
        "algorithm": _ALGORITHM,
        "count": count,
        "sum_a": f"{sum_a:064x}",
        "sum_b": f"{sum_b:064x}",
    }


def _element_hashes(key: str, value: str) -> tuple[int, int]:
    payload = json.dumps(
        [key, value],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    first = hashlib.sha256(b"aitp-family-a\0" + payload).digest()
    second = hashlib.sha256(b"aitp-family-b\0" + payload).digest()
    return int.from_bytes(first, "big"), int.from_bytes(second, "big")


def _validated_state(accumulator: Mapping[str, object]) -> dict[str, int | str]:
    algorithm = str(accumulator.get("algorithm") or "")
    if algorithm != _ALGORITHM:
        raise ValueError("content accumulator algorithm is unsupported")
    count = int(accumulator.get("count", -1))
    sum_a = str(accumulator.get("sum_a") or "")
    sum_b = str(accumulator.get("sum_b") or "")
    if count < 0 or not _is_digest(sum_a) or not _is_digest(sum_b):
        raise ValueError("content accumulator state is malformed")
    return {
        "algorithm": algorithm,
        "count": count,
        "sum_a": sum_a.lower(),
        "sum_b": sum_b.lower(),
    }


def _is_digest(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdefABCDEF" for character in value)
