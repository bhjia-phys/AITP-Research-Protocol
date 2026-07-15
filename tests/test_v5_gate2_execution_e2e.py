from __future__ import annotations

import base64
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta


def test_librpa_hpc_fixture_contract_recovers_exact_accepted_execution(
    tmp_path,
    monkeypatch,
):
    from tests.test_v5_execution_baselines import _approval, _actor, _ready_chain

    from brain.v5.checkpoint_bindings import decide_bound_checkpoint, request_bound_checkpoint
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.effective_attempts import resolve_effective_attempt_state
    from brain.v5.execution_baselines import BaselineAcceptanceRequest, assess_baseline_readiness
    from brain.v5.execution_writers import record_code_state_v2, record_tool_run_v2
    from brain.v5.mcp_execution import aitp_v5_execution_apply_bound_action
    from brain.v5.models import CodeStateRecord
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record
    from brain.v5.workspace import bind_session

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
        reason="Accept deterministic LibRPA/HPC fixture baseline.",
        requested_by="gate2-fixture",
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
    secret = b"gate2-fixture-approval-key-32-bytes"
    monkeypatch.setenv(
        "AITP_HUMAN_APPROVAL_HMAC_KEY_B64",
        base64.b64encode(secret).decode("ascii"),
    )
    rationale = "Reviewed the exact fixture dependency closure."
    decision = decide_bound_checkpoint(
        ws,
        request_ref=checkpoint.request_ref,
        expected=checkpoint.binding,
        decision="approve",
        rationale=rationale,
        decided_by="fixture-reviewer",
        approval_receipt=_approval(
            secret,
            checkpoint.record.checkpoint_id,
            checkpoint.request_ref.content_hash,
            rationale,
        ),
        now=now,
    )
    bind_session(
        ws,
        "gate2-execution-session",
        topic_id="compute",
        context_id="theory",
        runtime="pytest",
        active_claim=claim.claim_id,
    )
    applied = aitp_v5_execution_apply_bound_action(
        str(tmp_path),
        payload_json=__import__("json").dumps({
            "session_id": "gate2-execution-session",
            "action": "accept_execution_baseline",
            "request_ref": asdict(checkpoint.request_ref),
            "decision_ref": asdict(decision.decision_ref),
            "binding": asdict(checkpoint.binding),
            "action_request": request.action_payload(),
        }),
    )
    baseline_result = applied["result"]["result_refs"][0]
    baseline_pin = PinnedRecordRef(
        baseline_result["record_ref"],
        baseline_result["content_hash"],
        baseline_result["revision"],
    )
    baseline_ref = baseline_pin.record_ref
    baseline = get_record_version(ws, baseline_pin).record
    assert baseline.environment_ref == run.environment_ref
    assert baseline.environment_hash == run.environment_hash
    assert baseline.environment_revision == run.environment_revision

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="gate2-execution-session",
            objective_text="resume the accepted HPC solver execution",
            max_tokens=4000,
            max_bytes=18000,
            candidate_limit=40,
        ),
    )
    assert run_ref.record_ref in bundle.record_refs
    assert baseline_ref in bundle.record_refs
    assert monitor_ref.record_ref in bundle.record_refs
    assert run.environment_ref in bundle.record_refs
    assert bundle.can_update_claim_trust is False
    environment_pin = PinnedRecordRef(
        run.environment_ref,
        run.environment_hash,
        run.environment_revision,
    )
    exact_environment = compile_research_context(
        ws,
        ContextRequest(
            session_id="gate2-execution-session",
            disclosure_level="exact_expansion",
            exact_refs=(environment_pin.record_ref,),
            exact_pins=(environment_pin,),
            max_tokens=1200,
            max_bytes=6000,
        ),
    )
    environment_payload = exact_environment.expansion["items"][0]["record"]
    assert exact_environment.expansion["requested_pins"] == [asdict(environment_pin)]
    assert environment_payload["record_content_hash"] == environment_pin.content_hash
    assert environment_payload["revision"] == environment_pin.revision

    incomplete = replace(
        run,
        run_id="solver-incomplete-run",
        scientific_run_id="solver-incomplete-scientific-run",
        supersedes_run_id="",
        output_manifest=[],
        exit_status={"state": "RUNNING"},
        recorded_maturity="diagnostic",
    )
    incomplete_write = record_tool_run_v2(ws, incomplete, actor=_actor())
    incomplete_ref = PinnedRecordRef(
        incomplete_write.record_ref,
        incomplete_write.content_hash,
        incomplete_write.revision,
    )
    incomplete_state = resolve_effective_attempt_state(ws, incomplete_ref)
    assert incomplete_state.attempt_eligible is False

    dirty_unpatched = CodeStateRecord(
        code_state_id="librpa-dirty-unpatched",
        repo_id="librpa",
        upstream_remote="origin",
        upstream_branch="main",
        upstream_commit="a" * 40,
        local_branch="fixture",
        worktree_path="/fixture/librpa",
        dirty=True,
    )
    import pytest

    with pytest.raises(ValueError, match="patch manifest"):
        record_code_state_v2(ws, dirty_unpatched, actor=_actor())
    assert pin_current_record(ws, claim_ref.record_ref) == claim_ref
    claim_after = get_record_version(ws, claim_ref).record
    assert claim_after.confidence_state == claim.confidence_state


