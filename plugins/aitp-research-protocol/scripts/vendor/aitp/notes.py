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
from .records import validate_json_safe, validate_ref_shapes, validate_refs, validate_string_fields, validate_string_list
from .workspace import _template, load_store, resolve_root, store_lock


NOTE_ID_RE = re.compile(r"^note-[0-9a-f]{32}$")
NOTE_MODES = {"working", "theory"}
NOTE_REQUIRED = frozenset(
    "schema id topic title mode created_at created_by review_state summary basis_refs supersedes".split()
)
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
    if created_by == "agent:unknown":
        raise AITPError("missing_provenance", "created_by is required for Note prepare")
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


def validate_note(
    root: Path,
    frontmatter: dict[str, Any],
    body: str,
    *,
    validate_evidence: bool,
    topic_id: str | None = None,
) -> None:
    if topic_id is None:
        topic_id = load_store(root)["topic_id"]
    missing = sorted(NOTE_REQUIRED - frontmatter.keys())
    if missing:
        raise AITPError("missing_field", f"missing Note fields: {', '.join(missing)}")
    if not isinstance(frontmatter["schema"], str) or frontmatter["schema"] != "aitp/lite-note-0.1":
        raise AITPError("invalid_schema", "unsupported Note schema")
    if not isinstance(frontmatter["id"], str) or not NOTE_ID_RE.fullmatch(frontmatter["id"]):
        raise AITPError("invalid_id", "invalid Note ID")
    if not isinstance(frontmatter["topic"], str) or frontmatter["topic"] != topic_id:
        raise AITPError("topic_mismatch", "Note topic does not match repository")
    validate_string_fields(frontmatter, ("title", "created_by"), "Note")
    if not isinstance(frontmatter["created_at"], str): raise AITPError("invalid_timestamp", "Note created_at must be a string")
    mode = frontmatter["mode"]
    if not isinstance(mode, str) or mode not in NOTE_MODES:
        raise AITPError("invalid_mode", "invalid Note mode")
    if not isinstance(frontmatter["review_state"], str):
        raise AITPError("invalid_type", "Note review_state must be a string")
    if frontmatter["review_state"] != "agent_draft":
        raise AITPError("review_required", "save only creates agent_draft Notes")
    if not isinstance(frontmatter["summary"], str) or not frontmatter["summary"].strip():
        raise AITPError("missing_summary", "Note summary must not be empty")
    basis_refs = frontmatter["basis_refs"]
    validate_ref_shapes(basis_refs, "basis_refs")
    if validate_evidence:
        if not basis_refs:
            raise AITPError("missing_refs", "Note requires nonempty basis_refs")
        validate_refs(root, basis_refs)
    validate_string_list(frontmatter["supersedes"], "supersedes", "Note IDs")
    for target in frontmatter["supersedes"]:
        if not NOTE_ID_RE.fullmatch(target) or not (root / ".aitp" / "topic" / "notes" / f"{target}.md").is_file():
            raise AITPError("missing_relation", f"supersedes target does not exist: {target}")
    validate_json_safe(frontmatter, "Note frontmatter")
    if not isinstance(body, str): raise AITPError("invalid_type", "Note body must be a string")
    if PROMPT_MARKER in body:
        raise AITPError("unfilled_template", "remove all AITP template prompts")
    for heading in NOTE_SECTIONS[mode]:
        if not _section_content(body, heading):
            raise AITPError("empty_section", f"required section is empty: {heading}")


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
    validate_note(root, frontmatter, body, validate_evidence=True)
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
