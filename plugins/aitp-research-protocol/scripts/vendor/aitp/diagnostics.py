"""Read-only whole-store diagnostics (`aitp check`, M1b-R1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .md import AITPError, _section_content, parse_markdown
from .notes import validate_note
from .query import _scan_records, _stored_time
from .records import (
    _canonical_entries,
    _validate_relations,
    _verify_refs,
    validate_entry,
)
from .workspace import load_store, resolve_root

GOAL_PLACEHOLDER = "Not established yet"


def _finding(level: str, code: str, relative: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "path": relative, "message": message}


def _grade_records(root: Path, items: list[tuple[dict[str, Any], str, Path]], refs_key: str, label: str,
                   *, relations: bool, require_refs: bool, findings: list[dict[str, str]],
                   entry_map: dict[str, tuple[dict[str, Any], Path]] | None = None) -> None:
    for frontmatter, _, path in items:
        relative = str(path.relative_to(root))
        if _stored_time(frontmatter.get("created_at")) is None:
            findings.append(_finding("warning", "invalid_timestamp", relative, f"unparseable created_at: {frontmatter.get('created_at')}"))
        if relations:
            relation_failed = False
            for field in ("resolves", "supersedes"):
                try:
                    _validate_relations(root, frontmatter, field, frontmatter["id"], entry_map)
                except AITPError as exc:
                    findings.append(_finding("error", exc.code, relative, str(exc))); relation_failed = True
                except Exception as exc:
                    findings.append(_finding("error", "invalid_schema", relative, f"{path}: {exc}")); relation_failed = True
            if relation_failed: continue
        refs = frontmatter[refs_key]
        if require_refs and not refs:
            findings.append(_finding("error", "missing_refs", relative, f"{label} requires nonempty {refs_key}"))
        elif refs:
            try:
                graded = _verify_refs(root, refs)
            except Exception as exc:
                findings.append(_finding("error", "invalid_schema", relative, f"{path}: {exc}"))
            else:
                findings.extend(_finding(grade, code, relative, message) for code, message, grade in graded)


def check_workspace(cwd: str | Path) -> dict[str, Any]:
    root = resolve_root(cwd)
    topic_id = load_store(root)["topic_id"]
    findings: list[dict[str, str]] = []
    entry_paths = sorted(_canonical_entries(root), key=lambda item: item.name)
    entries, entry_warnings = _scan_records(root, entry_paths, validate_entry, "Entry", topic_id=topic_id)
    findings.extend(_finding("error", item["code"], item["path"], item["message"]) for item in entry_warnings)
    entry_map = {fm["id"]: (fm, path) for fm, _, path in entries if isinstance(fm.get("id"), str)}
    _grade_records(root, entries, "refs", "Entry", relations=True, require_refs=False,
                   findings=findings, entry_map=entry_map)
    notes_dir = root / ".aitp" / "topic" / "notes"
    note_paths = sorted(notes_dir.glob("note-*.md"), key=lambda item: item.name)
    notes, note_warnings = _scan_records(root, note_paths, validate_note, "Note", topic_id=topic_id)
    findings.extend(_finding("error", item["code"], item["path"], item["message"]) for item in note_warnings)
    _grade_records(root, notes, "basis_refs", "Note", relations=False, require_refs=True, findings=findings)
    topic_path = root / ".aitp" / "topic" / "TOPIC.md"
    relative = str(topic_path.relative_to(root))
    try:
        _, topic_body, _ = parse_markdown(topic_path)
        goal = _section_content(topic_body, "Research Goal").strip()
        if not goal or goal == GOAL_PLACEHOLDER:
            findings.append(_finding("warning", "empty_topic_goal", relative, "Research Goal is not established"))
    except AITPError as exc:
        findings.append(_finding("error", exc.code, relative, str(exc)))
    except Exception as exc:
        findings.append(_finding("error", "invalid_schema", relative, f"{topic_path}: {exc}"))
    findings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    errors = sum(1 for item in findings if item["level"] == "error")
    warnings = len(findings) - errors
    return {"schema": "aitp/check-report-0.1", "status": "clean" if not findings else "findings",
            "root": str(root),
            "counts": {"entries": len(entry_paths), "notes": len(note_paths),
                       "errors": errors, "warnings": warnings},
            "findings": findings}
