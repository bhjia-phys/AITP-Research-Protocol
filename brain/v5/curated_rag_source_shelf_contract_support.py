"""Shared values and scalar predicates for source-shelf RAG contracts."""

from __future__ import annotations

from typing import Any


MANIFEST_BASIS_KEYS = (
    "schema_version",
    "topic_id",
    "requested_source_asset_refs",
    "source_pins",
    "curation_rationale",
    "reader_version",
    "extractor_version",
    "max_passage_chars",
    "incomplete_coverage",
    "passages_hash",
    "issues_hash",
)
MANIFEST_KEYS = set(MANIFEST_BASIS_KEYS).union(
    {
        "generation",
        "passage_count",
        "issue_count",
        "passage_file",
        "issues_file",
        "orientation_only",
        "can_update_claim_trust",
    }
)
SOURCE_PIN_KEYS = {
    "source_asset_ref",
    "topic_id",
    "record_content_hash",
    "record_revision",
    "canonical_uri",
    "local_uri",
    "content_hash",
    "acquired_at",
    "access_disposition",
    "storage_permission",
    "acquisition_decision_ref",
    "acquisition_receipt_ref",
    "source_location_pins",
}
LOCATION_PIN_KEYS = {
    "record_ref",
    "content_hash",
    "revision",
    "topic_id",
    "source_asset_ref",
}


def non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def typed_ref(value: Any, family: str) -> bool:
    return isinstance(value, str) and value.startswith(f"{family}:") and len(value) > len(family) + 1


def digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def non_negative_int(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def positive_int(value: Any) -> bool:
    return non_negative_int(value) and value > 0


def items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


__all__ = [
    "LOCATION_PIN_KEYS",
    "MANIFEST_BASIS_KEYS",
    "MANIFEST_KEYS",
    "SOURCE_PIN_KEYS",
    "digest",
    "items",
    "non_empty",
    "non_negative_int",
    "positive_int",
    "typed_ref",
]
