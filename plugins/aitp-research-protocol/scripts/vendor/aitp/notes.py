"""Note preparation, validation, and save."""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from .md import (
    AITPError,
    PROMPT_MARKER,
    _section_content,
    atomic_write,
    now_utc,
    parse_markdown,
    render_markdown,
)
from .records import validate_refs
from .workspace import _template, load_store, resolve_root, store_lock


NOTE_ID_RE = re.compile(r"^note-[0-9a-f]{32}$")
NOTE_MODES = {"working", "theory"}
NOTE_SECTIONS = {
    "working": [
        "Purpose",
        "Scope And Basis",
        "Synthesis",
        "Evidence Map",
        "Uncertainty And Omissions",
        "Open Questions",
        "Next Actions",
    ],
    "theory": [
        "Question And Obstruction",
        "Setup And Assumptions",
        "Central Construction Or Argument",
        "Main Result",
        "Checks, Examples, And Failure Modes",
        "Limitations And Open Questions",
    ],
}


def prepare_note(
    cwd: str | Path,
    mode: str,
    title: str,
    *,
    created_by: str = "agent:unknown",
) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    if mode not in NOTE_MODES:
        raise AITPError("invalid_mode", f"unsupported Note mode: {mode}")
    if not title.strip():
        raise AITPError("invalid_title", "Note title must not be empty")
    note_id = f"note-{uuid.uuid4().hex}"
    frontmatter = {
        "schema": "aitp/lite-note-0.1",
        "id": note_id,
        "topic": store["topic_id"],
        "title": title.strip(),
        "mode": mode,
        "created_at": now_utc(),
        "created_by": created_by,
        "review_state": "agent_draft",
        "summary": "",
        "basis_refs": [],
        "supersedes": [],
    }
    body = _template(f"note/{mode}.md")
    path = root / ".aitp" / "local" / "drafts" / f"{note_id}.md"
    atomic_write(path, render_markdown(frontmatter, body))
    return {
        "status": "prepared",
        "id": note_id,
        "path": str(path.relative_to(root)),
        "save_command": f"aitp note save {path.relative_to(root)}",
    }


def save_note(cwd: str | Path, draft: str | Path) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    draft_path = (root / draft).resolve() if not Path(draft).is_absolute() else Path(draft).resolve()
    drafts_root = (root / ".aitp" / "local" / "drafts").resolve()
    try:
        draft_path.relative_to(drafts_root)
    except ValueError as exc:
        raise AITPError("invalid_draft", "Note draft must be under .aitp/local/drafts") from exc
    frontmatter, body, text = parse_markdown(draft_path)
    required = {
        "schema",
        "id",
        "topic",
        "title",
        "mode",
        "created_at",
        "created_by",
        "review_state",
        "summary",
        "basis_refs",
        "supersedes",
    }
    missing = sorted(required - frontmatter.keys())
    if missing:
        raise AITPError("missing_field", f"missing Note fields: {', '.join(missing)}")
    if frontmatter["schema"] != "aitp/lite-note-0.1":
        raise AITPError("invalid_schema", "unsupported Note schema")
    if not isinstance(frontmatter["id"], str) or not NOTE_ID_RE.fullmatch(frontmatter["id"]):
        raise AITPError("invalid_id", "invalid Note ID")
    if frontmatter["topic"] != store["topic_id"]:
        raise AITPError("topic_mismatch", "Note topic does not match repository")
    mode = frontmatter["mode"]
    if mode not in NOTE_MODES:
        raise AITPError("invalid_mode", "invalid Note mode")
    if frontmatter["review_state"] != "agent_draft":
        raise AITPError("review_required", "save only creates agent_draft Notes")
    if not isinstance(frontmatter["summary"], str) or not frontmatter["summary"].strip():
        raise AITPError("missing_summary", "Note summary must not be empty")
    basis_refs = frontmatter["basis_refs"]
    if not basis_refs:
        raise AITPError("missing_refs", "Note requires nonempty basis_refs")
    validate_refs(root, basis_refs)
    if PROMPT_MARKER in body:
        raise AITPError("unfilled_template", "remove all AITP template prompts")
    for heading in NOTE_SECTIONS[mode]:
        if not _section_content(body, heading):
            raise AITPError("empty_section", f"required section is empty: {heading}")
    final = root / ".aitp" / "topic" / "notes" / f"{frontmatter['id']}.md"
    with store_lock(root):
        if final.exists():
            if final.read_bytes() == text.encode("utf-8"):
                return {
                    "status": "already_saved",
                    "path": str(final.relative_to(root)),
                }
            raise AITPError("id_conflict", f"Note ID already exists: {frontmatter['id']}")
        atomic_write(final, text)
    return {"status": "saved", "path": str(final.relative_to(root))}
