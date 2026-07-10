"""Generation-stamped derived index for canonical AITP records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md, write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.record_envelope import read_envelope_compat
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import record_family_paths


_LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*")
_CJK_TOKEN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


class IndexIntegrityError(RuntimeError):
    """Raised when disposable index files disagree with their manifest."""


@dataclass(frozen=True)
class IndexManifest:
    generation: int
    canonical_watermark: str
    canonical_state_token: str
    content_hash: str
    record_count: int
    family_counts: dict[str, int]
    malformed_count: int
    malformed_family_counts: dict[str, int]
    built_at: str
    document_hash: str
    lexical_hash: str
    issues_hash: str
    document_file: str = "record_documents.json"
    lexical_file: str = "lexical_index.json"


@dataclass(frozen=True)
class IndexBuildIssue:
    family: str
    path: str
    error_type: str
    message: str


@dataclass(frozen=True)
class IndexBuildReport:
    manifest: IndexManifest
    checked_count: int
    indexed_count: int
    malformed_count: int
    issues: tuple[IndexBuildIssue, ...]
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class LoadedQueryIndex:
    manifest: IndexManifest
    documents: tuple[dict[str, Any], ...]
    lexical_terms: dict[str, tuple[int, ...]]
    record_refs: tuple[str, ...]


def build_query_index(ws: WorkspacePaths) -> IndexBuildReport:
    """Build disposable sorted metadata and lexical indexes from canonical files."""

    specs = record_family_specs()
    documents: list[dict[str, Any]] = []
    issues: list[IndexBuildIssue] = []
    canonical_pairs: list[list[str]] = []
    checked_count = 0
    family_counts: dict[str, int] = {}

    for family, spec in sorted(specs.items()):
        paths, _storage_exists = record_family_paths(ws, spec)
        for path in paths:
            checked_count += 1
            try:
                frontmatter, body = read_md(path)
                envelope = read_envelope_compat(frontmatter, spec, path, body=body)
                document = _document_row(ws, spec, frontmatter, body, envelope, path)
            except Exception as exc:  # noqa: BLE001 - derived coverage must retain every issue.
                canonical_pairs.append(
                    [
                        f"malformed:{family}:{_relative_path(ws, path)}",
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    ]
                )
                issues.append(
                    IndexBuildIssue(
                        family=family,
                        path=_relative_path(ws, path),
                        error_type=type(exc).__name__,
                        message=str(exc),
                    )
                )
                continue
            documents.append(document)
            canonical_pairs.append([document["record_ref"], document["record_content_hash"]])
            family_counts[family] = family_counts.get(family, 0) + 1

    documents.sort(key=lambda row: row["record_ref"])
    for doc_id, document in enumerate(documents):
        document["doc_id"] = doc_id
    lexical = _lexical_index(documents)
    watermark = _hash_json(sorted(canonical_pairs))
    issue_rows = [asdict(issue) for issue in issues]
    malformed_family_counts: dict[str, int] = {}
    for issue in issues:
        malformed_family_counts[issue.family] = malformed_family_counts.get(issue.family, 0) + 1
    document_text = json.dumps(documents, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lexical_text = json.dumps(lexical, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    issues_text = json.dumps(issue_rows, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    document_hash = _hash_text(document_text)
    lexical_hash = _hash_text(lexical_text)
    issues_hash = _hash_text(issues_text)
    content_hash = _hash_json(
        {
            "canonical_watermark": watermark,
            "document_hash": document_hash,
            "lexical_hash": lexical_hash,
            "issues_hash": issues_hash,
        }
    )
    generation = _next_generation(ws)
    manifest = IndexManifest(
        generation=generation,
        canonical_watermark=watermark,
        canonical_state_token=canonical_state_token(ws),
        content_hash=content_hash,
        record_count=len(documents),
        family_counts=dict(sorted(family_counts.items())),
        malformed_count=len(issues),
        malformed_family_counts=dict(sorted(malformed_family_counts.items())),
        built_at=datetime.now(UTC).isoformat(),
        document_hash=document_hash,
        lexical_hash=lexical_hash,
        issues_hash=issues_hash,
    )
    index_dir = ws.root / "indexes"
    write_text_atomic(
        index_dir / manifest.document_file,
        document_text,
    )
    write_text_atomic(
        index_dir / manifest.lexical_file,
        lexical_text,
    )
    write_text_atomic(
        index_dir / "manifest.json",
        json.dumps(asdict(manifest), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )
    write_text_atomic(
        index_dir / "issues.json",
        issues_text,
    )
    return IndexBuildReport(
        manifest=manifest,
        checked_count=checked_count,
        indexed_count=len(documents),
        malformed_count=len(issues),
        issues=tuple(issues),
    )


def load_query_index(ws: WorkspacePaths) -> LoadedQueryIndex:
    """Load an existing derived index without touching canonical records."""

    index_dir = ws.root / "indexes"
    manifest_data = _load_json(index_dir / "manifest.json")
    manifest_data.setdefault("malformed_family_counts", {})
    manifest = IndexManifest(**manifest_data)
    document_text = (index_dir / manifest.document_file).read_text(encoding="utf-8")
    lexical_text = (index_dir / manifest.lexical_file).read_text(encoding="utf-8")
    issues_text = (index_dir / "issues.json").read_text(encoding="utf-8")
    component_hashes = {
        "document_hash": _hash_text(document_text),
        "lexical_hash": _hash_text(lexical_text),
        "issues_hash": _hash_text(issues_text),
    }
    expected_components = {
        "document_hash": manifest.document_hash,
        "lexical_hash": manifest.lexical_hash,
        "issues_hash": manifest.issues_hash,
    }
    actual_hash = _hash_json(
        {
            "canonical_watermark": manifest.canonical_watermark,
            **component_hashes,
        }
    )
    if component_hashes != expected_components or actual_hash != manifest.content_hash:
        raise IndexIntegrityError("manifest content hash does not match derived index files")
    documents = tuple(json.loads(document_text))
    raw_lexical = json.loads(lexical_text)
    lexical = {term: tuple(refs) for term, refs in raw_lexical.items()}
    return LoadedQueryIndex(
        manifest=manifest,
        documents=documents,
        lexical_terms=lexical,
        record_refs=tuple(row["record_ref"] for row in documents),
    )


def current_canonical_watermark(ws: WorkspacePaths) -> str:
    """Compute the current canonical content watermark without writing an index."""

    pairs: list[list[str]] = []
    for family, spec in sorted(record_family_specs().items()):
        paths, _storage_exists = record_family_paths(ws, spec)
        for path in paths:
            try:
                frontmatter, body = read_md(path)
                envelope = read_envelope_compat(frontmatter, spec, path, body=body)
            except Exception:  # noqa: BLE001 - malformed paths are represented by a stable file digest.
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                pairs.append([f"malformed:{family}:{_relative_path(ws, path)}", digest])
                continue
            pairs.append([f"{spec.ref_kind}:{envelope.record_id}", envelope.content_hash])
    return _hash_json(sorted(pairs))


def canonical_state_token(ws: WorkspacePaths) -> str:
    """Return a cheap file-state token for index freshness checks."""

    rows: list[list[Any]] = []
    for family, spec in sorted(record_family_specs().items()):
        paths, _storage_exists = record_family_paths(ws, spec)
        for path in paths:
            stat = path.stat()
            rows.append([family, path.name, stat.st_size, stat.st_mtime_ns])
    return _hash_json(rows)


def _document_row(ws, spec, frontmatter, body, envelope, path):
    topic_id = str(frontmatter.get("topic_id") or frontmatter.get("topic") or "")
    lifecycle = str(frontmatter.get("lifecycle_status") or frontmatter.get("status") or "")
    searchable = json.dumps(_json_safe(frontmatter), ensure_ascii=False, sort_keys=True)
    return {
        "record_ref": f"{spec.ref_kind}:{envelope.record_id}",
        "record_id": envelope.record_id,
        "family": envelope.record_family,
        "kind": str(frontmatter.get("kind") or ""),
        "topic_id": topic_id,
        "claim_id": str(frontmatter.get("claim_id") or ""),
        "session_id": envelope.session_id,
        "program_id": envelope.program_id,
        "scope_refs": list(envelope.scope_refs),
        "source_record_refs": list(envelope.source_record_refs),
        "status": str(frontmatter.get("status") or ""),
        "lifecycle_status": lifecycle,
        "title": str(frontmatter.get("title") or frontmatter.get("statement") or ""),
        "record_content_hash": envelope.content_hash,
        "typed_materialization_status": _typed_materialization_status(frontmatter, spec),
        "relative_path": _relative_path(ws, path),
        "search_text": f"{searchable}\n{body}".strip(),
    }


def _lexical_index(documents):
    postings: dict[str, set[int]] = {}
    for row in documents:
        for term in lexical_terms(row["search_text"]):
            postings.setdefault(term, set()).add(row["doc_id"])
    return {term: sorted(refs) for term, refs in sorted(postings.items())}


def lexical_terms(text: str) -> tuple[str, ...]:
    """Tokenize Latin identifiers and bounded CJK n-grams deterministically."""

    lowered = str(text or "").lower()
    terms = set(_LATIN_TOKEN_RE.findall(lowered))
    for match in _CJK_TOKEN_RE.findall(lowered):
        sequence = match[:128]
        terms.add(sequence)
        for width in range(2, min(4, len(sequence)) + 1):
            terms.update(
                sequence[index : index + width]
                for index in range(len(sequence) - width + 1)
            )
    return tuple(sorted(term for term in terms if term))


def _typed_materialization_status(frontmatter, spec) -> str:
    if spec.record_class is None:
        return "not_applicable"
    values = dict(frontmatter)
    if spec.id_field not in values:
        for legacy_field in spec.legacy_id_fields:
            if values.get(legacy_field):
                values[spec.id_field] = values[legacy_field]
                break
    if "topic_id" not in values and values.get("topic"):
        values["topic_id"] = values["topic"]
    allowed = {field.name for field in fields(spec.record_class)}
    try:
        spec.record_class(**{key: value for key, value in values.items() if key in allowed})
    except (TypeError, ValueError):
        return "unavailable"
    return "ready"


def _next_generation(ws: WorkspacePaths) -> int:
    path = ws.root / "indexes" / "manifest.json"
    if not path.exists():
        return 1
    try:
        return int(_load_json(path).get("generation", 0)) + 1
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 1


def _relative_path(ws: WorkspacePaths, path: Path) -> str:
    return path.relative_to(ws.root).as_posix()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))
