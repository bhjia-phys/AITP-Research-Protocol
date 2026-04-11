from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def research_trajectory_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "research_trajectory.active.json",
        "note": runtime_root / "research_trajectory.active.md",
    }


def empty_research_trajectory(*, topic_slug: str, updated_by: str) -> dict[str, Any]:
    return {
        "artifact_kind": "research_trajectory",
        "topic_slug": topic_slug,
        "status": "absent",
        "trajectory_count": 0,
        "latest_run_id": "",
        "latest_summary": "",
        "trajectory_summaries": [],
        "related_topic_slugs": [],
        "recent_related_topic_slugs": [],
        "memory_ids": [],
        "summary": "No research trajectory is currently recorded for this topic.",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def load_research_trajectory(
    runtime_root: Path,
    *,
    topic_slug: str,
    updated_by: str = "aitp-service",
) -> dict[str, Any] | None:
    json_path = research_trajectory_paths(runtime_root)["json"]
    if not json_path.exists():
        return None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    payload = {
        **empty_research_trajectory(topic_slug=topic_slug, updated_by=updated_by),
        **payload,
    }
    payload["topic_slug"] = str(payload.get("topic_slug") or topic_slug)
    return payload


def derive_research_trajectory(
    self,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in self._load_collaborator_memory_rows()
        if self._collaborator_memory_matches_topic(row, topic_slug)
        and str(row.get("memory_kind") or "").strip() == "trajectory"
    ]
    primary_rows = [
        row for row in rows if str(row.get("topic_slug") or "").strip() == topic_slug
    ]
    related_rows = [
        row for row in rows if str(row.get("topic_slug") or "").strip() != topic_slug
    ]
    ordered_rows = primary_rows + related_rows
    trajectory_summaries = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in ordered_rows]
    )
    related_topic_slugs = self._dedupe_strings(
        [
            str(slug).strip()
            for row in rows
            for slug in (row.get("related_topic_slugs") or [])
            if str(slug).strip() and str(slug).strip() != topic_slug
        ]
    )
    recent_related_topic_slugs = self._dedupe_strings(
        [
            str(row.get("topic_slug") or "").strip()
            for row in self.recent_topics(limit=25)
            if str(row.get("topic_slug") or "").strip() in related_topic_slugs
        ]
    )
    latest_run_id = next(
        (
            str(row.get("run_id") or "").strip()
            for row in ordered_rows
            if str(row.get("run_id") or "").strip()
        ),
        "",
    )
    latest_summary = trajectory_summaries[0] if trajectory_summaries else ""
    status = "available" if rows else "absent"
    summary = (
        f"{len(rows)} trajectory signal(s) connect `{topic_slug}` across {len(related_topic_slugs)} related topic(s). Latest trajectory: {latest_summary}"
        if rows
        else "No research trajectory is currently recorded for this topic."
    )
    updated_at = str(ordered_rows[0].get("recorded_at") or "").strip() if ordered_rows else _now_iso()
    return {
        "artifact_kind": "research_trajectory",
        "topic_slug": topic_slug,
        "status": status,
        "trajectory_count": len(rows),
        "latest_run_id": latest_run_id,
        "latest_summary": latest_summary,
        "trajectory_summaries": trajectory_summaries,
        "related_topic_slugs": related_topic_slugs,
        "recent_related_topic_slugs": recent_related_topic_slugs,
        "memory_ids": self._dedupe_strings([str(row.get("memory_id") or "").strip() for row in rows]),
        "summary": summary,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }


def render_research_trajectory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Research trajectory",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Trajectory count: `{payload.get('trajectory_count') or 0}`",
        f"- Latest run id: `{payload.get('latest_run_id') or '(none)'}`",
        f"- Related topics: `{', '.join(payload.get('related_topic_slugs') or []) or '(none)'}`",
        f"- Recent related topics: `{', '.join(payload.get('recent_related_topic_slugs') or []) or '(none)'}`",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Trajectory summaries",
        "",
    ]
    for row in payload.get("trajectory_summaries") or ["(none)"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def materialize_research_trajectory_surface(
    self,
    *,
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = research_trajectory_paths(runtime_root)
    payload = derive_research_trajectory(self, topic_slug=topic_slug, updated_by=updated_by)
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
    }
    _write_json(paths["json"], payload)
    paths["note"].write_text(render_research_trajectory_markdown(payload), encoding="utf-8")
    return paths, payload


def normalize_research_trajectory_for_bundle(
    self,
    *,
    shell_surfaces: dict[str, Any],
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    trajectory = dict(shell_surfaces.get("research_trajectory") or {})
    if not trajectory:
        trajectory = empty_research_trajectory(topic_slug=topic_slug, updated_by=updated_by)
    paths = research_trajectory_paths(runtime_root)
    if not str(trajectory.get("path") or "").strip():
        trajectory["path"] = self._relativize(paths["json"])
    if not str(trajectory.get("note_path") or "").strip():
        trajectory["note_path"] = self._relativize(paths["note"])
    return trajectory


def research_trajectory_must_read_entry(trajectory: dict[str, Any]) -> dict[str, str] | None:
    if str(trajectory.get("status") or "") != "available":
        return None
    note_path = str(trajectory.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Recent trajectory context is available for this topic. Read it before resuming work as if this session had no history.",
    }


def append_research_trajectory_markdown(lines: list[str], trajectory: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Research trajectory",
            "",
            f"- Status: `{trajectory.get('status') or '(missing)'}`",
            f"- Trajectory count: `{trajectory.get('trajectory_count') or 0}`",
            f"- Latest run id: `{trajectory.get('latest_run_id') or '(none)'}`",
            f"- Note path: `{trajectory.get('note_path') or '(missing)'}`",
            "",
            f"{trajectory.get('summary') or '(missing)'}",
            "",
        ]
    )
