from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="effective-attempt-test", host="pytest")


def _workspace(tmp_path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute-topic", context_id="theory", title="Compute topic")
    claim = create_claim(
        ws,
        topic_id="compute-topic",
        statement="The final numerical workflow is reproducible.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="attempt state is unresolved",
    )
    return ws, claim


def _run(run_id: str, claim_id: str, **overrides):
    from brain.v5.models import ToolRunRecord

    values = {
        "run_id": run_id,
        "recipe_id": "recipe-v2",
        "tool_family": "hpc_workflow",
        "tool_name": "solver",
        "topic_id": "compute-topic",
        "claim_id": claim_id,
        "scientific_run_id": "scientific-run-1",
        "lane": "final",
        "recorded_maturity": "reproducible_candidate",
        "exit_status": {"code": 0, "state": "COMPLETED"},
        "output_manifest": [],
    }
    values.update(overrides)
    return ToolRunRecord(**values)


def _write(ws, family, record):
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    result = RecordRepository(ws, actor=_actor()).write(family, record)
    return PinnedRecordRef(
        record_ref=result.record_ref,
        content_hash=result.content_hash,
        revision=result.revision,
    )


def _monitor(ws, run, *, sequence=1, state="COMPLETED", output_file_sizes=None):
    from brain.v5.models import MonitorSnapshotRecord
    from brain.v5.pinned_record_refs import pin_current_record

    run_ref = pin_current_record(ws, f"tool_run:{run.run_id}")
    snapshot = MonitorSnapshotRecord(
        snapshot_id=f"monitor-{run.run_id}-{sequence}",
        topic_id=run.topic_id,
        claim_id=run.claim_id,
        tool_run_id=run.run_id,
        run_dir=f"/runs/{run.run_id}",
        job_id=f"job-{run.run_id}",
        scheduler_state={"state": state},
        output_file_sizes=output_file_sizes or {"result.dat": 128},
        captured_at=datetime.now(UTC).isoformat(),
        sequence=sequence,
        collector_id="slurm-monitor",
        collector_version="1.0.0",
        immutable=True,
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
    )
    return _write(ws, "monitor_snapshots", snapshot)


def _output_manifest(
    ws,
    run_id,
    claim_id,
    *,
    status="complete",
    topic_id="compute-topic",
):
    from brain.v5.artifact_blobs import capture_artifact_content
    from brain.v5.models import ArtifactRecord

    blob = capture_artifact_content(ws, f"result:{run_id}\n".encode("utf-8"), actor=_actor())
    artifact = ArtifactRecord(
        artifact_id=f"{run_id}-result",
        topic_id=topic_id,
        claim_id=claim_id,
        artifact_type="result",
        uri=f"aitp-blob://{blob.record.byte_sha256}",
        summary="Exact effective-attempt output.",
        content_hash=blob.record.byte_sha256,
        hash_algorithm="sha256",
        storage_mode="local_sha256",
        artifact_blob_receipt_ref=blob.pinned_ref.record_ref,
        artifact_blob_receipt_hash=blob.pinned_ref.content_hash,
        artifact_blob_receipt_revision=blob.pinned_ref.revision,
    )
    artifact_ref = _write(ws, "artifacts", artifact)
    return [
        {
            "role": "result",
            "artifact_ref": artifact_ref.record_ref,
            "artifact_record_hash": artifact_ref.content_hash,
            "artifact_revision": artifact_ref.revision,
            "content_hash": blob.record.byte_sha256,
            "status": status,
        }
    ]


def test_valid_final_leaf_is_eligible_and_uses_latest_immutable_monitor(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.pinned_record_refs import build_frozen_dependency_manifest

    ws, claim = _workspace(tmp_path)
    first = _run("attempt-1", claim.claim_id)
    leaf = _run(
        "attempt-2",
        claim.claim_id,
        supersedes_run_id=first.run_id,
        output_manifest=_output_manifest(ws, "attempt-2", claim.claim_id),
    )
    _write(ws, "tool_runs", first)
    leaf_ref = _write(ws, "tool_runs", leaf)
    _monitor(ws, leaf, sequence=1, state="RUNNING")
    latest = _monitor(ws, leaf, sequence=2, state="COMPLETED")

    state = resolve_effective_attempt_state(ws, leaf_ref)
    closure = build_frozen_dependency_manifest(ws, [leaf_ref])

    assert state.topology_status == "valid_leaf"
    assert state.effective_run_ref == leaf_ref
    assert [item.record_ref for item in state.attempt_chain] == [
        "tool_run:attempt-1",
        "tool_run:attempt-2",
    ]
    assert state.latest_monitor_ref == latest
    assert state.latest_monitor_sequence == 2
    assert state.scheduler_status == "completed"
    assert state.output_status == "complete"
    assert state.lane_status == "final_eligible"
    assert state.attempt_eligible is True
    assert state.can_update_claim_trust is False
    output_edge = next(
        edge
        for edge in closure.edges
        if edge.owner_ref == leaf_ref.record_ref
        and edge.field_name == "output_manifest[].artifact_ref"
    )
    assert output_edge.target_hash == leaf.output_manifest[0]["artifact_record_hash"]


def test_requested_success_is_not_eligible_after_failed_successor(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    first = _run("attempt-1", claim.claim_id)
    failed = _run(
        "attempt-2",
        claim.claim_id,
        supersedes_run_id=first.run_id,
        exit_status={"code": 1, "state": "FAILED"},
        output_manifest=[],
    )
    first_ref = _write(ws, "tool_runs", first)
    failed_ref = _write(ws, "tool_runs", failed)
    _monitor(ws, first, state="COMPLETED")
    _monitor(ws, failed, state="FAILED", output_file_sizes={})

    state = resolve_effective_attempt_state(ws, first_ref)

    assert state.topology_status == "superseded"
    assert state.effective_run_ref == failed_ref
    assert state.scheduler_status == "failed"
    assert state.output_status == "unknown"
    assert state.attempt_eligible is False
    assert "requested run is superseded" in state.blocking_reasons


def test_attempt_branch_fails_closed(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    root = _run("attempt-root", claim.claim_id)
    left = _run("attempt-left", claim.claim_id, supersedes_run_id=root.run_id)
    right = _run("attempt-right", claim.claim_id, supersedes_run_id=root.run_id)
    root_ref = _write(ws, "tool_runs", root)
    _write(ws, "tool_runs", left)
    _write(ws, "tool_runs", right)

    state = resolve_effective_attempt_state(ws, root_ref)

    assert state.topology_status == "branch"
    assert state.effective_run_ref is None
    assert state.attempt_eligible is False
    assert "attempt chain branches" in state.blocking_reasons


def test_attempt_cycle_and_missing_predecessor_fail_closed(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    cycle_a = _run("cycle-a", claim.claim_id, supersedes_run_id="cycle-b")
    cycle_b = _run("cycle-b", claim.claim_id, supersedes_run_id="cycle-a")
    cycle_ref = _write(ws, "tool_runs", cycle_a)
    _write(ws, "tool_runs", cycle_b)
    missing = _run("missing-child", claim.claim_id, supersedes_run_id="absent-parent")
    missing_ref = _write(ws, "tool_runs", missing)

    cycle_state = resolve_effective_attempt_state(ws, cycle_ref)
    missing_state = resolve_effective_attempt_state(ws, missing_ref)

    assert cycle_state.topology_status == "cycle"
    assert cycle_state.attempt_eligible is False
    assert missing_state.topology_status == "missing_predecessor"
    assert missing_state.attempt_eligible is False


def test_attempt_scope_mismatch_fails_closed(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    root = _run("attempt-root", claim.claim_id)
    child = _run(
        "attempt-child",
        claim.claim_id,
        supersedes_run_id=root.run_id,
        scientific_run_id="different-scientific-run",
    )
    root_ref = _write(ws, "tool_runs", root)
    _write(ws, "tool_runs", child)

    state = resolve_effective_attempt_state(ws, root_ref)

    assert state.topology_status == "scope_mismatch"
    assert state.attempt_eligible is False
    assert "attempt chain scope mismatch" in state.blocking_reasons


def test_completed_scheduler_with_partial_outputs_is_not_eligible(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    partial = _run(
        "attempt-partial",
        claim.claim_id,
        output_manifest=_output_manifest(
            ws,
            "attempt-partial",
            claim.claim_id,
            status="partial",
        ),
    )
    partial_ref = _write(ws, "tool_runs", partial)
    _monitor(ws, partial, state="COMPLETED")

    state = resolve_effective_attempt_state(ws, partial_ref)

    assert state.topology_status == "valid_leaf"
    assert state.scheduler_status == "completed"
    assert state.output_status == "partial"
    assert state.attempt_eligible is False
    assert "outputs are not complete" in state.blocking_reasons


def test_nonexistent_output_artifact_cannot_satisfy_completion(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    run = _run(
        "attempt-fake-output",
        claim.claim_id,
        output_manifest=[
            {
                "role": "result",
                "artifact_ref": "artifact:does-not-exist",
                "artifact_record_hash": "b" * 64,
                "artifact_revision": 1,
                "content_hash": "a" * 64,
                "status": "complete",
            }
        ],
    )
    run_ref = _write(ws, "tool_runs", run)
    _monitor(ws, run, state="COMPLETED")

    state = resolve_effective_attempt_state(ws, run_ref)

    assert state.output_status == "partial"
    assert state.attempt_eligible is False
    assert "outputs are not complete" in state.blocking_reasons


def test_foreign_topic_output_artifact_cannot_satisfy_completion(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    run = _run(
        "attempt-foreign-output",
        claim.claim_id,
        output_manifest=_output_manifest(
            ws,
            "attempt-foreign-output",
            "foreign-claim",
            topic_id="foreign-topic",
        ),
    )
    run_ref = _write(ws, "tool_runs", run)
    _monitor(ws, run, state="COMPLETED")

    state = resolve_effective_attempt_state(ws, run_ref)

    assert state.output_status == "partial"
    assert state.attempt_eligible is False


def test_diagnostic_lane_and_non_candidate_maturity_are_not_eligible(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state

    ws, claim = _workspace(tmp_path)
    diagnostic = _run(
        "attempt-diagnostic",
        claim.claim_id,
        lane="diagnostic",
        recorded_maturity="diagnostic",
        output_manifest=_output_manifest(ws, "attempt-diagnostic", claim.claim_id),
    )
    diagnostic_ref = _write(ws, "tool_runs", diagnostic)
    _monitor(ws, diagnostic, state="COMPLETED")

    state = resolve_effective_attempt_state(ws, diagnostic_ref)

    assert state.lane_status == "diagnostic_only"
    assert state.attempt_eligible is False
    assert "run is not a reproducible candidate" in state.blocking_reasons
    assert "lane is not final-eligible" in state.blocking_reasons


def test_legacy_reverse_only_supersession_is_not_a_verified_leaf(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.store import write_record

    ws, claim = _workspace(tmp_path)
    legacy = asdict(_run("legacy-attempt", claim.claim_id))
    legacy["superseded_by"] = "unresolved-successor"
    write_record(
        ws.registry_dir("tool_runs") / "legacy-attempt.md",
        legacy,
        body="# Legacy reverse-only attempt\n",
    )
    legacy_ref = pin_current_record(ws, "tool_run:legacy-attempt")

    state = resolve_effective_attempt_state(ws, legacy_ref)

    assert state.topology_status == "legacy_reverse_unverified"
    assert state.effective_run_ref is None
    assert state.attempt_eligible is False
    assert "legacy reverse supersession is unverified" in state.blocking_reasons
