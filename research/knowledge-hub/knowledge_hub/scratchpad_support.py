from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

SCRATCH_ENTRY_KINDS = (
    "scratch_note",
    "route_comparison",
    "open_question",
    "failed_attempt",
    "negative_result",
)


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _dedupe_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = str(value or "").strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            deduped.append(stripped)
    return deduped


def _default_slugify(value: Any) -> str:
    text = str(value or "").strip().lower()
    tokens = [token for token in "".join(ch if ch.isalnum() else "-" for ch in text).split("-") if token]
    return "-".join(tokens) or "scratch"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def scratchpad_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "scratchpad.active.json",
        "note": runtime_root / "scratchpad.active.md",
        "entries": runtime_root / "scratchpad.entries.jsonl",
    }


def empty_scratchpad(*, topic_slug: str, updated_by: str) -> dict[str, Any]:
    return {
        "artifact_kind": "scratchpad",
        "topic_slug": topic_slug,
        "status": "absent",
        "entry_count": 0,
        "negative_result_count": 0,
        "route_comparison_count": 0,
        "open_question_count": 0,
        "latest_summary": "No scratch or negative-result entries are currently recorded for this topic.",
        "latest_negative_result_summary": "No topic-scoped negative result is currently recorded.",
        "entry_ids": [],
        "path": "",
        "note_path": "",
        "entries_path": "",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def build_scratchpad_payload(
    *,
    topic_slug: str,
    rows: list[dict[str, Any]],
    updated_by: str,
) -> dict[str, Any]:
    payload = empty_scratchpad(topic_slug=topic_slug, updated_by=updated_by)
    negative_rows = [row for row in rows if str(row.get("entry_kind") or "").strip() == "negative_result"]
    route_rows = [row for row in rows if str(row.get("entry_kind") or "").strip() == "route_comparison"]
    open_rows = [row for row in rows if str(row.get("entry_kind") or "").strip() == "open_question"]
    latest_summary = str((rows[-1] if rows else {}).get("summary") or "").strip() or payload["latest_summary"]
    latest_negative_summary = (
        str((negative_rows[-1] if negative_rows else {}).get("summary") or "").strip()
        or payload["latest_negative_result_summary"]
    )
    return {
        **payload,
        "status": "active" if rows else "absent",
        "entry_count": len(rows),
        "negative_result_count": len(negative_rows),
        "route_comparison_count": len(route_rows),
        "open_question_count": len(open_rows),
        "latest_summary": latest_summary,
        "latest_negative_result_summary": latest_negative_summary,
        "entry_ids": _dedupe_strings([str(row.get("entry_id") or "").strip() for row in rows]),
        "updated_at": str((rows[-1] if rows else {}).get("recorded_at") or _now_iso()),
        "updated_by": updated_by,
    }


def render_scratchpad_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scratchpad",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Entry count: `{payload.get('entry_count') or 0}`",
        f"- Negative-result count: `{payload.get('negative_result_count') or 0}`",
        f"- Route-comparison count: `{payload.get('route_comparison_count') or 0}`",
        f"- Open-question count: `{payload.get('open_question_count') or 0}`",
        "",
        f"{payload.get('latest_summary') or '(missing)'}",
        "",
        "## Latest negative result",
        "",
        f"{payload.get('latest_negative_result_summary') or '(missing)'}",
        "",
    ]
    return "\n".join(lines) + "\n"


def scratchpad_dashboard_lines(scratchpad: dict[str, Any]) -> list[str]:
    return [
        "## Scratchpad",
        "",
        f"- Status: `{scratchpad.get('status') or '(missing)'}`",
        f"- Entry count: `{scratchpad.get('entry_count') or 0}`",
        f"- Negative results: `{scratchpad.get('negative_result_count') or 0}`",
        f"- Note path: `{scratchpad.get('note_path') or '(missing)'}`",
        "",
        f"{scratchpad.get('latest_summary') or '(missing)'}",
        "",
    ]


