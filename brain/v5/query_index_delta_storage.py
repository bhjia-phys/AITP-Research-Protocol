"""Atomic storage and lineage validation for query-index delta manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import IndexIntegrityError, IndexManifest, load_query_manifest
from brain.v5.query_index_delta_contracts import (
    DirtyFamilyState,
    IndexDeltaEntry,
    IndexDeltaManifest,
)
from brain.v5.query_index_documents import _hash_json


_DELTA_MANIFEST_KIND = "query_index_delta"
_DELTA_SCHEMA_VERSION = 1


def _delta_manifest_path(ws: WorkspacePaths) -> Path:
    return ws.root / "indexes" / "delta" / "manifest.json"


def _pointer_digest(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _new_delta_for_base(base: IndexManifest) -> IndexDeltaManifest:
    return IndexDeltaManifest(
        base_generation=base.generation,
        base_content_hash=base.base_content_hash or base.content_hash,
        generation=0,
        family_state_tokens=dict(base.family_state_tokens),
        family_content_watermarks=dict(base.family_content_watermarks),
        family_content_accumulators=dict(base.family_content_accumulators),
        family_malformed_counts=dict(base.malformed_family_counts),
        predecessor_chain_token=_hash_json(
            [base.generation, base.base_content_hash or base.content_hash]
        ),
    )


def _load_delta_manifest(ws: WorkspacePaths) -> IndexDeltaManifest | None:
    path = _delta_manifest_path(ws)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("manifest_kind") != _DELTA_MANIFEST_KIND:
        raise IndexIntegrityError("delta manifest kind is invalid")
    if int(payload.get("schema_version", 0)) != _DELTA_SCHEMA_VERSION:
        raise IndexIntegrityError("delta manifest schema version is unsupported")
    expected_hash = str(payload.get("content_hash") or "")
    hash_payload = dict(payload)
    hash_payload.pop("content_hash", None)
    if _hash_json(hash_payload) != expected_hash:
        raise IndexIntegrityError("delta manifest content hash mismatch")
    entries = {
        key: IndexDeltaEntry(**value)
        for key, value in dict(payload.get("entries") or {}).items()
    }
    dirty = {
        key: DirtyFamilyState(
            **{
                **value,
                "diagnostics": tuple(value.get("diagnostics") or ()),
            }
        )
        for key, value in dict(payload.get("dirty_families") or {}).items()
    }
    return IndexDeltaManifest(
        base_generation=int(payload["base_generation"]),
        base_content_hash=str(payload["base_content_hash"]),
        generation=int(payload["generation"]),
        entries=entries,
        repaired_families=dict(payload.get("repaired_families") or {}),
        family_state_tokens=dict(payload.get("family_state_tokens") or {}),
        family_content_watermarks=dict(payload.get("family_content_watermarks") or {}),
        family_content_accumulators={
            key: dict(value)
            for key, value in dict(payload.get("family_content_accumulators") or {}).items()
        },
        family_malformed_counts={
            key: int(value)
            for key, value in dict(payload.get("family_malformed_counts") or {}).items()
        },
        dirty_families=dirty,
        predecessor_chain_token=str(payload.get("predecessor_chain_token") or ""),
        content_hash=expected_hash,
        manifest_kind=str(payload["manifest_kind"]),
        schema_version=int(payload["schema_version"]),
    )


def _publish_delta_manifest(ws: WorkspacePaths, manifest: IndexDeltaManifest) -> None:
    payload = asdict(replace(manifest, content_hash=""))
    payload.pop("content_hash", None)
    for field_name in (
        "entries",
        "repaired_families",
        "dirty_families",
        "family_state_tokens",
        "family_content_watermarks",
        "family_content_accumulators",
        "family_malformed_counts",
    ):
        payload[field_name] = dict(sorted(payload.get(field_name, {}).items()))
    payload["content_hash"] = _hash_json(payload)
    write_text_atomic(
        _delta_manifest_path(ws),
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


def _delta_matches_base(delta: IndexDeltaManifest, base: IndexManifest) -> bool:
    return (
        delta.base_generation == base.generation
        and delta.base_content_hash == (base.base_content_hash or base.content_hash)
    )


def effective_family_content_watermark(ws: WorkspacePaths, family: str) -> str:
    """Read the projected predecessor watermark without scanning canonical files."""

    if not (ws.root / "indexes" / "manifest.json").exists():
        return ""
    base = load_query_manifest(ws)
    delta = _load_delta_manifest(ws)
    if delta is not None and _delta_matches_base(delta, base):
        return delta.family_content_watermarks.get(
            family,
            base.family_content_watermarks.get(family, ""),
        )
    return base.family_content_watermarks.get(family, "")
