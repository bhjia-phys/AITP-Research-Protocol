from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="session-lifecycle-test", host="pytest")


def _seed_workspace(tmp_path, *, active_claim: bool = True):
    from brain.v5.lifecycle_models import RecordingCandidateBatchRecord, SessionFocusSetRecord
    from brain.v5.models import (
        ProofObligationRecord,
        ResearchRouteRecord,
        SkillPatchProposalRecord,
        ToolRunRecord,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_scope import record_session_focus_set
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="theory", title="Finite diagnostic target")
    claim = create_claim(
        ws,
        topic_id="target",
        statement="The finite diagnostic is established but the large-size limit is open.",
        evidence_profile="formal_theory",
        confidence_state="finite_evidence",
        active_uncertainty="No large-size proof is available.",
    )
    repository = RecordRepository(ws, actor=_actor())
    repository.write(
        "tool_runs",
        ToolRunRecord(
            run_id="run-1",
            recipe_id="recipe-finite-diagnostic",
            tool_family="python",
            tool_name="finite-diagnostic",
            topic_id="target",
            claim_id=claim.claim_id,
            inputs={"sizes": [4, 6, 8]},
            outputs={"status": "completed"},
            evidence_status="reviewed",
        ),
        body="# Finite diagnostic run\n",
    )
    repository.write(
        "proof_obligations",
        ProofObligationRecord(
            obligation_id="large-L",
            topic_id="target",
            claim_id=claim.claim_id,
            statement="Control the large-size limit.",
            obligation_type="asymptotic_proof",
            status="open",
            maturity_level="open_gap",
            next_action="derive a uniform finite-size bound",
        ),
        body="# Large-size proof obligation\n",
    )
    repository.write(
        "routes",
        ResearchRouteRecord(
            route_id="naive-extrapolation",
            topic_id="target",
            title="Naive extrapolation",
            route_type="diagnostic",
            status="failed",
            rationale="Finite points do not prove the asymptotic limit.",
            claim_id=claim.claim_id,
            session_id="s1",
            next_action="replace extrapolation with a controlled bound",
        ),
        body="# Failed route\n",
    )
    repository.write(
        "recording_candidate_batches",
        RecordingCandidateBatchRecord(
            batch_id="batch-1",
            session_id="s1",
            topic_id="target",
            milestone_id="m1",
            candidates=[{"candidate_kind": "observation", "text": "finite diagnostic completed"}],
            dedup_keys=["observation:finite-diagnostic"],
        ),
        body="# Pending recording candidates\n",
    )
    repository.write(
        "skill_patch_proposals",
        SkillPatchProposalRecord(
            proposal_id="workflow-1",
            skill_name="finite-diagnostic-workflow",
            current_version="0.0.0",
            proposed_version="0.1.0",
            patch_summary="Candidate workflow only; review is still required.",
            patch_body="Run the finite diagnostic and check its applicability boundary.",
            topic_ids=["target"],
            supporting_records=["tool_run:run-1"],
            applicability=["finite-size diagnostics only"],
            preconditions=["validated input fixture"],
            execution_refs=["tool_run:run-1"],
            review_status="draft",
        ),
        body="# Reusable workflow candidate\n",
    )
    bind_session(
        ws,
        "s1",
        topic_id="target",
        context_id="theory",
        active_claim=claim.claim_id if active_claim else "",
        active_route="naive-extrapolation",
    )
    focus_kind = "claim" if active_claim else "route"
    focus_ref = f"claim:{claim.claim_id}" if active_claim else "research_route:naive-extrapolation"
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-1",
            session_id="s1",
            primary_topic_id="target",
            focus_kind=focus_kind,
            focus_ref=focus_ref,
            objective_refs=["proof_obligation:large-L"],
        ),
        actor=_actor(),
    )
    build_query_index(ws)
    return {
        "ws": ws,
        "claim": claim,
        "claim_path": ws.registry_dir("claims") / f"{claim.claim_id}.md",
    }


