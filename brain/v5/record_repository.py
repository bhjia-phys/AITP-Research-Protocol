"""Safe canonical record access for the AITP Markdown store."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from brain.v5.markdown import read_md, write_md, write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import (
    RecordActor,
    canonical_record_hash,
    envelope_for_record,
    read_envelope_compat,
)
from brain.v5.record_family_registry import (
    RecordFamilySpec,
    record_family_specs,
    spec_for_family,
)


class RecordCollisionError(RuntimeError):
    """Raised when one canonical id is reused for different content."""


class RecordLockError(RuntimeError):
    """Raised when a canonical record lock is already held."""


class RecordCompareAndSwapError(RuntimeError):
    """Raised when a revision does not target the current content hash."""


class RecordIntegrityError(RuntimeError):
    """Raised when persisted content disagrees with its declared hash."""


@dataclass(frozen=True)
class WritePolicy:
    mode: str = "create_or_idempotent"
    expected_hash: str = ""
    lock_timeout_seconds: float = 2.0
    stale_lock_after_seconds: float = 0.0


@dataclass(frozen=True)
class WriteResult:
    status: str
    record_ref: str
    path: str
    content_hash: str
    previous_hash: str = ""
    revision: int = 1
    archive_path: str = ""


@dataclass(frozen=True)
class RecordReadIssue:
    family: str
    path: str
    error_type: str
    message: str


@dataclass(frozen=True)
class RecordReadReport:
    records: tuple[Any, ...]
    checked_count: int
    loaded_count: int
    malformed: tuple[RecordReadIssue, ...]
    missing: bool


@dataclass(frozen=True)
class RecordReadResult:
    status: str
    record_ref: str
    path: str
    record: Any | None = None
    issue: RecordReadIssue | None = None


class RecordRepository:
    """Resolve record families and enforce collision-safe canonical writes."""

    def __init__(self, ws: WorkspacePaths, *, actor: RecordActor):
        self.ws = ws
        self.actor = actor

    def write(
        self,
        family: str,
        record: Any,
        *,
        body: str = "",
        policy: WritePolicy | None = None,
    ) -> WriteResult:
        policy = policy or WritePolicy()
        if policy.mode not in {"create_or_idempotent", "revision"}:
            raise ValueError(f"unsupported write policy mode: {policy.mode}")

        spec = spec_for_family(family)
        frontmatter = _frontmatter(record)
        _validate_payload_schema(frontmatter, spec)
        envelope = envelope_for_record(
            record,
            family=family,
            actor=self.actor,
            body=body,
        )
        path = _record_path(self.ws, spec, envelope.record_id)
        record_ref = f"{spec.ref_kind}:{envelope.record_id}"

        with self._record_lock(spec, envelope.record_id, policy):
            if path.exists():
                stored, stored_body = read_md(path)
                previous_hash = _stored_content_hash(stored, stored_body)
                if policy.expected_hash and policy.expected_hash != previous_hash:
                    raise RecordCompareAndSwapError(
                        f"expected hash does not match current record {envelope.record_id}"
                    )
                if policy.mode == "revision" and not policy.expected_hash:
                    raise RecordCompareAndSwapError(
                        f"expected hash is required to revise record {envelope.record_id}"
                    )
                if previous_hash == envelope.content_hash:
                    return WriteResult(
                        status="unchanged",
                        record_ref=record_ref,
                        path=str(path),
                        content_hash=envelope.content_hash,
                        previous_hash=previous_hash,
                        revision=_positive_revision(stored.get("revision")),
                    )
                if policy.mode == "revision":
                    archive_path = (
                        self.ws.root
                        / "revisions"
                        / family
                        / envelope.record_id
                        / f"{previous_hash}.md"
                    )
                    write_text_atomic(archive_path, path.read_text(encoding="utf-8"))
                    revision = _positive_revision(stored.get("revision")) + 1
                    supersedes = [
                        f"{record_ref}@sha256:{previous_hash}",
                        *_string_list(frontmatter.get("supersedes")),
                    ]
                    persisted = _persisted_frontmatter(
                        frontmatter,
                        envelope,
                        revision=revision,
                        supersedes=supersedes,
                    )
                    write_md(path, persisted, body)
                    return WriteResult(
                        status="revised",
                        record_ref=record_ref,
                        path=str(path),
                        content_hash=envelope.content_hash,
                        previous_hash=previous_hash,
                        revision=revision,
                        archive_path=str(archive_path),
                    )
                raise RecordCollisionError(
                    f"record id {envelope.record_id} already exists with different content"
                )

            if policy.mode == "revision" or policy.expected_hash:
                raise RecordCompareAndSwapError(
                    f"expected hash cannot revise missing record {envelope.record_id}"
                )

            persisted = _persisted_frontmatter(frontmatter, envelope)
            write_md(path, persisted, body)
            return WriteResult(
                status="created",
                record_ref=record_ref,
                path=str(path),
                content_hash=envelope.content_hash,
                revision=1,
            )

    def list(self, family: str) -> RecordReadReport:
        """Read every record in a family and report every malformed path."""

        spec = spec_for_family(family)
        paths, storage_exists = record_family_paths(self.ws, spec)
        if not storage_exists:
            return RecordReadReport((), 0, 0, (), True)

        records: list[Any] = []
        malformed: list[RecordReadIssue] = []
        for path in paths:
            try:
                frontmatter, body = read_md(path)
                _stored_content_hash(frontmatter, body)
                read_envelope_compat(frontmatter, spec, path, body=body)
                records.append(_materialize_record(frontmatter, spec))
            except Exception as exc:  # noqa: BLE001 - exhaustive reads must report all failures.
                malformed.append(
                    RecordReadIssue(
                        family=family,
                        path=str(path),
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )
        return RecordReadReport(
            records=tuple(records),
            checked_count=len(paths),
            loaded_count=len(records),
            malformed=tuple(malformed),
            missing=False,
        )

    def read(self, record_ref: str) -> RecordReadResult:
        """Read one exact typed ref without converting errors into absence."""

        kind, separator, record_id = record_ref.partition(":")
        if not separator or not kind.strip() or not record_id.strip():
            return RecordReadResult(status="malformed_ref", record_ref=record_ref, path="")
        spec = _spec_for_ref_kind(kind)
        if spec is None:
            return RecordReadResult(status="unsupported_ref", record_ref=record_ref, path="")
        path = _record_path(self.ws, spec, record_id)
        if not path.exists():
            return RecordReadResult(
                status="not_found",
                record_ref=record_ref,
                path=str(path),
            )
        try:
            frontmatter, body = read_md(path)
            _stored_content_hash(frontmatter, body)
            read_envelope_compat(frontmatter, spec, path, body=body)
            record = _materialize_record(frontmatter, spec)
        except Exception as exc:  # noqa: BLE001 - exact reads preserve parse diagnostics.
            issue = RecordReadIssue(
                family=spec.family,
                path=str(path),
                error_type=type(exc).__name__,
                message=str(exc),
            )
            return RecordReadResult(
                status="malformed",
                record_ref=record_ref,
                path=str(path),
                issue=issue,
            )
        return RecordReadResult(
            status="found",
            record_ref=record_ref,
            path=str(path),
            record=record,
        )

    @contextmanager
    def _record_lock(
        self,
        spec: RecordFamilySpec,
        record_id: str,
        policy: WritePolicy,
    ) -> Iterator[None]:
        lock_path = self.ws.root / "runtime" / "locks" / spec.family / f"{record_id}.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + max(0.0, policy.lock_timeout_seconds)
        while True:
            try:
                descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError as exc:
                if _remove_stale_lock(lock_path, policy.stale_lock_after_seconds):
                    continue
                if time.monotonic() >= deadline:
                    raise RecordLockError(f"record lock is already held: {lock_path}") from exc
                time.sleep(0.01)
        try:
            os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
            os.close(descriptor)
            yield
        finally:
            try:
                os.close(descriptor)
            except OSError:
                pass
            lock_path.unlink(missing_ok=True)


def _frontmatter(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("record must be a dataclass or mapping")


def _persisted_frontmatter(
    frontmatter: Mapping[str, Any],
    envelope: Any,
    *,
    revision: int = 1,
    supersedes: list[str] | None = None,
) -> dict[str, Any]:
    persisted = dict(frontmatter)
    persisted.update(
        {
            "record_id": envelope.record_id,
            "record_family": envelope.record_family,
            "schema_version": envelope.schema_version,
            "created_at": envelope.created_at,
            "created_by": asdict(envelope.created_by),
            "record_content_hash": envelope.content_hash,
            "revision": revision,
            "lifecycle_status": envelope.lifecycle_status,
            "supersedes": list(supersedes or envelope.supersedes),
            "trust_effect": envelope.trust_effect,
        }
    )
    return persisted


def _stored_content_hash(frontmatter: Mapping[str, Any], body: str) -> str:
    declared = str(frontmatter.get("record_content_hash") or "").strip()
    actual = canonical_record_hash(frontmatter, body)
    if declared and declared != actual:
        raise RecordIntegrityError("stored record content hash does not match canonical payload")
    return declared or actual


def _positive_revision(value: Any) -> int:
    if isinstance(value, bool):
        return 1
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str) and value.isdigit() and int(value) > 0:
        return int(value)
    return 1


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    items = value if isinstance(value, (list, tuple, set, frozenset)) else [value]
    return [str(item).strip() for item in items if str(item).strip()]


def _remove_stale_lock(lock_path: Path, stale_after_seconds: float) -> bool:
    if stale_after_seconds <= 0:
        return False
    try:
        age = time.time() - lock_path.stat().st_mtime
        if age < stale_after_seconds:
            return False
        lock_path.unlink()
        return True
    except FileNotFoundError:
        return True


def _materialize_record(frontmatter: Mapping[str, Any], spec: RecordFamilySpec) -> Any:
    if spec.record_class is None:
        return dict(frontmatter)
    values = dict(frontmatter)
    if spec.id_field not in values:
        for legacy_field in spec.legacy_id_fields:
            if values.get(legacy_field):
                values[spec.id_field] = values[legacy_field]
                break
    if "topic_id" not in values and values.get("topic"):
        values["topic_id"] = values["topic"]
    allowed = {field.name for field in fields(spec.record_class)}
    return spec.record_class(**{key: value for key, value in values.items() if key in allowed})


def _validate_payload_schema(frontmatter: Mapping[str, Any], spec: RecordFamilySpec) -> None:
    kind = str(frontmatter.get("kind") or "").strip()
    if kind and kind != spec.record_kind:
        raise ValueError(
            f"record kind {kind!r} does not match family {spec.family!r}"
        )
    _materialize_record(frontmatter, spec)


def _spec_for_ref_kind(kind: str) -> RecordFamilySpec | None:
    normalized = kind.strip().replace("-", "_")
    for spec in record_family_specs().values():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if normalized in aliases:
            return spec
    return None


def _record_path(ws: WorkspacePaths, spec: RecordFamilySpec, record_id: str) -> Path:
    if spec.is_registry_family:
        return ws.root / spec.relative_dir / f"{record_id}.md"
    if spec.family == "contexts":
        return ws.context_dir(record_id) / "context.md"
    if spec.family == "topics":
        return ws.topic_dir(record_id) / "topic.md"
    if spec.family == "sessions":
        return ws.session_path(record_id)
    if spec.family == "memory_entries":
        return ws.root / "memory" / "l2" / "entries" / f"{record_id}.md"
    raise ValueError(f"unsupported special record family: {spec.family}")


def record_family_paths(
    ws: WorkspacePaths,
    spec: RecordFamilySpec,
) -> tuple[list[Path], bool]:
    """Return sorted canonical paths and whether the family storage exists."""

    if spec.is_registry_family:
        directory = ws.root / spec.relative_dir
        return sorted(directory.glob("*.md")) if directory.exists() else [], directory.exists()
    if spec.family == "contexts":
        directory = ws.root / "contexts"
        return sorted(directory.glob("*/context.md")) if directory.exists() else [], directory.exists()
    if spec.family == "topics":
        directory = ws.root / "topics"
        return sorted(directory.glob("*/topic.md")) if directory.exists() else [], directory.exists()
    if spec.family == "sessions":
        directory = ws.root / "runtime" / "sessions"
        return sorted(directory.glob("*.md")) if directory.exists() else [], directory.exists()
    if spec.family == "memory_entries":
        directory = ws.root / "memory" / "l2" / "entries"
        return sorted(directory.glob("*.md")) if directory.exists() else [], directory.exists()
    return [], False
