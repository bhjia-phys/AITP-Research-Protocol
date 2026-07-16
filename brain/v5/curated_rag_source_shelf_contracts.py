"""Contracts for curated RAG projections over immutable source shelves."""

from __future__ import annotations

import hashlib
from typing import Any

from brain.v5.contracts import ContractResult, _require_list, _require_mapping
from brain.v5.curated_rag_source_shelf_coverage_contracts import (
    catalog_coverage as _catalog_coverage,
    validate_coverage as _validate_coverage,
)
from brain.v5.curated_rag_source_shelf_authority import validate_source_shelf_authority
from brain.v5.curated_rag_source_shelf_contract_support import (
    LOCATION_PIN_KEYS as _LOCATION_PIN_KEYS,
    MANIFEST_BASIS_KEYS as _MANIFEST_BASIS_KEYS,
    MANIFEST_KEYS as _MANIFEST_KEYS,
    SOURCE_PIN_KEYS as _SOURCE_PIN_KEYS,
    digest as _digest,
    items as _items,
    non_empty as _non_empty,
    non_negative_int as _non_negative_int,
    positive_int as _positive_int,
    typed_ref as _typed_ref,
)
from brain.v5.source_shelf_models import (
    SOURCE_SHELF_EXTRACTOR_VERSION,
    SOURCE_SHELF_READER_VERSION,
    SOURCE_SHELF_SCHEMA_VERSION,
)
from brain.v5.source_shelf_storage import hash_json, source_passage_id


def validate_source_shelf_catalog(
    payload: dict[str, Any], path: str, result: ContractResult, *, base: Any = None,
) -> None:
    policy = payload.get("index_policy")
    if not isinstance(policy, dict):
        return
    generation = policy.get("source_shelf_generation")
    topic_id = policy.get("source_shelf_topic_id")
    if not _digest(generation):
        result.add(f"{path}.index_policy.source_shelf_generation", "must be a sha256 digest")
    if not _non_empty(topic_id):
        result.add(f"{path}.index_policy.source_shelf_topic_id", "must be non-empty")
    if payload.get("truth_source") != "canonical_source_records_via_source_shelf":
        result.add(f"{path}.truth_source", "must identify canonical records via the shelf")
    if payload.get("can_claim_no_result") is not False:
        result.add(f"{path}.can_claim_no_result", "must be false")
    if payload.get("corpus_id") != f"aitp.curated.source_shelf.{generation}":
        result.add(f"{path}.corpus_id", "must bind the exact source shelf generation")

    coverage = _catalog_coverage(policy)
    _validate_coverage(coverage, f"{path}.index_policy", result)
    for key in (
        "source_shelf_schema_version",
        "source_shelf_issue_count",
        "source_shelf_passage_count",
        "indexed_passage_count",
    ):
        if not _non_negative_int(policy.get(key)):
            result.add(f"{path}.index_policy.{key}", "must be a non-negative integer")
    if policy.get("source_shelf_issue_count") != len(_items(coverage.get("issues"))):
        result.add(f"{path}.index_policy.source_shelf_issue_count", "must match issues")
    if policy.get("source_shelf_incomplete_coverage") is not bool(
        _items(coverage.get("issues"))
    ):
        result.add(
            f"{path}.index_policy.source_shelf_incomplete_coverage",
            "must match issues",
        )
    if policy.get("indexed_passage_count") != payload.get("chunk_count"):
        result.add(f"{path}.index_policy.indexed_passage_count", "must match chunks")
    shelf_count = policy.get("source_shelf_passage_count")
    indexed_count = policy.get("indexed_passage_count")
    if _non_negative_int(shelf_count) and _non_negative_int(indexed_count) and indexed_count > shelf_count:
        result.add(f"{path}.index_policy.indexed_passage_count", "must not exceed shelf passages")

    manifest = policy.get("source_shelf_manifest")
    _require_mapping(manifest, f"{path}.index_policy.source_shelf_manifest", result)
    pins = _validate_manifest(
        manifest,
        generation=generation,
        topic_id=topic_id,
        coverage=coverage,
        path=f"{path}.index_policy.source_shelf_manifest",
        result=result,
    )
    if isinstance(manifest, dict):
        for manifest_key, policy_key in (
            ("schema_version", "source_shelf_schema_version"),
            ("passage_count", "source_shelf_passage_count"),
            ("issue_count", "source_shelf_issue_count"),
            ("incomplete_coverage", "source_shelf_incomplete_coverage"),
        ):
            if manifest.get(manifest_key) != policy.get(policy_key):
                result.add(
                    f"{path}.index_policy.source_shelf_manifest.{manifest_key}",
                    f"must match {policy_key}",
                )
        if manifest.get("passages_hash") != policy.get("source_shelf_passages_hash"):
            result.add(f"{path}.index_policy.source_shelf_passages_hash", "must match the shelf manifest")

    documents_by_source: dict[str, dict[str, Any]] = {}
    for index, document in enumerate(_items(payload.get("documents"))):
        if not isinstance(document, dict):
            continue
        anchor = document.get("version_anchor")
        item_path = f"{path}.documents[{index}]"
        _require_mapping(anchor, f"{item_path}.version_anchor", result)
        if not isinstance(anchor, dict):
            continue
        source_ref = anchor.get("source_asset_ref")
        if isinstance(source_ref, str) and source_ref in documents_by_source:
            result.add(f"{item_path}.version_anchor.source_asset_ref", "must be unique")
        if source_ref not in _items(coverage.get("indexed_source_asset_refs")):
            result.add(
                f"{item_path}.version_anchor.source_asset_ref",
                "must identify an indexed source",
            )
        _validate_document_pin(
            document,
            pins.get(source_ref) if isinstance(source_ref, str) else None,
            generation=generation,
            topic_id=topic_id,
            path=item_path,
            result=result,
        )
        if isinstance(source_ref, str):
            documents_by_source[source_ref] = document

    chunk_sources: set[str] = set()
    for index, chunk in enumerate(_items(payload.get("chunks"))):
        if not isinstance(chunk, dict):
            continue
        anchor = chunk.get("anchor")
        item_path = f"{path}.chunks[{index}]"
        _require_mapping(anchor, f"{item_path}.anchor", result)
        if not isinstance(anchor, dict):
            continue
        source_ref = anchor.get("source_asset_ref")
        if isinstance(source_ref, str):
            chunk_sources.add(source_ref)
        _validate_chunk_anchor(
            chunk,
            documents_by_source.get(source_ref) if isinstance(source_ref, str) else None,
            generation=generation,
            indexed=coverage.get("indexed_source_asset_refs", []),
            passages_hash=policy.get("source_shelf_passages_hash"),
            path=item_path,
            result=result,
        )
    indexed = coverage.get("indexed_source_asset_refs")
    if isinstance(indexed, list) and all(isinstance(item, str) for item in indexed) and set(indexed) != set(documents_by_source):
        result.add(f"{path}.index_policy.indexed_source_asset_refs", "must match documents")
    if isinstance(indexed, list) and all(isinstance(item, str) for item in indexed) and set(indexed) != chunk_sources:
        result.add(f"{path}.index_policy.indexed_source_asset_refs", "must match chunk sources")
    validate_source_shelf_authority(payload, path, result, base=base)
