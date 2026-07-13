"""Generation-stamped derived index for canonical AITP records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from brain.v5.markdown import read_md, write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_accumulator import (
    content_accumulator_from_pairs,
    content_accumulator_watermark,
)
from brain.v5.query_index_documents import (
    _document_row,
    _hash_json,
    _hash_text,
    _json_safe,
    _lexical_index,
    _project_tool_run_supersession,
    _relative_path,
    _typed_materialization_status,
    lexical_terms,
)
from brain.v5.record_envelope import read_envelope_compat
from brain.v5.record_family_registry import record_family_specs
from brain.v5.record_repository import record_family_paths
from brain.v5.query_index_locking import acquire_index_build_lease, acquire_ranked_lock
from brain.v5.query_index_generation import (
    generation_component_files,
    load_generation_descriptor,
    next_generation_number,
    write_immutable_generation,
)
from brain.v5.query_index_state import current_family_state_snapshot


INDEX_SCHEMA_VERSION = 3


class IndexIntegrityError(RuntimeError):
    """Raised when disposable index files disagree with their manifest."""


class IndexSnapshotChangedError(RuntimeError):
    """Raised when canonical records change during an index build scan."""


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
    issues_file: str = "issues.json"
    index_schema_version: int = 1
    family_state_tokens: dict[str, str] = field(default_factory=dict)
    family_content_watermarks: dict[str, str] = field(default_factory=dict)
    family_content_accumulators: dict[str, dict[str, Any]] = field(default_factory=dict)
    base_content_hash: str = ""
    manifest_kind: str = ""
    schema_version: int = 1
    generation_manifest_file: str = ""


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

    with acquire_index_build_lease(ws, reason="full-query-index-build"):
        return _build_query_index_locked(ws)


def _build_query_index_locked(ws: WorkspacePaths) -> IndexBuildReport:
    """Build and publish while the caller owns base and mutation leases."""

    state_token_before = canonical_state_token(ws)
    specs = record_family_specs()
    canonical_content_before = {
        family: current_family_content_watermark(ws, family)
        for family in sorted(specs)
    }
    _run_failpoint("after_canonical_before")
    documents: list[dict[str, Any]] = []
    issues: list[IndexBuildIssue] = []
    canonical_pairs: list[list[str]] = []
    checked_count = 0
    family_counts: dict[str, int] = {}
    family_pairs: dict[str, list[list[str]]] = {family: [] for family in specs}
    family_state_rows: dict[str, list[list[Any]]] = {family: [] for family in specs}

    for family, spec in sorted(specs.items()):
        paths, _storage_exists = record_family_paths(ws, spec)
        for path in paths:
            checked_count += 1
            stat = path.stat()
            family_state_rows[family].append(
                [_relative_path(ws, path), stat.st_size, stat.st_mtime_ns]
            )
            try:
                frontmatter, body = read_md(path)
                envelope = read_envelope_compat(frontmatter, spec, path, body=body)
                document = _document_row(ws, spec, frontmatter, body, envelope, path)
            except Exception as exc:  # noqa: BLE001 - derived coverage must retain every issue.
                pair = [
                    f"malformed:{family}:{_relative_path(ws, path)}",
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                ]
                canonical_pairs.append(pair)
                family_pairs[family].append(pair)
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
            pair = [document["record_ref"], document["record_content_hash"]]
            canonical_pairs.append(pair)
            family_pairs[family].append(pair)
            family_counts[family] = family_counts.get(family, 0) + 1

    _project_tool_run_supersession(documents)
    documents.sort(key=lambda row: row["record_ref"])
    for doc_id, document in enumerate(documents):
        document["doc_id"] = doc_id
    lexical = _lexical_index(documents)
    watermark = _hash_json(sorted(canonical_pairs))
    issue_rows = [asdict(issue) for issue in issues]
    malformed_family_counts: dict[str, int] = {}
    for issue in issues:
        malformed_family_counts[issue.family] = malformed_family_counts.get(issue.family, 0) + 1
    family_content_accumulators = {
        family: content_accumulator_from_pairs(family_pairs[family])
        for family in sorted(specs)
    }
    family_content_watermarks = {
        family: content_accumulator_watermark(family_content_accumulators[family])
        for family in sorted(specs)
    }
    family_state_tokens = {
        family: _hash_json(sorted(family_state_rows[family])) for family in sorted(specs)
    }
    canonical_content_after = {
        family: current_family_content_watermark(ws, family)
        for family in sorted(specs)
    }
    changed_content_families = tuple(
        family
        for family in sorted(specs)
        if not (
            canonical_content_before[family]
            == family_content_watermarks[family]
            == canonical_content_after[family]
        )
    )
    if changed_content_families:
        raise IndexSnapshotChangedError(
            "strong canonical content changed while query index was built: "
            + ", ".join(changed_content_families)
        )
    document_text = json.dumps(documents, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    lexical_text = json.dumps(lexical, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    issues_text = json.dumps(issue_rows, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    document_hash = _hash_text(document_text)
    lexical_hash = _hash_text(lexical_text)
    issues_hash = _hash_text(issues_text)
    content_hash = _hash_json(
        {
            "schema_version": 3,
            "index_schema_version": INDEX_SCHEMA_VERSION,
            "canonical_watermark": watermark,
            "family_content_watermarks": family_content_watermarks,
            "family_content_accumulators": family_content_accumulators,
            "document_hash": document_hash,
            "lexical_hash": lexical_hash,
            "issues_hash": issues_hash,
            "record_count": len(documents),
            "family_counts": dict(sorted(family_counts.items())),
            "malformed_count": len(issues),
            "malformed_family_counts": dict(sorted(malformed_family_counts.items())),
        }
    )
    state_token_after = canonical_state_token(ws)
    if state_token_after != state_token_before:
        raise IndexSnapshotChangedError(
            "canonical state changed while query index was built; retry after writes quiesce"
        )
    generation = next_generation_number(ws, _published_generation(ws))
    generation_files = generation_component_files(generation)
    manifest = IndexManifest(
        generation=generation,
        canonical_watermark=watermark,
        canonical_state_token=state_token_before,
        content_hash=content_hash,
        record_count=len(documents),
        family_counts=dict(sorted(family_counts.items())),
        malformed_count=len(issues),
        malformed_family_counts=dict(sorted(malformed_family_counts.items())),
        built_at=datetime.now(UTC).isoformat(),
        document_hash=document_hash,
        lexical_hash=lexical_hash,
        issues_hash=issues_hash,
        index_schema_version=INDEX_SCHEMA_VERSION,
        family_state_tokens=family_state_tokens,
        family_content_watermarks=family_content_watermarks,
        family_content_accumulators=family_content_accumulators,
        base_content_hash=content_hash,
        manifest_kind="query_index_root",
        schema_version=3,
        **generation_files,
    )
    index_dir = ws.root / "indexes"
    manifest_payload = asdict(manifest)
    write_immutable_generation(
        ws,
        manifest_payload=manifest_payload,
        document_text=document_text,
        lexical_text=lexical_text,
        issues_text=issues_text,
    )
    _run_failpoint("after_generation_components")
    with acquire_ranked_lock(ws, "delta-manifest"):
        _run_failpoint("before_root_replace")
        write_text_atomic(
            index_dir / "manifest.json",
            json.dumps(manifest_payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        )
        _run_failpoint("after_root_replace")
        _run_failpoint("before_delta_rebase")
        _reset_delta_after_full_build(ws, manifest, lock_held=True)
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
    _apply_manifest_defaults(manifest_data)
    manifest = IndexManifest(**manifest_data)
    if (
        manifest.manifest_kind == "query_index_root"
        and manifest.schema_version >= 2
        and manifest.generation_manifest_file
    ):
        descriptor = load_generation_descriptor(ws, manifest.generation_manifest_file)
        if descriptor != manifest_data:
            raise IndexIntegrityError("generation descriptor does not match query index root")
    document_text = (index_dir / manifest.document_file).read_text(encoding="utf-8")
    lexical_text = (index_dir / manifest.lexical_file).read_text(encoding="utf-8")
    issues_text = (index_dir / manifest.issues_file).read_text(encoding="utf-8")
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
    hash_basis = _manifest_hash_basis(manifest, component_hashes)
    actual_hash = _hash_json(hash_basis)
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


def load_query_manifest(ws: WorkspacePaths) -> IndexManifest:
    """Load only the small manifest for exact-read freshness and coverage checks."""

    manifest_data = _load_json(ws.root / "indexes" / "manifest.json")
    _apply_manifest_defaults(manifest_data)
    return IndexManifest(**manifest_data)


def query_index_is_fresh(ws: WorkspacePaths, manifest: IndexManifest) -> bool:
    """Require both canonical-state and index-algorithm freshness."""

    if manifest.index_schema_version != INDEX_SCHEMA_VERSION:
        return False
    if manifest.manifest_kind == "query_index_root" and manifest.schema_version >= 2:
        from brain.v5.query_index_delta import global_index_state_is_fresh

        return global_index_state_is_fresh(ws, manifest)
    return canonical_state_token(ws) == manifest.canonical_state_token


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


def current_family_state_token(ws: WorkspacePaths, family: str) -> str:
    """Return the cheap state token for one canonical record family."""

    return current_family_state_snapshot(ws, family).token


def current_family_content_watermark(ws: WorkspacePaths, family: str) -> str:
    """Hash canonical content for one family, including malformed bytes."""

    return content_accumulator_watermark(
        current_family_content_accumulator(ws, family)
    )


def current_family_content_accumulator(
    ws: WorkspacePaths,
    family: str,
) -> dict[str, int | str]:
    """Rebuild one family accumulator directly from canonical content."""

    spec = record_family_specs()[family]
    paths, _storage_exists = record_family_paths(ws, spec)
    pairs: list[list[str]] = []
    for path in paths:
        try:
            frontmatter, body = read_md(path)
            envelope = read_envelope_compat(frontmatter, spec, path, body=body)
        except Exception:  # noqa: BLE001 - malformed bytes remain part of coverage.
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            pairs.append([f"malformed:{family}:{_relative_path(ws, path)}", digest])
            continue
        pairs.append([f"{spec.ref_kind}:{envelope.record_id}", envelope.content_hash])
    return content_accumulator_from_pairs(pairs)


def _published_generation(ws: WorkspacePaths) -> int:
    path = ws.root / "indexes" / "manifest.json"
    if not path.exists():
        return 0
    try:
        return int(_load_json(path).get("generation", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _apply_manifest_defaults(manifest_data: dict[str, Any]) -> None:
    manifest_data.setdefault("malformed_family_counts", {})
    manifest_data.setdefault("index_schema_version", 1)
    manifest_data.setdefault("issues_file", "issues.json")
    manifest_data.setdefault("family_state_tokens", {})
    manifest_data.setdefault("family_content_watermarks", {})
    manifest_data.setdefault("family_content_accumulators", {})
    manifest_data.setdefault("base_content_hash", manifest_data.get("content_hash", ""))
    manifest_data.setdefault("manifest_kind", "")
    manifest_data.setdefault("schema_version", 1)
    manifest_data.setdefault("generation_manifest_file", "")


def _manifest_hash_basis(
    manifest: IndexManifest,
    component_hashes: dict[str, str],
) -> dict[str, Any]:
    if manifest.manifest_kind == "query_index_root" and manifest.schema_version >= 2:
        basis = {
            "schema_version": manifest.schema_version,
            "index_schema_version": manifest.index_schema_version,
            "canonical_watermark": manifest.canonical_watermark,
            "family_content_watermarks": manifest.family_content_watermarks,
            **component_hashes,
            "record_count": manifest.record_count,
            "family_counts": manifest.family_counts,
            "malformed_count": manifest.malformed_count,
            "malformed_family_counts": manifest.malformed_family_counts,
        }
        if manifest.schema_version >= 3:
            basis["family_content_accumulators"] = manifest.family_content_accumulators
        return basis
    basis = {"canonical_watermark": manifest.canonical_watermark, **component_hashes}
    if manifest.index_schema_version >= 2:
        basis["index_schema_version"] = manifest.index_schema_version
    return basis


def _reset_delta_after_full_build(
    ws: WorkspacePaths,
    manifest: IndexManifest,
    *,
    lock_held: bool = False,
) -> None:
    from brain.v5.query_index_delta import reset_query_delta_for_base

    reset_query_delta_for_base(ws, manifest, lock_held=lock_held)


def _run_failpoint(_name: str) -> None:
    """Named no-op seam for deterministic publication interruption tests."""