def test_formal_derivation_fixture_preserves_gap_repair_and_trust_boundaries(tmp_path):
    from tests.test_v5_derivations import _actor, _chain, _fixture, _step

    from brain.v5.derivation_reviews import project_derivation_status
    from brain.v5.derivations import record_derivation_chain, record_derivation_step
    from brain.v5.pinned_record_refs import PinnedRecordRef, get_record_version, pin_current_record

    data = _fixture(tmp_path)
    claim_before = pin_current_record(data["ws"], f"claim:{data['claim'].claim_id}")
    blocked_step = _step(
        data,
        step_id="replica-gap-repair",
        sequence=1,
        unresolved=("analytic continuation uniqueness remains open",),
        status="blocked",
    )
    blocked_write = record_derivation_step(data["ws"], blocked_step, actor=_actor())
    blocked_ref = PinnedRecordRef(
        blocked_write.record_ref,
        blocked_write.content_hash,
        blocked_write.revision,
    )
    draft_chain = _chain(
        data,
        (blocked_ref,),
        status="blocked",
        open_gaps=("analytic continuation uniqueness remains open",),
    )
    draft_write = record_derivation_chain(data["ws"], draft_chain, actor=_actor())

    repaired_step = _step(
        data,
        step_id="replica-gap-repair",
        sequence=1,
        status="established",
    )
    repaired_write = record_derivation_step(
        data["ws"],
        repaired_step,
        actor=_actor(),
        expected_current_hash=blocked_ref.content_hash,
    )
    repaired_ref = PinnedRecordRef(
        repaired_write.record_ref,
        repaired_write.content_hash,
        repaired_write.revision,
    )
    closed_chain = _chain(data, (repaired_ref,), status="structurally_closed")
    closed_write = record_derivation_chain(
        data["ws"],
        closed_chain,
        actor=_actor(),
        expected_current_hash=draft_write.content_hash,
    )
    chain_ref = PinnedRecordRef(
        closed_write.record_ref,
        closed_write.content_hash,
        closed_write.revision,
    )
    status = project_derivation_status(data["ws"], chain_ref)
    stored = get_record_version(data["ws"], chain_ref)

    assert repaired_ref.revision == blocked_ref.revision + 1
    assert chain_ref.revision == 2
    assert status.structurally_closed is True
    assert status.reviewed is False
    assert status.validated is False
    assert status.can_update_claim_trust is False
    assert stored.record.assumptions == ["integer n before continuation"]
    assert stored.record.conventions == ["Euclidean signature", "normalized Z_1 = 1"]
    assert stored.record.open_gaps == []
    assert not ({"hidden_reasoning", "chain_of_thought", "private_scratchpad"} & stored.frontmatter.keys())
    assert pin_current_record(data["ws"], claim_before.record_ref) == claim_before
    claim_after = get_record_version(data["ws"], claim_before).record
    assert claim_after.confidence_state == data["claim"].confidence_state