def validate_source_shelf_retrieval(
    payload: dict[str, Any], path: str, result: ContractResult, *, base: Any = None,
) -> None:
    generation = payload.get("source_shelf_generation")
    topic_id = payload.get("source_shelf_topic_id")
    if not _digest(generation):
        result.add(f"{path}.source_shelf_generation", "must be a sha256 digest")
    if not _non_empty(topic_id):
        result.add(f"{path}.source_shelf_topic_id", "must be non-empty")
    if payload.get("can_claim_no_result") is not False:
        result.add(f"{path}.can_claim_no_result", "must be false")
    if payload.get("kind") == "curated_rag_search_result" and not _positive_int(
        payload.get("requested_limit")
    ):
        result.add(f"{path}.requested_limit", "must be a positive integer")
    coverage = payload.get("coverage")
    _require_mapping(coverage, f"{path}.coverage", result)
    if isinstance(coverage, dict):
        _validate_coverage(
            coverage,
            f"{path}.coverage",
            result,
            generation=generation,
            topic_id=topic_id,
        )

    items = payload.get("results", [])
    if isinstance(payload.get("chunk"), dict):
        items = [payload["chunk"]]
    for index, item in enumerate(_items(items)):
        if not isinstance(item, dict):
            continue
        _validate_chunk_anchor(
            item,
            None,
            generation=generation,
            indexed=coverage.get("indexed_source_asset_refs", []) if isinstance(coverage, dict) else [],
            passages_hash=coverage.get("source_shelf_passages_hash") if isinstance(coverage, dict) else None,
            path=f"{path}.results[{index}]",
            result=result,
            require_document=False,
        )

    document = payload.get("document")
    chunk = payload.get("chunk")
    if isinstance(document, dict) and isinstance(chunk, dict):
        manifest = payload.get("source_shelf_manifest")
        _require_mapping(manifest, f"{path}.source_shelf_manifest", result)
        pins = _validate_manifest(
            manifest,
            generation=generation,
            topic_id=topic_id,
            coverage=coverage if isinstance(coverage, dict) else {},
            path=f"{path}.source_shelf_manifest",
            result=result,
        )
        if isinstance(manifest, dict) and isinstance(coverage, dict) and manifest.get(
            "passage_count"
        ) != coverage.get("source_shelf_passage_count"):
            result.add(
                f"{path}.coverage.source_shelf_passage_count",
                "must match the carried shelf manifest",
            )
        if isinstance(manifest, dict) and isinstance(coverage, dict) and manifest.get(
            "passages_hash"
        ) != coverage.get("source_shelf_passages_hash"):
            result.add(f"{path}.coverage.source_shelf_passages_hash", "must match the carried shelf manifest")
        chunk_anchor = chunk.get("anchor")
        source_ref = chunk_anchor.get("source_asset_ref") if isinstance(chunk_anchor, dict) else None
        _validate_document_pin(
            document,
            pins.get(source_ref) if isinstance(source_ref, str) else None,
            generation=generation,
            topic_id=topic_id,
            path=f"{path}.document",
            result=result,
        )
        _validate_chunk_anchor(
            chunk,
            document,
            generation=generation,
            indexed=coverage.get("indexed_source_asset_refs", []) if isinstance(coverage, dict) else [],
            passages_hash=coverage.get("source_shelf_passages_hash") if isinstance(coverage, dict) else None,
            path=f"{path}.chunk",
            result=result,
        )
    validate_source_shelf_authority(payload, path, result, base=base)


