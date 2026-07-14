from __future__ import annotations

from dataclasses import asdict
from pathlib import Path


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="m1-e2e", host="pytest")


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _seed_two_topic_workspace(tmp_path):
    from brain.v5.lifecycle_models import (
        CrossTopicRelationRecord,
        ResearchProgramRecord,
        SessionFocusSetRecord,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_research_program,
        record_session_focus_set,
        resolve_session_scope,
    )
    from brain.v5.workspace import bind_session, create_claim, create_context, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_context(ws, "qg-program", title="Quantum gravity program")
    create_topic(
        ws,
        "replica-gravity",
        context_id="qg-program",
        title="Replica gravity primary problem",
    )
    create_topic(
        ws,
        "operator-algebra-methods",
        context_id="qg-program",
        title="Operator algebra supporting methods",
    )
    primary_claim = create_claim(
        ws,
        topic_id="replica-gravity",
        statement="The finite-replica identity holds under the stated assumptions.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="The analytic continuation remains open.",
    )
    supporting_claim = create_claim(
        ws,
        topic_id="operator-algebra-methods",
        statement="The modular-flow construction supplies a candidate method.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="Applicability to the target algebra requires revalidation.",
    )
    bind_session(
        ws,
        "qg-session",
        topic_id="replica-gravity",
        context_id="qg-program",
        active_claim=primary_claim.claim_id,
    )
    build_query_index(ws)

    primary_scope = resolve_session_scope(ws, "qg-session")
    assert primary_scope.program_id == ""
    assert primary_scope.supporting_refs == ()

    program = ResearchProgramRecord(
        program_id="qg-replica-program",
        title="Replica gravity with operator-algebra support",
        primary_topic_ids=["replica-gravity"],
        supporting_topic_ids=["operator-algebra-methods"],
        scientific_boundary="Method reuse does not transfer a source-topic claim.",
        review_status="approved",
    )
    record_research_program(ws, program, actor=_actor())
    bridge = CrossTopicRelationRecord(
        relation_id="modular-method-to-replica",
        source_topic_id="operator-algebra-methods",
        target_topic_id="replica-gravity",
        source_ref=f"claim:{supporting_claim.claim_id}",
        target_ref=f"claim:{primary_claim.claim_id}",
        relation_kind="method_candidate",
        transfer_rationale="Only the method is reusable; the physics claim remains topic-local.",
        applicability_boundary="Revalidate the algebra, state, and continuation assumptions.",
        revalidation_requirements=["check the target algebra", "check continuation assumptions"],
        status="reviewed",
    )
    record_cross_topic_relation(ws, bridge, actor=_actor())
    focus = SessionFocusSetRecord(
        focus_set_id="qg-session-focus",
        session_id="qg-session",
        primary_topic_id="replica-gravity",
        focus_kind="claim",
        focus_ref=f"claim:{primary_claim.claim_id}",
        supporting_refs=["cross_topic_relation:modular-method-to-replica"],
        program_id=program.program_id,
        created_at="2026-07-14T00:00:00+00:00",
    )
    record_session_focus_set(ws, focus, actor=_actor())
    return ws, primary_claim, supporting_claim, primary_scope


