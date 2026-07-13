# Compatibility shard 3 for curated_rag_corpus.
from __future__ import annotations

def _promotion_write_sequence() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "stage": "source_asset",
            "operation": "registerSourceAsset",
            "surface": "source_asset_record",
            "output_ref": "source_asset:<asset_id>",
            "requires_prior_refs": [],
            "feeds_next_stages": ["reference_location", "evidence"],
            "requires_explicit_execute_call": True,
            "executes_write_now": False,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
        },
        {
            "order": 2,
            "stage": "reference_location",
            "operation": "recordReferenceLocation",
            "surface": "reference_location_record",
            "output_ref": "reference_location:<location_id>",
            "requires_prior_refs": ["source_asset:<asset_id>"],
            "feeds_next_stages": ["evidence"],
            "requires_explicit_execute_call": True,
            "executes_write_now": False,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
        },
        {
            "order": 3,
            "stage": "evidence",
            "operation": "recordEvidence",
            "surface": "evidence_record",
            "output_ref": "evidence:<evidence_id>",
            "requires_prior_refs": [
                "source_asset:<asset_id>",
                "reference_location:<location_id>",
            ],
            "feeds_next_stages": ["validation", "trust_preflight"],
            "requires_explicit_execute_call": True,
            "executes_write_now": False,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
        },
        {
            "order": 4,
            "stage": "validation",
            "operation": "createValidationContract",
            "surface": "validation_contract_record",
            "output_ref": "validation_contract:<contract_id>",
            "requires_prior_refs": ["evidence:<evidence_id>"],
            "feeds_next_stages": ["trust_preflight"],
            "requires_explicit_execute_call": True,
            "executes_write_now": False,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
        },
        {
            "order": 5,
            "stage": "trust_preflight",
            "operation": "preflightTrustUpdate",
            "surface": "trust_update_preflight",
            "output_ref": "trust_preflight:<preflight_token>",
            "requires_prior_refs": [
                "evidence:<evidence_id>",
                "validation_result:<result_id>",
            ],
            "feeds_next_stages": [],
            "requires_explicit_execute_call": True,
            "executes_write_now": False,
            "records_validation_result": False,
            "claim_trust_mutation": "none",
        },
    ]

def _find_by_id(items: list[dict[str, Any]], key: str, value: str) -> dict[str, Any] | None:
    wanted = _string(value)
    for item in items:
        if item.get(key) == wanted:
            return item
    return None

def _linked_records(topic_id: str, claim_id: str) -> dict[str, Any]:
    links: dict[str, Any] = {}
    if topic_id:
        links["topic_id"] = topic_id
    if claim_id:
        links["claim_id"] = claim_id
    return links

def _source_asset_type(asset_type: str) -> str:
    value = _string(asset_type)
    if value in {"paper", "lecture", "note", "book", "code_repo", "code_snapshot", "dataset", "web_page", "other"}:
        return value
    if value in {"review", "textbook"}:
        return "book" if value == "textbook" else "paper"
    return "other"

def _reference_location_type(asset_type: str) -> str:
    value = _string(asset_type)
    if value in {"paper", "lecture", "note", "book", "code_repo", "dataset", "web_page"}:
        return value
    return "source"

def _hash_algorithm(content_hash: str) -> str:
    value = _string(content_hash)
    if value.startswith("sha256:"):
        return "sha256"
    return ""

def _tokenize(query: str) -> list[str]:
    return [
        token.strip().lower()
        for token in re.split(r"[^A-Za-z0-9]+", query.replace("_", " ").replace("-", " "))
        if token.strip()
    ]

def _flatten_anchor_terms(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(
            _flatten_anchor_terms(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return " ".join(_flatten_anchor_terms(item) for item in value)
    if isinstance(value, str):
        return value
    return ""

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
