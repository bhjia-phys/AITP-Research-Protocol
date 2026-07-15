"""Checkpoint-bound execution of deterministic registered M2 executors."""

from __future__ import annotations

import hashlib
import inspect
import json
import multiprocessing
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from brain.v5.checkpoint_bindings import CheckpointSubjectBinding
from brain.v5.checkpoint_transactions import apply_bound_checkpoint_action
from brain.v5.execution_scope_policy import assess_execution_scope
from brain.v5.models import ToolRecipeRecord, ToolRunRecord, ValidationResultRecord
from brain.v5.paths import WorkspacePaths
from brain.v5.pinned_record_refs import (
    PinnedRecordRef,
    get_record_version,
    pin_current_record,
)
from brain.v5.record_envelope import RecordActor
from brain.v5.record_repository import RecordRepository
from brain.v5.tool_executor_kernels import infer_evidence_status
from brain.v5.tool_executors import ToolExecutorSpec, builtin_tool_executors


@dataclass(frozen=True)
class BoundToolExecutionRequest:
    executor_id: str
    recipe: PinnedRecordRef
    topic_id: str
    claim_id: str
    inputs: Mapping[str, Any]
    argv: tuple[str, ...]
    environment_policy: Mapping[str, Any]
    write_policy: str
    network_policy: str
    timeout_seconds: int
    dependency_refs: tuple[PinnedRecordRef, ...]
    revalidation_decision_refs: tuple[PinnedRecordRef, ...] = ()

    def action_payload(self) -> dict[str, Any]:
        return {
            "executor_id": self.executor_id,
            "recipe": asdict(self.recipe),
            "topic_id": self.topic_id,
            "claim_id": self.claim_id,
            "inputs": dict(self.inputs),
            "argv": list(self.argv),
            "environment_policy": dict(self.environment_policy),
            "write_policy": self.write_policy,
            "network_policy": self.network_policy,
            "timeout_seconds": self.timeout_seconds,
            "dependency_refs": [
                asdict(item) for item in sorted(self.dependency_refs)
            ],
            "revalidation_decision_refs": [
                asdict(item) for item in sorted(self.revalidation_decision_refs)
            ],
        }


@dataclass(frozen=True)
class BoundExecutionReceipt:
    executor_id: str
    executor_version: str
    executor_hash: str
    tool_run_ref: PinnedRecordRef
    validation_result_ref: PinnedRecordRef
    application_receipt_ref: PinnedRecordRef
    replayed: bool
    can_update_claim_trust: bool = False


