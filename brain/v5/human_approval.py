"""Host-attested human approval receipts for trust-authorizing checkpoints."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from brain.v5.paths import WorkspacePaths


_APPROVAL_KEY_ENV = "AITP_HUMAN_APPROVAL_HMAC_KEY_B64"
_RECEIPT_VERSION = "v1"
_SIGNATURE_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
_RECEIPT_HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class HumanApprovalVerification:
    decision_verified: bool
    method: str
    receipt_hash: str
    nonce: str
    can_authorize_trust: bool


def checkpoint_can_authorize_trust(checkpoint: Any) -> bool:
    """Return whether persisted receipt metadata can authorize a trust action.

    ``can_authorize_trust`` is not an authority bit by itself. Consumers must
    require the complete production verifier shape so schema-v1 records or
    hand-built booleans remain trust-neutral.
    """

    return bool(
        getattr(checkpoint, "status", "") == "decided"
        and getattr(checkpoint, "decision_verified", False) is True
        and getattr(checkpoint, "can_authorize_trust", False) is True
        and getattr(checkpoint, "decision_verification", "") == "hmac_sha256_v1"
        and _RECEIPT_HASH_PATTERN.fullmatch(
            str(getattr(checkpoint, "decision_receipt_hash", ""))
        )
        and str(getattr(checkpoint, "decision_receipt_nonce", "")).strip()
    )


def load_human_approval_receipt(
    ws: WorkspacePaths,
    checkpoint_id: str,
) -> dict[str, Any] | None:
    """Load a host-written runtime receipt without treating it as canonical state."""

    if Path(checkpoint_id).name != checkpoint_id or "/" in checkpoint_id or "\\" in checkpoint_id:
        raise ValueError("checkpoint_id is not safe for a human approval receipt path")
    path = ws.root / "runtime" / "human_approval_receipts" / f"{checkpoint_id}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid host human approval receipt: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("host human approval receipt must be a JSON object")
    return payload


def verify_human_approval_receipt(
    ws: WorkspacePaths,
    *,
    checkpoint_id: str,
    checkpoint_content_hash: str,
    decision: str,
    rationale: str,
    decided_by: str,
    approval_receipt: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> HumanApprovalVerification:
    """Verify a receipt that binds a human decision to the current checkpoint revision."""

    receipt = approval_receipt
    if receipt is None:
        receipt = load_human_approval_receipt(ws, checkpoint_id)
    if receipt is None:
        raise ValueError("a host-verified human approval receipt is required")
    if not isinstance(receipt, dict):
        raise ValueError("host human approval receipt must be a JSON object")

    required_strings = (
        "version",
        "checkpoint_id",
        "checkpoint_content_hash",
        "decision",
        "rationale_hash",
        "decided_by",
        "issued_at",
        "expires_at",
        "nonce",
        "signature",
    )
    for field in required_strings:
        value = receipt.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"host human approval receipt {field} must be a non-empty string")

    expected_fields = {
        "version": _RECEIPT_VERSION,
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": checkpoint_content_hash,
        "decision": decision,
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": decided_by,
    }
    for field, expected in expected_fields.items():
        if not hmac.compare_digest(str(receipt[field]), expected):
            raise ValueError(f"host human approval receipt {field} does not match the checkpoint decision")

    issued_at = _parse_timestamp(str(receipt["issued_at"]), "issued_at")
    expires_at = _parse_timestamp(str(receipt["expires_at"]), "expires_at")
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    if issued_at > current_time + timedelta(minutes=5):
        raise ValueError("host human approval receipt issued_at is in the future")
    if expires_at <= issued_at:
        raise ValueError("host human approval receipt expires_at must be after issued_at")
    if expires_at <= current_time:
        raise ValueError("host human approval receipt has expired")

    signature = str(receipt["signature"])
    if not _SIGNATURE_PATTERN.fullmatch(signature):
        raise ValueError("host human approval receipt signature must be a SHA-256 hex digest")
    secret_key = _load_hmac_key()
    signed_payload = {
        field: value for field, value in receipt.items() if field != "signature"
    }
    encoded_payload = _canonical_json(signed_payload)
    expected_signature = hmac.new(
        secret_key,
        encoded_payload,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature.lower(), expected_signature):
        raise ValueError("host human approval receipt signature is invalid")

    receipt_hash = hashlib.sha256(_canonical_json(receipt)).hexdigest()
    return HumanApprovalVerification(
        decision_verified=True,
        method="hmac_sha256_v1",
        receipt_hash=f"sha256:{receipt_hash}",
        nonce=str(receipt["nonce"]),
        can_authorize_trust=True,
    )


def _load_hmac_key() -> bytes:
    encoded = os.environ.get(_APPROVAL_KEY_ENV, "").strip()
    if not encoded:
        raise ValueError(f"{_APPROVAL_KEY_ENV} is required to verify human approval receipts")
    try:
        key = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{_APPROVAL_KEY_ENV} must contain valid base64") from exc
    if len(key) < 32:
        raise ValueError(f"{_APPROVAL_KEY_ENV} must decode to at least 32 bytes")
    return key


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"host human approval receipt {field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"host human approval receipt {field} must include a timezone")
    return parsed.astimezone(UTC)


def _canonical_json(payload: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("host human approval receipt must contain JSON-compatible values") from exc
