"""Workspace root resolution, store metadata, init, and write lock."""

from __future__ import annotations

import hashlib
import json
import os
import re
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
from typing import Any

from .md import AITPError, atomic_write, now_utc, render_markdown


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
        marker = candidate / ".git"
        if marker.is_file() or (marker.is_dir() and (marker / "HEAD").is_file()):
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
    try:
        store_text = store_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise AITPError("malformed_store", f"store metadata is unreadable: {store_path}: {exc}") from exc
    result: dict[str, str] = {}
    for line in store_text.splitlines():
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


def _store_files(root: Path, topic_id: str, title: str) -> dict[Path, str]:
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
    return {
        root / ".aitp" / ".gitignore": "local/\n",
        root / ".aitp" / "STORE.toml": store,
        root / ".aitp" / "topic" / "TOPIC.md": render_markdown(
            topic_frontmatter, topic_body
        ),
        root / ".aitp" / "local" / "config.toml": local,
    }


def _init_files(root: Path, topic_id: str, title: str) -> dict[Path, str]:
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
        **_store_files(root, topic_id, title),
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
    _write_files(root, rendered, directories, dry_run)
    return {
        "status": "dry_run" if dry_run else "initialized",
        "root": str(root),
        "topic_id": topic_id,
        "created_files": [str(path.relative_to(root)) for path in rendered],
        "mode": "init",
    }


def _write_files(
    root: Path, rendered: dict[Path, str], directories: list[Path], dry_run: bool
) -> None:
    if dry_run:
        return
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
        # prune the created dirs and any empty ancestors mkdir(parents=True)
        # made (e.g. .aitp, .aitp/topic), up to the workspace root.
        for path in sorted(
            {p for p in created if p.is_dir()},
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            for candidate in (path, *path.parents):
                if candidate == root:
                    break
                try:
                    candidate.rmdir()
                except OSError:
                    break
        raise


def adopt_workspace(
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
    rendered = _store_files(root, topic_id, title)
    directories = [
        root / ".aitp" / "topic" / "entries",
        root / ".aitp" / "topic" / "notes",
        root / ".aitp" / "local" / "drafts",
        root / ".aitp" / "local" / "scratch",
        root / ".aitp" / "local" / "locks",
    ]
    _write_files(root, rendered, directories, dry_run)
    return {
        "status": "dry_run" if dry_run else "initialized",
        "root": str(root),
        "topic_id": topic_id,
        "created_files": [str(path.relative_to(root)) for path in rendered],
        "mode": "adopt",
    }


def build_inventory(cwd: str | Path, path: str | Path, name: str) -> dict[str, Any]:
    root = resolve_root(cwd)
    load_store(root)
    _safe_slug(name, "inventory name")
    scan_root = Path(path).expanduser().resolve()
    if not scan_root.is_dir():
        raise AITPError("invalid_root", f"workspace does not exist: {scan_root}")
    store_aitp = (root / ".aitp").resolve()
    entries: list[dict[str, Any]] = []
    total_bytes = 0

    def scan(directory: Path) -> None:
        nonlocal total_bytes
        for entry in sorted(os.scandir(directory), key=lambda e: e.name):
            full = Path(entry.path)
            if entry.name == ".git":
                continue
            relative = str(full.relative_to(scan_root))
            if full.is_symlink():
                entries.append({"path": relative, "type": "symlink"})
            elif full.is_dir():
                if full.resolve() != store_aitp:
                    scan(full)
            else:
                data = full.read_bytes()
                entries.append({"path": relative,
                                "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
                total_bytes += len(data)

    scan(scan_root)
    entries.sort(key=lambda item: item["path"])
    manifest = {
        "schema": "aitp/legacy-inventory-0.1", "name": name,
        "generated_at": now_utc(), "root": str(scan_root), "files": entries,
    }
    manifest_path = root / ".aitp" / "local" / "legacy" / f"{name}-inventory.json"
    atomic_write(manifest_path,
                 json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"status": "ok", "name": name,
            "manifest": str(manifest_path.relative_to(root)),
            "files": sum(1 for item in entries if "sha256" in item), "bytes": total_bytes}


def _lock_owner_alive(lock_path: Path) -> bool:
    """True when the recorded owner process is alive; pidless locks are stale."""
    try:
        pid = int(lock_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, OverflowError):
        return False
    except OSError:
        return True


@contextmanager
def store_lock(root: Path):
    lock_path = root / ".aitp" / "local" / "locks" / "write.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in (0, 1):
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.close(descriptor)
            break
        except FileExistsError:
            if attempt or _lock_owner_alive(lock_path):
                raise AITPError("store_busy", "another AITP write is in progress")
            lock_path.unlink(missing_ok=True)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)
