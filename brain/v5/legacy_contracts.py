"""Contracts for legacy-topic migration payloads."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult


def validate_legacy_migration_result(
    payload: dict[str, Any],
    *,
    path: str = "legacy_migration_result",
) -> ContractResult:
    result = ContractResult()
    if not isinstance(payload, dict):
        result.add(path, "must be a mapping")
        return result

    for key in ("kind", "topic_id", "context_id", "session_id", "active_claim_id"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if payload.get("kind") != "legacy_topic_migration_result":
        result.add(f"{path}.kind", "must be legacy_topic_migration_result")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")

    written = payload.get("written_records")
    if not isinstance(written, dict):
        result.add(f"{path}.written_records", "must be a mapping")
    else:
        for key in ("topics", "claims", "evidence", "reference_locations", "sensemaking_reports", "trace_events"):
            values = written.get(key)
            if not isinstance(values, list) or not all(isinstance(item, str) and item for item in values):
                result.add(f"{path}.written_records.{key}", "must be a list of non-empty strings")

    refs = payload.get("preserved_source_refs")
    if not isinstance(refs, list) or not all(isinstance(item, str) and item for item in refs):
        result.add(f"{path}.preserved_source_refs", "must be a list of non-empty strings")
    return result


def require_valid_legacy_migration_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_legacy_migration_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload
