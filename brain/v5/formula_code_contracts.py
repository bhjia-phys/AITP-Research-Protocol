"""Exact contracts for reviewed formula-to-code relations and edit capsules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from brain.v5.pinned_record_refs import PinnedRecordRef

if TYPE_CHECKING:
    from brain.v5.context_compiler import ContextRequest


FORMULA_CODE_RELATION_TYPES = frozenset(
    {
        "implemented_by",
        "controlled_by_parameter",
        "approximated_by",
        "discretized_by",
        "normalizes_as",
        "produces_observable",
        "validated_by",
    }
)


@dataclass(frozen=True)
class FormulaCodeRelation:
    topic_id: str
    claim_id: str
    relation_type: str
    statement: str
    formula_ref: PinnedRecordRef
    code_state_ref: PinnedRecordRef
    module: str = ""
    function: str = ""
    parameter: str = ""
    output: str = ""
    normalization: str = ""
    scope: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    source_refs: tuple[PinnedRecordRef, ...] = ()
    test_refs: tuple[PinnedRecordRef, ...] = ()
    accepted_baseline_ref: PinnedRecordRef | None = None
    known_failures: tuple[str, ...] = ()
    applicability_boundary: str = ""

    def __post_init__(self) -> None:
        for name in ("topic_id", "claim_id", "relation_type", "statement"):
            if not str(getattr(self, name) or "").strip():
                raise ValueError(f"formula-code relation {name} must be non-empty")
        if self.relation_type not in FORMULA_CODE_RELATION_TYPES:
            raise ValueError(f"unsupported formula-code relation type: {self.relation_type}")
        if not self.scope:
            raise ValueError("formula-code relation scope must be non-empty")
        expected_scope = {f"topic:{self.topic_id}", f"claim:{self.claim_id}"}
        if not expected_scope.issubset(set(self.scope)):
            raise ValueError("formula-code relation scope must include its topic and claim")
        if not self.assumptions:
            raise ValueError("formula-code relation assumptions must be non-empty")
        if not self.source_refs:
            raise ValueError("formula-code relation source refs must be non-empty")
        if not self.test_refs:
            raise ValueError("formula-code relation test refs must be non-empty")
        if not self.applicability_boundary.strip():
            raise ValueError("formula-code relation applicability boundary must be non-empty")
        if not any((self.module, self.function, self.parameter, self.output, self.normalization)):
            raise ValueError("formula-code relation must identify code, parameter, output, or normalization")
        if self.relation_type == "controlled_by_parameter" and not self.parameter:
            raise ValueError("controlled_by_parameter requires parameter")


@dataclass(frozen=True)
class CodeEditCapsuleRequest:
    relation_ref: PinnedRecordRef
    topic_id: str
    claim_id: str
    revalidation_decision_refs: tuple[PinnedRecordRef, ...] = ()

    def __post_init__(self) -> None:
        if not self.topic_id.strip() or not self.claim_id.strip():
            raise ValueError("code edit capsule requires target topic and claim")


def context_request_for_code_edit_capsule(
    session_id: str,
    capsule: dict[str, Any],
    *,
    max_tokens: int = 1200,
    max_bytes: int = 6000,
) -> ContextRequest:
    """Convert one bounded edit capsule into an explicit expansion request."""

    from brain.v5.context_compiler import ContextRequest

    refs = capsule.get("exact_expansion_refs")
    if not isinstance(refs, list) or not refs or len(refs) > 50:
        raise ValueError("code edit capsule must expose between 1 and 50 exact refs")
    if any(not isinstance(ref, str) or ":" not in ref for ref in refs):
        raise ValueError("code edit capsule exact refs must be typed record refs")
    if len(set(refs)) != len(refs):
        raise ValueError("code edit capsule must not contain duplicate refs")
    pin_payloads = capsule.get("exact_expansion_pins")
    if not isinstance(pin_payloads, list) or len(pin_payloads) != len(refs):
        raise ValueError("code edit capsule must preserve one exact pin per ref")
    pins = tuple(
        PinnedRecordRef(
            record_ref=str(item.get("record_ref") or ""),
            content_hash=str(item.get("content_hash") or ""),
            revision=item.get("revision"),
        )
        for item in pin_payloads
        if isinstance(item, dict)
    )
    if len(pins) != len(refs) or tuple(pin.record_ref for pin in pins) != tuple(refs):
        raise ValueError("code edit capsule exact pins must match exact refs")
    return ContextRequest(
        session_id=session_id,
        disclosure_level="exact_expansion",
        exact_refs=tuple(refs),
        exact_pins=pins,
        max_tokens=max_tokens,
        max_bytes=max_bytes,
    )
