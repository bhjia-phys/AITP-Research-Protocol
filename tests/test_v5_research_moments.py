from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, replace

import pytest


EVENT_TYPES = (
    "ResearchTurnStart",
    "SourceAcquired",
    "CodeStateChanged",
    "ToolRunCompleted",
    "ArtifactProduced",
    "FailureOrGapObserved",
    "RouteChanged",
    "MajorConclusionPending",
    "ExpensiveRunPending",
    "SessionCloseout",
)


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="tool", actor_id="moment-test", host="pytest")


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="formal-theory", title="Target topic")
    claim = create_claim(
        ws,
        topic_id="target",
        statement="The finite field-theory calculation is controlled in the stated scope.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="The asymptotic regime remains open.",
    )
    bind_session(
        ws,
        "session-1",
        topic_id="target",
        context_id="formal-theory",
        active_claim=claim.claim_id,
    )
    return ws, claim, f"claim:{claim.claim_id}"


def _event(event_type, *, subject_refs=(), objective=None, semantic=None, **overrides):
    from brain.v5.research_moment_contracts import ResearchEvent

    values = {
        "event_id": f"event-{event_type.casefold()}",
        "event_type": event_type,
        "occurred_at": "2099-07-16T12:00:00+00:00",
        "host": "codex",
        "host_session_id": "host-session-1",
        "session_id": "session-1",
        "topic_id": "target",
        "subject_refs": tuple(subject_refs),
        "objective_payload": dict(objective or {}),
        "semantic_payload": dict(semantic or {}),
        "source_event_id": "native-event-1",
        "recursion_origin": "host",
    }
    values.update(overrides)
    return ResearchEvent(**values)


@pytest.mark.parametrize("event_type", EVENT_TYPES)
def test_research_event_contract_accepts_only_the_ten_logical_events(event_type):
    from brain.v5.research_moment_contracts import (
        ALLOWED_RESEARCH_EVENT_TYPES,
        RESEARCH_MOMENT_OUTCOMES,
        normalize_research_event,
    )

    event = normalize_research_event(_event(event_type))

    assert event.event_type == event_type
    assert event.occurred_at.endswith("+00:00")
    assert ALLOWED_RESEARCH_EVENT_TYPES == frozenset(EVENT_TYPES)
    assert RESEARCH_MOMENT_OUTCOMES == frozenset(
        {
            "ignore",
            "auto_capture_process",
            "stage_semantic_candidate",
            "coalesce_for_review",
            "require_checkpoint",
            "block_until_prerequisites",
        }
    )


def test_event_contract_rejects_unknown_events_untyped_refs_and_nonfinite_payloads():
    from brain.v5.research_moment_contracts import normalize_research_event

    with pytest.raises(ValueError, match="unsupported research event"):
        normalize_research_event(_event("ChatMessage"))
    with pytest.raises(ValueError, match="typed ref"):
        normalize_research_event(_event("ArtifactProduced", subject_refs=("not-a-ref",)))
    with pytest.raises(ValueError, match="finite JSON"):
        normalize_research_event(
            _event("ToolRunCompleted", objective={"duration": float("nan")})
        )
    with pytest.raises(ValueError, match="safe path component"):
        normalize_research_event(_event("ResearchTurnStart", session_id="../escape"))


def test_controller_ignores_recursive_output_and_unchanged_status_noise(tmp_path):
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    recursive = decide_research_moment(
        ws,
        _event(
            "FailureOrGapObserved",
            subject_refs=(claim_ref,),
            semantic={
                "candidate_kind": "failed_route",
                "semantic_key": "recursive output",
                "summary": "AITP repeated its own diagnostic.",
                "payload": {"boundary": "diagnostic only"},
            },
            recursion_origin="aitp_diagnostic",
        ),
    )
    unchanged = decide_research_moment(
        ws,
        _event(
            "ToolRunCompleted",
            subject_refs=(claim_ref,),
            objective={
                "capture_operation": "capture_tool_run_auto",
                "content_changed": False,
                "poll_kind": "status_poll",
            },
        ),
    )

    assert recursive.outcome == "ignore"
    assert "recursive_aitp_output" in recursive.reason_codes
    assert unchanged.outcome == "ignore"
    assert "unchanged_status_poll" in unchanged.reason_codes
    receipt = apply_research_moment_decision(ws, recursive, actor=_actor())
    replay = apply_research_moment_decision(ws, recursive, actor=_actor())
    assert receipt == replay
    assert receipt.status == "ignored"
    assert receipt.can_update_claim_trust is False
    assert receipt.runtime_path.endswith(".json")


def test_code_state_event_auto_captures_exact_process_record_idempotently(tmp_path):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    repo = tmp_path / "code-under-study"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "aitp-test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "AITP Test"], cwd=repo, check=True)
    (repo / "model.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "model.py"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=repo, check=True, capture_output=True)
    event = _event(
        "CodeStateChanged",
        subject_refs=(claim_ref,),
        objective={
            "capture_operation": "capture_code_state_auto",
            "content_changed": True,
            "arguments": {
                "worktree_path": str(repo),
                "repo_id": "code-under-study",
                "topic_id": "target",
                "claim_id": claim_ref.split(":", 1)[1],
                "session_id": "session-1",
                "write_patch_artifact": False,
            },
        },
    )

    decision = decide_research_moment(ws, event)
    first = apply_research_moment_decision(ws, decision, actor=_actor())
    second = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "auto_capture_process"
    assert decision.application_operation == "capture_code_state_auto"
    assert decision.declared_effect == "kernel_write"
    assert first == second
    assert len(first.record_refs) == 1
    assert first.record_refs[0].startswith("code_state:")
    stored = RecordRepository(ws, actor=_actor()).read(first.record_refs[0])
    assert stored.status == "found"
    assert stored.record.upstream_commit
    assert stored.record.linked_records["session_id"] == "session-1"


def test_source_tool_run_and_artifact_events_use_only_their_exact_writers(tmp_path):
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment
    from brain.v5.tools import register_tool_recipe

    ws, claim, claim_ref = _seed_workspace(tmp_path)
    source_path = tmp_path / "source-note.txt"
    source_path.write_text("Pinned source material.\n", encoding="utf-8")
    run_path = tmp_path / "run.log"
    run_path.write_text("diagnostic run completed\n", encoding="utf-8")
    artifact_path = tmp_path / "result.json"
    artifact_path.write_text('{"finite": true}\n', encoding="utf-8")
    register_tool_recipe(
        ws,
        recipe_id="diagnostic-recipe",
        tool_family="pytest",
        tool_name="fixture-runner",
        purpose="Exercise exact moment capture.",
    )
    cases = (
        (
            "SourceAcquired",
            "capture_source_asset_auto",
            "source_asset:",
            {
                "path": str(source_path),
                "claim_id": claim.claim_id,
                "asset_type": "note",
                "title": "Pinned source note",
                "copy_to_store": False,
            },
        ),
        (
            "ToolRunCompleted",
            "capture_tool_run_auto",
            "tool_run:",
            {
                "path": str(run_path),
                "recipe_id": "diagnostic-recipe",
                "tool_family": "pytest",
                "tool_name": "fixture-runner",
                "claim_id": claim.claim_id,
                "inputs": {"case": "finite"},
            },
        ),
        (
            "ArtifactProduced",
            "attach_artifact_auto",
            "artifact:",
            {
                "path": str(artifact_path),
                "claim_id": claim.claim_id,
                "artifact_type": "result_json",
                "summary": "Finite diagnostic output.",
            },
        ),
    )

    for index, (event_type, operation, ref_prefix, arguments) in enumerate(cases):
        event = _event(
            event_type,
            subject_refs=(claim_ref,),
            objective={
                "capture_operation": operation,
                "content_changed": True,
                "arguments": arguments,
            },
            event_id=f"event-objective-{index}",
            source_event_id=f"native-objective-{index}",
        )
        decision = decide_research_moment(ws, event)
        receipt = apply_research_moment_decision(ws, decision, actor=_actor())

        assert decision.outcome == "auto_capture_process"
        assert decision.application_operation == operation
        assert receipt.status == "captured"
        assert len(receipt.record_refs) == 1
        assert receipt.record_refs[0].startswith(ref_prefix)


def test_existing_route_record_is_verified_without_duplicate_canonical_write(tmp_path):
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    event = _event(
        "RouteChanged",
        subject_refs=(claim_ref,),
        objective={"capture_operation": "verify_existing"},
    )
    before = current_canonical_watermark(ws)

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "auto_capture_process"
    assert decision.application_operation == "exact_record_expansion"
    assert receipt.status == "verified"
    assert receipt.record_refs == (claim_ref,)
    assert current_canonical_watermark(ws) == before


@pytest.mark.parametrize(
    ("event_type", "operation", "arguments"),
    (
        (
            "SourceAcquired",
            "capture_source_asset_auto",
            {"path": "source.txt", "force_refresh": True},
        ),
        (
            "ToolRunCompleted",
            "capture_tool_run_auto",
            {
                "path": "run.log",
                "recipe_id": "recipe",
                "tool_family": "hpc",
                "tool_name": "runner",
                "claim_id": "claim",
                "lane": "final",
            },
        ),
    ),
)
def test_unsafe_automatic_capture_arguments_return_one_blocking_decision(
    tmp_path,
    event_type,
    operation,
    arguments,
):
    from brain.v5.research_moments import decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    decision = decide_research_moment(
        ws,
        _event(
            event_type,
            subject_refs=(claim_ref,),
            objective={
                "capture_operation": operation,
                "content_changed": True,
                "arguments": arguments,
            },
        ),
    )

    assert decision.outcome == "block_until_prerequisites"
    assert decision.reason_codes == ("invalid_capture_arguments",)
    assert decision.blocked_action == operation
    assert decision.can_update_claim_trust is False


def test_mixed_objective_and_semantic_event_is_split_before_any_write(tmp_path):
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    event = _event(
        "RouteChanged",
        subject_refs=(claim_ref,),
        objective={"capture_operation": "verify_existing"},
        semantic={
            "candidate_kind": "interpretation",
            "semantic_key": "mixed event",
            "summary": "This semantic content must be emitted separately.",
            "payload": {"scope": "finite"},
        },
    )
    before = current_canonical_watermark(ws)

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "block_until_prerequisites"
    assert decision.reason_codes == ("mixed_objective_and_semantic_event",)
    assert receipt.status == "blocked"
    assert current_canonical_watermark(ws) == before


def test_semantic_signal_is_staged_once_without_scientific_promotion(tmp_path):
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    before = current_canonical_watermark(ws)
    event = _event(
        "RouteChanged",
        subject_refs=(claim_ref,),
        semantic={
            "candidate_kind": "formula",
            "semantic_key": "finite replica identity",
            "summary": "Record the finite replica identity with its boundary.",
            "payload": {"equation": "Z_n", "boundary": "finite n only"},
            "missing_prerequisites": ["analytic continuation"],
            "expires_at": "2099-08-01T00:00:00+00:00",
        },
    )

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=_actor())
    replay = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "stage_semantic_candidate"
    assert decision.declared_effect == "runtime_write"
    assert receipt == replay
    assert len(receipt.staging_refs) == 1
    assert current_canonical_watermark(ws) == before
    staging_payload = json.loads(
        next((ws.root / "runtime" / "recording_staging" / "session-1").glob("*.json")).read_text(
            encoding="utf-8"
        )
    )
    assert staging_payload["candidate"]["trust_effect"] == "none"
    assert staging_payload["candidate"]["can_update_claim_trust"] is False


