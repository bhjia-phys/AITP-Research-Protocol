"""Stable Python executable selection for generated host hook commands."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


_TRANSIENT_PATH_MARKERS = (
    "/.cache/codex-runtimes/",
    "/.cache/uv/",
    "/.codex/tmp/",
    "/uv/cache/builds-v0/",
    "/.tmp/",
)


def is_transient_python_path(value: str) -> bool:
    normalized = value.replace("\\", "/").casefold()
    return any(marker in normalized for marker in _TRANSIENT_PATH_MARKERS)


def stable_python_executable() -> str:
    """Return a durable Python command for hook configs.

    Hook files can outlive the installer process. Prefer an explicit
    AITP_HOOK_PYTHON override, then a PATH-resolved Python, and avoid transient
    uv/Codex runtime interpreters when possible.
    """

    override = os.environ.get("AITP_HOOK_PYTHON")
    if override:
        return _normalize_command_path(override)

    candidates: list[str] = []
    path_python = shutil.which("python")
    if path_python:
        candidates.append(path_python)
    if sys.executable:
        candidates.append(sys.executable)
    if os.name == "nt":
        path_py = shutil.which("py")
        if path_py:
            candidates.append(path_py)

    for candidate in candidates:
        if not candidate or is_transient_python_path(candidate):
            continue
        try:
            path = Path(candidate).expanduser().resolve(strict=False)
        except OSError:
            continue
        if path.exists():
            return path.as_posix()

    return "python" if os.name == "nt" else "python3"


def _normalize_command_path(value: str) -> str:
    try:
        path = Path(value).expanduser()
    except OSError:
        return value.replace("\\", "/")
    if path.is_absolute():
        return path.as_posix()
    return value.replace("\\", "/")
