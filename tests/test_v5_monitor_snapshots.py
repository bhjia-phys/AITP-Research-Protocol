from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="monitor-test", host="pytest")


def _workspace(tmp_path):
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "compute", context_id="physics", title="Compute")
    claim = create_claim(
        ws,
        topic_id="compute",
        statement="The monitored computation is reproducible.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="outputs are not validated",
    )
    return ws, claim


def _run(
    ws,
    claim,
    *,
    run_id="run-1",
    evidence_status="completed",
    lane="final",
    actual_parameters=None,
):
    from brain.v5.models import ToolRunRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef
    from brain.v5.record_repository import RecordRepository

    run = ToolRunRecord(
        run_id=run_id,
        recipe_id="recipe-v2",
        tool_family="hpc_slurm",
        tool_name="solver",
        topic_id="compute",
        claim_id=claim.claim_id,
        scientific_run_id="scientific-run-1",
        evidence_status=evidence_status,
        lane=lane,
        actual_parameters=actual_parameters or {},
        recorded_maturity="reproducible_candidate",
        exit_status={"code": 0, "state": "COMPLETED"},
    )
    written = RecordRepository(ws, actor=_actor()).write("tool_runs", run)
    return run, PinnedRecordRef(
        record_ref=written.record_ref,
        content_hash=written.content_hash,
        revision=written.revision,
    )


def _snapshot(run, run_ref, *, sequence=1, captured_at=None, state="RUNNING"):
    from brain.v5.models import MonitorSnapshotRecord

    return MonitorSnapshotRecord(
        snapshot_id="",
        topic_id=run.topic_id,
        claim_id=run.claim_id,
        tool_run_id=run.run_id,
        run_dir=f"/runs/{run.run_id}",
        job_id="4243",
        scheduler_state={"state": state},
        captured_at=(captured_at or datetime(2026, 7, 15, 2, 0, tzinfo=UTC)).isoformat(),
        sequence=sequence,
        collector_id="slurm-monitor",
        collector_version="1.0.0",
        immutable=True,
        tool_run_ref=run_ref.record_ref,
        tool_run_hash=run_ref.content_hash,
        tool_run_revision=run_ref.revision,
    )


def test_snapshot_identity_is_deterministic_idempotent_and_conflict_safe(tmp_path):
    from brain.v5.monitor_snapshots import (
        MonitorSnapshotConflict,
        list_monitor_history,
        record_monitor_snapshot_v2,
    )

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim)
    snapshot = _snapshot(run, run_ref)

    first = record_monitor_snapshot_v2(ws, snapshot, actor=_actor())
    replay = record_monitor_snapshot_v2(ws, snapshot, actor=_actor())
    history = list_monitor_history(ws, run_ref)

    assert first.record_ref.startswith("monitor_snapshot:monitor-snapshot-")
    assert replay.status == "unchanged"
    assert replay.content_hash == first.content_hash
    assert len(history.records) == 1
    assert history.records[0].snapshot_id == first.record_ref.split(":", 1)[1]
    assert history.latest_snapshot_ref == history.snapshot_refs[0]
    assert history.status == "complete"
    assert history.can_update_claim_trust is False

    conflicting = replace(snapshot, scheduler_state={"state": "COMPLETED"})
    with pytest.raises(MonitorSnapshotConflict, match="different content"):
        record_monitor_snapshot_v2(ws, conflicting, actor=_actor())


