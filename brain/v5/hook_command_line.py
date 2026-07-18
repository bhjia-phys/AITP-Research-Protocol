"""Portable command rendering for generated host hook configuration."""

from __future__ import annotations

import os
import shlex
import subprocess


def render_hook_command(argv: list[str]) -> str:
    if not argv or any(not isinstance(item, str) or not item for item in argv):
        raise ValueError("hook command argv must contain non-empty strings")
    if os.name == "nt":
        return subprocess.list2cmdline(argv)
    return " ".join(shlex.quote(item) for item in argv)


__all__ = ["render_hook_command"]