def test_m1_migration_audit_proposes_review_only_sidecars_without_writes(tmp_path):
    from brain.v5.lifecycle_migration import audit_lifecycle_migration_candidates
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import bind_session, create_claim, create_context, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_context(ws, "shared-context", title="Shared research context")
    create_topic(ws, "primary", context_id="shared-context", title="Primary topic")
    create_topic(ws, "supporting", context_id="shared-context", title="Supporting topic")
    claim = create_claim(
        ws,
        topic_id="primary",
        statement="A bounded claim anchors the existing session.",
        evidence_profile="formal_theory",
        confidence_state="conditional",
        active_uncertainty="The broader program boundary needs review.",
    )
    bind_session(
        ws,
        "legacy-session",
        topic_id="primary",
        context_id="shared-context",
        active_claim=claim.claim_id,
    )
    build_query_index(ws)
    before = _tree_snapshot(ws.root)

    first = audit_lifecycle_migration_candidates(ws)
    second = audit_lifecycle_migration_candidates(ws)

    assert first == second
    assert _tree_snapshot(ws.root) == before
    assert first["kind"] == "lifecycle_migration_candidate_audit"
    assert first["inventory"] == {
        "topic_count": 2,
        "session_count": 1,
        "focus_set_count": 0,
        "program_count": 0,
    }
    assert first["read_errors"] == []
    assert first["existing_sessions_without_focus"] == ["legacy-session"]
    assert first["focus_candidates"] == [
        {
            "session_id": "legacy-session",
            "primary_topic_id": "primary",
            "focus_kind": "claim",
            "focus_ref": f"claim:{claim.claim_id}",
            "basis": "existing_session_active_claim",
            "human_review_required": True,
            "canonical_payload_ready": False,
        }
    ]
    assert first["program_candidates"] == [
        {
            "context_id": "shared-context",
            "topic_ids": ["primary", "supporting"],
            "session_ids": ["legacy-session"],
            "basis": "shared_context_routing_hint_only",
            "scientific_boundary_inferred": False,
            "human_review_required": True,
            "canonical_payload_ready": False,
        }
    ]
    assert first["write_executed"] is False
    assert first["can_update_kernel_state"] is False
    assert first["can_update_claim_trust"] is False
    assert first["claim_trust_transfer"] == "forbidden"


def test_two_topic_lifecycle_closes_and_resumes_without_rebind_or_trust_transfer(tmp_path):
    from brain.v5.lifecycle_facade import (
        apply_session_closeout,
        coalesce_candidate_batch,
        plan_session_closeout,
        stage_candidate,
        start_session,
    )
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_scope import resolve_session_scope
    from brain.v5.session_resume import build_session_resume_card
    from brain.v5.workspace import get_session_binding

    ws, primary_claim, supporting_claim, primary_scope = _seed_two_topic_workspace(tmp_path)
    primary_claim_path = ws.registry_dir("claims") / f"{primary_claim.claim_id}.md"
    supporting_claim_path = ws.registry_dir("claims") / f"{supporting_claim.claim_id}.md"
    claim_bytes = (primary_claim_path.read_bytes(), supporting_claim_path.read_bytes())
    active_claim = get_session_binding(ws, "qg-session").active_claim

    program_scope = resolve_session_scope(ws, "qg-session")
    assert program_scope.primary_topic_id == primary_scope.primary_topic_id
    assert program_scope.program_id == "qg-replica-program"
    assert program_scope.supporting_topic_ids == ("operator-algebra-methods",)
    assert "claim:" + supporting_claim.claim_id in program_scope.supporting_refs
    assert "claim:" + supporting_claim.claim_id in program_scope.requires_revalidation_refs
    assert program_scope.claim_trust_transfer == "forbidden"

    candidate = {
        "staging_id": "",
        "session_id": "qg-session",
        "topic_id": "replica-gravity",
        "candidate_kind": "workflow_candidate",
        "semantic_key": "finite replica consistency check",
        "summary": "Check the finite-replica identity before attempting continuation.",
        "payload": {"boundary": "finite replica number only"},
        "source_refs": [f"claim:{primary_claim.claim_id}"],
        "source_event_refs": ["event:qg-e2e"],
        "missing_prerequisites": ["analytic continuation"],
        "dedup_key": "",
        "created_at": "2026-07-14T00:00:00+00:00",
        "expires_at": "2099-07-14T00:00:00+00:00",
    }
    staged = stage_candidate(ws.base, candidate)
    replay = stage_candidate(
        ws.base,
        {**candidate, "semantic_key": "  FINITE REPLICA CONSISTENCY CHECK  "},
    )
    assert replay["staging_id"] == staged["staging_id"]
    assert replay["dedup_key"] == staged["dedup_key"]
    assert replay["trust_effect"] == "none"

    batch = coalesce_candidate_batch(ws.base, "qg-session", "m1-e2e", actor=asdict(_actor()))
    batch_replay = coalesce_candidate_batch(
        ws.base, "qg-session", "m1-e2e", actor=asdict(_actor())
    )
    assert batch["batch_ref"] == batch_replay["batch_ref"]
    assert batch["review_status"] == "pending_review"
    assert (batch["status"], batch_replay["status"]) == ("created", "unchanged")

    closeout_request = {
        "session_id": "qg-session",
        "milestone_id": "m1-e2e",
        "completed_work": ["Established the bounded two-topic workflow."],
        "can_say": [
            {
                "text": "The finite-replica identity is available conditionally.",
                "boundary_class": "conditional",
                "source_refs": [f"claim:{primary_claim.claim_id}"],
            }
        ],
        "cannot_say": [
            {
                "text": "The supporting method proves the target claim.",
                "boundary_class": "open_gap",
                "source_refs": ["cross_topic_relation:modular-method-to-replica"],
            }
        ],
        "open_gaps": [
            {
                "text": "Analytic continuation and target-side revalidation remain open.",
                "boundary_class": "open_gap",
                "source_refs": [f"claim:{primary_claim.claim_id}"],
            }
        ],
        "failed_routes": [],
        "next_actions": ["Revalidate the operator-algebra method in the target topic."],
        "source_record_refs": [
            f"claim:{primary_claim.claim_id}",
            "cross_topic_relation:modular-method-to-replica",
        ],
        "pending_candidate_batch_refs": [batch["batch_ref"]],
        "reusable_workflow_candidate_refs": [],
    }
    closeout_plan = plan_session_closeout(ws.base, closeout_request)
    assert closeout_plan["allowed"] is True
    assert closeout_plan["write_executed"] is False
    closeout = apply_session_closeout(
        ws.base,
        closeout_plan,
        closeout_plan["plan_id"],
        actor=asdict(_actor()),
    )
    assert closeout["write_status"] == "created"
    assert closeout["can_update_claim_trust"] is False

    first_start = start_session(ws.base, "qg-session")
    reconnected_start = start_session(ws.base, "qg-session")
    direct_card = build_session_resume_card(ws, "qg-session")
    assert first_start == reconnected_start
    assert first_start["resume_card"] == direct_card
    assert direct_card["closeout_ref"] == closeout["closeout_ref"]
    assert direct_card["can_say"][0]["boundary_class"] == "conditional"
    assert direct_card["cannot_say"][0]["boundary_class"] == "open_gap"
    assert direct_card["coverage"]["content_verified"] is True

    repository = RecordRepository(ws, actor=_actor())
    stored_bridge = repository.read("cross_topic_relation:modular-method-to-replica").record
    stored_batch = repository.read(batch["batch_ref"]).record
    assert stored_bridge.claim_trust_transfer == "forbidden"
    assert stored_bridge.can_update_claim_trust is False
    assert stored_batch.can_update_claim_trust is False
    assert get_session_binding(ws, "qg-session").active_claim == active_claim
    assert (primary_claim_path.read_bytes(), supporting_claim_path.read_bytes()) == claim_bytes


def test_startup_reuses_one_strong_snapshot_and_preserves_global_freshness(
    tmp_path,
    monkeypatch,
):
    import brain.v5.query_index_snapshot as query_index_snapshot

    from brain.v5.lifecycle_facade import start_session
    from brain.v5.record_family_registry import record_family_specs

    ws, _primary_claim, _supporting_claim, _primary_scope = _seed_two_topic_workspace(
        tmp_path
    )
    with query_index_snapshot._orientation_cache_guard:
        query_index_snapshot._orientation_cache.clear()

    load_count = 0
    strong_state_families: list[str] = []
    original_load = query_index_snapshot.load_query_index
    original_state = query_index_snapshot._current_family_state_token

    def counted_load(workspace):
        nonlocal load_count
        load_count += 1
        return original_load(workspace)

    def counted_state(workspace, family):
        strong_state_families.append(family)
        return original_state(workspace, family)

    monkeypatch.setattr(query_index_snapshot, "load_query_index", counted_load)
    monkeypatch.setattr(
        query_index_snapshot,
        "_current_family_state_token",
        counted_state,
    )

    result = start_session(ws.base, "qg-session")
    replay = start_session(ws.base, "qg-session")

    assert result["resume_card"]["fallback_used"] is True
    assert replay == result
    assert load_count == 1
    assert strong_state_families == [
        *sorted(record_family_specs()),
        *sorted(record_family_specs()),
    ]
