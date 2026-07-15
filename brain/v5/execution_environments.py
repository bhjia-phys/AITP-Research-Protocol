"""Canonical writers for reusable execution-environment identity."""

from __future__ import annotations

import re
from dataclasses import asdict, replace
from datetime import datetime
from typing import Any, Mapping

from brain.v5.execution_contracts import RedactionPolicy, redact_execution_payload
from brain.v5.models import ExecutionEnvironmentRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def record_execution_environment(
    ws: WorkspacePaths,
    record: ExecutionEnvironmentRecord,
    *,
    actor: RecordActor,
    redaction_policy: RedactionPolicy | None = None,
) -> WriteResult:
    """Persist one redacted, provenance-pinned environment record."""

    _validate_environment(record)
    source_refs = [_coerce_pin(item) for item in record.source_refs]
    for source_ref in source_refs:
        get_record_version(ws, source_ref)
    redaction = redact_execution_payload(
        {"environment": record.redacted_environment},
        redaction_policy,
    )
    stored = replace(
        record,
        redacted_environment=redaction.payload["environment"],
        source_refs=[asdict(item) for item in sorted(source_refs)],
    )
    return RecordRepository(ws, actor=actor).write(
        "execution_environments",
        stored,
        body=(
            "# Execution Environment\n\n"
            f"Host: `{stored.host}`\n\n"
            "Secrets and non-allowlisted environment values are not persisted.\n"
        ),
    )


def _validate_environment(record: ExecutionEnvironmentRecord) -> None:
    for name, value in {
        "environment_id": record.environment_id,
        "host": record.host,
        "operating_system": record.operating_system,
        "architecture": record.architecture,
        "created_at": record.created_at,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"execution environment {name} must be non-empty")
    try:
        if datetime.fromisoformat(record.created_at).tzinfo is None:
            raise ValueError
    except ValueError as exc:
        raise ValueError("execution environment created_at must include a timezone") from exc
    if set(record.executable_paths) != set(record.executable_hashes):
        raise ValueError("every executable path requires one executable hash")
    if any(not _SHA256.fullmatch(str(value)) for value in record.executable_hashes.values()):
        raise ValueError("execution environment executable hash must be lowercase sha256")


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("execution environment source refs must be exact pinned refs")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )
