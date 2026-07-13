"""Deterministic candidate selection and omission accounting for compact context."""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence


NOT_SHOWN_REASON_CODES = (
    "retrieval_page_limit",
    "candidate_limit",
    "context_pack_candidate_limit",
)
_HIGH_VALUE_FAMILY_QUOTAS = (
    ("validation_results", 1),
    ("tool_runs", 1),
    ("code_states", 1),
    ("artifacts", 1),
    ("source_assets", 2),
    ("reference_locations", 1),
    ("proof_obligations", 1),
    ("exploratory_records", 1),
)


def select_candidate_summaries(
    candidates: Sequence[dict[str, Any]],
    *,
    limit: int,
) -> tuple[dict[str, Any], ...]:
    """Keep priority representatives, then family/status diversity, then rank order."""

    if limit < 1:
        return ()
    ordered = sorted(candidates, key=candidate_priority)
    selected: list[dict[str, Any]] = []
    selected_refs: set[str] = set()

    def add(candidate: dict[str, Any]) -> None:
        ref = str(candidate.get("record_ref") or "")
        if len(selected) < limit and ref not in selected_refs:
            selected.append(candidate)
            selected_refs.add(ref)

    seen_priorities: set[int] = set()
    for candidate in ordered:
        priority = candidate_priority(candidate)[0]
        if priority not in seen_priorities:
            add(candidate)
            seen_priorities.add(priority)

    for family, quota in _HIGH_VALUE_FAMILY_QUOTAS:
        representatives = (
            candidate for candidate in ordered if candidate.get("family") == family
        )
        for _ in range(quota):
            representative = next(representatives, None)
            if representative is None:
                break
            add(representative)

    seen_families = {str(candidate.get("family") or "unknown") for candidate in selected}
    for candidate in ordered:
        family = str(candidate.get("family") or "unknown")
        if family not in seen_families:
            add(candidate)
            seen_families.add(family)

    seen_statuses = {_status_key(candidate) for candidate in selected}
    for candidate in ordered:
        status = _status_key(candidate)
        if status not in seen_statuses:
            add(candidate)
            seen_statuses.add(status)

    for candidate in ordered:
        add(candidate)
    return tuple(sorted(selected, key=candidate_priority))


def candidate_priority(candidate: Mapping[str, Any]) -> tuple[int, int]:
    fields = candidate.get("summary_fields")
    selected = fields if isinstance(fields, Mapping) else {}
    status = _status_key(candidate)
    text = json.dumps(selected, ensure_ascii=False, sort_keys=True).lower()
    failed = bool(
        status in {"failed", "fail", "negative", "invalid", "contradicted", "superseded"}
        or selected.get("superseded_by")
        or any(marker in text for marker in ("does not test", "runtime failure", "wrong route"))
    )
    if failed:
        priority = 0
    elif candidate.get("family") == "claims":
        priority = 1
    elif bool(candidate.get("process_family")):
        priority = 2
    else:
        priority = 3
    return priority, int(candidate.get("retrieval_rank") or 0)


def candidate_not_shown(
    *,
    total_count: int,
    shown_anchor_count: int,
    page_candidate_count: int,
    selected_count: int,
    retrieval_truncated: bool,
) -> tuple[int, tuple[str, ...]]:
    count = max(0, int(total_count) - int(shown_anchor_count) - int(selected_count))
    if count == 0:
        return 0, ()
    reasons: list[str] = []
    if retrieval_truncated:
        reasons.append("retrieval_page_limit")
    if page_candidate_count > selected_count:
        reasons.append("candidate_limit")
    if not reasons:
        reasons.append("candidate_limit")
    return count, tuple(reasons)


def merge_not_shown_reasons(*groups: Sequence[str]) -> tuple[str, ...]:
    present = {str(reason) for group in groups for reason in group}
    return tuple(reason for reason in NOT_SHOWN_REASON_CODES if reason in present)


def _status_key(candidate: Mapping[str, Any]) -> str:
    return str(candidate.get("status") or "unknown").strip().lower() or "unknown"
