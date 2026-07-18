"""Trust-neutral contracts for dynamic host research routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from brain.v5.host_route_normalization import (
    clean_text as _clean_text,
    clean_text_tuple as _clean_text_tuple,
    freeze_component_scores as _freeze_component_scores,
    is_sha256 as _is_sha256,
    record_id as _record_id,
    record_id_tuple as _record_id_tuple,
    typed_ref_tuple as _typed_ref_tuple,
)


HOST_ROUTE_REQUEST_SCHEMA_VERSION = "aitp.host_route_request.v1"
HOST_ROUTE_DECISION_SCHEMA_VERSION = "aitp.host_route_decision.v1"
HOST_ROUTE_STATUSES = frozenset(
    {
        "outside_aitp",
        "selected",
        "ambiguous",
        "workspace_recovery",
        "conflict",
        "coverage_blocked",
    }
)
HOST_ROUTE_MODES = frozenset({"dynamic", "pinned", "pinned_compat"})
HOST_ROUTE_EVIDENCE_TIERS = frozenset(
    {
        "explicit",
        "pinned",
        "exact_anchor",
        "runtime_continuity",
        "indexed_text",
        "recency_tiebreak",
        "supporting_scope",
    }
)
HOST_ROUTE_INDEX_STATUSES = frozenset({"fresh", "stale", "missing", "invalid"})

_MAX_EXACT_REFS = 32


@dataclass(frozen=True)
class HostRouteRequest:
    request_summary: str
    host: str = ""
    host_session_id: str = ""
    project_root: str = ""
    current_path: str = ""
    repo_id: str = ""
    branch: str = ""
    visible_files: tuple[str, ...] = ()
    explicit_topic_ids: tuple[str, ...] = ()
    explicit_session_ids: tuple[str, ...] = ()
    exact_refs: tuple[str, ...] = ()
    pinned_session_id: str = ""
    routing_mode: str = "dynamic"
    semantic_assessment: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    schema_version: str = HOST_ROUTE_REQUEST_SCHEMA_VERSION


@dataclass(frozen=True)
class HostRouteCandidate:
    topic_id: str
    session_id: str
    score: int
    evidence_tier: str
    component_scores: Mapping[str, int]
    reason_codes: tuple[str, ...]
    exact_refs: tuple[str, ...]
    supporting_only: bool = False
    requires_target_revalidation: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "topic_id", _record_id(self.topic_id, "topic_id"))
        object.__setattr__(
            self, "session_id", _record_id(self.session_id, "session_id")
        )
        if not self.topic_id or not self.session_id:
            raise ValueError("route candidates require topic_id and session_id")
        if not isinstance(self.score, int) or not 0 <= self.score <= 1_000_000:
            raise ValueError("candidate score must be an integer between 0 and 1000000")
        tier = _clean_text(
            self.evidence_tier, "evidence_tier", required=True
        ).casefold()
        if tier not in HOST_ROUTE_EVIDENCE_TIERS:
            raise ValueError(f"unsupported route evidence tier: {tier}")
        object.__setattr__(self, "evidence_tier", tier)
        object.__setattr__(
            self,
            "component_scores",
            _freeze_component_scores(self.component_scores),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _clean_text_tuple(self.reason_codes, "reason_codes", required=True),
        )
        object.__setattr__(
            self,
            "exact_refs",
            _typed_ref_tuple(self.exact_refs, "exact_refs", max_items=_MAX_EXACT_REFS),
        )
        if not isinstance(self.supporting_only, bool):
            raise TypeError("supporting_only must be a bool")
        if not isinstance(self.requires_target_revalidation, bool):
            raise TypeError("requires_target_revalidation must be a bool")
        if self.supporting_only and not self.requires_target_revalidation:
            raise ValueError("supporting candidates require target revalidation")


@dataclass(frozen=True)
class HostRouteCoverage:
    checked_families: tuple[str, ...]
    not_shown_families: tuple[str, ...]
    not_checked_families: tuple[str, ...]
    malformed_count: int
    read_errors: tuple[str, ...]
    truncated: bool
    index_status: str
    index_generation: int
    canonical_watermark: str
    scope_fresh: bool
    strong_selection_eligible: bool

    def __post_init__(self) -> None:
        checked = _clean_text_tuple(
            self.checked_families, "checked_families", required=False
        )
        not_shown = _clean_text_tuple(
            self.not_shown_families, "not_shown_families", required=False
        )
        not_checked = _clean_text_tuple(
            self.not_checked_families, "not_checked_families", required=False
        )
        if set(checked) & (set(not_shown) | set(not_checked)):
            raise ValueError("coverage family sets must be disjoint")
        object.__setattr__(self, "checked_families", checked)
        object.__setattr__(self, "not_shown_families", not_shown)
        object.__setattr__(self, "not_checked_families", not_checked)
        if not isinstance(self.malformed_count, int) or self.malformed_count < 0:
            raise ValueError("malformed_count must be a non-negative integer")
        object.__setattr__(
            self,
            "read_errors",
            _clean_text_tuple(self.read_errors, "read_errors", required=False),
        )
        if not isinstance(self.truncated, bool):
            raise TypeError("truncated must be a bool")
        status = _clean_text(
            self.index_status, "index_status", required=True
        ).casefold()
        if status not in HOST_ROUTE_INDEX_STATUSES:
            raise ValueError(f"unsupported route index status: {status}")
        object.__setattr__(self, "index_status", status)
        if not isinstance(self.index_generation, int) or self.index_generation < 0:
            raise ValueError("index_generation must be a non-negative integer")
        watermark = _clean_text(
            self.canonical_watermark,
            "canonical_watermark",
            max_bytes=128,
        ).casefold()
        if watermark and not _is_sha256(watermark):
            raise ValueError("canonical_watermark must be a SHA-256 hex digest")
        object.__setattr__(self, "canonical_watermark", watermark)
        if not isinstance(self.scope_fresh, bool):
            raise TypeError("scope_fresh must be a bool")
        if not isinstance(self.strong_selection_eligible, bool):
            raise TypeError("strong_selection_eligible must be a bool")
        expected_strong = bool(
            status == "fresh"
            and self.scope_fresh
            and self.malformed_count == 0
            and not self.read_errors
            and not self.truncated
            and watermark
        )
        if self.strong_selection_eligible != expected_strong:
            raise ValueError(
                "strong_selection_eligible must match fresh complete route coverage"
            )


@dataclass(frozen=True)
class HostRouteDecision:
    status: str
    request_fingerprint: str
    candidates: tuple[HostRouteCandidate, ...]
    coverage: HostRouteCoverage
    selected_topic_id: str = ""
    selected_session_id: str = ""
    supporting_topic_ids: tuple[str, ...] = ()
    requires_target_revalidation: bool = False
    reason_codes: tuple[str, ...] = ()
    recommended_next_operation: str = "none"
    schema_version: str = HOST_ROUTE_DECISION_SCHEMA_VERSION
    orientation_only: bool = True
    summary_inputs_trusted: bool = False
    canonical_write_allowed: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False
    trust_effect: str = "none"

    def __post_init__(self) -> None:
        status = _clean_text(self.status, "status", required=True).casefold()
        if status not in HOST_ROUTE_STATUSES:
            raise ValueError(f"unsupported host route status: {status}")
        object.__setattr__(self, "status", status)
        if self.schema_version != HOST_ROUTE_DECISION_SCHEMA_VERSION:
            raise ValueError("unsupported host route decision schema")
        if not _is_sha256(self.request_fingerprint):
            raise ValueError("request_fingerprint must be a SHA-256 hex digest")
        if not isinstance(self.candidates, tuple) or any(
            not isinstance(candidate, HostRouteCandidate)
            for candidate in self.candidates
        ):
            raise TypeError("candidates must be a tuple of HostRouteCandidate")
        if len(self.candidates) > 3:
            raise ValueError("route decisions expose at most 3 candidates")
        if not isinstance(self.coverage, HostRouteCoverage):
            raise TypeError("coverage must be HostRouteCoverage")
        selected_topic = _record_id(self.selected_topic_id, "selected_topic_id")
        selected_session = _record_id(
            self.selected_session_id, "selected_session_id"
        )
        object.__setattr__(self, "selected_topic_id", selected_topic)
        object.__setattr__(self, "selected_session_id", selected_session)
        supporting_topics = _record_id_tuple(
            self.supporting_topic_ids,
            "supporting_topic_ids",
            max_items=3,
        )
        object.__setattr__(self, "supporting_topic_ids", supporting_topics)
        if not isinstance(self.requires_target_revalidation, bool):
            raise TypeError("requires_target_revalidation must be a bool")
        if supporting_topics and not self.requires_target_revalidation:
            raise ValueError("supporting topics require target revalidation")
        object.__setattr__(
            self,
            "reason_codes",
            _clean_text_tuple(self.reason_codes, "reason_codes", required=True),
        )
        operation = _clean_text(
            self.recommended_next_operation,
            "recommended_next_operation",
            required=True,
        )
        object.__setattr__(self, "recommended_next_operation", operation)
        self._validate_authority()
        if status == "selected":
            if not self.coverage.strong_selection_eligible:
                raise ValueError("selected routes require strong coverage")
            if not selected_topic or not selected_session:
                raise ValueError("selected routes require topic and session ids")
            if not any(
                candidate.topic_id == selected_topic
                and candidate.session_id == selected_session
                and not candidate.supporting_only
                for candidate in self.candidates
            ):
                raise ValueError("selected route must match a primary candidate")
        elif selected_topic or selected_session:
            raise ValueError("non-selected routes cannot carry selected ids")
        if status == "ambiguous":
            primary_count = sum(
                not candidate.supporting_only for candidate in self.candidates
            )
            if primary_count < 2:
                raise ValueError("ambiguous routes require at least two primary candidates")
        if status == "outside_aitp" and self.candidates:
            raise ValueError("outside_aitp routes cannot carry candidates")

    def _validate_authority(self) -> None:
        if self.orientation_only is not True:
            raise ValueError("orientation_only must be true")
        if self.summary_inputs_trusted is not False:
            raise ValueError("summary_inputs_trusted must be false")
        if self.canonical_write_allowed is not False:
            raise ValueError("canonical_write_allowed must be false")
        if self.can_update_kernel_state is not False:
            raise ValueError("can_update_kernel_state must be false")
        if self.can_update_claim_trust is not False:
            raise ValueError("can_update_claim_trust must be false")
        if self.trust_effect != "none":
            raise ValueError("trust_effect must be none")


def normalize_host_route_request(request: HostRouteRequest) -> HostRouteRequest:
    from brain.v5.host_route_requests import normalize_host_route_request as _normalize

    return _normalize(request)


def host_route_request_fingerprint(request: HostRouteRequest) -> str:
    from brain.v5.host_route_requests import host_route_request_fingerprint as _hash

    return _hash(request)


def route_decision_payload(decision: HostRouteDecision) -> dict[str, Any]:
    from brain.v5.host_route_payloads import route_decision_payload as _serialize

    return _serialize(decision)


def host_route_decision_from_payload(payload: Mapping[str, Any]) -> HostRouteDecision:
    from brain.v5.host_route_payloads import (
        host_route_decision_from_payload as _deserialize,
    )

    return _deserialize(payload)


def validate_host_route_decision_payload(payload: object) -> tuple[str, ...]:
    from brain.v5.host_route_payloads import (
        validate_host_route_decision_payload as _validate,
    )

    return _validate(payload)
