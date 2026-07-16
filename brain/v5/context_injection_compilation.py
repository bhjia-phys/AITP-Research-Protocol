"""Context compilation and receipt fingerprinting for host injection."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib

from brain.v5.context_compiler import ContextRequest, compile_research_context
from brain.v5.context_compiler_contracts import validate_context_bundle
from brain.v5.context_injection_contracts import (
    CONTEXT_INJECTION_PROFILE_BUDGETS,
    ContextInjectionError,
    ContextInjectionReceipt,
    ContextInjectionRequest,
    hash_json,
    seal_context_injection_receipt,
    workspace_identity,
)
from brain.v5.context_injection_storage import ResolvedLifecycle, namespace_digest
from brain.v5.query_index import (
    current_family_content_watermark,
    current_family_state_token,
)
from brain.v5.research_retrieval import QuerySnapshotSession


def compile_context_injection(ws, request, profile):
    budget = CONTEXT_INJECTION_PROFILE_BUDGETS[profile]
    max_tokens = request.max_tokens or budget["max_tokens"]
    max_bytes = request.max_bytes or budget["max_bytes"]
    if max_tokens > budget["max_tokens"] or max_bytes > budget["max_bytes"]:
        raise ValueError(
            f"{profile} profile budget cannot exceed "
            f"{budget['max_tokens']} tokens/{budget['max_bytes']} bytes"
        )
    context_request = ContextRequest(
        session_id=request.session_id,
        objective_text=request.objective_text,
        user_goal=request.user_goal,
        topic_id=request.topic_id,
        disclosure_level=profile,
        focus_set_ref=request.focus_set_ref,
        program_id=request.program_id,
        include_cross_topic_discovery=request.include_cross_topic_discovery,
        recall_audit_ref=request.recall_audit_ref,
        exact_refs=request.exact_refs,
        exact_pins=request.exact_pins,
        knowledge_request=request.knowledge_request,
        skill_request=request.skill_request,
        families=request.families,
        max_tokens=max_tokens,
        max_bytes=max_bytes,
        record_limit=request.record_limit or (40 if profile == "startup_orientation" else 160),
        candidate_limit=request.candidate_limit or (6 if profile == "startup_orientation" else 12),
        record_offset=request.record_offset,
    )
    query_session = QuerySnapshotSession(
        allow_pointer_bound_cache=profile == "startup_orientation"
    )
    bundle = compile_research_context(ws, context_request, query_session=query_session)
    contract_errors = validate_context_bundle(bundle)
    if contract_errors:
        raise ContextInjectionError(
            "compiled context violates its contract: " + "; ".join(contract_errors)
        )
    if query_session.snapshot is None:
        raise ContextInjectionError("context compiler did not expose its effective index snapshot")
    return bundle, query_session.snapshot, max_tokens, max_bytes


def build_compiled_receipt(
    ws,
    request: ContextInjectionRequest,
    lifecycle: ResolvedLifecycle,
    path,
    *,
    bundle,
    snapshot,
    max_tokens: int,
    max_bytes: int,
    status: str,
    existing: ContextInjectionReceipt | None,
    delivery_attempt_id: str = "",
) -> ContextInjectionReceipt:
    checked_families = tuple(
        sorted(set(bundle.coverage.get("checked_families") or request.families))
    )
    state_tokens, content_tokens = _selected_family_tokens(
        ws, snapshot, checked_families
    )
    dirty = sorted(set(snapshot.dirty_families).intersection(checked_families))
    checked_scope = _checked_scope(bundle, checked_families)
    content_sha256 = hashlib.sha256(bundle.markdown.encode("utf-8")).hexdigest()
    request_fingerprint = _request_fingerprint(
        request, lifecycle.profile, max_tokens=max_tokens, max_bytes=max_bytes
    )
    namespace = namespace_digest(ws, request, lifecycle.profile)
    content_fingerprint = hash_json(
        {
            "namespace_sha256": namespace,
            "request_fingerprint": request_fingerprint,
            "selected_family_state_tokens": state_tokens,
            "selected_family_content_tokens": content_tokens,
            "dirty_families": dirty,
            "checked_scope": checked_scope,
            "selected_record_refs": list(bundle.record_refs),
            "errors": list(bundle.read_errors),
            "content_sha256": content_sha256,
        }
    )
    revision = existing.receipt_revision + 1 if existing is not None else 1
    previous_receipt_id = existing.receipt_id if existing is not None else ""
    identity = hash_json(
        {
            "namespace_sha256": namespace,
            "content_fingerprint": content_fingerprint,
            "injection_status": status,
            "delivery_attempt_id": delivery_attempt_id,
            "previous_receipt_id": previous_receipt_id,
            "receipt_revision": revision,
        }
    )
    receipt = ContextInjectionReceipt(
        schema_version=1,
        receipt_id=f"context-injection-receipt:{identity}",
        content_fingerprint=content_fingerprint,
        receipt_revision=revision,
        receipt_payload_sha256="",
        namespace_sha256=namespace,
        request_fingerprint=request_fingerprint,
        workspace_identity=workspace_identity(ws),
        host=request.host,
        host_session_id=request.host_session_id,
        event_id=request.event_id,
        event_type=request.event_type,
        logical_event_type=lifecycle.logical_event_type,
        session_id=request.session_id,
        topic_id=bundle.topic_id,
        focus_set_ref=bundle.focus_set_ref,
        context_profile=lifecycle.profile,
        base_index_generation=int(snapshot.manifest.generation),
        base_index_content_hash=str(snapshot.manifest.content_hash),
        delta_generation=int(snapshot.delta_generation),
        selected_family_state_tokens=state_tokens,
        selected_family_content_tokens=content_tokens,
        dirty_families=dirty,
        canonical_watermark=str(snapshot.manifest.canonical_watermark),
        exact_refs=list(request.exact_refs),
        selected_record_refs=list(bundle.record_refs),
        checked_scope=checked_scope,
        errors=list(bundle.read_errors),
        max_tokens=max_tokens,
        max_bytes=max_bytes,
        byte_count=bundle.byte_count,
        estimated_tokens=bundle.estimated_tokens,
        content_sha256=content_sha256,
        created_at=datetime.now(timezone.utc).isoformat(),
        injection_status=status,
        delivery_attempt_id=delivery_attempt_id,
        runtime_path=path.relative_to(ws.base.resolve()).as_posix(),
        previous_receipt_id=previous_receipt_id,
    )
    return seal_context_injection_receipt(receipt)


def build_ignored_receipt(
    ws,
    request,
    lifecycle,
    path,
    *,
    existing: ContextInjectionReceipt | None,
):
    empty_hash = hashlib.sha256(b"").hexdigest()
    request_fingerprint = _request_fingerprint(
        request, lifecycle.profile, max_tokens=0, max_bytes=0
    )
    namespace = namespace_digest(ws, request, lifecycle.profile)
    content_fingerprint = hash_json(
        {
            "namespace_sha256": namespace,
            "request_fingerprint": request_fingerprint,
            "selected_family_state_tokens": {},
            "selected_family_content_tokens": {},
            "dirty_families": [],
            "checked_scope": {
                "checked_families": [],
                "primary_topic_id": request.topic_id,
            },
            "selected_record_refs": [],
            "errors": [],
            "content_sha256": empty_hash,
        }
    )
    revision = existing.receipt_revision + 1 if existing is not None else 1
    previous_receipt_id = existing.receipt_id if existing is not None else ""
    identity = hash_json(
        {
            "namespace_sha256": namespace,
            "content_fingerprint": content_fingerprint,
            "injection_status": "ignored_not_research_relevant",
            "delivery_attempt_id": "",
            "previous_receipt_id": previous_receipt_id,
            "receipt_revision": revision,
        }
    )
    receipt = ContextInjectionReceipt(
        schema_version=1,
        receipt_id=f"context-injection-receipt:{identity}",
        content_fingerprint=content_fingerprint,
        receipt_revision=revision,
        receipt_payload_sha256="",
        namespace_sha256=namespace,
        request_fingerprint=request_fingerprint,
        workspace_identity=workspace_identity(ws),
        host=request.host,
        host_session_id=request.host_session_id,
        event_id=request.event_id,
        event_type=request.event_type,
        logical_event_type=lifecycle.logical_event_type,
        session_id=request.session_id,
        topic_id=request.topic_id,
        focus_set_ref=request.focus_set_ref,
        context_profile="none",
        base_index_generation=0,
        base_index_content_hash="",
        delta_generation=0,
        selected_family_state_tokens={},
        selected_family_content_tokens={},
        dirty_families=[],
        canonical_watermark="",
        exact_refs=list(request.exact_refs),
        selected_record_refs=[],
        checked_scope={"checked_families": [], "primary_topic_id": request.topic_id},
        errors=[],
        max_tokens=0,
        max_bytes=0,
        byte_count=0,
        estimated_tokens=0,
        content_sha256=empty_hash,
        created_at=datetime.now(timezone.utc).isoformat(),
        injection_status="ignored_not_research_relevant",
        delivery_attempt_id="",
        runtime_path=path.relative_to(ws.base.resolve()).as_posix(),
        previous_receipt_id=previous_receipt_id,
    )
    return seal_context_injection_receipt(receipt)


def _selected_family_tokens(ws, snapshot, checked_families):
    state_tokens: dict[str, str] = {}
    content_tokens: dict[str, str] = {}
    for family in checked_families:
        current_state = current_family_state_token(ws, family)
        state_tokens[family] = current_state
        if current_state == snapshot.family_state_tokens.get(family, ""):
            content_tokens[family] = snapshot.family_content_watermarks.get(family, "")
        else:
            content_tokens[family] = current_family_content_watermark(ws, family)
    return state_tokens, content_tokens


def _checked_scope(bundle, checked_families):
    scope = dict(bundle.scope)
    return {
        "primary_topic_id": bundle.topic_id,
        "focus_set_ref": bundle.focus_set_ref,
        "program_id": bundle.program_id,
        "allowed_topic_ids": list(scope.get("allowed_topic_ids") or ()),
        "supporting_refs": list(scope.get("supporting_refs") or ()),
        "excluded_refs": list(scope.get("excluded_refs") or ()),
        "unresolved_refs": list(scope.get("unresolved_refs") or ()),
        "blocked_explicit_refs": list(scope.get("blocked_explicit_refs") or ()),
        "checked_families": list(checked_families),
        "not_checked_families": list(bundle.not_checked_families),
        "partial": bundle.partial,
        "index_status": bundle.index_status,
    }


def _request_fingerprint(request, profile, *, max_tokens, max_bytes):
    payload = asdict(request)
    payload["context_profile"] = profile
    payload["max_tokens"] = max_tokens
    payload["max_bytes"] = max_bytes
    return hash_json(payload)
