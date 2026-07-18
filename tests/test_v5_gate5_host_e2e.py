from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

import pytest


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "librpa-gw", context_id="gw", title="LibRPA GW")
    claim = create_claim(
        ws,
        topic_id="librpa-gw",
        statement="The diagnostic tool run preserves the finite benchmark boundary.",
        evidence_profile="code_method",
        confidence_state="hypothesis",
        active_uncertainty="the tool result is process-only",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="librpa-gw",
        context_id="gw",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    return ws, claim


def _host_event():
    from brain.v5.host_lifecycle_facade import normalize_host_lifecycle_event

    return normalize_host_lifecycle_event(
        "codex",
        "PostToolUse",
        {
            "event_id": "native-post-tool-1",
            "host_session_id": "codex-session-1",
            "tool_name": "pytest",
            "status": "completed",
        },
        session_id="session-1",
    )


def _research_event(claim_id: str):
    from brain.v5.research_moment_contracts import ResearchEvent

    return ResearchEvent(
        event_id="moment-event-1",
        event_type="RouteChanged",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        host="codex",
        host_session_id="codex-session-1",
        session_id="session-1",
        topic_id="librpa-gw",
        subject_refs=(f"claim:{claim_id}",),
        objective_payload={},
        semantic_payload={
            "candidate_kind": "open_direction",
            "semantic_key": "finite benchmark follow-up",
            "summary": "Review the finite benchmark follow-up.",
            "payload": {"status": "open"},
        },
        source_event_id="native-post-tool-1",
        recursion_origin="host_native",
    )


def test_post_tool_without_explicit_research_event_remains_trace_only(tmp_path):
    from brain.v5.host_lifecycle_facade import dispatch_host_lifecycle_event
    from brain.v5.query_index import current_canonical_watermark

    ws, _claim = _seed_workspace(tmp_path)
    before = current_canonical_watermark(ws)
    result = dispatch_host_lifecycle_event(ws, _host_event())

    assert result.status == "trace_only"
    assert result.operation == "delegate_existing_post_tool_trace"
    assert result.canonical_write is False
    assert current_canonical_watermark(ws) == before


def test_explicit_host_research_event_crosses_only_the_moment_policy_boundary(tmp_path):
    from brain.v5.host_lifecycle_facade import dispatch_host_lifecycle_event
    from brain.v5.record_envelope import RecordActor

    ws, claim = _seed_workspace(tmp_path)
    result = dispatch_host_lifecycle_event(
        ws,
        _host_event(),
        research_event=_research_event(claim.claim_id),
        actor=RecordActor(actor_type="tool", actor_id="host-moment-test", host="codex"),
    )

    assert result.operation == "dispatch_validated_research_moment"
    assert result.status == "moment_staged"
    assert result.receipt_status == "staged"
    assert result.receipt_id.startswith("moment-receipt:")
    assert result.runtime_write is True
    assert result.canonical_write is False


def test_explicit_objective_host_event_reports_its_exact_canonical_process_write(
    tmp_path
):
    from brain.v5.host_lifecycle_facade import dispatch_host_lifecycle_event
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.record_envelope import RecordActor
    from brain.v5.research_moment_contracts import ResearchEvent

    ws, claim = _seed_workspace(tmp_path)
    artifact = tmp_path / "diagnostic.json"
    artifact.write_text('{"finite": true}\n', encoding="utf-8")
    event = ResearchEvent(
        event_id="artifact-moment-1",
        event_type="ArtifactProduced",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        host="codex",
        host_session_id="codex-session-1",
        session_id="session-1",
        topic_id="librpa-gw",
        subject_refs=(f"claim:{claim.claim_id}",),
        objective_payload={
            "capture_operation": "attach_artifact_auto",
            "content_changed": True,
            "arguments": {
                "path": str(artifact),
                "claim_id": claim.claim_id,
                "artifact_type": "diagnostic_json",
                "summary": "Finite diagnostic artifact.",
            },
        },
        semantic_payload={},
        source_event_id="native-post-tool-1",
        recursion_origin="host_native",
    )
    before = current_canonical_watermark(ws)
    result = dispatch_host_lifecycle_event(
        ws,
        _host_event(),
        research_event=event,
        actor=RecordActor(
            actor_type="tool", actor_id="host-objective-test", host="codex"
        ),
    )

    assert result.status == "moment_captured"
    assert result.receipt_status == "captured"
    assert result.canonical_write is True
    assert current_canonical_watermark(ws) != before


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    (
        ("host", "claude_code", "host does not match"),
        ("host_session_id", "other-host-session", "host session does not match"),
        ("session_id", "other-session", "session does not match"),
        ("topic_id", "other-topic", "topic does not match"),
        ("source_event_id", "other-native-event", "source event does not match"),
    ),
)
def test_host_moment_bridge_rejects_identity_drift(
    tmp_path, field, replacement, message
):
    from brain.v5.host_lifecycle_facade import dispatch_host_lifecycle_event
    from brain.v5.record_envelope import RecordActor

    ws, claim = _seed_workspace(tmp_path)
    event = replace(_research_event(claim.claim_id), **{field: replacement})

    with pytest.raises(ValueError, match=message):
        dispatch_host_lifecycle_event(
            ws,
            _host_event(),
            research_event=event,
            actor=RecordActor(
                actor_type="tool", actor_id="host-moment-test", host="codex"
            ),
        )


