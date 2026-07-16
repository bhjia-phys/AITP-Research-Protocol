"""Bounded, auditable context injection shared by host adapters."""

from __future__ import annotations

from typing import Callable

from brain.v5.context_injection_compilation import (
    build_compiled_receipt,
    build_ignored_receipt,
    compile_context_injection,
)
from brain.v5.context_injection_contracts import (
    CONTEXT_INJECTION_PROFILE_BUDGETS,
    ContextInjectionDeliveryUncertainError,
    ContextInjectionError,
    ContextInjectionReceipt,
    ContextInjectionRequest,
    hash_json,
    transition_context_injection_receipt,
    validate_context_injection_receipt_payload,
)
from brain.v5.context_injection_storage import (
    context_injection_receipt_path,
    host_session_lock_path,
    persist_or_reuse,
    read_existing_receipt,
    reconcile_lifecycle_state,
    require_requested_profile,
    resolve_lifecycle,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_locking import acquire_ranked_lock


def prepare_context_injection(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
    *,
    deliver: Callable[[str], None] | None = None,
) -> ContextInjectionReceipt:
    """Compile once, deliver ephemerally, and persist only an audit receipt."""

    if not isinstance(request, ContextInjectionRequest):
        raise TypeError("request must be a ContextInjectionRequest")
    if deliver is not None and not callable(deliver):
        raise TypeError("deliver must be callable")
    with acquire_ranked_lock(
        ws,
        "runtime-transaction",
        timeout_seconds=10.0,
        lock_path=host_session_lock_path(ws, request),
    ):
        lifecycle = resolve_lifecycle(ws, request)
        require_requested_profile(request, lifecycle.profile)
        path = context_injection_receipt_path(ws, request, lifecycle.profile)
        existing = read_existing_receipt(ws, path)
        if lifecycle.profile == "none":
            receipt = build_ignored_receipt(
                ws,
                request,
                lifecycle,
                path,
                existing=existing,
            )
            if (
                existing is not None
                and existing.content_fingerprint == receipt.content_fingerprint
            ):
                reconcile_lifecycle_state(ws, request, lifecycle)
                return existing
            return persist_or_reuse(
                ws,
                path,
                receipt,
                existing=existing,
                request=request,
                lifecycle=lifecycle,
            )
        bundle, snapshot, max_tokens, max_bytes = compile_context_injection(
            ws, request, lifecycle.profile
        )
        receipt = build_compiled_receipt(
            ws,
            request,
            lifecycle,
            path,
            bundle=bundle,
            snapshot=snapshot,
            max_tokens=max_tokens,
            max_bytes=max_bytes,
            status="prepared",
            existing=existing,
        )
        if existing is not None and existing.content_fingerprint == receipt.content_fingerprint:
            reconcile_lifecycle_state(ws, request, lifecycle)
            receipt = existing
        else:
            if existing is not None and existing.injection_status == "delivery_started":
                raise ContextInjectionDeliveryUncertainError(
                    "delivery outcome is uncertain; acknowledge the active attempt "
                    "before replacing its context"
                )
            receipt = persist_or_reuse(
                ws,
                path,
                receipt,
                existing=existing,
                request=request,
                lifecycle=lifecycle,
            )
        if deliver is None or receipt.injection_status == "injected":
            return receipt
        if receipt.injection_status == "delivery_started":
            raise ContextInjectionDeliveryUncertainError(
                "delivery outcome is uncertain; acknowledge the active attempt "
                "before replay"
            )
        if receipt.injection_status != "prepared":
            raise ContextInjectionError(
                f"context injection cannot deliver from {receipt.injection_status!r}"
            )
        attempt_id = hash_json(
            {
                "receipt_id": receipt.receipt_id,
                "content_fingerprint": receipt.content_fingerprint,
                "operation": "deliver-context-injection",
            }
        )
        started = transition_context_injection_receipt(
            receipt,
            injection_status="delivery_started",
            delivery_attempt_id=attempt_id,
        )
        started = persist_or_reuse(
            ws,
            path,
            started,
            existing=receipt,
            request=request,
            lifecycle=lifecycle,
        )
        deliver(bundle.markdown)
        injected = transition_context_injection_receipt(
            started,
            injection_status="injected",
            delivery_attempt_id=attempt_id,
        )
        return persist_or_reuse(
            ws,
            path,
            injected,
            existing=started,
            request=request,
            lifecycle=lifecycle,
        )


def acknowledge_context_injection_delivery(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
    *,
    delivery_attempt_id: str,
    delivered: bool,
) -> ContextInjectionReceipt:
    """Resolve an uncertain host delivery without silently retrying it."""

    if not isinstance(request, ContextInjectionRequest):
        raise TypeError("request must be a ContextInjectionRequest")
    if not isinstance(delivered, bool):
        raise TypeError("delivered must be a boolean")
    with acquire_ranked_lock(
        ws,
        "runtime-transaction",
        timeout_seconds=10.0,
        lock_path=host_session_lock_path(ws, request),
    ):
        lifecycle = resolve_lifecycle(ws, request)
        require_requested_profile(request, lifecycle.profile)
        path = context_injection_receipt_path(ws, request, lifecycle.profile)
        existing = read_existing_receipt(ws, path)
        if existing is None or existing.injection_status != "delivery_started":
            raise ContextInjectionError("no uncertain context injection delivery is active")
        if existing.delivery_attempt_id != delivery_attempt_id:
            raise ContextInjectionError("delivery attempt identity mismatch")
        receipt = transition_context_injection_receipt(
            existing,
            injection_status="injected" if delivered else "prepared",
            delivery_attempt_id=delivery_attempt_id if delivered else "",
        )
        return persist_or_reuse(
            ws,
            path,
            receipt,
            existing=existing,
            request=request,
            lifecycle=lifecycle,
        )


__all__ = [
    "CONTEXT_INJECTION_PROFILE_BUDGETS",
    "ContextInjectionDeliveryUncertainError",
    "ContextInjectionError",
    "ContextInjectionReceipt",
    "ContextInjectionRequest",
    "acknowledge_context_injection_delivery",
    "context_injection_receipt_path",
    "prepare_context_injection",
    "validate_context_injection_receipt_payload",
]
