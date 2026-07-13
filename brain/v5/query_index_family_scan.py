"""Strong canonical-family scans shared by repair and bounded fallback."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_accumulator import (
    content_accumulator_from_pairs,
    content_accumulator_watermark,
)
from brain.v5.query_index import _document_row, _hash_json, _relative_path
from brain.v5.record_envelope import read_envelope_compat
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import record_family_paths


@dataclass(frozen=True)
class CanonicalFamilyScan:
    family: str
    documents: tuple[dict[str, Any], ...]
    content_watermark: str
    content_accumulator: dict[str, Any]
    state_token: str
    malformed_count: int
    checked_paths: tuple[str, ...]
    issues: tuple[str, ...] = ()


def canonical_family_paths(ws: WorkspacePaths, family: str) -> tuple[Path, ...]:
    spec = record_family_specs()[family]
    paths, _storage_exists = record_family_paths(ws, spec)
    return tuple(paths)


def scan_canonical_family(
    ws: WorkspacePaths,
    family: str,
    *,
    paths: Iterable[Path] | None = None,
) -> CanonicalFamilyScan:
    """Parse one family once and retain malformed bytes in its watermark."""

    spec = record_family_specs()[family]
    selected_paths = tuple(paths) if paths is not None else canonical_family_paths(ws, family)
    documents: list[dict[str, Any]] = []
    content_pairs: list[list[str]] = []
    state_rows: list[list[Any]] = []
    checked_paths: list[str] = []
    issues: list[str] = []
    for path in selected_paths:
        relative_path = _relative_path(ws, path)
        checked_paths.append(relative_path)
        stat = path.stat()
        state_rows.append([relative_path, stat.st_size, stat.st_mtime_ns])
        try:
            frontmatter, body = read_md(path)
            envelope = read_envelope_compat(frontmatter, spec, path, body=body)
            document = _document_row(ws, spec, frontmatter, body, envelope, path)
        except Exception as exc:  # noqa: BLE001 - malformed bytes remain explicit coverage.
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            content_pairs.append([f"malformed:{family}:{relative_path}", digest])
            issues.append(f"{relative_path}: {type(exc).__name__}: {exc}")
            continue
        documents.append(document)
        content_pairs.append([document["record_ref"], document["record_content_hash"]])
    documents.sort(key=lambda row: row["record_ref"])
    content_accumulator = content_accumulator_from_pairs(content_pairs)
    return CanonicalFamilyScan(
        family=family,
        documents=tuple(documents),
        content_watermark=content_accumulator_watermark(content_accumulator),
        content_accumulator=content_accumulator,
        state_token=_hash_json(sorted(state_rows)),
        malformed_count=len(issues),
        checked_paths=tuple(sorted(checked_paths)),
        issues=tuple(issues),
    )
