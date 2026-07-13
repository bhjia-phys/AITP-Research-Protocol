from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="scope-test", host="pytest")


def _seed_workspace(tmp_path):
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="theory", title="Target theory topic")
    create_topic(ws, "source", context_id="theory", title="Source method topic")
    target_claim = create_claim(
        ws,
        topic_id="target",
        statement="The target claim still requires a target-side derivation.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="The imported method has not been revalidated.",
    )
    source_claim = create_claim(
        ws,
        topic_id="source",
        statement="The source method is valid under its source assumptions.",
        evidence_profile="formal_theory",
        confidence_state="validated",
        active_uncertainty="Transfer outside the source topic is unknown.",
    )
    bind_session(
        ws,
        "s1",
        topic_id="target",
        context_id="theory",
        active_claim=target_claim.claim_id,
    )
    return ws, target_claim, source_claim


def _seed_focus_targets(ws, target_claim):
    from brain.v5.models import (
        CodeStateRecord,
        QuestionRecord,
        ResearchRouteRecord,
        ResearchRunRecord,
        SourceAssetRecord,
    )
    from brain.v5.record_repository import RecordRepository

    repository = RecordRepository(ws, actor=_actor())
    repository.write(
        "questions",
        QuestionRecord(
            question_id="question-1",
            scene="research",
            target_claim=target_claim.claim_id,
            question="Which boundary controls the target derivation?",
            why_this_question="It selects the next proof step.",
            expected_answer_shape="A sourced boundary statement.",
        ),
    )
    repository.write(
        "routes",
        ResearchRouteRecord(
            route_id="route-1",
            topic_id="target",
            title="Target derivation route",
            route_type="derivation",
            status="active",
            rationale="Resolve the target boundary first.",
            claim_id=target_claim.claim_id,
        ),
    )
    repository.write(
        "research_runs",
        ResearchRunRecord(
            run_id="run-1",
            topic_id="target",
            objective="Test the target derivation.",
            research_question="Does the source method survive target assumptions?",
            operator="pytest",
            status="active",
            phase="analysis",
            claim_id=target_claim.claim_id,
            session_id="s1",
        ),
    )
    repository.write(
        "source_assets",
        SourceAssetRecord(
            asset_id="source-1",
            topic_id="target",
            asset_type="note",
            uri="https://example.invalid/target-source",
            title="Target source set",
            claim_id=target_claim.claim_id,
        ),
    )
    repository.write(
        "code_states",
        CodeStateRecord(
            code_state_id="code-1",
            repo_id="theory-code",
            upstream_remote="origin",
            upstream_branch="main",
            upstream_commit="a" * 40,
            local_branch="analysis",
            worktree_path="/tmp/theory-code",
            dirty=False,
        ),
    )
    return {
        "question": "question:question-1",
        "claim": f"claim:{target_claim.claim_id}",
        "route": "research_route:route-1",
        "work_package": "research_run:run-1",
        "source_set": "source_asset:source-1",
        "code_change": "code_state:code-1",
        "run_campaign": "research_run:run-1",
    }


@pytest.mark.parametrize(
    "focus_kind",
    ["question", "claim", "route", "work_package", "source_set", "code_change", "run_campaign"],
)
def test_all_focus_kinds_require_existing_typed_refs(tmp_path, focus_kind):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import record_session_focus_set

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    refs = _seed_focus_targets(ws, target_claim)

    result = record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id=f"focus-{focus_kind}",
            session_id="s1",
            primary_topic_id="target",
            focus_kind=focus_kind,
            focus_ref=refs[focus_kind],
        ),
        actor=_actor(),
    )

    assert result.status == "created"
    assert result.record_ref == f"session_focus_set:focus-{focus_kind}"


