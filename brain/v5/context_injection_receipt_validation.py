"""Strict JSON validation for context injection runtime receipts."""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from brain.v5.context_injection_contracts import (
    CONTEXT_INJECTION_PROFILE_BUDGETS,
    EFFECTIVE_PROFILES,
    INJECTION_STATUSES,
    ContextInjectionReceipt,
    hash_json,
)


def validate_context_injection_receipt_payload(payload: Any) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ("receipt must be a mapping",)
    errors: list[str] = []
    _validate_field_set(payload, errors)
    _validate_identity(payload, errors)
    _validate_trust_and_shapes(payload, errors)
    _validate_counts_and_budgets(payload, errors)
    _validate_lineage(payload, errors)
    _validate_delivery_status(payload, errors)
    _validate_fingerprint_chain(payload, errors)
    _validate_payload_hash(payload, errors)
    return tuple(errors)


def _validate_field_set(payload, errors):
    expected_fields = {field.name for field in fields(ContextInjectionReceipt)}
    actual_fields = set(payload)
    if actual_fields != expected_fields:
        unknown = sorted(
            actual_fields - expected_fields,
            key=lambda value: (type(value).__name__, repr(value)),
        )
        errors.append(
            "receipt field set must match schema"
            f"; missing={sorted(expected_fields - actual_fields)}"
            f"; unknown={unknown}"
        )


