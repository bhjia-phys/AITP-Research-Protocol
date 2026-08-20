"""Entry templates, validation, relations, and save."""

from __future__ import annotations

import hashlib
import json
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
ENTRY_REQUIRED = frozenset(
    "schema id topic created_at created_by kind authority summary refs limitations resolves supersedes next_action".split()
)
# Same grammar as the Topic slug rule (`_safe_slug` in workspace.py).
WORKSTREAM_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def _validate_workstreams(values: Any) -> None:
    if not isinstance(values, list):
        raise AITPError("invalid_workstreams", "invalid workstreams: not a list")
    if not values:
        raise AITPError("invalid_workstreams", "invalid workstreams: empty list")
    seen: set[str] = set()
    for slug in values:
        if not isinstance(slug, str) or not WORKSTREAM_RE.fullmatch(slug):
            detail = "empty element" if slug == "" else f"invalid slug: {slug!r}"
            raise AITPError("invalid_workstreams", f"invalid workstreams: {detail}")
        if slug in seen:
            raise AITPError("invalid_workstreams", f"invalid workstreams: duplicate workstream: {slug}")
        seen.add(slug)


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
    workstreams: list[str] | None = None,
) -> dict[str, Any]:
    root = resolve_root(cwd)
    store = load_store(root)
    if kind not in ENTRY_KINDS:
        raise AITPError("invalid_kind", f"unsupported Entry kind: {kind}")
    if authority not in AUTHORITIES:
        raise AITPError("invalid_authority", f"unsupported authority: {authority}")
    if authority == "agent" and created_by == "agent:unknown":
        raise AITPError("missing_provenance", "created_by is required for agent authority")
    # Validate workstreams before the idempotency short-circuit: an invalid
    # value must error even when the key already exists, and the raw value is
    # passed uncoerced so a bare string/int is rejected, not silently unpacked.
    if workstreams is not None:
        _validate_workstreams(workstreams)
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
    if workstreams:
        # validated above; write a copy of the caller's list
        frontmatter["workstreams"] = list(workstreams)
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


def _git_env(root: Path) -> bool:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0
    except OSError:
        return False


def validate_ref_shapes(refs: Any, field: str = "refs") -> None:
    if not isinstance(refs, list):
        raise AITPError("invalid_refs", f"{field} must be a list")
    for index, ref in enumerate(refs):
        if not isinstance(ref, dict):
            raise AITPError("invalid_ref", f"{field}[{index}] must be a map")
        target, pin = ref.get("target"), ref.get("at")
        if not isinstance(target, str) or not target.strip():
            raise AITPError("invalid_ref", f"{field}[{index}].target is required")
        if not isinstance(pin, str) or ":" not in pin:
            raise AITPError("invalid_ref", f"{field}[{index}].at is required")
        if not pin.split(":", 1)[1]:
            raise AITPError("invalid_ref", f"{field}[{index}].at has no value")
        if "locator" in ref and not isinstance(ref["locator"], str):
            raise AITPError("invalid_ref", f"{field}[{index}].locator must be a string")


def validate_json_safe(value: Any, field: str) -> None:
    try:
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise AITPError("invalid_type", f"{field} must contain only JSON-safe values") from exc


def validate_string_list(values: Any, field: str, target: str) -> None:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise AITPError("invalid_relation", f"{field} must be a list of {target}")


def validate_string_fields(values: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    invalid = next((field for field in fields if not isinstance(values[field], str)), None)
    if invalid: raise AITPError("invalid_type", f"{label} {invalid} must be a string")


def _verify_refs(
    root: Path, refs: Any, *, save: bool = False
) -> list[tuple[str, str, str]]:
    failures: list[tuple[str, str, str]] = []
    for ref in refs:
        target, pin = ref["target"], ref["at"]
        scheme, value = pin.split(":", 1)
        external = target.startswith(("http://", "https://", "arxiv:", "doi:"))
        if scheme == "sha256-once":
            if external:
                failures.append(("invalid_sha256_once_ref", f"sha256-once requires a local target: {target}", "error"))
                continue
            try:
                path = _inside(root, target)
            except AITPError as exc:
                code = "missing_ref" if save else "historical_ref_missing"
                grade = "error" if save else "warning"
                failures.append((code, str(exc), grade))
                continue
            if not path.is_file():
                code = "unreadable_ref" if save else "historical_ref_missing"
                grade = "error" if save else "warning"
                failures.append((code, f"reference target is not a file: {target}", grade))
                continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                code = "unreadable_ref" if save else "historical_ref_missing"
                grade = "error" if save else "warning"
                failures.append((code, f"reference target is unreadable: {target}: {exc}", grade))
                continue
            if digest != value.lower():
                if save:
                    failures.append(("hash_mismatch", f"sha256-once mismatch: {target}: expected {value}, actual {digest}", "error"))
                else:
                    failures.append(("historical_pin_drift", f"sha256-once drift: {target}: recorded {value}, current {digest}", "warning"))
            continue
        if scheme == "git":
            if external:
                failures.append(("invalid_git_ref", f"Git ref does not contain target: {target}@{value}", "error")); continue
            if not _git_env(root):
                failures.append(("invalid_git_ref", f"Git ref does not contain target: {target}@{value}", "warning")); continue
            if not _git_has(root, value, target):
                failures.append(("invalid_git_ref", f"Git ref does not contain target: {target}@{value}", "error")); continue
        elif scheme == "sha256":
            try:
                path = _inside(root, target)
            except AITPError as exc:
                failures.append((exc.code, str(exc), "error")); continue
            if not path.is_file():
                failures.append(("unreadable_ref", f"reference target is not a file: {target}", "error")); continue
            try:
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError as exc:
                failures.append(("unreadable_ref", f"reference target is unreadable: {target}: {exc}", "error")); continue
            if digest != value.lower():
                failures.append(("hash_mismatch", f"sha256 mismatch: {target}: expected {value}, actual {digest}", "error")); continue
        elif scheme == "run":
            try:
                path = _inside(root, target)
            except AITPError as exc:
                failures.append((exc.code, str(exc), "error")); continue
            if not path.is_dir() or path.name != value:
                failures.append(("invalid_run_ref", f"run ref mismatch: {target}", "error")); continue
        elif scheme == "version":
            if not external:
                failures.append(("invalid_version_ref", "version pins require an external persistent identifier", "error")); continue
        elif scheme == "retrieved":
            if not target.startswith(("http://", "https://")):
                failures.append(("invalid_retrieved_ref", "retrieved pins require an HTTP(S) target", "error")); continue
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                failures.append(("invalid_retrieved_ref", f"invalid retrieval time: {value}", "error")); continue
        else:
            failures.append(("invalid_ref_pin", f"unsupported ref pin: {scheme}", "error")); continue
    return failures


def validate_refs(root: Path, refs: Any) -> None:
    validate_ref_shapes(refs)
    for code, message, _ in _verify_refs(root, refs, save=True):
        raise AITPError(code, message)


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
    root: Path,
    frontmatter: dict[str, Any],
    field: str,
    entry_id: str,
    entries: dict[str, tuple[dict[str, Any], Path]] | None = None,
) -> None:
    values = frontmatter[field]
    entries = entries if entries is not None else _entry_map(root)
    for value in values:
        if value == entry_id:
            raise AITPError("invalid_relation", f"{field} cannot target itself")
        if value not in entries:
            raise AITPError("missing_relation", f"{field} target does not exist: {value}")


def validate_entry(
    root: Path,
    frontmatter: dict[str, Any],
    body: str,
    *,
    validate_evidence: bool,
    topic_id: str | None = None,
) -> None:
    missing = sorted(ENTRY_REQUIRED - frontmatter.keys())
    if missing:
        raise AITPError("missing_field", f"missing Entry fields: {', '.join(missing)}")
    if not isinstance(frontmatter["schema"], str) or frontmatter["schema"] != "aitp/lite-entry-0.1":
        raise AITPError("invalid_schema", "unsupported Entry schema")
    entry_id = frontmatter["id"]
    if not isinstance(entry_id, str) or not ENTRY_ID_RE.fullmatch(entry_id):
        raise AITPError("invalid_id", "invalid Entry ID")
    if topic_id is None:
        topic_id = load_store(root)["topic_id"]
    if not isinstance(frontmatter["topic"], str) or frontmatter["topic"] != topic_id:
        raise AITPError("topic_mismatch", "Entry topic does not match repository")
    if not isinstance(frontmatter["created_at"], str):
        raise AITPError("invalid_timestamp", "Entry created_at must be a string")
    validate_string_fields(frontmatter, ("created_by", "next_action"), "Entry")
    if "workstreams" in frontmatter:
        _validate_workstreams(frontmatter["workstreams"])
    kind = frontmatter["kind"]
    if not isinstance(kind, str) or kind not in ENTRY_KINDS:
        raise AITPError("invalid_kind", f"unsupported Entry kind: {kind}")
    if not isinstance(frontmatter["authority"], str) or frontmatter["authority"] not in AUTHORITIES:
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
    validate_ref_shapes(refs)
    for field in ("resolves", "supersedes"):
        validate_string_list(frontmatter[field], field, "Entry IDs")
    if "idempotency_key" in frontmatter and not isinstance(frontmatter["idempotency_key"], str):
        raise AITPError("invalid_idempotency_key", "idempotency_key must be a string")
    validate_json_safe(frontmatter, "Entry frontmatter")
    if not isinstance(body, str):
        raise AITPError("invalid_type", "Entry body must be a string")
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
