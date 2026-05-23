"""Markdown plus YAML frontmatter persistence for AITP v5."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_DELIMITER = "---"


def read_md(path: str | Path) -> tuple[dict[str, Any], str]:
    """Read a Markdown file with optional YAML frontmatter."""

    p = Path(path)
    if not p.exists():
        return {}, ""
    text = p.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        frontmatter_text, body = _split_frontmatter(text)
        if frontmatter_text is not None:
            fm = yaml.safe_load(frontmatter_text) or {}
            return dict(fm), body
    return {}, text


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split YAML frontmatter on a delimiter line only."""

    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        return None, text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_DELIMITER:
            frontmatter_text = "".join(lines[1:index])
            body = "".join(lines[index + 1 :]).lstrip("\n")
            return frontmatter_text, body
    return None, text


def render_md(frontmatter: dict[str, Any], body: str) -> str:
    """Render frontmatter and body to Markdown text."""

    yaml_text = yaml.safe_dump(
        dict(frontmatter),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()
    clean_body = body.lstrip("\n")
    return f"---\n{yaml_text}\n---\n{clean_body}"


def write_text_atomic(path: str | Path, text: str) -> None:
    """Atomically write text using os.replace."""

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(p.parent),
        delete=False,
        newline="\n",
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, p)


def write_md(path: str | Path, frontmatter: dict[str, Any], body: str) -> None:
    """Write a Markdown file with YAML frontmatter."""

    write_text_atomic(path, render_md(frontmatter, body))