def _validate_manifest(
    manifest: Any, *, generation: Any, topic_id: Any,
    coverage: dict[str, Any], path: str, result: ContractResult,
) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        return {}
    if set(manifest) != _MANIFEST_KEYS:
        result.add(path, "must contain the exact source shelf manifest fields")
    if manifest.get("generation") != generation:
        result.add(f"{path}.generation", "must match the catalog shelf generation")
    if _digest(generation):
        basis = {key: manifest.get(key) for key in _MANIFEST_BASIS_KEYS}
        if hash_json(basis) != generation:
            result.add(f"{path}.generation", "must hash the exact shelf generation basis")
    if manifest.get("schema_version") != SOURCE_SHELF_SCHEMA_VERSION:
        result.add(f"{path}.schema_version", "must use the supported shelf schema")
    if manifest.get("topic_id") != topic_id:
        result.add(f"{path}.topic_id", "must match the shelf topic")
    if manifest.get("requested_source_asset_refs") != coverage.get(
        "requested_source_asset_refs"
    ):
        result.add(f"{path}.requested_source_asset_refs", "must match requested coverage")
    if not _non_empty(manifest.get("curation_rationale")):
        result.add(f"{path}.curation_rationale", "must be non-empty")
    if manifest.get("reader_version") != SOURCE_SHELF_READER_VERSION:
        result.add(f"{path}.reader_version", "must use the supported reader")
    if manifest.get("extractor_version") != SOURCE_SHELF_EXTRACTOR_VERSION:
        result.add(f"{path}.extractor_version", "must use the supported extractor")
    max_chars = manifest.get("max_passage_chars")
    if not _non_negative_int(max_chars) or not 256 <= max_chars <= 20000:
        result.add(f"{path}.max_passage_chars", "must be between 256 and 20000")
    for key in ("passage_count", "issue_count"):
        if not _non_negative_int(manifest.get(key)):
            result.add(f"{path}.{key}", "must be a non-negative integer")
    if manifest.get("issue_count") != len(_items(coverage.get("issues"))):
        result.add(f"{path}.issue_count", "must match exposed issues")
    if manifest.get("incomplete_coverage") is not bool(_items(coverage.get("issues"))):
        result.add(f"{path}.incomplete_coverage", "must match exposed issues")
    if manifest.get("issues_hash") != hash_json(_items(coverage.get("issues"))):
        result.add(f"{path}.issues_hash", "must hash the exposed shelf issues")
    if not _digest(manifest.get("passages_hash")):
        result.add(f"{path}.passages_hash", "must be a sha256 digest")
    if manifest.get("passage_file") != "passages.json":
        result.add(f"{path}.passage_file", "must name passages.json")
    if manifest.get("issues_file") != "issues.json":
        result.add(f"{path}.issues_file", "must name issues.json")
    if manifest.get("orientation_only") is not True:
        result.add(f"{path}.orientation_only", "must be true")
    if manifest.get("can_update_claim_trust") is not False:
        result.add(f"{path}.can_update_claim_trust", "must be false")

    source_pins = manifest.get("source_pins")
    _require_list(source_pins, f"{path}.source_pins", result)
    pins: dict[str, dict[str, Any]] = {}
    if not isinstance(source_pins, list):
        return pins
    for index, pin in enumerate(source_pins):
        pin_path = f"{path}.source_pins[{index}]"
        _require_mapping(pin, pin_path, result)
        if not isinstance(pin, dict):
            continue
        if set(pin) != _SOURCE_PIN_KEYS:
            result.add(pin_path, "must contain the exact source pin fields")
        source_ref = pin.get("source_asset_ref")
        if not _typed_ref(source_ref, "source_asset"):
            result.add(f"{pin_path}.source_asset_ref", "must be a typed source ref")
        elif source_ref in pins:
            result.add(f"{pin_path}.source_asset_ref", "must be unique")
        else:
            pins[source_ref] = pin
        if pin.get("topic_id") != topic_id:
            result.add(f"{pin_path}.topic_id", "must match the shelf topic")
        for key in ("record_content_hash", "content_hash"):
            if not _digest(pin.get(key)):
                result.add(f"{pin_path}.{key}", "must be a sha256 digest")
        revision = pin.get("record_revision")
        if revision is not None and not _positive_int(revision):
            result.add(f"{pin_path}.record_revision", "must be null or positive")
        for key in (
            "canonical_uri",
            "local_uri",
            "acquired_at",
            "access_disposition",
            "storage_permission",
        ):
            if not _non_empty(pin.get(key)):
                result.add(f"{pin_path}.{key}", "must be non-empty")
        for key in ("acquisition_decision_ref", "acquisition_receipt_ref"):
            _require_mapping(pin.get(key), f"{pin_path}.{key}", result)
        _validate_location_pins(pin, pin_path, result)
    if list(pins) != coverage.get("resolved_source_asset_refs"):
        result.add(f"{path}.source_pins", "must match resolved coverage")
    return pins
