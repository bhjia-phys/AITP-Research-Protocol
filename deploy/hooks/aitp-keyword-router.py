#!/usr/bin/env python3
"""UserPromptSubmit hook: detect AITP keywords, list existing topics, inject context.

When AITP keywords are detected in the user's message, this hook:
1. Scans the legacy AITP topics directory for topic slugs and titles.
2. Injects a v5-safe orientation list so the agent can match the request.
3. Reminds the agent to bind or migrate to a v5 session before research.
"""

import json
import os
import re
import sys
from pathlib import Path

AITP_KEYWORDS = [
    "aitp",
    "topic",
    "研究",
    "推导",
    "文献",
    "课题",
    "继续研究",
    "科研",
    "research",
    "derivation",
    "继续这个",
    "current topic",
    "this topic",
    "拓扑",
    "混沌",
    "量子引力",
    "von neumann",
    "测量诱导",
    "自能",
    "green function",
    "格林函数",
]

AITP_TOPICS_ROOT = Path(os.environ.get("AITP_TOPICS_ROOT", "{{TOPICS_ROOT}}"))


def parse_yaml_frontmatter(text: str) -> dict:
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            key, _, val = line.partition(':')
            val = val.strip().strip('"').strip("'")
            fm[key.strip()] = val
    return fm


def scan_topics() -> list[dict]:
    if not AITP_TOPICS_ROOT.is_dir():
        return []
    topics = []
    for d in sorted(AITP_TOPICS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        state_file = d / "state.md"
        if not state_file.exists():
            continue
        try:
            text = state_file.read_text(encoding="utf-8")
            fm = parse_yaml_frontmatter(text)
            body = re.sub(r'^---.*?---\s*', '', text, flags=re.DOTALL)
            question_match = re.search(r'## Research Question\s*\n(.*?)(?:\n\n|\n#|$)', body, re.DOTALL)
            question = question_match.group(1).strip() if question_match else ""
            memory_file = d / "MEMORY.md"
            memory_text = ""
            if memory_file.exists():
                try:
                    memory_raw = memory_file.read_text(encoding="utf-8")
                    memory_text = re.sub(r'^---.*?---\s*', '', memory_raw, flags=re.DOTALL).strip()
                except Exception:
                    pass
            topics.append({
                "slug": d.name,
                "title": fm.get("title", d.name),
                "legacy_stage": fm.get("stage", "unknown"),
                "lane": fm.get("lane", ""),
                "question": question[:120],
                "memory": memory_text,
            })
        except Exception:
            topics.append({"slug": d.name, "title": d.name, "legacy_stage": "unknown", "lane": "", "question": "", "memory": ""})
    return topics


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r'\\\\\1', raw)
            fixed = re.sub(r'\\u(?![0-9a-fA-F]{4})', r'\\\\u', fixed)
            data = json.loads(fixed)
        except json.JSONDecodeError:
            return 0

    user_message = data.get("user_message", "")
    if not user_message:
        return 0

    msg_lower = user_message.lower()
    matched = [kw for kw in AITP_KEYWORDS if kw in msg_lower]

    if not matched:
        return 0

    topics = scan_topics()

    topic_lines = []
    topic_memories = []
    for t in topics:
        line = f"  - slug: {t['slug']}  |  title: {t['title']}  |  legacy_stage: {t['legacy_stage']}  |  lane: {t['lane']}"
        if t['question']:
            line += f"\n    question: {t['question']}"
        topic_lines.append(line)
        if t.get('memory'):
            topic_memories.append(f"### Topic: {t['slug']}\n{t['memory']}")

    topics_block = "\n".join(topic_lines) if topic_lines else "  (no topics found)"
    memories_block = "\n\n---\n\n".join(topic_memories) if topic_memories else ""

    reminder = (
        "AITP RESEARCH REQUEST DETECTED. Keywords matched: " + ", ".join(matched) + "\n\n"
        "EXISTING AITP TOPICS:\n" + topics_block + "\n\n"
    )

    if memories_block:
        reminder += (
            "TOPIC MEMORIES (MUST follow these conventions for the matched topic):\n"
            + memories_block + "\n\n"
        )

    reminder += (
        "AITP V5 INSTRUCTIONS (follow exactly):\n"
        "1. Match the user's request to ONE of the topics above by comparing title/question.\n"
        "2. Do not treat legacy_stage/gate fields as v5 truth; they are orientation only.\n"
        "3. If a v5 session id is known, call mcp__aitp__aitp_v5_get_execution_brief("
        f"base='{AITP_TOPICS_ROOT.as_posix()}', session_id='<session-id>').\n"
        "4. If only a legacy slug is known, migrate or bind v5 state before research.\n"
        "5. If no topic matches, create a v5 topic/claim/session.\n"
        "6. Do NOT create a duplicate topic if one already matches.\n"
        "5. Do NOT read AITP topic files directly with Read/Grep/Glob — use MCP tools only.\n"
        "8. Record durable scientific content through typed v5 records; summaries and hooks are orientation only."
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
