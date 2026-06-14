"""Shared MCP base-path resolution for AITP v5 tools."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_workspace_base(base: str) -> Path:
    """Resolve common agent-provided AITP paths to the v5 topics root."""

    env_base = _env_topics_root()
    raw = Path(base).expanduser() if str(base or "").strip() else env_base or Path(".")
    if raw.name == ".aitp":
        if env_base is not None:
            env_store = env_base / ".aitp"
            if _same_path(raw, env_store):
                return env_base
            if not _same_path(raw, env_base):
                return env_base
        nested_topics = raw.parent / "research" / "aitp-topics"
        if _looks_like_v5_base(nested_topics):
            return nested_topics
        return raw.parent if _looks_like_v5_store(raw) else raw
    nested_topics = raw / "research" / "aitp-topics"
    if _looks_like_v5_base(nested_topics):
        return nested_topics
    if _looks_like_v5_store(raw):
        return raw.parent
    if _looks_like_v5_base(raw):
        return raw
    if env_base is not None and _looks_like_v5_base(env_base):
        return env_base
    return raw


def _env_topics_root() -> Path | None:
    value = os.environ.get("AITP_TOPICS_ROOT", "").strip()
    return Path(value).expanduser() if value else None


def _looks_like_v5_base(path: Path) -> bool:
    store = path / ".aitp"
    return (store / "workspace.md").exists() or (store / "topics").exists() or (store / "registry").exists()


def _looks_like_v5_store(path: Path) -> bool:
    return path.name == ".aitp" and (
        (path / "workspace.md").exists() or (path / "topics").exists() or (path / "registry").exists()
    )


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()
