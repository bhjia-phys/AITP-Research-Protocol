"""Topic-scoped typed materialization over one derived-index query."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from brain.v5.markdown import read_md
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index import build_query_index
from brain.v5.query_index import load_query_index
from brain.v5.record_envelope import RecordActor, read_envelope_compat
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import RecordRepository, record_family_paths
from brain.v5.research_retrieval import ResearchQuery, RetrievalResult, query_records


class IndexedTopicSnapshotError(RuntimeError):
    """Raised when a session cannot anchor an indexed topic snapshot."""


@dataclass(frozen=True)
class IndexedRecord:
    record_ref: str
    family: str
    record: Any
    path: Path
    frontmatter: dict[str, Any]


@dataclass(frozen=True)
class IndexedTopicSnapshot:
    session: Any
    topic_id: str
    records_by_family: dict[str, tuple[Any, ...]]
    indexed_records: tuple[IndexedRecord, ...]
    record_refs: tuple[str, ...]
    coverage: dict[str, Any]
    read_errors: tuple[str, ...]
    index_status: str
    index_generation: int
    truncated: bool


QueryFunction = Callable[[WorkspacePaths, ResearchQuery], RetrievalResult]


def load_indexed_topic_snapshot(
    ws: WorkspacePaths,
    session_id: str,
    *,
    families: tuple[str, ...] | list[str],
    max_records: int = 1000,
    query_fn: QueryFunction = query_records,
    repository: RecordRepository | None = None,
) -> IndexedTopicSnapshot:
    """Materialize one topic-scoped record set from one derived-index query."""

    if not 1 <= int(max_records) <= 2000:
        raise ValueError("max_records must be between 1 and 2000")
    repo = repository or RecordRepository(
        ws,
        actor=RecordActor(
            actor_type="migration",
            actor_id="indexed-topic-read",
            host="context-compiler",
        ),
    )
    session_ref = f"session:{session_id}"
    session_result = repo.read(session_ref)
    if session_result.status != "found" or session_result.record is None:
        detail = session_result.issue.message if session_result.issue else session_result.status
        raise IndexedTopicSnapshotError(f"cannot load indexed topic for {session_id!r}: {detail}")
    session = session_result.record
    session_data = _record_mapping(session)
    topic_id = str(session_data.get("topic_id") or "")
    if not topic_id:
        raise IndexedTopicSnapshotError("session does not identify a topic")
    if not (ws.root / "indexes" / "manifest.json").exists():
        build_query_index(ws)
    exact_refs = _unique_refs(
        (
            session_ref,
            f"topic:{topic_id}",
            _typed_ref("claim", session_data.get("active_claim")),
            _typed_ref("research_route", session_data.get("active_route")),
        )
    )
    result = query_fn(
        ws,
        ResearchQuery(
            exact_refs=exact_refs,
            topic_ids=(topic_id,),
            families=tuple(dict.fromkeys(str(family) for family in families)),
            limit=int(max_records),
            verification_mode="orientation",
        ),
    )

    indexed_records: list[IndexedRecord] = []
    records_by_family: dict[str, list[Any]] = {}
    errors = [f"unresolved_exact_ref:{ref}" for ref in result.excluded_candidates]
    cached_exact = {session_ref: session_result}
    for item in result.items:
        read_result = cached_exact.get(item.record_ref) or repo.read(item.record_ref)
        if read_result.status != "found" or read_result.record is None:
            message = read_result.issue.message if read_result.issue else read_result.status
            errors.append(f"{item.record_ref}:{message}")
            continue
        path = Path(read_result.path)
        frontmatter = dict(read_result.frontmatter or {})
        if not frontmatter:
            errors.append(f"{item.record_ref}:repository read omitted frontmatter")
            continue
        indexed = IndexedRecord(
            record_ref=item.record_ref,
            family=item.family,
            record=read_result.record,
            path=path,
            frontmatter=frontmatter,
        )
        indexed_records.append(indexed)
        records_by_family.setdefault(item.family, []).append(read_result.record)
    if result.index_status == "stale":
        _append_unindexed_paths(
            ws,
            repo=repo,
            topic_id=topic_id,
            families=tuple(dict.fromkeys(str(family) for family in families)),
            indexed_records=indexed_records,
            records_by_family=records_by_family,
            errors=errors,
            max_records=int(max_records),
        )
    if result.coverage.malformed_count:
        errors.append(f"malformed_records_in_scope:{result.coverage.malformed_count}")
    return IndexedTopicSnapshot(
        session=session,
        topic_id=topic_id,
        records_by_family={
            family: tuple(records)
            for family, records in sorted(records_by_family.items())
        },
        indexed_records=tuple(indexed_records),
        record_refs=tuple(record.record_ref for record in indexed_records),
        coverage=asdict(result.coverage),
        read_errors=tuple(errors),
        index_status=result.index_status,
        index_generation=result.index_generation,
        truncated=result.truncated,
    )


def _append_unindexed_paths(
    ws: WorkspacePaths,
    *,
    repo: RecordRepository,
    topic_id: str,
    families: tuple[str, ...],
    indexed_records: list[IndexedRecord],
    records_by_family: dict[str, list[Any]],
    errors: list[str],
    max_records: int,
) -> None:
    index = load_query_index(ws)
    indexed_paths = {str(row.get("relative_path") or "") for row in index.documents}
    existing_refs = {record.record_ref for record in indexed_records}
    specs = record_family_specs()
    for family in families:
        spec = specs.get(family)
        if spec is None:
            continue
        paths, _storage_exists = record_family_paths(ws, spec)
        for path in paths:
            relative_path = path.relative_to(ws.root).as_posix()
            if relative_path in indexed_paths:
                continue
            if len(indexed_records) >= max_records:
                errors.append("stale_delta_truncated:max_records")
                return
            try:
                frontmatter, body = read_md(path)
                envelope = read_envelope_compat(frontmatter, spec, path, body=body)
                record_ref = f"{spec.ref_kind}:{envelope.record_id}"
                if record_ref in existing_refs:
                    continue
                record_topic = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
                if record_topic and record_topic != topic_id:
                    continue
                read_result = repo.read(record_ref)
                if read_result.status != "found" or read_result.record is None:
                    detail = read_result.issue.message if read_result.issue else read_result.status
                    errors.append(f"{record_ref}:{detail}")
                    continue
            except (OSError, TypeError, ValueError) as exc:
                errors.append(f"{relative_path}:{type(exc).__name__}:{exc}")
                continue
            indexed = IndexedRecord(
                record_ref=record_ref,
                family=family,
                record=read_result.record,
                path=path,
                frontmatter=frontmatter,
            )
            indexed_records.append(indexed)
            records_by_family.setdefault(family, []).append(read_result.record)
            existing_refs.add(record_ref)


def _record_mapping(record: Any) -> dict[str, Any]:
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, Mapping):
        return dict(record)
    raise IndexedTopicSnapshotError(f"unsupported exact record type: {type(record).__name__}")


def _typed_ref(kind: str, record_id: Any) -> str:
    text = str(record_id or "").strip()
    return f"{kind}:{text}" if text else ""


def _unique_refs(refs: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(ref for ref in refs if ref and ":" in ref))