def test_focus_sidecar_does_not_rebind_session_claim(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import record_session_focus_set
    from brain.v5.workspace import get_session_binding

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    before_bytes = ws.session_path("s1").read_bytes()
    before = get_session_binding(ws, "s1")

    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-claim",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
        ),
        actor=_actor(),
    )

    after = get_session_binding(ws, "s1")
    assert after.active_claim == before.active_claim
    assert after.active_route == before.active_route
    assert ws.session_path("s1").read_bytes() == before_bytes
    persisted = (ws.registry_dir("session_focus_sets") / "focus-claim.md").read_text(
        encoding="utf-8"
    )
    assert "created_at:" in persisted


@pytest.mark.parametrize("program_review_status", ["reviewed", "approved"])
def test_reviewed_cross_topic_bridge_is_explicit_and_requires_revalidation(
    tmp_path,
    program_review_status,
):
    from brain.v5.lifecycle_models import (
        CrossTopicRelationRecord,
        ResearchProgramRecord,
        SessionFocusSetRecord,
    )
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_research_program,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, source_claim = _seed_workspace(tmp_path)
    record_research_program(
        ws,
        ResearchProgramRecord(
            program_id="program-1",
            title="Bounded method transfer",
            primary_topic_ids=["target"],
            supporting_topic_ids=["source"],
            scientific_boundary="Source trust never transfers to the target claim.",
            inclusion_rules=["reviewed bridges only"],
            review_status=program_review_status,
        ),
        actor=_actor(),
    )
    bridge = CrossTopicRelationRecord(
        relation_id="bridge-1",
        source_topic_id="source",
        target_topic_id="target",
        source_ref=f"claim:{source_claim.claim_id}",
        target_ref=f"claim:{target_claim.claim_id}",
        relation_kind="method_candidate",
        transfer_rationale="The algebraic technique may be reusable.",
        applicability_boundary="Only the method, never the source conclusion.",
        revalidation_requirements=["derive the target assumptions independently"],
        status="reviewed",
    )
    record_cross_topic_relation(ws, bridge, actor=_actor())
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-bridge",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-1"],
            program_id="program-1",
        ),
        actor=_actor(),
    )

    scope = resolve_session_scope(ws, "s1")

    assert scope.primary_topic_id == "target"
    assert scope.program_id == "program-1"
    assert scope.supporting_topic_ids == ("source",)
    assert "cross_topic_relation:bridge-1" in scope.supporting_refs
    assert f"claim:{source_claim.claim_id}" in scope.supporting_refs
    assert "cross_topic_relation:bridge-1" in scope.requires_revalidation_refs
    assert scope.claim_trust_transfer == "forbidden"


@pytest.mark.parametrize("review_status", ["pending_review", "rejected", "retired"])
def test_unreviewed_or_inactive_program_cannot_enter_session_scope(tmp_path, review_status):
    from brain.v5.lifecycle_models import ResearchProgramRecord, SessionFocusSetRecord
    from brain.v5.research_scope import (
        ScopeResolutionError,
        record_research_program,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    record_research_program(
        ws,
        ResearchProgramRecord(
            program_id=f"program-{review_status}",
            title="Program not eligible for active scope",
            primary_topic_ids=["target"],
            scientific_boundary="No program routing is active before review or after retirement.",
            review_status=review_status,
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id=f"focus-{review_status}",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            program_id=f"program-{review_status}",
        ),
        actor=_actor(),
    )

    with pytest.raises(ScopeResolutionError, match="not reviewed or approved"):
        resolve_session_scope(ws, "s1")


def test_unreviewed_bridge_is_excluded_and_only_discoverable_by_opt_in(tmp_path):
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, source_claim = _seed_workspace(tmp_path)
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-pending",
            source_topic_id="source",
            target_topic_id="target",
            source_ref=f"claim:{source_claim.claim_id}",
            target_ref=f"claim:{target_claim.claim_id}",
            relation_kind="analogy",
            transfer_rationale="Potentially useful analogy.",
            applicability_boundary="Not reviewed for target use.",
            revalidation_requirements=["review the bridge", "rederive on the target"],
            status="pending_review",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-pending",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-pending"],
        ),
        actor=_actor(),
    )

    hidden = resolve_session_scope(ws, "s1")
    discovered = resolve_session_scope(ws, "s1", include_discovery=True)

    assert "cross_topic_relation:bridge-pending" in hidden.excluded_refs
    assert hidden.discovery_refs == ()
    assert "cross_topic_relation:bridge-pending" in discovered.discovery_refs
    assert f"claim:{source_claim.claim_id}" not in hidden.supporting_refs


