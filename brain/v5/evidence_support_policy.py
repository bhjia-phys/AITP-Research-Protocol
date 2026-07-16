"""Exact support-pin classification shared by evidence trust paths."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from brain.v5.models import ArtifactRecord, SourceAssetRecord, ToolRunRecord, ValidationResultRecord


_CLAIM_REQUIRED_KINDS = frozenset({"artifact", "tool_run", "validation_result"})
_UNSAFE_ARTIFACT_TERMS = frozenset(
    {"candidate", "context", "draft", "insight", "orientation", "rag", "search", "skill", "summary"}
)
_UNSAFE_DERIVED_PREFIXES = (
    "context:",
    "insight:",
    "rag:",
    "search:",
    "skill:",
    "summary:",
)
_UNSAFE_SOURCE_KINDS = frozenset(
    {
        "context_pack",
        "derived_summary",
        "discovery_receipt",
        "rag_chunk",
        "search_receipt",
        "skill",
        "skill_candidate",
        "summary_orientation",
    }
)


def pinned_record_ids(values: Sequence[Any], record_kind: str) -> list[str]:
    """Return record ids of one kind from exact pin objects or mappings."""

    prefix = f"{record_kind}:"
    result: list[str] = []
    for value in values:
        record_ref = (
            str(value.get("record_ref") or "")
            if isinstance(value, Mapping)
            else str(getattr(value, "record_ref", "") or "")
        )
        if record_ref.startswith(prefix):
            record_id = record_ref[len(prefix) :]
            if record_id and record_id not in result:
                result.append(record_id)
    return result


def evidence_support_record_ids(evidence: Any, record_kind: str) -> list[str]:
    return pinned_record_ids(getattr(evidence, "support_basis_refs", []) or [], record_kind)


def support_record_policy_errors(
    support_records: Sequence[tuple[Any, Any]],
    *,
    claim_id: str,
) -> dict[str, tuple[str, ...]]:
    """Return per-ref semantic errors after all exact support records resolve."""

    errors: dict[str, list[str]] = {}
    run_records = [record for _pin, record in support_records if isinstance(record, ToolRunRecord)]
    run_ids = {record.run_id for record in run_records}
    for pin, record in support_records:
        record_ref = pin.record_ref
        kind = record_ref.split(":", 1)[0]
        record_claim = str(getattr(record, "claim_id", "") or "")
        if claim_id and record_claim and record_claim != claim_id:
            _add(errors, record_ref, f"support_claim_mismatch:{record_ref}")
        elif kind in _CLAIM_REQUIRED_KINDS and claim_id and not record_claim:
            _add(errors, record_ref, f"support_claim_missing:{record_ref}")

        if isinstance(record, ArtifactRecord):
            if _artifact_is_derived_only(record):
                _add(errors, record_ref, f"inadmissible_derived_support:{record_ref}")
            if not any(record.artifact_id in run.artifact_ids for run in run_records):
                _add(errors, record_ref, f"artifact_support_requires_tool_run:{record_ref}")
        elif isinstance(record, ValidationResultRecord) and record.tool_run_id not in run_ids:
            _add(errors, record_ref, f"validation_support_requires_tool_run:{record_ref}")
        elif isinstance(record, SourceAssetRecord) and _source_asset_is_derived_only(record):
            _add(errors, record_ref, f"inadmissible_derived_support:{record_ref}")
    return {record_ref: tuple(items) for record_ref, items in errors.items()}


def _artifact_is_derived_only(record: ArtifactRecord) -> bool:
    descriptors = [
        record.artifact_type,
        record.role,
        str(record.metadata.get("role") or ""),
        str(record.metadata.get("source_kind") or ""),
    ]
    return any(_descriptor_is_unsafe(descriptor) for descriptor in descriptors)


def _source_asset_is_derived_only(record: SourceAssetRecord) -> bool:
    normalized_raw_source_kind = unicodedata.normalize("NFKC", record.source_kind.strip())
    if normalized_raw_source_kind and not normalized_raw_source_kind.isascii():
        return True
    source_kind_parts = _descriptor_parts(record.source_kind)
    source_kind_tokens = set(source_kind_parts)
    normalized_source_kind = "_".join(source_kind_parts)
    if normalized_source_kind in _UNSAFE_SOURCE_KINDS:
        return True
    if source_kind_tokens & _UNSAFE_ARTIFACT_TERMS:
        return True
    if "_".join(_descriptor_parts(record.asset_type)) == "generated_artifact":
        return True
    return any(
        str(ref).strip().lower().startswith(_UNSAFE_DERIVED_PREFIXES)
        for ref in record.derived_from
    )


def _descriptor_tokens(value: Any) -> set[str]:
    return set(_descriptor_parts(value))


def _descriptor_is_unsafe(value: Any) -> bool:
    normalized = unicodedata.normalize("NFKC", str(value or "").strip())
    if normalized and not normalized.isascii():
        return True
    return bool(_descriptor_tokens(normalized) & _UNSAFE_ARTIFACT_TERMS)


def _descriptor_parts(value: Any) -> tuple[str, ...]:
    raw = unicodedata.normalize("NFKC", str(value or "").strip())
    with_acronym_boundaries = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", raw)
    with_word_boundaries = re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        "_",
        with_acronym_boundaries,
    )
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", with_word_boundaries).lower()
    return tuple(token for token in normalized.split("_") if token)


def _add(errors: dict[str, list[str]], record_ref: str, error: str) -> None:
    errors.setdefault(record_ref, []).append(error)
