"""AITP Compact hook — re-inject skill after context compaction.

Runs when context is compacted. Uses the same stage/posture logic as session_start
with a reminder that context was lost.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from session_start import (
    _find_topics_root,
    _find_active_topic,
    _parse_md,
)


def main():
    topics_root = _find_topics_root()
    if not topics_root:
        return

    topic_slug = _find_active_topic(topics_root)
    if not topic_slug:
        return

    from brain.state_model import topics_dir, evaluate_l1_stage
    td = topics_dir(topics_root)
    root = Path(td) / topic_slug
    fm, _ = _parse_md(root / "state.md")
    snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))

    print(
        f"AITP: Context was compacted. Resuming topic '{topic_slug}' "
        f"(stage: {snapshot.stage}, posture: {snapshot.posture}, gate: {snapshot.gate_status})."
    )
    if snapshot.required_artifact_path:
        print(f"AITP: Complete {snapshot.required_artifact_path} before advancing.")
    print(f"AITP: Read skills/{snapshot.skill}.md to restore your workflow context.")


if __name__ == "__main__":
    main()
