"""Helpers for host-facing AITP payload hint metadata."""

from __future__ import annotations

from typing import Any


def with_draft_schema(hint: dict[str, Any]) -> dict[str, Any]:
    """Attach placeholder/required-field metadata to a payload hint draft."""

    draft = hint.get("draft")
    required_fields = hint.get("required_fields")
    if not isinstance(draft, dict) or not isinstance(required_fields, list):
        return hint

    placeholder_values = _placeholder_values(draft)
    return {
        **hint,
        "draft_schema": {
            "required_fields": [str(item) for item in required_fields if str(item)],
            "placeholder_fields": list(placeholder_values),
            "placeholder_values": placeholder_values,
            "host_must_resolve": list(placeholder_values),
            "field_case": "snake_case",
            "summary_inputs_trusted": bool(hint.get("summary_inputs_trusted", False)),
            "can_update_claim_trust": bool(hint.get("can_update_claim_trust", False)),
        },
    }


def _placeholder_values(value: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(value, str) and _is_placeholder(value):
        return {prefix: value} if prefix else {}
    if isinstance(value, dict):
        result: dict[str, str] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_placeholder_values(item, path))
        return result
    if isinstance(value, list):
        result: dict[str, str] = {}
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            result.update(_placeholder_values(item, path))
        return result
    return {}


def _is_placeholder(value: str) -> bool:
    stripped = value.strip()
    return len(stripped) > 2 and stripped.startswith("<") and stripped.endswith(">")
