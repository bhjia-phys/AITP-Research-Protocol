from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path
from typing import Any, Iterable

import yaml


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
NOTE_MODES = {"working", "theory"}
AUTHORITIES = {"human", "agent", "source", "tool"}
REF_REQUIRED_KINDS = {"result", "failure", "source", "code_change", "run"}
LIMITATION_REQUIRED_KINDS = {"observation", "result", "source", "run"}
ENTRY_ID_RE = re.compile(r"^entry-[0-9a-f]{32}$")
NOTE_ID_RE = re.compile(r"^note-[0-9a-f]{32}$")
PROMPT_MARKER = "<!-- aitp:"


class AITPError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).rstrip()


def render_markdown(frontmatter: dict[str, Any], body: str) -> str:
    return f"---\n{dump_yaml(frontmatter)}\n---\n\n{body.strip()}\n"


def parse_markdown(path: Path) -> tuple[dict[str, Any], str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AITPError("unreadable_record", f"{path}: {exc}") from exc
    if not text.startswith("---\n"):
        raise AITPError("malformed_record", f"{path}: missing YAML frontmatter")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise AITPError("malformed_record", f"{path}: unclosed YAML frontmatter")
    try:
        frontmatter = yaml.safe_load(text[4:marker]) or {}
    except yaml.YAMLError as exc:
        raise AITPError("malformed_record", f"{path}: invalid YAML: {exc}") from exc
    if not isinstance(frontmatter, dict):
        raise AITPError("malformed_record", f"{path}: frontmatter must be a map")
    return frontmatter, text[marker + 5 :].lstrip("\n"), text


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def _template(relative: str, values: dict[str, str] | None = None) -> str:
    resource = files("aitp").joinpath("resources", "templates", *relative.split("/"))
    text = resource.read_text(encoding="utf-8")
    for key, value in (values or {}).items():
        text = text.replace("{" + key + "}", value)
    return text


def _safe_slug(value: str, label: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", value):
        raise AITPError(
            "invalid_slug",
            f"{label} must use lowercase letters, digits, and hyphens",
        )
    return value


def _git_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def resolve_root(cwd: str | Path) -> Path:
    start = Path(cwd).expanduser().resolve()
    if not start.is_dir():
        raise AITPError("invalid_root", f"workspace does not exist: {start}")
    existing_store = next(
        (p for p in (start, *start.parents) if (p / ".aitp" / "STORE.toml").is_file()),
        None,
    )
    return existing_store or _git_root(start) or start


def _ensure_safe_root(root: Path) -> None:
    home = Path.home().resolve()
    if root == Path("/") or root == home or root.parent == Path("/"):
        raise AITPError("unsafe_root", f"refusing broad workspace root: {root}")
    if not os.access(root, os.W_OK):
        raise AITPError("unwritable_root", f"workspace is not writable: {root}")


def _quoted_toml(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def load_store(root: Path) -> dict[str, str]:
    store_path = root / ".aitp" / "STORE.toml"
    if not store_path.is_file():
        raise AITPError("not_initialized", f"no AITP store at {root}")
    result: dict[str, str] = {}
    for line in store_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, raw = (part.strip() for part in line.split("=", 1))
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, str):
            result[key] = value
    if not result.get("topic_id") or not result.get("title"):
        raise AITPError("malformed_store", f"invalid store metadata: {store_path}")
    return result


def _init_files(root: Path, topic_id: str, title: str) -> dict[Path, str]:
    created_at = now_utc()
    topic_frontmatter = {
        "schema": "aitp/lite-topic-0.1",
        "id": topic_id,
        "title": title,
        "created_at": created_at,
        "created_by": "tool:aitp-init",
    }
    topic_body = _template(
        "init/topic.md",
        {"title": title, "goal": "Not established yet"},
    )
    store = "\n".join(
        [
            'schema = "aitp/lite-store-0.1"',
            f"topic_id = {_quoted_toml(topic_id)}",
            f"title = {_quoted_toml(title)}",
            "",
        ]
    )
    local = f"workspace_root = {_quoted_toml(str(root))}\n"
    root_readme = _template("init/root-readme.md", {"title": title})
    purposes = {
        "theory": "Analytic derivations, proofs, examples, and consistency checks.",
        "software": "Reusable scientific software and tests.",
        "calculations": "Reproducible numerical or symbolic calculations.",
        "data": "External, raw, and derived dataset provenance.",
        "figures": "Curated reusable figure pipelines.",
        "references": "Bibliography and source-specific reading notes.",
        "manuscripts": "Self-contained notes and publication manuscripts.",
    }
    result = {
        root / "README.md": root_readme,
        root / ".gitignore": "\n".join(
            [
                ".aitp/local/",
                "**/__pycache__/",
                "**/.pytest_cache/",
                "**/build/",
                "**/.venv/",
                "",
            ]
        ),
        root / ".aitp" / ".gitignore": "local/\n",
        root / ".aitp" / "STORE.toml": store,
        root / ".aitp" / "topic" / "TOPIC.md": render_markdown(
            topic_frontmatter, topic_body
        ),
        root / ".aitp" / "local" / "config.toml": local,
        root / "theory" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "theory", "purpose": purposes["theory"]},
        ),
        root / "theory" / "INDEX.md": "# Theory Index\n\nNo theory threads yet.\n",
        root / "theory" / "CONVENTIONS.md": (
            "# Conventions\n\nNot established yet.\n"
        ),
        root / "software" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "software", "purpose": purposes["software"]},
        ),
        root / "calculations" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "calculations", "purpose": purposes["calculations"]},
        ),
        root / "data" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "data", "purpose": purposes["data"]},
        ),
        root / "figures" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "figures", "purpose": purposes["figures"]},
        ),
        root / "references" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "references", "purpose": purposes["references"]},
        ),
        root / "references" / "library.bib": "",
        root / "manuscripts" / "README.md": _template(
            "init/folder-readme.md",
            {"folder": "manuscripts", "purpose": purposes["manuscripts"]},
        ),
    }
    return result