@pytest.mark.parametrize(
    ("host", "script_name", "runner_args", "result_path"),
    (
        (
            "codex",
            "aitp_v5_adapter_event_runner.py",
            ("post-tool", "--runtime", "codex"),
            ("research_moment",),
        ),
        (
            "opencode",
            "aitp_v5_adapter_event_runner.py",
            ("post-tool", "--runtime", "opencode"),
            ("research_moment",),
        ),
        (
            "claude_code",
            "aitp_v5_claude_hook.py",
            ("post-tool",),
            ("aitp", "research_moment"),
        ),
        (
            "kimi_code",
            "aitp_v5_kimi_hook.py",
            ("post-tool",),
            ("aitp", "research_moment"),
        ),
    ),
)
def test_real_host_post_tool_commands_accept_only_an_explicit_research_envelope(
    tmp_path, host, script_name, runner_args, result_path
):
    ws, claim = _seed_workspace(tmp_path)
    event = replace(
        _research_event(claim.claim_id),
        event_id=f"moment-event-{host}",
        host=host,
        host_session_id=f"{host}-session-1",
        source_event_id=f"native-post-tool-{host}",
    )
    script = Path(__file__).resolve().parents[1] / "hooks" / script_name
    command = [
        sys.executable,
        str(script),
        *runner_args,
        "--base",
        str(tmp_path),
        "--session-id",
        "session-1",
    ]
    result = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[1],
        input=json.dumps(
            {
                "tool_name": "pytest",
                "status": "completed",
                "aitp_research_event": asdict(event),
            }
        ),
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    moment = payload
    for key in result_path:
        moment = moment[key]
    assert moment["operation"] == "dispatch_validated_research_moment"
    assert moment["status"] == "moment_staged"
    assert moment["receipt_status"] == "staged"
    assert moment["canonical_write"] is False
    assert len(list((ws.root / "runtime" / "recording_staging" / "session-1").glob("*.json"))) == 1


def test_nested_tool_output_cannot_smuggle_a_research_event_into_the_hook_bridge(
    tmp_path
):
    from brain.v5.hook_research_moment_bridge import process_explicit_hook_research_moment
    from brain.v5.query_index import current_canonical_watermark

    ws, claim = _seed_workspace(tmp_path)
    before = current_canonical_watermark(ws)
    payload = {
        "tool_response": {
            "aitp_research_event": asdict(_research_event(claim.claim_id))
        }
    }

    assert (
        process_explicit_hook_research_moment(
            ws,
            payload,
            host="codex",
            session_id="session-1",
        )
        is None
    )
    assert current_canonical_watermark(ws) == before


def test_malformed_explicit_hook_envelope_returns_bounded_diagnostic_without_write(
    tmp_path
):
    from brain.v5.hook_research_moment_bridge import process_explicit_hook_research_moment
    from brain.v5.query_index import current_canonical_watermark

    ws, _claim = _seed_workspace(tmp_path)
    before = current_canonical_watermark(ws)
    diagnostic = process_explicit_hook_research_moment(
        ws,
        {"aitp_research_event": {"event_id": "incomplete"}},
        host="codex",
        session_id="session-1",
    )

    assert diagnostic == {
        "kind": "research_moment_hook_diagnostic",
        "status": "rejected",
        "reason_code": "invalid_explicit_research_event",
        "error_type": "ValueError",
        "orientation_only": True,
        "can_update_kernel_state": False,
        "can_update_claim_trust": False,
    }
    assert current_canonical_watermark(ws) == before
    assert not (ws.root / "runtime" / "research_moments").exists()


