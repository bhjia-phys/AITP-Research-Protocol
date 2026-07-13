# Compatibility shard 1 for curated_rag_corpus.
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
        {
            "document_id": "curated_rag_doc:open_theory_lecture_shelf",
            "title": "Open theory lecture shelf",
            "asset_type": "lecture",
            "source_uri": "aitp://curated-rag/open-theory-lecture-shelf",
            "version_anchor": {"catalog_version": CATALOG_VERSION, "revision": "v1"},
            "content_hash": "sha256:curated-rag-open-theory-lecture-shelf-v1",
            "tags": [
                "theoretical-physics",
                "lecture",
                "qft",
                "general-relativity",
                "holography",
                "quantum-information",
                "orientation",
            ],
            "domain_hints": ["theoretical-physics/general"],
            "topic_hints": ["lecture-orientation", "domain-intuition", "source-backtrace"],
            "language": "en",
            "priority": "high",
            "intended_use": "background_rag",
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "curation_policy": {
                "quality_filter": "open lecture notes and arXiv-style reviews with stable source anchors",
                "copyright_policy": "store source identity and short orientation summaries only; do not ingest copyrighted books wholesale",
                "claim_support_policy": "retrieval is not evidence; promote exact passages through source_asset/reference/evidence/validation",
            },
        },
        {
            "document_id": "curated_rag_doc:open_ads_holography_orientation",
            "title": "Open AdS and holography orientation shelf",
            "asset_type": "lecture",
            "source_uri": "aitp://curated-rag/open-ads-holography-orientation",
            "version_anchor": {"catalog_version": CATALOG_VERSION, "revision": "v1"},
            "content_hash": "sha256:curated-rag-open-ads-holography-orientation-v1",
            "tags": [
                "ads-cft",
                "holography",
                "bulk-boundary",
                "general-relativity",
                "qft",
                "open-system",
                "orientation",
            ],
            "domain_hints": ["theoretical-physics/gravity", "theoretical-physics/qft"],
            "topic_hints": [
                "ads-bulk-boundary",
                "holographic-methods",
                "boundary-conditions",
                "transport",
            ],
            "language": "en",
            "priority": "high",
            "intended_use": "background_rag",
            "trust_status": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "curation_policy": {
                "quality_filter": "open lecture notes and review-style sources for AdS/CFT and holographic methods",
                "copyright_policy": "store source identity and short orientation summaries only",
                "claim_support_policy": "use retrieved chunks only to choose what to inspect next",
            },
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
        {
            "chunk_id": "curated_rag_chunk:open_theory_lecture_shelf:0001",
            "document_id": "curated_rag_doc:open_theory_lecture_shelf",
            "anchor": {
                "section": "classic-open-lecture-sources",
                "ordinal": 1,
                "source_examples": [
                    "https://www.damtp.cam.ac.uk/user/tong/teaching.html",
                    "https://www.preposterousuniverse.com/grnotes/",
                    "https://www.preskill.caltech.edu/ph229/",
                    "https://arxiv.org/abs/0903.3246",
                ],
            },
            "text": (
                "For new theory topics, prefer open lecture notes and review-style "
                "sources as orientation shelves: Tong for field theory, gauge theory, "
                "statistical physics, solitons and strings; Carroll for graduate GR; "
                "Preskill for quantum information; Hartnoll-style holographic method "
                "notes for AdS/CFT transport intuition. Use these sources to choose "
                "definitions, regimes, and known checks before treating any passage as evidence."
            ),
            "summary": "Use vetted open lecture shelves to orient definitions, regimes, and known checks.",
            "tags": [
                "lecture-orientation",
                "qft",
                "gr",
                "holography",
                "quantum-information",
                "method-selection",
            ],
            "token_estimate": 66,
            "content_hash": "sha256:curated-rag-chunk-open-theory-lecture-shelf-0001",
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "chunk_role": "source_backtrace_suggestion",
        },
        {
            "chunk_id": "curated_rag_chunk:open_theory_lecture_shelf:0002",
            "document_id": "curated_rag_doc:open_theory_lecture_shelf",
            "anchor": {"section": "physics-object-discovery", "ordinal": 2},
            "text": (
                "Before retrieving details, ask which physical objects carry the problem: "
                "dynamical degrees of freedom, background geometry or lattice, control "
                "parameters, boundary/source/sink terms, observables, time scales, "
                "conserved currents, and known limiting regimes. Normal modes, spectra, "
                "and poles are diagnostics unless the user makes them the primary object."
            ),
            "summary": "Train object discovery before details: degrees of freedom, controls, boundaries, observables, scales, limits.",
            "tags": [
                "physics-object-discovery",
                "conceptual-scaffolding",
                "observable-selection",
                "known-limits",
            ],
            "token_estimate": 55,
            "content_hash": "sha256:curated-rag-chunk-open-theory-lecture-shelf-0002",
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "chunk_role": "object_discovery_lens",
            "physics_object_hints": [
                "dynamical_degree_of_freedom",
                "control_parameter",
                "boundary_or_sink",
                "observable",
                "time_scale",
                "known_limit",
            ],
        },
        {
            "chunk_id": "curated_rag_chunk:open_ads_holography_orientation:0001",
            "document_id": "curated_rag_doc:open_ads_holography_orientation",
            "anchor": {
                "section": "ads-boundary-motion",
                "ordinal": 1,
                "source_examples": [
                    "https://arxiv.org/abs/0903.3246",
                    "https://arxiv.org/abs/1612.07324",
                    "https://www.preposterousuniverse.com/grnotes/",
                ],
            },
            "text": (
                "For AdS or holographic boundary questions, separate bulk motion, "
                "boundary conditions, cutoff surfaces, external baths, and CFT/source "
                "interpretation. For massive matter, ask first whether the relevant "
                "description is point-particle/geodesic motion, a field wavepacket, a "
                "kinetic ensemble, or an effective open-system sink, then choose survival, "
                "hitting time, current, or energy flux as primary observables. As an "
                "orientation check, finite-energy classical massive timelike motion in "
                "global AdS should not be assumed to hit the conformal boundary; boundary "
                "loss may instead require a finite cutoff wall, a wavepacket tail or field "
                "boundary condition, or a kinetic distribution with a sink."
            ),
            "summary": "AdS massive-matter boundary problems should separate conformal-boundary reachability from finite cutoff-wall, wavepacket-tail, or kinetic-sink models before choosing survival, hitting time, current, and energy flux observables.",
            "tags": [
                "ads",
                "holography",
                "cutoff-wall",
                "massive-matter",
                "survival",
                "hitting-time",
                "energy-flux",
                "boundary-condition",
                "timelike-geodesic",
                "conformal-boundary",
                "wavepacket-tail",
                "kinetic-sink",
                "model-layer",
            ],
            "token_estimate": 104,
            "content_hash": "sha256:curated-rag-chunk-open-ads-holography-orientation-0001",
            "retrieval_role": "heuristic_context",
            "orientation_only": True,
            "can_update_claim_trust": False,
            "chunk_role": "domain_intuition",
            "physics_object_hints": [
                "massive_matter",
                "cutoff_wall",
                "boundary_condition",
                "bath_channel",
                "conformal_boundary_reachability",
                "timelike_geodesic",
                "field_wavepacket_tail",
                "kinetic_sink",
                "survival_probability",
                "hitting_time",
                "energy_flux",
            ],
        },
    ]
    return chunks
