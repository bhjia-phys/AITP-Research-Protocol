"""Efficient canonical family state snapshots for orientation freshness."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_documents import _hash_json, _relative_path
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import record_family_paths


@dataclass(frozen=True)
class FamilyStateSnapshot:
    token: str
    checked_paths: tuple[str, ...]


def current_family_state_snapshot(
    ws: WorkspacePaths,
    family: str,
) -> FamilyStateSnapshot:
    spec = record_family_specs()[family]
    if spec.is_registry_family:
        return _registry_state_snapshot(
            ws.root / spec.relative_dir,
            relative_dir=spec.relative_dir,
        )
    paths, _storage_exists = record_family_paths(ws, spec)
    rows = []
    checked_paths = []
    for path in paths:
        stat = path.stat()
        relative = _relative_path(ws, path)
        rows.append([relative, stat.st_size, stat.st_mtime_ns])
        checked_paths.append(relative)
    return FamilyStateSnapshot(
        token=_hash_json(sorted(rows)),
        checked_paths=tuple(sorted(checked_paths)),
    )


def _registry_state_snapshot(
    directory: Path,
    *,
    relative_dir: str,
) -> FamilyStateSnapshot:
    rows = []
    checked_paths = []
    relative_prefix = Path(relative_dir).as_posix().strip("/")
    if directory.exists():
        with os.scandir(directory) as entries:
            for entry in entries:
                if not entry.name.endswith(".md"):
                    continue
                stat = entry.stat()
                relative = f"{relative_prefix}/{entry.name}"
                rows.append([relative, stat.st_size, stat.st_mtime_ns])
                checked_paths.append(relative)
    return FamilyStateSnapshot(
        token=_hash_json(sorted(rows)),
        checked_paths=tuple(sorted(checked_paths)),
    )
