"""JSON coercion and dispatch for full-only M3 knowledge operations."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from brain.v5.knowledge_candidates import (
    KnowledgeCandidate,
    diagnose_knowledge_candidate,
    route_knowledge_candidate,
)
from brain.v5.knowledge_context import compile_knowledge_context
from brain.v5.knowledge_context_contracts import KnowledgeContextRequest
from brain.v5.knowledge_query import retrieve_knowledge
from brain.v5.knowledge_retrieval import KnowledgeQuery
from brain.v5.knowledge_review import (
    knowledge_candidate_hash,
    record_knowledge_review_decision,
    supersede_knowledge_review_decision,
)
from brain.v5.knowledge_promotion import promote_knowledge_candidate
from brain.v5.knowledge_surface_contracts import (
    knowledge_operation_specs,
    require_valid_knowledge_operation_result,
)
from brain.v5.literature_discovery import (
    build_literature_discovery_request,
    normalize_literature_discovery_result,
)
from brain.v5.literature_discovery_models import (
    LiteratureDiscoveryRequest,
    LiteratureDiscoverySpec,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef
from brain.v5.record_envelope import RecordActor
from brain.v5.source_shelf import build_source_shelf, load_source_shelf
from brain.v5.source_shelf_models import SourceShelfBuildRequest


_ACTOR = RecordActor(actor_type="tool", actor_id="knowledge-facade", host="aitp-v5")


def decode_knowledge_payload(payload_json: str) -> dict[str, Any]:
    try:
        payload = json.loads(payload_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("knowledge facade payload_json must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("knowledge facade payload must be a JSON object")
    return payload


def invoke_knowledge_operation(
    ws: WorkspacePaths,
    operation: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if operation not in knowledge_operation_specs():
        raise ValueError(f"unsupported knowledge operation: {operation}")
    candidate = None
    if operation in {
        "knowledge_diagnose_candidate",
        "knowledge_record_review",
        "knowledge_promote_candidate",
    }:
        candidate = _candidate(payload.get("candidate"))
    if operation == "knowledge_diagnose_candidate":
        diagnostics = diagnose_knowledge_candidate(ws, candidate)
        route = route_knowledge_candidate(candidate)
        value = {
            **asdict(diagnostics),
            "candidate_hash": knowledge_candidate_hash(candidate),
            "target_lanes": list(route.target_lanes),
            "eligible_for_skill": route.eligible_for_skill,
            "grounding_pins": [asdict(pin) for pin in candidate.grounding_pins],
        }
    elif operation == "knowledge_record_review":
        checkpoint_ref = _pin(payload.get("checkpoint_ref"), "checkpoint_ref")
        prior = payload.get("prior_decision_ref")
        writer = (
            supersede_knowledge_review_decision
            if prior
            else record_knowledge_review_decision
        )
        kwargs = {
            "checkpoint_ref": checkpoint_ref,
            "decision": str(payload.get("decision") or ""),
            "actor": _ACTOR,
        }
        if prior:
            kwargs["prior_decision_ref"] = _pin(prior, "prior_decision_ref")
        written = writer(ws, candidate, **kwargs)
        value = _candidate_write_result(
            candidate,
            written,
            checkpoint_ref=asdict(checkpoint_ref),
        )
    elif operation == "knowledge_promote_candidate":
        decision_ref = _pin(payload.get("decision_ref"), "decision_ref")
        written = promote_knowledge_candidate(
            ws,
            candidate,
            decision_ref=decision_ref,
            actor=_ACTOR,
        )
        value = _candidate_write_result(
            candidate,
            written,
            decision_ref=asdict(decision_ref),
        )
    elif operation == "knowledge_build_source_shelf":
        value = build_source_shelf(ws, _source_shelf_request(payload.get("request")))
    elif operation == "knowledge_get_source_shelf":
        value = load_source_shelf(ws, str(payload.get("generation") or ""))
    elif operation == "knowledge_build_discovery_request":
        value = build_literature_discovery_request(
            ws,
            _discovery_spec(payload.get("spec")),
        )
    elif operation == "knowledge_normalize_discovery_result":
        value = normalize_literature_discovery_result(
            _discovery_request(payload.get("request")),
            _mapping(payload.get("connector_result"), "connector_result"),
        )
    elif operation == "knowledge_query":
        freshness_mode = str(payload.get("verification_mode") or "orientation")
        if freshness_mode not in {"orientation", "strong"}:
            raise ValueError("knowledge query verification_mode is unsupported")
        value = retrieve_knowledge(
            ws,
            _knowledge_query(payload.get("query")),
            source_shelf_generation=str(payload.get("source_shelf_generation") or ""),
            source_shelf_topic_id=str(payload.get("source_shelf_topic_id") or ""),
            freshness_mode=freshness_mode,
        )
    elif operation == "knowledge_compile_context":
        value = compile_knowledge_context(
            ws,
            _context_request(payload.get("request")),
        )
    else:  # pragma: no cover - registry and dispatch are audited together.
        raise ValueError(f"unsupported knowledge operation: {operation}")
    return _knowledge_result(operation, value)


def _candidate_write_result(candidate, written, **binding) -> dict[str, Any]:
    return {
        "candidate_id": candidate.candidate_id,
        "candidate_hash": knowledge_candidate_hash(candidate),
        "candidate_lane": route_knowledge_candidate(candidate).lane,
        "pinned_ref": {
            "record_ref": written.record_ref,
            "content_hash": written.content_hash,
            "revision": written.revision,
        },
        "write_status": written.status,
        "can_update_claim_trust": False,
        **binding,
    }


def _knowledge_result(operation: str, value: Any) -> dict[str, Any]:
    spec = knowledge_operation_specs()[operation]
    kernel_write = spec.state_effect == "kernel_write"
    runtime_write = spec.state_effect == "runtime_write"
    payload = {
        "ok": True,
        "kind": "knowledge_operation_result",
        "operation": operation,
        "state_effect": spec.state_effect,
        "writes_records": kernel_write,
        "writes_derived_state": runtime_write,
        "result": _jsonable(value),
        "truth_source": spec.truth_source,
        "authorization_guard": spec.authorization_guard,
        "summary_inputs_trusted": False,
        "orientation_only": not kernel_write,
        "can_update_kernel_state": kernel_write,
        "can_update_claim_trust": False,
        "can_write_evidence": False,
    }
    return require_valid_knowledge_operation_result(payload)


def _candidate(value: Any) -> KnowledgeCandidate:
    data = _mapping(value, "candidate")
    return KnowledgeCandidate(
        candidate_id=str(data.get("candidate_id") or ""),
        content_kinds=_strings(data.get("content_kinds"), "content_kinds"),
        statement=str(data.get("statement") or ""),
        topic_id=str(data.get("topic_id") or ""),
        subject_ref=str(data.get("subject_ref") or ""),
        source_refs=_strings(data.get("source_refs", []), "source_refs"),
        grounding_pins=_pins(data.get("grounding_pins", []), "grounding_pins"),
        framework=str(data.get("framework") or ""),
        regime=str(data.get("regime") or ""),
        conventions=_strings(data.get("conventions", []), "conventions"),
        procedural_steps=_strings(data.get("procedural_steps", []), "procedural_steps"),
        validation_refs=_strings(data.get("validation_refs", []), "validation_refs"),
        applicability_boundary=str(data.get("applicability_boundary") or ""),
    )


def _source_shelf_request(value: Any) -> SourceShelfBuildRequest:
    data = _mapping(value, "request")
    return SourceShelfBuildRequest(
        topic_id=str(data.get("topic_id") or ""),
        source_asset_refs=_strings(data.get("source_asset_refs", []), "source_asset_refs"),
        curation_rationale=str(data.get("curation_rationale") or ""),
        max_passage_chars=data.get("max_passage_chars", 4000),
    )


def _discovery_spec(value: Any) -> LiteratureDiscoverySpec:
    data = _mapping(value, "spec")
    return LiteratureDiscoverySpec(
        gap_ref=_pin(data.get("gap_ref"), "gap_ref"),
        prior_audit_ref=_pin(data.get("prior_audit_ref"), "prior_audit_ref"),
        framework=str(data.get("framework") or ""),
        regime=str(data.get("regime") or ""),
        required_source_types=_strings(
            data.get("required_source_types", []), "required_source_types"
        ),
        connector_allowlist=_strings(
            data.get("connector_allowlist", []), "connector_allowlist"
        ),
        focus_terms=_strings(data.get("focus_terms", []), "focus_terms"),
        max_results=data.get("max_results", 20),
        timeout_seconds=data.get("timeout_seconds", 30),
        ttl_seconds=data.get("ttl_seconds", 900),
    )


def _discovery_request(value: Any) -> LiteratureDiscoveryRequest:
    data = _mapping(value, "request")
    trust_boundary = {
        "summary_inputs_trusted": False,
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
        "can_create_source_asset": False,
    }
    if any(
        field in data and data[field] is not expected
        for field, expected in trust_boundary.items()
    ):
        raise ValueError("literature discovery request violates its trust boundary")
    return LiteratureDiscoveryRequest(
        request_id=str(data.get("request_id") or ""),
        dedup_fingerprint=str(data.get("dedup_fingerprint") or ""),
        request_integrity_hash=str(data.get("request_integrity_hash") or ""),
        gap_ref=_pin(data.get("gap_ref"), "gap_ref"),
        prior_audit_ref=_pin(data.get("prior_audit_ref"), "prior_audit_ref"),
        topic_id=str(data.get("topic_id") or ""),
        claim_id=str(data.get("claim_id") or ""),
        program_id=str(data.get("program_id") or ""),
        focus_set_ref=str(data.get("focus_set_ref") or ""),
        normalized_query=str(data.get("normalized_query") or ""),
        query_expansions=_strings(data.get("query_expansions", []), "query_expansions"),
        framework=str(data.get("framework") or ""),
        regime=str(data.get("regime") or ""),
        focus_terms=_strings(data.get("focus_terms", []), "focus_terms"),
        required_source_types=_strings(
            data.get("required_source_types", []), "required_source_types"
        ),
        connector_allowlist=_strings(
            data.get("connector_allowlist", []), "connector_allowlist"
        ),
        max_results=data.get("max_results"),
        timeout_seconds=data.get("timeout_seconds"),
        ttl_seconds=data.get("ttl_seconds"),
        created_at=str(data.get("created_at") or ""),
        expires_at=str(data.get("expires_at") or ""),
    )


def _knowledge_query(value: Any) -> KnowledgeQuery:
    data = _mapping(value, "query")
    dummy_symbols = data.get("formula_dummy_symbols", [])
    if not isinstance(dummy_symbols, list):
        raise ValueError("formula_dummy_symbols must be a list")
    return KnowledgeQuery(
        text=str(data.get("text") or ""),
        topic_id=str(data.get("topic_id") or ""),
        framework=str(data.get("framework") or ""),
        regime=str(data.get("regime") or ""),
        conventions=_strings(data.get("conventions", []), "conventions"),
        formula=str(data.get("formula") or ""),
        formula_dummy_symbols=tuple(tuple(item) for item in dummy_symbols),
        formula_commutative_product_safe=data.get(
            "formula_commutative_product_safe", False
        ),
        intent=str(data.get("intent") or "default"),
        program_id=str(data.get("program_id") or ""),
        seed_refs=_strings(data.get("seed_refs", []), "seed_refs"),
        include_discovery=data.get("include_discovery", False),
        revalidation_decision_refs=_pins(
            data.get("revalidation_decision_refs", []),
            "revalidation_decision_refs",
        ),
        max_results=data.get("max_results", 8),
        page_offset=data.get("page_offset", 0),
        graph_depth=data.get("graph_depth", 2),
        deterministic=data.get("deterministic", True),
    )


def _context_request(value: Any) -> KnowledgeContextRequest:
    data = _mapping(value, "request")
    return KnowledgeContextRequest(
        query_text=str(data.get("query_text") or ""),
        topic_id=str(data.get("topic_id") or ""),
        framework=str(data.get("framework") or ""),
        regime=str(data.get("regime") or ""),
        conventions=_strings(data.get("conventions", []), "conventions"),
        formula=str(data.get("formula") or ""),
        intent=str(data.get("intent") or "default"),
        mode=str(data.get("mode") or "normal"),
        program_id=str(data.get("program_id") or ""),
        seed_refs=_strings(data.get("seed_refs", []), "seed_refs"),
        include_discovery=data.get("include_discovery", False),
        revalidation_decision_refs=_pins(
            data.get("revalidation_decision_refs", []),
            "revalidation_decision_refs",
        ),
        source_shelf_generation=str(data.get("source_shelf_generation") or ""),
        source_shelf_topic_id=str(data.get("source_shelf_topic_id") or ""),
        exact_refs=_strings(data.get("exact_refs", []), "exact_refs"),
        page_offset=data.get("page_offset", 0),
        max_results=data.get("max_results", 0),
        max_tokens=data.get("max_tokens", 0),
        max_bytes=data.get("max_bytes", 0),
    )


def _pin(value: Any, field_name: str) -> PinnedRecordRef:
    data = _mapping(value, field_name)
    return PinnedRecordRef(
        record_ref=str(data.get("record_ref") or ""),
        content_hash=str(data.get("content_hash") or ""),
        revision=data.get("revision"),
    )


def _pins(value: Any, field_name: str) -> tuple[PinnedRecordRef, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(_pin(item, field_name) for item in value)


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return dict(value)


def _strings(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    return tuple(value)


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [_jsonable(item) for item in value]
    if isinstance(value, bytes):
        raise TypeError("knowledge facade does not inline source bytes")
    return value


__all__ = ["decode_knowledge_payload", "invoke_knowledge_operation"]
