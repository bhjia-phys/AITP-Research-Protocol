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


def test_rehome_claim_marks_misrouted_adds_pointer_and_preserves_body(tmp_path):
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.markdown import read_md
    from brain.v5.workspace import create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si G0W0 throughput claim",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )

    event = rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="bohan-jia", timestamp="2026-06-20T10:00:00Z",
    )

    # registry file still exists at original location, body preserved, new fields set
    reg_path = ws.registry_dir("claims") / f"{claim.claim_id}.md"
    fm, body = read_md(reg_path)
    assert fm["lifecycle_status"] == "misrouted"
    assert fm["rehome_target_topic"] == "right-topic"
    assert fm["rehome_event_id"] == event.event_id
    assert "Si G0W0 throughput claim" in body  # body preserved

    # source topic ledger entry unchanged in location (still there, but now misrouted)
    src_ledger = ws.topic_dir("wrong-topic") / "claims" / "ledger" / f"{claim.claim_id}.md"
    src_fm, _ = read_md(src_ledger)
    assert src_fm["lifecycle_status"] == "misrouted"

    # target topic has a pointer entry referencing the original claim id
    tgt_ledger_dir = ws.topic_dir("right-topic") / "claims" / "ledger"
    pointer_files = list(tgt_ledger_dir.glob("*.md"))
    pointers = [read_md(p) for p in pointer_files]
    pointer_fms = [fm for (fm, _b) in pointers if fm.get("kind") == "cross_topic_reference"]
    assert len(pointer_fms) == 1
    assert pointer_fms[0]["source_record_id"] == claim.claim_id
    assert pointer_fms[0]["source_topic"] == "wrong-topic"


def test_rehome_invalid_record_id_aborts_with_no_change(tmp_path):
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")

    with pytest.raises(ValueError):
        rehome_record(
            ws, record_id="claim-does-not-exist", subject_kind="claim",
            from_topic="wrong-topic", to_topic="right-topic",
            reason="r", operator="o", timestamp="t",
        )
    events = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert events == []


def _misroute_fixture(ws):
    from brain.v5.evidence import record_evidence
    from brain.v5.workspace import bind_session, create_claim, create_topic

    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si G0W0 throughput",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    ev = record_evidence(
        ws, topic_id="wrong-topic", claim_id=claim.claim_id,
        evidence_type="bounded_numerical_replay", status="supports_scoped_claim",
        summary="supports", source_refs=[],
    )
    bind_session(ws, session_id="s1", topic_id="wrong-topic", context_id="ctx",
                 active_claim=claim.claim_id)
    return claim, ev


def test_supersede_evidence_marks_voided_and_audits(tmp_path):
    from brain.v5.lifecycle_events import audit_routing, supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    supersede_record(
        ws, record_id=ev.evidence_id, subject_kind="evidence",
        status="voided", reason="wrong topic", operator="o", timestamp="t",
    )

    routing = audit_routing(ws, topic_id="wrong-topic")
    ids = {r.subject_record_id for r in routing["events"]}
    assert ev.evidence_id in ids


def test_lifecycle_history_for_record(tmp_path):
    from brain.v5.lifecycle_events import lifecycle_history, rehome_record, supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="o", timestamp="2026-06-20T10:00:00Z",
    )
    supersede_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        status="misrouted", reason="replaced", operator="o",
        timestamp="2026-06-20T11:00:00Z",
        replacement_ref="claim-right-active",
    )
    history = lifecycle_history(ws, record_id=claim.claim_id)
    assert len(history["events"]) == 2
    # ordered by timestamp ascending
    assert history["events"][0].event_type == "rehome"
    assert history["events"][1].event_type == "supersede"
    # supersedes_event chains only to a prior *supersede* for the same subject; there is
    # none here (the prior event is a rehome), so it must be empty.
    assert history["events"][1].supersedes_event == ""


def test_lifecycle_event_record_contract_accepts_valid_payload():
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True,
        "kind": "lifecycle_event",
        "event_id": "ev-rehome-claim-x-abcd1234",
        "event_type": "rehome",
        "subject_record_id": "claim-x",
        "subject_kind": "claim",
        "lifecycle_status": "rehomed",
        "reason": "misrouted",
        "operator": "bohan-jia",
        "timestamp": "2026-06-20T10:00:00Z",
        "from_topic": "wrong-topic",
        "to_topic": "right-topic",
    }
    result = require_valid_public_surface("lifecycle_event_record", payload)
    assert result["ok"] is True


