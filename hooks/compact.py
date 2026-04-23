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
    _find_workspace_root,
    _find_topics_root,
    _find_active_topic,
    _hooks_disabled,
    _parse_md,
)


def main():
    workspace = _find_workspace_root()

    if _hooks_disabled(workspace):
        return

    topics_root = _find_topics_root()
    if not topics_root:
        return

    topic_slug = _find_active_topic(topics_root)
    if not topic_slug:
        return

    from brain.state_model import (
        topics_dir, evaluate_l0_stage, evaluate_l1_stage, evaluate_l3_stage,
    )
    td = topics_dir(topics_root)
    root = Path(td) / topic_slug
    fm, _ = _parse_md(root / "state.md")
    stage = str(fm.get("stage", "L0"))

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    elif stage == "L0":
        snapshot = evaluate_l0_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    else:
        snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))

    subplane_info = f", subplane: {snapshot.l3_subplane}" if snapshot.l3_subplane else ""
    print(
        f"AITP: Context was compacted. Resuming topic '{topic_slug}' "
        f"(stage: {snapshot.stage}, posture: {snapshot.posture}, gate: {snapshot.gate_status}{subplane_info})."
    )
    if snapshot.required_artifact_path:
        print(f"AITP: Complete {snapshot.required_artifact_path} before advancing.")
    print(f"AITP: Read skills/{snapshot.skill}.md to restore your workflow context.")


if __name__ == "__main__":
    main()