def _validate_location_pins(
    pin: dict[str, Any], path: str, result: ContractResult,
) -> None:
    locations = pin.get("source_location_pins")
    _require_list(locations, f"{path}.source_location_pins", result)
    if not isinstance(locations, list):
        return
    for index, location in enumerate(locations):
        location_path = f"{path}.source_location_pins[{index}]"
        _require_mapping(location, location_path, result)
        if not isinstance(location, dict):
            continue
        if set(location) != _LOCATION_PIN_KEYS:
            result.add(location_path, "must contain the exact location pin fields")
        if not _typed_ref(location.get("record_ref"), "reference_location"):
            result.add(f"{location_path}.record_ref", "must be a typed location ref")
        if not _digest(location.get("content_hash")):
            result.add(f"{location_path}.content_hash", "must be a sha256 digest")
        revision = location.get("revision")
        if revision is not None and not _positive_int(revision):
            result.add(f"{location_path}.revision", "must be null or positive")
        if location.get("topic_id") != pin.get("topic_id"):
            result.add(f"{location_path}.topic_id", "must match the source pin topic")
        if location.get("source_asset_ref") != pin.get("source_asset_ref"):
            result.add(f"{location_path}.source_asset_ref", "must match the source pin")
def _validate_document_pin(
    document: dict[str, Any], pin: dict[str, Any] | None, *, generation: Any,
    topic_id: Any, path: str, result: ContractResult,
) -> None:
    anchor = document.get("version_anchor")
    if not isinstance(anchor, dict):
        return
    if pin is None:
        result.add(f"{path}.version_anchor.source_asset_ref", "must bind a shelf source pin")
        return
    if not pin.get("source_location_pins"):
        result.add(f"{path}.version_anchor.source_location_pins", "must contain exact location provenance")
    expected = {
        "source_shelf_generation": generation,
        "source_asset_ref": pin.get("source_asset_ref"),
        "record_content_hash": pin.get("record_content_hash"),
        "record_revision": pin.get("record_revision"),
        "source_content_hash": pin.get("content_hash"),
        "canonical_uri": pin.get("canonical_uri"),
        "local_uri": pin.get("local_uri"),
        "acquisition_decision_ref": pin.get("acquisition_decision_ref"),
        "acquisition_receipt_ref": pin.get("acquisition_receipt_ref"),
        "source_location_pins": pin.get("source_location_pins"),
    }
    if anchor != expected:
        result.add(f"{path}.version_anchor", "must match the exact shelf source pin")
    if document.get("content_hash") != f"sha256:{pin.get('content_hash')}":
        result.add(f"{path}.content_hash", "must match the source bytes")
    if document.get("source_uri") != pin.get("canonical_uri"):
        result.add(f"{path}.source_uri", "must match the source pin")
    if document.get("topic_hints") != [topic_id]:
        result.add(f"{path}.topic_hints", "must match the shelf topic")