def execute_bound_tool_request(
    ws: WorkspacePaths,
    request: BoundToolExecutionRequest,
    *,
    binding: CheckpointSubjectBinding,
    request_ref: PinnedRecordRef | Mapping[str, Any],
    decision_ref: PinnedRecordRef | Mapping[str, Any],
    actor: RecordActor,
    now: datetime | None = None,
) -> BoundExecutionReceipt:
    """Execute one exact safe builtin through the checkpoint transaction."""

    spec = _registered_executor(request.executor_id)
    _validate_authority_policy(request, spec)
    if binding.action != "execute_bound_tool":
        raise ValueError("bound execution checkpoint action does not match")
    if binding.effect_policy != "execution_records_only":
        raise ValueError("bound execution checkpoint effect policy does not match")

    recipe_version = get_record_version(ws, request.recipe)
    recipe = recipe_version.record
    if not isinstance(recipe, ToolRecipeRecord):
        raise ValueError("bound execution recipe must pin a tool recipe")
    if recipe.tool_family != spec.tool_family or recipe.tool_name != spec.tool_name:
        raise ValueError("registered executor does not match the exact recipe")
    if request.recipe not in request.dependency_refs:
        raise ValueError("dependency refs must include the exact recipe")
    if set(binding.subjects) != set(request.dependency_refs):
        raise ValueError("bound execution subjects must equal the exact dependencies")

    scope = assess_execution_scope(
        ws,
        operation="execute_bound_tool",
        consumer_scope=(f"topic:{request.topic_id}", f"claim:{request.claim_id}"),
        dependency_refs=request.dependency_refs,
        revalidation_decision_refs=request.revalidation_decision_refs,
        now=now,
    )
    if scope.decision != "allowed":
        raise ValueError(f"bound execution scope is not allowed: {scope.decision}")

    executor_hash = _executor_hash(spec)

    def write_result(application_id: str) -> PinnedRecordRef:
        return _execute_and_write(
            ws,
            request=request,
            recipe=recipe,
            spec=spec,
            executor_hash=executor_hash,
            application_id=application_id,
            actor=actor,
            now=now,
        )[1]

    def resolve_result(application_id: str) -> PinnedRecordRef | None:
        record_ref = f"validation_result:{_validation_id(application_id)}"
        if RecordRepository(ws, actor=actor).read(record_ref).status != "found":
            return None
        return pin_current_record(ws, record_ref)

    def validate_result(application_id: str, result: PinnedRecordRef) -> None:
        expected = f"validation_result:{_validation_id(application_id)}"
        if result.record_ref != expected:
            raise ValueError("bound execution result does not belong to application")
        validation = get_record_version(ws, result).record
        expected_run_ref = f"tool_run:{_run_id(application_id)}"
        if not isinstance(validation, ValidationResultRecord) or any(
            (
                validation.result_id != _validation_id(application_id),
                validation.topic_id != request.topic_id,
                validation.claim_id != request.claim_id,
                validation.contract_id
                != f"builtin-executor:{spec.executor_id}:{spec.version}",
                validation.tool_run_id != _run_id(application_id),
                validation.tool_run_ref != expected_run_ref,
                not validation.tool_run_hash,
                validation.tool_run_revision < 1,
                validation.recipe_ref != request.recipe.record_ref,
                validation.recipe_hash != request.recipe.content_hash,
                validation.recipe_revision != request.recipe.revision,
                validation.executor_id != spec.executor_id,
                validation.executor_version != spec.version,
                validation.executor_hash != executor_hash,
                validation.failure_contract_hash != _sha256_json(spec.output_schema),
            )
        ):
            raise ValueError("bound execution result content does not match application")
        run_ref = PinnedRecordRef(
            validation.tool_run_ref,
            validation.tool_run_hash,
            validation.tool_run_revision,
        )
        run = get_record_version(ws, run_ref).record
        outputs = run.outputs if isinstance(run, ToolRunRecord) else {}
        if isinstance(run, ToolRunRecord):
            _validate_schema(outputs, spec.output_schema, "bound execution outputs")
        expected_evidence = infer_evidence_status(outputs) if isinstance(run, ToolRunRecord) else ""
        expected_status = {
            "supports": "passed",
            "refutes": "failed",
        }.get(expected_evidence, "inconclusive")
        required_outputs = list(spec.output_schema.get("required") or [])
        expected_checked = [key for key in required_outputs if key in outputs]
        expected_missing = [key for key in required_outputs if key not in outputs]
        if not isinstance(run, ToolRunRecord) or any(
            (
                run.run_id != _run_id(application_id),
                run.scientific_run_id != application_id,
                run.topic_id != request.topic_id,
                run.claim_id != request.claim_id,
                run.recipe_id != recipe.recipe_id,
                run.recipe_ref != request.recipe.record_ref,
                run.executor_id != spec.executor_id,
                run.executor_version != spec.version,
                run.executor_hash != executor_hash,
                run.argv != list(request.argv),
                run.inputs != dict(request.inputs),
                run.environment != dict(request.environment_policy),
                run.recorded_maturity != "diagnostic",
                run.evidence_status != expected_evidence,
                validation.status != expected_status,
                validation.checked_outputs != expected_checked,
                validation.missing_outputs != expected_missing,
                validation.output_manifest_hash != _sha256_json(run.outputs),
            )
        ):
            raise ValueError("bound execution result content does not match application")

    application = apply_bound_checkpoint_action(
        ws,
        binding=binding,
        request_ref=request_ref,
        decision_ref=decision_ref,
        action_payload=request.action_payload(),
        result_writer=write_result,
        result_resolver=resolve_result,
        result_validator=validate_result,
        actor=actor,
        now=now,
    )
    if application.result_ref is None:
        raise RuntimeError("bound execution application did not produce validation")
    validation_ref = application.result_ref
    validation = get_record_version(ws, validation_ref).record
    if (
        not isinstance(validation, ValidationResultRecord)
        or not validation.tool_run_ref
        or not validation.tool_run_hash
    ):
        raise RuntimeError("bound execution validation does not pin an exact tool run")
    tool_run_ref = PinnedRecordRef(
        record_ref=validation.tool_run_ref,
        content_hash=validation.tool_run_hash,
        revision=validation.tool_run_revision,
    )
    run_version = get_record_version(ws, tool_run_ref)
    if not isinstance(run_version.record, ToolRunRecord):
        raise RuntimeError("bound execution validation target is not a tool run")
    return BoundExecutionReceipt(
        executor_id=spec.executor_id,
        executor_version=spec.version,
        executor_hash=executor_hash,
        tool_run_ref=tool_run_ref,
        validation_result_ref=validation_ref,
        application_receipt_ref=application.receipt_ref,
        replayed=application.replayed,
    )