def test_closeout_coalesces_staged_semantics_into_one_review_batch(tmp_path):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    semantic = _event(
        "RouteChanged",
        subject_refs=(claim_ref,),
        semantic={
            "candidate_kind": "open_direction",
            "semantic_key": "large n continuation",
            "summary": "Review the large-n continuation as an open direction.",
            "payload": {"status": "open"},
            "expires_at": "2099-08-01T00:00:00+00:00",
        },
    )
    apply_research_moment_decision(ws, decide_research_moment(ws, semantic), actor=_actor())
    closeout = _event(
        "SessionCloseout",
        subject_refs=(claim_ref,),
        objective={"milestone_id": "milestone-1"},
        event_id="event-closeout-1",
    )

    decision = decide_research_moment(ws, closeout)
    receipt = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "coalesce_for_review"
    assert len(receipt.record_refs) == 1
    assert receipt.record_refs[0].startswith("recording_candidate_batch:")
    batch = RecordRepository(ws, actor=_actor()).read(receipt.record_refs[0]).record
    assert batch.status == "pending_review"
    assert len(batch.candidates) == 1
    assert batch.can_update_claim_trust is False


def test_high_cost_action_requires_checkpoint_but_missing_prerequisites_block(tmp_path):
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, claim, claim_ref = _seed_workspace(tmp_path)
    ready = _event(
        "ExpensiveRunPending",
        subject_refs=(claim_ref,),
        objective={
            "requested_action": "submit_expensive_hpc_run",
            "prerequisite_refs": [claim_ref],
            "claim_id": claim.claim_id,
            "reason": "Approve the bounded HPC run and its resource budget.",
            "options": ["approve", "revise", "reject"],
        },
    )
    blocked = _event(
        "ExpensiveRunPending",
        subject_refs=(claim_ref,),
        objective={
            "requested_action": "submit_expensive_hpc_run",
            "prerequisite_refs": [claim_ref, "artifact:missing-input"],
            "claim_id": claim.claim_id,
        },
        event_id="event-expensive-blocked",
    )

    ready_decision = decide_research_moment(ws, ready)
    checkpoint = apply_research_moment_decision(ws, ready_decision, actor=_actor())
    before_block = current_canonical_watermark(ws)
    blocked_decision = decide_research_moment(ws, blocked)
    blocked_receipt = apply_research_moment_decision(ws, blocked_decision, actor=_actor())

    assert ready_decision.outcome == "require_checkpoint"
    assert ready_decision.required_checkpoint_action == "submit_expensive_hpc_run"
    assert len(checkpoint.checkpoint_refs) == 1
    assert checkpoint.checkpoint_refs[0].startswith("human_checkpoint:")
    assert blocked_decision.outcome == "block_until_prerequisites"
    assert "artifact:missing-input" in blocked_decision.minimum_refs
    assert blocked_decision.blocked_action == "submit_expensive_hpc_run"
    assert blocked_receipt.status == "blocked"
    assert current_canonical_watermark(ws) == before_block


def test_persisted_knowledge_gap_builds_only_a_bounded_discovery_handoff(tmp_path):
    from brain.v5.pinned_record_refs import pin_current_record
    from brain.v5.proof_obligations import create_proof_obligation
    from brain.v5.recall_audit import RecallRequest, run_recall_audit
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, claim, claim_ref = _seed_workspace(tmp_path)
    gap = create_proof_obligation(
        ws,
        topic_id="target",
        claim_id=claim.claim_id,
        statement="Locate primary literature for the unresolved definition and scope.",
        obligation_type="source_scope_gap",
        status="open",
        maturity_level="exploratory",
        next_action="Run bounded literature discovery after exhaustive local recall.",
        required_evidence=["primary paper", "review source"],
        failure_modes=["search snippet mistaken for evidence"],
    )
    audit = run_recall_audit(
        ws,
        RecallRequest(
            session_id="session-1",
            query_text="finite calculation definition primary literature",
            normalized_intent="identify_missing_literature",
            required_families=(
                "claims",
                "proof_obligations",
                "source_assets",
                "reference_locations",
            ),
            top_k=20,
        ),
        actor=_actor(),
    )
    gap_pin = pin_current_record(ws, f"proof_obligation:{gap.obligation_id}")
    audit_pin = pin_current_record(ws, f"recall_audit:{audit.audit_id}")
    event = _event(
        "FailureOrGapObserved",
        subject_refs=(claim_ref, gap_pin.record_ref, audit_pin.record_ref),
        objective={
            "gap_kind": "knowledge",
            "external_read_approved": True,
            "discovery_spec": {
                "gap_ref": asdict(gap_pin),
                "prior_audit_ref": asdict(audit_pin),
                "framework": "qft",
                "regime": "finite formal calculation",
                "focus_terms": ["finite calculation", "definition"],
                "required_source_types": ["primary_paper", "review"],
                "connector_allowlist": ["qft_literature"],
                "max_results": 8,
                "timeout_seconds": 20,
                "ttl_seconds": 600,
            },
        },
    )

    decision = decide_research_moment(ws, event)
    receipt = apply_research_moment_decision(ws, decision, actor=_actor())

    assert decision.outcome == "auto_capture_process"
    assert decision.application_operation == "knowledge_build_discovery_request"
    assert decision.declared_effect == "read_only"
    assert receipt.status == "handoff_ready"
    assert receipt.handoff["request_id"].startswith("literature-discovery-request:")
    assert receipt.handoff["max_results"] == 8
    assert receipt.handoff["can_create_source_asset"] is False
    assert receipt.record_refs == ()

    stale_spec = {
        **event.objective_payload["discovery_spec"],
        "prior_audit_ref": {
            **event.objective_payload["discovery_spec"]["prior_audit_ref"],
            "content_hash": "0" * 64,
        },
    }
    stale_event = replace(
        event,
        event_id="event-stale-discovery",
        objective_payload={
            **event.objective_payload,
            "discovery_spec": stale_spec,
        },
    )
    stale_decision = decide_research_moment(ws, stale_event)
    assert stale_decision.outcome == "block_until_prerequisites"
    assert any(code.startswith("stale_ref:recall_audit:") for code in stale_decision.reason_codes)


