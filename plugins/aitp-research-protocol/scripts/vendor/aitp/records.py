"""Entry templates, validation, relations, and save."""

from __future__ import annotations

import hashlib
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .md import (
    AITPError,
    PROMPT_MARKER,
    _section_content,
    atomic_write,
    now_utc,
    parse_markdown,
    render_markdown,
)
from .workspace import _template, load_store, resolve_root, store_lock


ENTRY_KINDS = {
    "observation",
    "result",
    "failure",
    "decision",
    "source",
    "code_change",
    "run",
    "closeout",
}
AUTHORITIES = {"human", "agent", "source", "tool"}
REF_REQUIRED_KINDS = {"result", "failure", "source", "code_change", "run"}
LIMITATION_REQUIRED_KINDS = {"observation", "result", "source", "run"}
ENTRY_ID_RE = re.compile(r"^entry-[0-9a-f]{32}$")


def _drafts(root: Path) -> Iterable[Path]:
    drafts = root / ".aitp" / "local" / "drafts"
    return drafts.glob("*.md") if drafts.is_dir() else ()


def _canonical_entries(root: Path) -> Iterable[Path]:
    entries = root / ".aitp" / "topic" / "entries"
    return entries.glob("entry-*.md") if entries.is_dir() else ()


def _find_idempotency(root: Path, key: str) -> Path | None:
    for path in (*list(_canonical_entries(root)), *list(_drafts(root))):
        try:
            frontmatter, _, _ = parse_markdown(path)
        except AITPError:
            continue
        if frontmatter.get("idempotency_key") == key:
            return path
    return None


