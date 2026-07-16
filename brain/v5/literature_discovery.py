"""Build bounded literature discovery handoffs from persisted research gaps."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from brain.v5.knowledge_connectors import builtin_knowledge_connectors
from brain.v5.lifecycle_models import RecallAuditRecord
from brain.v5.literature_discovery_contracts import (
    literature_discovery_fingerprint,
    literature_discovery_request_integrity,
    normalized_token,
    validate_literature_discovery_request,
    validate_literature_discovery_spec,
)
from brain.v5.literature_discovery_models import (
    LiteratureDiscoveryRequest,
    LiteratureDiscoverySpec,
)
from brain.v5.literature_discovery_normalization import normalize_literature_discovery_result
from brain.v5.models import ProofObligationRecord
from brain.v5.pinned_record_refs import get_record_version, pin_current_record
from brain.v5.query_index import current_family_content_watermark
from brain.v5.workspace import get_claim


_GAP_TERMS = (
    "definition",
    "knowledge",
    "literature",
    "paper",
    "reference",
    "review",
    "source",
)
_DISCOVERY_RECALL_FAMILIES = frozenset(
    {"claims", "proof_obligations", "reference_locations", "source_assets"}
)
_FRAMEWORK_HINTS = {
    "quantum_gravity": (
        "ads",
        "black hole",
        "holograph",
        "quantum gravity",
        "replica wormhole",
        "wormhole",
    ),
    "qft": ("field theory", "gauge theory", "qft", "renormal"),
    "condensed_matter": ("band", "condensed", "lattice", "topological order"),
    "many_body": ("many body", "many-body", "dmft", "green function"),
}


def build_literature_discovery_request(
    ws,
    spec: LiteratureDiscoverySpec,
) -> LiteratureDiscoveryRequest:
    """Create a process-only request after exact gap and recall validation."""

    validate_literature_discovery_spec(spec)
    gap = _exact_current_record(ws, spec.gap_ref, ProofObligationRecord, "gap_ref")
    audit = _exact_current_record(ws, spec.prior_audit_ref, RecallAuditRecord, "prior_audit_ref")
    _validate_gap_and_audit(ws, gap, audit)
    framework = normalized_token(spec.framework)
    regime = _clean_text(spec.regime)
    focus_terms = _clean_unique(spec.focus_terms)
    source_types = tuple(normalized_token(item) for item in spec.required_source_types)
    connectors = _connector_allowlist(spec.connector_allowlist)
    claim = get_claim(ws, gap.claim_id)
    corpus = " ".join(
        (
            gap.topic_id,
            gap.statement,
            gap.obligation_type,
            gap.next_action,
            " ".join(gap.required_evidence),
            audit.query_text,
            audit.normalized_intent,
            claim.statement,
            claim.scope,
            claim.active_uncertainty,
        )
    ).lower()
    _require_compatible_framework(framework, corpus)
    query = _normalized_query(
        gap,
        audit,
        framework=framework,
        regime=regime,
        focus_terms=focus_terms,
        source_types=source_types,
    )
    expansions = _query_expansions(
        query,
        framework=framework,
        regime=regime,
        focus_terms=focus_terms,
        source_types=source_types,
    )
    fingerprint = literature_discovery_fingerprint(
        gap_ref=spec.gap_ref,
        prior_audit_ref=spec.prior_audit_ref,
        topic_id=gap.topic_id,
        claim_id=gap.claim_id,
        program_id=audit.program_id,
        focus_set_ref=audit.focus_set_ref,
        normalized_query=query,
        query_expansions=expansions,
        framework=framework,
        regime=regime,
        focus_terms=focus_terms,
        required_source_types=source_types,
        connector_allowlist=connectors,
        max_results=spec.max_results,
        timeout_seconds=spec.timeout_seconds,
        ttl_seconds=spec.ttl_seconds,
    )
    now = datetime.now(UTC)
    created_at = now.isoformat()
    expires_at = (now + timedelta(seconds=spec.ttl_seconds)).isoformat()
    request = LiteratureDiscoveryRequest(
        request_id=f"literature-discovery-request:{fingerprint}",
        dedup_fingerprint=fingerprint,
        request_integrity_hash=literature_discovery_request_integrity(
            dedup_fingerprint=fingerprint,
            created_at=created_at,
            expires_at=expires_at,
        ),
        gap_ref=spec.gap_ref,
        prior_audit_ref=spec.prior_audit_ref,
        topic_id=gap.topic_id,
        claim_id=gap.claim_id,
        program_id=audit.program_id,
        focus_set_ref=audit.focus_set_ref,
        normalized_query=query,
        query_expansions=expansions,
        framework=framework,
        regime=regime,
        focus_terms=focus_terms,
        required_source_types=source_types,
        connector_allowlist=connectors,
        max_results=spec.max_results,
        timeout_seconds=spec.timeout_seconds,
        ttl_seconds=spec.ttl_seconds,
        created_at=created_at,
        expires_at=expires_at,
    )
    validate_literature_discovery_request(request)
    return request


def _exact_current_record(ws, pin, expected_type, field):
    try:
        current = pin_current_record(ws, pin.record_ref)
        version = get_record_version(ws, pin)
    except Exception as exc:  # noqa: BLE001 - stale discovery prerequisites fail closed.
        raise ValueError(f"{field} must be an exact current pin") from exc
    if current != pin:
        raise ValueError(f"{field} must be an exact current pin")
    if not isinstance(version.record, expected_type):
        raise ValueError(f"{field} must resolve to {expected_type.__name__}")
    return version.record


def _validate_gap_and_audit(ws, gap, audit):
    if gap.topic_id != audit.topic_id:
        raise ValueError("gap and prior audit must belong to the same topic")
    if str(gap.status).strip().lower() in {"closed", "complete", "resolved", "satisfied"}:
        raise ValueError("persisted gap is no longer open")
    gap_text = " ".join(
        [gap.statement, gap.obligation_type, gap.next_action, *gap.required_evidence]
    ).lower()
    if not any(term in gap_text for term in _GAP_TERMS):
        raise ValueError("persisted gap does not justify literature discovery")
    missing_families = sorted(
        _DISCOVERY_RECALL_FAMILIES.difference(audit.required_families)
    )
    if missing_families:
        raise ValueError(
            "prior recall audit is missing required families: "
            + ", ".join(missing_families)
        )
    if (
        audit.unchecked_families
        or audit.missing_exact_refs
        or audit.read_errors
        or audit.truncated
        or audit.stale
        or not audit.content_verified
        or not audit.exhaustive
    ):
        raise ValueError("prior recall audit is not complete enough for discovery")
    for family in audit.required_families:
        expected = audit.family_content_watermarks.get(family, "")
        if not expected or current_family_content_watermark(ws, family) != expected:
            raise ValueError(f"prior recall audit is stale for required family {family}")


def _connector_allowlist(values):
    connectors = builtin_knowledge_connectors()
    normalized = _clean_unique(values)
    unknown = [connector for connector in normalized if connector not in connectors]
    if unknown:
        raise ValueError("unknown connector in connector_allowlist: " + ", ".join(unknown))
    return tuple(sorted(normalized))


def _require_compatible_framework(framework, corpus):
    detected = {
        candidate
        for candidate, hints in _FRAMEWORK_HINTS.items()
        if any(hint in corpus for hint in hints)
    }
    if framework != "general_theory" and detected and framework not in detected:
        raise ValueError(
            f"framework {framework} is incompatible with the persisted gap ({', '.join(sorted(detected))})"
        )


def _normalized_query(gap, audit, *, framework, regime, focus_terms, source_types):
    framework_text = framework.replace("_", " ")
    parts = [
        gap.statement,
        audit.query_text,
        f"Framework: {framework_text}.",
        f"Regime: {regime}.",
        f"Required sources: {', '.join(item.replace('_', ' ') for item in source_types)}.",
    ]
    if focus_terms:
        parts.append(f"Focus: {', '.join(focus_terms)}.")
    return _clean_text(" ".join(parts))[:2000]


def _query_expansions(query, *, framework, regime, focus_terms, source_types):
    values = (
        query,
        _clean_text(" ".join([framework.replace("_", " "), regime, *focus_terms])),
        _clean_text(" ".join([*focus_terms, *[item.replace("_", " ") for item in source_types]])),
    )
    return tuple(dict.fromkeys(value[:2000] for value in values if value))


def _clean_unique(values):
    return tuple(dict.fromkeys(_clean_text(value) for value in values if _clean_text(value)))


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


__all__ = [
    "LiteratureDiscoveryRequest",
    "LiteratureDiscoverySpec",
    "build_literature_discovery_request",
    "normalize_literature_discovery_result",
]
