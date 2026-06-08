"""Curated heuristic RAG corpus contracts for AITP v5 hosts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths


CATALOG_VERSION = "aitp.v5.curated_rag_corpus.v1"

_ALLOWED_USES = [
    "conceptual_scaffolding",
    "literature_orientation",
    "derivation_scaffolding",
    "method_selection",
    "source_backtrace_suggestions",
]
_FORBIDDEN_USES = [
    "evidence_support",
    "validation_result",
    "claim_trust_update",
    "trust_apply",
    "final_gate_satisfaction",
]


def curated_rag_corpus(base: str | Path | WorkspacePaths | None = None) -> dict[str, Any]:
    """Return the canonical lightweight curated RAG corpus catalog.

    Without a workspace corpus file this returns the stable contract fixture.
    When ``.aitp/curated_rag/corpus.json`` exists under ``base``, it is loaded
    as a file-backed corpus manifest and normalized into the same no-trust
    public surface. Retrieved chunks are heuristic context only.
    """

    file_manifest = _load_file_manifest(base)
    if file_manifest is not None:
        documents = _normalize_documents(file_manifest.get("documents"), source="file_backed")
        chunks = _normalize_chunks(file_manifest.get("chunks"), source="file_backed")
        corpus_id = _string(file_manifest.get("corpus_id")) or "aitp.curated.file_backed_background.v1"
        index_extra = _file_index_policy_extra(base, documents=documents, chunks=chunks)
        return _catalog(
            corpus_id=corpus_id,
            documents=documents,
            chunks=chunks,
            index_mode="lexical_file_backed",
            index_extra=index_extra,
        )

    documents = _fixture_documents()
    chunks = _fixture_chunks()
    return _catalog(
        corpus_id="aitp.curated.heuristic_background.v1",
        documents=documents,
        chunks=chunks,
        index_mode="lexical_fixture",
        index_extra={},
    )


def ingest_curated_rag_corpus(
    base: str | Path | WorkspacePaths,
    *,
    paths: list[str],
    corpus_id: str = "",
    tags: list[str] | None = None,
    domain_hints: list[str] | None = None,
    topic_hints: list[str] | None = None,
    language: str = "en",
    priority: str = "medium",
    chunk_token_limit: int = 220,
    title_prefix: str = "",
    asset_type: str = "",
    rebuild_index: bool = True,
) -> dict[str, Any]:
    """Create or update a file-backed curated RAG corpus from local files.

    This writes only the lightweight curated RAG manifest/index lane under
    ``.aitp/curated_rag``. It does not create evidence, validation, trust, or
    final-gate records.
    """

    if not paths:
        raise ValueError("curated RAG ingestion requires at least one path")
    resolved_files = _resolve_input_files(base, paths)
    if not resolved_files:
        raise ValueError("curated RAG ingestion found no readable files")

    documents: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    for ordinal, file_path in enumerate(resolved_files, start=1):
        text, reader = _read_curated_source_text(file_path)
        document_id = f"curated_rag_doc:{_stable_slug(file_path.stem)}"
        document_tags = _unique_strings([*(tags or []), file_path.suffix.lower().lstrip(".")])
        document = {
            "document_id": document_id,
            "title": _document_title(file_path, title_prefix=title_prefix),
            "asset_type": _string(asset_type) or _asset_type_for_path(file_path),
            "source_uri": file_path.resolve().as_uri(),
            "version_anchor": {
                "path": str(file_path),
                "mtime_ns": file_path.stat().st_mtime_ns,
                "size_bytes": file_path.stat().st_size,
                "reader": reader,
                "ordinal": ordinal,
            },
            "content_hash": _hash_text(text),
            "tags": document_tags,
            "domain_hints": _string_list(domain_hints or []),
            "topic_hints": _string_list(topic_hints or []),
            "language": _string(language) or "en",
            "priority": _string(priority) or "medium",
            "intended_use": "background_rag",
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        }
        documents.append(document)
        chunks.extend(
            _chunks_for_text(
                document_id=document_id,
                text=text,
                tags=document_tags,
                chunk_token_limit=chunk_token_limit,
            )
        )

    manifest = {
        "corpus_id": _string(corpus_id) or "aitp.curated.user_background.v1",
        "documents": documents,
        "chunks": chunks,
    }
    corpus_path = _corpus_manifest_path(base)
    corpus_path.parent.mkdir(parents=True, exist_ok=True)
    corpus_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    catalog = curated_rag_corpus(base)
    index_payload = _lexical_index_payload(catalog)
    index_path = _lexical_index_path(base)
    if rebuild_index:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(
            json.dumps(index_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        catalog = curated_rag_corpus(base)

    return {
        "kind": "curated_rag_ingest_result",
        "catalog_version": CATALOG_VERSION,
        "ok": True,
        "state_effect": "curated_rag_manifest_write",
        "truth_source": "curated_rag_ingestion",
        "corpus_id": catalog["corpus_id"],
        "manifest_path": str(corpus_path),
        "index_path": str(index_path),
        "manifest_hash": catalog["index_policy"].get("manifest_hash", index_payload["manifest_hash"]),
        "index_status": catalog["index_policy"].get("index_status", "derived_in_memory"),
        "document_count": catalog["document_count"],
        "chunk_count": catalog["chunk_count"],
        "document_ids": catalog["document_index"],
        "chunk_ids": catalog["chunk_index"],
        "source_paths": [str(path) for path in resolved_files],
        "rebuild_index": rebuild_index,
        "retrieval_role": "heuristic_context",
        "orientation_only": True,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "forbidden_uses": _FORBIDDEN_USES,
        "promotion_required_before_claim_support": True,
        "promotion_path": [
            "source_asset",
            "reference_location",
            "evidence",
            "validation",
            "trust_preflight",
        ],
    }


def _fixture_documents() -> list[dict[str, Any]]:
    documents = [
        {
            "document_id": "curated_rag_doc:theory_methods_orientation",
            "title": "Theory methods orientation shelf",
            "asset_type": "note",
            "source_uri": "aitp://curated-rag/theory-methods-orientation",
            "version_anchor": {"catalog_version": CATALOG_VERSION, "revision": "v1"},
            "content_hash": "sha256:curated-rag-theory-methods-orientation-v1",
            "tags": ["theoretical-physics", "methods", "orientation"],
            "domain_hints": ["theoretical-physics/general"],
            "topic_hints": ["method-selection", "derivation-scaffolding"],
            "language": "en",
            "priority": "high",
            "intended_use": "background_rag",
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        {
            "document_id": "curated_rag_doc:source_backtrace_orientation",
            "title": "Source backtrace orientation shelf",
            "asset_type": "lecture",
            "source_uri": "aitp://curated-rag/source-backtrace-orientation",
            "version_anchor": {"catalog_version": CATALOG_VERSION, "revision": "v1"},
            "content_hash": "sha256:curated-rag-source-backtrace-orientation-v1",
            "tags": ["source-reconstruction", "literature", "orientation"],
            "domain_hints": ["theoretical-physics/general"],
            "topic_hints": ["source-backtrace", "literature-orientation"],
            "language": "en",
            "priority": "medium",
            "intended_use": "background_rag",
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
    ]
    return documents


def _fixture_chunks() -> list[dict[str, Any]]:
    chunks = [
        {
            "chunk_id": "curated_rag_chunk:theory_methods_orientation:0001",
            "document_id": "curated_rag_doc:theory_methods_orientation",
            "anchor": {"section": "method-selection", "ordinal": 1},
            "text": (
                "When a theory problem feels underdetermined, first separate "
                "definitions, assumptions, calculational handles, and validation "
                "targets before choosing a formal route."
            ),
            "summary": "Use method selection to separate definitions, assumptions, handles, and validation.",
            "tags": ["method-selection", "problem-framing"],
            "token_estimate": 32,
            "content_hash": "sha256:curated-rag-chunk-theory-methods-0001",
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        {
            "chunk_id": "curated_rag_chunk:source_backtrace_orientation:0001",
            "document_id": "curated_rag_doc:source_backtrace_orientation",
            "anchor": {"section": "source-backtrace", "ordinal": 1},
            "text": (
                "Treat a retrieved lecture or review passage as a pointer to "
                "source reconstruction work. It can suggest where to look next, "
                "but claim support needs explicit reference locations and evidence records."
            ),
            "summary": "Retrieved passages suggest source reconstruction, not claim support.",
            "tags": ["source-backtrace", "trust-boundary"],
            "token_estimate": 38,
            "content_hash": "sha256:curated-rag-chunk-source-backtrace-0001",
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
    ]
    return chunks


def _catalog(
    *,
    corpus_id: str,
    documents: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    index_mode: str,
    index_extra: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "curated_rag_corpus",
        "catalog_version": CATALOG_VERSION,
        "truth_source": "curated_rag_corpus_catalog",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "retrieval_policy": {
            "result_role": "heuristic_context",
            "read_surface_effect": "orientation_only",
            "allowed_uses": _ALLOWED_USES,
            "forbidden_uses": _FORBIDDEN_USES,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
            "summary_inputs_trusted": False,
            "can_update_claim_trust": False,
            "requires_promotion_for_claim_support": True,
        },
        "index_policy": {
            "active_index_mode": index_mode,
            "supported_index_modes": [index_mode],
            "embedding_index_required": False,
            "index_is_derived": True,
            "derived_from": "curated_rag_chunk_manifest",
            "stale_index_behavior": "return_diagnostic_not_trust",
            **index_extra,
        },
        "corpus_id": corpus_id,
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "document_index": [document["document_id"] for document in documents],
        "chunk_index": [chunk["chunk_id"] for chunk in chunks],
        "documents": documents,
        "chunks": chunks,
    }


def search_curated_rag_corpus(
    query: str,
    *,
    limit: int = 5,
    base: str | Path | WorkspacePaths | None = None,
) -> dict[str, Any]:
    """Return deterministic lexical retrieval over the curated corpus."""

    catalog = curated_rag_corpus(base)
    terms = [term for term in _tokenize(query) if term]
    scored: list[tuple[int, dict[str, Any]]] = []
    for chunk in catalog["chunks"]:
        haystack = " ".join(
            [
                chunk["text"],
                chunk["summary"],
                " ".join(chunk["tags"]),
                chunk["document_id"],
            ]
        ).lower()
        score = sum(1 for term in terms if term in haystack)
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]["chunk_id"]))
    results = [
        {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "score": score,
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "summary": chunk["summary"],
            "text": chunk["text"],
            "anchor": chunk["anchor"],
            "tags": chunk["tags"],
            "content_hash": chunk["content_hash"],
        }
        for score, chunk in scored[: max(0, limit)]
    ]
    return {
        "kind": "curated_rag_search_result",
        "catalog_version": CATALOG_VERSION,
        "query": query,
        "index_mode": catalog["index_policy"]["active_index_mode"],
        "result_role": "heuristic_context",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "index_status": catalog["index_policy"].get("index_status", "fresh"),
        "stale_index_diagnostics": catalog["index_policy"].get("stale_index_diagnostics", []),
        "result_count": len(results),
        "results": results,
    }


def _tokenize(query: str) -> list[str]:
    return [
        token.strip().lower()
        for token in query.replace("_", " ").replace("-", " ").split()
        if token.strip()
    ]


def _load_file_manifest(base: str | Path | WorkspacePaths | None) -> dict[str, Any] | None:
    if base is None:
        return None
    path = _corpus_manifest_path(base)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("curated RAG corpus manifest must be a JSON object")
    return payload


def _corpus_manifest_path(base: str | Path | WorkspacePaths) -> Path:
    return _aitp_root(base) / "curated_rag" / "corpus.json"


def _lexical_index_path(base: str | Path | WorkspacePaths) -> Path:
    return _aitp_root(base) / "curated_rag" / "indexes" / "lexical_index.json"


def _aitp_root(base: str | Path | WorkspacePaths) -> Path:
    if isinstance(base, WorkspacePaths):
        return base.root
    path = Path(base)
    if path.name == ".aitp":
        return path
    return path / ".aitp"


def _normalize_documents(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("curated RAG documents must be a list")
    documents: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise ValueError("curated RAG document entries must be objects")
        document_id = _required_string(raw, "document_id")
        title = _required_string(raw, "title")
        asset_type = _required_string(raw, "asset_type")
        source_uri = _required_string(raw, "source_uri")
        content_hash = _string(raw.get("content_hash")) or _hash_payload(
            {
                "document_id": document_id,
                "title": title,
                "asset_type": asset_type,
                "source_uri": source_uri,
                "source": source,
            }
        )
        documents.append(
            {
                **raw,
                "document_id": document_id,
                "title": title,
                "asset_type": asset_type,
                "source_uri": source_uri,
                "version_anchor": raw.get("version_anchor")
                if isinstance(raw.get("version_anchor"), dict)
                else {"catalog_version": CATALOG_VERSION, "source": source, "ordinal": index + 1},
                "content_hash": content_hash,
                "tags": _string_list(raw.get("tags")),
                "domain_hints": _string_list(raw.get("domain_hints")),
                "topic_hints": _string_list(raw.get("topic_hints")),
                "language": _string(raw.get("language")) or "en",
                "priority": _string(raw.get("priority")) or "medium",
                "intended_use": _string(raw.get("intended_use")) or "background_rag",
                "trust_status": "heuristic_context",
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    return documents


def _normalize_chunks(value: Any, *, source: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("curated RAG chunks must be a list")
    chunks: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise ValueError("curated RAG chunk entries must be objects")
        text = _required_string(raw, "text")
        summary = _string(raw.get("summary")) or text[:160]
        token_estimate = raw.get("token_estimate")
        if not isinstance(token_estimate, int) or token_estimate <= 0:
            token_estimate = max(1, len(text.split()))
        chunks.append(
            {
                **raw,
                "chunk_id": _required_string(raw, "chunk_id"),
                "document_id": _required_string(raw, "document_id"),
                "anchor": raw.get("anchor")
                if isinstance(raw.get("anchor"), dict)
                else {"source": source, "ordinal": index + 1},
                "text": text,
                "summary": summary,
                "tags": _string_list(raw.get("tags")),
                "token_estimate": token_estimate,
                "content_hash": _string(raw.get("content_hash")) or _hash_text(text),
                "retrieval_role": "heuristic_context",
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    return chunks


def _resolve_input_files(base: str | Path | WorkspacePaths, paths: list[str]) -> list[Path]:
    base_path = base.base if isinstance(base, WorkspacePaths) else Path(base)
    resolved: list[Path] = []
    for raw_path in paths:
        value = _string(raw_path)
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = base_path / path
        if path.is_dir():
            candidates = sorted(
                item
                for item in path.rglob("*")
                if item.is_file() and item.suffix.lower() in {".md", ".markdown", ".txt", ".tex", ".rst", ".pdf"}
            )
            resolved.extend(candidates)
        elif path.is_file():
            resolved.append(path)
        else:
            raise FileNotFoundError(f"curated RAG source path does not exist: {path}")
    unique: list[Path] = []
    seen: set[str] = set()
    for path in resolved:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _read_curated_source_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore[import-not-found]
        except ImportError as exc:
            raise ValueError("PDF curated RAG ingestion requires pypdf") from exc
        reader = PdfReader(str(path))
        parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(part.strip() for part in parts if part.strip())
        return _nonempty_text(text, path), "pypdf"
    text = path.read_text(encoding="utf-8-sig")
    return _nonempty_text(text, path), "utf-8-sig"


def _nonempty_text(text: str, path: Path) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not value:
        raise ValueError(f"curated RAG source file has no extractable text: {path}")
    return value


def _chunks_for_text(
    *,
    document_id: str,
    text: str,
    tags: list[str],
    chunk_token_limit: int,
) -> list[dict[str, Any]]:
    limit = chunk_token_limit if chunk_token_limit > 0 else 220
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", text) if part.strip()]
    chunks: list[dict[str, Any]] = []
    current: list[str] = []
    current_tokens = 0
    for paragraph in paragraphs:
        tokens = paragraph.split()
        token_count = len(tokens)
        if current and current_tokens + token_count > limit:
            chunks.append(_chunk_payload(document_id, len(chunks) + 1, "\n\n".join(current), tags))
            current = []
            current_tokens = 0
        if token_count > limit:
            for start in range(0, token_count, limit):
                chunks.append(
                    _chunk_payload(
                        document_id,
                        len(chunks) + 1,
                        " ".join(tokens[start : start + limit]),
                        tags,
                    )
                )
            continue
        current.append(paragraph)
        current_tokens += token_count
    if current:
        chunks.append(_chunk_payload(document_id, len(chunks) + 1, "\n\n".join(current), tags))
    if not chunks:
        chunks.append(_chunk_payload(document_id, 1, text, tags))
    return chunks


def _chunk_payload(document_id: str, ordinal: int, text: str, tags: list[str]) -> dict[str, Any]:
    chunk_id = f"curated_rag_chunk:{document_id.split(':', 1)[-1]}:{ordinal:04d}"
    summary = " ".join(text.split())[:240]
    return {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "anchor": {"ordinal": ordinal},
        "text": text,
        "summary": summary,
        "tags": tags,
        "token_estimate": max(1, len(text.split())),
        "content_hash": _hash_text(text),
        "retrieval_role": "heuristic_context",
        "orientation_only": True,
        "can_update_claim_trust": False,
    }


def _lexical_index_payload(catalog: dict[str, Any]) -> dict[str, Any]:
    chunks = catalog["chunks"]
    terms_by_chunk: dict[str, list[str]] = {}
    for chunk in chunks:
        text = " ".join([chunk["text"], chunk["summary"], " ".join(chunk["tags"])])
        terms_by_chunk[chunk["chunk_id"]] = sorted(set(_tokenize(text)))
    return {
        "kind": "curated_rag_lexical_index",
        "catalog_version": CATALOG_VERSION,
        "index_mode": "lexical_file_backed",
        "manifest_hash": catalog["index_policy"]["manifest_hash"],
        "document_index": catalog["document_index"],
        "chunk_index": catalog["chunk_index"],
        "terms_by_chunk": terms_by_chunk,
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
    }


def _document_title(path: Path, *, title_prefix: str) -> str:
    title = path.stem.replace("_", " ").replace("-", " ").strip() or path.name
    prefix = _string(title_prefix)
    return f"{prefix} {title}".strip() if prefix else title


def _asset_type_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "paper"
    if suffix in {".md", ".markdown", ".txt", ".rst"}:
        return "note"
    if suffix == ".tex":
        return "lecture"
    return "other"


def _stable_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "document"


def _unique_strings(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        item = _string(value)
        if item and item not in out:
            out.append(item)
    return out


def _file_index_policy_extra(
    base: str | Path | WorkspacePaths | None,
    *,
    documents: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    if base is None:
        return {}
    manifest_hash = _hash_payload(
        {
            "documents": documents,
            "chunks": chunks,
        }
    )
    index_path = _lexical_index_path(base)
    diagnostics: list[dict[str, Any]] = []
    status = "derived_in_memory"
    if index_path.exists():
        try:
            index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            index_payload = {}
            diagnostics.append(
                {
                    "code": "curated_rag_index_unreadable",
                    "message": f"lexical index JSON could not be parsed: {exc.msg}",
                    "path": str(index_path),
                }
            )
        recorded_hash = index_payload.get("manifest_hash") if isinstance(index_payload, dict) else None
        if recorded_hash == manifest_hash:
            status = "fresh"
        else:
            status = "stale"
            diagnostics.append(
                {
                    "code": "curated_rag_index_stale",
                    "message": "lexical index manifest_hash does not match the current chunk manifest",
                    "path": str(index_path),
                }
            )
    return {
        "index_source": "file_backed_corpus_manifest",
        "index_path": str(index_path),
        "manifest_hash": manifest_hash,
        "index_status": status,
        "stale_index_diagnostics": diagnostics,
    }


def _required_string(raw: dict[str, Any], key: str) -> str:
    value = _string(raw.get(key))
    if value:
        return value
    raise ValueError(f"curated RAG {key} must be a non-empty string")


def _string(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return _hash_text(raw)
