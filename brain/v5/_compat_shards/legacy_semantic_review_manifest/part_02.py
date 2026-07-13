# Compatibility shard 2 for legacy_semantic_review_manifest.
from __future__ import annotations

def _text_matches(current: str, expected: str) -> bool:
    current_text = _clean_text(current)
    expected_text = _clean_text(expected)
    return bool(current_text and expected_text and current_text == expected_text)

def _clean_text(value: str) -> str:
    return " ".join(str(value).split())

def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result
