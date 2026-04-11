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


def mode_learning_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "mode_learning.active.json",
        "note": runtime_root / "mode_learning.active.md",
    }


def empty_mode_learning(*, topic_slug: str, updated_by: str) -> dict[str, Any]:
    return {
        "artifact_kind": "mode_learning",
        "topic_slug": topic_slug,
        "status": "absent",
        "preferred_lane": "",
        "latest_run_id": "",
        "helpful_pattern_count": 0,
        "harmful_pattern_count": 0,
        "recommended_routes": [],
        "avoid_routes": [],
        "source_paths": [],
        "summary": "No mode learning is currently recorded for this topic.",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def load_mode_learning(
    runtime_root: Path,
    *,
    topic_slug: str,
    updated_by: str = "aitp-service",
) -> dict[str, Any] | None:
    json_path = mode_learning_paths(runtime_root)["json"]
    if not json_path.exists():
        return None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    payload = {
        **empty_mode_learning(topic_slug=topic_slug, updated_by=updated_by),
        **payload,
    }
    payload["topic_slug"] = str(payload.get("topic_slug") or topic_slug)
    return payload


def derive_mode_learning(
    self,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    rows = self._load_strategy_memory_rows(topic_slug)
    helpful_rows = [row for row in rows if str(row.get("outcome") or "").strip() == "helpful"]
    harmful_rows = [row for row in rows if str(row.get("outcome") or "").strip() == "harmful"]
    lane_scores: dict[str, int] = {}
    for row in helpful_rows:
        lane = str(row.get("lane") or "").strip()
        if lane:
            lane_scores[lane] = lane_scores.get(lane, 0) + 1
    for row in harmful_rows:
        lane = str(row.get("lane") or "").strip()
        if lane:
            lane_scores[lane] = lane_scores.get(lane, 0) - 1
    preferred_lane = max(lane_scores.items(), key=lambda item: (item[1], item[0]))[0] if lane_scores else ""
    recommended_routes = self._dedupe_strings([str(row.get("summary") or "").strip() for row in helpful_rows][:3])
    avoid_routes = self._dedupe_strings([str(row.get("summary") or "").strip() for row in harmful_rows][:3])
    latest_run_id = next((str(row.get("run_id") or "").strip() for row in rows if str(row.get("run_id") or "").strip()), "")
    status = "available" if rows else "absent"
    summary = (
        f"Mode learning favors `{preferred_lane}` with {len(helpful_rows)} helpful and {len(harmful_rows)} harmful learned pattern(s). Latest reusable route: {recommended_routes[0]}"
        if rows and recommended_routes
        else (
            f"Mode learning favors `{preferred_lane}` with {len(helpful_rows)} helpful and {len(harmful_rows)} harmful learned pattern(s)."
            if rows
            else "No mode learning is currently recorded for this topic."
        )
    )
    updated_at = str(rows[0].get("timestamp") or "").strip() if rows else _now_iso()
    return {
        "artifact_kind": "mode_learning",
        "topic_slug": topic_slug,
        "status": status,
        "preferred_lane": preferred_lane,
        "latest_run_id": latest_run_id,
        "helpful_pattern_count": len(helpful_rows),
        "harmful_pattern_count": len(harmful_rows),
        "recommended_routes": recommended_routes,
        "avoid_routes": avoid_routes,
        "source_paths": self._dedupe_strings([str(row.get("path") or "").strip() for row in rows if str(row.get("path") or "").strip()]),
        "summary": summary,
        "updated_at": updated_at,
        "updated_by": updated_by,
    }


def render_mode_learning_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Mode learning",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Preferred lane: `{payload.get('preferred_lane') or '(none)'}`",
        f"- Latest run id: `{payload.get('latest_run_id') or '(none)'}`",
        f"- Helpful patterns: `{payload.get('helpful_pattern_count') or 0}`",
        f"- Harmful patterns: `{payload.get('harmful_pattern_count') or 0}`",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Recommended routes",
        "",
    ]
    for row in payload.get("recommended_routes") or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Avoid routes", ""])
    for row in payload.get("avoid_routes") or ["(none)"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"


def materialize_mode_learning_surface(
    self,
    *,
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = mode_learning_paths(runtime_root)
    payload = derive_mode_learning(self, topic_slug=topic_slug, updated_by=updated_by)
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
    }
    _write_json(paths["json"], payload)
    paths["note"].write_text(render_mode_learning_markdown(payload), encoding="utf-8")
    return paths, payload


def normalize_mode_learning_for_bundle(
    self,
    *,
    shell_surfaces: dict[str, Any],
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    mode_learning = dict(shell_surfaces.get("mode_learning") or {})
    if not mode_learning:
        mode_learning = empty_mode_learning(topic_slug=topic_slug, updated_by=updated_by)
    paths = mode_learning_paths(runtime_root)
    if not str(mode_learning.get("path") or "").strip():
        mode_learning["path"] = self._relativize(paths["json"])
    if not str(mode_learning.get("note_path") or "").strip():
        mode_learning["note_path"] = self._relativize(paths["note"])
    return mode_learning


def mode_learning_must_read_entry(mode_learning: dict[str, Any]) -> dict[str, str] | None:
    if str(mode_learning.get("status") or "") != "available":
        return None
    note_path = str(mode_learning.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Learned route guidance is available for this topic. Read it before repeating a previously harmful lane choice.",
    }


def append_mode_learning_markdown(lines: list[str], mode_learning: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Mode learning",
            "",
            f"- Status: `{mode_learning.get('status') or '(missing)'}`",
            f"- Preferred lane: `{mode_learning.get('preferred_lane') or '(none)'}`",
            f"- Helpful patterns: `{mode_learning.get('helpful_pattern_count') or 0}`",
            f"- Harmful patterns: `{mode_learning.get('harmful_pattern_count') or 0}`",
            f"- Note path: `{mode_learning.get('note_path') or '(missing)'}`",
            "",
            f"{mode_learning.get('summary') or '(missing)'}",
            "",
        ]
    )
