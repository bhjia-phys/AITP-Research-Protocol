"""Normalize host-returned literature candidates without creating source truth."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, replace
from datetime import UTC, datetime
from typing import Any

from brain.v5.literature_discovery_contracts import (
    normalized_token,
    parse_timestamp,
    validate_literature_discovery_request,
)
from brain.v5.literature_discovery_models import (
    LiteratureConnectorCoverage,
    LiteratureDiscoveryCandidate,
    LiteratureDiscoveryExclusion,
    LiteratureDiscoveryReceipt,
    LiteratureDiscoveryRequest,
)
from brain.v5.literature_discovery_values import (
    FrozenJsonDict,
    normalize_coverage,
    safe_external_uri,
    uri_dedup_key,
)


_CONNECTOR_STATUSES = {"ok", "partial", "failed"}
_RESTRICTED_ACCESS = {"denied", "forbidden", "license_denied", "license_restricted", "restricted"}
_ELIGIBLE_ACCESS = {"author_copy", "license_verified", "open_access", "public_domain"}
_MAX_CONNECTOR_PACKETS = 64
_MAX_DIAGNOSTICS = 200


def normalize_literature_discovery_result(
    request: LiteratureDiscoveryRequest,
    connector_result: dict[str, Any],
) -> LiteratureDiscoveryReceipt:
    """Normalize bounded connector metadata; snippets remain process-only."""

    if not isinstance(request, LiteratureDiscoveryRequest):
        raise TypeError("request must be LiteratureDiscoveryRequest")
    now = datetime.now(UTC)
    if now >= parse_timestamp(request.expires_at):
        raise ValueError("literature discovery request is expired")
    validate_literature_discovery_request(request)
    if (now - parse_timestamp(request.created_at)).total_seconds() > request.timeout_seconds:
        raise ValueError("literature discovery request execution timeout exceeded")
    if type(connector_result) is not dict:
        raise TypeError("connector_result must be a plain JSON object")
    raw_connectors = connector_result.get("connector_results", [])
    if type(raw_connectors) is not list:
        raise ValueError("connector_results must be a plain JSON list")
    if len(raw_connectors) > _MAX_CONNECTOR_PACKETS:
        raise ValueError("connector result packet budget exceeded")

    coverage: list[LiteratureConnectorCoverage] = []
    exclusions: list[LiteratureDiscoveryExclusion] = []
    errors: list[str] = []
    candidates_by_key: dict[str, LiteratureDiscoveryCandidate] = {}
    duplicate_count = 0
    raw_result_count = 0
    input_dropped_count = 0
    packet_diagnostic_dropped_count = 0
    packets_by_connector: dict[str, list[dict]] = {}
    for raw_connector in raw_connectors:
        if type(raw_connector) is not dict:
            errors.append("malformed connector result")
            continue
        connector_id = _bounded_text(raw_connector.get("connector_id"), 200)
        if connector_id not in request.connector_allowlist:
            errors.append(f"connector {connector_id or '<missing>'} is not allowed by request")
            continue
        packets_by_connector.setdefault(connector_id, []).append(raw_connector)

    for connector_id in sorted(request.connector_allowlist):
        packets = packets_by_connector.get(connector_id, [])
        if not packets:
            detail = f"connector {connector_id} did not return a result packet"
            coverage.append(_failed_coverage(connector_id, detail))
            errors.append(detail)
            continue
        if len(packets) > 1:
            detail = f"connector {connector_id} returned more than one result packet"
            coverage.append(_failed_coverage(connector_id, detail))
            errors.append(detail)
            continue
        (
            packet_coverage,
            normalized_items,
            connector_errors,
            raw_count,
            dropped,
            diagnostic_dropped,
        ) = _normalize_connector_packet(request, connector_id, packets[0])
        coverage.append(packet_coverage)
        errors.extend(connector_errors)
        raw_result_count += raw_count
        input_dropped_count += dropped
        packet_diagnostic_dropped_count += diagnostic_dropped
        for normalized in normalized_items:
            if isinstance(normalized, LiteratureDiscoveryExclusion):
                exclusions.append(normalized)
                continue
            existing = candidates_by_key.get(normalized.dedup_key)
            if existing is None:
                candidates_by_key[normalized.dedup_key] = normalized
                continue
            duplicate_count += 1
            candidates_by_key[normalized.dedup_key] = _merge_candidate(existing, normalized)

    coverage.sort(key=lambda item: item.connector_id)
    ordered = sorted(candidates_by_key.values(), key=lambda item: item.dedup_key)
    budget_dropped_count = max(0, len(ordered) - request.max_results)
    candidates = tuple(ordered[: request.max_results])
    exclusions.sort(key=_normalized_item_sort_key)
    unique_errors = sorted(set(errors))
    diagnostic_dropped_count = (
        packet_diagnostic_dropped_count
        + max(0, len(exclusions) - _MAX_DIAGNOSTICS)
        + max(0, len(unique_errors) - _MAX_DIAGNOSTICS)
    )
    exclusions = exclusions[:_MAX_DIAGNOSTICS]
    unique_errors = unique_errors[:_MAX_DIAGNOSTICS]
    truncated = any(
        (budget_dropped_count, input_dropped_count, diagnostic_dropped_count)
    )
    status = _receipt_status(coverage, unique_errors, candidates)
    normalized_at = now.isoformat()
    receipt_basis = {
        "request_id": request.request_id,
        "request_fingerprint": request.dedup_fingerprint,
        "request_integrity_hash": request.request_integrity_hash,
        "status": status,
        "candidates": [asdict(item) for item in candidates],
        "excluded_candidates": [asdict(item) for item in exclusions],
        "connector_coverage": [asdict(item) for item in coverage],
        "errors": unique_errors,
        "raw_result_count": raw_result_count,
        "duplicate_count": duplicate_count,
        "budget_dropped_count": budget_dropped_count,
        "input_dropped_count": input_dropped_count,
        "diagnostic_dropped_count": diagnostic_dropped_count,
    }
    return LiteratureDiscoveryReceipt(
        receipt_id=f"literature-discovery-receipt:{_hash_json(receipt_basis)}",
        request_id=request.request_id,
        request_fingerprint=request.dedup_fingerprint,
        request_integrity_hash=request.request_integrity_hash,
        status=status,
        candidates=candidates,
        excluded_candidates=tuple(exclusions),
        connector_coverage=tuple(coverage),
        errors=tuple(unique_errors),
        raw_result_count=raw_result_count,
        candidate_count=len(candidates),
        eligible_candidate_count=sum(item.acquisition_eligible for item in candidates),
        duplicate_count=duplicate_count,
        excluded_count=len(exclusions),
        budget_dropped_count=budget_dropped_count,
        input_dropped_count=input_dropped_count,
        diagnostic_dropped_count=diagnostic_dropped_count,
        truncated=truncated,
        normalized_at=normalized_at,
    )


def _normalize_connector_packet(request, connector_id, packet):
    status = _bounded_text(packet.get("status"), 50).lower() or "failed"
    connector_errors, diagnostic_dropped_count = _clean_errors(packet.get("errors", []))
    if status not in _CONNECTOR_STATUSES:
        connector_errors.append(f"unsupported connector status: {status}")
        status = "failed"
    connector_coverage, coverage_error = normalize_coverage(packet.get("coverage", {}))
    if not connector_coverage and not coverage_error:
        coverage_error = "coverage must describe connector work"
    elif not coverage_error and (
        type(connector_coverage.get("query_count")) is not int
        or connector_coverage["query_count"] <= 0
    ):
        coverage_error = "coverage must report a positive query_count"
    if coverage_error:
        connector_errors.append(coverage_error)
        status = "partial" if status == "ok" else status
    raw_results = packet.get("results", [])
    if type(raw_results) is not list:
        connector_errors.append("results must be a plain JSON list")
        raw_results = []
        status = "failed"
    raw_count = len(raw_results)
    result_limit = max(100, min(500, request.max_results * 10))
    input_dropped_count = 0
    if raw_count > result_limit:
        connector_errors.append(
            f"connector result budget exceeded: {raw_count} > {result_limit}"
        )
        input_dropped_count = raw_count
        raw_results = []
        status = "failed"
    normalized = [
        _normalize_candidate(request, connector_id, raw_candidate)
        for raw_candidate in raw_results
    ]
    normalized.sort(key=_normalized_item_sort_key)
    unique_connector_errors = sorted(set(connector_errors))
    diagnostic_dropped_count += max(
        0, len(unique_connector_errors) - _MAX_DIAGNOSTICS
    )
    connector_errors = unique_connector_errors[:_MAX_DIAGNOSTICS]
    return (
        LiteratureConnectorCoverage(
            connector_id=connector_id,
            status=status,
            raw_result_count=raw_count,
            coverage=connector_coverage,
            errors=tuple(connector_errors),
        ),
        normalized,
        connector_errors,
        raw_count,
        input_dropped_count,
        diagnostic_dropped_count,
    )


def _failed_coverage(connector_id, detail):
    return LiteratureConnectorCoverage(
        connector_id=connector_id,
        status="failed",
        raw_result_count=0,
        coverage=FrozenJsonDict(),
        errors=(detail,),
    )


def _normalized_item_sort_key(item):
    if isinstance(item, LiteratureDiscoveryCandidate):
        return ("candidate", item.dedup_key, _hash_json(asdict(item)))
    return (
        "exclusion",
        item.connector_id,
        item.reason,
        item.dedup_hint,
        item.detail,
    )


def _normalize_candidate(request, connector_id, raw):
    if type(raw) is not dict:
        return _exclusion(
            connector_id,
            "invalid_candidate",
            "",
            "candidate must be a plain JSON object",
        )
    title = _bounded_text(raw.get("title"), 1000)
    raw_doi, invalid_doi_input = _identity_text(raw.get("doi"), 300)
    raw_arxiv, invalid_arxiv_input = _identity_text(raw.get("arxiv_id"), 100)
    uri, invalid_uri_input = _identity_text(raw.get("uri"), 2000)
    if invalid_doi_input or invalid_arxiv_input:
        return _exclusion(
            connector_id,
            "invalid_identifier",
            "",
            "candidate DOI or arXiv identifier exceeds its input contract",
        )
    if invalid_uri_input:
        return _exclusion(
            connector_id,
            "invalid_location",
            "",
            "candidate URI exceeds its input contract",
        )
    doi = _normalize_doi(raw_doi)
    arxiv_id = _normalize_arxiv(raw_arxiv)
    if raw_doi and not doi or raw_arxiv and not arxiv_id:
        return _exclusion(
            connector_id,
            "invalid_identifier",
            "",
            "candidate DOI or arXiv identifier is malformed",
        )
    if uri and not safe_external_uri(uri):
        return _exclusion(
            connector_id,
            "unsafe_uri_scheme",
            "",
            "candidate URI must be an absolute HTTP or HTTPS location",
        )
    dedup_key = _dedup_key(
        doi=doi,
        arxiv_id=arxiv_id,
        uri=uri,
        title=title,
        year=raw.get("year"),
    )
    if not title or not dedup_key:
        return _exclusion(
            connector_id,
            "invalid_candidate",
            dedup_key,
            "candidate requires title plus DOI, arXiv ID, or URI",
        )
    framework = normalized_token(_bounded_text(raw.get("framework"), 100) or request.framework)
    if framework != request.framework:
        return _exclusion(
            connector_id,
            "framework_mismatch",
            dedup_key,
            f"candidate framework {framework} does not match {request.framework}",
        )
    source_type = normalized_token(_bounded_text(raw.get("source_type"), 100) or "primary_paper")
    if source_type not in request.required_source_types:
        return _exclusion(
            connector_id,
            "source_type_mismatch",
            dedup_key,
            f"candidate source type {source_type} was not requested",
        )
    access = normalized_token(
        _bounded_text(raw.get("access_disposition"), 100) or "not_checked"
    )
    stable_locator = bool(doi or arxiv_id or uri)
    eligible = stable_locator and access in _ELIGIBLE_ACCESS
    if access in _RESTRICTED_ACCESS:
        exclusion_reason = access
    elif not stable_locator:
        exclusion_reason = "stable_locator_not_verified"
    else:
        exclusion_reason = "" if eligible else "access_not_verified"
    return LiteratureDiscoveryCandidate(
        candidate_id=f"literature-candidate:{_hash_json({'dedup_key': dedup_key})}",
        dedup_key=dedup_key,
        title=title,
        authors=_authors(raw.get("authors")),
        year=_year(raw.get("year")),
        doi=doi,
        arxiv_id=arxiv_id,
        uri=uri,
        connector_ids=(connector_id,),
        framework=framework,
        source_type=source_type,
        snippet=_bounded_text(raw.get("snippet"), 1000),
        access_disposition=access,
        acquisition_eligible=eligible,
        exclusion_reason=exclusion_reason,
    )


def _merge_candidate(first, second):
    connector_ids = tuple(sorted(set(first.connector_ids + second.connector_ids)))
    access, eligible, exclusion_reason = _merge_access(first, second)
    return replace(
        first,
        authors=first.authors or second.authors,
        year=first.year if first.year is not None else second.year,
        uri=first.uri or second.uri,
        connector_ids=connector_ids,
        snippet=first.snippet or second.snippet,
        access_disposition=access,
        acquisition_eligible=eligible,
        exclusion_reason=exclusion_reason,
    )


def _merge_access(first, second):
    for candidate in (first, second):
        if candidate.access_disposition in _RESTRICTED_ACCESS:
            return candidate.access_disposition, False, candidate.exclusion_reason
    for candidate in (first, second):
        if candidate.acquisition_eligible:
            return candidate.access_disposition, True, ""
    return first.access_disposition or second.access_disposition, False, "access_not_verified"


def _dedup_key(*, doi, arxiv_id, uri, title, year):
    if doi:
        return f"doi:{doi}"
    if arxiv_id:
        return f"arxiv:{arxiv_id.lower()}"
    if uri:
        return f"uri:{uri_dedup_key(uri)}"
    if title:
        return f"title:{title.casefold()}:{_year(year) or ''}"
    return ""


def _normalize_doi(value):
    text = _bounded_text(value, 300).lower()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    return text if re.fullmatch(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", text, re.I) else ""


def _normalize_arxiv(value):
    text = _bounded_text(value, 100)
    text = re.sub(
        r"^(?:arxiv:|https?://arxiv\.org/(?:abs|pdf)/)",
        "",
        text,
        flags=re.I,
    ).removesuffix(".pdf")
    if re.fullmatch(r"\d{4}\.\d{4,5}(?:v\d+)?", text, re.I):
        return text
    if re.fullmatch(r"[a-z-]+(?:\.[a-z]{2})?/\d{7}(?:v\d+)?", text, re.I):
        return text
    return ""


def _authors(value):
    if isinstance(value, str):
        author = _bounded_text(value, 300)
        return (author,) if author else ()
    if type(value) is list:
        authors = (
            _bounded_text(item, 300)
            for item in value[:32]
            if isinstance(item, str)
        )
        return tuple(dict.fromkeys(item for item in authors if item))
    return ()


def _year(value):
    if isinstance(value, bool) or type(value) not in (int, str):
        return None
    try:
        year = int(value)
    except (TypeError, ValueError):
        return None
    return year if 1000 <= year <= datetime.now(UTC).year + 1 else None


def _receipt_status(coverage, errors, candidates):
    if not coverage:
        return "failed"
    statuses = {item.status for item in coverage}
    if statuses == {"ok"} and not errors:
        return "complete"
    return "partial" if candidates else "failed"


def _clean_errors(value):
    if type(value) is not list:
        return ["errors must be a plain JSON list"], 0
    if len(value) > _MAX_DIAGNOSTICS:
        return [
            f"connector error budget exceeded: {len(value)} > {_MAX_DIAGNOSTICS}"
        ], len(value)
    errors = (
        _bounded_text(item, 500)
        for item in value
        if isinstance(item, str)
    )
    return sorted(set(item for item in errors if item)), 0


def _exclusion(connector_id, reason, dedup_hint, detail):
    return LiteratureDiscoveryExclusion(
        connector_id=connector_id,
        reason=reason,
        dedup_hint=dedup_hint,
        detail=detail,
    )


def _bounded_text(value, limit):
    if type(value) is not str:
        return ""
    return re.sub(r"\s+", " ", value[: limit * 2]).strip()[:limit]


def _identity_text(value, limit):
    if value is None:
        return "", False
    if type(value) is not str or len(value) > limit:
        return "", True
    return re.sub(r"\s+", " ", value).strip(), False


def _hash_json(value):
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
