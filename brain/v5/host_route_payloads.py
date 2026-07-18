"""Runtime payload encoding for trust-neutral host route decisions."""

from __future__ import annotations

from typing import Any, Mapping

from brain.v5.host_route_contracts import (
    HOST_ROUTE_DECISION_SCHEMA_VERSION,
    HostRouteCandidate,
    HostRouteCoverage,
    HostRouteDecision,
)


def route_decision_payload(decision: HostRouteDecision) -> dict[str, Any]:
    if not isinstance(decision, HostRouteDecision):
        raise TypeError("decision must be a HostRouteDecision")
    return {
        "kind": "host_route_decision",
        "schema_version": decision.schema_version,
        "status": decision.status,
        "request_fingerprint": decision.request_fingerprint,
        "candidates": [_candidate_payload(item) for item in decision.candidates],
        "coverage": _coverage_payload(decision.coverage),
        "selected_topic_id": decision.selected_topic_id,
        "selected_session_id": decision.selected_session_id,
        "supporting_topic_ids": list(decision.supporting_topic_ids),
        "requires_target_revalidation": decision.requires_target_revalidation,
        "reason_codes": list(decision.reason_codes),
        "recommended_next_operation": decision.recommended_next_operation,
        "orientation_only": decision.orientation_only,
        "summary_inputs_trusted": decision.summary_inputs_trusted,
        "canonical_write_allowed": decision.canonical_write_allowed,
        "can_update_kernel_state": decision.can_update_kernel_state,
        "can_update_claim_trust": decision.can_update_claim_trust,
        "trust_effect": decision.trust_effect,
    }


def host_route_decision_from_payload(payload: Mapping[str, Any]) -> HostRouteDecision:
    """Rebuild and revalidate a decision received across a runtime boundary."""

    if not isinstance(payload, Mapping):
        raise TypeError("host route decision payload must be a mapping")
    if payload.get("kind") != "host_route_decision":
        raise ValueError("host route decision kind is unsupported")
    if payload.get("schema_version") != HOST_ROUTE_DECISION_SCHEMA_VERSION:
        raise ValueError("unsupported host route decision schema")
    try:
        raw_coverage = payload["coverage"]
        if not isinstance(raw_coverage, Mapping):
            raise TypeError("coverage must be a mapping")
        raw_candidates = payload["candidates"]
        if not isinstance(raw_candidates, list):
            raise TypeError("candidates must be a list")
        return HostRouteDecision(
            status=payload["status"],
            request_fingerprint=payload["request_fingerprint"],
            candidates=tuple(_candidate_from_payload(item) for item in raw_candidates),
            coverage=_coverage_from_payload(raw_coverage),
            selected_topic_id=payload.get("selected_topic_id", ""),
            selected_session_id=payload.get("selected_session_id", ""),
            supporting_topic_ids=tuple(payload.get("supporting_topic_ids", ())),
            requires_target_revalidation=payload.get(
                "requires_target_revalidation", False
            ),
            reason_codes=tuple(payload["reason_codes"]),
            recommended_next_operation=payload["recommended_next_operation"],
            schema_version=payload["schema_version"],
            orientation_only=payload["orientation_only"],
            summary_inputs_trusted=payload["summary_inputs_trusted"],
            canonical_write_allowed=payload["canonical_write_allowed"],
            can_update_kernel_state=payload["can_update_kernel_state"],
            can_update_claim_trust=payload["can_update_claim_trust"],
            trust_effect=payload["trust_effect"],
        )
    except KeyError as exc:
        raise ValueError(f"host route decision is missing {exc.args[0]}") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError(str(exc)) from exc


def validate_host_route_decision_payload(payload: object) -> tuple[str, ...]:
    try:
        host_route_decision_from_payload(payload)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        return (str(exc),)
    return ()


def _candidate_payload(candidate: HostRouteCandidate) -> dict[str, Any]:
    return {
        "topic_id": candidate.topic_id,
        "session_id": candidate.session_id,
        "score": candidate.score,
        "evidence_tier": candidate.evidence_tier,
        "component_scores": dict(candidate.component_scores),
        "reason_codes": list(candidate.reason_codes),
        "exact_refs": list(candidate.exact_refs),
        "supporting_only": candidate.supporting_only,
        "requires_target_revalidation": candidate.requires_target_revalidation,
    }


def _coverage_payload(coverage: HostRouteCoverage) -> dict[str, Any]:
    return {
        "checked_families": list(coverage.checked_families),
        "not_shown_families": list(coverage.not_shown_families),
        "not_checked_families": list(coverage.not_checked_families),
        "malformed_count": coverage.malformed_count,
        "read_errors": list(coverage.read_errors),
        "truncated": coverage.truncated,
        "index_status": coverage.index_status,
        "index_generation": coverage.index_generation,
        "canonical_watermark": coverage.canonical_watermark,
        "scope_fresh": coverage.scope_fresh,
        "strong_selection_eligible": coverage.strong_selection_eligible,
    }


def _candidate_from_payload(payload: object) -> HostRouteCandidate:
    if not isinstance(payload, Mapping):
        raise TypeError("candidate must be a mapping")
    try:
        return HostRouteCandidate(
            topic_id=payload["topic_id"],
            session_id=payload["session_id"],
            score=payload["score"],
            evidence_tier=payload["evidence_tier"],
            component_scores=payload["component_scores"],
            reason_codes=tuple(payload["reason_codes"]),
            exact_refs=tuple(payload["exact_refs"]),
            supporting_only=payload.get("supporting_only", False),
            requires_target_revalidation=payload.get(
                "requires_target_revalidation", False
            ),
        )
    except KeyError as exc:
        raise ValueError(f"candidate is missing {exc.args[0]}") from exc


def _coverage_from_payload(payload: Mapping[str, Any]) -> HostRouteCoverage:
    return HostRouteCoverage(
        checked_families=tuple(payload["checked_families"]),
        not_shown_families=tuple(payload["not_shown_families"]),
        not_checked_families=tuple(payload["not_checked_families"]),
        malformed_count=payload["malformed_count"],
        read_errors=tuple(payload["read_errors"]),
        truncated=payload["truncated"],
        index_status=payload["index_status"],
        index_generation=payload["index_generation"],
        canonical_watermark=payload["canonical_watermark"],
        scope_fresh=payload["scope_fresh"],
        strong_selection_eligible=payload["strong_selection_eligible"],
    )
