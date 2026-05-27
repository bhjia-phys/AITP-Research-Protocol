"""vNext lane-specific exemplar records and closure manifest."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from brain.v5.ids import prefixed_id
from brain.v5.markdown import write_md
from brain.v5.paths import WorkspacePaths

REQUIRED_LANES = ("toy_numeric", "semi_formal_theory", "code_backed_algorithm")
_LANES = set(REQUIRED_LANES)
_STATUSES = {"candidate", "accepted", "needs_review"}


@dataclass
class LaneExemplarRecord:
    exemplar_id: str
    topic_id: str
    lane: str
    title: str
    summary: str
    claim_id: str = ""
    run_id: str = ""
    gates_demonstrated: list[str] = field(default_factory=list)
    artifact_refs: list[str] = field(default_factory=list)
    trust_boundary: str = ""
    source_refs: list[str] = field(default_factory=list)
    status: str = "candidate"
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = True
    can_update_claim_trust: bool = False
    kind: str = "lane_exemplar"


def record_lane_exemplar(
    ws: WorkspacePaths,
    *,
    topic_id: str,
    lane: str,
    title: str,
    summary: str,
    claim_id: str = "",
    run_id: str = "",
    gates_demonstrated: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    trust_boundary: str = "",
    source_refs: list[str] | None = None,
    status: str = "candidate",
) -> LaneExemplarRecord:
    """Record a vNext lane exemplar without making it scientific evidence."""

    if lane not in _LANES:
        raise ValueError(f"lane must be one of {sorted(_LANES)}")
    if status not in _STATUSES:
        raise ValueError(f"status must be one of {sorted(_STATUSES)}")
    record = LaneExemplarRecord(
        exemplar_id=prefixed_id("lane-exemplar", f"{topic_id}:{lane}:{title}", max_slug=72),
        topic_id=topic_id,
        lane=lane,
        title=title,
        summary=summary,
        claim_id=claim_id,
        run_id=run_id,
        gates_demonstrated=gates_demonstrated or [],
        artifact_refs=artifact_refs or [],
        trust_boundary=trust_boundary,
        source_refs=source_refs or [],
        status=status,
    )
    runtime_dir = _runtime_dir(ws, topic_id)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    payload = asdict(record)
    _append_jsonl(runtime_dir / "lane_exemplars.jsonl", payload)
    write_md(
        runtime_dir / "lane_exemplars" / f"{record.exemplar_id}.md",
        payload,
        _lane_exemplar_body(record),
    )
    return record


def load_lane_exemplars(ws: WorkspacePaths, topic_id: str, *, limit: int = 6) -> dict[str, Any]:
    """Load topic-local lane exemplars for briefs and status surfaces."""

    items = [_brief_item(item) for item in _read_topic_exemplars(ws, topic_id)]
    items = items[-limit:]
    return {
        "present": bool(items),
        "items": items,
        "required_lanes": list(REQUIRED_LANES),
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def build_lane_exemplar_manifest(ws: WorkspacePaths) -> dict[str, Any]:
    """Return a workspace-level vNext Phase 5 lane exemplar closure manifest."""

    items = []
    topics_dir = ws.root / "topics"
    if topics_dir.exists():
        for topic_dir in sorted(path for path in topics_dir.iterdir() if path.is_dir()):
            items.extend(_read_topic_exemplars(ws, topic_dir.name))
    lane_status_counts = {lane: {} for lane in REQUIRED_LANES}
    for item in items:
        lane = str(item.get("lane") or "")
        status = str(item.get("status") or "")
        if lane in lane_status_counts and status:
            lane_status_counts[lane][status] = lane_status_counts[lane].get(status, 0) + 1
    covered_lanes = [
        lane
        for lane in REQUIRED_LANES
        if any(item.get("lane") == lane and item.get("status") == "accepted" for item in items)
    ]
    missing_lanes = [lane for lane in REQUIRED_LANES if lane not in covered_lanes]
    return {
        "kind": "lane_exemplar_manifest",
        "required_lanes": list(REQUIRED_LANES),
        "covered_lanes": covered_lanes,
        "missing_lanes": missing_lanes,
        "lane_status_counts": lane_status_counts,
        "exemplar_count": len(items),
        "items": [_brief_item(item) for item in items],
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _read_topic_exemplars(ws: WorkspacePaths, topic_id: str) -> list[dict[str, Any]]:
    path = _runtime_dir(ws, topic_id) / "lane_exemplars.jsonl"
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def _brief_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "exemplar_id": str(item.get("exemplar_id") or ""),
        "topic_id": str(item.get("topic_id") or ""),
        "lane": str(item.get("lane") or ""),
        "title": str(item.get("title") or ""),
        "summary": str(item.get("summary") or ""),
        "claim_id": str(item.get("claim_id") or ""),
        "run_id": str(item.get("run_id") or ""),
        "gates_demonstrated": list(item.get("gates_demonstrated") or []),
        "artifact_refs": list(item.get("artifact_refs") or []),
        "trust_boundary": str(item.get("trust_boundary") or ""),
        "status": str(item.get("status") or ""),
        "orientation_only": True,
    }


def _lane_exemplar_body(record: LaneExemplarRecord) -> str:
    return (
        "# Lane Exemplar\n\n"
        f"Lane: {record.lane}\n\n"
        f"Title: {record.title}\n\n"
        f"Summary: {record.summary}\n\n"
        f"Trust boundary: {record.trust_boundary or 'Workflow exemplar only; not claim evidence.'}\n\n"
        "Gates demonstrated:\n"
        f"{_bullets(record.gates_demonstrated)}\n\n"
        "Artifacts:\n"
        f"{_bullets(record.artifact_refs)}\n"
    )


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) if values else "- None"


def _runtime_dir(ws: WorkspacePaths, topic_id: str) -> Path:
    return ws.topic_dir(topic_id) / "runtime"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
