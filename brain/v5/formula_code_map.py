"""Reviewed formula-code object relations and bounded execution edit capsules."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from brain.v5.execution_models import CodeStateRecord, ExecutionBaselineRecord
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.formula_code_contracts import CodeEditCapsuleRequest, FormulaCodeRelation
from brain.v5.models import (
    ArtifactRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ReferenceLocationRecord,
    SourceAssetRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WriteResult


def record_formula_code_relation(
    ws: WorkspacePaths,
    relation: FormulaCodeRelation,
    *,
    actor: RecordActor,
) -> WriteResult:
    """Persist a reviewed exact link using the existing object-relation graph."""

    formula = _require_current_record(ws, relation.formula_ref, "formula ref")
    code = _require_current_record(ws, relation.code_state_ref, "code state ref")
    if not isinstance(formula, PhysicsObjectRecord) or formula.object_type != "formula":
        raise ValueError("formula_ref must pin a formula PhysicsObjectRecord")
    if not isinstance(code, CodeStateRecord):
        raise ValueError("code_state_ref must pin a CodeStateRecord")
    if formula.topic_id != relation.topic_id:
        raise ValueError("formula-code relation has a foreign formula topic")
    code_topic = str(code.linked_records.get("topic_id") or "")
    code_claim = str(code.linked_records.get("claim_id") or "")
    if code_topic != relation.topic_id or code_claim != relation.claim_id:
        raise ValueError("formula-code relation code state must match topic and claim scope")

    source_records = _require_current_refs(ws, relation.source_refs, "source ref")
    test_records = _require_current_refs(ws, relation.test_refs, "test ref")
    _require_source_records(source_records, relation.topic_id, relation.claim_id)
    _require_test_records(test_records, relation.topic_id, relation.claim_id)
    baseline = None
    if relation.accepted_baseline_ref is not None:
        baseline = _require_current_record(
            ws,
            relation.accepted_baseline_ref,
            "accepted baseline ref",
        )
        _require_matching_baseline(
            baseline,
            relation.topic_id,
            relation.claim_id,
            relation.code_state_ref,
        )

    metadata = _relation_metadata(relation)
    relation_id = _relation_id(relation, metadata)
    stored = ObjectRelationRecord(
        relation_id=relation_id,
        topic_id=relation.topic_id,
        relation_type=relation.relation_type,
        subject_id=formula.object_id,
        object_id=code.code_state_id,
        statement=relation.statement,
        claim_id=relation.claim_id,
        assumptions=list(relation.assumptions),
        failure_modes=list(relation.known_failures),
        source_refs=[_pinned_text(item) for item in relation.source_refs],
        evidence_refs=[_pinned_text(item) for item in relation.test_refs],
        metadata=metadata,
        status="reviewed",
    )
    return RecordRepository(ws, actor=actor).write(
        "object_relations",
        stored,
        body=(
            "# Formula-Code Relation\n\n"
            f"Relation: `{relation.relation_type}`\n\n"
            f"{relation.statement}\n\n"
            "Reviewed against exact formula, code-state, source, test, and baseline refs.\n"
        ),
    )


def build_code_edit_execution_capsule(
    ws: WorkspacePaths,
    request: CodeEditCapsuleRequest,
) -> dict[str, Any]:
    """Build a bounded, trust-neutral edit packet from one exact relation."""

    relation_version = get_record_version(ws, request.relation_ref)
    relation = relation_version.record
    if not isinstance(relation, ObjectRelationRecord):
        raise ValueError("relation_ref must pin an ObjectRelationRecord")
    metadata = relation.metadata if isinstance(relation.metadata, Mapping) else {}
    if metadata.get("schema_version") != "formula-code-relation/v1":
        raise ValueError("relation_ref is not a formula-code relation")

    formula_ref = _pin_from_mapping(metadata.get("formula_ref"), "formula_ref")
    code_ref = _pin_from_mapping(metadata.get("code_state_ref"), "code_state_ref")
    source_refs = _pins_from_sequence(metadata.get("source_refs"), "source_refs")
    test_refs = _pins_from_sequence(metadata.get("test_refs"), "test_refs")
    baseline_ref = _optional_pin(metadata.get("accepted_baseline_ref"))
    formula = get_record_version(ws, formula_ref).record
    code = get_record_version(ws, code_ref).record
    source_records = tuple(get_record_version(ws, pin).record for pin in source_refs)
    test_records = tuple(get_record_version(ws, pin).record for pin in test_refs)
    baseline = get_record_version(ws, baseline_ref).record if baseline_ref else None
    _revalidate_stored_relation(
        relation,
        metadata,
        formula_ref=formula_ref,
        formula=formula,
        code_ref=code_ref,
        code=code,
        source_refs=source_refs,
        source_records=source_records,
        test_refs=test_refs,
        test_records=test_records,
        baseline_ref=baseline_ref,
        baseline=baseline,
    )

    same_scope = relation.topic_id == request.topic_id and relation.claim_id == request.claim_id
    scope_decision = assess_execution_scope(
        ws,
        operation="use_formula_code_relation",
        consumer_scope=(f"topic:{request.topic_id}", f"claim:{request.claim_id}"),
        dependency_refs=(request.relation_ref,),
        revalidation_decision_refs=request.revalidation_decision_refs,
    )
    foreign = relation.topic_id != request.topic_id
    scope_allowed = scope_decision.decision == "allowed"

    pins = tuple(
        dict.fromkeys(
            (
                request.relation_ref,
                formula_ref,
                code_ref,
                *source_refs,
                *test_refs,
                *((baseline_ref,) if baseline_ref else ()),
            )
        )
    )
    stale_reasons = _stale_reasons(
        ws,
        request.relation_ref,
        formula_ref,
        code_ref,
        source_refs,
        test_refs,
        baseline_ref,
    )
    if baseline_ref and (
        not isinstance(baseline, ExecutionBaselineRecord) or baseline.status != "active"
    ):
        stale_reasons.append("accepted baseline is no longer active")
    if not test_refs:
        stale_reasons.append("no pinned tests are available")

    blocking = list(dict.fromkeys(stale_reasons))
    limitations: list[str] = []
    if baseline_ref is None:
        limitations.append("no accepted baseline is pinned")
    if not same_scope and not foreign:
        blocking.append("relation claim does not match target claim")
    if not scope_allowed:
        blocking.extend(scope_decision.reasons or ("formula-code relation scope is not allowed",))
    if foreign:
        blocking.append("target-side code and baseline revalidation is required")

    stale_code = "code state changed after relation review" in stale_reasons
    if not scope_allowed or (not same_scope and not foreign):
        status = "scope_blocked"
    elif foreign:
        status = "orientation_only"
    elif stale_code:
        status = "stale_code_state"
    elif blocking:
        status = "blocked"
    elif baseline_ref is None:
        status = "ready_for_edit"
    else:
        status = "ready"
    executable = status in {"ready", "ready_for_edit"}
    reproducible = status == "ready"
    return {
        "ok": status in {"ready", "ready_for_edit", "orientation_only"},
        "kind": "code_edit_execution_capsule",
        "status": status,
        "topic_id": request.topic_id,
        "claim_id": request.claim_id,
        "source_topic_id": relation.topic_id,
        "source_claim_id": relation.claim_id,
        "relation": {
            "record_ref": request.relation_ref.record_ref,
            "relation_type": relation.relation_type,
            "statement": relation.statement,
            "applicability_boundary": str(metadata.get("applicability_boundary") or ""),
            "assumptions": list(relation.assumptions),
            "known_failures": list(metadata.get("known_failures") or []),
        },
        "formula": {
            "record_ref": formula_ref.record_ref,
            "name": formula.name,
            "notation": formula.notation,
            "definition": formula.definition,
        },
        "code": {
            "record_ref": code_ref.record_ref,
            "repo_id": code.repo_id,
            "module": str(metadata.get("module") or ""),
            "function": str(metadata.get("function") or ""),
            "commit": code.upstream_commit,
            "branch": code.local_branch,
            "dirty": code.dirty,
            "patch_manifest_ref": code.patch_manifest_ref,
        },
        "parameter": {
            "name": str(metadata.get("parameter") or ""),
            "role": relation.relation_type,
        },
        "output": str(metadata.get("output") or ""),
        "normalization": str(metadata.get("normalization") or ""),
        "tests": [asdict(item) for item in test_refs],
        "sources": [asdict(item) for item in source_refs],
        "accepted_baseline": asdict(baseline_ref) if baseline_ref else None,
        "exact_expansion_refs": [item.record_ref for item in pins],
        "exact_expansion_pins": [asdict(item) for item in pins],
        "scope_decision": scope_decision.decision,
        "scope_reasons": list(scope_decision.reasons),
        "blocking_reasons": blocking,
        "limitations": limitations,
        "reproducible": reproducible,
        "can_execute_edit": executable,
        "baseline_claims_allowed": reproducible,
        "requires_target_revalidation": foreign,
        "orientation_only": status == "orientation_only",
        "summary_inputs_trusted": False,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }


def _relation_metadata(relation: FormulaCodeRelation) -> dict[str, Any]:
    return {
        "schema_version": "formula-code-relation/v1",
        "formula_ref": asdict(relation.formula_ref),
        "code_state_ref": asdict(relation.code_state_ref),
        "module": relation.module,
        "function": relation.function,
        "parameter": relation.parameter,
        "output": relation.output,
        "normalization": relation.normalization,
        "scope": list(relation.scope),
        "assumptions": list(relation.assumptions),
        "source_refs": [asdict(item) for item in relation.source_refs],
        "test_refs": [asdict(item) for item in relation.test_refs],
        "accepted_baseline_ref": (
            asdict(relation.accepted_baseline_ref)
            if relation.accepted_baseline_ref is not None
            else None
        ),
        "known_failures": list(relation.known_failures),
        "applicability_boundary": relation.applicability_boundary,
    }


def _relation_id(relation: FormulaCodeRelation, metadata: Mapping[str, Any]) -> str:
    basis = {
        "topic_id": relation.topic_id,
        "claim_id": relation.claim_id,
        "relation_type": relation.relation_type,
        "statement": relation.statement,
        "metadata": metadata,
    }
    digest = hashlib.sha256(
        json.dumps(basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"formula-code-relation-{digest}"


def _require_current_record(ws: WorkspacePaths, pin: PinnedRecordRef, label: str) -> Any:
    version = get_record_version(ws, pin)
    current = pin_current_record(ws, pin.record_ref)
    if current != pin:
        normalized = "code state ref" if label == "code state ref" else label
        raise ValueError(f"{normalized} is stale relative to the current record")
    return version.record


def _require_current_refs(
    ws: WorkspacePaths,
    refs: Sequence[PinnedRecordRef],
    label: str,
) -> tuple[Any, ...]:
    return tuple(_require_current_record(ws, item, label) for item in refs)


def _require_source_records(
    records: Sequence[Any],
    topic_id: str,
    claim_id: str,
) -> None:
    for record in records:
        if not isinstance(record, (ReferenceLocationRecord, SourceAssetRecord)):
            raise ValueError("source ref must pin a reference location or source asset")
        if not record.topic_id:
            raise ValueError("source ref must have explicit topic scope")
        if record.topic_id != topic_id:
            raise ValueError("formula-code relation source ref has a foreign topic")
        if record.claim_id and record.claim_id != claim_id:
            raise ValueError("formula-code relation source ref has a foreign claim")


def _require_test_records(
    records: Sequence[Any],
    topic_id: str,
    claim_id: str,
) -> None:
    for record in records:
        if not isinstance(record, (ArtifactRecord, ValidationResultRecord)):
            raise ValueError("test ref must pin an artifact or validation result")
        if record.topic_id != topic_id:
            raise ValueError("formula-code relation test ref has a foreign topic")
        if record.claim_id != claim_id:
            raise ValueError("formula-code relation test ref has a foreign claim")


def _require_matching_baseline(
    baseline: Any,
    topic_id: str,
    claim_id: str,
    code_ref: PinnedRecordRef,
) -> None:
    if not isinstance(baseline, ExecutionBaselineRecord) or baseline.status != "active":
        raise ValueError("accepted_baseline_ref must pin an active execution baseline")
    if baseline.topic_id != topic_id or baseline.claim_id != claim_id:
        raise ValueError("accepted baseline must match relation topic and claim")
    baseline_code = PinnedRecordRef(
        baseline.code_state_ref,
        baseline.code_state_hash,
        baseline.code_state_revision,
    )
    if baseline_code != code_ref:
        raise ValueError("accepted baseline must bind the same exact code state")


def _revalidate_stored_relation(
    relation: ObjectRelationRecord,
    metadata: Mapping[str, Any],
    *,
    formula_ref: PinnedRecordRef,
    formula: Any,
    code_ref: PinnedRecordRef,
    code: Any,
    source_refs: tuple[PinnedRecordRef, ...],
    source_records: tuple[Any, ...],
    test_refs: tuple[PinnedRecordRef, ...],
    test_records: tuple[Any, ...],
    baseline_ref: PinnedRecordRef | None,
    baseline: Any,
) -> None:
    if relation.status != "reviewed":
        raise ValueError("formula-code relation must remain reviewed")
    declared = FormulaCodeRelation(
        topic_id=relation.topic_id,
        claim_id=relation.claim_id,
        relation_type=relation.relation_type,
        statement=relation.statement,
        formula_ref=formula_ref,
        code_state_ref=code_ref,
        module=str(metadata.get("module") or ""),
        function=str(metadata.get("function") or ""),
        parameter=str(metadata.get("parameter") or ""),
        output=str(metadata.get("output") or ""),
        normalization=str(metadata.get("normalization") or ""),
        scope=_string_tuple(metadata.get("scope"), "scope"),
        assumptions=_string_tuple(metadata.get("assumptions"), "assumptions"),
        source_refs=source_refs,
        test_refs=test_refs,
        accepted_baseline_ref=baseline_ref,
        known_failures=_string_tuple(metadata.get("known_failures"), "known_failures"),
        applicability_boundary=str(metadata.get("applicability_boundary") or ""),
    )
    if not isinstance(formula, PhysicsObjectRecord) or formula.object_type != "formula":
        raise ValueError("formula_ref must pin a formula PhysicsObjectRecord")
    if not isinstance(code, CodeStateRecord):
        raise ValueError("code_state_ref must pin a CodeStateRecord")
    if formula.topic_id != relation.topic_id or relation.subject_id != formula.object_id:
        raise ValueError("stored formula-code relation formula scope or identity changed")
    if relation.object_id != code.code_state_id:
        raise ValueError("stored formula-code relation code identity changed")
    if str(code.linked_records.get("topic_id") or "") != relation.topic_id or str(
        code.linked_records.get("claim_id") or ""
    ) != relation.claim_id:
        raise ValueError("stored formula-code relation code scope changed")
    if tuple(relation.assumptions) != declared.assumptions:
        raise ValueError("stored formula-code relation assumptions changed")
    if tuple(relation.failure_modes) != declared.known_failures:
        raise ValueError("stored formula-code relation failure modes changed")
    if relation.source_refs != [_pinned_text(pin) for pin in source_refs]:
        raise ValueError("stored formula-code relation source refs changed")
    if relation.evidence_refs != [_pinned_text(pin) for pin in test_refs]:
        raise ValueError("stored formula-code relation test refs changed")
    _require_source_records(source_records, relation.topic_id, relation.claim_id)
    _require_test_records(test_records, relation.topic_id, relation.claim_id)
    if baseline_ref is not None:
        _require_matching_baseline(
            baseline,
            relation.topic_id,
            relation.claim_id,
            code_ref,
        )


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"formula-code relation {field} must be a list of strings")
    return tuple(value)


def _stale_reasons(
    ws: WorkspacePaths,
    relation_ref: PinnedRecordRef,
    formula_ref: PinnedRecordRef,
    code_ref: PinnedRecordRef,
    source_refs: Sequence[PinnedRecordRef],
    test_refs: Sequence[PinnedRecordRef],
    baseline_ref: PinnedRecordRef | None,
) -> list[str]:
    reasons: list[str] = []
    checks = (
        (relation_ref, "formula-code relation changed after review"),
        (formula_ref, "formula changed after relation review"),
        (code_ref, "code state changed after relation review"),
        *((item, f"source ref changed after relation review: {item.record_ref}") for item in source_refs),
        *((item, f"test ref changed after relation review: {item.record_ref}") for item in test_refs),
        *(((baseline_ref, "accepted baseline changed after relation review"),) if baseline_ref else ()),
    )
    for pin, message in checks:
        try:
            if pin_current_record(ws, pin.record_ref) != pin:
                reasons.append(message)
        except Exception:  # noqa: BLE001 - missing current state is stale.
            reasons.append(message)
    return reasons


def _pin_from_mapping(value: Any, field: str) -> PinnedRecordRef:
    if not isinstance(value, Mapping):
        raise ValueError(f"formula-code relation {field} must be an exact pinned ref")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )


def _pins_from_sequence(value: Any, field: str) -> tuple[PinnedRecordRef, ...]:
    if not isinstance(value, list):
        raise ValueError(f"formula-code relation {field} must be a list")
    return tuple(_pin_from_mapping(item, f"{field}[]") for item in value)


def _optional_pin(value: Any) -> PinnedRecordRef | None:
    return None if value in (None, {}) else _pin_from_mapping(value, "accepted_baseline_ref")


def _pinned_text(pin: PinnedRecordRef) -> str:
    return f"{pin.record_ref}@sha256:{pin.content_hash}#revision={pin.revision}"
