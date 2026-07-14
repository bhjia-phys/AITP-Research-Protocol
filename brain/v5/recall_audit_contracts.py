"""Contracts and deterministic identities for persisted deep-recall audits."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from brain.v5.lifecycle_models import RecallAuditRecord
from brain.v5.record_family_registry import record_family_specs
from brain.v5.research_scope_contracts import canonical_typed_ref


LANE_ORDER = ("primary", "program_shared", "discovery")


def validate_recall_request_shape(request: object) -> None:
    session_id = str(getattr(request, "session_id", "") or "").strip()
    query_text = str(getattr(request, "query_text", "") or "").strip()
    intent = str(getattr(request, "normalized_intent", "") or "").strip()
    if not session_id:
        raise ValueError("session_id must be non-empty")
    if not query_text:
        raise ValueError("query_text must be non-empty")
    if not intent:
        raise ValueError("normalized_intent must be non-empty")
    if len(query_text) > 4000 or len(intent) > 200:
        raise ValueError("recall query or normalized intent exceeds its bounded size")
    required = getattr(request, "required_families", None)
    exact_refs = getattr(request, "exact_refs", None)
    if not isinstance(required, tuple) or not required:
        raise TypeError("required_families must be a non-empty tuple")
    if not isinstance(exact_refs, tuple):
        raise TypeError("exact_refs must be a tuple")
    if len(required) > 32 or len(exact_refs) > 100:
        raise ValueError("recall family or exact-ref scope exceeds its bounded size")
    specs = record_family_specs()
    unknown = sorted(set(required) - set(specs))
    if unknown:
        raise ValueError("unknown required families: " + ", ".join(unknown))
    if any(not str(family or "").strip() for family in required):
        raise ValueError("required_families must contain non-empty values")
    for ref in exact_refs:
        canonical_typed_ref(ref)
    if not isinstance(getattr(request, "include_program_scope", None), bool):
        raise TypeError("include_program_scope must be a boolean")
    if not isinstance(getattr(request, "include_discovery", None), bool):
        raise TypeError("include_discovery must be a boolean")
    top_k = getattr(request, "top_k", 0)
    if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= 100:
        raise ValueError("top_k must be an integer between 1 and 100")


def deterministic_audit_id(payload: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"recall-audit-{hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:24]}"


def validate_recall_lane(
    lane: Mapping[str, Any],
    *,
    expected_name: str,
    expected_order: int,
) -> tuple[str, ...]:
    errors: list[str] = []
    lane_name = str(lane.get("lane") or "")
    if lane_name != expected_name:
        errors.append(f"lane order {expected_order} must be {expected_name}")
    if lane.get("order") != expected_order:
        errors.append(f"lane {lane_name} has an invalid order")
    for key in (
        "scope_refs",
        "topic_ids",
        "program_ids",
        "requested_exact_refs",
        "checked_families",
        "unchecked_families",
        "top_refs",
        "excluded_candidates",
        "dirty_families",
        "read_errors",
        "results",
    ):
        if not isinstance(lane.get(key), list):
            errors.append(f"lane {lane_name}.{key} must be a list")
    for key in (
        "exact_only",
        "content_verified",
        "exhaustive",
        "stale",
        "truncated",
        "self_certification_blocked",
    ):
        if not isinstance(lane.get(key), bool):
            errors.append(f"lane {lane_name}.{key} must be a boolean")
    for result in lane.get("results") or []:
        if not isinstance(result, Mapping):
            errors.append(f"lane {lane_name}.results must contain mappings")
            continue
        if "record" in result or "summary" in result or "search_text" in result:
            errors.append(f"lane {lane_name} persists retrieved content")
    if lane.get("self_certification_blocked") and lane.get("exhaustive"):
        errors.append(f"lane {lane_name} cannot self-certify recall_audits")
    return tuple(errors)


def validate_recall_audit(record: RecallAuditRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if not record.audit_id or not record.session_id or not record.topic_id:
        errors.append("audit_id, session_id, and topic_id must be non-empty")
    if not record.query_text or not record.normalized_intent:
        errors.append("query_text and normalized_intent must be non-empty")
    if not record.required_families:
        errors.append("required_families must be non-empty")
    checked = set(record.checked_families)
    unchecked = set(record.unchecked_families)
    if not set(record.required_families).issubset(checked | unchecked):
        errors.append("required_families must be classified as checked or unchecked")
    if checked.intersection(unchecked):
        errors.append("checked_families and unchecked_families must be disjoint")
    if set(record.family_state_tokens) != checked:
        errors.append("family_state_tokens must exactly cover checked_families")
    if set(record.family_content_watermarks) != checked:
        errors.append("family_content_watermarks must exactly cover checked_families")
    if not record.retrieval_scope_token:
        errors.append("retrieval_scope_token must be non-empty")
    if not set(record.missing_exact_refs).issubset(set(record.required_exact_refs)):
        errors.append("missing_exact_refs must be requested exact refs")
    expected_names = [name for name in LANE_ORDER if name != "discovery" or record.include_discovery]
    if not record.include_program_scope:
        expected_names.remove("program_shared")
    actual_names = [str(lane.get("lane") or "") for lane in record.lanes]
    if actual_names != expected_names:
        errors.append("recall lanes do not match the requested ordered scope")
    for order, lane in enumerate(record.lanes):
        expected_name = expected_names[order] if order < len(expected_names) else "<none>"
        errors.extend(
            validate_recall_lane(
                lane,
                expected_name=expected_name,
                expected_order=order,
            )
        )
    if record.can_claim_no_result and (
        not record.exhaustive
        or not record.content_verified
        or record.stale
        or record.truncated
        or record.top_refs
        or record.read_errors
        or record.missing_exact_refs
    ):
        errors.append("can_claim_no_result requires an empty exhaustive verified audit")
    if "recall_audits" in record.required_families and record.exhaustive:
        errors.append("recall_audits cannot self-certify in the generation it creates")
    if record.can_update_claim_trust is not False:
        errors.append("can_update_claim_trust must be false")
    return tuple(dict.fromkeys(errors))
