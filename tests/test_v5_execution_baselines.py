from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="baseline-test", host="pytest")


def _write(ws, family, record):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    write = RecordRepository(ws, actor=_actor()).write(family, record)
    return PinnedRecordRef(write.record_ref, write.content_hash, write.revision)


def _approval(secret, checkpoint_id, checkpoint_hash, rationale):
    now = datetime.now(UTC)
    payload = {
        "version": "v1",
        "checkpoint_id": checkpoint_id,
        "checkpoint_content_hash": checkpoint_hash,
        "decision": "approve",
        "rationale_hash": hashlib.sha256(rationale.encode()).hexdigest(),
        "decided_by": "samur",
        "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "nonce": f"baseline-{checkpoint_id}",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return {**payload, "signature": hmac.new(secret, encoded, hashlib.sha256).hexdigest()}


def _ready_chain(tmp_path):
    from brain.v5.artifact_blobs import capture_artifact_content
    from brain.v5.execution_environments import record_execution_environment
    from brain.v5.execution_writers import (
        record_code_state_v2,
        record_tool_recipe_v2,
        record_tool_run_v2,
    )
    from brain.v5.models import (
        ArtifactRecord,
        CodeStateRecord,
        ExecutionEnvironmentRecord,
        MonitorSnapshotRecord,
        ToolRecipeRecord,
        ToolRunRecord,
        ValidationContractRecord,
        ValidationResultRecord,
    )
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute", context_id="theory", title="Compute")
    claim = create_claim(
        ws,
        topic_id="compute",
        statement="The exact final run is reproducible.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="baseline review pending",
    )
    recipe = ToolRecipeRecord(
        recipe_id="solver-v2",
        tool_family="solver",
        tool_name="solver",
        purpose="Pinned deterministic solver.",
        recipe_version="2.0.0",
    )
    recipe_write = record_tool_recipe_v2(ws, recipe, actor=_actor())
    recipe_ref = pin_current_record(ws, recipe_write.record_ref)
    code = CodeStateRecord(
        code_state_id="solver-code",
        repo_id="solver",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="main",
        worktree_path="/work/solver",
        dirty=False,
    )
    code_write = record_code_state_v2(ws, code, actor=_actor())
    code_ref = pin_current_record(ws, code_write.record_ref)
    environment = ExecutionEnvironmentRecord(
        environment_id="solver-env",
        host="cluster",
        operating_system="Linux",
        architecture="x86_64",
        executable_paths={"solver": "/opt/solver"},
        executable_hashes={"solver": "b" * 64},
        created_at="2026-07-15T00:00:00+00:00",
    )
    env_write = record_execution_environment(ws, environment, actor=_actor())
    env_ref = pin_current_record(ws, env_write.record_ref)
    blob = capture_artifact_content(ws, b"validated-result\n", actor=_actor())
    artifact = ArtifactRecord(
        artifact_id="solver-output",
        topic_id="compute",
        claim_id=claim.claim_id,
        artifact_type="result",
        uri=f"aitp-blob://{blob.record.byte_sha256}",
        summary="Pinned solver output.",
        content_hash=blob.record.byte_sha256,
        hash_algorithm="sha256",
        role="validated_output",
        storage_mode="local_sha256",
        artifact_blob_receipt_ref=blob.pinned_ref.record_ref,
        artifact_blob_receipt_hash=blob.pinned_ref.content_hash,
        artifact_blob_receipt_revision=blob.pinned_ref.revision,
    )
    artifact_ref = _write(ws, "artifacts", artifact)
    outputs = {"value": 1.0, "within_tolerance": True}
    run = ToolRunRecord(
        run_id="solver-final-run",
        recipe_id=recipe.recipe_id,
        tool_family="solver",
        tool_name="solver",
        topic_id="compute",
        claim_id=claim.claim_id,
        inputs={"parameter": 1.0},
        outputs=outputs,
        scientific_run_id="solver-scientific-run",
        lane="final",
        recipe_ref=recipe_ref.record_ref,
        recipe_hash=recipe_ref.content_hash,
        recipe_revision=recipe_ref.revision,
        code_state_ref=code_ref.record_ref,
        code_state_hash=code_ref.content_hash,
        code_state_revision=code_ref.revision,
        environment_ref=env_ref.record_ref,
        environment_hash=env_ref.content_hash,
        environment_revision=env_ref.revision,
        output_manifest=[{
            "role": "validated_output",
            "artifact_ref": artifact_ref.record_ref,
            "artifact_record_hash": artifact_ref.content_hash,
            "artifact_revision": artifact_ref.revision,
            "content_hash": blob.record.byte_sha256,
            "status": "complete",
        }],
        exit_status={"code": 0, "state": "COMPLETED"},
        executor_id="solver-executor",
        executor_version="1.0.0",
        executor_hash="c" * 64,
        recorded_maturity="reproducible_candidate",
    )
    run_write = record_tool_run_v2(ws, run, actor=_actor())
    run_ref = pin_current_record(ws, run_write.record_ref)
    monitor = MonitorSnapshotRecord(
        snapshot_id="solver-monitor-1",
        topic_id="compute",
        claim_id=claim.claim_id,
        tool_run_id=run.run_id,
        run_dir="/runs/solver-final-run",
        job_id="42",
        scheduler_state={"state": "COMPLETED"},
        output_file_sizes={"result.dat": 17},
        captured_at=datetime.now(UTC).isoformat(),
        sequence=1,
        collector_id="monitor",
        collector_version="1.0.0",
        immutable=True,
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
    )
    monitor_ref = _write(ws, "monitor_snapshots", monitor)
    contract = ValidationContractRecord(
        contract_id="solver-contract",
        topic_id="compute",
        claim_id=claim.claim_id,
        required_checks=["validated output"],
        failure_modes=["numerical mismatch"],
        required_evidence_outputs=["validated_output"],
        tool_recipe_refs=[recipe_ref.record_ref],
        failure_contract_hash="d" * 64,
    )
    contract_ref = _write(ws, "validation_contracts", contract)
    validation = ValidationResultRecord(
        result_id="solver-validation",
        topic_id="compute",
        claim_id=claim.claim_id,
        contract_id="solver-contract",
        tool_run_id=run.run_id,
        status="passed",
        checked_outputs=["validated_output"],
        contract_ref=contract_ref.record_ref,
        contract_hash=contract_ref.content_hash,
        contract_revision=contract_ref.revision,
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
        recipe_ref=recipe_ref.record_ref,
        recipe_hash=recipe_ref.content_hash,
        recipe_revision=recipe_ref.revision,
        executor_id=run.executor_id,
        executor_version=run.executor_version,
        executor_hash=run.executor_hash,
        output_manifest_hash=hashlib.sha256(
            json.dumps(run.output_manifest, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        failure_contract_hash="d" * 64,
    )
    validation_ref = _write(ws, "validation_results", validation)
    claim_ref = pin_current_record(ws, f"claim:{claim.claim_id}")
    return ws, claim, claim_ref, run, run_ref, validation_ref, monitor_ref


def test_ready_baseline_requires_bound_checkpoint_and_projects_maturity(tmp_path, monkeypatch):
    from dataclasses import replace

    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint
    from brain.v5.execution_baselines import (
        BaselineAcceptanceRequest,
        accept_execution_baseline,
        assess_baseline_readiness,
        project_execution_maturity,
    )
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version
    from brain.v5.record_repository import RecordRepository, WritePolicy

    ws, claim, claim_ref, run, run_ref, validation_ref, monitor_ref = _ready_chain(tmp_path)
    request = BaselineAcceptanceRequest(run_ref=run_ref, validation_refs=(validation_ref,))
    readiness = assess_baseline_readiness(ws, request)
    assert readiness.ready is True
    assert monitor_ref in readiness.frozen_dependencies.nodes
    now = datetime.now(UTC)
    checkpoint = request_bound_checkpoint(
        ws,
        topic_id="compute",
        claim_id=claim.claim_id,
        reason="Accept exact reproducible execution baseline.",
        requested_by="baseline-test",
        action="accept_execution_baseline",
        action_payload=request.action_payload(),
        intent_ref=claim_ref,
        subject_refs=list(readiness.frozen_dependencies.nodes),
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=["topic:compute", f"claim:{claim.claim_id}"],
        effect_policy="execution_maturity_only",
        actor=_actor(),
        now=now,
    )
    secret = b"baseline-approval-secret-32-bytes"
    monkeypatch.setenv("AITP_HUMAN_APPROVAL_HMAC_KEY_B64", base64.b64encode(secret).decode())
    rationale = "Reviewed the exact frozen dependency closure."
    decision = decide_bound_checkpoint(
        ws,
        request_ref=checkpoint.request_ref,
        expected=checkpoint.binding,
        decision="approve",
        rationale=rationale,
        decided_by="samur",
        approval_receipt=_approval(secret, checkpoint.record.checkpoint_id, checkpoint.request_ref.content_hash, rationale),
        now=now,
    )
    accepted = accept_execution_baseline(
        ws,
        request,
        binding=checkpoint.binding,
        checkpoint_request_ref=checkpoint.request_ref,
        checkpoint_decision_ref=decision.decision_ref,
        actor=_actor(),
        now=now,
    )
    replay = accept_execution_baseline(
        ws,
        request,
        binding=checkpoint.binding,
        checkpoint_request_ref=checkpoint.request_ref,
        checkpoint_decision_ref=decision.decision_ref,
        actor=_actor(),
        now=now,
    )
    projection = project_execution_maturity(ws, run_ref)

    assert replay.baseline_ref == accepted.baseline_ref
    assert projection.recorded_maturity == "reproducible_candidate"
    assert projection.effective_maturity == "accepted_baseline"
    assert projection.active_baseline_ref == accepted.baseline_ref
    assert get_record_version(ws, run_ref).record.recorded_maturity == "reproducible_candidate"
    assert accepted.can_update_claim_trust is False

    baseline = get_record_version(ws, accepted.baseline_ref).record
    recipe_pin = PinnedRecordRef(
        baseline.recipe_ref,
        baseline.recipe_hash,
        baseline.recipe_revision,
    )
    recipe_version = get_record_version(ws, recipe_pin)
    RecordRepository(ws, actor=_actor()).write(
        "tool_recipes",
        replace(recipe_version.record, purpose="Later recipe documentation revision."),
        policy=WritePolicy(mode="revision", expected_hash=recipe_pin.content_hash),
    )
    archived = get_record_version(ws, recipe_pin)

    assert archived.version_source == "archive"
    assert archived.record.purpose == "Pinned deterministic solver."
    assert project_execution_maturity(ws, run_ref).active_baseline_ref == accepted.baseline_ref


def test_baseline_readiness_rejects_diagnostic_run(tmp_path):
    from dataclasses import replace

    from brain.v5.execution_baselines import BaselineAcceptanceRequest, assess_baseline_readiness
    from brain.v5.record_repository import RecordRepository, WritePolicy

    ws, _claim, _claim_ref, run, run_ref, validation_ref, _monitor_ref = _ready_chain(tmp_path)
    RecordRepository(ws, actor=_actor()).write(
        "tool_runs",
        replace(run, recorded_maturity="diagnostic"),
        policy=WritePolicy(mode="revision", expected_hash=run_ref.content_hash),
    )
    from brain.v5.pinned_record_refs import pin_current_record

    current = pin_current_record(ws, run_ref.record_ref)
    readiness = assess_baseline_readiness(
        ws,
        BaselineAcceptanceRequest(run_ref=current, validation_refs=(validation_ref,)),
    )
    assert readiness.ready is False
    assert "run is not a reproducible candidate" in readiness.blocking_reasons


def test_baseline_acceptance_rejects_checkpoint_not_bound_to_full_closure(tmp_path):
    from brain.v5.checkpoint_bindings import request_bound_checkpoint
    from brain.v5.execution_baselines import (
        BaselineAcceptanceRequest,
        accept_execution_baseline,
    )

    ws, claim, claim_ref, _run, run_ref, validation_ref, _monitor_ref = _ready_chain(tmp_path)
    request = BaselineAcceptanceRequest(run_ref=run_ref, validation_refs=(validation_ref,))
    now = datetime.now(UTC)
    checkpoint = request_bound_checkpoint(
        ws,
        topic_id="compute",
        claim_id=claim.claim_id,
        reason="Incomplete baseline review fixture.",
        requested_by="baseline-test",
        action="accept_execution_baseline",
        action_payload=request.action_payload(),
        intent_ref=claim_ref,
        subject_refs=[run_ref],
        options=["approve", "reject"],
        expires_at=(now + timedelta(minutes=10)).isoformat(),
        replay_policy="exact_idempotent",
        target_scope_refs=["topic:compute", f"claim:{claim.claim_id}"],
        effect_policy="execution_maturity_only",
        actor=_actor(),
        now=now,
    )
    with pytest.raises(ValueError, match="subjects do not match"):
        accept_execution_baseline(
            ws,
            request,
            binding=checkpoint.binding,
            checkpoint_request_ref=checkpoint.request_ref,
            checkpoint_decision_ref=checkpoint.request_ref,
            actor=_actor(),
            now=now,
        )
