"""Stable public API over the private AITP Lite engine."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import engine as _engine


def _precise_now_utc() -> str:
    """Keep microseconds so immediate consecutive Entries remain ordered."""
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


# The engine resolves this global at call time. Keep this policy in the public
# facade until the engine becomes an implementation-independent package.
_engine.now_utc = _precise_now_utc

from .engine import (  # noqa: E402
    AITPError,
    atomic_write,
    enter_workspace,
    init_workspace,
    parse_markdown,
    prepare_entry as _prepare_entry,
    prepare_note,
    render_markdown,
    resolve_root,
    save_entry,
    save_note,
)
from .engine import _canonical_entries, parse_markdown as _parse_markdown  # noqa: E402

__all__ = [
    "AITPError",
    "atomic_write",
    "enter_workspace",
    "init_workspace",
    "parse_markdown",
    "prepare_entry",
    "prepare_note",
    "render_markdown",
    "save_entry",
    "save_note",
]


def prepare_entry(
    cwd: str | Path,
    kind: str,
    authority: str,
    *,
    created_by: str = "agent:unknown",
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Prepare an Entry, preferring an already-saved canonical retry target."""
    if idempotency_key:
        root = resolve_root(cwd)
        for path in _canonical_entries(root):
            try:
                frontmatter, _, _ = _parse_markdown(path)
            except AITPError:
                continue
            if frontmatter.get("idempotency_key") == idempotency_key:
                return {
                    "status": "existing",
                    "path": str(path.relative_to(root)),
                    "idempotency_key": idempotency_key,
                }
    return _prepare_entry(
        cwd,
        kind,
        authority,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
