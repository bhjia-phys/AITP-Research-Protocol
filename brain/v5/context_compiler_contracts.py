"""Contracts for bounded, trust-neutral compiled research context."""

from __future__ import annotations

from brain.v5.context_compiler import ContextBundle, estimate_context_tokens
from brain.v5.context_selection import NOT_SHOWN_REASON_CODES


def validate_context_bundle(bundle: ContextBundle) -> tuple[str, ...]:
    errors: list[str] = []
    if not bundle.session_id:
        errors.append("session_id must be non-empty")
    if not bundle.topic_id:
        errors.append("topic_id must be non-empty")
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