def _request(*, milestone_id: str = "m1", can_say_text: str = "finite diagnostic completed"):
    from brain.v5.lifecycle_models import CloseoutBoundaryItem
    from brain.v5.session_lifecycle import SessionCloseoutRequest

    return SessionCloseoutRequest(
        session_id="s1",
        milestone_id=milestone_id,
        completed_work=(can_say_text,),
        can_say=(
            CloseoutBoundaryItem(
                text=can_say_text,
                boundary_class="finite_evidence",
                source_refs=["tool_run:run-1"],
            ),
        ),
        cannot_say=(
            CloseoutBoundaryItem(
                text="no large-size proof",
                boundary_class="open_gap",
                source_refs=["proof_obligation:large-L"],
            ),
        ),
        open_gaps=(
            CloseoutBoundaryItem(
                text="large-size proof",
                boundary_class="open_gap",
                source_refs=["proof_obligation:large-L"],
            ),
        ),
        failed_routes=(
            CloseoutBoundaryItem(
                text="naive extrapolation",
                boundary_class="finite_evidence",
                source_refs=["research_route:naive-extrapolation"],
            ),
        ),
        next_actions=("derive the finite-size bound",),
        source_record_refs=(
            "tool_run:run-1",
            "proof_obligation:large-L",
            "research_route:naive-extrapolation",
        ),
        pending_candidate_batch_refs=("recording_candidate_batch:batch-1",),
        reusable_workflow_candidate_refs=("skill_patch_proposal:workflow-1",),
    )


def _record_closeout(seed, request=None):
    from brain.v5.session_lifecycle import build_session_closeout_plan, record_session_closeout

    plan = build_session_closeout_plan(seed["ws"], request or _request())
    result = record_session_closeout(seed["ws"], plan, actor=_actor())
    return plan, result


def test_one_closeout_is_idempotent_and_has_no_trust_effect(tmp_path):
    from brain.v5.record_repository import RecordRepository
    from brain.v5.session_lifecycle import build_session_closeout_plan, record_session_closeout

    seed = _seed_workspace(tmp_path)
    original_claim = seed["claim_path"].read_bytes()
    plan = build_session_closeout_plan(seed["ws"], _request())

    first = record_session_closeout(seed["ws"], plan, actor=_actor())
    second = record_session_closeout(seed["ws"], plan, actor=_actor())
    stored = RecordRepository(seed["ws"], actor=_actor()).read(first.record_ref)

    assert plan.allowed is True
    assert plan.record.can_update_claim_trust is False
    assert plan.record.coverage_content_verified is True
    assert plan.record.coverage_exhaustive is True
    assert plan.record.family_state_tokens
    assert plan.record.family_content_watermarks
    assert (first.status, second.status) == ("created", "unchanged")
    assert stored.status == "found"
    assert seed["claim_path"].read_bytes() == original_claim


def test_unverified_can_say_is_demoted_and_unresolved_core_refs_block_write(tmp_path):
    from brain.v5.lifecycle_models import CloseoutBoundaryItem
    from brain.v5.session_lifecycle import (
        SessionLifecycleError,
        build_session_closeout_plan,
        record_session_closeout,
    )

    seed = _seed_workspace(tmp_path)
    unsupported = CloseoutBoundaryItem(
        text="the asymptotic result is probably true",
        boundary_class="speculative",
        source_refs=[],
    )
    request = replace(_request(), can_say=(unsupported, *_request().can_say))
    plan = build_session_closeout_plan(seed["ws"], request)

    assert plan.allowed is True
    assert [item.text for item in plan.record.can_say] == ["finite diagnostic completed"]
    assert [item.text for item in plan.record.unverified_notes] == [unsupported.text]

    blocked = build_session_closeout_plan(
        seed["ws"],
        replace(request, source_record_refs=(*request.source_record_refs, "tool_run:missing")),
    )
    assert blocked.allowed is False
    assert "tool_run:missing" in blocked.unresolved_refs
    with pytest.raises(SessionLifecycleError, match="not allowed"):
        record_session_closeout(seed["ws"], blocked, actor=_actor())