def append_scratchpad_markdown(lines: list[str], scratchpad: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Scratchpad",
            "",
            f"- Status: `{scratchpad.get('status') or '(missing)'}`",
            f"- Entry count: `{scratchpad.get('entry_count') or 0}`",
            f"- Negative results: `{scratchpad.get('negative_result_count') or 0}`",
            f"- Note path: `{scratchpad.get('note_path') or '(missing)'}`",
            "",
            f"{scratchpad.get('latest_summary') or '(missing)'}",
            "",
        ]
    )


def append_scratchpad_entry(
    runtime_root: Path,
    *,
    topic_slug: str,
    entry_kind: str,
    summary: str,
    updated_by: str,
    details: str = "",
    run_id: str = "",
    candidate_id: str = "",
    failure_kind: str = "",
    related_artifacts: list[str] | None = None,
    slugify: Any | None = None,
) -> tuple[Path, dict[str, Any]]:
    paths = scratchpad_paths(runtime_root)
    recorded_at = _now_iso()
    slugify_fn = slugify or _default_slugify
    row = {
        "entry_id": f"scratch-{slugify_fn(entry_kind)}-{slugify_fn(recorded_at)}",
        "recorded_at": recorded_at,
        "storage_layer": "runtime",
        "canonical_status": "separate_from_scientific_memory",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "entry_kind": entry_kind,
        "summary": summary,
        "details": details,
        "candidate_id": candidate_id,
        "failure_kind": failure_kind,
        "related_artifacts": _dedupe_strings([str(item) for item in (related_artifacts or [])]),
        "updated_by": updated_by,
    }
    rows = _read_jsonl(paths["entries"])
    rows.append(row)
    _write_jsonl(paths["entries"], rows)
    return paths["entries"], row


