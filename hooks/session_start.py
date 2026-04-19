"""AITP SessionStart hook — inject skill based on topic status.

Runs when a new session starts. Reads the active topic's state and prints
a skill injection instruction for the agent to follow.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _find_topics_root() -> str | None:
    """Find the topics root directory by walking up from cwd."""
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


def _parse_frontmatter(path: str) -> dict:
    import re
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


def _find_active_topic(topics_root: str) -> str | None:
    """Resolve the active topic from marker or most-recent."""
    from brain.state_model import topics_dir
    td = topics_dir(topics_root)

    marker = Path(td) / ".current_topic"
    if marker.exists():
        slug = marker.read_text(encoding="utf-8").strip()
        if slug and (Path(td) / slug / "state.md").exists():
            return slug

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


_SKILL_MAP = {
    "new": "skill-explore",
    "sources_registered": "skill-intake",
    "intake_done": "skill-derive",
    "candidate_ready": "skill-validate",
    "validated": "skill-promote",
    "promoted": "skill-write",
}


def main():
    topics_root = _find_topics_root()
    if not topics_root:
        print("AITP: No topics root found. Skipping skill injection.")
        return

    topic_slug = _find_active_topic(topics_root)
    if not topic_slug:
        print("AITP: No active topic found. Start one with aitp_bootstrap_topic.")
        return

    from brain.state_model import topics_dir
    td = topics_dir(topics_root)
    state_path = os.path.join(td, topic_slug, "state.md")
    fm = _parse_frontmatter(state_path)
    status = fm.get("status", "new")
    skill = _SKILL_MAP.get(status, "skill-continuous")

    print(f"AITP: Active topic '{topic_slug}' (status: {status}).")
    print(f"AITP: Read and follow skills/{skill}.md before continuing.")


if __name__ == "__main__":
    main()