def test_history_is_append_only_ordered_and_retains_earlier_observations(tmp_path):
    from brain.v5.monitor_snapshots import list_monitor_history, record_monitor_snapshot_v2
    from brain.v5.pinned_record_refs import get_record_version

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim)
    first_time = datetime(2026, 7, 15, 2, 0, tzinfo=UTC)
    first = record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, sequence=1, captured_at=first_time, state="RUNNING"),
        actor=_actor(),
    )
    second = record_monitor_snapshot_v2(
        ws,
        _snapshot(
            run,
            run_ref,
            sequence=2,
            captured_at=first_time + timedelta(minutes=5),
            state="COMPLETED",
        ),
        actor=_actor(),
    )

    history = list_monitor_history(ws, run_ref)

    assert [item.sequence for item in history.records] == [1, 2]
    assert [item.scheduler_state["state"] for item in history.records] == [
        "RUNNING",
        "COMPLETED",
    ]
    assert history.records[1].previous_snapshot_ref == first.record_ref
    assert history.records[1].previous_snapshot_hash == first.content_hash
    assert history.records[1].previous_snapshot_revision == first.revision
    assert history.latest_snapshot_ref.record_ref == second.record_ref
    assert get_record_version(ws, history.snapshot_refs[0]).record.scheduler_state == {
        "state": "RUNNING"
    }


def test_sequence_gap_time_regression_and_scope_mismatch_are_rejected(tmp_path):
    from brain.v5.monitor_snapshots import record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim)
    first_time = datetime(2026, 7, 15, 2, 0, tzinfo=UTC)
    record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, captured_at=first_time),
        actor=_actor(),
    )

    with pytest.raises(ValueError, match="next sequence"):
        record_monitor_snapshot_v2(
            ws,
            _snapshot(run, run_ref, sequence=3, captured_at=first_time + timedelta(minutes=2)),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="later than"):
        record_monitor_snapshot_v2(
            ws,
            _snapshot(run, run_ref, sequence=2, captured_at=first_time - timedelta(minutes=1)),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="topic and claim"):
        record_monitor_snapshot_v2(
            ws,
            replace(
                _snapshot(
                    run,
                    run_ref,
                    sequence=2,
                    captured_at=first_time + timedelta(minutes=2),
                ),
                topic_id="foreign-topic",
            ),
            actor=_actor(),
        )


def test_concurrent_sequence_competition_allows_only_one_observation(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from brain.v5.monitor_snapshots import list_monitor_history, record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim)
    barrier = Barrier(2)

    def write_at(minute: int):
        barrier.wait()
        return record_monitor_snapshot_v2(
            ws,
            _snapshot(
                run,
                run_ref,
                captured_at=datetime(2026, 7, 15, 2, minute, tzinfo=UTC),
            ),
            actor=_actor(),
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = []
        for future in (pool.submit(write_at, 1), pool.submit(write_at, 2)):
            try:
                outcomes.append(future.result())
            except ValueError as exc:
                outcomes.append(exc)

    assert sum(not isinstance(item, Exception) for item in outcomes) == 1
    assert any("next sequence" in str(item) for item in outcomes if isinstance(item, Exception))
    assert len(list_monitor_history(ws, run_ref).records) == 1


def test_scheduler_completion_is_process_only_without_outputs_or_validation(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.monitor_snapshots import record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim, evidence_status="accepted_baseline")
    record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, state="COMPLETED"),
        actor=_actor(),
    )

    state = resolve_effective_attempt_state(ws, run_ref)

    assert state.scheduler_status == "completed"
    assert state.output_status == "unknown"
    assert state.attempt_eligible is False
    assert "outputs are not complete" in state.blocking_reasons
    assert state.can_update_claim_trust is False


def test_mutable_evidence_status_cannot_override_latest_monitor(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.monitor_snapshots import record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim, evidence_status="completed")
    record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, state="RUNNING"),
        actor=_actor(),
    )

    state = resolve_effective_attempt_state(ws, run_ref)

    assert state.scheduler_status == "active"
    assert state.attempt_eligible is False
    assert "latest scheduler observation is not completed" in state.blocking_reasons


def test_effective_attempt_applies_topic_local_final_lane_allowlist(tmp_path):
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.lane_contracts import record_lane_contract
    from brain.v5.monitor_snapshots import record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(
        ws,
        claim,
        actual_parameters={"lane_key": "diagnostic-grid"},
    )
    record_lane_contract(
        ws,
        topic_id="compute",
        campaign="production",
        final_allowlist=["production-grid"],
    )
    record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, state="COMPLETED"),
        actor=_actor(),
    )

    state = resolve_effective_attempt_state(ws, run_ref)

    assert state.lane_status == "blocked"
    assert state.attempt_eligible is False
    assert any("not in the final allowlist" in reason for reason in state.blocking_reasons)


