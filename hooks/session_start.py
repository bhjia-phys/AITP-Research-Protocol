"""AITP SessionStart hook — inject skill based on topic stage/posture.

Runs when a new session starts. Reads the active topic's state and prints
a stage/posture-aware skill injection instruction for the agent to follow.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


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
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm


def _parse_md(path: Path) -> tuple[dict[str, Any], str]:
    """Parse markdown with YAML frontmatter."""
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    import yaml
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2)


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


def main():
    topics_root = _find_topics_root()
    if not topics_root:
        print("AITP: No topics root found. Skipping skill injection.")
        return

    topic_slug = _find_active_topic(topics_root)
    if not topic_slug:
        print("AITP: No active topic found. Start one with aitp_bootstrap_topic.")
        return

    from brain.state_model import (
        topics_dir, evaluate_l1_stage, evaluate_l3_stage,
        get_tool_catalog, get_pattern_b_instructions,
    )
    td = topics_dir(topics_root)
    root = Path(td) / topic_slug
    fm, _ = _parse_md(root / "state.md")
    stage = str(fm.get("stage", "L1"))

    if stage == "L3":
        snapshot = evaluate_l3_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))
    else:
        snapshot = evaluate_l1_stage(_parse_md, root, lane=fm.get("lane", "unspecified"))

    subplane_info = f", subplane: {snapshot.l3_subplane}" if snapshot.l3_subplane else ""
    print(
        f"AITP: Active topic '{topic_slug}' "
        f"(stage: {snapshot.stage}, posture: {snapshot.posture}, gate: {snapshot.gate_status}{subplane_info})."
    )
    if snapshot.required_artifact_path:
        print(f"AITP: Fill {snapshot.required_artifact_path} before advancing.")
    print(f"AITP: MANDATORY — read and follow skills/{snapshot.skill}.md before continuing.")

    # Progressive-disclosure tool catalog with integration patterns.
    # Pattern A: load on demand  |  Pattern B: invoke at checkpoint  |  Pattern C: already in skill
    posture_key = snapshot.l3_subplane or snapshot.posture
    catalog = get_tool_catalog(snapshot.stage, posture_key)
    if catalog:
        pattern_a = [(n, d) for n, d, p in catalog if p == "A"]
        pattern_b = [(n, d) for n, d, p in catalog if p == "B"]
        pattern_c = [(n, d) for n, d, p in catalog if p == "C"]
        if pattern_b:
            print("AITP: INVOKE at checkpoint (Pattern B — load before discussion rounds):")
            for name, desc in pattern_b:
                print(f"  - {name} — {desc}")
        if pattern_a:
            print("AITP: Available on demand (Pattern A — load with Skill or ToolSearch when needed):")
            for name, desc in pattern_a:
                print(f"  - {name} — {desc}")
        if pattern_c:
            print("AITP: Already embedded in current skill (Pattern C):")
            for name, desc in pattern_c:
                print(f"  - {name} — {desc}")

    # Pattern B explicit invoke instructions
    b_instructions = get_pattern_b_instructions(snapshot.stage, posture_key)
    for tool_name, instruction in b_instructions:
        print(f"AITP: PATTERN-B [{tool_name}]: {instruction}")


if __name__ == "__main__":
    main()
