from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest


def _slow_side_effect_kernel(inputs):
    time.sleep(2)
    Path(inputs["side_effect_path"]).write_text("late side effect\n", encoding="utf-8")
    return {"absolute_error": 0.0, "within_tolerance": True}


def _large_output_kernel(_inputs):
    return {"padding": "x" * 700_000}


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="bound-execution-test", host="pytest")


def _approval_receipt(secret, checkpoint_id, checkpoint_hash, rationale):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": checkpoint_hash,
        "decision": "approve",
        "rationale_hash": hashlib.sha256(rationale.encode("utf-8")).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": f"bound-execution-{checkpoint_id}",
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _approved_request(
    tmp_path,
    monkeypatch,
    *,
    executor_id="scalar_tolerance_check",
    timeout_seconds=30,
    inputs=None,
):
    from brain.v5.bound_execution import BoundToolExecutionRequest
    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint
    from brain.v5.models import ToolRecipeRecord
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.record_repository import RecordRepository
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute", context_id="theory", title="Compute")
    claim = create_claim(
        ws,
        topic_id="compute",
        statement="A bounded scalar check is reproducible.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="bounded execution is pending",
    )
    repository = RecordRepository(ws, actor=_actor())
    recipe = ToolRecipeRecord(
        recipe_id="scalar-check-v2",
        tool_family="sanity_check",
        tool_name="scalar_tolerance_check",
        purpose="Check one scalar tolerance without shell access.",
        recipe_version="2.0.0",
        required_inputs=["observed", "expected", "tolerance"],
        expected_outputs=["absolute_error", "within_tolerance"],
    )
    repository.write("tool_recipes", recipe)
    recipe_ref = pin_current_record(ws, "tool_recipe:scalar-check-v2")
    intent_write = repository.write(
        "intents",
        {
            "intent_id": "intent-bound-scalar-check",
            "kind": "research_intent",
            "topic_id": "compute",
            "objective": "Execute the exact reviewed scalar check.",
        },
        body="# Bound execution intent\n",
    )
    intent_ref = pin_current_record(ws, intent_write.record_ref)
    claim_ref = pin_current_record(ws, f"claim:{claim.claim_id}")
    request = BoundToolExecutionRequest(
        executor_id=executor_id,
        recipe=recipe_ref,
        topic_id="compute",
        claim_id=claim.claim_id,
        inputs=inputs or {"observed": 1.0, "expected": 1.0, "tolerance": 1e-8},
        argv=("scalar_tolerance_check", "--tolerance", "1e-8"),
        environment_policy={"execution_mode": "safe_builtin", "host": "aitp"},
        write_policy="canonical_records_only",
        network_policy="deny",
        timeout_seconds=timeout_seconds,
        dependency_refs=(claim_ref, recipe_ref),
    )
    now = datetime.now(UTC)
    requested = request_bound_checkpoint(
        ws,
        topic_id="compute",
        claim_id=claim.claim_id,
        reason="Approve the exact safe builtin execution.",
        requested_by="bound-execution-test",
        action="execute_bound_tool",
        action_payload=request.action_payload(),
        intent_ref=intent_ref,
        subject_refs=[claim_ref, recipe_ref],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=["topic:compute", claim_ref.record_ref],
        effect_policy="execution_records_only",
        actor=_actor(),
        now=now,
    )
    secret = b"m2-bound-execution-secret-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact executor, inputs, and authority policies."
    decided = decide_bound_checkpoint(
        ws,
        request_ref=requested.request_ref,
        expected=requested.binding,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=_approval_receipt(
            secret,
            requested.record.checkpoint_id,
            requested.request_ref.content_hash,
            rationale,
        ),
        now=now,
    )
    return ws, request, requested, decided, now


