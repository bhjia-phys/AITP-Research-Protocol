"""Lightweight trace events for AITP v5 harness audits."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TraceEvent:
    event_id: str
    session_id: str
    topic_id: str
    event_type: str
    risk_level: str
    claim_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    kind: str = "trace_event"


def append_trace_event(path: str | Path, event: TraceEvent) -> None:
    """Append one JSONL trace event."""

    trace_path = Path(path)
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def read_trace_events(path: str | Path) -> list[TraceEvent]:
    """Read JSONL trace events."""

    trace_path = Path(path)
    if not trace_path.exists():
        return []
    events: list[TraceEvent] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(TraceEvent(**json.loads(line)))
    return events