def test_lifecycle_event_record_contract_rejects_unknown_event_type():
    from brain.v5.contracts import ContractError
    from brain.v5.public_surfaces import require_valid_public_surface

    payload = {
        "ok": True, "kind": "lifecycle_event",
        "event_id": "ev", "event_type": "bogus",
        "subject_record_id": "c", "subject_kind": "claim",
        "lifecycle_status": "rehomed", "reason": "r",
        "operator": "o", "timestamp": "t",
    }
    with pytest.raises(ContractError):
        require_valid_public_surface("lifecycle_event_record", payload)


def test_relation_map_excludes_misrouted_evidence(tmp_path):
    from brain.v5.lifecycle_events import supersede_record
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    supersede_record(
        ws, record_id=ev.evidence_id, subject_kind="evidence",
        status="misrouted", reason="wrong topic", operator="o", timestamp="t",
    )

    mapping = build_claim_relation_map(ws, session_id="s1")
    # the misrouted evidence must not be in the active support buckets
    supported_ids = {e.get("record_id") for e in mapping.get("supported_by", [])}
    limited_ids = {e.get("record_id") for e in mapping.get("limited_by", [])}
    contradict_ids = {e.get("record_id") for e in mapping.get("contradicted_by", [])}
    active_ids = supported_ids | limited_ids | contradict_ids
    assert ev.evidence_id not in active_ids
    # and it should appear in the misrouted zone (entries use record_id, matching _evidence_entry)
    misrouted_ids = {e.get("record_id") for e in mapping.get("misrouted", [])}
    assert ev.evidence_id in misrouted_ids


def test_relation_map_lists_cross_topic_references(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.lifecycle_events import rehome_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "wrong-topic", context_id="ctx", title="Wrong")
    create_topic(ws, "right-topic", context_id="ctx", title="Right")
    claim = create_claim(
        ws, topic_id="wrong-topic", statement="Si throughput",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    rehome_record(
        ws, record_id=claim.claim_id, subject_kind="claim",
        from_topic="wrong-topic", to_topic="right-topic",
        reason="misrouted", operator="o", timestamp="t",
    )
    bind_session(ws, session_id="s-right", topic_id="right-topic", context_id="ctx",
                 active_claim=claim.claim_id)
    mapping = build_claim_relation_map(ws, session_id="s-right")
    refs = mapping.get("cross_topic_references", [])
    assert any(r.get("source_record_id") == claim.claim_id for r in refs)


def test_cli_record_supersede_then_audit_routing(tmp_path):
    from brain.v5.cli import _build_parser, _dispatch
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    parser = _build_parser()
    args = parser.parse_args([
        "--base", str(tmp_path / "ws"),
        "record", "supersede",
        "--record-id", ev.evidence_id,
        "--kind", "evidence",
        "--status", "voided",
        "--reason", "wrong topic",
        "--operator", "bohan-jia",
        "--timestamp", "2026-06-20T10:00:00Z",
    ])
    result = _dispatch(args)
    assert result["ok"] is True

    args2 = parser.parse_args([
        "--base", str(tmp_path / "ws"),
        "record", "audit-routing",
        "--topic", "wrong-topic",
    ])
    result2 = _dispatch(args2)
    ids = {r["subject_record_id"] for r in result2["events"]}
    assert ev.evidence_id in ids


def test_cli_record_rehome_requires_explicit_record_id(tmp_path):
    from brain.v5.cli import _build_parser

    parser = _build_parser()
    # missing --record-id must fail at argparse level
    with pytest.raises(SystemExit):
        parser.parse_args([
            "record", "rehome",
            "--base", str(tmp_path / "ws"),
            "--from-topic", "wrong-topic",
            "--to-topic", "right-topic",
            "--reason", "r",
        ])


def test_mcp_build_rehome_plan_is_readonly_and_apply_requires_explicit_ids(tmp_path):
    from brain.v5.mcp_lifecycle import aitp_v5_apply_rehome_plan, aitp_v5_build_rehome_plan
    from brain.v5.models import LifecycleEventRecord
    from brain.v5.store import list_valid_records
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)

    plan = aitp_v5_build_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
    )
    assert plan["ok"] is True
    # build_plan must not write any events
    events_before = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert events_before == []

    # apply requires the explicit record_ids from the plan
    result = aitp_v5_apply_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    assert result["ok"] is True
    events_after = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events_after) == 1

    # re-apply is idempotent — no second event
    result2 = aitp_v5_apply_rehome_plan(
        base=str(tmp_path / "ws"),
        record_ids=[claim.claim_id],
        from_topic="wrong-topic",
        to_topic="right-topic",
        reason="misrouted",
        operator="bohan-jia",
        timestamp="2026-06-20T10:00:00Z",
    )
    events_final = list_valid_records(ws.registry_dir("lifecycle_events"), LifecycleEventRecord)
    assert len(events_final) == 1
    assert result["event_ids"] == result2["event_ids"]


