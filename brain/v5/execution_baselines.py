"""Readiness, acceptance, and maturity projection for execution baselines."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from brain.v5.checkpoint_bindings import CheckpointSubjectBinding
from brain.v5.checkpoint_transactions import apply_bound_checkpoint_action
from brain.v5.effective_attempts import EffectiveAttemptState, resolve_effective_attempt_state
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.models import (
    CodeStateRecord,
    ExecutionBaselineRecord,
    ExecutionEnvironmentRecord,
    ToolRecipeRecord,
    ToolRunRecord,
    ValidationContractRecord,
    ValidationResultRecord,
)
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    FrozenDependencyManifest,
    PinnedRecordRef,
    build_frozen_dependency_manifest,
    get_record_version,
    pin_current_record,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository


@dataclass(frozen=True)
class BaselineAcceptanceRequest:
    run_ref: PinnedRecordRef
    validation_refs: tuple[PinnedRecordRef, ...]

    def action_payload(self) -> dict[str, Any]:
        return {
            "run_ref": asdict(self.run_ref),
            "validation_refs": [asdict(item) for item in sorted(self.validation_refs)],
        }


@dataclass(frozen=True)
class BaselineReadiness:
    request: BaselineAcceptanceRequest
    ready: bool
    effective_attempt: EffectiveAttemptState
    frozen_dependencies: FrozenDependencyManifest | None
    blocking_reasons: tuple[str, ...]
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class BaselineAcceptanceResult:
    baseline_ref: PinnedRecordRef
    checkpoint_application_receipt_ref: PinnedRecordRef
    replayed: bool
    can_update_claim_trust: bool = False


@dataclass(frozen=True)
class ExecutionMaturityProjection:
    run_ref: PinnedRecordRef
    recorded_maturity: str
    effective_maturity: str
    active_baseline_ref: PinnedRecordRef | None
    can_update_claim_trust: bool = False


def assess_baseline_readiness(
    ws: WorkspacePaths,
    request: BaselineAcceptanceRequest,
) -> BaselineReadiness:
    state = resolve_effective_attempt_state(ws, request.run_ref)
    reasons = list(state.blocking_reasons)
    run_version = get_record_version(ws, request.run_ref)
    run = run_version.record
    if not isinstance(run, ToolRunRecord):
        raise ValueError("baseline run_ref must pin a tool run")
    if not state.attempt_eligible and not reasons:
        reasons.append("effective attempt is not eligible")
    core_pins = _core_pins(run, reasons)
    if len(core_pins) == 3:
        _validate_core(ws, run, core_pins, reasons)
    validation_pins = tuple(sorted(set(request.validation_refs)))
    if not validation_pins:
        reasons.append("at least one exact validation result is required")
    for pin in validation_pins:
        _validate_result(ws, run, request.run_ref, pin, reasons)
    roots = [request.run_ref, *validation_pins]
    if state.latest_monitor_ref is not None:
        roots.append(state.latest_monitor_ref)
    else:
        reasons.append("latest immutable monitor is required")
    manifest = None
    try:
        manifest = build_frozen_dependency_manifest(ws, roots)
    except Exception as exc:  # noqa: BLE001 - readiness is fail closed.
        reasons.append(f"frozen dependency closure failed: {exc}")
    if manifest is not None:
        scope = assess_execution_scope(
            ws,
            operation="accept_execution_baseline",
            consumer_scope=(f"topic:{run.topic_id}", f"claim:{run.claim_id}"),
            dependency_refs=manifest.nodes,
        )
        if scope.decision != "allowed":
            reasons.append(f"baseline dependency scope is not allowed: {scope.decision}")
    return BaselineReadiness(
        request=request,
        ready=not reasons and manifest is not None,
        effective_attempt=state,
        frozen_dependencies=manifest,
        blocking_reasons=tuple(dict.fromkeys(reasons)),
    )


def accept_execution_baseline(
    ws: WorkspacePaths,
    request: BaselineAcceptanceRequest,
    *,
    binding: CheckpointSubjectBinding,
    checkpoint_request_ref: PinnedRecordRef | Mapping[str, Any],
    checkpoint_decision_ref: PinnedRecordRef | Mapping[str, Any],
    actor: RecordActor,
    now: datetime | None = None,
) -> BaselineAcceptanceResult:
    readiness = assess_baseline_readiness(ws, request)
    if not readiness.ready or readiness.frozen_dependencies is None:
        raise ValueError("execution baseline is not ready: " + "; ".join(readiness.blocking_reasons))
    if binding.action != "accept_execution_baseline":
        raise ValueError("baseline checkpoint action does not match")
    if binding.effect_policy != "execution_maturity_only":
        raise ValueError("baseline checkpoint effect policy does not match")
    if set(binding.subjects) != set(readiness.frozen_dependencies.nodes):
        raise ValueError("baseline checkpoint subjects do not match frozen dependencies")
    decision_pin = _coerce_pin(checkpoint_decision_ref)
    run = get_record_version(ws, request.run_ref).record
    assert isinstance(run, ToolRunRecord)
    manifest = readiness.frozen_dependencies
    baseline_id = f"execution-baseline-{_sha256_json({'run': asdict(request.run_ref), 'closure_hash': manifest.closure_hash})}"
    record = ExecutionBaselineRecord(
        baseline_id=baseline_id,
        topic_id=run.topic_id,
        claim_id=run.claim_id,
        run_ref=request.run_ref.record_ref,
        run_hash=request.run_ref.content_hash,
        run_revision=request.run_ref.revision,
        frozen_dependencies=asdict(manifest),
        recipe_ref=run.recipe_ref,
        recipe_hash=run.recipe_hash,
        recipe_revision=run.recipe_revision,
        code_state_ref=run.code_state_ref,
        code_state_hash=run.code_state_hash,
        code_state_revision=run.code_state_revision,
        environment_ref=run.environment_ref,
        environment_hash=run.environment_hash,
        environment_revision=run.environment_revision,
        validation_refs=[asdict(item) for item in sorted(request.validation_refs)],
        monitor_refs=[asdict(readiness.effective_attempt.latest_monitor_ref)],
        acceptance_checkpoint_ref=decision_pin.record_ref,
        acceptance_checkpoint_hash=decision_pin.content_hash,
        acceptance_checkpoint_revision=decision_pin.revision,
        non_claims=["accepted execution maturity does not update claim trust"],
        created_at=_utc(now).isoformat(),
    )
    repository = RecordRepository(ws, actor=actor)

    def write_result(_application_id: str) -> PinnedRecordRef:
        write = repository.write("execution_baselines", record, body="# Execution Baseline\n")
        return PinnedRecordRef(write.record_ref, write.content_hash, write.revision)

    def resolve_result(_application_id: str) -> PinnedRecordRef | None:
        ref = f"execution_baseline:{baseline_id}"
        return pin_current_record(ws, ref) if repository.read(ref).status == "found" else None

    def validate_result(_application_id: str, result: PinnedRecordRef) -> None:
        stored = get_record_version(ws, result).record
        if (
            result.record_ref != f"execution_baseline:{baseline_id}"
            or not isinstance(stored, ExecutionBaselineRecord)
            or _sha256_json(asdict(stored)) != _sha256_json(asdict(record))
        ):
            raise ValueError("execution baseline result content does not match application")

    application = apply_bound_checkpoint_action(
        ws,
        binding=binding,
        request_ref=checkpoint_request_ref,
        decision_ref=decision_pin,
        action_payload=request.action_payload(),
        result_writer=write_result,
        result_resolver=resolve_result,
        result_validator=validate_result,
        actor=actor,
        now=now,
    )
    assert application.result_ref is not None
    return BaselineAcceptanceResult(
        baseline_ref=application.result_ref,
        checkpoint_application_receipt_ref=application.receipt_ref,
        replayed=application.replayed,
    )


def project_execution_maturity(
    ws: WorkspacePaths,
    run_ref: PinnedRecordRef | Mapping[str, Any],
) -> ExecutionMaturityProjection:
    pin = _coerce_pin(run_ref)
    run = get_record_version(ws, pin).record
    if not isinstance(run, ToolRunRecord):
        raise ValueError("maturity projection requires a tool run")
    matches = []
    report = RecordRepository(ws, actor=_reader_actor()).list("execution_baselines")
    if report.malformed:
        raise ValueError("execution baselines are not exhaustively readable")
    for baseline in report.records:
        if (
            isinstance(baseline, ExecutionBaselineRecord)
            and baseline.status == "active"
            and baseline.run_ref == pin.record_ref
            and baseline.run_hash == pin.content_hash
            and baseline.run_revision == pin.revision
        ):
            matches.append(pin_current_record(ws, f"execution_baseline:{baseline.baseline_id}"))
    if len(matches) > 1:
        raise ValueError("multiple active execution baselines target one exact run")
    return ExecutionMaturityProjection(
        run_ref=pin,
        recorded_maturity=run.recorded_maturity,
        effective_maturity="accepted_baseline" if matches else run.recorded_maturity,
        active_baseline_ref=matches[0] if matches else None,
    )


def _core_pins(run: ToolRunRecord, reasons: list[str]) -> tuple[PinnedRecordRef, ...]:
    values = (
        ("recipe", run.recipe_ref, run.recipe_hash, run.recipe_revision),
        ("code state", run.code_state_ref, run.code_state_hash, run.code_state_revision),
        ("environment", run.environment_ref, run.environment_hash, run.environment_revision),
    )
    pins = []
    for label, ref, content_hash, revision in values:
        if not ref or not content_hash or not revision:
            reasons.append(f"exact {label} ref is required")
        else:
            pins.append(PinnedRecordRef(ref, content_hash, revision))
    return tuple(pins)


def _validate_core(ws, run, pins, reasons):
    try:
        recipe, code, environment = [get_record_version(ws, pin).record for pin in pins]
    except Exception as exc:  # noqa: BLE001 - readiness reports stale exact dependencies.
        reasons.append(f"exact core dependency is unreadable: {exc}")
        return
    if not isinstance(recipe, ToolRecipeRecord) or recipe.recipe_id != run.recipe_id:
        reasons.append("exact recipe does not match run")
    if not isinstance(code, CodeStateRecord) or len(code.upstream_commit) != 40:
        reasons.append("exact code state is not reproducible")
    elif code.dirty and not (code.patch_manifest_ref and code.patch_manifest_hash and code.patch_manifest_revision):
        reasons.append("dirty code state lacks an exact patch manifest")
    if not isinstance(environment, ExecutionEnvironmentRecord) or not environment.executable_hashes:
        reasons.append("exact execution environment lacks executable hashes")


def _validate_result(ws, run, run_pin, pin, reasons):
    try:
        result = get_record_version(ws, pin).record
    except Exception as exc:  # noqa: BLE001 - readiness reports stale validation.
        reasons.append(f"validation result is unreadable: {pin.record_ref}: {exc}")
        return
    expected_output_hash = hashlib.sha256(
        json.dumps(run.output_manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if not isinstance(result, ValidationResultRecord) or any((
        result.status != "passed",
        bool(result.missing_outputs),
        not result.contract_ref,
        not result.contract_hash,
        result.contract_revision < 1,
        result.tool_run_ref != run_pin.record_ref,
        result.tool_run_hash != run_pin.content_hash,
        result.tool_run_revision != run_pin.revision,
        result.recipe_ref != run.recipe_ref,
        result.recipe_hash != run.recipe_hash,
        result.recipe_revision != run.recipe_revision,
        result.executor_id != run.executor_id,
        result.executor_version != run.executor_version,
        result.executor_hash != run.executor_hash,
        result.output_manifest_hash != expected_output_hash,
        not result.failure_contract_hash,
    )):
        reasons.append(f"validation result is not exact and passed: {pin.record_ref}")
        return
    try:
        contract = get_record_version(
            ws,
            PinnedRecordRef(
                result.contract_ref,
                result.contract_hash,
                result.contract_revision,
            ),
        ).record
    except Exception as exc:  # noqa: BLE001 - exact contract is mandatory.
        reasons.append(f"validation contract is unreadable: {result.contract_ref}: {exc}")
        return
    if not isinstance(contract, ValidationContractRecord) or contract.contract_id != result.contract_id:
        reasons.append("validation contract does not match validation result")


def _coerce_pin(value):
    if isinstance(value, PinnedRecordRef):
        return value
    return PinnedRecordRef(str(value.get("record_ref") or ""), str(value.get("content_hash") or ""), value.get("revision"))


def _utc(value):
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must include timezone")
    return current.astimezone(UTC)


def _sha256_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _reader_actor():
    return RecordActor(actor_type="tool", actor_id="execution-maturity-projection", host="aitp-v5")
