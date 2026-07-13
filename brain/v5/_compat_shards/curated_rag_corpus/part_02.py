# Compatibility shard 2 for curated_rag_corpus.
from __future__ import annotations

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
    documents_by_id = {
        document["document_id"]: document
        for document in catalog["documents"]
    }
    terms = [term for term in _tokenize(query) if term]
    scored: list[tuple[int, dict[str, Any]]] = []
    for chunk in catalog["chunks"]:
        document = documents_by_id.get(chunk["document_id"], {})
        haystack = " ".join(
            [
                chunk["text"],
                chunk["summary"],
                " ".join(chunk["tags"]),
                chunk["document_id"],
                " ".join(_string_list(document.get("tags"))),
                " ".join(_string_list(document.get("domain_hints"))),
                " ".join(_string_list(document.get("topic_hints"))),
                _string(document.get("title")),
                _string(document.get("source_uri")),
                _flatten_anchor_terms(chunk.get("anchor")),
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

def read_curated_rag_chunk(
    chunk_id: str,
    *,
    base: str | Path | WorkspacePaths | None = None,
) -> dict[str, Any]:
    """Return one curated RAG chunk with canonical manifest identity metadata.

    This is a read-only lookup surface. It exposes chunk/document identity,
    anchor, hash, and source metadata for host planning, but it does not promote
    the chunk into source support, evidence, validation, final-gate state, or
    claim trust.
    """

    catalog = curated_rag_corpus(base)
    chunk = _find_by_id(catalog["chunks"], "chunk_id", chunk_id)
    if chunk is None:
        raise ValueError(f"curated RAG chunk not found: {chunk_id}")
    document = _find_by_id(catalog["documents"], "document_id", chunk["document_id"])
    if document is None:
        raise ValueError(f"curated RAG document not found for chunk: {chunk_id}")
    return {
        "kind": "curated_rag_chunk",
        "catalog_version": CATALOG_VERSION,
        "truth_source": "curated_rag_chunk_manifest",
        "state_effect": "read_only",
        "retrieval_role": "heuristic_context",
        "read_surface_effect": "orientation_only",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "promotion_required_before_claim_support": True,
        "lookup_creates_records": False,
        "corpus_id": catalog["corpus_id"],
        "chunk_id": chunk["chunk_id"],
        "document_id": document["document_id"],
        "index_mode": catalog["index_policy"]["active_index_mode"],
        "index_status": catalog["index_policy"].get("index_status", "fresh"),
        "stale_index_diagnostics": catalog["index_policy"].get("stale_index_diagnostics", []),
        "chunk": {
            "chunk_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "anchor": chunk["anchor"],
            "summary": chunk["summary"],
            "text": chunk["text"],
            "tags": chunk["tags"],
            "token_estimate": chunk["token_estimate"],
            "content_hash": chunk["content_hash"],
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        "document": {
            "document_id": document["document_id"],
            "title": document["title"],
            "asset_type": document["asset_type"],
            "source_uri": document["source_uri"],
            "version_anchor": document["version_anchor"],
            "content_hash": document["content_hash"],
            "tags": document["tags"],
            "domain_hints": document["domain_hints"],
            "topic_hints": document["topic_hints"],
            "language": document["language"],
            "priority": document["priority"],
            "intended_use": document["intended_use"],
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        "promotion_path": [
            "source_asset",
            "reference_location",
            "evidence",
            "validation",
            "trust_preflight",
        ],
        "forbidden_uses": _FORBIDDEN_USES,
        "promotion_boundary": {
            "retrieval_is_claim_support": False,
            "lookup_is_evidence": False,
            "lookup_records_validation_result": False,
            "lookup_satisfies_final_gate": False,
            "lookup_can_update_claim_trust": False,
            "requires_user_or_model_decision_before_write": True,
        },
    }

def draft_curated_rag_promotion(
    chunk_id: str,
    *,
    base: str | Path | WorkspacePaths | None = None,
    topic_id: str = "",
    claim_id: str = "",
    connector_id: str = "curated_rag",
    promotion_intent: str = "claim_support_review",
) -> dict[str, Any]:
    """Draft the normal AITP promotion path for one curated RAG chunk.

    The returned payload is a read-only planning surface. It does not register
    sources, create evidence, record validation, satisfy a final gate, or change
    claim trust.
    """

    catalog = curated_rag_corpus(base)
    chunk = _find_by_id(catalog["chunks"], "chunk_id", chunk_id)
    if chunk is None:
        raise ValueError(f"curated RAG chunk not found: {chunk_id}")
    document = _find_by_id(catalog["documents"], "document_id", chunk["document_id"])
    if document is None:
        raise ValueError(f"curated RAG document not found for chunk: {chunk_id}")

    topic = _string(topic_id)
    claim = _string(claim_id)
    connector = _string(connector_id) or "curated_rag"
    intent = _string(promotion_intent) or "claim_support_review"
    missing_context = [name for name, value in (("topic_id", topic), ("claim_id", claim)) if not value]
    chunk_ref = chunk["chunk_id"]
    document_ref = document["document_id"]
    source_summary = (
        f"Promotion draft for curated RAG chunk {chunk_ref}. "
        "The chunk remains heuristic context until ordinary AITP source, evidence, "
        "validation, and trust-preflight records are created."
    )

    source_asset_payload = {
        "topic_id": topic,
        "claim_id": claim,
        "asset_type": _source_asset_type(document["asset_type"]),
        "uri": document["source_uri"],
        "title": document["title"],
        "label": document["title"],
        "content_hash": document["content_hash"],
        "hash_algorithm": _hash_algorithm(document["content_hash"]),
        "version_anchor": document["version_anchor"],
        "source_kind": "curated_rag_promotion_draft",
        "summary": source_summary,
        "source_refs": [chunk_ref],
        "artifact_ids": [],
        "code_state_ids": [],
        "reference_location_ids": [],
        "derived_from": [document_ref, chunk_ref],
        "metadata": {
            "curated_rag_corpus_id": catalog["corpus_id"],
            "curated_rag_document_id": document_ref,
            "curated_rag_chunk_id": chunk_ref,
            "retrieval_role": "heuristic_context",
            "promotion_intent": intent,
        },
        "linked_records": _linked_records(topic, claim),
    }
    reference_payload = {
        "topic_id": topic,
        "claim_id": claim,
        "connector_id": connector,
        "location_type": _reference_location_type(document["asset_type"]),
        "uri": document["source_uri"],
        "label": document["title"],
        "source_ref": chunk_ref,
        "external_id": document_ref,
        "status": "located",
        "summary": chunk["summary"],
        "metadata": {
            "curated_rag_corpus_id": catalog["corpus_id"],
            "curated_rag_document_id": document_ref,
            "curated_rag_chunk_id": chunk_ref,
            "anchor": chunk["anchor"],
            "content_hash": chunk["content_hash"],
            "retrieval_role": "heuristic_context",
        },
        "linked_records": _linked_records(topic, claim),
    }

    return {
        "kind": "curated_rag_promotion_draft",
        "catalog_version": CATALOG_VERSION,
        "truth_source": "curated_rag_chunk_manifest",
        "state_effect": "read_only",
        "draft_role": "promotion_planning",
        "retrieval_role": "heuristic_context",
        "read_surface_effect": "orientation_only",
        "summary_inputs_trusted": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "promotion_required_before_claim_support": True,
        "draft_creates_records": False,
        "corpus_id": catalog["corpus_id"],
        "chunk_id": chunk_ref,
        "document_id": document_ref,
        "topic_id": topic,
        "claim_id": claim,
        "connector_id": connector,
        "promotion_intent": intent,
        "required_context_before_write": missing_context,
        "index_mode": catalog["index_policy"]["active_index_mode"],
        "index_status": catalog["index_policy"].get("index_status", "fresh"),
        "stale_index_diagnostics": catalog["index_policy"].get("stale_index_diagnostics", []),
        "chunk": {
            "chunk_id": chunk_ref,
            "document_id": document_ref,
            "anchor": chunk["anchor"],
            "summary": chunk["summary"],
            "text": chunk["text"],
            "tags": chunk["tags"],
            "content_hash": chunk["content_hash"],
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        "document": {
            "document_id": document_ref,
            "title": document["title"],
            "asset_type": document["asset_type"],
            "source_uri": document["source_uri"],
            "version_anchor": document["version_anchor"],
            "content_hash": document["content_hash"],
            "tags": document["tags"],
            "domain_hints": document["domain_hints"],
            "topic_hints": document["topic_hints"],
            "language": document["language"],
            "priority": document["priority"],
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
        },
        "draft_operations": [
            {
                "stage": "source_asset",
                "operation": "registerSourceAsset",
                "mcp_tool": "aitp_v5_register_source_asset",
                "cli_template": "aitp-v5 asset register <args>",
                "surface": "source_asset_record",
                "draft_only": True,
                "creates_record_now": False,
                "claim_support_created": False,
                "payload_draft": source_asset_payload,
            },
            {
                "stage": "reference_location",
                "operation": "recordReferenceLocation",
                "mcp_tool": "aitp_v5_record_reference_location",
                "cli_template": "aitp-v5 reference location record <args>",
                "surface": "reference_location_record",
                "draft_only": True,
                "creates_record_now": False,
                "claim_support_created": False,
                "payload_draft": reference_payload,
            },
            {
                "stage": "evidence",
                "operation": "recordEvidence",
                "mcp_tool": "aitp_v5_record_evidence",
                "cli_template": "aitp-v5 evidence record <args>",
                "surface": "evidence_record",
                "draft_only": True,
                "creates_record_now": False,
                "claim_support_created": False,
                "requires_existing_records": ["source_asset_record", "reference_location_record"],
                "payload_template": {
                    "topic_id": topic,
                    "claim_id": claim,
                    "evidence_type": "source_text_review",
                    "status": "unreviewed",
                    "summary": chunk["summary"],
                    "supports_outputs": [],
                    "source_refs": ["<source_asset_id>", "<reference_location_id>"],
                    "tool_run_ids": [],
                    "validation_result_ids": [],
                    "artifact_ids": [],
                },
            },
            {
                "stage": "validation",
                "operation": "createValidationContract",
                "mcp_tool": "aitp_v5_create_validation_contract",
                "cli_template": "aitp-v5 validation contract create <args>",
                "surface": "validation_contract_record",
                "draft_only": True,
                "creates_record_now": False,
                "claim_support_created": False,
                "requires_existing_records": ["evidence_record"],
                "payload_template": {
                    "topic_id": topic,
                    "claim_id": claim,
                    "required_checks": ["verify_source_text_supports_claim_scope"],
                    "failure_modes": [
                        "retrieved_chunk_is_only_background",
                        "source_context_changes_claim_meaning",
                    ],
                    "required_evidence_outputs": ["source_text_claim_support_assessment"],
                    "tool_recipe_ids": [],
                    "executor_ids": [],
                    "validator_role": "adversarial_reviewer",
                },
            },
            {
                "stage": "trust_preflight",
                "operation": "preflightTrustUpdate",
                "mcp_tool": "aitp_v5_preflight_trust_update",
                "cli_template": "aitp-v5 trust preflight <args>",
                "surface": "trust_update_preflight",
                "draft_only": True,
                "creates_record_now": False,
                "claim_support_created": False,
                "requires_existing_records": ["evidence_record", "validation_result_record"],
                "payload_template": {
                    "action": "change_claim_confidence",
                    "topic_id": topic,
                    "claim_id": claim,
                    "source_kind": "typed_records",
                    "source_ref": "<evidence_id>",
                    "evidence_refs": ["<evidence_id>"],
                    "code_state_ids": [],
                    "rationale": "Only after source/evidence/validation records exist.",
                },
            },
        ],
        "promotion_write_sequence": _promotion_write_sequence(),
        "promotion_path": [
            "source_asset",
            "reference_location",
            "evidence",
            "validation",
            "trust_preflight",
        ],
        "forbidden_uses": _FORBIDDEN_USES,
        "promotion_boundary": {
            "retrieval_is_claim_support": False,
            "draft_is_evidence": False,
            "draft_records_validation_result": False,
            "draft_satisfies_final_gate": False,
            "draft_can_update_claim_trust": False,
            "requires_user_or_model_decision_before_write": True,
        },
    }
