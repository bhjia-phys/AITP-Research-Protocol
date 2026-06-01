"""Small typed-object store for AITP v5 Markdown artifacts."""

from __future__ import annotations

from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from brain.v5.markdown import read_md, write_md

T = TypeVar("T")


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
        allowed = {field.name for field in fields(cls)}
        fm = {key: value for key, value in fm.items() if key in allowed}
    return cls(**fm)


def list_records(directory: str | Path, cls: type[T]) -> list[T]:
    """Read all Markdown records in a directory."""

    root = Path(directory)
    if not root.exists():
        return []
    return [read_record(path, cls) for path in sorted(root.glob("*.md"))]


def list_valid_records(directory: str | Path, cls: type[T]) -> list[T]:
    """Read valid Markdown records and skip malformed legacy leftovers."""

    root = Path(directory)
    if not root.exists():
        return []
    records: list[T] = []
    for path in sorted(root.glob("*.md")):
        try:
            records.append(read_record(path, cls))
        except (TypeError, ValueError):
            continue
    return records


def default_body(record: Any) -> str:
    """Create a minimal human-readable body for a record."""

    data = to_frontmatter(record)
    title = data.get("title") or data.get("statement") or data.get("session_id") or data.get("kind") or "Record"
    return f"# {title}\n"