def _validate_chunk_anchor(
    chunk: dict[str, Any], document: dict[str, Any] | None, *, generation: Any,
    indexed: Any, passages_hash: Any, path: str, result: ContractResult,
    require_document: bool = True,
) -> None:
    anchor = chunk.get("anchor")
    if not isinstance(anchor, dict):
        return
    if anchor.get("source_shelf_generation") != generation:
        result.add(f"{path}.anchor.source_shelf_generation", "must match shelf generation")
    if not _digest(passages_hash) or anchor.get("source_shelf_passages_hash") != passages_hash:
        result.add(f"{path}.anchor.source_shelf_passages_hash", "must match the shelf passage component")
    source_ref = anchor.get("source_asset_ref")
    if not _typed_ref(source_ref, "source_asset"):
        result.add(f"{path}.anchor.source_asset_ref", "must be a typed source ref")
    elif not isinstance(indexed, list) or source_ref not in indexed:
        result.add(f"{path}.anchor.source_asset_ref", "must be present in indexed coverage")
    for key in ("source_content_hash", "source_record_content_hash", "text_hash"):
        if not _digest(anchor.get(key)):
            result.add(f"{path}.anchor.{key}", "must be a sha256 digest")
    if chunk.get("content_hash") != f"sha256:{anchor.get('text_hash')}":
        result.add(f"{path}.content_hash", "must match the passage text hash")
    text = chunk.get("text")
    actual_text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest() if isinstance(text, str) else None
    if actual_text_hash != anchor.get("text_hash"):
        result.add(f"{path}.text", "must hash to the exact source passage text hash")
    if not _typed_ref(anchor.get("source_passage_id"), "source-passage"):
        result.add(f"{path}.anchor.source_passage_id", "must be a source passage ref")
    ordinal = anchor.get("source_passage_ordinal")
    if not _positive_int(ordinal):
        result.add(f"{path}.anchor.source_passage_ordinal", "must be a positive integer")
    elif _digest(anchor.get("source_content_hash")) and _digest(anchor.get("text_hash")):
        expected_passage_id = source_passage_id(
            source_asset_ref=source_ref,
            source_content_hash=anchor.get("source_content_hash"),
            page_start=anchor.get("page_start"),
            page_end=anchor.get("page_end"),
            section=anchor.get("section"),
            ordinal=ordinal,
            text_hash=anchor.get("text_hash"),
        )
        if anchor.get("source_passage_id") != expected_passage_id:
            result.add(f"{path}.anchor.source_passage_id", "must match the deterministic passage identity")
    _require_list(anchor.get("source_location_refs"), f"{path}.anchor.source_location_refs", result)
    _require_list(anchor.get("source_location_pins"), f"{path}.anchor.source_location_pins", result)
    if not anchor.get("source_location_refs") or not anchor.get("source_location_pins"):
        result.add(f"{path}.anchor", "must contain exact location provenance")
    pinned_refs = [pin.get("record_ref") for pin in _items(anchor.get("source_location_pins")) if isinstance(pin, dict)]
    if anchor.get("source_location_refs") != pinned_refs:
        result.add(f"{path}.anchor.source_location_refs", "must match exact location pins")
    if document is None:
        if require_document:
            result.add(f"{path}.document_id", "must bind a source shelf document")
        return
    if document.get("document_id") != chunk.get("document_id"):
        result.add(f"{path}.document_id", "must match the source shelf document")
    version = document.get("version_anchor")
    if not isinstance(version, dict):
        return
    shared = {
        "source_shelf_generation": "source_shelf_generation",
        "source_asset_ref": "source_asset_ref",
        "source_content_hash": "source_content_hash",
        "source_record_content_hash": "record_content_hash",
        "source_record_revision": "record_revision",
        "canonical_uri": "canonical_uri",
        "local_uri": "local_uri",
        "source_location_pins": "source_location_pins",
    }
    for chunk_key, document_key in shared.items():
        if anchor.get(chunk_key) != version.get(document_key):
            result.add(f"{path}.anchor.{chunk_key}", "must match the document version pin")


__all__ = ["validate_source_shelf_catalog", "validate_source_shelf_retrieval"]