def test_hpc_cockpit_uses_effective_attempt_state_not_mutable_run_status(tmp_path):
    from brain.v5.hpc_cockpit import build_hpc_cockpit
    from brain.v5.monitor_snapshots import record_monitor_snapshot_v2

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim, evidence_status="failed_runtime")
    record_monitor_snapshot_v2(
        ws,
        _snapshot(run, run_ref, state="RUNNING"),
        actor=_actor(),
    )

    cockpit = build_hpc_cockpit(ws, "compute")

    assert [item["run_id"] for item in cockpit["active_jobs"]] == [run.run_id]
    assert cockpit["failure_history"] == []
    attempt = cockpit["effective_attempts"][0]
    assert attempt["scheduler_status"] == "active"
    assert attempt["attempt_eligible"] is False
    assert "latest scheduler observation is not completed" in attempt["blocking_reasons"]


def test_monitor_write_policy_requires_canonical_context_and_read_is_nonwriting():
    from brain.v5.policy import evaluate_policy

    denied = evaluate_policy(
        action="record_monitor_snapshot_v2",
        context={"source_kind": "derived_summary", "orientation_only": True},
    )
    allowed = evaluate_policy(
        action="record_monitor_snapshot_v2",
        context={"source_kind": "explicit_user_request", "orientation_only": False},
    )

    assert denied.allowed is False
    assert allowed.allowed is True
    assert allowed.reasons == []


def test_monitor_mcp_surfaces_and_capabilities_are_registered_full_only(tmp_path):
    import json
    from dataclasses import asdict

    from brain.v5.capability_registry import capability_specs
    from brain.v5.mcp_tools import (
        aitp_v5_list_monitor_history,
        aitp_v5_record_monitor_snapshot_v2,
    )
    from brain.v5.public_surfaces import require_valid_public_surface

    ws, claim = _workspace(tmp_path)
    run, run_ref = _run(ws, claim)
    snapshot = _snapshot(run, run_ref, state="RUNNING")

    written = aitp_v5_record_monitor_snapshot_v2(
        str(ws.base),
        record_json=json.dumps(asdict(snapshot)),
    )
    history = aitp_v5_list_monitor_history(
        str(ws.base),
        tool_run_ref=run_ref.record_ref,
        content_hash=run_ref.content_hash,
        revision=run_ref.revision,
    )
    specs = capability_specs()

    assert require_valid_public_surface("monitor_snapshot_write_result", written) == written
    assert require_valid_public_surface("monitor_history", history) == history
    assert written["writes_records"] is True
    assert written["can_update_claim_trust"] is False
    assert history["can_update_kernel_state"] is False
    assert specs["record_monitor_snapshot_v2"].state_effect == "kernel_write"
    assert specs["record_monitor_snapshot_v2"].compact_visibility == "full"
    assert specs["list_monitor_history"].state_effect == "read_only"


def test_monitor_public_contracts_reject_trust_or_write_flag_inflation():
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    write_payload = {
        "ok": True,
        "kind": "monitor_snapshot_write_result",
        "snapshot_id": "s1",
        "record_ref": "monitor_snapshot:s1",
        "content_hash": "a" * 64,
        "revision": 1,
        "writes_records": True,
        "can_update_claim_trust": True,
    }
    history_payload = {
        "ok": True,
        "kind": "monitor_history",
        "status": "complete",
        "tool_run_ref": {},
        "snapshot_refs": [],
        "snapshots": [],
        "errors": [],
        "can_update_kernel_state": True,
        "can_update_claim_trust": False,
    }

    with pytest.raises(ContractError, match="can_update_claim_trust"):
        require_valid_public_surface("monitor_snapshot_write_result", write_payload)
    with pytest.raises(ContractError, match="can_update_kernel_state"):
        require_valid_public_surface("monitor_history", history_payload)
