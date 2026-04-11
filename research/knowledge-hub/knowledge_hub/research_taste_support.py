from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

TASTE_KINDS = (
    "route_taste",
    "elegance",
    "formalism",
    "intuition",
    "surprise_handling",
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
    return "-".join(tokens) or "research-taste"


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


def research_taste_paths(runtime_root: Path) -> dict[str, Path]:
    return {
        "json": runtime_root / "research_taste.active.json",
        "note": runtime_root / "research_taste.active.md",
        "entries": runtime_root / "research_taste_entries.jsonl",
    }


def empty_research_taste(*, topic_slug: str, updated_by: str) -> dict[str, Any]:
    return {
        "artifact_kind": "research_taste",
        "topic_slug": topic_slug,
        "status": "absent",
        "taste_entry_count": 0,
        "route_taste_count": 0,
        "elegance_signal_count": 0,
        "intuition_signal_count": 0,
        "formalism_preferences": [],
        "preferred_tags": [],
        "route_taste_summaries": [],
        "elegance_summaries": [],
        "intuition_summaries": [],
        "surprise_handling": {
            "status": "none",
            "latest_summary": "No explicit taste-side surprise handling is currently recorded.",
            "entry_ids": [],
            "evidence_refs": [],
        },
        "memory_ids": [],
        "summary": "No research taste or physical-intuition surface is currently recorded for this topic.",
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def build_research_taste_payload(
    *,
    topic_slug: str,
    taste_rows: list[dict[str, Any]],
    collaborator_preference_rows: list[dict[str, Any]],
    research_judgment: dict[str, Any] | None,
    updated_by: str,
) -> dict[str, Any]:
    payload = empty_research_taste(topic_slug=topic_slug, updated_by=updated_by)
    grouped = {
        kind: [
            row
            for row in taste_rows
            if str(row.get("taste_kind") or "").strip() == kind
        ]
        for kind in TASTE_KINDS
    }
    route_taste_summaries = _dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["route_taste"]]
        + [str(row.get("summary") or "").strip() for row in collaborator_preference_rows]
    )
    elegance_summaries = _dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["elegance"]]
    )
    intuition_summaries = _dedupe_strings(
        [str(row.get("summary") or "").strip() for row in grouped["intuition"]]
    )
    formalism_preferences = _dedupe_strings(
        [
            formalism
            for row in grouped["formalism"]
            for formalism in (row.get("formalisms") or [])
        ]
    )
    preferred_tags = _dedupe_strings(
        [tag for row in taste_rows for tag in (row.get("tags") or [])]
        + [tag for row in collaborator_preference_rows for tag in (row.get("tags") or [])]
    )
    surprise = (research_judgment or {}).get("surprise") or {}
    explicit_surprise_rows = grouped["surprise_handling"]
    surprise_entry_ids = _dedupe_strings(
        [str(row.get("taste_entry_id") or "").strip() for row in explicit_surprise_rows]
    )
    surprise_refs = _dedupe_strings(
        [
            artifact
            for row in explicit_surprise_rows
            for artifact in (row.get("related_artifacts") or [])
        ]
        + list(surprise.get("evidence_refs") or [])
    )
    if explicit_surprise_rows:
        surprise_status = "active"
        surprise_summary = (
            str(explicit_surprise_rows[0].get("summary") or "").strip()
            or "An explicit surprise-handling note is recorded."
        )
    elif str(surprise.get("status") or "").strip() == "active":
        surprise_status = "active"
        surprise_summary = (
            str(surprise.get("latest_summary") or "").strip()
            or "A surprise signal is active, but no explicit handling note is recorded yet."
        )
    else:
        surprise_status = "none"
        surprise_summary = "No explicit taste-side surprise handling is currently recorded."

    memory_ids = _dedupe_strings(
        [str(row.get("memory_id") or "").strip() for row in collaborator_preference_rows]
    )
    explicit_entry_ids = _dedupe_strings(
        [str(row.get("taste_entry_id") or "").strip() for row in taste_rows]
    )
    status = (
        "available"
        if (
            taste_rows
            or collaborator_preference_rows
            or surprise_status == "active"
        )
        else "absent"
    )
    summary_parts: list[str] = []
    if route_taste_summaries:
        summary_parts.append(f"{len(route_taste_summaries)} route-taste signal(s)")
    if formalism_preferences:
        summary_parts.append(f"{len(formalism_preferences)} preferred formalism(s)")
    if elegance_summaries:
        summary_parts.append(f"{len(elegance_summaries)} elegance signal(s)")
    if intuition_summaries:
        summary_parts.append(f"{len(intuition_summaries)} intuition signal(s)")
    if surprise_status == "active":
        summary_parts.append("active surprise-handling guidance")
    summary = (
        "; ".join(summary_parts) + "."
        if summary_parts
        else "No research taste or physical-intuition surface is currently recorded for this topic."
    )
    if route_taste_summaries:
        summary += f" Latest route taste: {route_taste_summaries[0]}"

    return {
        **payload,
        "status": status,
        "taste_entry_count": len(taste_rows),
        "route_taste_count": len(route_taste_summaries),
        "elegance_signal_count": len(elegance_summaries),
        "intuition_signal_count": len(intuition_summaries),
        "formalism_preferences": formalism_preferences,
        "preferred_tags": preferred_tags,
        "route_taste_summaries": route_taste_summaries,
        "elegance_summaries": elegance_summaries,
        "intuition_summaries": intuition_summaries,
        "surprise_handling": {
            "status": surprise_status,
            "latest_summary": surprise_summary,
            "entry_ids": surprise_entry_ids,
            "evidence_refs": surprise_refs,
        },
        "memory_ids": _dedupe_strings([*explicit_entry_ids, *memory_ids]),
        "summary": summary,
        "updated_at": _now_iso(),
        "updated_by": updated_by,
    }