def test_scope_reports_stale_focus_ref_without_calling_it_absent_from_history(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import record_session_focus_set, resolve_session_scope

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    focus_ref = f"claim:{target_claim.claim_id}"
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-stale",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=focus_ref,
        ),
        actor=_actor(),
    )
    (ws.registry_dir("claims") / f"{target_claim.claim_id}.md").unlink()

    scope = resolve_session_scope(ws, "s1")

    assert focus_ref in scope.unresolved_refs
    assert focus_ref not in scope.primary_refs


def test_scope_writers_reject_unknown_refs_wrong_primary_and_unsafe_bridges(tmp_path):
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.research_scope import record_cross_topic_relation, record_session_focus_set

    ws, target_claim, source_claim = _seed_workspace(tmp_path)
    focus = SessionFocusSetRecord(
        focus_set_id="focus-invalid",
        session_id="s1",
        primary_topic_id="target",
        focus_kind="claim",
        focus_ref=f"claim:{target_claim.claim_id}",
    )
    with pytest.raises(ValueError, match="unsupported typed ref"):
        record_session_focus_set(
            ws,
            replace(focus, supporting_refs=["mystery:record"]),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="session topic"):
        record_session_focus_set(
            ws,
            replace(focus, focus_set_id="focus-wrong-topic", primary_topic_id="source"),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="ISO-8601"):
        record_session_focus_set(
            ws,
            replace(focus, focus_set_id="focus-bad-time", created_at="sometime"),
            actor=_actor(),
        )

    bridge = CrossTopicRelationRecord(
        relation_id="bridge-invalid",
        source_topic_id="source",
        target_topic_id="target",
        source_ref=f"claim:{source_claim.claim_id}",
        target_ref=f"claim:{target_claim.claim_id}",
        relation_kind="method_candidate",
        transfer_rationale="Candidate transfer.",
        applicability_boundary="Target validation required.",
        revalidation_requirements=["target validation"],
    )
    with pytest.raises(ValueError, match="different topics"):
        record_cross_topic_relation(
            ws,
            replace(bridge, source_topic_id="target", source_ref=f"claim:{target_claim.claim_id}"),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="revalidation"):
        record_cross_topic_relation(
            ws,
            replace(bridge, revalidation_requirements=[]),
            actor=_actor(),
        )
    with pytest.raises(ValueError, match="claim_trust_transfer"):
        replace(bridge, claim_trust_transfer="allowed")


def test_pending_target_bridge_is_writeable_but_never_enters_supporting_scope(tmp_path):
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, source_claim = _seed_workspace(tmp_path)
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-future",
            source_topic_id="source",
            target_topic_id="target",
            source_ref=f"claim:{source_claim.claim_id}",
            target_ref="claim:future-target-claim",
            relation_kind="pending_target",
            transfer_rationale="Preserve the source handle until the target claim exists.",
            applicability_boundary="Excluded until a target record is created and reviewed.",
            revalidation_requirements=["create and validate the target claim"],
            status="pending_target",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-future",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-future"],
        ),
        actor=_actor(),
    )

    scope = resolve_session_scope(ws, "s1", include_discovery=True)

    assert "cross_topic_relation:bridge-future" in scope.excluded_refs
    assert "claim:future-target-claim" in scope.unresolved_refs
    assert f"claim:{source_claim.claim_id}" not in scope.supporting_refs


