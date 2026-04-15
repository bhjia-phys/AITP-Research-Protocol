from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from .bundle_support import materialized_default_user_kernel_root

from .decision_point_handler import list_pending_decision_points
from .topic_truth_root_support import topic_root


def _kernel_root(kernel_root: Path | None = None) -> Path:
    if kernel_root is not None:
        return kernel_root
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return candidate
    return materialized_default_user_kernel_root()


def _runtime_root(kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "topics"


def _topic_root(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return topic_root(_kernel_root(kernel_root), topic_slug) / "runtime"


def _chronicle_dir(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return _topic_root(topic_slug, kernel_root) / "chronicles"


def _schema_path(kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "schemas" / "session-chronicle.schema.json"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slugify(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", str(value).lower())
    return "-".join(tokens) or "item"


def _safe_filename(identifier: str) -> str:
    return identifier.replace(":", "__")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _validate_payload(payload: dict[str, Any], kernel_root: Path | None = None) -> None:
    schema = _read_json(_schema_path(kernel_root))
    jsonschema.validate(instance=payload, schema=schema)


def _topic_state_summary(topic_slug: str, kernel_root: Path | None = None) -> str:
    topic_state_path = _topic_root(topic_slug, kernel_root) / "topic_state.json"
    if not topic_state_path.exists():
        return "Topic state has not been materialized yet."
    payload = _read_json(topic_state_path)
    stage = str(payload.get("resume_stage") or payload.get("last_materialized_stage") or "(unknown)")
    summary = str(payload.get("summary") or payload.get("resume_reason") or "").strip()
    if summary:
        return f"Topic `{topic_slug}` is at stage `{stage}`. {summary}"
    return f"Topic `{topic_slug}` is at stage `{stage}`."


def _chronicle_paths_from_payload(payload: dict[str, Any], kernel_root: Path | None = None) -> tuple[Path, Path]:
    chronicle_root = _chronicle_dir(str(payload["topic_slug"]), kernel_root)
    base = _safe_filename(str(payload["id"]))
    return chronicle_root / f"{base}.json", chronicle_root / f"{base}.md"


def _find_chronicle_path(chronicle_id: str, kernel_root: Path | None = None) -> Path:
    base = f"{_safe_filename(chronicle_id)}.json"
    for path in _runtime_root(kernel_root).glob(f"*/runtime/chronicles/{base}"):
        return path
    raise FileNotFoundError(f"chronicle not found: {chronicle_id}")


def _decision_point_summary(topic_slug: str, decision_id: str, kernel_root: Path | None = None) -> str:
    path = _topic_root(topic_slug, kernel_root) / "decision_points" / f"{_safe_filename(decision_id)}.json"
    if not path.exists():
        return "(question unavailable)"
    decision_payload = _read_json(path)
    return str(decision_payload.get("question") or "(question unavailable)")


def _decision_trace_summary(topic_slug: str, trace_id: str, kernel_root: Path | None = None) -> str:
    path = _topic_root(topic_slug, kernel_root) / "decision_traces" / f"{_safe_filename(trace_id)}.json"
    if not path.exists():
        return "recorded in this session"
    trace_payload = _read_json(path)
    return str(trace_payload.get("decision_summary") or "recorded in this session")


def _render_markdown(payload: dict[str, Any], kernel_root: Path | None = None) -> str:
    started = str(payload.get("session_start") or "(unknown)")
    ended = str(payload.get("session_end") or "(open)")
    topic_slug = str(payload.get("topic_slug") or "")
    decisions: list[str] = []
    for action in payload.get("actions_taken") or []:
        for ref in action.get("decision_trace_refs") or []:
            text = str(ref or "").strip()
            if text and text not in decisions:
                decisions.append(text)
    lines = [
        f"# Session Chronicle: {payload.get('topic_slug') or '(missing)'}",
        "",
        f"**Session**: {payload.get('id') or '(missing)'}",
        f"**Date**: {started}",
        f"**Duration**: {started} -> {ended}",
        "",
        "## Summary",
        str(payload.get("summary") or "Session chronicle started; summary pending finalization."),
        "",
        "## Starting State",
        str(payload.get("starting_state") or "(missing)"),
        "",
        "## Actions Taken",
    ]
    actions = payload.get("actions_taken") or []
    if actions:
        for action in actions:
            artifacts = list(action.get("artifacts_created") or []) + list(action.get("artifacts_modified") or [])
            artifact_text = ", ".join(str(item) for item in artifacts if str(item).strip()) or "(none)"
            lines.append(f"- **{action.get('action') or '(missing)'}**: {action.get('result') or '(missing)'} -> [{artifact_text}]")
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Decisions Made"])
    if decisions:
        for ref in decisions:
            lines.append(f"- {ref}: {_decision_trace_summary(topic_slug, ref, kernel_root)}")
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Problems Encountered"])
    problems = payload.get("problems_encountered") or []
    if problems:
        for problem in problems:
            resolution = problem.get("resolution") or ("still open" if problem.get("still_open") else "(none)")
            lines.append(f"- {problem.get('problem') or '(missing)'}: {resolution}")
    else:
        lines.append("- None recorded.")
    lines.extend(
        [
            "",
            "## Ending State",
            str(payload.get("ending_state") or "(not finalized)"),
            "",
            "## Next Steps",
        ]
    )
    next_steps = payload.get("next_steps") or []
    if next_steps:
        for index, step in enumerate(next_steps, start=1):
            lines.append(f"{index}. {step}")
    else:
        lines.append("1. No next steps recorded.")
    lines.extend(["", "## Open Decision Points"])
    open_points = payload.get("open_decision_points") or []
    if open_points:
        for point in open_points:
            lines.append(f"- {point}: {_decision_point_summary(topic_slug, point, kernel_root)} [UNRESOLVED]")
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def _persist(payload: dict[str, Any], kernel_root: Path | None = None) -> dict[str, Any]:
    _validate_payload(payload, kernel_root)
    json_path, md_path = _chronicle_paths_from_payload(payload, kernel_root)
    _write_json(json_path, payload)
    md_path.write_text(_render_markdown(payload, kernel_root), encoding="utf-8")
    return {
        "chronicle": payload,
        "json_path": str(json_path),
        "markdown_path": str(md_path),
    }


def start_chronicle(topic_slug: str, *, kernel_root: Path | None = None) -> str:
    normalized_topic = str(topic_slug).strip()
    if not normalized_topic:
        raise ValueError("topic_slug is required")
    chronicle_id = f"chronicle:{_slugify(normalized_topic)}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payload: dict[str, Any] = {
        "id": chronicle_id,
        "topic_slug": normalized_topic,
        "session_start": _utcnow_iso(),
        "starting_state": _topic_state_summary(normalized_topic, kernel_root),
        "actions_taken": [],
        "problems_encountered": [],
        "open_decision_points": [row["id"] for row in list_pending_decision_points(normalized_topic, kernel_root=kernel_root)],
        "summary": "Session chronicle started; summary pending finalization.",
    }
    _persist(payload, kernel_root)
    return chronicle_id


def append_chronicle_action(
    chronicle_id: str,
    action: str,
    result: str,
    artifacts_created: list[str] | tuple[str, ...] | None = None,
    artifacts_modified: list[str] | tuple[str, ...] | None = None,
    decision_trace_refs: list[str] | tuple[str, ...] | None = None,
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _find_chronicle_path(chronicle_id, kernel_root)
    payload = _read_json(path)
    payload.setdefault("actions_taken", []).append(
        {
            "action": str(action or "").strip(),
            "result": str(result or "").strip(),
            "artifacts_created": [str(item).strip() for item in (artifacts_created or []) if str(item).strip()],
            "artifacts_modified": [str(item).strip() for item in (artifacts_modified or []) if str(item).strip()],
            "decision_trace_refs": [str(item).strip() for item in (decision_trace_refs or []) if str(item).strip()],
        }
    )
    return _persist(payload, kernel_root)


def append_chronicle_problem(
    chronicle_id: str,
    problem: str,
    resolution: str | None = None,
    still_open: bool = False,
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _find_chronicle_path(chronicle_id, kernel_root)
    payload = _read_json(path)
    payload.setdefault("problems_encountered", []).append(
        {
            "problem": str(problem or "").strip(),
            "resolution": str(resolution or "").strip(),
            "still_open": bool(still_open),
        }
    )
    return _persist(payload, kernel_root)


def finalize_chronicle(
    chronicle_id: str,
    ending_state: str,
    next_steps: list[str] | tuple[str, ...],
    summary: str,
    *,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    path = _find_chronicle_path(chronicle_id, kernel_root)
    payload = _read_json(path)
    payload["session_end"] = _utcnow_iso()
    payload["ending_state"] = str(ending_state or "").strip()
    payload["next_steps"] = [str(step).strip() for step in next_steps if str(step).strip()]
    payload["summary"] = str(summary or "").strip()
    payload["open_decision_points"] = [
        row["id"] for row in list_pending_decision_points(str(payload["topic_slug"]), kernel_root=kernel_root)
    ]
    return _persist(payload, kernel_root)


def get_latest_chronicle(topic_slug: str, *, kernel_root: Path | None = None) -> dict[str, Any] | None:
    chronicle_root = _chronicle_dir(topic_slug, kernel_root)
    if not chronicle_root.exists():
        return None
    rows = [_read_json(path) for path in chronicle_root.glob("*.json")]
    if not rows:
        return None
    rows.sort(key=lambda item: (str(item.get("session_start") or ""), str(item.get("id") or "")))
    return rows[-1]


def render_chronicle_markdown(chronicle_id: str, *, kernel_root: Path | None = None) -> str:
    path = _find_chronicle_path(chronicle_id, kernel_root)
    payload = _read_json(path)
    return _render_markdown(payload, kernel_root)
