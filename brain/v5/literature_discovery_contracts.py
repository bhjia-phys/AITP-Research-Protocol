"""Validation helpers for bounded literature discovery process objects."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

from brain.v5.knowledge_connectors import builtin_knowledge_connectors
from brain.v5.literature_discovery_models import (
    LiteratureDiscoveryRequest,
    LiteratureDiscoverySpec,
)
from brain.v5.pinned_record_refs import PinnedRecordRef


FRAMEWORKS = {
    "condensed_matter",
    "general_theory",
    "many_body",
    "qft",
    "quantum_gravity",
}
SOURCE_TYPES = {
    "book",
    "lecture_note",
    "primary_paper",
    "review",
    "web_page",
}


def validate_literature_discovery_spec(spec: LiteratureDiscoverySpec) -> None:
    if not isinstance(spec, LiteratureDiscoverySpec):
        raise TypeError("spec must be LiteratureDiscoverySpec")
    if not isinstance(spec.gap_ref, PinnedRecordRef):
        raise TypeError("gap_ref must be an exact PinnedRecordRef")
    if not isinstance(spec.prior_audit_ref, PinnedRecordRef):
        raise TypeError("prior_audit_ref must be an exact PinnedRecordRef")
    framework = _normalized_token(spec.framework)
    if framework not in FRAMEWORKS:
        raise ValueError(f"framework must be one of: {', '.join(sorted(FRAMEWORKS))}")
    if not isinstance(spec.regime, str) or not spec.regime.strip():
        raise ValueError("regime is required")
    _validate_text_length(spec.regime, "regime", max_length=500)
    _validate_bounded_text_tuple(
        spec.focus_terms,
        "focus_terms",
        max_count=32,
        max_item_length=200,
        allow_empty=True,
    )
    _validate_bounded_text_tuple(
        spec.required_source_types,
        "required_source_types",
        max_count=8,
        max_item_length=50,
    )
    if any(_normalized_token(item) not in SOURCE_TYPES for item in spec.required_source_types):
        raise ValueError("required_source_types contains an unsupported source type")
    _validate_bounded_text_tuple(
        spec.connector_allowlist,
        "connector_allowlist",
        max_count=16,
        max_item_length=100,
    )
    if (
        isinstance(spec.max_results, bool)
        or not isinstance(spec.max_results, int)
        or not 1 <= spec.max_results <= 50
    ):
        raise ValueError("max_results must be between 1 and 50")
    if (
        isinstance(spec.timeout_seconds, bool)
        or not isinstance(spec.timeout_seconds, int)
        or not 1 <= spec.timeout_seconds <= 120
    ):
        raise ValueError("timeout_seconds must be between 1 and 120")
    if isinstance(spec.ttl_seconds, bool) or not isinstance(spec.ttl_seconds, int) or not 60 <= spec.ttl_seconds <= 3600:
        raise ValueError("ttl_seconds must be between 60 and 3600")


def validate_literature_discovery_request(request: LiteratureDiscoveryRequest) -> None:
    if not isinstance(request, LiteratureDiscoveryRequest):
        raise TypeError("request must be LiteratureDiscoveryRequest")
    for field in (
        "request_id",
        "dedup_fingerprint",
        "request_integrity_hash",
        "topic_id",
        "claim_id",
        "normalized_query",
        "framework",
        "regime",
        "created_at",
        "expires_at",
    ):
        if not isinstance(getattr(request, field), str) or not getattr(request, field).strip():
            raise ValueError(f"{field} must be non-empty")
    for field in ("program_id", "focus_set_ref"):
        if not isinstance(getattr(request, field), str):
            raise ValueError(f"{field} must be a string")
    if not isinstance(request.gap_ref, PinnedRecordRef) or not isinstance(
        request.prior_audit_ref, PinnedRecordRef
    ):
        raise ValueError("request must retain exact gap and prior audit pins")
    if request.framework not in FRAMEWORKS:
        raise ValueError("request framework is invalid")
    _validate_text_length(request.normalized_query, "normalized_query", max_length=2000)
    _validate_text_length(request.regime, "regime", max_length=500)
    _validate_bounded_text_tuple(
        request.query_expansions,
        "query_expansions",
        max_count=3,
        max_item_length=2000,
    )
    _validate_bounded_text_tuple(
        request.focus_terms,
        "focus_terms",
        max_count=32,
        max_item_length=200,
        allow_empty=True,
    )
    _validate_bounded_text_tuple(
        request.required_source_types,
        "required_source_types",
        max_count=8,
        max_item_length=50,
    )
    if any(item not in SOURCE_TYPES for item in request.required_source_types):
        raise ValueError("required_source_types contains an unsupported source type")
    _validate_bounded_text_tuple(
        request.connector_allowlist,
        "connector_allowlist",
        max_count=16,
        max_item_length=100,
    )
    known_connectors = builtin_knowledge_connectors()
    if any(item not in known_connectors for item in request.connector_allowlist):
        raise ValueError("connector_allowlist contains an unknown connector")
    if isinstance(request.max_results, bool) or not isinstance(request.max_results, int) or not 1 <= request.max_results <= 50:
        raise ValueError("max_results must be between 1 and 50")
    if (
        isinstance(request.timeout_seconds, bool)
        or not isinstance(request.timeout_seconds, int)
        or not 1 <= request.timeout_seconds <= 120
    ):
        raise ValueError("timeout_seconds must be between 1 and 120")
    if (
        isinstance(request.ttl_seconds, bool)
        or not isinstance(request.ttl_seconds, int)
        or not 60 <= request.ttl_seconds <= 3600
    ):
        raise ValueError("ttl_seconds must be between 60 and 3600")
    created_at = parse_timestamp(request.created_at)
    expires_at = parse_timestamp(request.expires_at)
    lifetime = (expires_at - created_at).total_seconds()
    if not 60 <= lifetime <= 3600:
        raise ValueError("request lifetime must be between 60 and 3600 seconds")
    if lifetime != request.ttl_seconds:
        raise ValueError("request timestamps must match ttl_seconds")
    expected_fingerprint = literature_discovery_fingerprint(
        gap_ref=request.gap_ref,
        prior_audit_ref=request.prior_audit_ref,
        topic_id=request.topic_id,
        claim_id=request.claim_id,
        program_id=request.program_id,
        focus_set_ref=request.focus_set_ref,
        normalized_query=request.normalized_query,
        query_expansions=request.query_expansions,
        framework=request.framework,
        regime=request.regime,
        focus_terms=request.focus_terms,
        required_source_types=request.required_source_types,
        connector_allowlist=request.connector_allowlist,
        max_results=request.max_results,
        timeout_seconds=request.timeout_seconds,
        ttl_seconds=request.ttl_seconds,
    )
    if request.dedup_fingerprint != expected_fingerprint:
        raise ValueError("request fingerprint does not match its bound fields")
    if request.request_id != f"literature-discovery-request:{expected_fingerprint}":
        raise ValueError("request_id does not match request fingerprint")
    expected_integrity = literature_discovery_request_integrity(
        dedup_fingerprint=request.dedup_fingerprint,
        created_at=request.created_at,
        expires_at=request.expires_at,
    )
    if request.request_integrity_hash != expected_integrity:
        raise ValueError("request integrity hash does not match its timestamps")
    if created_at > datetime.now(UTC) + timedelta(seconds=5):
        raise ValueError("request created_at cannot be in the future")
    if (
        request.summary_inputs_trusted
        or not request.orientation_only
        or request.can_update_kernel_state
        or request.can_update_claim_trust
        or request.can_create_source_asset
    ):
        raise ValueError("literature discovery request violates trust boundary")


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def normalized_token(value: str) -> str:
    return _normalized_token(value)


def literature_discovery_fingerprint(
    *,
    gap_ref,
    prior_audit_ref,
    topic_id,
    claim_id,
    program_id,
    focus_set_ref,
    normalized_query,
    query_expansions,
    framework,
    regime,
    focus_terms,
    required_source_types,
    connector_allowlist,
    max_results,
    timeout_seconds,
    ttl_seconds,
) -> str:
    basis = {
        "gap_ref": asdict(gap_ref),
        "prior_audit_ref": asdict(prior_audit_ref),
        "topic_id": topic_id,
        "claim_id": claim_id,
        "program_id": program_id,
        "focus_set_ref": focus_set_ref,
        "normalized_query": str(normalized_query).casefold(),
        "query_expansions": tuple(query_expansions),
        "framework": framework,
        "regime": str(regime).casefold(),
        "focus_terms": tuple(focus_terms),
        "required_source_types": tuple(required_source_types),
        "connector_allowlist": tuple(connector_allowlist),
        "max_results": max_results,
        "timeout_seconds": timeout_seconds,
        "ttl_seconds": ttl_seconds,
    }
    payload = json.dumps(basis, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def literature_discovery_request_integrity(*, dedup_fingerprint, created_at, expires_at):
    payload = json.dumps(
        {
            "dedup_fingerprint": dedup_fingerprint,
            "created_at": created_at,
            "expires_at": expires_at,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_token(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _validate_text_length(value: str, field: str, *, max_length: int) -> None:
    if len(value) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")


def _validate_bounded_text_tuple(
    values,
    field: str,
    *,
    max_count: int,
    max_item_length: int,
    allow_empty: bool = False,
) -> None:
    if not isinstance(values, tuple):
        raise ValueError(f"{field} must be a tuple of non-empty strings")
    if len(values) > max_count:
        raise ValueError(f"{field} must contain at most {max_count} items")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{field} must be a tuple of non-empty strings")
    if any(len(item) > max_item_length for item in values):
        raise ValueError(f"{field} items must be at most {max_item_length} characters")
    normalized = [_normalized_token(item) for item in values]
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field} must not contain duplicates")
    if not values and not allow_empty:
        raise ValueError(f"{field} must be non-empty")