def test_unresolved_focus_objective_blocks_closeout_even_when_request_omits_it(tmp_path):
    from brain.v5.query_index import build_query_index
    from brain.v5.session_lifecycle import build_session_closeout_plan

    seed = _seed_workspace(tmp_path)
    objective_path = seed["ws"].registry_dir("proof_obligations") / "large-L.md"
    objective_path.unlink()
    build_query_index(seed["ws"])
    request = replace(
        _request(),
        cannot_say=(),
        open_gaps=(),
        source_record_refs=("tool_run:run-1", "research_route:naive-extrapolation"),
    )

    plan = build_session_closeout_plan(seed["ws"], request)

    assert plan.allowed is False
    assert "proof_obligation:large-L" in plan.unresolved_refs


def test_resume_card_preserves_boundaries_candidates_and_coverage(tmp_path):
    from brain.v5.session_resume import build_session_resume_card

    seed = _seed_workspace(tmp_path)
    plan, result = _record_closeout(seed)
    card = build_session_resume_card(seed["ws"], "s1")

    assert card["closeout_ref"] == result.record_ref
    assert card["milestone_id"] == "m1"
    assert card["can_say"][0]["boundary_class"] == "finite_evidence"
    assert card["can_say"][0]["source_refs"] == ["tool_run:run-1"]
    assert card["cannot_say"][0]["boundary_class"] == "open_gap"
    assert card["open_gaps"][0]["text"] == "large-size proof"
    assert card["failed_routes"][0]["text"] == "naive extrapolation"
    assert card["next_actions"] == ["derive the finite-size bound"]
    assert card["pending_candidate_batch_refs"] == ["recording_candidate_batch:batch-1"]
    assert card["reusable_workflow_candidate_refs"] == ["skill_patch_proposal:workflow-1"]
    assert card["coverage"]["checked_families"] == plan.record.checked_families
    assert card["coverage"]["relevant_stale"] is False
    assert card["coverage"]["content_verified"] is True
    assert result.record_ref in card["exact_expansion_refs"]
    assert card["orientation_only"] is True
    assert card["can_update_kernel_state"] is False
    assert card["can_update_claim_trust"] is False


def test_resume_staleness_distinguishes_unrelated_and_required_family_writes(tmp_path):
    from brain.v5.models import ArtifactRecord, ToolRunRecord
    from brain.v5.record_repository import RecordRepository
    from brain.v5.session_resume import build_session_resume_card

    seed = _seed_workspace(tmp_path)
    _record_closeout(seed)
    repository = RecordRepository(seed["ws"], actor=_actor())
    repository.write(
        "artifacts",
        ArtifactRecord(
            artifact_id="unrelated-artifact",
            topic_id="target",
            claim_id=seed["claim"].claim_id,
            artifact_type="note",
            uri="artifact://unrelated",
            summary="This family was not part of the closeout coverage scope.",
        ),
    )
    unrelated = build_session_resume_card(seed["ws"], "s1")

    assert unrelated["coverage"]["relevant_stale"] is False
    assert "artifacts" not in unrelated["coverage"]["changed_content_families"]

    repository.write(
        "tool_runs",
        ToolRunRecord(
            run_id="run-2",
            recipe_id="recipe-finite-diagnostic",
            tool_family="python",
            tool_name="finite-diagnostic",
            topic_id="target",
            claim_id=seed["claim"].claim_id,
            outputs={"status": "new-related-run"},
        ),
    )
    related = build_session_resume_card(seed["ws"], "s1")

    assert related["coverage"]["relevant_stale"] is True
    assert "tool_runs" in related["coverage"]["changed_content_families"]
    assert related["partial"] is True


def test_resume_fails_closed_when_required_family_bypasses_the_index(tmp_path):
    from brain.v5.models import ToolRunRecord
    from brain.v5.session_resume import build_session_resume_card
    from brain.v5.store import write_record

    seed = _seed_workspace(tmp_path)
    _record_closeout(seed)
    write_record(
        seed["ws"].registry_dir("tool_runs") / "run-unindexed.md",
        ToolRunRecord(
            run_id="run-unindexed",
            recipe_id="recipe-finite-diagnostic",
            tool_family="python",
            tool_name="finite-diagnostic",
            topic_id="target",
            claim_id=seed["claim"].claim_id,
            outputs={"status": "bypassed-derived-index"},
        ),
    )

    card = build_session_resume_card(seed["ws"], "s1")

    assert card["coverage"]["relevant_stale"] is True
    assert card["coverage"]["content_verified"] is False
    assert card["partial"] is True


def test_resume_without_closeout_or_active_claim_uses_bounded_fallback(tmp_path):
    from brain.v5.session_resume import build_session_resume_card

    seed = _seed_workspace(tmp_path, active_claim=False)
    before = list(seed["ws"].registry_dir("session_closeouts").glob("*.md"))
    card = build_session_resume_card(seed["ws"], "s1", max_tokens=300)
    after = list(seed["ws"].registry_dir("session_closeouts").glob("*.md"))

    assert card["closeout_ref"] == ""
    assert card["fallback_used"] is True
    assert card["current_boundary"]["claim_id"] == ""
    assert card["disclosure_level"] == "startup_orientation"
    assert card["estimated_tokens"] <= 300
    assert card["byte_count"] <= 4000
    assert card["orientation_only"] is True
    assert before == after == []


def test_latest_closeout_revision_is_selected_without_overwriting_prior_milestone(tmp_path):
    from brain.v5.session_resume import build_session_resume_card

    seed = _seed_workspace(tmp_path)
    first_plan, first = _record_closeout(seed, _request(milestone_id="m1"))
    second_plan, second = _record_closeout(
        seed,
        _request(milestone_id="m2", can_say_text="controlled finite-size bound derived"),
    )
    card = build_session_resume_card(seed["ws"], "s1")

    assert first.record_ref != second.record_ref
    assert first_plan.record.closeout_id != second_plan.record.closeout_id
    assert card["closeout_ref"] == second.record_ref
    assert card["milestone_id"] == "m2"
    assert card["can_say"][0]["text"] == "controlled finite-size bound derived"


def test_topic_status_startup_workspace_and_generated_file_share_resume_boundary(tmp_path):
    from brain.v5.topic_status import write_topic_status_surfaces
    from brain.v5.topic_status_startup import write_topic_status_startup_surfaces
    from brain.v5.workspace_refresh import refresh_workspace_startup_views

    seed = _seed_workspace(tmp_path)
    _record_closeout(seed)
    full = write_topic_status_surfaces(seed["ws"], session_id="s1")
    startup = write_topic_status_startup_surfaces(seed["ws"], session_id="s1")
    refresh = refresh_workspace_startup_views(seed["ws"], session_id="s1")
    generated = seed["ws"].topic_dir("target") / "runtime" / "session_start.generated.md"
    generated_text = generated.read_text(encoding="utf-8")

    boundary_json = full["resume_boundary_json"]
    assert startup["resume_boundary_json"] == boundary_json
    assert refresh["resume_boundary_json"] == boundary_json
    assert refresh["topic_status_bundles"][0]["resume_boundary_json"] == boundary_json
    assert boundary_json in generated_text
    assert full["resume_boundary"] == startup["resume_boundary"]
    assert startup["resume_boundary"] == refresh["resume_boundary"]
    assert full["resume_boundary"]["can_update_claim_trust"] is False
    compact_coverage = full["compact_context"]["retrieval_coverage"]
    assert compact_coverage["scope_state_fresh"] is True
    assert compact_coverage["scope_content_verified"] is True
    assert compact_coverage["can_claim_no_result"] is False