def prepare_entry(
    cwd: str | Path,
    kind: str,
    authority: str,
    *,
    created_by: str = "agent:unknown",
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    if kind not in ENTRY_KINDS:
        raise AITPError("invalid_kind", f"unsupported Entry kind: {kind}")
    if authority not in AUTHORITIES:
        raise AITPError("invalid_authority", f"unsupported authority: {authority}")
    if idempotency_key:
        existing = _find_idempotency(root, idempotency_key)
        if existing:
            return {
                "status": "existing",
                "path": str(existing.relative_to(root)),
                "idempotency_key": idempotency_key,
            }
    entry_id = f"entry-{uuid.uuid4().hex}"
    frontmatter: dict[str, Any] = {
        "schema": "aitp/lite-entry-0.1",
        "id": entry_id,
        "topic": store["topic_id"],
        "created_at": now_utc(),
        "created_by": created_by,
        "kind": kind,
        "authority": authority,
        "summary": "",
        "refs": [],
        "limitations": [],
        "resolves": [],
        "supersedes": [],
        "next_action": "",
    }
    if idempotency_key:
        frontmatter["idempotency_key"] = idempotency_key
    body = _template(f"record/{kind.replace('_', '-')}.md")
    path = root / ".aitp" / "local" / "drafts" / f"{entry_id}.md"
    atomic_write(path, render_markdown(frontmatter, body))
    return {
        "status": "prepared",
        "id": entry_id,
        "path": str(path.relative_to(root)),
        "save_command": f"aitp record save {path.relative_to(root)}",
    }


ENTRY_SECTIONS = {
    "observation": ["Durable Summary", "Observation And Conditions", "Locator And Uncertainty"],
    "result": ["Durable Summary", "Basis And Checks", "Validity And Implication"],
    "failure": ["Durable Summary", "Attempt, Expected, And Observed", "Evidence And Next Diagnostic"],
    "decision": ["Durable Summary", "Decision And Alternatives", "Reason, Scope, And Revisit Condition"],
    "source": ["Durable Summary", "Identity And Relevance", "Exact Locator And Claim Boundary"],
    "code_change": ["Durable Summary", "Change And Revision", "Verification And Scientific Effect"],
    "run": ["Durable Summary", "Question, Command, And Inputs", "Outputs, Result, And Status"],
    "closeout": ["Durable Summary", "Accomplished And Unresolved", "Next Action And Resume Refs"],
}


def _inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise AITPError("ref_escape", f"reference escapes workspace: {value}") from exc
    if not path.exists():
        raise AITPError("missing_ref", f"reference target does not exist: {value}")
    return path


def _git_has(root: Path, commit: str, target: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{commit}:{target}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def validate_refs(root: Path, refs: Any) -> None:
    if not isinstance(refs, list):
        raise AITPError("invalid_refs", "refs must be a list")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise AITPError("invalid_ref", f"refs[{index}] must be a map")
        target = ref.get("target")
        pin = ref.get("at")
        if not isinstance(target, str) or not target.strip():
            raise AITPError("invalid_ref", f"refs[{index}].target is required")
        if not isinstance(pin, str) or ":" not in pin:
            raise AITPError("invalid_ref", f"refs[{index}].at is required")
        scheme, value = pin.split(":", 1)
        if not value:
            raise AITPError("invalid_ref", f"refs[{index}].at has no value")
        external = target.startswith(("http://", "https://", "arxiv:", "doi:"))
        if scheme == "git":
            if external or not _git_has(root, value, target):
                raise AITPError(
                    "invalid_git_ref",
                    f"Git ref does not contain target: {target}@{value}",
                )
        elif scheme == "sha256":
            path = _inside(root, target)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != value.lower():
                raise AITPError("hash_mismatch", f"sha256 mismatch: {target}")
        elif scheme == "run":
            path = _inside(root, target)
            if not path.is_dir() or path.name != value:
                raise AITPError("invalid_run_ref", f"run ref mismatch: {target}")
        elif scheme == "version":
            if not external:
                raise AITPError(
                    "invalid_version_ref",
                    "version pins require an external persistent identifier",
                )
        elif scheme == "retrieved":
            if not target.startswith(("http://", "https://")):
                raise AITPError(
                    "invalid_retrieved_ref",
                    "retrieved pins require an HTTP(S) target",
                )
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise AITPError(
                    "invalid_retrieved_ref", f"invalid retrieval time: {value}"
                ) from exc
        else:
            raise AITPError("invalid_ref_pin", f"unsupported ref pin: {scheme}")


def _entry_map(root: Path) -> dict[str, tuple[dict[str, Any], Path]]:
    result: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in _canonical_entries(root):
        try:
            frontmatter, _, _ = parse_markdown(path)
        except AITPError:
            continue
        entry_id = frontmatter.get("id")
        if isinstance(entry_id, str):
            result[entry_id] = (frontmatter, path)
    return result


def _validate_relations(
    root: Path, frontmatter: dict[str, Any], field: str, entry_id: str
) -> None:
    values = frontmatter.get(field, [])
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise AITPError("invalid_relation", f"{field} must be a list of Entry IDs")
    entries = _entry_map(root)
    for value in values:
        if value == entry_id:
            raise AITPError("invalid_relation", f"{field} cannot target itself")
        if value not in entries:
            raise AITPError("missing_relation", f"{field} target does not exist: {value}")
        if field == "supersedes":
            target_time = str(entries[value][0].get("created_at", ""))
            if target_time >= str(frontmatter.get("created_at", "")):
                raise AITPError(
                    "invalid_supersession",
                    f"supersedes target is not older: {value}",
                )


def validate_entry(
    root: Path,
    frontmatter: dict[str, Any],
    body: str,
    *,
    validate_evidence: bool,
) -> None:
    required = {
        "schema",
        "id",
        "topic",
        "created_at",
        "created_by",
        "kind",
        "authority",
        "summary",
        "refs",
        "limitations",
        "resolves",
        "supersedes",
        "next_action",
    }
    missing = sorted(required - frontmatter.keys())
    if missing:
        raise AITPError("missing_field", f"missing Entry fields: {', '.join(missing)}")
    if frontmatter["schema"] != "aitp/lite-entry-0.1":
        raise AITPError("invalid_schema", "unsupported Entry schema")
    entry_id = frontmatter["id"]
    if not isinstance(entry_id, str) or not ENTRY_ID_RE.fullmatch(entry_id):
        raise AITPError("invalid_id", "invalid Entry ID")
    store = load_store(root)
    if frontmatter["topic"] != store["topic_id"]:
        raise AITPError("topic_mismatch", "Entry topic does not match repository")
    kind = frontmatter["kind"]
    if kind not in ENTRY_KINDS:
        raise AITPError("invalid_kind", f"unsupported Entry kind: {kind}")
    if frontmatter["authority"] not in AUTHORITIES:
        raise AITPError("invalid_authority", "invalid Entry authority")
    if not isinstance(frontmatter["summary"], str) or not frontmatter["summary"].strip():
        raise AITPError("missing_summary", "Entry summary must not be empty")
    limitations = frontmatter["limitations"]
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) and item.strip() for item in limitations
    ):
        raise AITPError("invalid_limitations", "limitations must be a string list")
    if kind in LIMITATION_REQUIRED_KINDS and not limitations:
        raise AITPError(
            "missing_limitations", f"{kind} requires at least one limitation"
        )
    refs = frontmatter["refs"]
    if kind in REF_REQUIRED_KINDS and not refs:
        raise AITPError("missing_refs", f"{kind} requires at least one pinned ref")
    if kind == "observation" and frontmatter["authority"] != "human" and not refs:
        raise AITPError(
            "missing_refs", "non-human observation requires at least one pinned ref"
        )
    if validate_evidence:
        validate_refs(root, refs)
        _validate_relations(root, frontmatter, "resolves", entry_id)
        _validate_relations(root, frontmatter, "supersedes", entry_id)
    if PROMPT_MARKER in body:
        raise AITPError("unfilled_template", "remove all AITP template prompts")
    for heading in ENTRY_SECTIONS[kind]:
        if not _section_content(body, heading):
            raise AITPError("empty_section", f"required section is empty: {heading}")


def save_entry(cwd: str | Path, draft: str | Path) -> dict[str, Any]:
    root = resolve_root(cwd)
    load_store(root)
    draft_path = (root / draft).resolve() if not Path(draft).is_absolute() else Path(draft).resolve()
    drafts_root = (root / ".aitp" / "local" / "drafts").resolve()
    try:
        draft_path.relative_to(drafts_root)
    except ValueError as exc:
        raise AITPError("invalid_draft", "Entry draft must be under .aitp/local/drafts") from exc
    frontmatter, body, text = parse_markdown(draft_path)
    validate_entry(root, frontmatter, body, validate_evidence=True)
    final = root / ".aitp" / "topic" / "entries" / f"{frontmatter['id']}.md"
    with store_lock(root):
        if final.exists():
            if final.read_bytes() == text.encode("utf-8"):
                return {
                    "status": "already_saved",
                    "path": str(final.relative_to(root)),
                }
            raise AITPError("id_conflict", f"Entry ID already exists: {frontmatter['id']}")
        atomic_write(final, text)
    return {"status": "saved", "path": str(final.relative_to(root))}
