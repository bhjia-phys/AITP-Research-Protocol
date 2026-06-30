#!/usr/bin/env python3
"""UserPromptSubmit hook: detect AITP requests and inject v5 routing context.

The hook is only a router/reminder. It never updates AITP state.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

AITP_KEYWORDS = [
    "aitp",
    "topic",
    "research",
    "derivation",
    "claim",
    "evidence",
    "validation",
    "paper",
    "literature",
    "proof",
    "calculation",
    "theoretical physics",
    "current topic",
    "this topic",
    "ads",
    "cft",
    "boundary",
    "matter",
    "qsgw",
    "gw",
    "librpa",
    "green function",
    "von neumann",
    "研究",
    "科研",
    "课题",
    "继续科研",
    "继续研究",
    "继续这个",
    "推导",
    "文献",
    "论文",
    "验证",
    "证据",
    "理论物理",
    "量子引力",
    "全息",
    "边界",
    "物质",
    "拓扑",
    "混沌",
    "格林函数",
    "测量诱导",
    "自能",
]

AITP_TOPICS_ROOT = Path(os.environ.get("AITP_TOPICS_ROOT", "{{TOPICS_ROOT}}"))


def parse_yaml_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    frontmatter: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def scan_topics() -> list[dict[str, str]]:
    if not AITP_TOPICS_ROOT.is_dir():
        return []
    topics: list[dict[str, str]] = []
    for directory in sorted(AITP_TOPICS_ROOT.iterdir()):
        if not directory.is_dir():
            continue
        state_file = directory / "state.md"
        topic_file = AITP_TOPICS_ROOT / ".aitp" / "topics" / directory.name / "topic.md"
        if not state_file.exists() and not topic_file.exists():
            continue
        try:
            text = state_file.read_text(encoding="utf-8") if state_file.exists() else topic_file.read_text(encoding="utf-8")
            frontmatter = parse_yaml_frontmatter(text)
            body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
            question_match = re.search(r"## Research Question\s*\n(.*?)(?:\n\n|\n#|$)", body, re.DOTALL)
            question = question_match.group(1).strip() if question_match else ""
            memory_file = directory / "MEMORY.md"
            memory_text = ""
            if memory_file.exists():
                try:
                    memory_raw = memory_file.read_text(encoding="utf-8")
                    memory_text = re.sub(r"^---.*?---\s*", "", memory_raw, flags=re.DOTALL).strip()
                except Exception:
                    pass
            topics.append(
                {
                    "slug": directory.name,
                    "title": frontmatter.get("title", directory.name),
                    "legacy_stage": frontmatter.get("stage", "unknown"),
                    "lane": frontmatter.get("lane", ""),
                    "question": question[:120],
                    "memory": memory_text,
                }
            )
        except Exception:
            topics.append(
                {
                    "slug": directory.name,
                    "title": directory.name,
                    "legacy_stage": "unknown",
                    "lane": "",
                    "question": "",
                    "memory": "",
                }
            )
    return topics


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r"\\\\\1", raw)
            fixed = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", fixed)
            data = json.loads(fixed)
        except json.JSONDecodeError:
            return 0

    user_message = str(data.get("user_message", ""))
    if not user_message:
        return 0

    msg_lower = user_message.lower()
    matched = [keyword for keyword in AITP_KEYWORDS if keyword.lower() in msg_lower]
    if not matched:
        return 0

    topics = scan_topics()
    topic_lines = []
    topic_memories = []
    for topic in topics:
        line = (
            f"  - slug: {topic['slug']}  |  title: {topic['title']}  |  "
            f"legacy_stage: {topic['legacy_stage']}  |  lane: {topic['lane']}"
        )
        if topic["question"]:
            line += f"\n    question: {topic['question']}"
        topic_lines.append(line)
        if topic.get("memory"):
            topic_memories.append(f"### Topic: {topic['slug']}\n{topic['memory']}")

    topics_block = "\n".join(topic_lines) if topic_lines else "  (no topics found)"
    memories_block = "\n\n---\n\n".join(topic_memories) if topic_memories else ""

    reminder = (
        "AITP RESEARCH REQUEST DETECTED. Keywords matched: "
        + ", ".join(matched)
        + "\n\n"
        + "EXISTING AITP TOPICS:\n"
        + topics_block
        + "\n\n"
    )
    if memories_block:
        reminder += (
            "TOPIC MEMORIES (MUST follow these conventions for the matched topic):\n"
            + memories_block
            + "\n\n"
        )
    reminder += (
        "AITP V5 INSTRUCTIONS (follow exactly):\n"
        "1. Match the user's request to ONE topic above by comparing title/question.\n"
        "2. Do not treat legacy_stage/gate fields as v5 truth; they are orientation only.\n"
        "3. If a v5 session id is known, call mcp__aitp__aitp_v5_codex_enter("
        f"base='{AITP_TOPICS_ROOT.as_posix()}', session_id='<session-id>', request_summary='<user request>').\n"
        "4. Expand through mcp__aitp__aitp_v5_codex_expand("
        f"base='{AITP_TOPICS_ROOT.as_posix()}', session_id='<session-id>', expansion='brief' or 'relation_map') only when needed.\n"
        "5. If only a legacy slug is known, call mcp__aitp__aitp_v5_codex_enter("
        f"base='{AITP_TOPICS_ROOT.as_posix()}', topics=['<topic-slug>'], request_summary='<user request>') and choose a recovery_ready session before research.\n"
        "6. If no topic matches, ask before switching to a full-kernel maintenance surface to create or migrate topic/claim/session state.\n"
        "7. Do NOT create a duplicate topic if one already matches.\n"
        "8. Do NOT read or edit AITP topic-state files directly with Read/Grep/Glob/Edit/MultiEdit.\n"
        "9. Use MCP typed tools for research state; use aitp-v5 only as a CLI diagnostic/fallback.\n"
        "10. Record durable scientific content through typed v5 records; summaries, relation maps, and hooks are orientation only.\n"
        "11. Do not confuse root .aitp or Hakimi-local state with the canonical research/aitp-topics/.aitp store."
    )

    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": reminder,
        }
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
