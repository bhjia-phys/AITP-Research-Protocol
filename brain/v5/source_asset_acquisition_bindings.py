"""Policy bindings shared by source-asset acquisition adapters."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from brain.v5.record_envelope import RecordActor
from brain.v5.source_acquisition import (
    record_source_acquisition_decision,
    record_source_acquisition_receipt,
    resolve_source_acquisition_for_source_asset,
)


def source_acquisition_binding(
    source_url: str,
    source_metadata: dict[str, Any],
    metadata: dict[str, Any] | None,
) -> dict[str, str]:
    supplied = dict(metadata or {})
    stable_identifier = str(
        supplied.get("identifier_dedup_key")
        or supplied.get("doi")
        or supplied.get("arxiv_id")
        or source_metadata.get("arxiv_id")
        or ""
    ).strip()
    return {
        "dedup_key": stable_identifier or f"uri:{source_url}",
        "policy_basis": str(
            supplied.get("acquisition_policy_basis") or "explicit_pdf_acquisition_request"
        ),
        "access_disposition": str(
            supplied.get("access_license_disposition") or "not_independently_verified"
        ),
        "storage_permission": str(
            supplied.get("storage_permission") or "private_topic_store_authorized_by_request"
        ),
        "connector_id": str(source_metadata.get("source_scheme") or "direct"),
        "collector_id": "aitp_v5_acquire_pdf_source_asset",
    }


def source_acquisition_actor() -> RecordActor:
    return RecordActor(
        actor_type="tool",
        actor_id="aitp_v5_acquire_pdf_source_asset",
        host="aitp-v5",
    )


def record_pdf_acquisition_decision(
    ws,
    *,
    topic_id: str,
    claim_id: str,
    source_url: str,
    source_metadata: dict[str, Any],
    metadata: dict[str, Any] | None,
    decided_at: str,
    action: str = "allow",
):
    binding = source_acquisition_binding(source_url, source_metadata, metadata)
    if action == "deny":
        binding.update({
            "policy_basis": "source_url_rejected_by_acquisition_policy",
            "access_disposition": "not_acquired",
            "storage_permission": "forbidden",
        })
    capture = record_source_acquisition_decision(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        canonical_uri=source_url,
        action=action,
        decided_at=decided_at,
        actor=source_acquisition_actor(),
        **binding,
    )
    return binding, capture


def record_pdf_acquisition_receipt(
    ws,
    *,
    topic_id: str,
    claim_id: str,
    source_url: str,
    binding: dict[str, str],
    decision_capture,
    status: str,
    acquired_at: str,
    errors: list[str],
    byte_sha256: str = "",
    byte_length: int = 0,
    stored_uri: str = "",
):
    capture = record_source_acquisition_receipt(
        ws,
        topic_id=topic_id,
        claim_id=claim_id,
        decision_ref=decision_capture.pinned_ref,
        canonical_uri=source_url,
        dedup_key=binding["dedup_key"],
        status=status,
        byte_sha256=byte_sha256,
        hash_algorithm="sha256" if status == "succeeded" else "",
        byte_length=byte_length,
        stored_uri=stored_uri,
        connector_id=binding["connector_id"],
        collector_id=binding["collector_id"],
        acquired_at=acquired_at,
        errors=errors,
        actor=source_acquisition_actor(),
    )
    if status == "succeeded":
        resolve_source_acquisition_for_source_asset(ws, capture.pinned_ref)
    return capture


def source_acquisition_metadata(
    decision_capture,
    receipt_capture,
    *,
    acquisition_state: str,
    eligible: bool,
) -> dict[str, Any]:
    return {
        "acquisition_state": acquisition_state,
        "source_acquisition_decision_ref": asdict(decision_capture.pinned_ref),
        "source_acquisition_receipt_ref": asdict(receipt_capture.pinned_ref),
        "access_license_disposition": decision_capture.record.access_disposition,
        "storage_permission": decision_capture.record.storage_permission,
        "shelf_eligible": eligible,
        "reconstruction_eligible": eligible,
    }
