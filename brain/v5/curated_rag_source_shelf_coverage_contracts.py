"""Coverage accounting contracts for source-shelf RAG projections."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractResult, _require_list
from brain.v5.curated_rag_source_shelf_contract_support import (
    digest,
    items,
    non_negative_int,
    typed_ref,
)
from brain.v5.source_shelf_storage import hash_json


def validate_coverage(
    coverage: dict[str, Any],
    path: str,
    result: ContractResult,
    *,
    generation: Any = None,
    topic_id: Any = None,
) -> None:
    inventory_keys = (
        "requested_source_asset_refs",
        "resolved_source_asset_refs",
        "indexed_source_asset_refs",
        "unindexed_source_asset_refs",
    )
    for key in (*inventory_keys, "issues"):
        _require_list(coverage.get(key), f"{path}.{key}", result)
    values = [coverage.get(key) for key in inventory_keys]
    if all(isinstance(value, list) for value in values):
        requested, resolved, indexed, unindexed = values
        refs_valid = all(
            typed_ref(item, "source_asset")
            for inventory in values
            for item in inventory
        )
        if not refs_valid:
            result.add(path, "source inventories must contain typed refs")
        else:
            if any(len(inventory) != len(set(inventory)) for inventory in values):
                result.add(path, "source inventories must not contain duplicates")
            if not set(resolved).issubset(requested):
                result.add(f"{path}.resolved_source_asset_refs", "must be requested")
            if not set(indexed).issubset(resolved):
                result.add(f"{path}.indexed_source_asset_refs", "must be resolved")
            if unindexed != sorted(set(requested).difference(indexed)):
                result.add(f"{path}.unindexed_source_asset_refs", "must account for omissions")
    issue_count = coverage.get("issue_count")
    if issue_count is not None:
        if not non_negative_int(issue_count):
            result.add(f"{path}.issue_count", "must be a non-negative integer")
        if issue_count != len(items(coverage.get("issues"))):
            result.add(f"{path}.issue_count", "must match issues")
    incomplete = coverage.get("incomplete")
    if incomplete is not None:
        if not isinstance(incomplete, bool):
            result.add(f"{path}.incomplete", "must be boolean")
        if incomplete is not bool(items(coverage.get("issues"))):
            result.add(f"{path}.incomplete", "must match issues")
    for key in ("source_shelf_passage_count", "indexed_passage_count"):
        if key in coverage and not non_negative_int(coverage.get(key)):
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if generation is not None and not digest(coverage.get("source_shelf_passages_hash")):
        result.add(f"{path}.source_shelf_passages_hash", "must be a sha256 digest")
    shelf_count = coverage.get("source_shelf_passage_count")
    indexed_count = coverage.get("indexed_passage_count")
    if non_negative_int(shelf_count) and non_negative_int(indexed_count) and indexed_count > shelf_count:
        result.add(f"{path}.indexed_passage_count", "must not exceed shelf passages")
    if generation is not None:
        if coverage.get("source_shelf_generation") != generation:
            result.add(f"{path}.source_shelf_generation", "must match retrieval generation")
        if coverage.get("source_shelf_topic_id") != topic_id:
            result.add(f"{path}.source_shelf_topic_id", "must match retrieval topic")
        fingerprint = coverage.get("coverage_hash")
        if not digest(fingerprint) or hash_json(coverage_basis(coverage)) != fingerprint:
            result.add(f"{path}.coverage_hash", "must hash the exact generation-bound coverage")


def catalog_coverage(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "requested_source_asset_refs": policy.get("requested_source_asset_refs"),
        "resolved_source_asset_refs": policy.get("resolved_source_asset_refs"),
        "indexed_source_asset_refs": policy.get("indexed_source_asset_refs"),
        "unindexed_source_asset_refs": policy.get("unindexed_source_asset_refs"),
        "issues": policy.get("source_shelf_issues"),
        "source_shelf_passage_count": policy.get("source_shelf_passage_count"),
        "source_shelf_passages_hash": policy.get("source_shelf_passages_hash"),
        "indexed_passage_count": policy.get("indexed_passage_count"),
    }


def coverage_basis(coverage: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in coverage.items() if key != "coverage_hash"}


__all__ = ["catalog_coverage", "coverage_basis", "validate_coverage"]
