"""Read-only corpus-backed literature extraction artifact drafts."""

from __future__ import annotations

from typing import Any

from brain.v5.curated_rag_corpus import read_curated_rag_chunk
from brain.v5.models import ReferenceLocationRecord
from brain.v5.record_refs import lookup_record_refs
from brain.v5.store import list_valid_records
from brain.v5.workspace import get_session_binding


_FORBIDDEN_USES = [
    "curated_rag_chunk_as_evidence",
    "corpus_backed_artifact_as_evidence",
    "paper_summary_as_evidence",
    "source_support_result",
    "validation_result",
    "write_execution",
    "final_gate_satisfaction",
    "claim_trust_update",
    "trust_apply",
]


def build_literature_corpus_extraction_artifact(
    ws,
    *,
    session_id: str,
    chunk_ids: list[str],
    reference_location_ids: list[str],
    report_profile: str = "paper_learning",
    focus_terms: list[str] | None = None,
    optional_claim_id: str = "",
    artifact_intent: str = "corpus_backed_extraction_report",
) -> dict[str, Any]:
    """Draft a no-trust artifact connecting curated RAG chunks to exact anchors."""

    session = get_session_binding(ws, session_id)
    claim_id = optional_claim_id or session.active_claim
    normalized_chunks = _nonempty_unique(chunk_ids)
    normalized_location_ids = _nonempty_unique(reference_location_ids)
    if not normalized_chunks:
        raise ValueError("chunk_ids is required")
    if not normalized_location_ids:
        raise ValueError("reference_location_ids is required")
    normalized_focus_terms = _nonempty_unique(focus_terms or [])
    chunks = [read_curated_rag_chunk(chunk_id, base=ws) for chunk_id in normalized_chunks]
    reference_items = _reference_location_items(ws, normalized_location_ids)
    alignment_items = [
        _alignment_item(chunk, reference_items)
        for chunk in chunks
    ]
    exact_anchor_count = sum(1 for item in reference_items if item["status"] == "found")
    return {
        "ok": True,
        "kind": "literature_corpus_extraction_artifact",
        "session_id": session_id,
        "topic_id": session.topic_id,
        "claim_id": claim_id,
        "artifact_intent": artifact_intent,
        "report_profile": report_profile,
        "chunk_ids": normalized_chunks,
        "chunk_count": len(normalized_chunks),
        "reference_location_ids": normalized_location_ids,
        "reference_location_count": len(normalized_location_ids),
        "found_reference_location_count": exact_anchor_count,
        "missing_reference_location_count": len(reference_items) - exact_anchor_count,
        "focus_terms": normalized_focus_terms,
        "focus_term_count": len(normalized_focus_terms),
        "chunk_items": [_chunk_item(chunk) for chunk in chunks],
        "chunk_item_count": len(chunks),
        "reference_location_items": reference_items,
        "reference_location_item_count": len(reference_items),
        "alignment_items": alignment_items,
        "alignment_item_count": len(alignment_items),
        "record_ref_lookup": lookup_record_refs(
            ws,
            [f"reference_location:{_location_id(item)}" for item in normalized_location_ids],
        ),
        "artifact_draft": {
            "kind": "corpus_backed_extraction_report_artifact",
            "status": "draft_only",
            "artifact_role": "literature_extraction_orientation",
            "artifact_record_created_now": False,
            "creates_record_now": False,
            "records_validation_result": False,
            "source_support_result": False,
            "claim_trust_mutation": "none",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "required_inputs": [
                "curated_rag_chunk_manifest",
                "reference_location_record",
                "human_or_agent_review_before_write",
            ],
            "sections": _artifact_sections(),
        },
        "downstream_extraction_report_call": {
            "entrypoint": "build_literature_extraction_report",
            "mcp": "aitp_v5_build_literature_extraction_report",
            "cli": "aitp-v5 literature extraction-report <args>",
            "surface": "literature_extraction_report",
            "session_id": session_id,
            "source_refs": [f"reference_location:{_location_id(item)}" for item in normalized_location_ids],
            "report_profile": report_profile,
            "focus_terms": normalized_focus_terms,
            "requires_explicit_next_action": True,
            "records_validation_result": False,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        },
        "recommended_next_entrypoints": _recommended_next_entrypoints(reference_items),
        "artifact_policy": {
            "source": "curated_rag_chunk_manifest_and_typed_reference_locations",
            "host_may_use_for": [
                "corpus_backed_extraction_artifact_draft",
                "chunk_to_exact_anchor_alignment",
                "literature_extraction_report_input_planning",
                "missing_reference_location_triage",
            ],
            "requires_curated_rag_chunks": True,
            "requires_exact_reference_locations": True,
            "requires_explicit_next_entrypoint": True,
            "retrieval_role": "heuristic_context",
            "retrieval_requires_promotion_for_claim_support": True,
            "allowed_next_entrypoints": [
                "record_reference_location",
                "build_literature_extraction_report",
                "build_literature_source_set_readiness",
                "record_physics_object",
                "record_object_relation",
                "create_proof_obligation",
                "record_sensemaking_report",
                "preflight_trust_update",
            ],
            "forbidden_uses": list(_FORBIDDEN_USES),
        },
        "read_surface_effect": "literature_corpus_extraction_artifact_only",
        "read_only": True,
        "draft_creates_records": False,
        "requires_explicit_next_action": True,
        "bridge_called": False,
        "executes_write_now": False,
        "mutates_next_payload_now": False,
        "infers_payload_values": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "records_validation_result": False,
        "source_support_result": False,
        "evidence_created": False,
        "validation_created": False,
        "artifact_record_created": False,
        "write_executed": False,
        "trust_update_forbidden": True,
        "claim_trust_mutation": "none",
        "truth_source": "curated_rag_chunk_manifest_and_typed_reference_locations",
    }