def test_scope_lookup_isolates_focus_sets_by_session_in_the_index(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import record_session_focus_set, resolve_session_scope
    from brain.v5.workspace import bind_session

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    bind_session(
        ws,
        "s2",
        topic_id="target",
        context_id="theory",
        active_claim=target_claim.claim_id,
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-s1",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            created_at="2026-01-01T00:00:00Z",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-s2-newer",
            session_id="s2",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            created_at="2099-01-01T00:00:00Z",
        ),
        actor=_actor(),
    )

    scope = resolve_session_scope(ws, "s1")

    assert scope.focus_set_ref == "session_focus_set:focus-s1"
    assert "session_focus_set:focus-s2-newer" not in scope.primary_refs


def test_direct_cross_topic_record_cannot_bypass_a_typed_bridge(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import record_session_focus_set, resolve_session_scope

    ws, target_claim, source_claim = _seed_workspace(tmp_path)
    source_ref = f"claim:{source_claim.claim_id}"
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-direct-source",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            supporting_refs=[source_ref],
        ),
        actor=_actor(),
    )

    hidden = resolve_session_scope(ws, "s1")
    discovered = resolve_session_scope(ws, "s1", include_discovery=True)

    assert source_ref in hidden.excluded_refs
    assert source_ref not in hidden.supporting_refs
    assert source_ref in discovered.discovery_refs


def test_equal_timestamp_active_focus_sets_fail_closed_as_ambiguous(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import (
        ScopeResolutionError,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    for suffix in ("a", "b"):
        record_session_focus_set(
            ws,
            SessionFocusSetRecord(
                focus_set_id=f"focus-{suffix}",
                session_id="s1",
                primary_topic_id="target",
                focus_kind="claim",
                focus_ref=f"claim:{target_claim.claim_id}",
                created_at="2026-01-01T00:00:00Z",
            ),
            actor=_actor(),
        )

    with pytest.raises(ScopeResolutionError, match="ambiguous"):
        resolve_session_scope(ws, "s1")


def test_malformed_focus_family_cannot_be_misreported_as_no_focus(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import (
        ScopeResolutionError,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    result = record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-corrupt",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
        ),
        actor=_actor(),
    )
    path = ws.registry_dir("session_focus_sets") / "focus-corrupt.md"
    path.write_text("---\nkind: session_focus_set\n---\n", encoding="utf-8")

    with pytest.raises(ScopeResolutionError, match="stale or malformed"):
        resolve_session_scope(ws, "s1")


def test_explicit_focus_selection_rejects_closed_or_superseded_scope(tmp_path):
    from brain.v5.lifecycle_models import SessionFocusSetRecord
    from brain.v5.research_scope import (
        ScopeResolutionError,
        record_session_focus_set,
        resolve_session_scope,
    )

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-closed",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target_claim.claim_id}",
            scope_status="closed",
        ),
        actor=_actor(),
    )

    with pytest.raises(ScopeResolutionError, match="not active"):
        resolve_session_scope(
            ws,
            "s1",
            focus_set_ref="session_focus_set:focus-closed",
        )


def test_bridge_endpoint_must_establish_topic_ownership(tmp_path):
    from brain.v5.lifecycle_models import CrossTopicRelationRecord
    from brain.v5.research_scope import record_cross_topic_relation

    ws, target_claim, _source_claim = _seed_workspace(tmp_path)
    refs = _seed_focus_targets(ws, target_claim)
    bridge = CrossTopicRelationRecord(
        relation_id="bridge-topicless-source",
        source_topic_id="source",
        target_topic_id="target",
        source_ref=refs["code_change"],
        target_ref=f"claim:{target_claim.claim_id}",
        relation_kind="code_candidate",
        transfer_rationale="A code state alone does not establish source-topic ownership.",
        applicability_boundary="Require a topic-local execution or source record.",
        revalidation_requirements=["record a topic-local source anchor"],
    )

    with pytest.raises(ValueError, match="topic ownership"):
        record_cross_topic_relation(ws, bridge, actor=_actor())
