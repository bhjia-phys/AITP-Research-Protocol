"""Exact source-chain resolution for reconstruction coverage."""

from __future__ import annotations

import hashlib

from dataclasses import asdict
from pathlib import Path

from brain.v5.models import ReferenceLocationRecord, SourceAssetRecord
from brain.v5.source_acquisition import (
    SourceAcquisitionResolutionError,
    resolve_source_acquisition_for_source_asset,
)


def resolve_reconstructable_source_locations(
    ws,
    *,
    topic_id: str,
    anchor_refs: list[str],
    references: list[ReferenceLocationRecord],
    source_assets_by_id: dict[str, SourceAssetRecord],
) -> dict:
    references_by_id = {record.location_id: record for record in references}
    resolved_location_ids: list[str] = []
    resolved_asset_ids: list[str] = []
    issues: list[dict[str, str]] = []

    for anchor_ref in _unique(anchor_refs):
        candidates = _locations_for_anchor(anchor_ref, references, references_by_id)
        if not candidates:
            issues.append(_issue(
                "unresolved_source_asset_ref",
                anchor_ref,
                "source anchors must resolve through reference_location:<id>",
            ))
            continue
        resolved = False
        candidate_issues: list[dict[str, str]] = []
        for location in candidates:
            asset_id = _record_id_for_ref(location.source_ref, "source_asset")
            asset = source_assets_by_id.get(asset_id) if asset_id else None
            issue = _validate_source_chain(ws, topic_id, location, asset)
            if issue is not None:
                candidate_issues.append(issue)
                continue
            resolved = True
            resolved_location_ids.append(location.location_id)
            resolved_asset_ids.append(asset.asset_id)
        if not resolved:
            issues.extend(candidate_issues or [
                _issue(
                    "missing_source_asset",
                    anchor_ref,
                    "reference location has no typed source asset",
                )
            ])

    unique_issues = _unique_issues(issues)
    complete = bool(anchor_refs) and not unique_issues
    return {
        "status": "complete" if complete else "incomplete",
        "resolved_location_ids": _unique(resolved_location_ids) if complete else [],
        "resolved_asset_ids": _unique(resolved_asset_ids) if complete else [],
        "issues": unique_issues,
    }


def source_anchor_refs(evidence, objects, relations) -> list[str]:
    refs: set[str] = set()
    for record in evidence:
        refs.update(record.source_refs)
    for record in objects:
        refs.update(record.source_refs)
    for record in relations:
        refs.update(record.source_refs)
    return sorted(ref for ref in refs if ref)


def _locations_for_anchor(anchor_ref, references, references_by_id):
    location_id = _record_id_for_ref(anchor_ref, "reference_location")
    if location_id:
        location = references_by_id.get(location_id)
        return [location] if location is not None else []
    asset_id = _record_id_for_ref(anchor_ref, "source_asset")
    if asset_id:
        expected_ref = f"source_asset:{asset_id}"
        return [record for record in references if record.source_ref == expected_ref]
    return []


def _validate_source_chain(ws, topic_id, location, asset):
    if location.topic_id != topic_id:
        return _issue(
            "reference_location_topic_mismatch",
            location.source_ref,
            f"reference location {location.location_id} belongs to another topic",
        )
    if asset is None:
        return _issue(
            "missing_source_asset",
            location.source_ref,
            f"reference location {location.location_id} has no typed source asset",
        )
    if asset.topic_id != topic_id:
        return _issue(
            "source_asset_topic_mismatch",
            location.source_ref,
            f"source asset {asset.asset_id} belongs to another topic",
        )
    if asset.metadata.get("acquisition_state") != "acquired":
        return _unverified(location, asset)
    receipt_ref = asset.metadata.get("source_acquisition_receipt_ref")
    decision_ref = asset.metadata.get("source_acquisition_decision_ref")
    if not isinstance(receipt_ref, dict) or not isinstance(decision_ref, dict):
        return _unverified(location, asset)
    try:
        resolution = resolve_source_acquisition_for_source_asset(ws, receipt_ref)
    except (SourceAcquisitionResolutionError, TypeError, ValueError):
        return _unverified(location, asset)
    if asdict(resolution.receipt_ref) != receipt_ref or asdict(resolution.decision_ref) != decision_ref:
        return _unverified(location, asset)
    if (
        resolution.receipt.topic_id != asset.topic_id
        or resolution.receipt.claim_id != asset.claim_id
        or resolution.receipt.canonical_uri != asset.uri
        or resolution.receipt.byte_sha256 != asset.content_hash
        or resolution.receipt.hash_algorithm != asset.hash_algorithm
    ):
        return _issue(
            "source_asset_hash_mismatch",
            location.source_ref,
            f"source asset {asset.asset_id} disagrees with its acquisition receipt",
        )
    local_path = str(asset.metadata.get("local_path") or "").strip()
    if not local_path:
        return _issue(
            "source_asset_storage_mismatch",
            location.source_ref,
            f"source asset {asset.asset_id} does not resolve to the receipted blob",
        )
    try:
        resolved_path = Path(local_path).resolve(strict=True)
    except (FileNotFoundError, OSError):
        return _issue(
            "source_blob_missing",
            location.source_ref,
            f"source asset {asset.asset_id} receipted blob is missing",
        )
    blob_root = (ws.root / "source_blobs").resolve()
    if (
        not resolved_path.is_file()
        or not resolved_path.is_relative_to(blob_root)
        or resolved_path.as_uri() != resolution.receipt.stored_uri
    ):
        return _issue(
            "source_asset_storage_mismatch",
            location.source_ref,
            f"source asset {asset.asset_id} does not resolve to the authorized blob store",
        )
    if (
        resolved_path.stat().st_size != resolution.receipt.byte_length
        or _sha256(resolved_path) != resolution.receipt.byte_sha256
    ):
        return _issue(
            "source_blob_hash_mismatch",
            location.source_ref,
            f"source asset {asset.asset_id} blob bytes disagree with the acquisition receipt",
        )
    if (
        asset.metadata.get("access_license_disposition") != resolution.decision.access_disposition
        or asset.metadata.get("storage_permission") != resolution.decision.storage_permission
    ):
        return _unverified(location, asset)
    return None


def _unverified(location, asset):
    return _issue(
        "source_acquisition_unverified",
        location.source_ref,
        f"source asset {asset.asset_id} lacks a valid exact acquisition receipt",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _issue(code: str, source_ref: str, detail: str) -> dict[str, str]:
    return {"code": code, "source_ref": source_ref, "detail": detail}


def _record_id_for_ref(value: str, expected_kind: str) -> str:
    text = str(value or "").strip()
    prefix = f"{expected_kind}:"
    if not text.startswith(prefix):
        return ""
    record_id = text[len(prefix):].strip()
    return record_id if record_id and ":" not in record_id else ""


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _unique_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    result = []
    for issue in issues:
        key = (issue["code"], issue["source_ref"])
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result
