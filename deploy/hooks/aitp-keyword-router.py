#!/usr/bin/env python3
"""UserPromptSubmit hook: emit a bounded AITP topic route hint."""

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

MAX_CONTEXT_BYTES = 4096
MAX_CANDIDATES = 6
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
_GENERIC_SIGNALS = {
    "topic",
    "research",
    "current topic",
    "this topic",
    "研究",
    "科研",
    "课题",
    "继续科研",
    "继续研究",
    "继续这个",
}
AITP_TOPICS_ROOT = Path(os.environ.get("AITP_TOPICS_ROOT", "{{TOPICS_ROOT}}"))


def parse_yaml_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---", text, re.DOTALL)
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
    topics: dict[str, dict[str, str]] = {}
    v5_root = AITP_TOPICS_ROOT / ".aitp" / "topics"
    if v5_root.is_dir():
        for directory in sorted(v5_root.iterdir()):
            topic_file = directory / "topic.md"
            if directory.is_dir() and topic_file.is_file():
                topics[directory.name] = _topic_metadata(directory.name, topic_file)
    for directory in sorted(AITP_TOPICS_ROOT.iterdir()):
        state_file = directory / "state.md"
        if not directory.is_dir() or directory.name.startswith(".") or not state_file.is_file():
            continue
        legacy = _topic_metadata(directory.name, state_file)
        existing = topics.get(directory.name, {})
        topics[directory.name] = {
            "topic_id": directory.name,
            "title": existing.get("title") or legacy["title"],
            "question": legacy.get("question") or existing.get("question", ""),
            "lane": legacy.get("lane") or existing.get("lane", ""),
            "legacy_stage": legacy.get("legacy_stage") or existing.get("legacy_stage", ""),
        }
    return [topics[key] for key in sorted(topics)]


def _topic_metadata(topic_id: str, path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return _empty_topic(topic_id)
    frontmatter = parse_yaml_frontmatter(text)
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    question_match = re.search(
        r"## Research Question\s*\r?\n(.*?)(?:\r?\n\s*\r?\n|\r?\n#|$)",
        body,
        re.DOTALL,
    )
    question = _one_line(question_match.group(1) if question_match else "", 96)
    return {
        "topic_id": topic_id,
        "title": _one_line(frontmatter.get("title") or topic_id, 96),
        "question": question,
        "lane": _one_line(frontmatter.get("lane") or "", 32),
        "legacy_stage": _one_line(frontmatter.get("stage") or "", 24),
    }


def _empty_topic(topic_id: str) -> dict[str, str]:
    return {
        "topic_id": topic_id,
        "title": topic_id,
        "question": "",
        "lane": "",
        "legacy_stage": "",
    }


def rank_topics(
    message: str,
    matched_signals: list[str],
    topics: list[dict[str, str]],
) -> list[dict[str, str | int | list[str]]]:
    lowered = message.lower()
    latin_terms = {
        term
        for term in re.findall(r"[a-z0-9_+.-]+", lowered)
        if len(term) >= 3 and term not in {"the", "this", "that", "with", "from", "continue"}
    }
    ranked = []
    for topic in topics:
        haystack = " ".join(
            [topic["topic_id"], topic["title"], topic["question"], topic["lane"]]
        ).lower()
        reasons: list[str] = []
        score = 0
        if topic["topic_id"].lower() in lowered or topic["title"].lower() in lowered:
            score += 24
            reasons.append("direct_topic_match")
        for signal in matched_signals:
            if signal in _GENERIC_SIGNALS:
                continue
            if signal.lower() in haystack:
                score += 8
                reasons.append(f"signal:{signal}")
        overlaps = sorted(term for term in latin_terms if term in haystack)
        if overlaps:
            score += min(len(overlaps), 6) * 2
            reasons.append("terms:" + ",".join(overlaps[:4]))
        if score:
            ranked.append({**topic, "score": score, "reasons": reasons})
    ranked.sort(key=lambda item: (-int(item["score"]), str(item["topic_id"])))
    return ranked[:MAX_CANDIDATES]


def build_route_hint(
    message: str,
    matched_signals: list[str],
    candidates: list[dict[str, str | int | list[str]]],
) -> str:
    base = AITP_TOPICS_ROOT.as_posix()
    prefix = [
        "AITP ROUTE HINT (orientation only; not evidence or claim trust).",
        "matched_signals: " + ", ".join(matched_signals[:10]),
        f"canonical_base: {base}",
        "candidate_topics:",
    ]
    suffix = [
        "compact_entrypoints:",
        "- mcp__aitp__aitp_v5_codex_autoroute(base='<canonical_base>', request_summary='<request>')",
        "- mcp__aitp__aitp_v5_codex_enter(base='<canonical_base>', topics=['<topic-id>'], request_summary='<request>')",
        "- mcp__aitp__aitp_v5_codex_expand(base='<canonical_base>', session_id='<session-id>', expansion='context_pack' or 'record_refs')",
        "Select one topic/session before expansion. Exact-expand typed refs before evidence, validation, or trust conclusions.",
        "The canonical research/aitp-topics/.aitp store is authoritative; do not read or edit topic-state files directly.",
    ]
    candidate_lines: list[str] = []
    for candidate in candidates:
        reasons = candidate.get("reasons") or []
        reason = ",".join(str(item) for item in reasons[:2])
        line = (
            f"- topic_id={_one_line(candidate.get('topic_id'), 80)}"
            f" | title={_one_line(candidate.get('title'), 96)}"
            f" | reason={_one_line(reason, 96)}"
        )
        question = _one_line(candidate.get("question"), 96)
        if question:
            line += f" | question={question}"
        tentative = "\n".join([*prefix, *candidate_lines, line, *suffix]) + "\n"
        if len(tentative.encode("utf-8")) > MAX_CONTEXT_BYTES:
            break
        candidate_lines.append(line)
    if not candidate_lines:
        candidate_lines.append("- none; use autoroute and ask before creating or switching topics")
    context = "\n".join([*prefix, *candidate_lines, *suffix]) + "\n"
    if len(context.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise RuntimeError("fixed AITP route hint exceeds byte budget")
    return context


def _one_line(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _read_input() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            fixed = re.sub(r'\\([^"\\/bfnrtu])', r"\\\\\1", raw)
            fixed = re.sub(r"\\u(?![0-9a-fA-F]{4})", r"\\\\u", fixed)
            return json.loads(fixed)
        except json.JSONDecodeError:
            return {}


def main() -> int:
    data = _read_input()
    user_message = str(data.get("user_message", ""))
    if not user_message:
        return 0
    lowered = user_message.lower()
    matched = [keyword for keyword in AITP_KEYWORDS if keyword.lower() in lowered]
    if not matched:
        return 0
    candidates = rank_topics(user_message, matched, scan_topics())
    context = build_route_hint(user_message, matched, candidates)
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
