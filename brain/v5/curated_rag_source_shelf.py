"""Read-only curated RAG projections over an exact source shelf generation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

from brain.v5.paths import WorkspacePaths
from brain.v5.source_shelf import load_source_shelf
from brain.v5.source_shelf_storage import (
    hash_json,
    load_source_shelf_manifest,
    source_shelf_root,
)


_DIGEST = re.compile(r"[0-9a-f]{64}")
_MAX_PASSAGES = 2000
_MAX_TEXT_BYTES = 8 * 1024 * 1024
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_MAX_PASSAGE_COMPONENT_BYTES = 12 * 1024 * 1024
_MAX_ISSUE_COMPONENT_BYTES = 2 * 1024 * 1024
_MAX_REQUESTED_SOURCES = 128
_MAX_SOURCE_PINS = 128
_MAX_ISSUES = 256
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
_PROMOTION_PATH = [
    "source_asset",
    "reference_location",
    "evidence",
    "validation",
    "trust_preflight",
]


def _source_shelf_curated_rag_catalog(
    base,
    *,
    generation: str,
    topic_id: str,
    catalog_version: str,
):
    shelf = _load_exact_shelf(base, generation=generation, topic_id=topic_id)
    passages = _grounded_passages(shelf)
    documents, document_ids = _documents(shelf, passages)
    chunks = _chunks(shelf, document_ids, passages)
    manifest = shelf.manifest
    requested = list(manifest.requested_source_asset_refs)
    resolved = [pin.source_asset_ref for pin in manifest.source_pins]
    indexed = sorted({passage.source_asset_ref for passage in passages})
    unindexed = sorted(set(requested).difference(indexed))
    issues = [
        {
            **asdict(issue),
            "source_location_pins": [asdict(pin) for pin in issue.source_location_pins],
        }
        for issue in shelf.issues
    ]
    return {
        "kind": "curated_rag_corpus",
        "catalog_version": catalog_version,
        "truth_source": "canonical_source_records_via_source_shelf",
        "summary_inputs_trusted": False,
        "can_claim_no_result": False,
        "can_update_claim_trust": False,
        "retrieval_policy": {
            "result_role": "heuristic_context",
            "read_surface_effect": "orientation_only",
            "allowed_uses": list(_ALLOWED_USES),
            "forbidden_uses": list(_FORBIDDEN_USES),
            "records_validation_result": False,
            "claim_trust_mutation": "none",
            "summary_inputs_trusted": False,
            "can_claim_no_result": False,
            "can_update_claim_trust": False,
            "requires_promotion_for_claim_support": True,
        },
        "index_policy": {
            "active_index_mode": "lexical_source_shelf",
            "supported_index_modes": ["lexical_source_shelf"],
            "embedding_index_required": False,
            "index_is_derived": True,
            "derived_from": "source_shelf_generation",
            "stale_index_behavior": "return_diagnostic_not_trust",
            "index_status": "fresh",
            "stale_index_diagnostics": [],
            "source_shelf_generation": manifest.generation,
            "source_shelf_manifest": _json_value(asdict(manifest)),
            "source_shelf_schema_version": manifest.schema_version,
            "source_shelf_topic_id": manifest.topic_id,
            "source_shelf_incomplete_coverage": manifest.incomplete_coverage,
            "source_shelf_issue_count": manifest.issue_count,
            "source_shelf_passage_count": manifest.passage_count,
            "source_shelf_passages_hash": manifest.passages_hash,
            "indexed_passage_count": len(chunks),
            "requested_source_asset_refs": requested,
            "resolved_source_asset_refs": resolved,
            "indexed_source_asset_refs": indexed,
            "unindexed_source_asset_refs": unindexed,
            "source_shelf_issues": issues,
        },
        "corpus_id": f"aitp.curated.source_shelf.{manifest.generation}",
        "document_count": len(documents),
        "chunk_count": len(chunks),
        "document_index": [document["document_id"] for document in documents],
        "chunk_index": [chunk["chunk_id"] for chunk in chunks],
        "documents": documents,
        "chunks": chunks,
    }


def _search_source_shelf_curated_rag(
    query: str,
    *,
    limit: int,
    catalog: dict,
    catalog_version: str,
):
    if type(query) is not str or not query.strip() or len(query) > 2000:
        raise ValueError("source shelf curated RAG query must be 1 to 2000 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 50:
        raise ValueError("source shelf curated RAG limit must be between 1 and 50")
    documents_by_id = {
        document["document_id"]: document for document in catalog["documents"]
    }
    terms = _tokenize(query)
    scored = []
    for chunk in catalog["chunks"]:
        document = documents_by_id[chunk["document_id"]]
        haystack = " ".join(
            (
                chunk["text"],
                chunk["summary"],
                " ".join(chunk["tags"]),
                document["title"],
                document["source_uri"],
                _flatten(chunk["anchor"]),
            )
        ).casefold()
        score = sum(1 for term in terms if term in haystack)
        if score:
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
            "anchor": _json_value(chunk["anchor"]),
            "tags": list(chunk["tags"]),
            "content_hash": chunk["content_hash"],
        }
        for score, chunk in scored[:limit]
    ]
    policy = catalog["index_policy"]
    return {
        "kind": "curated_rag_search_result",
        "catalog_version": catalog_version,
        "query": query,
        "requested_limit": limit,
        "index_mode": "lexical_source_shelf",
        "index_status": "fresh",
        "stale_index_diagnostics": [],
        "result_role": "heuristic_context",
        "summary_inputs_trusted": False,
        "can_claim_no_result": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "source_shelf_generation": policy["source_shelf_generation"],
        "source_shelf_topic_id": policy["source_shelf_topic_id"],
        "coverage": _coverage(policy),
        "result_count": len(results),
        "results": results,
    }


def _read_source_shelf_curated_rag_chunk(
    chunk_id: str,
    *,
    catalog: dict,
    catalog_version: str,
):
    if type(chunk_id) is not str or not chunk_id:
        raise ValueError("source shelf curated RAG chunk_id is required")
    chunk = _find(catalog["chunks"], "chunk_id", chunk_id)
    if chunk is None:
        raise ValueError(f"curated RAG chunk not found in source shelf generation: {chunk_id}")
    document = _find(catalog["documents"], "document_id", chunk["document_id"])
    policy = catalog["index_policy"]
    return {
        "kind": "curated_rag_chunk",
        "catalog_version": catalog_version,
        "truth_source": "canonical_source_records_via_source_shelf",
        "state_effect": "read_only",
        "retrieval_role": "heuristic_context",
        "read_surface_effect": "orientation_only",
        "summary_inputs_trusted": False,
        "can_claim_no_result": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
        "requires_promotion_for_claim_support": True,
        "promotion_required_before_claim_support": True,
        "lookup_creates_records": False,
        "corpus_id": catalog["corpus_id"],
        "chunk_id": chunk["chunk_id"],
        "document_id": document["document_id"],
        "index_mode": "lexical_source_shelf",
        "index_status": "fresh",
        "stale_index_diagnostics": [],
        "source_shelf_generation": policy["source_shelf_generation"],
        "source_shelf_topic_id": policy["source_shelf_topic_id"],
        "source_shelf_manifest": _json_value(policy["source_shelf_manifest"]),
        "coverage": _coverage(policy),
        "chunk": _json_value(chunk),
        "document": _json_value(document),
        "promotion_path": list(_PROMOTION_PATH),
        "forbidden_uses": list(_FORBIDDEN_USES),
        "promotion_boundary": {
            "retrieval_is_claim_support": False,
            "lookup_is_evidence": False,
            "lookup_records_validation_result": False,
            "lookup_satisfies_final_gate": False,
            "lookup_can_update_claim_trust": False,
            "requires_user_or_model_decision_before_write": True,
        },
    }


def _load_exact_shelf(base, *, generation, topic_id):
    if type(generation) is not str or not _DIGEST.fullmatch(generation):
        raise ValueError("source_shelf_generation must be a 64-character digest")
    if type(topic_id) is not str or not topic_id.strip():
        raise ValueError("topic_id is required with source_shelf_generation")
    ws = _workspace(base)
    generation_dir = source_shelf_root(ws) / "generations" / generation
    _require_bounded_file(generation_dir / "manifest.json", _MAX_MANIFEST_BYTES, "manifest")
    manifest = load_source_shelf_manifest(ws, generation)
    if manifest.topic_id != topic_id:
        raise ValueError("source shelf generation belongs to a different topic")
    if manifest.passage_count > _MAX_PASSAGES:
        raise ValueError("source shelf exceeds the bounded passage budget")
    if len(manifest.requested_source_asset_refs) > _MAX_REQUESTED_SOURCES:
        raise ValueError("source shelf exceeds the bounded requested-source budget")
    if len(manifest.source_pins) > _MAX_SOURCE_PINS:
        raise ValueError("source shelf exceeds the bounded source-pin budget")
    if manifest.issue_count > _MAX_ISSUES:
        raise ValueError("source shelf exceeds the bounded issue budget")
    _require_bounded_file(
        generation_dir / manifest.passage_file,
        _MAX_PASSAGE_COMPONENT_BYTES,
        "passage component",
    )
    _require_bounded_file(
        generation_dir / manifest.issues_file,
        _MAX_ISSUE_COMPONENT_BYTES,
        "issue component",
    )
    shelf = load_source_shelf(ws, generation)
    text_bytes = sum(len(passage.text.encode("utf-8")) for passage in shelf.passages)
    if text_bytes > _MAX_TEXT_BYTES:
        raise ValueError("source shelf exceeds the bounded text-byte budget")
    return shelf


def _require_bounded_file(path, max_bytes, label):
    try:
        size = path.stat().st_size
    except OSError:
        return
    if size > max_bytes:
        raise ValueError(f"source shelf exceeds the bounded {label} byte budget")


def _workspace(base):
    if isinstance(base, WorkspacePaths):
        return base
    if base is None:
        raise ValueError("base is required for source shelf curated RAG")
    path = Path(base).expanduser().resolve()
    if path.name == ".aitp":
        path = path.parent
    return WorkspacePaths(path)


def _documents(shelf, passages):
    passages_by_source = {}
    for passage in passages:
        passages_by_source.setdefault(passage.source_asset_ref, []).append(passage)
    documents = []
    ids = {}
    for pin in shelf.manifest.source_pins:
        source_passages = passages_by_source.get(pin.source_asset_ref, [])
        if not source_passages:
            continue
        document_id = f"curated_rag_doc:source_shelf:{_digest(pin.source_asset_ref)[:24]}"
        ids[pin.source_asset_ref] = document_id
        tags = _unique(
            [
                "source-shelf",
                "theoretical-physics",
                *(
                    kind
                    for passage in source_passages
                    for kind in passage.anchor_kinds
                ),
            ]
        )
        documents.append(
            {
                "document_id": document_id,
                "title": _source_title(pin.canonical_uri, pin.source_asset_ref),
                "asset_type": "source_shelf_source",
                "source_uri": pin.canonical_uri,
                "version_anchor": {
                    "source_shelf_generation": shelf.manifest.generation,
                    "source_asset_ref": pin.source_asset_ref,
                    "record_content_hash": pin.record_content_hash,
                    "record_revision": pin.record_revision,
                    "source_content_hash": pin.content_hash,
                    "canonical_uri": pin.canonical_uri,
                    "local_uri": pin.local_uri,
                    "acquisition_decision_ref": dict(pin.acquisition_decision_ref),
                    "acquisition_receipt_ref": dict(pin.acquisition_receipt_ref),
                    "source_location_pins": [
                        asdict(item) for item in pin.source_location_pins
                    ],
                },
                "content_hash": f"sha256:{pin.content_hash}",
                "tags": tags,
                "domain_hints": ["theoretical-physics"],
                "topic_hints": [shelf.manifest.topic_id],
                "language": "source",
                "priority": "high",
                "intended_use": "background_rag",
                "trust_status": "heuristic_context",
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    documents.sort(key=lambda item: item["document_id"])
    return documents, ids


def _chunks(shelf, document_ids, passages):
    chunks = []
    pins_by_source = {
        pin.source_asset_ref: pin for pin in shelf.manifest.source_pins
    }
    for passage in passages:
        pin = pins_by_source[passage.source_asset_ref]
        anchor = {
            "source_shelf_generation": shelf.manifest.generation,
            "source_shelf_passages_hash": shelf.manifest.passages_hash,
            "source_passage_id": passage.passage_id,
            "source_passage_ordinal": passage.ordinal,
            "source_asset_ref": passage.source_asset_ref,
            "source_content_hash": passage.source_content_hash,
            "source_record_content_hash": pin.record_content_hash,
            "source_record_revision": pin.record_revision,
            "text_hash": passage.text_hash,
            "canonical_uri": passage.canonical_uri,
            "local_uri": passage.local_uri,
            "page_start": passage.page_start,
            "page_end": passage.page_end,
            "section": passage.section,
            "anchor_kinds": list(passage.anchor_kinds),
            "anchor_labels": list(passage.anchor_labels),
            "source_location_refs": list(passage.source_location_refs),
            "source_location_pins": [
                asdict(item) for item in pin.source_location_pins
            ],
        }
        chunks.append(
            {
                "chunk_id": (
                    "curated_rag_chunk:source_shelf:"
                    + passage.passage_id.split(":", 1)[-1]
                ),
                "document_id": document_ids[passage.source_asset_ref],
                "anchor": anchor,
                "text": passage.text,
                "summary": _summary(passage.text, passage.section),
                "tags": _unique(["source-shelf", *passage.anchor_kinds]),
                "token_estimate": max(1, len(passage.text.split())),
                "content_hash": f"sha256:{passage.text_hash}",
                "retrieval_role": "heuristic_context",
                "orientation_only": True,
                "can_update_claim_trust": False,
            }
        )
    chunks.sort(key=lambda item: item["chunk_id"])
    return chunks


def _coverage(policy):
    coverage = {
        "source_shelf_generation": policy["source_shelf_generation"],
        "source_shelf_topic_id": policy["source_shelf_topic_id"],
        "requested_source_asset_refs": list(policy["requested_source_asset_refs"]),
        "resolved_source_asset_refs": list(policy["resolved_source_asset_refs"]),
        "indexed_source_asset_refs": list(policy["indexed_source_asset_refs"]),
        "unindexed_source_asset_refs": list(policy["unindexed_source_asset_refs"]),
        "incomplete": policy["source_shelf_incomplete_coverage"],
        "issue_count": policy["source_shelf_issue_count"],
        "issues": list(policy["source_shelf_issues"]),
        "source_shelf_passage_count": policy["source_shelf_passage_count"],
        "source_shelf_passages_hash": policy["source_shelf_passages_hash"],
        "indexed_passage_count": policy["indexed_passage_count"],
    }
    coverage["coverage_hash"] = hash_json(coverage)
    return coverage


def _grounded_passages(shelf):
    pins = {pin.source_asset_ref: pin for pin in shelf.manifest.source_pins}
    grounded = []
    for passage in shelf.passages:
        pin = pins.get(passage.source_asset_ref)
        if pin is None or not pin.source_location_pins or not passage.source_location_refs:
            continue
        pinned_refs = {location.record_ref for location in pin.source_location_pins}
        if set(passage.source_location_refs).issubset(pinned_refs):
            grounded.append(passage)
    return tuple(grounded)


def _tokenize(value):
    return list(dict.fromkeys(re.findall(r"[a-z0-9_+.-]+", value.casefold())))


def _flatten(value):
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    return str(value or "")


def _summary(text, section):
    compact = re.sub(r"\s+", " ", text).strip()
    prefix = f"{section}: " if section else ""
    return (prefix + compact)[:360]


def _source_title(uri, fallback):
    name = Path(unquote(urlsplit(uri).path)).name
    return name or fallback


def _find(items, key, value):
    return next((item for item in items if item.get(key) == value), None)


def _unique(values):
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def _digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json_value(value):
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value
