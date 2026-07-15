"""Repository writers and exact DAG validation for formal derivations."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Sequence

from brain.v5.derivation_contracts import DerivationDagValidation
from brain.v5.derivation_models import DerivationChainRecord, DerivationStepRecord
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.lifecycle_models import CrossTopicRelationRecord
from brain.v5.models import (
    ArtifactRecord,
    ObjectRelationRecord,
    PhysicsObjectRecord,
    ReferenceLocationRecord,
    ScopeRevalidationDecisionRecord,
    SourceAssetRecord,
    ToolRunRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository, WritePolicy, WriteResult


def record_derivation_step(
    ws: WorkspacePaths,
    step: DerivationStepRecord,
    *,
    actor: RecordActor,
    expected_current_hash: str = "",
) -> WriteResult:
    """Record one inspectable step after resolving every exact dependency."""

    _validate_step_refs(ws, step)
    policy = (
        WritePolicy(mode="revision", expected_hash=expected_current_hash)
        if expected_current_hash
        else None
    )
    return RecordRepository(ws, actor=actor).write(
        "derivation_steps",
        step,
        body=(
            f"# Derivation Step: {step.step_id}\n\n"
            f"Input: `{step.input_expression}`\n\n"
            f"Output: `{step.output_expression}`\n"
        ),
        policy=policy,
    )


def record_derivation_chain(
    ws: WorkspacePaths,
    chain: DerivationChainRecord,
    *,
    actor: RecordActor,
    expected_current_hash: str = "",
) -> WriteResult:
    """Record a chain only after its complete pinned DAG validates."""

    validate_derivation_dag(ws, chain)
    policy = (
        WritePolicy(mode="revision", expected_hash=expected_current_hash)
        if expected_current_hash
        else None
    )
    return RecordRepository(ws, actor=actor).write(
        "derivation_chains",
        chain,
        body=(
            f"# Derivation Chain: {chain.title}\n\n"
            f"Target: {chain.target}\n\n"
            f"Structural status: `{chain.status}`\n"
        ),
        policy=policy,
    )


def validate_derivation_dag(
    ws: WorkspacePaths,
    chain: DerivationChainRecord | PinnedRecordRef | Mapping[str, Any],
) -> DerivationDagValidation:
    """Validate exact step order, dependency closure, imports, and open gaps."""

    if not isinstance(chain, DerivationChainRecord):
        resolved = get_record_version(ws, _coerce_pin(chain)).record
        if not isinstance(resolved, DerivationChainRecord):
            raise ValueError("derivation chain ref must resolve to DerivationChainRecord")
        chain = resolved
    step_pins = _pins(chain.ordered_step_refs, "ordered_step_refs")
    if len({pin.record_ref for pin in step_pins}) != len(step_pins):
        raise ValueError("derivation chain ordered steps must be unique")
    steps = [_current_step(ws, pin) for pin in step_pins]
    local_by_ref = {pin.record_ref: (pin, step) for pin, step in zip(step_pins, steps)}
    checked = [pin.record_ref for pin in step_pins]
    imported_checked: list[str] = []
    unresolved: list[str] = []
    seen: set[str] = set()
    prior_sequences: list[int] = []
    for pin, step in zip(step_pins, steps):
        if step.chain_id != chain.chain_id:
            raise ValueError("ordered derivation step belongs to another chain")
        _require_same_scope(chain, step)
        if step.step_id in seen:
            raise ValueError("derivation step identity is duplicated")
        seen.add(step.step_id)
        if prior_sequences and step.sequence <= prior_sequences[-1]:
            raise ValueError("derivation step sequence must follow ordered_step_refs")
        prior_sequences.append(step.sequence)
        for field_name in (
            "invoked_knowledge_refs",
            "source_anchor_refs",
            "local_check_refs",
        ):
            _resolve_chain_refs(ws, getattr(step, field_name), field_name, chain)
        for dependency in _pins(step.dependency_step_refs, "dependency_step_refs"):
            checked.append(dependency.record_ref)
            dependency_step = _exact_step(ws, dependency)
            if dependency.record_ref == pin.record_ref:
                raise ValueError("derivation DAG contains a self dependency cycle")
            local = local_by_ref.get(dependency.record_ref)
            if local is not None:
                if local[0] != dependency:
                    raise ValueError("local derivation dependency pin is stale")
                if dependency_step.sequence >= step.sequence:
                    raise ValueError("derivation DAG contains a cycle or forward dependency")
                continue
            imported_ref = _validate_imported_dependency(
                ws,
                chain,
                dependency,
                dependency_step,
            )
            imported_checked.append(imported_ref)
        unresolved.extend(step.unresolved_conditions)
    _resolve_chain_refs(ws, chain.check_refs, "check_refs", chain)
    _resolve_chain_refs(ws, chain.source_refs, "source_refs", chain)
    if chain.status == "structurally_closed":
        if not step_pins:
            raise ValueError("structurally closed derivation requires at least one step")
        if chain.open_gaps or unresolved:
            raise ValueError("structurally closed derivation cannot have open gaps or unresolved conditions")
        if any(step.status != "established" for step in steps):
            raise ValueError("structurally closed derivation requires established steps")
        if not chain.check_refs or not chain.source_refs:
            raise ValueError("structurally closed derivation requires checks and source refs")
    return DerivationDagValidation(
        chain_id=chain.chain_id,
        valid=True,
        ordered_step_ids=tuple(step.step_id for step in steps),
        open_gaps=tuple(chain.open_gaps),
        unresolved_conditions=tuple(unresolved),
        checked_refs=tuple(dict.fromkeys(checked)),
        imported_chain_refs=tuple(dict.fromkeys(imported_checked)),
    )


def _validate_step_refs(ws: WorkspacePaths, step: DerivationStepRecord) -> None:
    for pin in _pins(step.dependency_step_refs, "dependency_step_refs"):
        get_record_version(ws, pin)
    for field_name in (
        "invoked_knowledge_refs",
        "source_anchor_refs",
        "local_check_refs",
    ):
        for pin in _pins(getattr(step, field_name), field_name):
            _resolve_scoped_ref(
                ws,
                pin,
                field_name,
                topic_id=step.topic_id,
                claim_id=step.claim_id,
            )
    if step.status == "established" and (
        not step.invoked_knowledge_refs
        or not step.source_anchor_refs
        or not step.local_check_refs
        or step.unresolved_conditions
    ):
        raise ValueError("established derivation step requires knowledge, sources, checks, and no unresolved conditions")


def _current_step(ws: WorkspacePaths, pin: PinnedRecordRef) -> DerivationStepRecord:
    if pin_current_record(ws, pin.record_ref) != pin:
        raise ValueError(f"derivation step ref is stale: {pin.record_ref}")
    return _exact_step(ws, pin)


def _exact_step(ws: WorkspacePaths, pin: PinnedRecordRef) -> DerivationStepRecord:
    record = get_record_version(ws, pin).record
    if not isinstance(record, DerivationStepRecord):
        raise ValueError(f"derivation dependency is not a step: {pin.record_ref}")
    return record


def _validate_imported_dependency(
    ws: WorkspacePaths,
    chain: DerivationChainRecord,
    dependency: PinnedRecordRef,
    step: DerivationStepRecord,
) -> str:
    for binding in chain.imported_chain_bindings:
        if not isinstance(binding, Mapping):
            raise ValueError("imported-chain binding must be a mapping")
        chain_pin = _coerce_pin(binding.get("chain_ref"))
        if pin_current_record(ws, chain_pin.record_ref) != chain_pin:
            raise ValueError("imported chain ref is stale")
        imported = get_record_version(ws, chain_pin).record
        if not isinstance(imported, DerivationChainRecord) or imported.chain_id != step.chain_id:
            continue
        imported_steps = _pins(imported.ordered_step_refs, "imported ordered_step_refs")
        if dependency not in imported_steps:
            continue
        if chain.status == "structurally_closed":
            if imported.status != "structurally_closed":
                raise ValueError(
                    "imported chain must be structurally closed before the target chain can close"
                )
            validate_derivation_dag(ws, imported)
        if imported.topic_id != chain.topic_id or imported.claim_id != chain.claim_id or imported.program_id != chain.program_id:
            _validate_foreign_import(ws, chain, imported, chain_pin, binding)
        return chain_pin.record_ref
    raise ValueError("cross-chain derivation dependency requires an explicit imported-chain binding")


def _validate_foreign_import(
    ws: WorkspacePaths,
    chain: DerivationChainRecord,
    imported: DerivationChainRecord,
    chain_pin: PinnedRecordRef,
    binding: Mapping[str, Any],
) -> None:
    if imported.topic_id == chain.topic_id:
        raise ValueError(
            "same-topic foreign claim or program chain must be remapped into a target-local chain"
        )
    bridge_pin = _coerce_pin(binding.get("bridge_ref"))
    decision_pin = _coerce_pin(binding.get("revalidation_decision_ref"))
    bridge = get_record_version(ws, bridge_pin).record
    decision = get_record_version(ws, decision_pin).record
    if not isinstance(bridge, CrossTopicRelationRecord):
        raise ValueError("imported-chain bridge_ref must pin a cross-topic relation")
    if not isinstance(decision, ScopeRevalidationDecisionRecord):
        raise ValueError("imported-chain revalidation ref must pin a scope decision")
    if (
        decision.bridge_ref != bridge_pin.record_ref
        or decision.bridge_hash != bridge_pin.content_hash
        or decision.bridge_revision != bridge_pin.revision
    ):
        raise ValueError("imported-chain binding does not bind the reviewed M1 bridge")
    consumer_scope = [f"topic:{chain.topic_id}", f"claim:{chain.claim_id}"]
    if chain.program_id:
        consumer_scope.append(f"program:{chain.program_id}")
    assessment = assess_execution_scope(
        ws,
        operation="use_imported_derivation_chain",
        consumer_scope=consumer_scope,
        dependency_refs=(chain_pin,),
        revalidation_decision_refs=(decision_pin,),
    )
    if assessment.decision != "allowed":
        raise ValueError(f"foreign imported-chain scope is not allowed: {assessment.decision}")


def _resolve_chain_refs(
    ws: WorkspacePaths,
    values: Sequence[Mapping[str, Any]],
    field_name: str,
    chain: DerivationChainRecord,
) -> None:
    for pin in _pins(values, field_name):
        _resolve_scoped_ref(
            ws,
            pin,
            field_name,
            topic_id=chain.topic_id,
            claim_id=chain.claim_id,
        )


def _resolve_scoped_ref(
    ws: WorkspacePaths,
    pin: PinnedRecordRef,
    field_name: str,
    *,
    topic_id: str,
    claim_id: str,
) -> Any:
    if pin_current_record(ws, pin.record_ref) != pin:
        raise ValueError(f"derivation {field_name} contains a stale ref")
    record = get_record_version(ws, pin).record
    _require_record_role(record, field_name)
    data = asdict(record) if hasattr(record, "__dataclass_fields__") else {}
    record_topic = str(data.get("topic_id") or "")
    record_claim = str(data.get("claim_id") or "")
    if not record_topic or record_topic != topic_id:
        raise ValueError(f"derivation {field_name} contains a foreign topic ref")
    if field_name in {"local_check_refs", "check_refs"} and record_claim != claim_id:
        raise ValueError(f"derivation {field_name} contains a foreign claim ref")
    if record_claim and record_claim != claim_id:
        raise ValueError(f"derivation {field_name} contains a foreign claim ref")
    return record


def _require_record_role(record: Any, field_name: str) -> None:
    allowed = {
        "invoked_knowledge_refs": (PhysicsObjectRecord, ObjectRelationRecord),
        "source_anchor_refs": (ReferenceLocationRecord, SourceAssetRecord),
        "source_refs": (ReferenceLocationRecord, SourceAssetRecord),
        "local_check_refs": (ArtifactRecord, ValidationResultRecord, ToolRunRecord),
        "check_refs": (ArtifactRecord, ValidationResultRecord, ToolRunRecord),
    }.get(field_name)
    if allowed is None or not isinstance(record, allowed):
        raise ValueError(f"derivation {field_name} contains an unsupported record type")


def _require_same_scope(chain: DerivationChainRecord, step: DerivationStepRecord) -> None:
    if (
        step.topic_id != chain.topic_id
        or step.claim_id != chain.claim_id
        or step.program_id != chain.program_id
    ):
        raise ValueError("ordered derivation step must match chain topic, claim, and program")


def _pins(values: Sequence[Mapping[str, Any]], field_name: str) -> tuple[PinnedRecordRef, ...]:
    try:
        return tuple(_coerce_pin(value) for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"derivation {field_name} must contain exact pinned refs") from exc


def _coerce_pin(value: PinnedRecordRef | Mapping[str, Any] | None) -> PinnedRecordRef:
    if isinstance(value, PinnedRecordRef):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("derivation refs must be exact pinned mappings")
    return PinnedRecordRef(
        record_ref=str(value.get("record_ref") or ""),
        content_hash=str(value.get("content_hash") or ""),
        revision=value.get("revision"),
    )
