from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema

from .bundle_support import materialized_default_user_kernel_root
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


def _trace_dir(topic_slug: str, kernel_root: Path | None = None) -> Path:
    return _runtime_topic_root(topic_slug, kernel_root) / "decision_traces"


def _schema_path(kernel_root: Path | None = None) -> Path:
    return _kernel_root(kernel_root) / "schemas" / "decision-trace.schema.json"


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


def _ensure_unique_trace_id(topic_slug: str, base_id: str, kernel_root: Path | None = None) -> str:
    trace_root = _trace_dir(topic_slug, kernel_root)
    candidate = base_id
    suffix = 1
    while (trace_root / f"{_safe_filename(candidate)}.json").exists():
        candidate = f"{base_id}-{suffix}"
        suffix += 1
    return candidate


def _normalize_string_list(values: list[str] | tuple[str, ...] | None) -> list[str]:
    normalized: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text:
            normalized.append(text)
    return normalized


def record_decision_trace(
    topic_slug: str,
    summary: str,
    chosen: str,
    rationale: str,
    input_refs: list[str] | tuple[str, ...],
    *,
    context: str | None = None,
    decision_point_ref: str | None = None,
    options_considered: list[dict[str, Any]] | None = None,
    would_change_if: str | None = None,
    output_refs: list[str] | tuple[str, ...] | None = None,
    layer_transition: dict[str, str] | None = None,
    related_traces: list[str] | tuple[str, ...] | None = None,
    trace_id: str | None = None,
    timestamp: str | None = None,
    kernel_root: Path | None = None,
) -> dict[str, Any]:
    normalized_topic = str(topic_slug).strip()
    if not normalized_topic:
        raise ValueError("topic_slug is required")
    normalized_summary = str(summary or "").strip()
    normalized_chosen = str(chosen or "").strip()
    normalized_rationale = str(rationale or "").strip()
    if not normalized_summary or not normalized_chosen or not normalized_rationale:
        raise ValueError("summary, chosen, and rationale are required")

    base_trace_id = trace_id or f"dt:{_slugify(normalized_topic)}-{_slugify(normalized_summary)}"
    final_trace_id = _ensure_unique_trace_id(normalized_topic, base_trace_id, kernel_root)
    payload: dict[str, Any] = {
        "id": final_trace_id,
        "topic_slug": normalized_topic,
        "timestamp": str(timestamp or _utcnow_iso()),
        "decision_summary": normalized_summary,
        "chosen": normalized_chosen,
        "rationale": normalized_rationale,
        "input_refs": _normalize_string_list(list(input_refs)),
    }
    if decision_point_ref:
        payload["decision_point_ref"] = str(decision_point_ref).strip()
    if context:
        payload["context"] = str(context).strip()
    if options_considered:
        payload["options_considered"] = options_considered
    if would_change_if:
        payload["would_change_if"] = str(would_change_if).strip()
    normalized_output_refs = _normalize_string_list(list(output_refs or []))
    if normalized_output_refs:
        payload["output_refs"] = normalized_output_refs
    if layer_transition:
        payload["layer_transition"] = layer_transition
    normalized_related = _normalize_string_list(list(related_traces or []))
    if normalized_related:
        payload["related_traces"] = normalized_related

    _validate_payload(payload, kernel_root)
    path = _trace_dir(normalized_topic, kernel_root) / f"{_safe_filename(final_trace_id)}.json"
    _write_json(path, payload)
    return {
        "decision_trace": payload,
        "path": str(path),
    }


def get_decision_traces(topic_slug: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    trace_root = _trace_dir(topic_slug, kernel_root)
    if not trace_root.exists():
        return []
    traces = [_read_json(path) for path in sorted(trace_root.glob("*.json"))]
    traces.sort(key=lambda item: str(item.get("timestamp") or ""))
    return traces


def query_traces(topic_slug: str, question: str, *, kernel_root: Path | None = None) -> list[dict[str, Any]]:
    keywords = {token for token in re.findall(r"[a-z0-9]+", str(question).lower()) if token}
    if not keywords:
        return []

    scored: list[tuple[int, dict[str, Any]]] = []
    for trace in get_decision_traces(topic_slug, kernel_root=kernel_root):
        fields = [
            str(trace.get("decision_summary") or ""),
            str(trace.get("rationale") or ""),
            str(trace.get("context") or ""),
            str(trace.get("would_change_if") or ""),
            str(trace.get("chosen") or ""),
        ]
        haystack = " ".join(fields).lower()
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score:
            scored.append((score, trace))

    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1].get("timestamp") or ""),
            str(item[1].get("id") or ""),
        )
    )
    return [trace for _, trace in scored]