def _validate_identity(payload, errors):
    required_strings = (
        "receipt_id",
        "content_fingerprint",
        "receipt_payload_sha256",
        "namespace_sha256",
        "request_fingerprint",
        "workspace_identity",
        "host",
        "host_session_id",
        "event_id",
        "event_type",
        "logical_event_type",
        "session_id",
        "topic_id",
        "context_profile",
        "content_sha256",
        "created_at",
        "injection_status",
        "runtime_path",
    )
    for field_name in required_strings:
        if not isinstance(payload.get(field_name), str) or not payload[field_name]:
            errors.append(f"{field_name} must be a non-empty string")
    profile = payload.get("context_profile")
    if not isinstance(profile, str) or profile not in EFFECTIVE_PROFILES:
        errors.append("context_profile is unsupported")
    status = payload.get("injection_status")
    if not isinstance(status, str) or status not in INJECTION_STATUSES:
        errors.append("injection_status is unsupported")
    for field_name in (
        "namespace_sha256",
        "request_fingerprint",
        "content_fingerprint",
        "content_sha256",
        "receipt_payload_sha256",
    ):
        if not _is_sha256(payload.get(field_name)):
            errors.append(f"{field_name} must be a lowercase SHA-256 digest")
    receipt_id = payload.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.startswith(
        "context-injection-receipt:"
    ) or not _is_sha256(receipt_id.rsplit(":", 1)[-1]):
        errors.append("receipt_id must be a hash-bound context injection receipt id")
    revision = payload.get("receipt_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append("receipt_revision must be a positive integer")
    previous = payload.get("previous_receipt_id")
    if not isinstance(previous, str):
        errors.append("previous_receipt_id must be a string")
    elif revision == 1 and previous:
        errors.append("revision 1 must not declare previous_receipt_id")
    elif (
        isinstance(revision, int)
        and not isinstance(revision, bool)
        and revision > 1
        and (
            not previous.startswith("context-injection-receipt:")
            or not _is_sha256(previous.rsplit(":", 1)[-1])
        )
    ):
        errors.append("later revisions require a hash-bound previous_receipt_id")
    namespace = payload.get("namespace_sha256")
    expected_path = (
        f".aitp/runtime/context_injections/{namespace[:2]}/{namespace}.json"
        if _is_sha256(namespace)
        else ""
    )
    if payload.get("runtime_path") != expected_path:
        errors.append("runtime_path must match the hashed receipt namespace")


def _validate_trust_and_shapes(payload, errors):
    if payload.get("trust_effect") != "none":
        errors.append("trust_effect must be none")
    for field_name, expected in (
        ("orientation_only", True),
        ("summary_inputs_trusted", False),
        ("can_update_kernel_state", False),
        ("can_update_claim_trust", False),
    ):
        if payload.get(field_name) is not expected:
            errors.append(f"{field_name} must be {expected!r}")
    for field_name in ("dirty_families", "exact_refs", "selected_record_refs", "errors"):
        if not isinstance(payload.get(field_name), (list, tuple)):
            errors.append(f"{field_name} must be a list")
    for field_name in (
        "selected_family_state_tokens",
        "selected_family_content_tokens",
        "checked_scope",
    ):
        if not isinstance(payload.get(field_name), dict):
            errors.append(f"{field_name} must be a mapping")
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")


def _validate_counts_and_budgets(payload, errors):
    integer_fields = (
        "base_index_generation",
        "delta_generation",
        "max_tokens",
        "max_bytes",
        "byte_count",
        "estimated_tokens",
    )
    valid: dict[str, int] = {}
    for field_name in integer_fields:
        value = payload.get(field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{field_name} must be a non-negative integer")
        else:
            valid[field_name] = value
    profile = payload.get("context_profile")
    if isinstance(profile, str) and profile in CONTEXT_INJECTION_PROFILE_BUDGETS:
        budget = CONTEXT_INJECTION_PROFILE_BUDGETS[profile]
        max_tokens = valid.get("max_tokens")
        max_bytes = valid.get("max_bytes")
        estimated_tokens = valid.get("estimated_tokens")
        byte_count = valid.get("byte_count")
        if max_tokens is not None and not 64 <= max_tokens <= budget["max_tokens"]:
            errors.append("max_tokens must stay within the named profile budget")
        if max_bytes is not None and not 384 <= max_bytes <= budget["max_bytes"]:
            errors.append("max_bytes must stay within the named profile budget")
        if estimated_tokens is not None and max_tokens is not None and estimated_tokens > max_tokens:
            errors.append("estimated_tokens must not exceed max_tokens")
        if byte_count is not None and max_bytes is not None and byte_count > max_bytes:
            errors.append("byte_count must not exceed max_bytes")
    elif profile == "none" and any(
        payload.get(field_name) != 0
        for field_name in ("max_tokens", "max_bytes", "byte_count", "estimated_tokens")
    ):
        errors.append("ignored receipts must have zero budgets and counts")


def _validate_lineage(payload, errors):
    profile = payload.get("context_profile")
    if isinstance(profile, str) and profile in CONTEXT_INJECTION_PROFILE_BUDGETS:
        generation = payload.get("base_index_generation")
        if isinstance(generation, int) and not isinstance(generation, bool) and generation < 1:
            errors.append("active receipts require a positive base index generation")
        for field_name in ("base_index_content_hash", "canonical_watermark"):
            if not _is_sha256(payload.get(field_name)):
                errors.append(f"{field_name} must be a lowercase SHA-256 digest")
    for field_name in (
        "selected_family_state_tokens",
        "selected_family_content_tokens",
    ):
        mapping = payload.get(field_name)
        if isinstance(mapping, dict) and any(
            not isinstance(family, str)
            or not family
            or not _is_sha256(token)
            for family, token in mapping.items()
        ):
            errors.append(f"{field_name} must map family names to SHA-256 digests")


def _validate_delivery_status(payload, errors):
    status = payload.get("injection_status")
    attempt = payload.get("delivery_attempt_id")
    if not isinstance(attempt, str):
        errors.append("delivery_attempt_id must be a string")
        return
    if (
        isinstance(status, str)
        and status in {"delivery_started", "injected"}
        and not _is_sha256(attempt)
    ):
        errors.append("started or injected receipts require a delivery attempt digest")
    if (
        isinstance(status, str)
        and status in {"prepared", "ignored_not_research_relevant"}
        and attempt
    ):
        errors.append("prepared or ignored receipts must not declare a delivery attempt")


def _validate_fingerprint_chain(payload, errors):
    content_basis = {
        "namespace_sha256": payload.get("namespace_sha256"),
        "request_fingerprint": payload.get("request_fingerprint"),
        "selected_family_state_tokens": payload.get("selected_family_state_tokens"),
        "selected_family_content_tokens": payload.get("selected_family_content_tokens"),
        "dirty_families": payload.get("dirty_families"),
        "checked_scope": payload.get("checked_scope"),
        "selected_record_refs": payload.get("selected_record_refs"),
        "errors": payload.get("errors"),
        "content_sha256": payload.get("content_sha256"),
    }
    try:
        expected_content = hash_json(content_basis)
    except (TypeError, ValueError):
        errors.append("content fingerprint basis must be finite JSON")
    else:
        if payload.get("content_fingerprint") != expected_content:
            errors.append("content_fingerprint does not match the receipt content basis")
    instance_basis = {
        "namespace_sha256": payload.get("namespace_sha256"),
        "content_fingerprint": payload.get("content_fingerprint"),
        "injection_status": payload.get("injection_status"),
        "delivery_attempt_id": payload.get("delivery_attempt_id"),
        "previous_receipt_id": payload.get("previous_receipt_id"),
        "receipt_revision": payload.get("receipt_revision"),
    }
    try:
        expected_id = hash_json(instance_basis)
    except (TypeError, ValueError):
        errors.append("receipt identity basis must be finite JSON")
    else:
        if payload.get("receipt_id") != f"context-injection-receipt:{expected_id}":
            errors.append("receipt_id does not match the receipt instance basis")


def _validate_payload_hash(payload, errors):
    payload_hash = payload.get("receipt_payload_sha256")
    if not _is_sha256(payload_hash):
        return
    basis = dict(payload)
    basis["receipt_payload_sha256"] = ""
    try:
        expected = hash_json(basis)
    except (TypeError, ValueError):
        errors.append("receipt payload must be finite JSON")
    else:
        if expected != payload_hash:
            errors.append("receipt payload SHA-256 mismatch")


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )
