from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest


LIFECYCLE_OPERATIONS = {
    "session_start": (
        "aitp_v5_session_start",
        "aitp-v5 session start <session-id>",
        "session_start_boundary",
        "read_only",
    ),
    "recall_audit": (
        "aitp_v5_run_recall_audit",
        "aitp-v5 session recall-audit --request-json <args>",
        "recall_audit_result",
        "kernel_write",
    ),
    "recording_stage": (
        "aitp_v5_stage_recording_candidate",
        "aitp-v5 session recording-stage --candidate-json <args>",
        "recording_candidate_staging",
        "runtime_write",
    ),
    "recording_batch": (
        "aitp_v5_coalesce_recording_batch",
        "aitp-v5 session recording-batch <session-id> <args>",
        "recording_batch_handoff",
        "kernel_write",
    ),
    "session_closeout_plan": (
        "aitp_v5_plan_session_closeout",
        "aitp-v5 session closeout-plan --request-json <args>",
        "session_closeout_plan",
        "read_only",
    ),
    "session_closeout_apply": (
        "aitp_v5_apply_session_closeout",
        "aitp-v5 session closeout-apply --plan-json <args>",
        "session_closeout_apply",
        "kernel_write",
    ),
}


def _seed_workspace(tmp_path: Path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import record_session_focus_set
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="formal-theory", title="Target lifecycle topic")
    claim = create_claim(
        ws,
        topic_id="target",
        statement="The finite diagnostic is controlled in the declared scope.",
        evidence_profile="formal_theory",
        confidence_state="finite_evidence",
        active_uncertainty="No asymptotic proof is claimed.",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="target",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-1",
            session_id="session-1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{claim.claim_id}",
        ),
        actor=_actor(),
    )
    build_query_index(ws)
    return ws, f"claim:{claim.claim_id}"


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="lifecycle-facade-test", host="pytest")


def _actor_mapping():
    return {
        "actor_type": "model",
        "actor_id": "lifecycle-facade-test",
        "host": "pytest",
    }


def _candidate(source_ref: str):
    return {
        "session_id": "session-1",
        "topic_id": "target",
        "candidate_kind": "formula",
        "semantic_key": "finite diagnostic formula",
        "summary": "Preserve the finite diagnostic formula and its boundary.",
        "payload": {"formula": "Z_n", "boundary": "finite n"},
        "source_refs": [source_ref],
        "source_event_refs": ["event:derivation-complete"],
        "missing_prerequisites": ["asymptotic proof"],
        "expires_at": "2099-07-21T00:00:00+00:00",
    }


def _recall_request(source_ref: str):
    return {
        "session_id": "session-1",
        "query_text": "recover the finite diagnostic and its exact source",
        "normalized_intent": "recover_prior_result",
        "required_families": ["claims"],
        "exact_refs": [source_ref],
        "include_program_scope": True,
        "include_discovery": False,
        "top_k": 10,
    }


def _closeout_request(source_ref: str, batch_ref: str = ""):
    pending = [batch_ref] if batch_ref else []
    return {
        "session_id": "session-1",
        "milestone_id": "milestone-1",
        "completed_work": ["Completed the finite diagnostic derivation."],
        "can_say": [
            {
                "text": "The finite diagnostic is controlled in the declared scope.",
                "boundary_class": "finite_evidence",
                "source_refs": [source_ref],
            }
        ],
        "cannot_say": [
            {
                "text": "No asymptotic proof has been established.",
                "boundary_class": "open_gap",
                "source_refs": [source_ref],
            }
        ],
        "open_gaps": [],
        "failed_routes": [],
        "next_actions": ["Derive a uniform asymptotic bound."],
        "source_record_refs": [source_ref],
        "pending_candidate_batch_refs": pending,
        "reusable_workflow_candidate_refs": [],
    }


