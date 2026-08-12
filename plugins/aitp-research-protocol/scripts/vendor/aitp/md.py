"""Record-file format and safe writes."""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


PROMPT_MARKER = "<!-- aitp:"


class AITPError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now_utc() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    return f"---\n{dump_yaml(frontmatter)}\n---\n\n{body.strip()}\n"


def parse_markdown(path: Path) -> tuple[dict[str, Any], str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AITPError("unreadable_record", f"{path}: {exc}") from exc
    if not text.startswith("---\n"):
        raise AITPError("malformed_record", f"{path}: missing YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise AITPError("malformed_record", f"{path}: unclosed YAML frontmatter")
    try:
        frontmatter = yaml.safe_load(text[4:marker]) or {}
    except yaml.YAMLError as exc:
        raise AITPError("malformed_record", f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise AITPError("malformed_record", f"{path}: frontmatter must be a map")
    return frontmatter, text[marker + 5 :].lstrip("\n"), text


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _section_content(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)"
    )
    match = pattern.search(body)
    if not match:
        return ""
    content = re.sub(r"<!--\s*aitp:.*?-->", "", match.group(1), flags=re.S)
    return content.strip()
