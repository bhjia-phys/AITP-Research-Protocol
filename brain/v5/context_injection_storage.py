"""Hashed runtime storage and first-relevant-turn state for context injection."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path

from brain.v5.context_injection_contracts import (
    EFFECTIVE_PROFILES,
    ContextInjectionError,
    ContextInjectionReceipt,
    ContextInjectionRequest,
    hash_json,
    validate_context_injection_receipt_payload,
    workspace_identity,
)
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths


@dataclass(frozen=True)
class ResolvedLifecycle:
    profile: str
    logical_event_type: str
    event_key: str


def context_injection_receipt_path(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
    context_profile: str,
) -> Path:
    if context_profile not in EFFECTIVE_PROFILES:
        raise ValueError("context_profile is not an effective injection profile")
    digest = namespace_digest(ws, request, context_profile)
    root = _runtime_subroot(ws, "context_injections")
    return _contained_digest_path(root, digest, "context injection receipt")


def host_session_lock_path(ws: WorkspacePaths, request: ContextInjectionRequest) -> Path:
    root = _runtime_subroot(ws, "locks/context-injections")
    return _contained_digest_path(root, _session_key(ws, request), "context injection lock", ".lock")


def resolve_lifecycle(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
) -> ResolvedLifecycle:
    event_key = _event_key(ws, request)
    event_path = _event_resolution_path(ws, event_key)
    if event_path.exists():
        payload = _read_runtime_json(event_path, "context injection event resolution")
        if payload.get("event_key") != event_key:
            raise ContextInjectionError("context injection event resolution identity mismatch")
        if payload.get("research_relevant") is not request.research_relevant:
            raise ContextInjectionError("host event research relevance changed across replay")
        return ResolvedLifecycle(
            profile=str(payload["context_profile"]),
            logical_event_type=str(payload["logical_event_type"]),
            event_key=event_key,
        )
    if not request.research_relevant:
        return ResolvedLifecycle("none", request.event_type, event_key)
    state = _read_session_state(ws, request)
    if request.event_type == "SessionStart":
        return ResolvedLifecycle("startup_orientation", "SessionStart", event_key)
    if not state.get("first_relevant_event_key") and not request.host_supports_session_start:
        return ResolvedLifecycle("startup_orientation", "ResearchTurnStart", event_key)
    return ResolvedLifecycle("normal_research", request.event_type, event_key)


def require_requested_profile(
    request: ContextInjectionRequest,
    effective_profile: str,
) -> None:
    if (
        effective_profile != "none"
        and request.context_profile != "auto"
        and request.context_profile != effective_profile
    ):
        raise ValueError(
            f"requested profile {request.context_profile!r} conflicts with "
            f"lifecycle-selected profile {effective_profile!r}"
        )


def read_existing_receipt(
    ws: WorkspacePaths,
    path: Path,
) -> ContextInjectionReceipt | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_context_injection_receipt_payload(payload)
        if errors:
            raise ValueError("; ".join(errors))
        receipt = ContextInjectionReceipt(**payload)
    except Exception as exc:  # noqa: BLE001 - never replace an unreadable audit receipt.
        raise ContextInjectionError(
            f"cannot read existing context injection receipt: {exc}"
        ) from exc
    resolved = path.resolve(strict=False)
    history_root = _runtime_subroot(ws, "context_injections/history")
    if resolved.is_relative_to(history_root):
        digest = receipt.receipt_id.rsplit(":", 1)[-1]
        expected = _contained_digest_path(
            history_root,
            digest,
            "context injection history",
        )
    else:
        expected = (ws.base / receipt.runtime_path).resolve(strict=False)
    if resolved != expected:
        raise ContextInjectionError(
            "cannot read existing context injection receipt: runtime_path mismatch"
        )
    return receipt


def persist_or_reuse(
    ws: WorkspacePaths,
    path: Path,
    receipt: ContextInjectionReceipt,
    *,
    existing: ContextInjectionReceipt | None,
    request: ContextInjectionRequest,
    lifecycle: ResolvedLifecycle,
) -> ContextInjectionReceipt:
    if existing is not None and existing.receipt_id == receipt.receipt_id:
        reconcile_lifecycle_state(ws, request, lifecycle)
        return existing
    if existing is not None:
        history = _history_path(ws, existing.receipt_id)
        if history.exists():
            if read_existing_receipt(ws, history) != existing:
                raise ContextInjectionError("context injection history identity mismatch")
        else:
            write_text_atomic(history, _serialize_receipt(existing))
    write_text_atomic(path, _serialize_receipt(receipt))
    reconcile_lifecycle_state(ws, request, lifecycle)
    return receipt


def reconcile_lifecycle_state(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
    lifecycle: ResolvedLifecycle,
) -> None:
    """Idempotently repair event/session state after an interrupted receipt write."""

    _persist_lifecycle_state(ws, request, lifecycle)


def namespace_digest(
    ws: WorkspacePaths,
    request: ContextInjectionRequest,
    profile: str,
) -> str:
    return hash_json(
        {
            "workspace_identity": workspace_identity(ws),
            "host": request.host,
            "host_session_id": request.host_session_id,
            "session_id": request.session_id,
            "topic_id": request.topic_id,
            "focus_set_ref": request.focus_set_ref,
            "context_profile": profile,
            "event_id": request.event_id,
            "event_type": request.event_type,
        }
    )


def _persist_lifecycle_state(ws, request, lifecycle):
    event_payload = {
        "schema_version": 1,
        "event_key": lifecycle.event_key,
        "host": request.host,
        "host_session_id": request.host_session_id,
        "session_id": request.session_id,
        "event_id": request.event_id,
        "event_type": request.event_type,
        "research_relevant": request.research_relevant,
        "context_profile": lifecycle.profile,
        "logical_event_type": lifecycle.logical_event_type,
    }
    write_text_atomic(
        _event_resolution_path(ws, lifecycle.event_key),
        _serialize_runtime_payload(event_payload),
    )
    if lifecycle.profile == "none":
        return
    state_path = _session_state_path(ws, request)
    state = _read_session_state(ws, request)
    if not state.get("first_relevant_event_key"):
        state["first_relevant_event_key"] = lifecycle.event_key
        state["first_relevant_event_id"] = request.event_id
        state["first_relevant_profile"] = lifecycle.profile
        write_text_atomic(state_path, _serialize_runtime_payload(state))


def _read_session_state(ws, request):
    path = _session_state_path(ws, request)
    if not path.exists():
        return {
            "schema_version": 1,
            "workspace_identity": workspace_identity(ws),
            "host": request.host,
            "host_session_id": request.host_session_id,
            "session_id": request.session_id,
            "first_relevant_event_key": "",
        }
    payload = _read_runtime_json(path, "context injection session state")
    expected = {
        "workspace_identity": workspace_identity(ws),
        "host": request.host,
        "host_session_id": request.host_session_id,
        "session_id": request.session_id,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise ContextInjectionError("context injection session state identity mismatch")
    return payload


def _event_key(ws, request):
    return hash_json(
        {
            "workspace_identity": workspace_identity(ws),
            "host": request.host,
            "host_session_id": request.host_session_id,
            "session_id": request.session_id,
            "event_id": request.event_id,
            "event_type": request.event_type,
        }
    )


def _session_key(ws, request):
    return hash_json(
        {
            "workspace_identity": workspace_identity(ws),
            "host": request.host,
            "host_session_id": request.host_session_id,
            "session_id": request.session_id,
        }
    )


def _event_resolution_path(ws, digest):
    root = _runtime_subroot(ws, "context_injections/events")
    return _contained_digest_path(root, digest, "context injection event")


def _session_state_path(ws, request):
    root = _runtime_subroot(ws, "context_injections/sessions")
    return _contained_digest_path(root, _session_key(ws, request), "context injection session")


def _history_path(ws, receipt_id):
    digest = receipt_id.rsplit(":", 1)[-1]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ContextInjectionError("context injection receipt id is not hash-bound")
    root = _runtime_subroot(ws, "context_injections/history")
    return _contained_digest_path(root, digest, "context injection history")


def _runtime_subroot(ws, relative):
    workspace_root = ws.root.resolve(strict=False)
    runtime_root = (ws.root / "runtime").resolve(strict=False)
    if not runtime_root.is_relative_to(workspace_root):
        raise ValueError("AITP runtime root escapes the workspace")
    root = (runtime_root / Path(relative)).resolve(strict=False)
    if not root.is_relative_to(runtime_root):
        raise ValueError("context injection runtime root escapes AITP runtime")
    return root


def _contained_digest_path(root, digest, label, suffix=".json"):
    path = (root / digest[:2] / f"{digest}{suffix}").resolve(strict=False)
    if not path.is_relative_to(root):
        raise ValueError(f"{label} path escapes AITP runtime")
    return path


def _read_runtime_json(path, label):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - runtime identity state is fail-closed.
        raise ContextInjectionError(f"cannot read {label}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ContextInjectionError(f"{label} is malformed")
    return payload


def _serialize_receipt(receipt):
    return _serialize_runtime_payload(asdict(receipt))


def _serialize_runtime_payload(payload):
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"