def materialize_scratchpad_surface(
    service: Any,
    *,
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = scratchpad_paths(runtime_root)
    rows = [row for row in _read_jsonl(paths["entries"]) if str(row.get("topic_slug") or "").strip() == topic_slug]
    payload = build_scratchpad_payload(topic_slug=topic_slug, rows=rows, updated_by=updated_by)
    payload = {
        **payload,
        "path": service._relativize(paths["json"]),
        "note_path": service._relativize(paths["note"]),
        "entries_path": service._relativize(paths["entries"]),
    }
    _write_json(paths["json"], payload)
    _write_text(paths["note"], render_scratchpad_markdown(payload))
    return paths, payload


def normalize_scratchpad_for_bundle(
    service: Any,
    *,
    shell_surfaces: dict[str, Any],
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    scratchpad = dict(shell_surfaces.get("scratchpad") or {})
    if not scratchpad:
        scratchpad = empty_scratchpad(topic_slug=topic_slug, updated_by=updated_by)
    paths = scratchpad_paths(runtime_root)
    if not str(scratchpad.get("path") or "").strip():
        scratchpad["path"] = service._relativize(paths["json"])
    if not str(scratchpad.get("note_path") or "").strip():
        scratchpad["note_path"] = service._relativize(paths["note"])
    if not str(scratchpad.get("entries_path") or "").strip():
        scratchpad["entries_path"] = service._relativize(paths["entries"])
    return scratchpad


def scratchpad_must_read_entry(scratchpad: dict[str, Any]) -> dict[str, str] | None:
    if str(scratchpad.get("status") or "") != "active":
        return None
    note_path = str(scratchpad.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Topic-scoped scratch and negative-result memory is available. Read it before retrying the same failed route or forgetting an open comparison.",
    }


def load_scratchpad(
    runtime_root: Path,
    *,
    topic_slug: str,
    updated_by: str = "aitp-service",
) -> dict[str, Any] | None:
    json_path = scratchpad_paths(runtime_root)["json"]
    payload = _read_json(json_path)
    if not isinstance(payload, dict):
        return None
    return {
        **empty_scratchpad(topic_slug=topic_slug, updated_by=updated_by),
        **payload,
        "topic_slug": str(payload.get("topic_slug") or topic_slug),
    }


def record_scratch_note_payload(
    service: Any,
    *,
    topic_slug: str,
    entry_kind: str,
    summary: str,
    updated_by: str = "aitp-cli",
    details: str | None = None,
    run_id: str | None = None,
    candidate_id: str | None = None,
    related_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(entry_kind or "").strip()
    if normalized_kind not in set(SCRATCH_ENTRY_KINDS) - {"negative_result"}:
        raise ValueError(f"entry_kind must be one of {sorted(set(SCRATCH_ENTRY_KINDS) - {'negative_result'})}")
    normalized_summary = str(summary or "").strip()
    if not normalized_summary:
        raise ValueError("summary must not be empty")
    runtime_root = service._runtime_root(topic_slug)
    runtime_root.mkdir(parents=True, exist_ok=True)
    entries_path, row = append_scratchpad_entry(
        runtime_root,
        topic_slug=topic_slug,
        entry_kind=normalized_kind,
        summary=normalized_summary,
        updated_by=updated_by,
        details=str(details or "").strip(),
        run_id=str(run_id or "").strip(),
        candidate_id=str(candidate_id or "").strip(),
        related_artifacts=related_artifacts,
        slugify=getattr(service, "slugify", None),
    )
    if (runtime_root / "topic_state.json").exists():
        shell_surfaces = service.ensure_topic_shell_surfaces(topic_slug=topic_slug, updated_by=updated_by)
        scratchpad_payload = dict(shell_surfaces.get("scratchpad") or {})
    else:
        scratchpad_payload = load_scratchpad(runtime_root, topic_slug=topic_slug, updated_by=updated_by) or {}
    paths = scratchpad_paths(runtime_root)
    return {
        "topic_slug": topic_slug,
        "scratchpad_entries_path": str(entries_path),
        "scratchpad_path": str(paths["json"]),
        "scratchpad_note_path": str(paths["note"]),
        "scratchpad_entry": row,
        "scratchpad": scratchpad_payload,
    }


def record_negative_result_payload(
    service: Any,
    *,
    topic_slug: str,
    summary: str,
    failure_kind: str,
    updated_by: str = "aitp-cli",
    details: str | None = None,
    run_id: str | None = None,
    candidate_id: str | None = None,
    related_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    normalized_failure_kind = str(failure_kind or "").strip()
    if not normalized_failure_kind:
        raise ValueError("failure_kind must not be empty")
    runtime_root = service._runtime_root(topic_slug)
    runtime_root.mkdir(parents=True, exist_ok=True)
    entries_path, row = append_scratchpad_entry(
        runtime_root,
        topic_slug=topic_slug,
        entry_kind="negative_result",
        summary=str(summary or "").strip(),
        updated_by=updated_by,
        details=str(details or "").strip(),
        run_id=str(run_id or "").strip(),
        candidate_id=str(candidate_id or "").strip(),
        failure_kind=normalized_failure_kind,
        related_artifacts=related_artifacts,
        slugify=getattr(service, "slugify", None),
    )
    if (runtime_root / "topic_state.json").exists():
        shell_surfaces = service.ensure_topic_shell_surfaces(topic_slug=topic_slug, updated_by=updated_by)
        scratchpad_payload = dict(shell_surfaces.get("scratchpad") or {})
    else:
        scratchpad_payload = load_scratchpad(runtime_root, topic_slug=topic_slug, updated_by=updated_by) or {}
    paths = scratchpad_paths(runtime_root)
    return {
        "topic_slug": topic_slug,
        "scratchpad_entries_path": str(entries_path),
        "scratchpad_path": str(paths["json"]),
        "scratchpad_note_path": str(paths["note"]),
        "scratchpad_entry": row,
        "scratchpad": scratchpad_payload,
    }


def topic_scratchpad_payload(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    shell_surfaces = service.ensure_topic_shell_surfaces(topic_slug=topic_slug, updated_by=updated_by)
    runtime_root = service._runtime_root(topic_slug)
    paths = scratchpad_paths(runtime_root)
    return {
        "topic_slug": topic_slug,
        "scratchpad": dict(shell_surfaces.get("scratchpad") or {}),
        "scratchpad_entries_path": str(paths["entries"]),
        "scratchpad_path": str(paths["json"]),
        "scratchpad_note_path": str(paths["note"]),
    }