def _reference_location_items(ws, location_ids: list[str]) -> list[dict[str, Any]]:
    records = {
        record.location_id: record
        for record in list_valid_records(ws.registry_dir("reference_locations"), ReferenceLocationRecord)
    }
    return [
        _reference_location_item(records.get(_location_id(location_ref)), original_ref=location_ref)
        for location_ref in location_ids
    ]


def _reference_location_item(
    record: ReferenceLocationRecord | None,
    *,
    original_ref: str,
) -> dict[str, Any]:
    if record is None:
        location_id = _location_id(original_ref)
        return {
            "input_ref": original_ref,
            "record_ref": f"reference_location:{location_id}",
            "location_id": location_id,
            "status": "missing",
            "topic_id": "",
            "claim_id": "",
            "connector_id": "",
            "location_type": "",
            "uri": "",
            "label": "",
            "source_ref": "",
            "external_id": "",
            "summary": "",
            "metadata": {},
            "exact_anchor_available": False,
            "recommended_next_entrypoint": "record_reference_location",
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "source_support_result": False,
            "claim_trust_mutation": "none",
        }
    return {
        "input_ref": original_ref,
        "record_ref": f"reference_location:{record.location_id}",
        "location_id": record.location_id,
        "status": "found",
        "topic_id": record.topic_id,
        "claim_id": record.claim_id,
        "connector_id": record.connector_id,
        "location_type": record.location_type,
        "uri": record.uri,
        "label": record.label,
        "source_ref": record.source_ref,
        "external_id": record.external_id,
        "summary": record.summary,
        "metadata": dict(record.metadata),
        "exact_anchor_available": True,
        "recommended_next_entrypoint": "",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _chunk_item(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"],
        "corpus_id": chunk["corpus_id"],
        "index_mode": chunk["index_mode"],
        "index_status": chunk["index_status"],
        "retrieval_role": "heuristic_context",
        "document_title": chunk["document"]["title"],
        "document_source_uri": chunk["document"]["source_uri"],
        "document_content_hash": chunk["document"]["content_hash"],
        "chunk_anchor": chunk["chunk"]["anchor"],
        "chunk_summary": chunk["chunk"]["summary"],
        "chunk_tags": chunk["chunk"]["tags"],
        "chunk_content_hash": chunk["chunk"]["content_hash"],
        "promotion_required_before_claim_support": True,
        "records_validation_result": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "claim_trust_mutation": "none",
    }


def _alignment_item(chunk: dict[str, Any], reference_items: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        _alignment_candidate(chunk, reference)
        for reference in reference_items
    ]
    direct = [candidate for candidate in candidates if candidate["alignment_basis"] != "agent_supplied_candidate"]
    exact = [candidate for candidate in candidates if candidate["exact_anchor_available"]]
    return {
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"],
        "candidate_reference_locations": candidates,
        "candidate_reference_location_count": len(candidates),
        "direct_alignment_count": len(direct),
        "alignment_status": "has_typed_anchor_candidate" if exact else "missing_reference_location",
        "requires_human_or_agent_review": True,
        "retrieval_role": "heuristic_context",
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "source_support_result": False,
        "records_validation_result": False,
        "claim_trust_mutation": "none",
    }


def _alignment_candidate(chunk: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    basis = _alignment_basis(chunk, reference)
    return {
        "reference_location_ref": reference["record_ref"],
        "reference_location_status": reference["status"],
        "alignment_basis": basis,
        "alignment_status": "candidate_alignment_requires_review",
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"],
        "reference_uri": reference["uri"],
        "reference_source_ref": reference["source_ref"],
        "reference_external_id": reference["external_id"],
        "exact_anchor_available": reference["exact_anchor_available"],
        "retrieval_is_claim_support": False,
        "records_validation_result": False,
        "source_support_result": False,
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "claim_trust_mutation": "none",
    }


def _alignment_basis(chunk: dict[str, Any], reference: dict[str, Any]) -> str:
    metadata = reference.get("metadata") if isinstance(reference.get("metadata"), dict) else {}
    if reference.get("status") != "found":
        return "missing_reference_location"
    if reference.get("source_ref") == chunk["chunk_id"]:
        return "reference_source_ref_matches_chunk"
    if metadata.get("curated_rag_chunk_id") == chunk["chunk_id"]:
        return "reference_metadata_matches_chunk"
    if reference.get("external_id") == chunk["document_id"]:
        return "reference_external_id_matches_document"
    if metadata.get("curated_rag_document_id") == chunk["document_id"]:
        return "reference_metadata_matches_document"
    if reference.get("uri") == chunk["document"]["source_uri"]:
        return "reference_uri_matches_document_source"
    return "agent_supplied_candidate"


def _artifact_sections() -> list[dict[str, Any]]:
    sections = [
        ("curated_chunk_table", "List curated RAG chunk identities and heuristic summaries."),
        ("exact_reference_anchor_table", "List exact reference locations selected for source inspection."),
        ("chunk_to_anchor_alignment", "Connect each heuristic chunk to typed exact anchors for review."),
        ("typed_extraction_report_inputs", "Prepare downstream literature_extraction_report source_refs."),
        ("promotion_boundary", "State that chunks and artifact drafts are not evidence or trust updates."),
    ]
    return [
        {
            "section_id": section_id,
            "purpose": purpose,
            "creates_record_now": False,
            "records_validation_result": False,
            "source_support_result": False,
            "summary_inputs_trusted": False,
            "orientation_only": True,
            "claim_trust_mutation": "none",
        }
        for section_id, purpose in sections
    ]


def _recommended_next_entrypoints(reference_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    entries = []
    if any(item["status"] != "found" for item in reference_items):
        entries.append(
            {
                "entrypoint": "record_reference_location",
                "surface": "reference_location_record",
                "reason": "record exact source anchors before using corpus chunks for extraction work",
            }
        )
    entries.extend(
        [
            {
                "entrypoint": "build_literature_extraction_report",
                "surface": "literature_extraction_report",
                "reason": "summarize existing typed extraction records after exact anchors exist",
            },
            {
                "entrypoint": "record_physics_object",
                "surface": "physics_object_record",
                "reason": "write source-backed definitions, notation, or conventions after reviewing anchors",
            },
            {
                "entrypoint": "record_sensemaking_report",
                "surface": "sensemaking_report_record",
                "reason": "store corpus-backed extraction orientation without claim support",
            },
            {
                "entrypoint": "preflight_trust_update",
                "surface": "trust_update_preflight",
                "reason": "trust changes require evidence, validation, and explicit preflight",
            },
        ]
    )
    return entries


def _location_id(value: str) -> str:
    normalized = str(value).strip()
    if normalized.startswith("reference_location:"):
        return normalized.split(":", 1)[1]
    if normalized.startswith("aitp:reference_location:"):
        return normalized.split(":", 2)[2]
    return normalized


def _nonempty_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result