def _execute_and_write(
    ws: WorkspacePaths,
    *,
    request: BoundToolExecutionRequest,
    recipe: ToolRecipeRecord,
    spec: ToolExecutorSpec,
    executor_hash: str,
    application_id: str,
    actor: RecordActor,
    now: datetime | None,
) -> tuple[PinnedRecordRef, PinnedRecordRef]:
    outputs = _run_with_timeout(spec, request)
    if not isinstance(outputs, dict):
        raise TypeError("registered M2 executor output must be an object")
    status = infer_evidence_status(outputs)
    validation_status = {
        "supports": "passed",
        "refutes": "failed",
    }.get(status, "inconclusive")
    completed_at = _utc(now).isoformat()
    run = ToolRunRecord(
        run_id=_run_id(application_id),
        recipe_id=recipe.recipe_id,
        tool_family=spec.tool_family,
        tool_name=spec.tool_name,
        topic_id=request.topic_id,
        claim_id=request.claim_id,
        inputs=dict(request.inputs),
        outputs=outputs,
        environment=dict(request.environment_policy),
        evidence_status=status,
        source_refs=[item.record_ref for item in request.dependency_refs],
        scientific_run_id=application_id,
        lane="diagnostic",
        argv=list(request.argv),
        actual_parameters=dict(request.inputs),
        parameter_provenance={key: "checkpoint_bound_input" for key in request.inputs},
        recipe_ref=request.recipe.record_ref,
        executor_id=spec.executor_id,
        executor_version=spec.version,
        executor_hash=executor_hash,
        completed_at=completed_at,
        exit_status={"code": 0, "state": "COMPLETED"},
        recorded_maturity="diagnostic",
        non_claims=["safe builtin execution does not update claim trust"],
    )
    repository = RecordRepository(ws, actor=actor)
    run_write = repository.write(
        "tool_runs",
        run,
        body=f"# Bound Tool Run\n\nExecutor: `{spec.executor_id}`\n",
    )
    run_ref = PinnedRecordRef(
        record_ref=run_write.record_ref,
        content_hash=run_write.content_hash,
        revision=run_write.revision,
    )
    output_hash = _sha256_json(outputs)
    required_outputs = list(spec.output_schema.get("required") or [])
    validation = ValidationResultRecord(
        result_id=_validation_id(application_id),
        topic_id=request.topic_id,
        claim_id=request.claim_id,
        contract_id=f"builtin-executor:{spec.executor_id}:{spec.version}",
        tool_run_id=run.run_id,
        status=validation_status,
        checked_outputs=[key for key in required_outputs if key in outputs],
        missing_outputs=[key for key in required_outputs if key not in outputs],
        summary="Bound registered executor output contract evaluation.",
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
        recipe_ref=request.recipe.record_ref,
        recipe_hash=request.recipe.content_hash,
        recipe_revision=request.recipe.revision,
        executor_id=spec.executor_id,
        executor_version=spec.version,
        executor_hash=executor_hash,
        output_manifest_hash=output_hash,
        failure_contract_hash=_sha256_json(spec.output_schema),
    )
    validation_write = repository.write(
        "validation_results",
        validation,
        body=(
            "# Bound Execution Validation\n\n"
            f"Status: `{validation_status}`\n"
        ),
    )
    validation_ref = PinnedRecordRef(
        record_ref=validation_write.record_ref,
        content_hash=validation_write.content_hash,
        revision=validation_write.revision,
    )
    return run_ref, validation_ref


def _registered_executor(executor_id: str) -> ToolExecutorSpec:
    spec = builtin_tool_executors().get(str(executor_id).strip())
    if spec is None or spec.execution_mode != "safe_builtin":
        raise ValueError("bound execution requires a registered M2 executor")
    return spec


