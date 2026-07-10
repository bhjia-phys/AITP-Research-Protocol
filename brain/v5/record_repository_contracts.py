"""Structural contracts for safe repository results."""

from __future__ import annotations

import re

from brain.v5.record_repository import RecordReadReport, WriteResult


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_WRITE_STATUSES = {"created", "unchanged", "revised"}


def validate_write_result(result: WriteResult) -> tuple[str, ...]:
    errors: list[str] = []
    if result.status not in _WRITE_STATUSES:
        errors.append("status is unsupported")
    if ":" not in result.record_ref:
        errors.append("record_ref must be a typed ref")
    if not result.path:
        errors.append("path must be non-empty")
    if not _HASH_RE.fullmatch(result.content_hash):
        errors.append("content_hash must be lowercase SHA-256")
    if result.previous_hash and not _HASH_RE.fullmatch(result.previous_hash):
        errors.append("previous_hash must be lowercase SHA-256 when present")
    if not isinstance(result.revision, int) or isinstance(result.revision, bool) or result.revision < 1:
        errors.append("revision must be a positive integer")
    if result.status == "revised" and not result.archive_path:
        errors.append("revised results require archive_path")
    return tuple(errors)


def validate_record_read_report(report: RecordReadReport) -> tuple[str, ...]:
    errors: list[str] = []
    if report.checked_count < 0 or report.loaded_count < 0:
        errors.append("counts must be non-negative")
    if report.loaded_count != len(report.records):
        errors.append("loaded_count must equal records length")
    if report.checked_count != report.loaded_count + len(report.malformed):
        errors.append("checked_count must equal loaded plus malformed")
    if report.missing and report.checked_count != 0:
        errors.append("missing directories cannot have checked records")
    for issue in report.malformed:
        if not issue.family or not issue.path or not issue.error_type or not issue.message:
            errors.append("malformed issues require family, path, type, and message")
    return tuple(errors)
