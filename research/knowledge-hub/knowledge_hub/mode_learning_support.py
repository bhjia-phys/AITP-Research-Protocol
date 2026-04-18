from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .mode_registry import (
    DEFAULT_RUNTIME_MODE,
    VALID_RUNTIME_MODES,
    normalize_runtime_mode,
    transition_direction,
    is_valid_transition,
)


SUPPORTED_TRANSITIONS: tuple[tuple[str, str], ...] = (
    ("explore", "learn"),
    ("learn", "implement"),
)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _dedupe_strings(values: Iterable[Any]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def mode_learning_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "mode_learning.active.json",
        "note": runtime_root / "mode_learning.active.md",
    }


def get_last_recorded_mode(runtime_root: Path, *, topic_slug: str) -> str | None:
    """Return the to_mode from the most recent transition for this topic, or None."""
    rows = _load_transition_rows(runtime_root, topic_slug=topic_slug)
    if not rows:
        return None
    return str(rows[0].get("to_mode") or "").strip() or None


def mode_transition_history_path(runtime_root: Path) -> Path:
    return runtime_root / "mode_transition_history.jsonl"


def _normalize_transition_row(
    row: dict[str, Any] | Any,
    *,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    payload = row if isinstance(row, dict) else {}
    transition_at = str(payload.get("transition_at") or "").strip() or _now_iso()
    from_mode = normalize_runtime_mode(payload.get("from_mode"))
    to_mode = normalize_runtime_mode(payload.get("to_mode"))
    transition_id = str(payload.get("transition_id") or "").strip()
    if not transition_id:
        transition_id = f"mode-transition-{from_mode}-{to_mode}-{transition_at}"
    dwell_seconds = payload.get("dwell_seconds")
    try:
        normalized_dwell = float(dwell_seconds) if dwell_seconds is not None else 0.0
    except (TypeError, ValueError):
        normalized_dwell = 0.0
    return {
        "transition_id": transition_id,
        "transition_at": transition_at,
        "topic_slug": str(payload.get("topic_slug") or topic_slug).strip(),
        "run_id": str(payload.get("run_id") or "").strip(),
        "from_mode": from_mode,
        "to_mode": to_mode,
        "transition_direction": transition_direction(from_mode, to_mode),
        "dwell_seconds": max(0.0, normalized_dwell),
        "trigger": str(payload.get("trigger") or "").strip(),
        "summary": str(payload.get("summary") or "").strip()
        or f"Transitioned from `{from_mode}` to `{to_mode}`.",
        "outcome": str(payload.get("outcome") or "observed").strip(),
        "evidence_refs": _dedupe_strings(payload.get("evidence_refs") or []),
        "updated_by": str(payload.get("updated_by") or updated_by).strip(),
    }


def _load_transition_rows(
    runtime_root: Path,
    *,
    topic_slug: str | None = None,
) -> list[dict[str, Any]]:
    rows = [
        _normalize_transition_row(
            row,
            topic_slug=str(row.get("topic_slug") or topic_slug or "").strip(),
            updated_by=str(row.get("updated_by") or "aitp-service").strip(),
        )
        for row in _read_jsonl(mode_transition_history_path(runtime_root))
    ]
    if topic_slug:
        rows = [
            row
            for row in rows
            if str(row.get("topic_slug") or "").strip() == str(topic_slug).strip()
        ]
    rows.sort(
        key=lambda item: (
            str(item.get("transition_at") or ""),
            str(item.get("transition_id") or ""),
        ),
        reverse=True,
    )
    return rows


def record_mode_transition(
    runtime_root: Path,
    *,
    topic_slug: str,
    from_mode: str,
    to_mode: str,
    updated_by: str = "aitp-service",
    run_id: str | None = None,
    dwell_seconds: float | int | None = None,
    trigger: str | None = None,
    summary: str | None = None,
    outcome: str | None = None,
    evidence_refs: list[str] | None = None,
) -> tuple[Path, dict[str, Any]]:
    normalized_from = normalize_runtime_mode(from_mode)
    normalized_to = normalize_runtime_mode(to_mode)
    if normalized_from not in VALID_RUNTIME_MODES or normalized_to not in VALID_RUNTIME_MODES:
        raise ValueError(
            f"from_mode and to_mode must be one of {sorted(VALID_RUNTIME_MODES)}"
        )
    direction = transition_direction(normalized_from, normalized_to)
    if direction == "invalid":
        raise ValueError(
            f"Transition {normalized_from} -> {normalized_to} is not in the protocol "
            f"mode-transition graph. Valid forward: explore->learn, learn->implement, "
            f"implement->explore. Valid backward: learn->explore, implement->learn."
        )
    if direction == "backward" and not trigger and not summary:
        raise ValueError(
            f"Backward transition {normalized_from} -> {normalized_to} requires an "
            f"explicit trigger or summary explaining why the backward move is justified."
        )
    row = _normalize_transition_row(
        {
            "topic_slug": topic_slug,
            "run_id": str(run_id or "").strip(),
            "from_mode": normalized_from,
            "to_mode": normalized_to,
            "dwell_seconds": dwell_seconds,
            "trigger": str(trigger or "").strip(),
            "summary": str(summary or "").strip(),
            "outcome": str(outcome or "observed").strip(),
            "evidence_refs": evidence_refs or [],
            "updated_by": updated_by,
        },
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    path = mode_transition_history_path(runtime_root)
    rows = _read_jsonl(path)
    rows.append(row)
    _write_jsonl(path, rows)
    return path, row


def get_mode_history(
    runtime_root: Path,
    *,
    topic_slug: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    rows = _load_transition_rows(runtime_root, topic_slug=topic_slug)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = f"{row.get('from_mode')}->{row.get('to_mode')}"
        grouped.setdefault(key, []).append(row)
    transition_counts = {
        key: len(value)
        for key, value in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
    }
    average_dwell = {
        key: round(
            sum(float(item.get("dwell_seconds") or 0.0) for item in value) / len(value),
            2,
        )
        for key, value in grouped.items()
        if value
    }
    return {
        "topic_slug": str(topic_slug or "").strip() or None,
        "transition_count": len(rows),
        "latest_transition": rows[0] if rows else {},
        "transitions": rows[: max(1, limit)],
        "transition_counts": transition_counts,
        "average_dwell_seconds": average_dwell,
        "history_path": str(mode_transition_history_path(runtime_root)),
    }


def suggest_transition(
    runtime_root: Path,
    *,
    current_mode: str,
    topic_slug: str | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_runtime_mode(current_mode)
    rows = _load_transition_rows(runtime_root, topic_slug=topic_slug)
    relevant_rows = [
        row for row in rows if str(row.get("from_mode") or "").strip() == normalized_mode
    ]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in relevant_rows:
        grouped.setdefault(str(row.get("to_mode") or "").strip(), []).append(row)
    if grouped:
        recommended_mode, supporting_rows = max(
            grouped.items(),
            key=lambda item: (len(item[1]), item[0]),
        )
        avg_dwell = round(
            sum(float(row.get("dwell_seconds") or 0.0) for row in supporting_rows)
            / len(supporting_rows),
            2,
        )
        confidence = min(1.0, 0.4 + 0.15 * len(supporting_rows))
        summary = (
            f"History suggests `{normalized_mode}` usually advances to "
            f"`{recommended_mode}` after about {avg_dwell:g} second(s)."
        )
        evidence_refs = _dedupe_strings(
            [
                str(row.get("transition_id") or "").strip()
                for row in supporting_rows[:3]
            ]
        )
        return {
            "current_mode": normalized_mode,
            "recommended_mode": recommended_mode,
            "confidence": round(confidence, 2),
            "average_dwell_seconds": avg_dwell,
            "supporting_count": len(supporting_rows),
            "summary": summary,
            "evidence_refs": evidence_refs,
        }
    fallback = normalized_mode
    for source_mode, target_mode in SUPPORTED_TRANSITIONS:
        if normalized_mode == source_mode:
            fallback = target_mode
            break
    if fallback == normalized_mode and normalized_mode not in VALID_RUNTIME_MODES:
        fallback = DEFAULT_RUNTIME_MODE
    return {
        "current_mode": normalized_mode,
        "recommended_mode": fallback,
        "confidence": 0.25,
        "average_dwell_seconds": 0.0,
        "supporting_count": 0,
        "summary": (
            f"No learned transition history exists for `{normalized_mode}` yet. "
            f"Use `{fallback}` as the conservative next mode."
        ),
        "evidence_refs": [],
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
    helpful_rows = [
        row for row in rows if str(row.get("outcome") or "").strip() == "helpful"
    ]
    harmful_rows = [
        row for row in rows if str(row.get("outcome") or "").strip() == "harmful"
    ]
    lane_scores: dict[str, int] = {}
    for row in helpful_rows:
        lane = str(row.get("lane") or "").strip()
        if lane:
            lane_scores[lane] = lane_scores.get(lane, 0) + 1
    for row in harmful_rows:
        lane = str(row.get("lane") or "").strip()
        if lane:
            lane_scores[lane] = lane_scores.get(lane, 0) - 1
    preferred_lane = (
        max(lane_scores.items(), key=lambda item: (item[1], item[0]))[0]
        if lane_scores
        else ""
    )
    recommended_routes = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in helpful_rows][:3]
    )
    avoid_routes = self._dedupe_strings(
        [str(row.get("summary") or "").strip() for row in harmful_rows][:3]
    )
    runtime_root = self._runtime_root(topic_slug)
    transition_rows = _load_transition_rows(runtime_root, topic_slug=topic_slug)
    latest_run_id = next(
        (
            str(row.get("run_id") or "").strip()
            for row in [*transition_rows, *rows]
            if str(row.get("run_id") or "").strip()
        ),
        "",
    )
    transition_suggestion = suggest_transition(
        runtime_root,
        current_mode="explore",
        topic_slug=topic_slug,
    )
    if transition_rows and not recommended_routes:
        recommended_routes = self._dedupe_strings(
            [transition_suggestion.get("summary") or ""]
        )
    status = "available" if rows or transition_rows else "absent"
    summary = "No mode learning is currently recorded for this topic."
    if rows:
        summary = (
            f"Mode learning favors `{preferred_lane}` with {len(helpful_rows)} helpful "
            f"and {len(harmful_rows)} harmful learned pattern(s)."
        )
        if recommended_routes:
            summary += f" Latest reusable route: {recommended_routes[0]}"
        if transition_rows:
            summary += (
                f" Typical transition: "
                f"{transition_suggestion.get('summary') or '(missing)'}"
            )
    elif transition_rows:
        summary = transition_suggestion.get("summary") or (
            "Mode-transition history is available, but no strategy-memory rows exist yet."
        )
    updated_at = next(
        (
            str(row.get("transition_at") or row.get("timestamp") or "").strip()
            for row in [*transition_rows, *rows]
            if str(row.get("transition_at") or row.get("timestamp") or "").strip()
        ),
        _now_iso(),
    )
    source_paths = self._dedupe_strings(
        [str(row.get("path") or "").strip() for row in rows if str(row.get("path") or "").strip()]
        + (
            [self._relativize(mode_transition_history_path(runtime_root))]
            if transition_rows
            else []
        )
    )
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
        "source_paths": source_paths,
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
    payload = derive_mode_learning(
        self,
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
    }
    _write_json(paths["json"], payload)
    paths["note"].write_text(
        render_mode_learning_markdown(payload),
        encoding="utf-8",
    )
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
        mode_learning = empty_mode_learning(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
    paths = mode_learning_paths(runtime_root)
    if not str(mode_learning.get("path") or "").strip():
        mode_learning["path"] = self._relativize(paths["json"])
    if not str(mode_learning.get("note_path") or "").strip():
        mode_learning["note_path"] = self._relativize(paths["note"])
    return mode_learning


def mode_learning_must_read_entry(
    mode_learning: dict[str, Any],
) -> dict[str, str] | None:
    if str(mode_learning.get("status") or "") != "available":
        return None
    note_path = str(mode_learning.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": (
            "Learned route guidance is available for this topic. Read it before "
            "repeating a previously harmful lane choice."
        ),
    }


def append_mode_learning_markdown(
    lines: list[str],
    mode_learning: dict[str, Any],
) -> None:
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
