"""Process-only contracts for bounded literature discovery handoffs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from brain.v5.pinned_record_refs import PinnedRecordRef


@dataclass(frozen=True)
class LiteratureDiscoverySpec:
    gap_ref: PinnedRecordRef
    prior_audit_ref: PinnedRecordRef
    framework: str
    regime: str
    required_source_types: tuple[str, ...]
    connector_allowlist: tuple[str, ...]
    focus_terms: tuple[str, ...] = ()
    max_results: int = 20
    timeout_seconds: int = 30
    ttl_seconds: int = 900


@dataclass(frozen=True)
class LiteratureDiscoveryRequest:
    request_id: str
    dedup_fingerprint: str
    request_integrity_hash: str
    gap_ref: PinnedRecordRef
    prior_audit_ref: PinnedRecordRef
    topic_id: str
    claim_id: str
    program_id: str
    focus_set_ref: str
    normalized_query: str
    query_expansions: tuple[str, ...]
    framework: str
    regime: str
    focus_terms: tuple[str, ...]
    required_source_types: tuple[str, ...]
    connector_allowlist: tuple[str, ...]
    max_results: int
    timeout_seconds: int
    ttl_seconds: int
    created_at: str
    expires_at: str
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False
    can_create_source_asset: bool = False


@dataclass(frozen=True)
class LiteratureDiscoveryCandidate:
    candidate_id: str
    dedup_key: str
    title: str
    authors: tuple[str, ...]
    year: int | None
    doi: str
    arxiv_id: str
    uri: str
    connector_ids: tuple[str, ...]
    framework: str
    source_type: str
    snippet: str
    access_disposition: str
    acquisition_eligible: bool
    exclusion_reason: str = ""
    orientation_only: bool = True
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class LiteratureDiscoveryExclusion:
    connector_id: str
    reason: str
    dedup_hint: str
    detail: str


@dataclass(frozen=True)
class LiteratureConnectorCoverage:
    connector_id: str
    status: str
    raw_result_count: int
    coverage: dict[str, Any]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class LiteratureDiscoveryReceipt:
    receipt_id: str
    request_id: str
    request_fingerprint: str
    request_integrity_hash: str
    status: str
    candidates: tuple[LiteratureDiscoveryCandidate, ...]
    excluded_candidates: tuple[LiteratureDiscoveryExclusion, ...]
    connector_coverage: tuple[LiteratureConnectorCoverage, ...]
    errors: tuple[str, ...]
    raw_result_count: int
    candidate_count: int
    eligible_candidate_count: int
    duplicate_count: int
    excluded_count: int
    budget_dropped_count: int
    input_dropped_count: int
    diagnostic_dropped_count: int
    truncated: bool
    normalized_at: str
    summary_inputs_trusted: bool = False
    orientation_only: bool = True
    can_claim_no_result: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False
    can_create_source_asset: bool = False
