#!/usr/bin/env python3
"""Shared helpers for OpenClaw-side AITP runtime entrypoints."""

from __future__ import annotations

import json
import shlex
from datetime import datetime
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_ROOT = RESEARCH_ROOT / "adapters" / "openclaw"
ADAPTER_STATE_ROOT = ADAPTER_ROOT / "state"
KNOWLEDGE_ROOT = RESEARCH_ROOT / "knowledge-hub"
RUNTIME_ROOT = KNOWLEDGE_ROOT / "runtime"
TOPICS_ROOT = RUNTIME_ROOT / "topics"
TOPIC_INDEX_PATH = RUNTIME_ROOT / "topic_index.jsonl"
STOP_PATH = RESEARCH_ROOT.parent / "research-bot" / "state" / "STOP"
HEARTBEAT_STATE_PATH = ADAPTER_STATE_ROOT / "heartbeat_state.json"
HEARTBEAT_HISTORY_PATH = ADAPTER_STATE_ROOT / "heartbeat_history.jsonl"
ACTION_PRIORITY = {
    "ingest_execution_result": 130,
    "dispatch_execution_task": 125,
    "materialize_execution_task": 120,
    "select_validation_route": 110,
    "conformance_audit": 90,
    "literature_followup_search": 85,
    "l0_source_expansion": 80,
    "baseline_reproduction": 70,
    "await_execution_result": 65,
    "atomic_understanding": 60,
    "l4_revalidation": 50,
    "l2_promotion_review": 40,
    "skill_discovery": 35,
    "backend_extension": 30,
    "manual_followup": 20,
    "inspect_resume_state": 10,
}
RESUME_STAGE_PRIORITY = {
    "L4": 40,
    "L3": 30,
    "L2": 20,
    "L1": 10,
    "L0": 5,
}
SCRATCH_TOPIC_MARKERS = ("fixture", "smoke", "demo", "toy", "sandbox")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text((serialized + "\n") if serialized else "", encoding="utf-8")


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def relative_to_research(path: Path) -> str:
    try:
        return path.relative_to(RESEARCH_ROOT).as_posix()
    except ValueError:
        return str(path)


def quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def trim_text(text: str | None, limit: int = 2000) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 15] + "\n...[truncated]"


def topic_runtime_root(topic_slug: str) -> Path:
    return TOPICS_ROOT / topic_slug


def action_priority(action: dict) -> int:
    return ACTION_PRIORITY.get(str(action.get("action_type") or ""), 0) + (
        5 if action.get("auto_runnable") else 0
    )


def is_scratch_topic(topic_slug: str, latest_run_id: str | None = None, summary: str | None = None) -> bool:
    haystacks = [
        topic_slug.lower(),
        str(latest_run_id or "").lower(),
        str(summary or "").lower(),
    ]
    return any(marker in haystack for haystack in haystacks for marker in SCRATCH_TOPIC_MARKERS)


def runtime_topic_snapshot(topic_slug: str, index_row: dict | None = None) -> dict:
    runtime_root = topic_runtime_root(topic_slug)
    topic_state = read_json(runtime_root / "topic_state.json") or {}
    queue_rows = read_jsonl(runtime_root / "action_queue.jsonl")
    pending_rows = [row for row in queue_rows if row.get("status") == "pending"]
    auto_pending_rows = [row for row in pending_rows if row.get("auto_runnable")]
    pending_count = len(pending_rows)
    if pending_count == 0:
        pending_count = len(topic_state.get("pending_actions") or [])

    resume_stage = str(topic_state.get("resume_stage") or (index_row or {}).get("resume_stage") or "")
    latest_run_id = str(topic_state.get("latest_run_id") or (index_row or {}).get("latest_run_id") or "")
    updated_at = str(topic_state.get("updated_at") or (index_row or {}).get("updated_at") or "")
    summary = str(topic_state.get("summary") or (index_row or {}).get("summary") or "")
    scratch_topic = is_scratch_topic(topic_slug, latest_run_id, summary)

    selection_reason = (
        f"pending={pending_count}, auto_runnable={len(auto_pending_rows)}, "
        f"highest_priority={max((action_priority(row) for row in pending_rows), default=0)}, "
        f"resume_stage={resume_stage or '(unknown)'}"
    )
    if scratch_topic:
        selection_reason += "; scratch-topic penalty applied"

    return {
        "topic_slug": topic_slug,
        "resume_stage": resume_stage,
        "latest_run_id": latest_run_id,
        "updated_at": updated_at,
        "summary": summary,
        "pending_count": pending_count,
        "auto_runnable_count": len(auto_pending_rows),
        "highest_priority": max((action_priority(row) for row in pending_rows), default=0),
        "scratch_topic": scratch_topic,
        "selection_reason": selection_reason,
        "_sort_key": (
            0 if scratch_topic else 1,
            1 if pending_count > 0 else 0,
            1 if auto_pending_rows else 0,
            max((action_priority(row) for row in pending_rows), default=0),
            RESUME_STAGE_PRIORITY.get(resume_stage, 0),
            pending_count,
            updated_at,
            topic_slug,
        ),
    }


def select_active_topic() -> dict:
    rows = [row for row in read_jsonl(TOPIC_INDEX_PATH) if row.get("topic_slug")]
    if not rows:
        raise SystemExit(
            "No runtime topics are indexed. Pass --topic-slug or materialize a topic first."
        )
    snapshots = [runtime_topic_snapshot(str(row["topic_slug"]), row) for row in rows]
    snapshots.sort(key=lambda row: row["_sort_key"])
    return snapshots[-1]


def resolve_active_topic() -> str:
    return select_active_topic()["topic_slug"]


def resolve_topic_slug(topic_slug: str | None) -> str:
    resolved = topic_slug or resolve_active_topic()
    runtime_root = topic_runtime_root(resolved)
    if not runtime_root.exists():
        raise SystemExit(f"Runtime topic root does not exist: {runtime_root}")
    return resolved