def init_workspace(
    cwd: str | Path,
    topic_id: str,
    title: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = resolve_root(cwd)
    _ensure_safe_root(root)
    _safe_slug(topic_id, "topic ID")
    title = title.strip()
    if not title:
        raise AITPError("invalid_title", "topic title must not be empty")
    if (root / ".aitp").exists():
        raise AITPError("already_initialized", f"AITP already exists at {root}")
    unexpected = [path.name for path in root.iterdir() if path.name != ".git"]
    if unexpected:
        raise AITPError(
            "workspace_not_blank",
            f"workspace must be blank; found: {', '.join(sorted(unexpected))}",
        )
    rendered = _init_files(root, topic_id, title)
    directories = [
        root / ".aitp" / "topic" / "entries",
        root / ".aitp" / "topic" / "notes",
        root / ".aitp" / "local" / "drafts",
        root / ".aitp" / "local" / "scratch",
        root / ".aitp" / "local" / "locks",
        root / "data" / "external",
        root / "data" / "raw",
        root / "data" / "derived",
        root / "references" / "reading-notes",
    ]
    if not dry_run:
        created: list[Path] = []
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                created.append(directory)
            for path, text in rendered.items():
                if path.exists():
                    raise AITPError("path_conflict", f"refusing overwrite: {path}")
                atomic_write(path, text)
                created.append(path)
        except Exception:
            for path in reversed(created):
                if path.is_file():
                    path.unlink(missing_ok=True)
            for path in sorted(
                {p for p in created if p.is_dir()},
                key=lambda p: len(p.parts),
                reverse=True,
            ):
                try:
                    path.rmdir()
                except OSError:
                    pass
            raise
    return {
        "status": "dry_run" if dry_run else "initialized",
        "root": str(root),
        "topic_id": topic_id,
        "created_files": [str(path.relative_to(root)) for path in rendered],
    }


def _drafts(root: Path) -> Iterable[Path]:
    drafts = root / ".aitp" / "local" / "drafts"
    return drafts.glob("*.md") if drafts.is_dir() else ()


def _canonical_entries(root: Path) -> Iterable[Path]:
    entries = root / ".aitp" / "topic" / "entries"
    return entries.glob("entry-*.md") if entries.is_dir() else ()


def _find_idempotency(root: Path, key: str) -> Path | None:
    for path in (*list(_drafts(root)), *list(_canonical_entries(root))):
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


def _section_content(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)"
    )
    match = pattern.search(body)
    if not match:
        return ""
    content = re.sub(r"<!--\s*aitp:.*?-->", "", match.group(1), flags=re.S)
    return content.strip()


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


@contextmanager
def store_lock(root: Path):
    lock_path = root / ".aitp" / "local" / "locks" / "write.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise AITPError("store_busy", "another AITP write is in progress") from exc
    os.close(descriptor)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


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
