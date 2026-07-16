"""Typed and validation contracts for bounded context injection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import unicodedata
from typing import Any

from brain.v5.context_compiler_support import DEFAULT_CONTEXT_FAMILIES
from brain.v5.knowledge_context_contracts import KnowledgeContextRequest
from brain.v5.paths import WorkspacePaths
from brain.v5.skill_applicability import SkillApplicabilityRequest


CONTEXT_INJECTION_PROFILE_BUDGETS = {
    "startup_orientation": {"max_tokens": 800, "max_bytes": 4000},
    "normal_research": {"max_tokens": 1500, "max_bytes": 7500},
}
REQUESTED_PROFILES = frozenset({"auto", *CONTEXT_INJECTION_PROFILE_BUDGETS})
EFFECTIVE_PROFILES = frozenset({"none", *CONTEXT_INJECTION_PROFILE_BUDGETS})
INJECTION_STATUSES = frozenset(
    {
        "prepared",
        "delivery_started",
        "injected",
        "ignored_not_research_relevant",
    }
)
_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
)
_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")


class ContextInjectionError(RuntimeError):
    """Raised when a context injection cannot be prepared safely."""


class ContextInjectionDeliveryUncertainError(ContextInjectionError):
    """Raised when replay could duplicate a delivery with unknown outcome."""


@dataclass(frozen=True)
class ContextInjectionRequest:
    event_id: str
    event_type: str
    host: str
    host_session_id: str
    session_id: str
    topic_id: str
    context_profile: str = "auto"
    research_relevant: bool = True
    host_supports_session_start: bool = True
    objective_text: str = ""
    user_goal: str = ""
    focus_set_ref: str = ""
    program_id: str = ""
    include_cross_topic_discovery: bool = False
    recall_audit_ref: str = ""
    exact_refs: tuple[str, ...] = ()
    exact_pins: tuple[Any, ...] = ()
    knowledge_request: KnowledgeContextRequest | None = None
    skill_request: SkillApplicabilityRequest | None = None
    families: tuple[str, ...] = DEFAULT_CONTEXT_FAMILIES
    max_tokens: int | None = None
    max_bytes: int | None = None
    record_limit: int | None = None
    candidate_limit: int | None = None
    record_offset: int = 0

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "event_type",
            "host",
            "host_session_id",
            "session_id",
            "topic_id",
        ):
            _validate_logical_identifier(field_name, getattr(self, field_name))
        for field_name in ("focus_set_ref", "program_id", "recall_audit_ref"):
            value = getattr(self, field_name)
            if value:
                _validate_logical_identifier(field_name, value, allow_typed_ref=True)
        if self.context_profile not in REQUESTED_PROFILES:
            raise ValueError(
                "context_profile must be auto, startup_orientation, or normal_research"
            )
        _require_bool("research_relevant", self.research_relevant)
        _require_bool("host_supports_session_start", self.host_supports_session_start)
        _require_bool(
            "include_cross_topic_discovery", self.include_cross_topic_discovery
        )
        for field_name in ("objective_text", "user_goal"):
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(f"{field_name} must be a string")
            if len(value.encode("utf-8")) > 65536:
                raise ValueError(f"{field_name} must be at most 65536 UTF-8 bytes")
        for ref in self.exact_refs:
            _validate_typed_ref("exact_refs", ref)
        if not self.families or any(
            not isinstance(family, str) or not family.strip() for family in self.families
        ):
            raise ValueError("families must contain non-empty family names")
        if len(set(self.families)) != len(self.families):
            raise ValueError("families must not contain duplicates")
        for field_name, minimum in (("max_tokens", 64), ("max_bytes", 384)):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, int) or value < minimum):
                raise ValueError(f"{field_name} must be at least {minimum} when supplied")
        for field_name, lower, upper in (
            ("record_limit", 1, 200),
            ("candidate_limit", 1, 40),
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, int) or not lower <= value <= upper
            ):
                raise ValueError(f"{field_name} must be between {lower} and {upper}")
        if not isinstance(self.record_offset, int) or self.record_offset < 0:
            raise ValueError("record_offset must be a non-negative integer")


@dataclass(frozen=True)
class ContextInjectionReceipt:
    schema_version: int
    receipt_id: str
    content_fingerprint: str
    receipt_revision: int
    receipt_payload_sha256: str
    namespace_sha256: str
    request_fingerprint: str
    workspace_identity: str
    host: str
    host_session_id: str
    event_id: str
    event_type: str
    logical_event_type: str
    session_id: str
    topic_id: str
    focus_set_ref: str
    context_profile: str
    base_index_generation: int
    base_index_content_hash: str
    delta_generation: int
    selected_family_state_tokens: dict[str, str]
    selected_family_content_tokens: dict[str, str]
    dirty_families: list[str]
    canonical_watermark: str
    exact_refs: list[str]
    selected_record_refs: list[str]
    checked_scope: dict[str, Any]
    errors: list[str]
    max_tokens: int
    max_bytes: int
    byte_count: int
    estimated_tokens: int
    content_sha256: str
    created_at: str
    injection_status: str
    delivery_attempt_id: str
    runtime_path: str
    previous_receipt_id: str = ""
    trust_effect: str = "none"
    orientation_only: bool = True
    summary_inputs_trusted: bool = False
    can_update_kernel_state: bool = False
    can_update_claim_trust: bool = False


def validate_context_injection_receipt_payload(payload: Any) -> tuple[str, ...]:
    from brain.v5.context_injection_receipt_validation import (
        validate_context_injection_receipt_payload as _validate,
    )

    return _validate(payload)


def seal_context_injection_receipt(
    receipt: ContextInjectionReceipt,
) -> ContextInjectionReceipt:
    basis = asdict(receipt)
    basis["receipt_payload_sha256"] = ""
    return replace(receipt, receipt_payload_sha256=hash_json(basis))


def transition_context_injection_receipt(
    receipt: ContextInjectionReceipt,
    *,
    injection_status: str,
    delivery_attempt_id: str,
) -> ContextInjectionReceipt:
    if injection_status not in INJECTION_STATUSES:
        raise ValueError("injection_status is unsupported")
    revision = receipt.receipt_revision + 1
    identity = hash_json(
        {
            "namespace_sha256": receipt.namespace_sha256,
            "content_fingerprint": receipt.content_fingerprint,
            "injection_status": injection_status,
            "delivery_attempt_id": delivery_attempt_id,
            "previous_receipt_id": receipt.receipt_id,
            "receipt_revision": revision,
        }
    )
    transitioned = replace(
        receipt,
        receipt_id=f"context-injection-receipt:{identity}",
        receipt_revision=revision,
        receipt_payload_sha256="",
        previous_receipt_id=receipt.receipt_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        injection_status=injection_status,
        delivery_attempt_id=delivery_attempt_id,
    )
    return seal_context_injection_receipt(transitioned)


def workspace_identity(ws: WorkspacePaths) -> str:
    return unicodedata.normalize(
        "NFC",
        os.path.normcase(os.path.normpath(str(ws.base.resolve(strict=False)))),
    )


def hash_json(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_bool(field_name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")


def _validate_typed_ref(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or ":" not in value:
        raise ValueError(f"{field_name} must contain typed refs")
    _validate_logical_identifier(field_name, value, allow_typed_ref=True, max_bytes=512)


def _validate_logical_identifier(
    field_name: str,
    value: Any,
    *,
    allow_typed_ref: bool = False,
    max_bytes: int = 256,
) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != unicodedata.normalize("NFC", value):
        raise ValueError(f"{field_name} must be NFC-normalized")
    if value != value.strip():
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{field_name} must be at most {max_bytes} UTF-8 bytes")
    if (
        value in {".", ".."}
        or ".." in value
        or "/" in value
        or "\\" in value
        or _DRIVE_PREFIX.match(value)
        or any(ord(char) < 32 for char in value)
        or (":" in value and not allow_typed_ref)
    ):
        raise ValueError(f"{field_name} must be a safe logical identifier")
    logical_id = value.rsplit(":", 1)[-1] if allow_typed_ref else value
    if logical_id.endswith(".") or logical_id.endswith(" "):
        raise ValueError(f"{field_name} must be a safe logical identifier")
    if logical_id.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(f"{field_name} must not use a reserved filesystem name")
