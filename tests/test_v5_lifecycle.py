from __future__ import annotations

from pathlib import Path

import pytest


def test_claim_and_evidence_have_default_active_lifecycle():
    from brain.v5.models import ClaimRecord, EvidenceRecord

    claim = ClaimRecord(
        claim_id="claim-x", topic_id="t", statement="s",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    assert claim.lifecycle_status == "active"
    assert claim.rehome_event_id == ""
    assert claim.rehome_target_topic == ""
    assert claim.replaced_by == ""

    evidence = EvidenceRecord(
        evidence_id="ev-x", topic_id="t", claim_id="claim-x",
        evidence_type="bounded_numerical_replay", status="supports_scoped_claim",
        summary="s",
    )
    assert evidence.lifecycle_status == "active"
    assert evidence.replaced_by == ""


def test_lifecycle_event_record_roundtrip(tmp_path):
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import read_record, write_record

    event = LifecycleEventRecord(
        event_id="ev-rehome-claim-x-abcd1234",
        event_type="rehome",
        subject_record_id="claim-x",
        subject_kind="claim",
        from_topic="wrong-topic",
        to_topic="right-topic",
        lifecycle_status="rehomed",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
        replacement_ref="",
        supersedes_event="",
    )
    path = tmp_path / "ev.md"
    write_record(path, event, body="# Rehome event\n")
    loaded = read_record(path, LifecycleEventRecord)
    assert loaded.event_type == "rehome"
    assert loaded.lifecycle_status == "rehomed"
    assert loaded.from_topic == "wrong-topic"
    assert loaded.to_topic == "right-topic"


def test_create_lifecycle_event_is_idempotent(tmp_path):
    from brain.v5.lifecycle_events import create_lifecycle_event
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    args = dict(
        event_type="rehome",
        subject_record_id="claim-x",
        subject_kind="claim",
        from_topic="wrong-topic",
        to_topic="right-topic",
        lifecycle_status="rehomed",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    first = create_lifecycle_event(ws, **args)
    second = create_lifecycle_event(ws, **args)
    assert first.event_id == second.event_id
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events) == 1


def test_create_lifecycle_event_supersede_distinct_keys(tmp_path):
    from brain.v5.lifecycle_events import create_lifecycle_event
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    a = create_lifecycle_event(
        ws, event_type="supersede", subject_record_id="claim-x", subject_kind="claim",
        lifecycle_status="misrouted", reason="r1", operator="o", timestamp="t1",
        replacement_ref="claim-y",
    )
    b = create_lifecycle_event(
        ws, event_type="supersede", subject_record_id="claim-x", subject_kind="claim",
        lifecycle_status="superseded", reason="r2", operator="o", timestamp="t2",
        replacement_ref="claim-y",
    )
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    # same (record, status, replacement) -> one; different status -> two
    assert len(events) == 2
    assert a.event_id != b.event_id
    assert b.supersedes_event == a.event_id
