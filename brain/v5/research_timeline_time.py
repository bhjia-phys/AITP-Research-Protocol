"""Timestamp extraction for indexed research timeline records."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def event_time(
    path: Path,
    record: Any,
    frontmatter: dict[str, Any],
) -> tuple[str, str, float]:
    for key in ("timestamp", "updated_at", "created_at", "captured_at", "acquired_at"):
        value = _time_value(frontmatter.get(key))
        if value:
            return value, key, _sort_time(value, path)
    metadata = frontmatter.get("metadata")
    if isinstance(metadata, dict):
        for key in ("timestamp", "updated_at", "created_at", "captured_at", "acquired_at"):
            value = _time_value(metadata.get(key))
            if value:
                return value, f"metadata.{key}", _sort_time(value, path)
    runtime = frontmatter.get("runtime_environment")
    if isinstance(runtime, dict):
        for key in ("timestamp", "captured_at", "created_at"):
            value = _time_value(runtime.get(key))
            if value:
                return value, f"runtime_environment.{key}", _sort_time(value, path)
    for key in ("timestamp", "acquired_at"):
        value = _time_value(getattr(record, key, ""))
        if value:
            return value, key, _sort_time(value, path)
    mtime = path.stat().st_mtime
    return datetime.fromtimestamp(mtime, timezone.utc).isoformat(), "file_mtime", mtime


def _time_value(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else ""


def _sort_time(value: str, path: Path) -> float:
    text = str(value or "").strip()
    if text:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
