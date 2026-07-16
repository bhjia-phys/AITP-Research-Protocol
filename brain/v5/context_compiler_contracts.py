"""Contracts for bounded, trust-neutral compiled research context."""

from __future__ import annotations

from brain.v5.context_compiler import ContextBundle, estimate_context_tokens
from brain.v5.context_selection import NOT_SHOWN_REASON_CODES
from brain.v5.context_disclosure import DISCLOSURE_LEVELS
from brain.v5.knowledge_context_integration import knowledge_context_payload_errors
from brain.v5.skill_context_integration import skill_context_payload_errors


_NEXT_DISCLOSURE = {
    "route_hint": "startup_orientation",
    "startup_orientation": "normal_research",
    "normal_research": "exact_expansion",
    "exact_expansion": "",
}


def validate_context_bundle(bundle: ContextBundle) -> tuple[str, ...]:
    errors: list[str] = []
    errors.extend(message for _path, message in knowledge_context_payload_errors(bundle.knowledge_context))
    errors.extend(skill_context_payload_errors(bundle.applicable_skills))
    if not bundle.session_id:
        errors.append("session_id must be non-empty")
    if not bundle.topic_id:
        errors.append("topic_id must be non-empty")
    if bundle.disclosure_level not in DISCLOSURE_LEVELS:
        errors.append("disclosure_level is unsupported")
    if bundle.source_index_generation < 1:
        errors.append("source_index_generation must be positive")
    if bundle.index_status not in {"fresh", "stale"}:
        errors.append("index_status must be fresh or stale")
    if bundle.byte_count != len(bundle.markdown.encode("utf-8")):
        errors.append("byte_count must match markdown UTF-8 bytes")
    if bundle.estimated_tokens != estimate_context_tokens(bundle.markdown):
        errors.append("estimated_tokens must match deterministic estimator")
    if bundle.byte_count > bundle.max_bytes:
        errors.append("byte_count exceeds max_bytes")
    if bundle.estimated_tokens > bundle.max_tokens:
        errors.append("estimated_tokens exceeds max_tokens")
    if len(bundle.record_refs) > 200:
        errors.append("record_refs must remain bounded")
    if not isinstance(bundle.not_shown_count, int) or isinstance(bundle.not_shown_count, bool) or bundle.not_shown_count < 0:
        errors.append("not_shown_count must be a non-negative integer")
    unknown_reasons = set(bundle.not_shown_reason) - set(NOT_SHOWN_REASON_CODES)
    if unknown_reasons:
        errors.append(f"not_shown_reason contains unknown codes: {sorted(unknown_reasons)}")
    if bundle.not_shown_count == 0 and bundle.not_shown_reason:
        errors.append("not_shown_reason must be empty when not_shown_count is zero")
    if bundle.not_shown_count > 0 and not bundle.not_shown_reason:
        errors.append("not_shown_reason is required when candidates are omitted")
    for label, value in (
        ("partial", bundle.partial),
        ("retrieval_truncated", bundle.retrieval_truncated),
        ("render_truncated", bundle.render_truncated),
        ("truncated", bundle.truncated),
    ):
        if not isinstance(value, bool):
            errors.append(f"{label} must be a boolean")
    if bundle.truncated != (bundle.retrieval_truncated or bundle.render_truncated):
        errors.append("truncated must combine retrieval_truncated and render_truncated")
    if bundle.not_found_refs and bundle.can_claim_no_prior_result:
        errors.append("not-found exact refs forbid a no-prior-result claim")

    scope = bundle.scope
    for key in (
        "session_id",
        "primary_topic_id",
        "focus_set_ref",
        "program_id",
        "primary_refs",
        "supporting_topic_ids",
        "supporting_refs",
        "excluded_refs",
        "unresolved_refs",
        "discovery_refs",
        "requires_revalidation_refs",
        "checked_refs",
        "unchecked_refs",
        "claim_trust_transfer",
    ):
        if key not in scope:
            errors.append(f"scope missing {key}")
    if scope.get("session_id") != bundle.session_id:
        errors.append("scope session_id must match bundle session_id")
    if scope.get("primary_topic_id") != bundle.topic_id:
        errors.append("scope primary_topic_id must match bundle topic_id")
    if scope.get("focus_set_ref", "") != bundle.focus_set_ref:
        errors.append("scope focus_set_ref must match bundle focus_set_ref")
    if scope.get("program_id", "") != bundle.program_id:
        errors.append("scope program_id must match bundle program_id")
    if scope.get("claim_trust_transfer") != "forbidden":
        errors.append("scope claim_trust_transfer must be forbidden")
    primary_refs = set(scope.get("primary_refs") or ())
    supporting_refs = set(scope.get("supporting_refs") or ())
    excluded_refs = set(scope.get("excluded_refs") or ())
    unresolved_refs = set(scope.get("unresolved_refs") or ())
    if (primary_refs | supporting_refs) & (excluded_refs | unresolved_refs):
        errors.append("scope included refs must not overlap excluded or unresolved refs")
    if set(scope.get("requires_revalidation_refs") or ()) - supporting_refs:
        errors.append("revalidation refs must be contained in supporting scope")
    if set(bundle.not_found_refs) & excluded_refs:
        errors.append("scope-excluded refs cannot be reported as not_found")
    if set(bundle.not_found_refs) & set(scope.get("discovery_refs") or ()):
        errors.append("scope-discovery refs cannot be reported as not_found")
    blocked_explicit = set(scope.get("blocked_explicit_refs") or ())
    if blocked_explicit & set(bundle.record_refs):
        errors.append("blocked explicit refs cannot enter compiled context")
    if blocked_explicit & set(bundle.not_found_refs):
        errors.append("blocked explicit refs cannot be reported as not_found")

    handles = bundle.next_level_handles
    if handles.get("next_disclosure_level") != _NEXT_DISCLOSURE.get(
        bundle.disclosure_level
    ):
        errors.append("next disclosure handle does not follow the fixed ladder")
    if handles.get("session_id") != bundle.session_id:
        errors.append("next-level session handle must match the bundle")
    if handles.get("topic_id") != bundle.topic_id:
        errors.append("next-level topic handle must match the bundle")
    recoverable_refs = tuple(handles.get("exact_expansion_refs") or ())
    recoverable_count = handles.get("exact_expansion_ref_count", 0)
    if not isinstance(recoverable_count, int) or isinstance(recoverable_count, bool):
        errors.append("exact expansion ref count must be an integer")
    elif recoverable_count < len(recoverable_refs):
        errors.append("exact expansion ref count cannot be smaller than the handle page")
    if handles.get("exact_expansion_refs_truncated") != (
        isinstance(recoverable_count, int)
        and not isinstance(recoverable_count, bool)
        and recoverable_count > len(recoverable_refs)
    ):
        errors.append("exact expansion handle truncation must match its bounded ref page")
    if set(recoverable_refs) - set(scope.get("not_shown_refs") or ()):
        errors.append("exact expansion handles must point to refs omitted from this context")
    if bundle.disclosure_level == "route_hint":
        if bundle.candidate_summaries:
            errors.append("route hints cannot contain scientific candidate summaries")
        if bundle.current_boundary.get("claim_id"):
            errors.append("route hints cannot disclose an active scientific claim")
    if bundle.disclosure_level == "exact_expansion":
        requested_refs = set(bundle.expansion.get("requested_refs") or ())
        if set(bundle.record_refs) - requested_refs:
            errors.append("exact expansion returned an unrequested ref")
        if bundle.expansion.get("canonical_record_payloads_in_expansion") is not True:
            errors.append("exact expansion must include canonical record payloads")
        item_refs = tuple(
            item.get("record_ref")
            for item in bundle.expansion.get("items") or ()
            if isinstance(item, dict)
        )
        if item_refs != bundle.record_refs:
            errors.append("exact expansion items must match returned record_refs")
        if bundle.expansion.get("unchecked_requested_refs") and bundle.coverage.get("exhaustive"):
            errors.append("exact expansion with unchecked refs cannot claim exhaustive coverage")

    coverage = bundle.coverage
    for key in (
        "exhaustive",
        "can_claim_no_result",
        "checked_families",
        "unchecked_families",
        "malformed_count",
        "reason",
    ):
        if key not in coverage:
            errors.append(f"coverage missing {key}")
    if bundle.index_status == "stale" and coverage.get("exhaustive"):
        errors.append("stale context cannot claim exhaustive coverage")
    if (bundle.truncated or bundle.read_errors or not coverage.get("exhaustive")) and bundle.can_claim_no_prior_result:
        errors.append("partial context cannot claim no prior result")

    expansion = bundle.expansion
    if expansion.get("surface") != "record_refs":
        errors.append("expansion surface must be record_refs")
    if tuple(expansion.get("refs") or ()) != bundle.record_refs:
        errors.append("expansion refs must match record_refs")
    if expansion.get("requires_explicit_call") is not True:
        errors.append("record expansion must require an explicit call")
    if expansion.get("full_record_bodies_in_default_context") is not False:
        errors.append("default context cannot include full record bodies")

    if bundle.orientation_only is not True:
        errors.append("orientation_only must be true")
    if bundle.summary_inputs_trusted is not False:
        errors.append("summary_inputs_trusted must be false")
    if bundle.can_update_kernel_state is not False:
        errors.append("can_update_kernel_state must be false")
    if bundle.can_update_claim_trust is not False:
        errors.append("can_update_claim_trust must be false")
    if bundle.requires_exact_expansion_before_trust_conclusions is not True:
        errors.append("trust-sensitive conclusions must require exact expansion")
    return tuple(errors)
