"""Active-state projection for `aitp enter`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .md import AITPError, _section_content, parse_markdown
from .notes import validate_note
from .query import _projection, _descending_key, _is_legacy_derived, _scan_entries, _stored_time, _superseded_ids, _warning
from .workspace import load_store, resolve_root


def _pick_next_action(ordered: list[tuple[dict[str, Any], str, Path]]) -> dict[str, Any] | None:
    for closeout_only in (True, False):
        for frontmatter, _, path in ordered:
            if closeout_only and frontmatter["kind"] != "closeout":
                continue
            text = frontmatter["next_action"]
            if text.strip():
                return {
                    "text": text,
                    "entry_id": frontmatter["id"],
                    "authority": frontmatter["authority"],
                    "created_at": frontmatter["created_at"],
                    "source": str(path.relative_to(path.parents[3])),
                }
    return None


def _scan_notes(
    root: Path, *, topic_id: str | None = None
) -> tuple[list[tuple[dict[str, Any], str, Path]], list[dict[str, str]]]:
    notes: list[tuple[dict[str, Any], str, Path]] = []
    warnings: list[dict[str, str]] = []
    notes_dir = root / ".aitp" / "topic" / "notes"
    for path in sorted(notes_dir.glob("note-*.md"), key=lambda item: item.name):
        try:
            frontmatter, body, _ = parse_markdown(path)
            validate_note(
                root, frontmatter, body, validate_evidence=False, topic_id=topic_id
            )
            notes.append((frontmatter, body, path))
        except AITPError as exc:
            warnings.append(_warning(root, path, exc.code, str(exc)))
        except Exception as exc:
            warnings.append(_warning(root, path, "invalid_schema", f"{path}: {exc}"))
    return notes, warnings


def enter_workspace(cwd: str | Path, *, recent: int = 20) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    topic_id = store["topic_id"]
    topic_path = root / ".aitp" / "topic" / "TOPIC.md"
    topic_frontmatter, topic_body, _ = parse_markdown(topic_path)
    items, warnings = _scan_entries(root, topic_id=topic_id)
    valid = {item[0]["id"]: item for item in items}
    malformed = len(warnings)
    for frontmatter, _, path in items:
        if _stored_time(frontmatter.get("created_at")) is None:
            warnings.append(_warning(root, path, "invalid_timestamp", f"unparseable created_at: {frontmatter.get('created_at')}"))
    superseded_ids = _superseded_ids(items)
    active = {entry_id: item for entry_id, item in valid.items() if entry_id not in superseded_ids}
    resolved_ids = {
        target for frontmatter, _, _ in active.values() for target in frontmatter["resolves"]
    }
    ordered = sorted(active.values(), key=lambda item: _descending_key(item[0].get("created_at", ""), item[0]["id"]), reverse=True)

    def output_entry(item: tuple[dict[str, Any], str, Path]) -> dict[str, Any]:
        return _projection(root, item, superseded_ids, details=True)

    unresolved = [output_entry(item) for entry_id, item in active.items() if item[0]["kind"] == "failure" and entry_id not in resolved_ids]
    unresolved.sort(key=lambda item: _descending_key(item["created_at"], item["id"]), reverse=True)
    note_items, note_warnings = _scan_notes(root, topic_id=topic_id)
    warnings.extend(note_warnings)
    malformed += len(note_warnings)
    note_items.sort(key=lambda item: _descending_key(item[0].get("created_at", ""), item[0]["id"]), reverse=True)
    for frontmatter, _, path in note_items:
        if _stored_time(frontmatter.get("created_at")) is None:
            warnings.append(_warning(root, path, "invalid_timestamp", f"unparseable created_at: {frontmatter.get('created_at')}"))
    latest_item = next((item for item in note_items if item[0]["mode"] == "working"), None)
    latest = None if latest_item is None else {
        "id": latest_item[0]["id"], "created_at": latest_item[0]["created_at"],
        "source": str(latest_item[2].relative_to(root)),
    }
    latest_time = _stored_time(latest_item[0].get("created_at")) if latest_item else None
    age = None
    if latest_time is not None:
        age = sum(1 for item in active.values() if (time := _stored_time(item[0].get("created_at"))) is not None and time > latest_time)
    notes = [
        {
            "id": frontmatter["id"], "title": frontmatter["title"], "mode": frontmatter["mode"],
            "review_state": frontmatter["review_state"], "created_at": frontmatter["created_at"],
            "summary": frontmatter["summary"], "source": str(path.relative_to(root)),
            "legacy_derived": _is_legacy_derived(body),
        }
        for frontmatter, body, path in note_items[:recent]
    ]
    next_action = _pick_next_action(ordered)
    memory_status = "partial" if malformed else "available"
    if not valid and not malformed:
        memory_status = "not_established"
    return {
        "schema": "aitp/enter-0.2", "memory_status": memory_status, "root": str(root),
        "topic": {"id": store["topic_id"], "title": topic_frontmatter.get("title", store["title"]),
                  "goal": {"text": _section_content(topic_body, "Research Goal") or "Not established yet", "source": str(topic_path.relative_to(root))}},
        "recent_entries": [output_entry(item) for item in ordered[:recent]],
        "unresolved_failures": unresolved,
        "next_action": next_action or {"status": "not_established", "source": None},
        "latest_working_note": latest,
        "recent_notes": notes,
        "counts": {"active": len(active), "superseded": len(superseded_ids), "unresolved_failures": len(unresolved),
                   "malformed": malformed, "omitted_active": max(0, len(active) - recent),
                   "active_newer_than_latest_working_note": age},
        "warnings": warnings,
    }
