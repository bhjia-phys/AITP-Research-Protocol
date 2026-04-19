"""AITP Stop hook — save progress summary at session end.

Only updates the active topic (via .current_topic marker or most-recent),
not every topic in the tree.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path


def _parse_frontmatter(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _find_topics_root() -> str | None:
    cwd = os.getcwd()
    for _ in range(5):
        candidate = os.path.join(cwd, "topics")
        if os.path.isdir(candidate):
            return os.path.dirname(candidate)
        parent = os.path.dirname(cwd)
        if parent == cwd:
            break
        cwd = parent
    return os.environ.get("AITP_TOPICS_ROOT")


def _find_active_topic(topics_root: str) -> str | None:
    """Resolve the active topic from .current_topic marker or most-recent."""
    from brain.state_model import topics_dir
    td = topics_dir(topics_root)

    # Prefer explicit marker
    marker = Path(td) / ".current_topic"
    if marker.exists():
        slug = marker.read_text(encoding="utf-8").strip()
        if slug and (Path(td) / slug / "state.md").exists():
            return slug

    # Fallback: most recently updated
    best_slug = None
    best_time = ""
    if not os.path.isdir(td):
        return None
    for entry in os.listdir(td):
        state_path = os.path.join(td, entry, "state.md")
        if os.path.isfile(state_path):
            fm = _parse_frontmatter(state_path)
            updated = fm.get("updated_at", "")
            if updated > best_time:
                best_time = updated
                best_slug = entry
    return best_slug


def stop_for_topic(topics_root: str) -> None:
    """Stop hook that only touches the active topic."""
    from brain.state_model import topics_dir
    td = topics_dir(topics_root)
    slug = _find_active_topic(topics_root)
    if not slug:
        return
    state_path = Path(td) / slug / "state.md"
    if state_path.exists():
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        with open(state_path, "a", encoding="utf-8") as f:
            f.write(f"\n## Session ended {now}\n\n")


def main():
    topics_root = _find_topics_root()
    if not topics_root:
        return
    stop_for_topic(topics_root)


if __name__ == "__main__":
    main()