def _tree_state(root: Path):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_lifecycle_operations_have_exact_cross_surface_declarations():
    from brain.v5 import mcp_tools
    from brain.v5.capability_registry import (
        audit_capability_registry,
        capability_specs,
        compact_mcp_tools,
    )
    from brain.v5.capability_registry_data import (
        CODEX_FACADE_MCP_NAMES,
        CODEX_SUPPORT_MCP_NAMES,
    )
    from brain.v5.public_surfaces import public_surface_names
    from brain.v5.runtime_entrypoints import (
        runtime_entrypoints,
        validate_runtime_entrypoints,
    )

    specs = capability_specs()
    entrypoints = runtime_entrypoints()
    public = set(public_surface_names())

    for operation, expected in LIFECYCLE_OPERATIONS.items():
        mcp_name, cli_route, surface, state_effect = expected
        spec = specs[operation]
        assert (spec.mcp_name, spec.cli_route, spec.public_surface, spec.state_effect) == expected
        assert spec.compact_visibility == "full"
        assert entrypoints[operation] == {
            "mcp": mcp_name,
            "cli": cli_route,
            "surface": surface,
        }
        assert callable(getattr(mcp_tools, mcp_name))
        assert surface in public

    expected_compact = set(CODEX_FACADE_MCP_NAMES + CODEX_SUPPORT_MCP_NAMES)
    assert set(compact_mcp_tools()) == expected_compact
    assert not {value[0] for value in LIFECYCLE_OPERATIONS.values()} & expected_compact
    assert validate_runtime_entrypoints() == []
    assert audit_capability_registry()["issues"] == []


def test_read_only_start_and_closeout_plan_never_initialize_or_write_workspace(tmp_path):
    from brain.v5.lifecycle_facade import LifecycleFacadeError
    from brain.v5.mcp_tools import (
        aitp_v5_plan_session_closeout,
        aitp_v5_session_start,
    )

    missing = tmp_path / "missing"
    with pytest.raises(LifecycleFacadeError, match="workspace"):
        aitp_v5_session_start(str(missing), session_id="session-1")
    with pytest.raises(LifecycleFacadeError, match="workspace"):
        aitp_v5_plan_session_closeout(
            str(missing), request=_closeout_request("claim:missing")
        )
    assert not (missing / ".aitp").exists()

    ws, source_ref = _seed_workspace(tmp_path / "seeded")
    before = _tree_state(ws.root)
    start = aitp_v5_session_start(str(ws.base), session_id="session-1")
    plan = aitp_v5_plan_session_closeout(
        str(ws.base), request=_closeout_request(source_ref)
    )
    after = _tree_state(ws.root)

    assert start["disclosure_level"] == "startup_orientation"
    assert start["write_executed"] is False
    assert plan["kind"] == "session_closeout_plan"
    assert plan["write_executed"] is False
    assert before == after


def test_explicit_workspace_never_falls_back_to_environment_store(tmp_path, monkeypatch):
    from brain.v5.lifecycle_facade import LifecycleFacadeError
    from brain.v5.mcp_tools import aitp_v5_session_start

    ws, _source_ref = _seed_workspace(tmp_path / "environment-store")
    unrelated = tmp_path / "existing-empty-directory"
    unrelated.mkdir()
    monkeypatch.setenv("AITP_TOPICS_ROOT", str(ws.base))

    with pytest.raises(LifecycleFacadeError, match="workspace"):
        aitp_v5_session_start(str(unrelated), session_id="session-1")

    assert not (unrelated / ".aitp").exists()


