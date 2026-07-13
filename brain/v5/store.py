"""Small typed-object store for AITP v5 Markdown artifacts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml

from brain.v5.legacy_record_materialization import materialize_record_class
from brain.v5.markdown import read_md, write_md

T = TypeVar("T")

LEGACY_TOLERANT_READ_OPERATIONS = frozenset(
    {
        "legacy_l2_seed_audit",
        "legacy_migration_accounting",
        "legacy_semantic_repair",
        "legacy_semantic_review",
        "legacy_semantic_review_packet",
        "legacy_source_reconstruction",
        "legacy_source_reconstruction_review",
        "execution_brief_legacy_orientation",
        "session_summary_legacy_tool_runs",
        "workspace_interaction_preview_legacy_records",
        "workspace_recovery_audit",
        "workspace_recovery_binding_repair",
    }
)


def to_frontmatter(record: Any) -> dict[str, Any]:
    """Convert a dataclass or mapping into serializable frontmatter."""

    if is_dataclass(record):
        return asdict(record)
    return dict(record)


def write_record(path: str | Path, record: Any, *, body: str = "") -> None:
    """Write a v5 record as Markdown+YAML."""

    write_md(path, to_frontmatter(record), body or default_body(record))


def read_record(path: str | Path, cls: type[T]) -> T:
    """Read frontmatter into a dataclass class."""

    fm, _ = read_md(path)
    if is_dataclass(cls):
        return materialize_record_class(fm, cls, path=path)
    return cls(**fm)


def list_records(directory: str | Path, cls: type[T]) -> list[T]:
    """Read all Markdown records in a directory."""

    root = Path(directory)
    if not root.exists():
        return []
    return [read_record(path, cls) for path in sorted(root.glob("*.md"))]


def list_valid_records(
    directory: str | Path,
    cls: type[T],
    *,
    operation: str | None = None,
) -> list[T]:
    """Legacy/recovery-only tolerant read that skips malformed files.

    Do not use this helper for exhaustive canonical queries or absence claims;
    use ``RecordRepository.list`` so every malformed path remains visible.
    """

    if operation not in LEGACY_TOLERANT_READ_OPERATIONS:
        raise ValueError(
            "tolerant record reads require a named legacy or recovery operation"
        )

    root = Path(directory)
    if not root.exists():
        return []
    records: list[T] = []
    for path in sorted(root.glob("*.md")):
        try:
            records.append(read_record(path, cls))
        except (TypeError, ValueError, UnicodeError, yaml.YAMLError):
            continue
    return records


def default_body(record: Any) -> str:
    """Create a minimal human-readable body for a record."""

    data = to_frontmatter(record)
    title = data.get("title") or data.get("statement") or data.get("session_id") or data.get("kind") or "Record"
    return f"# {title}\n"
