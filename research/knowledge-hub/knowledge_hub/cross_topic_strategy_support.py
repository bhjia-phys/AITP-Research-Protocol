"""Cross-topic strategy memory sharing.

Provides a kernel-level registry where helpful/harmful strategy patterns
from one topic can be discovered and reused by other topics.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def shared_strategy_registry_path(kernel_root: Path) -> Path:
    return kernel_root / "shared_strategy_registry.jsonl"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def publish_strategy_to_shared_registry(
    kernel_root: Path,
    *,
    source_topic_slug: str,
    strategy_id: str,
    strategy_type: str,
    lane: str,
    outcome: str,
    summary: str,
    confidence: float,
    updated_by: str = "aitp-service",
) -> dict[str, Any]:
    """Publish a strategy pattern from a topic into the shared kernel registry."""
    path = shared_strategy_registry_path(kernel_root)
    rows = _read_jsonl(path)
    entry = {
        "strategy_id": f"shared:{source_topic_slug}:{strategy_id}",
        "source_topic_slug": source_topic_slug,
        "original_strategy_id": strategy_id,
        "strategy_type": strategy_type,
        "lane": lane,
        "outcome": outcome,
        "summary": summary,
        "confidence": confidence,
        "published_at": _now_iso(),
        "published_by": updated_by,
    }
    # Deduplicate by strategy_id
    existing_ids = {str(row.get("strategy_id") or "").strip() for row in rows}
    if entry["strategy_id"] not in existing_ids:
        rows.append(entry)
        _write_jsonl(path, rows)
    return entry


def query_shared_strategies(
    kernel_root: Path,
    *,
    requesting_topic_slug: str | None = None,
    lane: str | None = None,
    outcome: str | None = None,
    strategy_type: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Query the shared strategy registry for patterns applicable to a topic."""
    path = shared_strategy_registry_path(kernel_root)
    rows = _read_jsonl(path)
    filtered = rows
    if requesting_topic_slug:
        filtered = [
            row for row in filtered
            if str(row.get("source_topic_slug") or "") != requesting_topic_slug
        ]
    if lane:
        filtered = [
            row for row in filtered
            if str(row.get("lane") or "").strip() == lane.strip()
        ]
    if outcome:
        filtered = [
            row for row in filtered
            if str(row.get("outcome") or "").strip() == outcome.strip()
        ]
    if strategy_type:
        filtered = [
            row for row in filtered
            if str(row.get("strategy_type") or "").strip() == strategy_type.strip()
        ]
    filtered.sort(
        key=lambda row: (float(row.get("confidence") or 0.0), str(row.get("published_at") or "")),
        reverse=True,
    )
    return filtered[:limit]


def sync_topic_helpful_patterns_to_shared(
    kernel_root: Path,
    *,
    topic_slug: str,
    strategy_memory_rows: list[dict[str, Any]],
    updated_by: str = "aitp-service",
) -> dict[str, Any]:
    """Sync helpful patterns from a topic's strategy memory into the shared registry."""
    helpful_rows = [
        row for row in strategy_memory_rows
        if str(row.get("outcome") or "").strip() == "helpful"
        and float(row.get("confidence") or 0.0) >= 0.5
    ]
    published = []
    for row in helpful_rows[:5]:
        entry = publish_strategy_to_shared_registry(
            kernel_root,
            source_topic_slug=topic_slug,
            strategy_id=str(row.get("strategy_id") or ""),
            strategy_type=str(row.get("strategy_type") or ""),
            lane=str(row.get("lane") or ""),
            outcome="helpful",
            summary=str(row.get("summary") or ""),
            confidence=float(row.get("confidence") or 0.0),
            updated_by=updated_by,
        )
        published.append(entry)
    return {
        "topic_slug": topic_slug,
        "published_count": len(published),
        "published_entries": published,
    }