def test_full_lifecycle_wrappers_form_one_trust_neutral_session_flow(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_apply_session_closeout,
        aitp_v5_coalesce_recording_batch,
        aitp_v5_plan_session_closeout,
        aitp_v5_run_recall_audit,
        aitp_v5_session_start,
        aitp_v5_stage_recording_candidate,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.session_resume import build_session_resume_card

    ws, source_ref = _seed_workspace(tmp_path)
    start = aitp_v5_session_start(str(ws.base), session_id="session-1")
    recall = aitp_v5_run_recall_audit(
        str(ws.base), request=_recall_request(source_ref), actor=_actor_mapping()
    )
    staged = aitp_v5_stage_recording_candidate(
        str(ws.base), candidate=_candidate(source_ref)
    )
    batch = aitp_v5_coalesce_recording_batch(
        str(ws.base),
        session_id="session-1",
        milestone_id="milestone-1",
        actor=_actor_mapping(),
    )
    planned = aitp_v5_plan_session_closeout(
        str(ws.base), request=_closeout_request(source_ref, batch["batch_ref"])
    )

    assert start["resume_card"] == build_session_resume_card(ws, "session-1")
    assert start["context_receipt"]["transition"] == "route_hint->startup_orientation"
    assert recall["audit_ref"].startswith("recall_audit:")
    assert recall["can_update_claim_trust"] is False
    assert staged["status"] == "staged"
    assert staged["state_effect"] == "runtime_write"
    assert batch["review_status"] == "pending_review"
    assert batch["human_review_required"] is True
    assert planned["allowed"] is True
    assert planned["plan_id"]
    assert planned["plan_fingerprint"]

    with pytest.raises(Exception, match="plan_id"):
        aitp_v5_apply_session_closeout(
            str(ws.base),
            plan=planned,
            plan_id="wrong-plan-id",
            actor=_actor_mapping(),
        )

    tampered = deepcopy(planned)
    tampered["record"]["completed_work"] = ["Substitute an unreviewed conclusion."]
    with pytest.raises(Exception, match="fingerprint"):
        aitp_v5_apply_session_closeout(
            str(ws.base),
            plan=tampered,
            plan_id=planned["plan_id"],
            actor=_actor_mapping(),
        )

    applied = aitp_v5_apply_session_closeout(
        str(ws.base),
        plan=planned,
        plan_id=planned["plan_id"],
        actor=_actor_mapping(),
    )
    stored = RecordRepository(ws, actor=_actor()).read(applied["closeout_ref"])

    assert applied["write_status"] == "created"
    assert stored.status == "found"
    assert stored.record.can_update_claim_trust is False


def test_session_cli_uses_file_backed_nested_payloads(tmp_path, capsys):
    from brain.v5 import cli

    ws, source_ref = _seed_workspace(tmp_path)
    candidate_path = tmp_path / "candidate.json"
    recall_path = tmp_path / "recall-request.json"
    request_path = tmp_path / "closeout-request.json"
    plan_path = tmp_path / "closeout-plan.json"
    candidate_path.write_text(json.dumps(_candidate(source_ref)), encoding="utf-8")
    recall_path.write_text(json.dumps(_recall_request(source_ref)), encoding="utf-8")
    request_path.write_text(
        json.dumps(_closeout_request(source_ref)), encoding="utf-8"
    )

    assert cli.main(["--base", str(ws.base), "session", "start", "session-1"]) == 0
    started = json.loads(capsys.readouterr().out)
    assert started["kind"] == "session_start_boundary"

    assert cli.main(
        [
            "--base",
            str(ws.base),
            "session",
            "recall-audit",
            "--request-json",
            str(recall_path),
        ]
    ) == 0
    recalled = json.loads(capsys.readouterr().out)
    assert recalled["audit_ref"].startswith("recall_audit:")

    assert cli.main(
        [
            "--base",
            str(ws.base),
            "session",
            "recording-stage",
            "--candidate-json",
            str(candidate_path),
        ]
    ) == 0
    staged = json.loads(capsys.readouterr().out)
    assert staged["status"] == "staged"

    assert cli.main(
        [
            "--base",
            str(ws.base),
            "session",
            "recording-batch",
            "session-1",
            "milestone-1",
        ]
    ) == 0
    batch = json.loads(capsys.readouterr().out)
    assert batch["batch_ref"].startswith("recording_candidate_batch:")
    request_path.write_text(
        json.dumps(_closeout_request(source_ref, batch["batch_ref"])),
        encoding="utf-8",
    )

    assert cli.main(
        [
            "--base",
            str(ws.base),
            "session",
            "closeout-plan",
            "--request-json",
            str(request_path),
        ]
    ) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["kind"] == "session_closeout_plan"
    plan_path.write_text(json.dumps(planned), encoding="utf-8")

    assert cli.main(
        [
            "--base",
            str(ws.base),
            "session",
            "closeout-apply",
            "--plan-json",
            str(plan_path),
            "--plan-id",
            planned["plan_id"],
        ]
    ) == 0
    applied = json.loads(capsys.readouterr().out)
    assert applied["write_status"] == "created"

    parser = cli._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--base",
                str(ws.base),
                "session",
                "recording-stage",
                "--candidate-json-inline",
                json.dumps(_candidate(source_ref)),
            ]
        )