def _run_with_timeout(
    spec: ToolExecutorSpec,
    request: BoundToolExecutionRequest,
) -> dict[str, Any]:
    context = multiprocessing.get_context("spawn")
    outcome, sender = context.Pipe(duplex=False)
    worker = context.Process(
        target=_invoke_in_subprocess,
        args=(spec.run, dict(request.inputs), sender),
        name=f"aitp-bound-{spec.executor_id}",
        daemon=False,
    )
    worker.start()
    sender.close()
    if not outcome.poll(request.timeout_seconds):
        was_alive = worker.is_alive()
        if was_alive:
            worker.terminate()
        worker.join(timeout=5)
        outcome.close()
        if not was_alive:
            raise RuntimeError("registered M2 executor exited without an outcome")
        raise TimeoutError(
            f"registered M2 executor timed out after {request.timeout_seconds} seconds"
        )
    try:
        kind, value = outcome.recv()
    except EOFError as exc:
        raise RuntimeError("registered M2 executor exited without an outcome") from exc
    finally:
        outcome.close()
    worker.join(timeout=5)
    if worker.is_alive():
        worker.terminate()
        worker.join(timeout=5)
        raise RuntimeError("registered M2 executor did not exit after returning an outcome")
    if kind == "error":
        raise RuntimeError(f"registered M2 executor failed: {value}")
    if not isinstance(value, dict):
        raise TypeError("registered M2 executor output must be an object")
    return value


def _invoke_in_subprocess(run: Any, inputs: dict[str, Any], outcome: Any) -> None:
    try:
        outcome.send(("result", run(inputs)))
    except Exception as exc:  # noqa: BLE001 - serialize a bounded diagnostic only.
        outcome.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        outcome.close()


def _validate_authority_policy(
    request: BoundToolExecutionRequest,
    spec: ToolExecutorSpec,
) -> None:
    if request.network_policy != "deny":
        raise ValueError("bound execution network policy must be deny")
    if request.write_policy != "canonical_records_only":
        raise ValueError("bound execution write policy must be canonical_records_only")
    if not isinstance(request.timeout_seconds, int) or not 1 <= request.timeout_seconds <= 60:
        raise ValueError("bound execution timeout must be between 1 and 60 seconds")
    if request.environment_policy.get("execution_mode") != spec.execution_mode:
        raise ValueError("bound execution environment policy does not match executor mode")
    if not request.argv or any(not isinstance(item, str) or not item for item in request.argv):
        raise ValueError("bound execution argv must contain non-empty strings")
    _validate_schema(request.inputs, spec.input_schema, "bound execution inputs")


def _validate_schema(value: Any, schema: Mapping[str, Any], path: str) -> None:
    kind = schema.get("type")
    object_like = kind == "object" or "required" in schema or "properties" in schema
    if object_like:
        if not isinstance(value, Mapping):
            raise ValueError(f"{path} must be an object")
        for key in schema.get("required") or []:
            if key not in value:
                raise ValueError(f"{path}.{key} is required")
        for key, child in (schema.get("properties") or {}).items():
            if key in value:
                _validate_schema(value[key], child, f"{path}.{key}")
        return
    if kind == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path} must be an array")
        child = schema.get("items")
        if isinstance(child, Mapping):
            for index, item in enumerate(value):
                _validate_schema(item, child, f"{path}[{index}]")
        return
    if kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path} must be a number")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path} is below the minimum")
    elif kind == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
        raise ValueError(f"{path} must be an integer")
    elif kind == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{path} must be a boolean")
    elif kind == "string" and not isinstance(value, str):
        raise ValueError(f"{path} must be a string")


def _executor_hash(spec: ToolExecutorSpec) -> str:
    try:
        source = inspect.getsource(spec.run)
    except (OSError, TypeError) as exc:
        raise ValueError("registered M2 executor source is not inspectable") from exc
    return _sha256_json(
        {
            "executor_id": spec.executor_id,
            "version": spec.version,
            "execution_mode": spec.execution_mode,
            "input_schema": spec.input_schema,
            "output_schema": spec.output_schema,
            "source": source,
        }
    )


def _run_id(application_id: str) -> str:
    return f"bound-run-{application_id.rsplit('-', 1)[-1]}"


def _validation_id(application_id: str) -> str:
    return f"bound-validation-{application_id.rsplit('-', 1)[-1]}"


def _utc(value: datetime | None) -> datetime:
    current = value or datetime.now(UTC)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    return current.astimezone(UTC)


def _sha256_json(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
