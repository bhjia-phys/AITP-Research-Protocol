"""Contracts for curated heuristic RAG corpus surfaces."""

from __future__ import annotations

from typing import Any

from brain.v5.contracts import ContractError, ContractResult, _require_list, _require_mapping
from brain.v5.curated_rag_corpus import CATALOG_VERSION, curated_rag_corpus


def validate_curated_rag_corpus(
    payload: Any,
    *,
    path: str = "curated_rag_corpus",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    _validate_common_no_trust(payload, path, result)
    if payload.get("kind") != "curated_rag_corpus":
        result.add(f"{path}.kind", "must be 'curated_rag_corpus'")
    if payload.get("truth_source") != "curated_rag_corpus_catalog":
        result.add(f"{path}.truth_source", "must be 'curated_rag_corpus_catalog'")
    _require_mapping(payload.get("retrieval_policy"), f"{path}.retrieval_policy", result)
    if isinstance(payload.get("retrieval_policy"), dict):
        _validate_retrieval_policy(payload["retrieval_policy"], f"{path}.retrieval_policy", result)
    _require_mapping(payload.get("index_policy"), f"{path}.index_policy", result)
    if isinstance(payload.get("index_policy"), dict):
        _validate_index_policy(payload["index_policy"], f"{path}.index_policy", result)

    for key in ("documents", "chunks", "document_index", "chunk_index"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("documents"), list):
        if payload.get("document_count") != len(payload["documents"]):
            result.add(f"{path}.document_count", "must equal len(documents)")
        document_index = [document.get("document_id") for document in payload["documents"] if isinstance(document, dict)]
        if payload.get("document_index") != document_index:
            result.add(f"{path}.document_index", "must list document ids in catalog order")
        _validate_documents(payload["documents"], f"{path}.documents", result)
    document_ids = {
        document.get("document_id")
        for document in payload.get("documents", [])
        if isinstance(document, dict) and isinstance(document.get("document_id"), str)
    }
    if isinstance(payload.get("chunks"), list):
        if payload.get("chunk_count") != len(payload["chunks"]):
            result.add(f"{path}.chunk_count", "must equal len(chunks)")
        chunk_index = [chunk.get("chunk_id") for chunk in payload["chunks"] if isinstance(chunk, dict)]
        if payload.get("chunk_index") != chunk_index:
            result.add(f"{path}.chunk_index", "must list chunk ids in catalog order")
        _validate_chunks(payload["chunks"], f"{path}.chunks", result, document_ids)

    if payload.get("index_policy", {}).get("active_index_mode") == "lexical_fixture":
        if payload != curated_rag_corpus():
            result.add(path, "fixture corpus must match curated_rag_corpus()")
    return result


def require_valid_curated_rag_corpus(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_curated_rag_corpus(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_curated_rag_search_result(
    payload: Any,
    *,
    path: str = "curated_rag_search_result",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    _validate_common_no_trust(payload, path, result)
    if payload.get("kind") != "curated_rag_search_result":
        result.add(f"{path}.kind", "must be 'curated_rag_search_result'")
    if payload.get("result_role") != "heuristic_context":
        result.add(f"{path}.result_role", "must be 'heuristic_context'")
    if payload.get("records_validation_result") is not False:
        result.add(f"{path}.records_validation_result", "must be false")
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    if payload.get("requires_promotion_for_claim_support") is not True:
        result.add(f"{path}.requires_promotion_for_claim_support", "must be true")
    if not isinstance(payload.get("query"), str):
        result.add(f"{path}.query", "must be a string")
    if payload.get("index_mode") not in {"lexical_fixture", "lexical_file_backed"}:
        result.add(f"{path}.index_mode", "must be a supported lexical curated RAG mode")
    if payload.get("index_status") is not None and not isinstance(payload.get("index_status"), str):
        result.add(f"{path}.index_status", "must be a string when present")
    if payload.get("stale_index_diagnostics") is not None:
        _require_list(payload.get("stale_index_diagnostics"), f"{path}.stale_index_diagnostics", result)
    _require_list(payload.get("results"), f"{path}.results", result)
    if isinstance(payload.get("results"), list):
        if payload.get("result_count") != len(payload["results"]):
            result.add(f"{path}.result_count", "must equal len(results)")
        for index, item in enumerate(payload["results"]):
            _validate_search_result_item(item, f"{path}.results[{index}]", result)
    return result


def require_valid_curated_rag_search_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_curated_rag_search_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def validate_curated_rag_ingest_result(
    payload: Any,
    *,
    path: str = "curated_rag_ingest_result",
) -> ContractResult:
    result = ContractResult()
    _require_mapping(payload, path, result)
    if not isinstance(payload, dict):
        return result

    _validate_common_no_trust(payload, path, result)
    if payload.get("kind") != "curated_rag_ingest_result":
        result.add(f"{path}.kind", "must be 'curated_rag_ingest_result'")
    if payload.get("ok") is not True:
        result.add(f"{path}.ok", "must be true")
    if payload.get("state_effect") != "curated_rag_manifest_write":
        result.add(f"{path}.state_effect", "must be 'curated_rag_manifest_write'")
    if payload.get("truth_source") != "curated_rag_ingestion":
        result.add(f"{path}.truth_source", "must be 'curated_rag_ingestion'")
    for key in ("corpus_id", "manifest_path", "index_path", "manifest_hash", "index_status"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    for key in ("document_count", "chunk_count"):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            result.add(f"{path}.{key}", "must be a non-negative integer")
    for key in ("document_ids", "chunk_ids", "source_paths", "forbidden_uses", "promotion_path"):
        _require_list(payload.get(key), f"{path}.{key}", result)
    if isinstance(payload.get("document_ids"), list) and payload.get("document_count") != len(payload["document_ids"]):
        result.add(f"{path}.document_count", "must equal len(document_ids)")
    if isinstance(payload.get("chunk_ids"), list) and payload.get("chunk_count") != len(payload["chunk_ids"]):
        result.add(f"{path}.chunk_count", "must equal len(chunk_ids)")
    if payload.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    if payload.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if payload.get("records_validation_result") is not False:
        result.add(f"{path}.records_validation_result", "must be false")
    if payload.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    if payload.get("requires_promotion_for_claim_support") is not True:
        result.add(f"{path}.requires_promotion_for_claim_support", "must be true")
    if payload.get("promotion_required_before_claim_support") is not True:
        result.add(f"{path}.promotion_required_before_claim_support", "must be true")
    if payload.get("forbidden_uses") != [
        "evidence_support",
        "validation_result",
        "claim_trust_update",
        "trust_apply",
        "final_gate_satisfaction",
    ]:
        result.add(f"{path}.forbidden_uses", "must list evidence/validation/trust exclusions")
    if payload.get("promotion_path") != [
        "source_asset",
        "reference_location",
        "evidence",
        "validation",
        "trust_preflight",
    ]:
        result.add(f"{path}.promotion_path", "must describe the normal AITP promotion path")
    return result


def require_valid_curated_rag_ingest_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_curated_rag_ingest_result(payload)
    if not result.ok:
        raise ContractError(result)
    return payload


def _validate_common_no_trust(payload: dict[str, Any], path: str, result: ContractResult) -> None:
    if payload.get("catalog_version") != CATALOG_VERSION:
        result.add(f"{path}.catalog_version", f"must be '{CATALOG_VERSION}'")
    if payload.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if payload.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")


def _validate_retrieval_policy(policy: dict[str, Any], path: str, result: ContractResult) -> None:
    if policy.get("result_role") != "heuristic_context":
        result.add(f"{path}.result_role", "must be 'heuristic_context'")
    if policy.get("read_surface_effect") != "orientation_only":
        result.add(f"{path}.read_surface_effect", "must be 'orientation_only'")
    if policy.get("allowed_uses") != [
        "conceptual_scaffolding",
        "literature_orientation",
        "derivation_scaffolding",
        "method_selection",
        "source_backtrace_suggestions",
    ]:
        result.add(f"{path}.allowed_uses", "must list heuristic host uses")
    if policy.get("forbidden_uses") != [
        "evidence_support",
        "validation_result",
        "claim_trust_update",
        "trust_apply",
        "final_gate_satisfaction",
    ]:
        result.add(f"{path}.forbidden_uses", "must list evidence/validation/trust exclusions")
    if policy.get("records_validation_result") is not False:
        result.add(f"{path}.records_validation_result", "must be false")
    if policy.get("claim_trust_mutation") != "none":
        result.add(f"{path}.claim_trust_mutation", "must be 'none'")
    if policy.get("summary_inputs_trusted") is not False:
        result.add(f"{path}.summary_inputs_trusted", "must be false")
    if policy.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    if policy.get("requires_promotion_for_claim_support") is not True:
        result.add(f"{path}.requires_promotion_for_claim_support", "must be true")


def _validate_index_policy(policy: dict[str, Any], path: str, result: ContractResult) -> None:
    active_index_mode = policy.get("active_index_mode")
    if active_index_mode not in {"lexical_fixture", "lexical_file_backed"}:
        result.add(f"{path}.active_index_mode", "must be a supported lexical curated RAG mode")
    if policy.get("supported_index_modes") != [active_index_mode]:
        result.add(f"{path}.supported_index_modes", "must list the active lexical mode")
    if policy.get("embedding_index_required") is not False:
        result.add(f"{path}.embedding_index_required", "must be false")
    if policy.get("index_is_derived") is not True:
        result.add(f"{path}.index_is_derived", "must be true")
    if policy.get("derived_from") != "curated_rag_chunk_manifest":
        result.add(f"{path}.derived_from", "must be 'curated_rag_chunk_manifest'")
    if policy.get("stale_index_behavior") != "return_diagnostic_not_trust":
        result.add(f"{path}.stale_index_behavior", "must return diagnostics, not trust")
    if active_index_mode == "lexical_file_backed":
        if policy.get("index_source") != "file_backed_corpus_manifest":
            result.add(f"{path}.index_source", "must be 'file_backed_corpus_manifest'")
        if not isinstance(policy.get("manifest_hash"), str) or not policy.get("manifest_hash"):
            result.add(f"{path}.manifest_hash", "must be a non-empty string")
        if policy.get("index_status") not in {"fresh", "stale", "derived_in_memory"}:
            result.add(f"{path}.index_status", "must be fresh, stale, or derived_in_memory")
        _require_list(policy.get("stale_index_diagnostics"), f"{path}.stale_index_diagnostics", result)


def _validate_documents(documents: list[Any], path: str, result: ContractResult) -> None:
    ids: set[str] = set()
    for index, document in enumerate(documents):
        item_path = f"{path}[{index}]"
        _require_mapping(document, item_path, result)
        if not isinstance(document, dict):
            continue
        document_id = document.get("document_id")
        if not isinstance(document_id, str) or not document_id:
            result.add(f"{item_path}.document_id", "must be a non-empty string")
        elif document_id in ids:
            result.add(f"{item_path}.document_id", "must be unique")
        else:
            ids.add(document_id)
        for key in ("title", "asset_type", "source_uri", "content_hash", "language", "priority", "intended_use"):
            if not isinstance(document.get(key), str) or not document.get(key):
                result.add(f"{item_path}.{key}", "must be a non-empty string")
        for key in ("tags", "domain_hints", "topic_hints"):
            _require_list(document.get(key), f"{item_path}.{key}", result)
        if document.get("trust_status") != "heuristic_context":
            result.add(f"{item_path}.trust_status", "must be 'heuristic_context'")
        if document.get("orientation_only") is not True:
            result.add(f"{item_path}.orientation_only", "must be true")
        if document.get("can_update_claim_trust") is not False:
            result.add(f"{item_path}.can_update_claim_trust", "must be false")


def _validate_chunks(
    chunks: list[Any],
    path: str,
    result: ContractResult,
    document_ids: set[str],
) -> None:
    ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        item_path = f"{path}[{index}]"
        _require_mapping(chunk, item_path, result)
        if not isinstance(chunk, dict):
            continue
        chunk_id = chunk.get("chunk_id")
        if not isinstance(chunk_id, str) or not chunk_id:
            result.add(f"{item_path}.chunk_id", "must be a non-empty string")
        elif chunk_id in ids:
            result.add(f"{item_path}.chunk_id", "must be unique")
        else:
            ids.add(chunk_id)
        for key in ("document_id", "text", "summary", "content_hash"):
            if not isinstance(chunk.get(key), str) or not chunk.get(key):
                result.add(f"{item_path}.{key}", "must be a non-empty string")
        if chunk.get("document_id") not in document_ids:
            result.add(f"{item_path}.document_id", "must refer to a corpus document")
        _require_mapping(chunk.get("anchor"), f"{item_path}.anchor", result)
        _require_list(chunk.get("tags"), f"{item_path}.tags", result)
        if not isinstance(chunk.get("token_estimate"), int) or chunk["token_estimate"] <= 0:
            result.add(f"{item_path}.token_estimate", "must be a positive integer")
        if chunk.get("retrieval_role") != "heuristic_context":
            result.add(f"{item_path}.retrieval_role", "must be 'heuristic_context'")
        if chunk.get("orientation_only") is not True:
            result.add(f"{item_path}.orientation_only", "must be true")
        if chunk.get("can_update_claim_trust") is not False:
            result.add(f"{item_path}.can_update_claim_trust", "must be false")


def _validate_search_result_item(item: Any, path: str, result: ContractResult) -> None:
    _require_mapping(item, path, result)
    if not isinstance(item, dict):
        return
    for key in ("chunk_id", "document_id", "summary", "text", "content_hash"):
        if not isinstance(item.get(key), str) or not item.get(key):
            result.add(f"{path}.{key}", "must be a non-empty string")
    if not isinstance(item.get("score"), int) or item["score"] <= 0:
        result.add(f"{path}.score", "must be a positive integer")
    if item.get("retrieval_role") != "heuristic_context":
        result.add(f"{path}.retrieval_role", "must be 'heuristic_context'")
    if item.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if item.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")
    _require_mapping(item.get("anchor"), f"{path}.anchor", result)
    _require_list(item.get("tags"), f"{path}.tags", result)
