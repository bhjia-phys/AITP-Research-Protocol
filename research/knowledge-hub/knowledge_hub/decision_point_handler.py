from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from .bundle_support import materialized_default_user_kernel_root
from .decision_trace_handler import record_decision_trace
from .topic_truth_root_support import runtime_root


def _kernel_root(kernel_root: Path | None = None) -> Path:
    if kernel_root is not None:
        return kernel_root
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "runtime" / "scripts" / "orchestrate_topic.py").exists():
        return candidate
    return materialized_default_user_kernel_root()


def _runtime_topic_root(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return runtime_root(_kernel_root(kernel_root), topic_slug)


def _decision_dir(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return _runtime_topic_root(topic_slug, kernel_root) / "decision_points"


def _operator_console_path(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return _runtime_topic_root(topic_slug, kernel_root) / "operator_console.md"


def _schema_path(kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "schemas" / "decision-point.schema.json"


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


def _normalize_string_list(values: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text:
            normalized.append(text)
    return normalized


def _ensure_unique_decision_id(topic_slug: str, base_id: str, kernel_root: Path | None = None) -> str:
    decision_root = _decision_dir(topic_slug, kernel_root)
    candidate = base_id
    suffix = 1
    while (decision_root / f"{_safe_filename(candidate)}.json").exists():
        candidate = f"{base_id}-{suffix}"
        suffix += 1
    return candidate


def _load_decision_points(topic_slug: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    decision_root = _decision_dir(topic_slug, kernel_root)
    if not decision_root.exists():
        return []
    rows = [_read_json(path) for path in sorted(decision_root.glob("*.json"))]
    rows.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")))
    return rows


def _upsert_markdown_section(markdown: str, heading: str, body: str) -> str:
    content = markdown.strip("\n")
    if not content:
        content = "# Operator Console"
    lines = content.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    replacement = [heading, ""]
    replacement.extend(body.strip("\n").splitlines())
    if start is None:
        if lines and lines[-1].strip():
            lines.extend(["", *replacement])
        else:
            lines.extend(replacement)
        return "\n".join(lines).rstrip() + "\n"
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    updated = lines[:start] + replacement + lines[end:]
    return "\n".join(updated).rstrip() + "\n"


def _render_pending_section(decisions: list[dict[str, Any]]) -> str:
    if not decisions:
        return "- None."
    lines: list[str] = []
    for payload in decisions:
        lines.append(
            f"- `{payload.get('id')}` blocking=`{str(bool(payload.get('blocking'))).lower()}` "
            f"phase=`{payload.get('phase') or '(missing)'}` trigger=`{payload.get('trigger_rule') or '(none)'}`"
        )
        lines.append(f"  Question: {payload.get('question') or '(missing)'}")
        for index, option in enumerate(payload.get("options") or []):
            lines.append(
                f"  Option {index}: {option.get('label') or '(missing)'}"
                f" -- {option.get('description') or '(missing)'}"
            )
    return "\n".join(lines)


def _refresh_operator_console(topic_slug: str, *, kernel_root: Path | None = None) -> str:
    console_path = _operator_console_path(topic_slug, kernel_root)
    existing = console_path.read_text(encoding="utf-8") if console_path.exists() else "# Operator Console\n"
    pending = list_pending_decision_points(topic_slug, kernel_root=kernel_root)
    updated = _upsert_markdown_section(existing, "## Pending Decision Points", _render_pending_section(pending))
    console_path.parent.mkdir(parents=True, exist_ok=True)
    console_path.write_text(updated, encoding="utf-8")
    return str(console_path)


def emit_decision_point(
    topic_slug: str,
    question: str,
    options: list[dict[str, Any]],
    blocking: bool,
    *,
    phase: str = "routing",
    layer_context: dict[str, str] | None = None,
    default_option_index: int | None = None,
    timeout_hint: str | None = None,
    trigger_rule: str | None = None,
    related_artifacts: list[str] | tuple[str, ...] | None = None,
    decision_id: str | None = None,
    created_at: str | None = None,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    normalized_topic = str(topic_slug).strip()
    normalized_question = str(question or "").strip()
    if not normalized_topic or not normalized_question:
        raise ValueError("topic_slug and question are required")
    if len(options or []) < 2:
        raise ValueError("decision points require at least two options")

    base_id = decision_id or f"dp:{_slugify(normalized_topic)}-{_slugify(normalized_question)}"
    if decision_id:
        final_id = base_id
        existing_path = _decision_dir(normalized_topic, kernel_root) / f"{_safe_filename(final_id)}.json"
        if existing_path.exists():
            raise FileExistsError(f"decision point already exists: {existing_path}")
    else:
        final_id = _ensure_unique_decision_id(normalized_topic, base_id, kernel_root)
    payload: dict[str, Any] = {
        "id": final_id,
        "topic_slug": normalized_topic,
        "phase": phase,
        "layer_context": layer_context or {"current_layer": "L3"},
        "question": normalized_question,
        "options": options,
        "blocking": bool(blocking),
        "created_at": str(created_at or _utcnow_iso()),
    }
    if default_option_index is not None:
        payload["default_option_index"] = default_option_index
    if timeout_hint:
        payload["timeout_hint"] = str(timeout_hint).strip()
    if trigger_rule:
        payload["trigger_rule"] = str(trigger_rule).strip()
    normalized_related = _normalize_string_list(list(related_artifacts or []))
    if normalized_related:
        payload["related_artifacts"] = normalized_related

    _validate_payload(payload, kernel_root)
    path = _decision_dir(normalized_topic, kernel_root) / f"{_safe_filename(final_id)}.json"
    if path.exists():
        raise FileExistsError(f"decision point already exists: {path}")
    _write_json(path, payload)
    operator_console = _refresh_operator_console(normalized_topic, kernel_root=kernel_root)
    return {
        "decision_point": payload,
        "path": str(path),
        "operator_console_path": operator_console,
    }


def list_pending_decision_points(topic_slug: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    return [row for row in _load_decision_points(topic_slug, kernel_root=kernel_root) if not row.get("resolution")]


def check_blocking_decision_points(topic_slug: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    return [row for row in list_pending_decision_points(topic_slug, kernel_root=kernel_root) if row.get("blocking")]


def resolve_decision_point(
    topic_slug: str,
    decision_id: str,
    option_index: int,
    comment: str | None = None,
    *,
    resolved_by: str = "human",
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    normalized_topic = str(topic_slug).strip()
    normalized_id = str(decision_id).strip()
    if not normalized_topic or not normalized_id:
        raise ValueError("topic_slug and decision_id are required")
    path = _decision_dir(normalized_topic, kernel_root) / f"{_safe_filename(normalized_id)}.json"
    if not path.exists():
        raise FileNotFoundError(f"decision point not found: {normalized_id}")
    payload = _read_json(path)
    if payload.get("resolution"):
        raise ValueError(f"decision point already resolved: {normalized_id}")
    options = payload.get("options") or []
    if option_index < 0 or option_index >= len(options):
        raise IndexError("option_index is out of range")
    chosen_option = options[option_index]
    payload["resolution"] = {
        "chosen_option_index": option_index,
        "human_comment": str(comment or "").strip(),
        "resolved_at": _utcnow_iso(),
        "resolved_by": str(resolved_by).strip() or "human",
    }
    _validate_payload(payload, kernel_root)
    _write_json(path, payload)
    trace_result = record_decision_trace(
        normalized_topic,
        summary=f"Resolved decision point {normalized_id}",
        chosen=str(chosen_option.get("label") or f"option-{option_index}"),
        rationale=str(comment or chosen_option.get("description") or payload.get("question") or "").strip(),
        input_refs=_normalize_string_list((payload.get("related_artifacts") or []) + [str(path)]),
        context=str(payload.get("question") or "").strip(),
        decision_point_ref=normalized_id,
        options_considered=[
            {
                "option": str(option.get("label") or f"option-{index}"),
                "pros": str(option.get("description") or ""),
                "cons": str(option.get("consequences") or ""),
            }
            for index, option in enumerate(options)
        ],
        output_refs=[str(path)],
        kernel_root=kernel_root,
    )
    operator_console = _refresh_operator_console(normalized_topic, kernel_root=kernel_root)
    return {
        "decision_point": payload,
        "path": str(path),
        "decision_trace": trace_result["decision_trace"],
        "decision_trace_path": trace_result["path"],
        "operator_console_path": operator_console,
    }


def get_all_decision_points(topic_slug: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    return _load_decision_points(topic_slug, kernel_root=kernel_root)
