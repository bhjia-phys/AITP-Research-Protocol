"""Hash-qualified record resolution and deterministic dependency closure."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Mapping

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import RecordActor, read_envelope_compat
from brain.v5.record_family_registry import RecordFamilySpec, record_family_specs
from brain.v5.record_path_safety import validate_record_id
from brain.v5.record_repository import RecordRepository, _stored_content_hash
from brain.v5.record_repository_payloads import _materialize_record, _positive_revision


_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class PinnedRecordError(RuntimeError):
    """Base error for an unresolved or inconsistent frozen dependency."""


class PinnedRecordMismatchError(PinnedRecordError):
    """Raised when a typed ref cannot resolve the requested hash/revision."""


@dataclass(frozen=True, order=True)
class PinnedRecordRef:
    record_ref: str
    content_hash: str
    revision: int

    def __post_init__(self) -> None:
        if not _typed_ref_parts(self.record_ref):
            raise ValueError("record_ref must be an exact '<kind>:<record-id>' typed ref")
        if not _SHA256_PATTERN.fullmatch(self.content_hash):
            raise ValueError("content_hash must be a lowercase SHA-256 hex digest")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise ValueError("revision must be a positive integer")


@dataclass(frozen=True)
class PinnedRecordVersion:
    pinned_ref: PinnedRecordRef
    record: Any
    frontmatter: dict[str, Any]
    body: str
    path: str
    version_source: str


@dataclass(frozen=True, order=True)
class FrozenDependencyEdge:
    owner_ref: str
    field_name: str
    target_ref: str
    target_hash: str
    target_revision: int


@dataclass(frozen=True)
class FrozenDependencyManifest:
    roots: tuple[PinnedRecordRef, ...]
    nodes: tuple[PinnedRecordRef, ...]
    edges: tuple[FrozenDependencyEdge, ...]
    closure_hash: str
    truth_source: str = "typed_canonical_record_versions"
    can_update_claim_trust: bool = False


def pin_current_record(ws: WorkspacePaths, record_ref: str) -> PinnedRecordRef:
    """Pin the current exact record after repository integrity validation."""

    result = _repository(ws).read(record_ref)
    if result.status != "found" or result.record is None or result.frontmatter is None:
        detail = result.issue.message if result.issue else result.status
        raise PinnedRecordMismatchError(f"cannot pin current record {record_ref!r}: {detail}")
    content_hash = _stored_content_hash(result.frontmatter, result.body)
    return PinnedRecordRef(
        record_ref=result.record_ref,
        content_hash=content_hash,
        revision=_positive_revision(result.frontmatter.get("revision")),
    )


def pin_record_hash(
    ws: WorkspacePaths,
    record_ref: str,
    content_hash: str,
    *,
    revision: int = 0,
) -> PinnedRecordRef:
    """Pin an exact current or archived hash, deriving a missing revision safely."""

    if not _SHA256_PATTERN.fullmatch(content_hash):
        raise ValueError("content_hash must be a lowercase SHA-256 digest")
    if revision:
        target = PinnedRecordRef(
            record_ref=record_ref,
            content_hash=content_hash,
            revision=revision,
        )
        get_record_version(ws, target)
        return target
    spec, record_id = _spec_and_id(record_ref)
    current = _repository(ws).read(record_ref)
    if current.status == "found" and current.frontmatter is not None:
        if _stored_content_hash(current.frontmatter, current.body) == content_hash:
            return PinnedRecordRef(
                record_ref=record_ref,
                content_hash=content_hash,
                revision=_positive_revision(current.frontmatter.get("revision")),
            )
    archive_path = (
        ws.root
        / "revisions"
        / spec.family
        / record_id
        / f"{content_hash}.md"
    )
    if not archive_path.exists():
        raise PinnedRecordMismatchError(
            f"content hash {content_hash} is not available for {record_ref}"
        )
    try:
        frontmatter, body = read_md(archive_path)
        actual_hash = _stored_content_hash(frontmatter, body)
        read_envelope_compat(frontmatter, spec, archive_path, body=body)
    except Exception as exc:  # noqa: BLE001 - archive corruption is a strict pin failure.
        raise PinnedRecordMismatchError(
            f"archived record version is invalid for {record_ref}: {exc}"
        ) from exc
    if actual_hash != content_hash:
        raise PinnedRecordMismatchError(
            f"archived content hash does not match {record_ref}"
        )
    target = PinnedRecordRef(
        record_ref=record_ref,
        content_hash=content_hash,
        revision=_positive_revision(frontmatter.get("revision")),
    )
    get_record_version(ws, target)
    return target


def get_record_version(
    ws: WorkspacePaths,
    pinned: PinnedRecordRef | Mapping[str, Any],
) -> PinnedRecordVersion:
    """Resolve an exact current or archived canonical record version."""

    target = _coerce_pinned_ref(pinned)
    spec, record_id = _spec_and_id(target.record_ref)
    current = _repository(ws).read(target.record_ref)
    if current.status == "found" and current.frontmatter is not None:
        current_hash = _stored_content_hash(current.frontmatter, current.body)
        if current_hash == target.content_hash:
            return _version_from_payload(
                target,
                spec,
                current.frontmatter,
                current.body,
                Path(current.path),
                "current",
            )
    archive_path = (
        ws.root
        / "revisions"
        / spec.family
        / record_id
        / f"{target.content_hash}.md"
    )
    if not archive_path.exists():
        current_detail = ""
        if current.status == "malformed":
            detail = current.issue.message if current.issue else "malformed current record"
            current_detail = f"; current record is malformed: {detail}"
        raise PinnedRecordMismatchError(
            f"content hash {target.content_hash} is not available for "
            f"{target.record_ref}{current_detail}"
        )
    try:
        frontmatter, body = read_md(archive_path)
        actual_hash = _stored_content_hash(frontmatter, body)
        read_envelope_compat(frontmatter, spec, archive_path, body=body)
    except Exception as exc:  # noqa: BLE001 - convert archive corruption to one strict error.
        raise PinnedRecordMismatchError(
            f"archived record version is invalid for {target.record_ref}: {exc}"
        ) from exc
    if actual_hash != target.content_hash:
        raise PinnedRecordMismatchError(
            f"archived content hash does not match {target.record_ref}"
        )
    return _version_from_payload(
        target,
        spec,
        frontmatter,
        body,
        archive_path,
        "archive",
    )


def build_frozen_dependency_manifest(
    ws: WorkspacePaths,
    roots: list[PinnedRecordRef | Mapping[str, Any]],
) -> FrozenDependencyManifest:
    """Resolve the recursive registry-declared dependency graph by exact version."""

    if not roots:
        raise ValueError("at least one pinned root is required")
    root_refs = tuple(sorted({_coerce_pinned_ref(item) for item in roots}))
    pending = list(root_refs)
    nodes: dict[PinnedRecordRef, PinnedRecordRef] = {}
    edges: set[FrozenDependencyEdge] = set()

    while pending:
        owner = pending.pop(0)
        if owner in nodes:
            continue
        version = get_record_version(ws, owner)
        nodes[owner] = owner
        spec, _record_id = _spec_and_id(owner.record_ref)
        payload = asdict(version.record) if is_dataclass(version.record) else dict(version.record)
        for field_name in spec.dependency_fields:
            for target_value, expected_hash, expected_revision in _dependency_values(
                payload,
                field_name,
            ):
                if expected_revision and not expected_hash:
                    raise PinnedRecordMismatchError(
                        f"dependency pin is incomplete at {owner.record_ref}.{field_name}"
                    )
                if expected_hash:
                    target = pin_record_hash(
                        ws,
                        target_value,
                        expected_hash,
                        revision=expected_revision,
                    )
                else:
                    target = pin_current_record(ws, target_value)
                edge = FrozenDependencyEdge(
                    owner_ref=owner.record_ref,
                    field_name=field_name,
                    target_ref=target.record_ref,
                    target_hash=target.content_hash,
                    target_revision=target.revision,
                )
                edges.add(edge)
                pending.append(target)

    sorted_nodes = tuple(sorted(nodes.values()))
    sorted_edges = tuple(sorted(edges))
    closure_hash = _closure_hash(root_refs, sorted_nodes, sorted_edges)
    return FrozenDependencyManifest(
        roots=root_refs,
        nodes=sorted_nodes,
        edges=sorted_edges,
        closure_hash=closure_hash,
    )


def _version_from_payload(
    target: PinnedRecordRef,
    spec: RecordFamilySpec,
    frontmatter: Mapping[str, Any],
    body: str,
    path: Path,
    source: str,
) -> PinnedRecordVersion:
    revision = _positive_revision(frontmatter.get("revision"))
    if revision != target.revision:
        raise PinnedRecordMismatchError(
            f"revision {revision} does not match requested revision {target.revision} "
            f"for {target.record_ref}"
        )
    record = _materialize_record(frontmatter, spec)
    return PinnedRecordVersion(
        pinned_ref=target,
        record=record,
        frontmatter=dict(frontmatter),
        body=body,
        path=str(path),
        version_source=source,
    )


def _dependency_values(
    payload: Mapping[str, Any],
    field_path: str,
) -> list[tuple[str, str, int]]:
    if "[]." in field_path:
        collection_name, item_field = field_path.split("[].", 1)
        collection = payload.get(collection_name) or []
        if not isinstance(collection, list):
            raise PinnedRecordMismatchError(f"{field_path} owner field must be a list")
        values = []
        for item in collection:
            if not isinstance(item, Mapping):
                raise PinnedRecordMismatchError(f"{field_path} entries must be mappings")
            raw = item.get(item_field)
            values.extend(_coerce_dependency_values(raw, item_field, item))
        return values
    return _coerce_dependency_values(payload.get(field_path), field_path, payload)


def _coerce_dependency_values(
    raw: Any,
    field_name: str,
    owner: Mapping[str, Any],
) -> list[tuple[str, str, int]]:
    if raw in (None, "", [], ()):
        return []
    items = raw if isinstance(raw, (list, tuple)) else [raw]
    values: list[tuple[str, str, int]] = []
    for item in items:
        if isinstance(item, Mapping):
            record_ref = str(item.get("record_ref") or "").strip()
            content_hash = str(item.get("content_hash") or "").strip()
            revision = _optional_revision(item.get("revision"))
        else:
            record_ref = str(item or "").strip()
            hash_field = f"{field_name[:-4]}_hash" if field_name.endswith("_ref") else ""
            revision_field = (
                f"{field_name[:-4]}_revision" if field_name.endswith("_ref") else ""
            )
            content_hash = str(owner.get(hash_field) or "").strip() if hash_field else ""
            if not content_hash and field_name.endswith("_ref"):
                content_hash = str(
                    owner.get(f"{field_name[:-4]}_record_hash") or ""
                ).strip()
            revision = _optional_revision(owner.get(revision_field)) if revision_field else 0
        if not record_ref:
            continue
        if content_hash and not _SHA256_PATTERN.fullmatch(content_hash):
            raise PinnedRecordMismatchError(
                f"dependency hash for {field_name} must be a lowercase SHA-256 digest"
            )
        values.append((record_ref, content_hash, revision))
    return values


def _optional_revision(value: Any) -> int:
    if value in (None, "", 0):
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PinnedRecordMismatchError("dependency revision must be a positive integer")
    return value


def _coerce_pinned_ref(value: PinnedRecordRef | Mapping[str, Any]) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("pinned record ref must be PinnedRecordRef or a mapping")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _spec_and_id(record_ref: str) -> tuple[RecordFamilySpec, str]:
    parts = _typed_ref_parts(record_ref)
    if parts is None:
        raise PinnedRecordMismatchError(f"malformed typed record ref: {record_ref!r}")
    kind, record_id = parts
    validate_record_id(record_id)
    normalized = kind.replace("-", "_")
    for spec in record_family_specs().values():
        aliases = {alias.replace("-", "_") for alias in spec.exact_ref_aliases}
        if normalized in aliases:
            return spec, record_id
    raise PinnedRecordMismatchError(f"unsupported typed record ref kind: {kind!r}")


def _typed_ref_parts(record_ref: str) -> tuple[str, str] | None:
    kind, separator, record_id = str(record_ref or "").partition(":")
    if not separator or not kind.strip() or not record_id.strip() or ":" in record_id:
        return None
    return kind.strip(), record_id.strip()


def _closure_hash(
    roots: tuple[PinnedRecordRef, ...],
    nodes: tuple[PinnedRecordRef, ...],
    edges: tuple[FrozenDependencyEdge, ...],
) -> str:
    payload = {
        "roots": [asdict(item) for item in roots],
        "nodes": [asdict(item) for item in nodes],
        "edges": [asdict(item) for item in edges],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _repository(ws: WorkspacePaths) -> RecordRepository:
    return RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="tool",
            actor_id="pinned-record-read",
            host="aitp-v5",
        ),
    )
