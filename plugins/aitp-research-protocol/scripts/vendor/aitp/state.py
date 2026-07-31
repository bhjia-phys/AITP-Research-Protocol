"""Active-state projection for `aitp enter`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .md import AITPError, _section_content, parse_markdown
from .records import _canonical_entries, validate_entry
from .workspace import load_store, resolve_root


def _topic_goal(body: str) -> str:
    return _section_content(body, "Research Goal") or "Not established yet"


def enter_workspace(cwd: str | Path, *, recent: int = 20) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    topic_path = root / ".aitp" / "topic" / "TOPIC.md"
    topic_frontmatter, topic_body, _ = parse_markdown(topic_path)
    valid: dict[str, tuple[dict[str, Any], Path]] = {}
    warnings: list[dict[str, str]] = []
    malformed = 0
    for path in _canonical_entries(root):
        try:
            frontmatter, body, _ = parse_markdown(path)
            validate_entry(root, frontmatter, body, validate_evidence=False)
            entry_id = frontmatter["id"]
            if entry_id in valid:
                raise AITPError("duplicate_id", f"duplicate Entry ID: {entry_id}")
            valid[entry_id] = (frontmatter, path)
        except AITPError as exc:
            malformed += 1
            warnings.append(
                {
                    "code": exc.code,
                    "path": str(path.relative_to(root)),
                    "message": str(exc),
                }
            )
    superseded_ids = {
        target
        for frontmatter, _ in valid.values()
        for target in frontmatter.get("supersedes", [])
        if target in valid
    }
    active = {
        entry_id: item for entry_id, item in valid.items() if entry_id not in superseded_ids
    }
    resolved_ids = {
        target
        for frontmatter, _ in active.values()
        for target in frontmatter.get("resolves", [])
    }
    ordered = sorted(
        active.values(),
        key=lambda item: (str(item[0].get("created_at", "")), str(item[0].get("id", ""))),
        reverse=True,
    )

    def output_entry(item: tuple[dict[str, Any], Path]) -> dict[str, Any]:
        frontmatter, path = item
        return {
            "id": frontmatter["id"],
            "kind": frontmatter["kind"],
            "summary": frontmatter["summary"],
            "limitations": frontmatter["limitations"],
            "authority": frontmatter["authority"],
            "created_at": frontmatter["created_at"],
            "refs": frontmatter["refs"],
            "source": str(path.relative_to(root)),
        }

    unresolved = [
        output_entry(item)
        for entry_id, item in active.items()
        if item[0]["kind"] == "failure" and entry_id not in resolved_ids
    ]
    unresolved.sort(key=lambda item: (item["created_at"], item["id"]), reverse=True)
    next_action: dict[str, Any] | None = None
    for frontmatter, path in ordered:
        text = frontmatter.get("next_action")
        if isinstance(text, str) and text.strip():
            next_action = {
                "text": text,
                "entry_id": frontmatter["id"],
                "authority": frontmatter["authority"],
                "created_at": frontmatter["created_at"],
                "source": str(path.relative_to(root)),
            }
            break
    notes: list[dict[str, Any]] = []
    notes_dir = root / ".aitp" / "topic" / "notes"
    for path in sorted(notes_dir.glob("note-*.md"), reverse=True)[:recent]:
        try:
            frontmatter, _, _ = parse_markdown(path)
            notes.append(
                {
                    "id": frontmatter.get("id"),
                    "title": frontmatter.get("title"),
                    "mode": frontmatter.get("mode"),
                    "review_state": frontmatter.get("review_state"),
                    "summary": frontmatter.get("summary"),
                    "source": str(path.relative_to(root)),
                }
            )
        except AITPError as exc:
            malformed += 1
            warnings.append(
                {
                    "code": exc.code,
                    "path": str(path.relative_to(root)),
                    "message": str(exc),
                }
            )
    if not valid:
        memory_status = "not_established" if not malformed else "partial"
    else:
        memory_status = "partial" if malformed else "available"
    return {
        "memory_status": memory_status,
        "root": str(root),
        "topic": {
            "id": store["topic_id"],
            "title": topic_frontmatter.get("title", store["title"]),
            "goal": {
                "text": _topic_goal(topic_body),
                "source": str(topic_path.relative_to(root)),
            },
        },
        "recent_entries": [output_entry(item) for item in ordered[:recent]],
        "unresolved_failures": unresolved,
        "next_action": next_action or {
            "status": "not_established",
            "source": None,
        },
        "recent_notes": notes,
        "counts": {
            "active": len(active),
            "superseded": len(superseded_ids),
            "unresolved_failures": len(unresolved),
            "malformed": malformed,
            "omitted_active": max(0, len(active) - recent),
        },
        "warnings": warnings,
    }