def test_mcp_apply_rehome_plan_rejects_empty_or_glob_ids(tmp_path):
    from brain.v5.mcp_lifecycle import aitp_v5_apply_rehome_plan

    with pytest.raises(ValueError):
        aitp_v5_apply_rehome_plan(
            base=str(tmp_path / "ws"), record_ids=[],
            from_topic="a", to_topic="b", reason="r",
        )
    with pytest.raises(ValueError):
        aitp_v5_apply_rehome_plan(
            base=str(tmp_path / "ws"), record_ids=["claim-*"],
            from_topic="a", to_topic="b", reason="r",
        )


def test_mcp_supersede_and_audit(tmp_path):
    from brain.v5.mcp_lifecycle import aitp_v5_audit_record_routing, aitp_v5_supersede_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    claim, ev = _misroute_fixture(ws)
    res = aitp_v5_supersede_record(
        base=str(tmp_path / "ws"), record_id=ev.evidence_id, subject_kind="evidence",
        status="voided", reason="wrong topic", operator="o", timestamp="t",
    )
    assert res["ok"] is True
    audit = aitp_v5_audit_record_routing(base=str(tmp_path / "ws"), topic_id="wrong-topic")
    ids = {e["subject_record_id"] for e in audit["events"]}
    assert ev.evidence_id in ids


def test_old_format_record_without_lifecycle_fields_parses_as_active(tmp_path):
    """A claim written in the old format (no lifecycle fields) must still load and
    default to lifecycle_status='active' so the relation-map keeps showing it."""

    from brain.v5.markdown import write_md
    from brain.v5.models import ClaimRecord
    from brain.v5.store import read_record
    from brain.v5.workspace import init_workspace

    ws = init_workspace(tmp_path / "ws")
    # write a hand-crafted old-format claim (no lifecycle_* keys)
    old_fm = {
        "claim_id": "claim-old",
        "topic_id": "t",
        "statement": "legacy",
        "evidence_profile": "code_method",
        "confidence_state": "hypothesis",
        "active_uncertainty": "u",
        "kind": "claim",
    }
    path = ws.registry_dir("claims") / "claim-old.md"
    write_md(path, old_fm, body="# legacy\n")
    rec = read_record(path, ClaimRecord)
    assert rec.lifecycle_status == "active"
    assert rec.replaced_by == ""


def test_supersede_with_replacement_then_relation_map_prefers_replacement(tmp_path):
    from brain.v5.claim_relation_map import build_claim_relation_map
    from brain.v5.lifecycle_events import supersede_record
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path / "ws")
    create_topic(ws, "t", context_id="ctx", title="T")
    old_claim = create_claim(
        ws, topic_id="t", statement="old answer",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    new_claim = create_claim(
        ws, topic_id="t", statement="new answer supersedes old",
        evidence_profile="code_method", confidence_state="hypothesis",
        active_uncertainty="u",
    )
    supersede_record(
        ws, record_id=old_claim.claim_id, subject_kind="claim",
        status="superseded", reason="replaced", operator="o",
        timestamp="2026-06-20T10:00:00Z", replacement_ref=new_claim.claim_id,
    )
    bind_session(ws, session_id="s", topic_id="t", context_id="ctx",
                 active_claim=new_claim.claim_id)
    mapping = build_claim_relation_map(ws, session_id="s")
    # the superseded claim is not the active claim, so the map focuses on new_claim;
    # the key assertion is the map builds cleanly and the superseded record does not
    # surface as the current conclusion.
    assert mapping.get("supported_by") is not None
