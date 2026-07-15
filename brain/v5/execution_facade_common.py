"""Shared JSON coercion and result normalization for the M2 execution facade."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from brain.v5.execution_surface_contracts import (
    execution_operation_specs,
    require_valid_execution_operation_result,
)
from brain.v5.pinned_record_refs import PinnedRecordRef


def decode_payload(payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("execution facade payload_json must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("execution facade payload must be a JSON object")
    return payload


def coerce_pin(value: Any, field_name: str = "record_ref") -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an exact pinned mapping")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def coerce_pins(values: Any, field_name: str) -> tuple[PinnedRecordRef, ...]:
    if not isinstance(values, list):
        raise ValueError(f"{field_name} must be a list of exact pins")
    return tuple(coerce_pin(value, field_name) for value in values)


def execution_result(operation: str, value: Any) -> dict[str, Any]:
    spec = execution_operation_specs()[operation]
    payload = {
        "ok": True,
        "kind": "execution_operation_result",
        "operation": operation,
        "state_effect": spec.state_effect,
        "writes_records": False,
        "result": jsonable(value),
        "truth_source": spec.truth_source,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    return require_valid_execution_operation_result(payload)


def jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [jsonable(item) for item in value]
    if isinstance(value, bytes):
        raise TypeError("execution facade does not inline artifact bytes")
    return value