def test_compact_facade_routes_disclosure_staging_batch_and_explicit_closeout(tmp_path):
    from brain.v5.mcp_tools import (
        aitp_v5_codex_autoroute,
        aitp_v5_codex_closeout,
        aitp_v5_codex_enter,
        aitp_v5_codex_expand,
        aitp_v5_codex_record_apply,
        aitp_v5_codex_recording_step,
        aitp_v5_session_start,
    )

    ws, source_ref = _seed_workspace(tmp_path)
    direct_start = aitp_v5_session_start(str(ws.base), session_id="session-1")
    route = aitp_v5_codex_autoroute(
        str(ws.base),
        session_id="session-1",
        request_summary="Continue the existing finite diagnostic research.",
    )
    entered = aitp_v5_codex_enter(
        str(ws.base),
        session_id="session-1",
        request_summary="Continue the finite diagnostic.",
    )
    expanded = aitp_v5_codex_expand(
        str(ws.base), session_id="session-1", expansion="context_pack"
    )
    exact = aitp_v5_codex_expand(
        str(ws.base),
        session_id="session-1",
        expansion="record_refs",
        record_refs=[source_ref],
    )

    assert route["disclosure_level"] == "route_hint"
    assert "resume_card" not in route
    assert entered["session_start"] == direct_start
    assert entered["disclosure_level"] == "startup_orientation"
    assert expanded["disclosure_level"] == "normal_research"
    assert exact["disclosure_level"] == "exact_expansion"

    recording = aitp_v5_codex_recording_step(
        str(ws.base),
        session_id="session-1",
        event_type="source_touched",
        summary="The exact finite diagnostic formula was located.",
        claim_id=source_ref.partition(":")[2],
        candidate=_candidate(source_ref),
    )
    assert recording["recording_candidate_staging"]["status"] == "staged"
    assert recording["runtime_write_executed"] is True

    batch = aitp_v5_codex_record_apply(
        str(ws.base),
        session_id="session-1",
        slot="recording_batch",
        payload={"milestone_id": "milestone-1", "actor": _actor_mapping()},
    )
    assert batch["batch_ref"].startswith("recording_candidate_batch:")

    request = _closeout_request(source_ref, batch["batch_ref"])
    planned = aitp_v5_codex_closeout(
        str(ws.base),
        session_id="session-1",
        summary="Plan the canonical session closeout.",
        lifecycle_request=request,
        apply=True,
    )
    assert planned["mode"] == "lifecycle_plan"
    assert planned["write_executed"] is False
    closeout_plan = planned["session_closeout_plan"]

    applied = aitp_v5_codex_closeout(
        str(ws.base),
        session_id="session-1",
        summary="Apply the reviewed canonical session closeout.",
        lifecycle_plan=closeout_plan,
        lifecycle_plan_id=closeout_plan["plan_id"],
    )
    assert applied["mode"] == "lifecycle_apply"
    assert applied["write_executed"] is True
    assert applied["session_closeout_apply"]["closeout_ref"].startswith(
        "session_closeout:"
    )