def test_normal_session_vertical_recalls_stages_reviews_and_resumes(tmp_path):
    from brain.v5.host_lifecycle_facade import (
        closeout_session,
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )
    from brain.v5.record_envelope import RecordActor
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_moment_facade import process_research_moment_request
    from brain.v5.workspace import bind_session

    ws, claim = _seed_workspace(tmp_path)
    actor = RecordActor(actor_type="model", actor_id="normal-session", host="pytest")
    start = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "start-session-1",
            "host_session_id": "codex-session-1",
            "research_relevant": True,
            "objective_text": "Resume the exact finite benchmark boundary.",
        },
        session_id="session-1",
    )
    start_result = dispatch_host_lifecycle_event(ws, start)
    staged = dispatch_host_lifecycle_event(
        ws,
        _host_event(),
        research_event=_research_event(claim.claim_id),
        actor=actor,
    )
    closeout_request = {
        "apply": True,
        "event": {
            "event_id": "closeout-moment-1",
            "event_type": "SessionCloseout",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "host": "codex",
            "host_session_id": "codex-session-1",
            "session_id": "session-1",
            "topic_id": "librpa-gw",
            "subject_refs": [f"claim:{claim.claim_id}"],
            "objective_payload": {"milestone_id": "finite-benchmark-review"},
            "semantic_payload": {},
            "source_event_id": "explicit-closeout-1",
            "recursion_origin": "host_native",
        },
    }
    reviewed = process_research_moment_request(ws, closeout_request, actor=actor)
    closeout = normalize_host_lifecycle_event(
        "codex",
        "plan_session_closeout",
        {
            "event_id": "host-closeout-1",
            "host_session_id": "codex-session-1",
        },
        session_id="session-1",
    )
    closeout_result = closeout_session(ws, closeout)

    bind_session(
        ws,
        "session-2",
        topic_id="librpa-gw",
        context_id="gw",
        runtime="codex",
        active_claim=claim.claim_id,
    )
    resume = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "start-session-2",
            "host_session_id": "codex-session-2",
            "research_relevant": True,
            "objective_text": "Continue from the reviewed finite benchmark state.",
        },
        session_id="session-2",
    )
    resume_result = dispatch_host_lifecycle_event(ws, resume)

    assert start_result.status == "context_prepared"
    assert staged.status == "moment_staged"
    assert reviewed["receipt"]["status"] == "review_batch_ready"
    batch_refs = reviewed["receipt"]["record_refs"]
    assert len(batch_refs) == 1
    batch = RecordRepository(ws, actor=actor).read(batch_refs[0]).record
    assert batch.status == "pending_review"
    assert len(batch.candidates) == 1
    assert closeout_result.status == "plan_only"
    assert closeout_result.canonical_write is False
    assert resume_result.status == "context_prepared"
    assert resume_result.receipt_id != start_result.receipt_id


def test_research_friction_becomes_only_one_reviewable_generic_dossier(tmp_path):
    from brain.v5.harness_feedback_case_contracts import HarnessFeedbackCaseRequest
    from brain.v5.harness_feedback_cases import (
        build_harness_feedback_review_view,
        harness_feedback_case_write_payload,
        record_harness_feedback_case,
    )
    from brain.v5.record_envelope import RecordActor

    ws, claim = _seed_workspace(tmp_path)
    actor = RecordActor(actor_type="model", actor_id="friction-test", host="codex")
    result = record_harness_feedback_case(
        ws,
        HarnessFeedbackCaseRequest(
            topic_id="librpa-gw",
            problem_type="bounded_context_omission",
            friction="The resumed session omitted one exact process reference.",
            expected_behavior="Bounded recall should expose the pinned process reference.",
            actual_behavior="The compact entry required an extra manual lookup.",
            impact="The agent could repeat an already completed diagnostic run.",
            reproduction_steps=(
                "Bind a new session to the existing topic.",
                "Request bounded startup context.",
                "Inspect the exact process references.",
            ),
            host_id="codex",
            runtime_context={"event": "session_start", "surface": "compact"},
            source_refs=(
                "session:session-1",
                f"claim:{claim.claim_id}",
            ),
            proposed_direction="Review the bounded recall selection policy.",
            affected_capability="context_injection",
            affected_record_family="sessions",
        ),
        actor=actor,
    )
    payload = harness_feedback_case_write_payload(result)
    view = build_harness_feedback_review_view(ws)

    assert payload["status"] == "created"
    assert payload["requires_human_review"] is True
    assert payload["can_modify_harness"] is False
    assert payload["produces_harness_optimization_plan"] is False
    assert payload["can_emit_skill_artifacts"] is False
    assert payload["can_install_skill"] is False
    assert payload["can_update_claim_trust"] is False
    assert view["checked_count"] == 1
    assert view["groups"] == []
    assert view["errors"] == []
