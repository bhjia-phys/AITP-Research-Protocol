"""Allowlisted side-effect adapters and receipts for research moments."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from brain.v5.capability_registry import capability_specs
from brain.v5.markdown import write_text_atomic
from brain.v5.paths import WorkspacePaths
from brain.v5.query_index_locking import acquire_ranked_lock
from brain.v5.record_envelope import RecordActor
from brain.v5.research_moment_contracts import (
    MomentReceipt,
    ResearchEvent,
    ResearchMomentDecision,
    decision_fingerprint,
    deserialize_moment_receipt,
    normalize_decision,
    serialize_moment_receipt,
)
from brain.v5.research_moment_validation import (
    mapping,
    payload_refs,
    pinned_record_ref,
    unreadable_refs,
    workspace_identity,
)


class ResearchMomentApplicationError(RuntimeError):
    """Raised when a decision cannot cross its declared side-effect boundary."""


def apply_research_moment_decision(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
    *,
    actor: RecordActor,
) -> MomentReceipt:
    """Apply one allowlisted decision and persist an idempotent runtime receipt."""

    decision = normalize_decision(decision)
    _require_declared_effect(decision)
    _require_current_decision_identity(ws, decision)
    if datetime.fromisoformat(decision.expires_at) <= datetime.now(timezone.utc):
        raise ResearchMomentApplicationError("research moment decision has expired")
    path = research_moment_receipt_path(ws, decision.dedup_key)
    lock_path = (
        ws.root
        / "runtime"
        / "locks"
        / "research-moments"
        / f"{decision.dedup_key}.lock"
    )
    with acquire_ranked_lock(
        ws,
        "runtime-transaction",
        timeout_seconds=10.0,
        lock_path=lock_path,
    ):
        return _apply_research_moment_under_lock(
            ws,
            decision,
            actor=actor,
            path=path,
        )


def _apply_research_moment_under_lock(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
    *,
    actor: RecordActor,
    path: Path,
) -> MomentReceipt:
    if path.exists():
        try:
            existing = deserialize_moment_receipt(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - never overwrite a corrupt receipt.
            raise ResearchMomentApplicationError(f"cannot read existing moment receipt: {exc}") from exc
        if existing.decision_id != decision.decision_id:
            raise ResearchMomentApplicationError("moment receipt decision identity mismatch")
        return existing

    status = "ignored"
    record_refs: tuple[str, ...] = ()
    staging_refs: tuple[str, ...] = ()
    checkpoint_refs: tuple[str, ...] = ()
    handoff: dict[str, Any] = {}
    if decision.outcome == "block_until_prerequisites":
        status = "blocked"
    elif decision.outcome == "auto_capture_process":
        status, record_refs, handoff = _apply_process_decision(ws, decision)
    elif decision.outcome == "stage_semantic_candidate":
        staging_refs = _apply_semantic_staging(ws, decision)
        status = "staged"
    elif decision.outcome == "coalesce_for_review":
        record_refs = _apply_coalescing(ws, decision, actor=actor)
        status = "review_batch_ready"
    elif decision.outcome == "require_checkpoint":
        checkpoint_refs = _apply_checkpoint(ws, decision, actor=actor)
        status = "checkpoint_required"

    relative_path = path.relative_to(ws.base.resolve()).as_posix()
    receipt = MomentReceipt(
        receipt_id=f"moment-receipt:{decision.dedup_key}",
        decision_id=decision.decision_id,
        event_id=decision.event.event_id,
        outcome=decision.outcome,
        status=status,
        application_operation=decision.application_operation,
        application_effect=decision.declared_effect,
        runtime_path=relative_path,
        record_refs=tuple(record_refs),
        staging_refs=tuple(staging_refs),
        checkpoint_refs=tuple(checkpoint_refs),
        handoff=handoff,
        created_at=datetime.now(timezone.utc).isoformat(),
        trust_effect="none",
        can_update_claim_trust=False,
    )
    write_text_atomic(path, serialize_moment_receipt(receipt))
    return receipt


def research_moment_receipt_path(ws: WorkspacePaths, dedup_key: str) -> Path:
    if len(dedup_key) != 64 or any(char not in "0123456789abcdef" for char in dedup_key):
        raise ValueError("moment dedup_key must be a lowercase SHA-256 digest")
    workspace_root = ws.root.resolve()
    runtime_root = (ws.root / "runtime").resolve()
    if not runtime_root.is_relative_to(workspace_root):
        raise ValueError("AITP runtime root escapes the workspace")
    root = (ws.root / "runtime" / "research_moments").resolve()
    if not root.is_relative_to(runtime_root):
        raise ValueError("research moment runtime root escapes AITP runtime")
    path = (root / dedup_key[:2] / f"{dedup_key}.json").resolve()
    if not path.is_relative_to(root):
        raise ValueError("research moment receipt path escapes runtime root")
    return path


def _apply_process_decision(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
) -> tuple[str, tuple[str, ...], dict[str, Any]]:
    operation = decision.application_operation
    if operation == "exact_record_expansion":
        refs = _verify_refs(ws, decision.application_payload.get("record_refs", ()))
        return "verified", refs, {}
    if operation == "knowledge_build_discovery_request":
        request = _build_discovery_request(ws, decision.application_payload["discovery_spec"])
        handoff = {
            "request_id": request.request_id,
            "dedup_fingerprint": request.dedup_fingerprint,
            "topic_id": request.topic_id,
            "claim_id": request.claim_id,
            "connector_allowlist": list(request.connector_allowlist),
            "max_results": request.max_results,
            "timeout_seconds": request.timeout_seconds,
            "expires_at": request.expires_at,
            "orientation_only": True,
            "can_update_kernel_state": False,
            "can_update_claim_trust": False,
            "can_create_source_asset": False,
        }
        return "handoff_ready", (), handoff
    record_ref = _apply_capture_operation(
        ws,
        decision.event,
        operation,
        decision.application_payload.get("arguments", {}),
    )
    _verify_refs(ws, (record_ref,))
    return "captured", (record_ref,), {}


def _apply_capture_operation(
    ws: WorkspacePaths,
    event: ResearchEvent,
    operation: str,
    arguments: object,
) -> str:
    args = dict(mapping(arguments, "arguments"))
    audit = {
        "research_moment_event_id": event.event_id,
        "research_moment_source_event_id": event.source_event_id,
        "research_moment_host": event.host,
        "research_moment_host_session_id": event.host_session_id,
        "can_update_claim_trust": False,
    }
    if operation == "capture_source_asset_auto":
        from brain.v5.source_assets import capture_source_asset_from_local_path

        args["metadata"] = {**dict(args.get("metadata") or {}), **audit}
        record = capture_source_asset_from_local_path(ws, **args)
        return f"source_asset:{record.asset_id}"
    if operation == "capture_code_state_auto":
        from brain.v5.code import capture_code_state_from_git

        args["runtime_environment"] = {
            **dict(args.get("runtime_environment") or {}),
            **audit,
        }
        record = capture_code_state_from_git(ws, **args)
        return f"code_state:{record.code_state_id}"
    if operation == "capture_tool_run_auto":
        from brain.v5.tools import capture_tool_run_from_local_path

        args["environment"] = {**dict(args.get("environment") or {}), **audit}
        record = capture_tool_run_from_local_path(ws, **args)
        return f"tool_run:{record.run_id}"
    if operation == "attach_artifact_auto":
        from brain.v5.research_state import attach_artifact_from_local_path

        args["metadata"] = {**dict(args.get("metadata") or {}), **audit}
        record = attach_artifact_from_local_path(ws, **args)
        return f"artifact:{record.artifact_id}"
    raise ResearchMomentApplicationError(f"unsupported process capture operation: {operation}")


def _apply_semantic_staging(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
) -> tuple[str, ...]:
    from brain.v5.recording_batch_contracts import StagedCandidate
    from brain.v5.recording_batches import stage_recording_candidate

    raw = dict(mapping(decision.application_payload.get("candidate"), "candidate"))
    candidate = StagedCandidate(
        staging_id="",
        session_id=decision.event.session_id,
        topic_id=decision.event.topic_id,
        candidate_kind=str(raw["candidate_kind"]),
        semantic_key=str(raw["semantic_key"]),
        summary=str(raw["summary"]),
        payload=dict(raw["payload"]),
        source_refs=tuple(raw["source_refs"]),
        source_event_refs=(f"event:{decision.event.event_id}",),
        missing_prerequisites=tuple(raw.get("missing_prerequisites") or ()),
        dedup_key="",
        created_at=decision.event.occurred_at,
        expires_at=str(raw["expires_at"]),
    )
    staged = stage_recording_candidate(ws, candidate)
    return (f"staged_candidate:{staged.staging_id}",)


def _apply_coalescing(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
    *,
    actor: RecordActor,
) -> tuple[str, ...]:
    from brain.v5.recording_batches import coalesce_recording_batch

    result = coalesce_recording_batch(
        ws,
        decision.event.session_id,
        str(decision.application_payload["milestone_id"]),
        actor=actor,
    )
    return (result.record_ref,)


def _apply_checkpoint(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
    *,
    actor: RecordActor,
) -> tuple[str, ...]:
    from brain.v5.checkpoints import request_human_checkpoint

    payload = decision.application_payload
    record = request_human_checkpoint(
        ws,
        topic_id=decision.event.topic_id,
        claim_id=str(payload.get("claim_id") or ""),
        reason=str(payload.get("reason") or ""),
        requested_by=f"{actor.host}:{actor.actor_id}",
        options=list(payload.get("options") or ()),
    )
    return (f"human_checkpoint:{record.checkpoint_id}",)


def _build_discovery_request(ws: WorkspacePaths, raw_spec: object):
    from brain.v5.literature_discovery import build_literature_discovery_request
    from brain.v5.literature_discovery_models import LiteratureDiscoverySpec

    raw = dict(mapping(raw_spec, "discovery_spec"))
    spec = LiteratureDiscoverySpec(
        gap_ref=pinned_record_ref(raw["gap_ref"]),
        prior_audit_ref=pinned_record_ref(raw["prior_audit_ref"]),
        framework=str(raw["framework"]),
        regime=str(raw["regime"]),
        focus_terms=tuple(raw.get("focus_terms") or ()),
        required_source_types=tuple(raw["required_source_types"]),
        connector_allowlist=tuple(raw["connector_allowlist"]),
        max_results=int(raw["max_results"]),
        timeout_seconds=int(raw["timeout_seconds"]),
        ttl_seconds=int(raw["ttl_seconds"]),
    )
    return build_literature_discovery_request(ws, spec)


def _require_current_decision_identity(
    ws: WorkspacePaths,
    decision: ResearchMomentDecision,
) -> None:
    expected = decision_fingerprint(
        workspace_identity(ws),
        decision.event,
        outcome=decision.outcome,
        reason_codes=decision.reason_codes,
        target_families=decision.target_families,
        minimum_refs=decision.minimum_refs,
        expires_at=decision.expires_at,
        verification_steps=decision.verification_steps,
        required_checkpoint_action=decision.required_checkpoint_action,
        blocked_action=decision.blocked_action,
        application_operation=decision.application_operation,
        application_payload=decision.application_payload,
        declared_effect=decision.declared_effect,
    )
    if decision.dedup_key != expected or decision.decision_id != f"research-moment-decision:{expected}":
        raise ResearchMomentApplicationError("research moment decision identity mismatch")


def _require_declared_effect(decision: ResearchMomentDecision) -> None:
    operation = decision.application_operation
    expected = "read_only"
    if operation:
        spec = capability_specs().get(operation)
        if spec is None:
            raise ResearchMomentApplicationError(
                f"application operation has no CapabilitySpec: {operation}"
            )
        expected = spec.state_effect
    if decision.declared_effect != expected:
        raise ResearchMomentApplicationError(
            f"declared effect {decision.declared_effect!r} differs from "
            f"CapabilitySpec effect {expected!r} for {operation or 'no-op'}"
        )


def _verify_refs(ws: WorkspacePaths, values: object) -> tuple[str, ...]:
    refs = payload_refs(values)
    missing = unreadable_refs(ws, refs)
    if missing:
        raise ResearchMomentApplicationError(
            "exact process refs are no longer readable: " + ", ".join(missing)
        )
    return refs
