"""Safe canonical record access for the AITP Markdown store."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
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
from brain.v5.query_index_delta_contracts import IndexProjectionOutcome
from brain.v5.query_index_locking import (
    LockTimeoutError,
    acquire_canonical_mutation_lease,
    acquire_ranked_lock,
    active_canonical_mutation_lease,
)
from brain.v5.record_path_safety import (
    record_lock_path as _record_lock_path,
    record_path as _record_path,
    validate_record_id as _validate_record_id,
)
from brain.v5.record_repository_payloads import (
    _frontmatter,
    _materialize_record,
    _persisted_frontmatter,
    _positive_revision,
    _string_list,
    _validate_payload_schema,
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
    index_projection: IndexProjectionOutcome = field(default_factory=IndexProjectionOutcome)


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
    frontmatter: dict[str, Any] | None = None
    body: str = ""


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
        active_lease = active_canonical_mutation_lease(self.ws)
        if active_lease is not None:
            active_lease.assert_active(self.ws)
            return self._write_under_mutation(
                family=family,
                spec=spec,
                envelope=envelope,
                frontmatter=frontmatter,
                body=body,
                policy=policy,
                path=path,
                record_ref=record_ref,
            )
        with acquire_canonical_mutation_lease(
            self.ws,
            timeout_seconds=policy.lock_timeout_seconds,
        ):
            return self._write_under_mutation(
                family=family,
                spec=spec,
                envelope=envelope,
                frontmatter=frontmatter,
                body=body,
                policy=policy,
                path=path,
                record_ref=record_ref,
            )

    def _write_under_mutation(
        self,
        *,
        family: str,
        spec: RecordFamilySpec,
        envelope: Any,
        frontmatter: dict[str, Any],
        body: str,
        policy: WritePolicy,
        path: Path,
        record_ref: str,
    ) -> WriteResult:
        predecessor_content_watermark = _family_content_watermark_if_indexed(
            self.ws,
            family,
        )
        with self._record_lock(spec, envelope.record_id, policy):
            result = self._write_canonical_locked(
                family=family,
                envelope=envelope,
                frontmatter=frontmatter,
                body=body,
                policy=policy,
                path=path,
                record_ref=record_ref,
            )
        return self._project_write_result(
            family,
            result,
            predecessor_content_watermark=predecessor_content_watermark,
        )

    def _write_canonical_locked(
        self,
        *,
        family: str,
        envelope: Any,
        frontmatter: dict[str, Any],
        body: str,
        policy: WritePolicy,
        path: Path,
        record_ref: str,
    ) -> WriteResult:
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

    def _project_write_result(
        self,
        family: str,
        result: WriteResult,
        *,
        predecessor_content_watermark: str,
    ) -> WriteResult:
        from brain.v5.query_index_delta import mark_query_delta_dirty, project_record_delta

        try:
            outcome = project_record_delta(
                self.ws,
                result.record_ref,
                predecessor_content_watermark=predecessor_content_watermark,
                predecessor_record_content_hash=result.previous_hash,
            )
        except Exception as exc:  # noqa: BLE001 - canonical success must survive projection failure.
            reason = f"{type(exc).__name__}: {exc}"
            try:
                outcome = mark_query_delta_dirty(
                    self.ws,
                    family,
                    reason=reason,
                    predecessor_content_watermark=predecessor_content_watermark,
                )
            except Exception as dirty_exc:  # noqa: BLE001 - surface both derived failures.
                outcome = IndexProjectionOutcome(
                    status="dirty",
                    dirty_families=(family,),
                    diagnostics=(reason, f"dirty marker failed: {type(dirty_exc).__name__}: {dirty_exc}"),
                    repair_required=True,
                )
        return replace(result, index_projection=outcome)

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
        try:
            _validate_record_id(record_id)
        except ValueError:
            return RecordReadResult(status="malformed_ref", record_ref=record_ref, path="")
        path = _record_path(self.ws, spec, record_id)
        if not path.exists():
            return RecordReadResult(
                status="not_found",
                record_ref=record_ref,
                path=str(path),
            )
        frontmatter: dict[str, Any] | None = None
        body = ""
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
                frontmatter=frontmatter,
                body=body,
            )
        return RecordReadResult(
            status="found",
            record_ref=record_ref,
            path=str(path),
            record=record,
            frontmatter=frontmatter,
            body=body,
        )

    @contextmanager
    def lock_record(
        self,
        family: str,
        record_id: str,
        *,
        policy: WritePolicy | None = None,
    ) -> Iterator[None]:
        """Serialize a domain transition around one canonical record identity."""

        spec = spec_for_family(family)
        write_policy = policy or WritePolicy()
        _record_lock_path(self.ws, spec, record_id)
        active_lease = active_canonical_mutation_lease(self.ws)
        if active_lease is not None:
            active_lease.assert_active(self.ws)
            yield
            return
        with acquire_canonical_mutation_lease(
            self.ws,
            timeout_seconds=write_policy.lock_timeout_seconds,
        ):
            yield

    @contextmanager
    def _record_lock(
        self,
        spec: RecordFamilySpec,
        record_id: str,
        policy: WritePolicy,
    ) -> Iterator[None]:
        lock_path = _record_lock_path(self.ws, spec, record_id)
        try:
            with acquire_ranked_lock(
                self.ws,
                "canonical-record",
                timeout_seconds=policy.lock_timeout_seconds,
                lock_path=lock_path,
            ):
                yield
        except LockTimeoutError as exc:
            raise RecordLockError(f"record lock is already held: {lock_path}") from exc


def _stored_content_hash(frontmatter: Mapping[str, Any], body: str) -> str:
    declared = str(frontmatter.get("record_content_hash") or "").strip()
    actual = canonical_record_hash(frontmatter, body)
    if declared and declared != actual:
        raise RecordIntegrityError("stored record content hash does not match canonical payload")
    return declared or actual


def _family_content_watermark_if_indexed(ws: WorkspacePaths, family: str) -> str:
    try:
        from brain.v5.query_index_delta_storage import effective_family_content_watermark

        return effective_family_content_watermark(ws, family)
    except Exception:  # noqa: BLE001 - derived failure cannot block canonical truth.
        return ""


def _spec_for_ref_kind(kind: str) -> RecordFamilySpec | None:
    normalized = kind.strip().replace("-", "_")
    for spec in record_family_specs().values():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if normalized in aliases:
            return spec
    return None


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