def test_application_rejects_declared_effect_drift(tmp_path):
    from brain.v5.research_moments import (
        ResearchMomentApplicationError,
        apply_research_moment_decision,
        decide_research_moment,
    )

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    decision = decide_research_moment(
        ws,
        _event(
            "RouteChanged",
            subject_refs=(claim_ref,),
            semantic={
                "candidate_kind": "interpretation",
                "semantic_key": "finite interpretation",
                "summary": "Keep this interpretation review gated.",
                "payload": {"scope": "finite only"},
                "expires_at": "2099-08-01T00:00:00+00:00",
            },
        ),
    )

    with pytest.raises(ResearchMomentApplicationError, match="declared effect"):
        apply_research_moment_decision(
            ws,
            replace(decision, declared_effect="kernel_write"),
            actor=_actor(),
        )


def test_decision_identity_binds_payload_and_namespaces_workspace_and_host(tmp_path):
    from brain.v5.research_moments import (
        ResearchMomentApplicationError,
        apply_research_moment_decision,
        decide_research_moment,
    )

    first_ws, _claim, first_ref = _seed_workspace(tmp_path / "first")
    second_ws, _claim, second_ref = _seed_workspace(tmp_path / "second")
    first_event = _event(
        "RouteChanged",
        subject_refs=(first_ref,),
        semantic={
            "candidate_kind": "interpretation",
            "semantic_key": "namespace test",
            "summary": "Keep this interpretation review gated.",
            "payload": {"scope": "finite only"},
            "expires_at": "2099-08-01T00:00:00+00:00",
        },
    )
    second_event = replace(first_event, subject_refs=(second_ref,))
    other_host_event = replace(first_event, host="claude")

    first = decide_research_moment(first_ws, first_event)
    other_workspace = decide_research_moment(second_ws, second_event)
    other_host = decide_research_moment(first_ws, other_host_event)

    assert len({first.dedup_key, other_workspace.dedup_key, other_host.dedup_key}) == 3
    assert not (first_ws.root / "runtime" / "research_moments").exists()
    tampered = replace(
        first,
        application_payload={
            "candidate": {
                **first.application_payload["candidate"],
                "summary": "Tampered after decision.",
            }
        },
    )
    with pytest.raises(ResearchMomentApplicationError, match="identity mismatch"):
        apply_research_moment_decision(first_ws, tampered, actor=_actor())


def test_corrupt_runtime_receipt_is_never_silently_overwritten(tmp_path):
    from brain.v5.research_moments import (
        ResearchMomentApplicationError,
        apply_research_moment_decision,
        decide_research_moment,
        research_moment_receipt_path,
    )

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    decision = decide_research_moment(
        ws,
        _event(
            "ToolRunCompleted",
            subject_refs=(claim_ref,),
            objective={"content_changed": False, "poll_kind": "status_poll"},
        ),
    )
    apply_research_moment_decision(ws, decision, actor=_actor())
    receipt_path = research_moment_receipt_path(ws, decision.dedup_key)
    receipt_path.write_text('{"corrupt": true}\n', encoding="utf-8")

    with pytest.raises(ResearchMomentApplicationError, match="cannot read existing"):
        apply_research_moment_decision(ws, decision, actor=_actor())
    assert receipt_path.read_text(encoding="utf-8") == '{"corrupt": true}\n'


def test_concurrent_replay_applies_the_moment_only_once(tmp_path, monkeypatch):
    import time
    from concurrent.futures import ThreadPoolExecutor

    from brain.v5 import recording_batches
    from brain.v5.research_moments import apply_research_moment_decision, decide_research_moment

    ws, _claim, claim_ref = _seed_workspace(tmp_path)
    decision = decide_research_moment(
        ws,
        _event(
            "RouteChanged",
            subject_refs=(claim_ref,),
            semantic={
                "candidate_kind": "interpretation",
                "semantic_key": "concurrent replay",
                "summary": "Stage this interpretation once.",
                "payload": {"scope": "finite"},
                "expires_at": "2099-08-01T00:00:00+00:00",
            },
        ),
    )
    original = recording_batches.stage_recording_candidate
    calls = []

    def counted_stage(*args, **kwargs):
        calls.append("stage")
        time.sleep(0.05)
        return original(*args, **kwargs)

    monkeypatch.setattr(recording_batches, "stage_recording_candidate", counted_stage)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(apply_research_moment_decision, ws, decision, actor=_actor())
            for _ in range(2)
        ]
        receipts = [future.result() for future in futures]

    assert receipts[0] == receipts[1]
    assert calls == ["stage"]
