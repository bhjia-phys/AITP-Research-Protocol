"""Contracts for generation-stamped AITP indexes."""

from __future__ import annotations

import re

from brain.v5.query_index import IndexBuildReport


_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_index_build_report(report: IndexBuildReport) -> tuple[str, ...]:
    errors: list[str] = []
    manifest = report.manifest
    if manifest.generation < 1:
        errors.append("generation must be positive")
    if manifest.index_schema_version < 1:
        errors.append("index_schema_version must be positive")
    for name, value in (
        ("canonical_watermark", manifest.canonical_watermark),
        ("canonical_state_token", manifest.canonical_state_token),
        ("content_hash", manifest.content_hash),
        ("document_hash", manifest.document_hash),
        ("lexical_hash", manifest.lexical_hash),
        ("issues_hash", manifest.issues_hash),
    ):
        if not _HASH_RE.fullmatch(value):
            errors.append(f"{name} must be lowercase SHA-256")
    if report.indexed_count != manifest.record_count:
        errors.append("indexed_count must equal manifest record_count")
    if report.malformed_count != manifest.malformed_count:
        errors.append("malformed_count must equal manifest malformed_count")
    if sum(manifest.malformed_family_counts.values()) != manifest.malformed_count:
        errors.append("malformed_family_counts must sum to malformed_count")
    if report.checked_count != report.indexed_count + report.malformed_count:
        errors.append("checked_count must equal indexed plus malformed")
    if report.can_update_kernel_state or report.can_update_claim_trust:
        errors.append("derived index builds cannot update kernel state or claim trust")
    return tuple(errors)