def render_research_taste_markdown(payload: dict[str, Any]) -> str:
    surprise = payload.get("surprise_handling") or {}
    lines = [
        "# Research taste",
        "",
        f"- Topic slug: `{payload.get('topic_slug') or '(missing)'}`",
        f"- Status: `{payload.get('status') or '(missing)'}`",
        f"- Taste entry count: `{payload.get('taste_entry_count') or 0}`",
        f"- Route-taste count: `{payload.get('route_taste_count') or 0}`",
        f"- Elegance signal count: `{payload.get('elegance_signal_count') or 0}`",
        f"- Intuition signal count: `{payload.get('intuition_signal_count') or 0}`",
        f"- Formalism preferences: `{', '.join(payload.get('formalism_preferences') or []) or '(none)'}`",
        f"- Preferred tags: `{', '.join(payload.get('preferred_tags') or []) or '(none)'}`",
        "",
        payload.get("summary") or "(missing)",
        "",
        "## Route taste",
        "",
    ]
    for row in payload.get("route_taste_summaries") or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Elegance", ""])
    for row in payload.get("elegance_summaries") or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(["", "## Physical intuition", ""])
    for row in payload.get("intuition_summaries") or ["(none)"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Surprise handling",
            "",
            f"- Status: `{surprise.get('status') or '(missing)'}`",
            f"- Entry ids: `{', '.join(surprise.get('entry_ids') or []) or '(none)'}`",
            f"- Evidence refs: `{', '.join(surprise.get('evidence_refs') or []) or '(none)'}`",
            "",
            surprise.get("latest_summary") or "(missing)",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def dashboard_research_taste_lines(research_taste: dict[str, Any]) -> list[str]:
    return [
        "## Research taste",
        "",
        f"- Status: `{research_taste.get('status') or '(missing)'}`",
        f"- Formalisms: `{', '.join(research_taste.get('formalism_preferences') or []) or '(none)'}`",
        f"- Intuition signals: `{research_taste.get('intuition_signal_count') or 0}`",
        f"- Note path: `{research_taste.get('note_path') or '(missing)'}`",
        "",
        f"{research_taste.get('summary') or '(missing)'}",
        "",
    ]


def append_research_taste_markdown(lines: list[str], research_taste: dict[str, Any]) -> None:
    lines.extend(
        [
            "## Research taste",
            "",
            f"- Status: `{research_taste.get('status') or '(missing)'}`",
            f"- Taste entry count: `{research_taste.get('taste_entry_count') or 0}`",
            f"- Formalisms: `{', '.join(research_taste.get('formalism_preferences') or []) or '(none)'}`",
            f"- Intuition signals: `{research_taste.get('intuition_signal_count') or 0}`",
            f"- Note path: `{research_taste.get('note_path') or '(missing)'}`",
            "",
            f"{research_taste.get('summary') or '(missing)'}",
            "",
        ]
    )


def materialize_research_taste_surface(
    self,
    *,
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
    research_judgment: dict[str, Any],
) -> tuple[dict[str, Path], dict[str, Any]]:
    paths = research_taste_paths(runtime_root)
    taste_rows = [
        row
        for row in _read_jsonl(paths["entries"])
        if str(row.get("topic_slug") or "").strip() == topic_slug
    ]
    collaborator_preference_rows = [
        row
        for row in self._load_collaborator_memory_rows()
        if self._collaborator_memory_matches_topic(row, topic_slug)
        and str(row.get("memory_kind") or "").strip() == "preference"
    ]
    payload = build_research_taste_payload(
        topic_slug=topic_slug,
        taste_rows=taste_rows,
        collaborator_preference_rows=collaborator_preference_rows,
        research_judgment=research_judgment,
        updated_by=updated_by,
    )
    payload = {
        **payload,
        "path": self._relativize(paths["json"]),
        "note_path": self._relativize(paths["note"]),
        "entries_path": self._relativize(paths["entries"]),
    }
    _write_json(paths["json"], payload)
    _write_text(paths["note"], render_research_taste_markdown(payload))
    return paths, payload


def normalize_research_taste_for_bundle(
    self,
    *,
    shell_surfaces: dict[str, Any],
    runtime_root: Path,
    topic_slug: str,
    updated_by: str,
) -> dict[str, Any]:
    research_taste = dict(shell_surfaces.get("research_taste") or {})
    if not research_taste:
        research_taste = empty_research_taste(topic_slug=topic_slug, updated_by=updated_by)
    paths = research_taste_paths(runtime_root)
    if not str(research_taste.get("path") or "").strip():
        research_taste["path"] = self._relativize(paths["json"])
    if not str(research_taste.get("note_path") or "").strip():
        research_taste["note_path"] = self._relativize(paths["note"])
    if not str(research_taste.get("entries_path") or "").strip():
        research_taste["entries_path"] = self._relativize(paths["entries"])
    return research_taste


def research_taste_must_read_entry(research_taste: dict[str, Any]) -> dict[str, str] | None:
    if str(research_taste.get("status") or "") != "available":
        return None
    note_path = str(research_taste.get("note_path") or "").strip()
    if not note_path:
        return None
    return {
        "path": note_path,
        "reason": "Topic-scoped research taste is available. Read it before flattening physical intuition, elegance criteria, or preferred formalisms into generic routing.",
    }


def load_research_taste(
    runtime_root: Path,
    *,
    topic_slug: str,
    updated_by: str = "aitp-service",
) -> dict[str, Any] | None:
    json_path = research_taste_paths(runtime_root)["json"]
    payload = _read_json(json_path)
    if not isinstance(payload, dict):
        return None
    return {
        **empty_research_taste(topic_slug=topic_slug, updated_by=updated_by),
        **payload,
        "topic_slug": str(payload.get("topic_slug") or topic_slug),
    }


def append_research_taste_entry(
    runtime_root: Path,
    *,
    topic_slug: str,
    taste_kind: str,
    summary: str,
    updated_by: str,
    details: str = "",
    run_id: str = "",
    formalisms: list[str] | None = None,
    tags: list[str] | None = None,
    related_artifacts: list[str] | None = None,
    slugify: Any | None = None,
) -> tuple[Path, dict[str, Any]]:
    paths = research_taste_paths(runtime_root)
    recorded_at = _now_iso()
    slugify_fn = slugify or _default_slugify
    row = {
        "taste_entry_id": f"taste-{slugify_fn(taste_kind)}-{slugify_fn(recorded_at)}",
        "recorded_at": recorded_at,
        "storage_layer": "runtime",
        "canonical_status": "separate_from_scientific_memory",
        "topic_slug": topic_slug,
        "run_id": run_id,
        "taste_kind": taste_kind,
        "summary": summary,
        "details": details,
        "formalisms": _dedupe_strings([str(item) for item in (formalisms or [])]),
        "tags": _dedupe_strings([str(item) for item in (tags or [])]),
        "related_artifacts": _dedupe_strings([str(item) for item in (related_artifacts or [])]),
        "updated_by": updated_by,
    }
    rows = _read_jsonl(paths["entries"])
    rows.append(row)
    _write_jsonl(paths["entries"], rows)
    return paths["entries"], row


def record_research_taste_payload(
    service: Any,
    *,
    topic_slug: str,
    taste_kind: str,
    summary: str,
    updated_by: str = "aitp-cli",
    details: str | None = None,
    run_id: str | None = None,
    formalisms: list[str] | None = None,
    tags: list[str] | None = None,
    related_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    normalized_kind = str(taste_kind or "").strip()
    if normalized_kind not in set(TASTE_KINDS):
        raise ValueError(f"taste_kind must be one of {sorted(TASTE_KINDS)}")
    normalized_summary = str(summary or "").strip()
    if not normalized_summary:
        raise ValueError("summary must not be empty")
    runtime_root = service._runtime_root(topic_slug)
    runtime_root.mkdir(parents=True, exist_ok=True)
    entries_path, row = append_research_taste_entry(
        runtime_root,
        topic_slug=topic_slug,
        taste_kind=normalized_kind,
        summary=normalized_summary,
        updated_by=updated_by,
        details=str(details or "").strip(),
        run_id=str(run_id or "").strip(),
        formalisms=formalisms,
        tags=tags,
        related_artifacts=related_artifacts,
        slugify=getattr(service, "slugify", None),
    )
    if (runtime_root / "topic_state.json").exists():
        shell_surfaces = service.ensure_topic_shell_surfaces(
            topic_slug=topic_slug,
            updated_by=updated_by,
        )
        research_taste_payload = dict(shell_surfaces.get("research_taste") or {})
    else:
        research_taste_payload = load_research_taste(
            runtime_root,
            topic_slug=topic_slug,
            updated_by=updated_by,
        ) or {}
    paths = research_taste_paths(runtime_root)
    return {
        "topic_slug": topic_slug,
        "research_taste_entries_path": str(entries_path),
        "research_taste_path": str(paths["json"]),
        "research_taste_note_path": str(paths["note"]),
        "research_taste_entry": row,
        "research_taste": research_taste_payload,
    }


def topic_research_taste_payload(
    service: Any,
    *,
    topic_slug: str,
    updated_by: str = "aitp-cli",
) -> dict[str, Any]:
    shell_surfaces = service.ensure_topic_shell_surfaces(
        topic_slug=topic_slug,
        updated_by=updated_by,
    )
    runtime_root = service._runtime_root(topic_slug)
    paths = research_taste_paths(runtime_root)
    return {
        "topic_slug": topic_slug,
        "research_taste": dict(shell_surfaces.get("research_taste") or {}),
        "research_taste_entries_path": str(paths["entries"]),
        "research_taste_path": str(paths["json"]),
        "research_taste_note_path": str(paths["note"]),
    }
