"""Safe record-id validation and family-contained canonical paths."""

from __future__ import annotations

import os
from pathlib import Path

from brain.v5.paths import WorkspacePaths
from brain.v5.record_family_registry import RecordFamilySpec


_UNSAFE_RECORD_ID_CHARACTERS = frozenset('/\\:*?"<>|')
_WINDOWS_RESERVED_RECORD_IDS = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)


def validate_record_id(record_id: str) -> str:
    if not isinstance(record_id, str) or not record_id:
        raise ValueError("record_id must be a non-empty string")
    if record_id != record_id.strip():
        raise ValueError("record_id must not have leading or trailing whitespace")
    if record_id in {".", ".."} or record_id.endswith("."):
        raise ValueError("record_id must be an unambiguous path component")
    if any(
        character in _UNSAFE_RECORD_ID_CHARACTERS or ord(character) < 32
        for character in record_id
    ):
        raise ValueError("record_id must be a single safe path component")
    if record_id.split(".", 1)[0].upper() in _WINDOWS_RESERVED_RECORD_IDS:
        raise ValueError("record_id must not use a reserved filesystem name")
    return record_id


def record_path(
    ws: WorkspacePaths,
    spec: RecordFamilySpec,
    record_id: str,
) -> Path:
    record_id = validate_record_id(record_id)
    family_root = _canonical_family_root(ws, spec)
    if spec.is_registry_family:
        path = family_root / f"{record_id}.md"
    elif spec.family == "contexts":
        path = ws.context_dir(record_id) / "context.md"
    elif spec.family == "topics":
        path = ws.topic_dir(record_id) / "topic.md"
    elif spec.family == "sessions":
        path = ws.session_path(record_id)
    elif spec.family == "memory_entries":
        path = family_root / f"{record_id}.md"
    else:
        raise ValueError(f"unsupported special record family: {spec.family}")
    return _assert_resolved_within_family_root(
        path,
        family_root,
        label="canonical record",
    )


def record_lock_path(
    ws: WorkspacePaths,
    spec: RecordFamilySpec,
    record_id: str,
) -> Path:
    record_id = validate_record_id(record_id)
    family_root = ws.root / "runtime" / "locks" / spec.family
    return _assert_resolved_within_family_root(
        family_root / f"{record_id}.lock",
        family_root,
        label="record lock",
    )


def _assert_resolved_within_family_root(
    path: Path,
    family_root: Path,
    *,
    label: str,
) -> Path:
    resolved_root = _normalized_resolved_path(family_root)
    resolved_path = _normalized_resolved_path(path)
    try:
        common = os.path.commonpath([resolved_root, resolved_path])
    except ValueError as exc:
        raise ValueError(f"{label} path escaped its family root") from exc
    if common != resolved_root:
        raise ValueError(f"{label} path escaped its family root")
    return path


def _normalized_resolved_path(path: Path) -> str:
    value = os.path.normcase(os.path.normpath(str(path.resolve(strict=False))))
    if value.startswith("\\\\?\\UNC\\"):
        return f"\\\\{value[8:]}"
    if value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _canonical_family_root(ws: WorkspacePaths, spec: RecordFamilySpec) -> Path:
    if spec.is_registry_family:
        return ws.root / spec.relative_dir
    if spec.family == "contexts":
        return ws.root / "contexts"
    if spec.family == "topics":
        return ws.root / "topics"
    if spec.family == "sessions":
        return ws.root / "runtime" / "sessions"
    if spec.family == "memory_entries":
        return ws.root / "memory" / "l2" / "entries"
    raise ValueError(f"unsupported special record family: {spec.family}")