def test_bound_registered_execution_is_exact_idempotent_and_pins_validation(
    tmp_path,
    monkeypatch,
):
    from brain.v5.bound_execution import execute_bound_tool_request
    from brain.v5.models import ToolRunRecord, ValidationResultRecord
    from brain.v5.pinned_record_refs import get_record_version

    ws, request, requested, decided, now = _approved_request(tmp_path, monkeypatch)

    first = execute_bound_tool_request(
        ws,
        request,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    replay = execute_bound_tool_request(
        ws,
        request,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    run = get_record_version(ws, first.tool_run_ref).record
    validation = get_record_version(ws, first.validation_result_ref).record

    assert replay == replace(first, replayed=True)
    assert isinstance(run, ToolRunRecord)
    assert run.executor_id == "scalar_tolerance_check"
    assert run.recipe_ref == request.recipe.record_ref
    assert run.argv == list(request.argv)
    assert run.recorded_maturity == "diagnostic"
    assert isinstance(validation, ValidationResultRecord)
    assert validation.status == "passed"
    assert validation.tool_run_ref == first.tool_run_ref.record_ref
    assert validation.tool_run_hash == first.tool_run_ref.content_hash
    assert validation.tool_run_revision == first.tool_run_ref.revision
    assert first.application_receipt_ref.record_ref.startswith(
        "checkpoint_application_receipt:"
    )
    assert first.can_update_claim_trust is False


def test_bound_replay_uses_receipt_pinned_validation_after_current_revision(
    tmp_path,
    monkeypatch,
):
    from brain.v5.bound_execution import execute_bound_tool_request
    from brain.v5.models import ValidationResultRecord
    from brain.v5.pinned_record_refs import get_record_version
    from brain.v5.record_repository import RecordRepository, WritePolicy

    ws, request, requested, decided, now = _approved_request(tmp_path, monkeypatch)
    first = execute_bound_tool_request(
        ws,
        request,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )
    original = get_record_version(ws, first.validation_result_ref).record
    assert isinstance(original, ValidationResultRecord)
    RecordRepository(ws, actor=_actor()).write(
        "validation_results",
        replace(original, status="failed", summary="Later diagnostic revision."),
        policy=WritePolicy(
            mode="revision",
            expected_hash=first.validation_result_ref.content_hash,
        ),
    )

    replay = execute_bound_tool_request(
        ws,
        request,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )

    assert replay.validation_result_ref == first.validation_result_ref
    assert replay.tool_run_ref == first.tool_run_ref
    assert get_record_version(ws, replay.validation_result_ref).record.status == "passed"


def test_bound_resolver_rejects_same_id_validation_with_wrong_semantics(
    tmp_path,
    monkeypatch,
):
    from brain.v5 import bound_execution
    from brain.v5.models import ValidationResultRecord
    from brain.v5.record_repository import RecordRepository

    ws, request, requested, decided, now = _approved_request(tmp_path, monkeypatch)

    def write_wrong_result(*args, **kwargs):
        application_id = kwargs["application_id"]
        RecordRepository(ws, actor=_actor()).write(
            "validation_results",
            ValidationResultRecord(
                result_id=bound_execution._validation_id(application_id),
                topic_id="wrong-topic",
                claim_id="wrong-claim",
                contract_id="wrong-contract",
                tool_run_id="wrong-run",
                status="passed",
            ),
        )
        raise RuntimeError("crashed after writing a colliding result")

    monkeypatch.setattr(bound_execution, "_execute_and_write", write_wrong_result)

    with pytest.raises(ValueError, match="content does not match"):
        bound_execution.execute_bound_tool_request(
            ws,
            request,
            binding=requested.binding,
            request_ref=requested.request_ref,
            decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )


def test_bound_resolver_rejects_schema_valid_but_inconsistent_output_status(
    tmp_path,
    monkeypatch,
):
    from brain.v5 import bound_execution
    from brain.v5.models import ToolRunRecord, ValidationResultRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    ws, request, requested, decided, now = _approved_request(tmp_path, monkeypatch)

    def write_inconsistent_result(*args, **kwargs):
        application_id = kwargs["application_id"]
        spec = kwargs["spec"]
        recipe = kwargs["recipe"]
        executor_hash = kwargs["executor_hash"]
        repository = RecordRepository(ws, actor=_actor())
        outputs = {"absolute_error": 0.0, "within_tolerance": False}
        run = ToolRunRecord(
            run_id=bound_execution._run_id(application_id),
            recipe_id=recipe.recipe_id,
            tool_family=spec.tool_family,
            tool_name=spec.tool_name,
            topic_id=request.topic_id,
            claim_id=request.claim_id,
            inputs=dict(request.inputs),
            outputs=outputs,
            environment=dict(request.environment_policy),
            evidence_status="supports",
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
            completed_at=now.isoformat(),
            exit_status={"code": 0, "state": "COMPLETED"},
            recorded_maturity="diagnostic",
        )
        run_write = repository.write("tool_runs", run)
        run_ref = PinnedRecordRef(
            run_write.record_ref,
            run_write.content_hash,
            run_write.revision,
        )
        validation = ValidationResultRecord(
            result_id=bound_execution._validation_id(application_id),
            topic_id=request.topic_id,
            claim_id=request.claim_id,
            contract_id=f"builtin-executor:{spec.executor_id}:{spec.version}",
            tool_run_id=run.run_id,
            status="passed",
            checked_outputs=list(spec.output_schema["required"]),
            tool_run_ref=run_ref.record_ref,
            tool_run_hash=run_ref.content_hash,
            tool_run_revision=run_ref.revision,
            recipe_ref=request.recipe.record_ref,
            recipe_hash=request.recipe.content_hash,
            recipe_revision=request.recipe.revision,
            executor_id=spec.executor_id,
            executor_version=spec.version,
            executor_hash=executor_hash,
            output_manifest_hash=bound_execution._sha256_json(outputs),
            failure_contract_hash=bound_execution._sha256_json(spec.output_schema),
        )
        repository.write("validation_results", validation)
        raise RuntimeError("crashed after writing inconsistent records")

    monkeypatch.setattr(bound_execution, "_execute_and_write", write_inconsistent_result)

    with pytest.raises(ValueError, match="content does not match"):
        bound_execution.execute_bound_tool_request(
            ws,
            request,
            binding=requested.binding,
            request_ref=requested.request_ref,
            decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )


def test_unknown_executor_cannot_consume_bound_checkpoint(tmp_path, monkeypatch):
    from brain.v5.bound_execution import execute_bound_tool_request
    from brain.v5.record_repository import RecordRepository

    ws, request, requested, decided, now = _approved_request(
        tmp_path,
        monkeypatch,
        executor_id="unregistered-shell",
    )

    with pytest.raises(ValueError, match="registered M2 executor"):
        execute_bound_tool_request(
            ws,
            request,
            binding=requested.binding,
            request_ref=requested.request_ref,
            decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )

    assert RecordRepository(ws, actor=_actor()).list("tool_runs").loaded_count == 0
    assert (
        RecordRepository(ws, actor=_actor())
        .list("checkpoint_application_receipts")
        .loaded_count
        == 0
    )


def test_bound_executor_timeout_is_enforced_and_records_failed_application(
    tmp_path,
    monkeypatch,
):
    from dataclasses import replace as dc_replace

    from brain.v5 import bound_execution
    from brain.v5.checkpoint_transactions import CheckpointApplicationFailed
    from brain.v5.record_repository import RecordRepository

    side_effect = tmp_path / "late-side-effect.txt"
    ws, request, requested, decided, now = _approved_request(
        tmp_path,
        monkeypatch,
        timeout_seconds=1,
        inputs={"side_effect_path": str(side_effect)},
    )
    original = bound_execution.builtin_tool_executors()[request.executor_id]

    monkeypatch.setattr(
        bound_execution,
        "builtin_tool_executors",
        lambda: {
            request.executor_id: dc_replace(
                original,
                input_schema={
                    "type": "object",
                    "required": ["side_effect_path"],
                    "properties": {"side_effect_path": {"type": "string"}},
                },
                run=_slow_side_effect_kernel,
            )
        },
    )
    started = time.monotonic()

    with pytest.raises(CheckpointApplicationFailed, match="timed out"):
        bound_execution.execute_bound_tool_request(
            ws,
            request,
            binding=requested.binding,
            request_ref=requested.request_ref,
            decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )

    assert time.monotonic() - started < 1.8
    receipts = RecordRepository(ws, actor=_actor()).list(
        "checkpoint_application_receipts"
    )
    assert receipts.records[0].status == "failed"
    time.sleep(1.2)
    assert not side_effect.exists()


def test_bound_executor_drains_large_result_before_joining_worker(tmp_path, monkeypatch):
    from dataclasses import replace as dc_replace

    from brain.v5 import bound_execution

    ws, request, requested, decided, now = _approved_request(
        tmp_path,
        monkeypatch,
        timeout_seconds=3,
    )
    original = bound_execution.builtin_tool_executors()[request.executor_id]
    monkeypatch.setattr(
        bound_execution,
        "builtin_tool_executors",
        lambda: {
            request.executor_id: dc_replace(
                original,
                output_schema={
                    "type": "object",
                    "required": ["padding"],
                    "properties": {"padding": {"type": "string"}},
                },
                run=_large_output_kernel,
            )
        },
    )

    receipt = bound_execution.execute_bound_tool_request(
        ws,
        request,
        binding=requested.binding,
        request_ref=requested.request_ref,
        decision_ref=decided.decision_ref,
        actor=_actor(),
        now=now,
    )

    assert receipt.validation_result_ref.record_ref.startswith("validation_result:")

@pytest.mark.parametrize(
    "change, message",
    [
        ({"network_policy": "allow"}, "network policy"),
        ({"write_policy": "workspace_write"}, "write policy"),
        ({"timeout_seconds": 0}, "timeout"),
    ],
)
def test_bound_execution_rejects_authority_policy_drift_before_application(
    tmp_path,
    monkeypatch,
    change,
    message,
):
    from brain.v5.bound_execution import execute_bound_tool_request

    ws, request, requested, decided, now = _approved_request(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match=message):
        execute_bound_tool_request(
            ws,
            replace(request, **change),
            binding=requested.binding,
            request_ref=requested.request_ref,
            decision_ref=decided.decision_ref,
            actor=_actor(),
            now=now,
        )
