"""AITP Compact hook — re-inject skill after context compaction.

Runs when context is compacted. Same logic as session_start but
with a reminder that context was lost.
"""

from __future__ import annotations

import os
from pathlib import Path

from session_start import _find_topics_root, _find_active_topic, _parse_frontmatter, _SKILL_MAP


def main():
    topics_root = _find_topics_root()
    if not topics_root:
        return

    topic_slug = _find_active_topic(topics_root)
    if not topic_slug:
        return

    from brain.state_model import topics_dir
    td = topics_dir(topics_root)
    state_path = os.path.join(td, topic_slug, "state.md")
    fm = _parse_frontmatter(state_path)
    status = fm.get("status", "new")
    skill = _SKILL_MAP.get(status, "skill-continuous")

    print(f"AITP: Context was compacted. Resuming topic '{topic_slug}' (status: {status}).")
    print(f"AITP: Read skills/{skill}.md to restore your workflow context.")
    print(f"AITP: Also read topics/{topic_slug}/state.md for the full picture.")


if __name__ == "__main__":
    main()
