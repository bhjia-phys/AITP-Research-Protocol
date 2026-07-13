from __future__ import annotations

from dataclasses import replace

import pytest


def _actor():
    from brain.v5.record_envelope import RecordActor

    return RecordActor(actor_type="model", actor_id="disclosure-test", host="pytest")


def _seed_scoped_workspace(tmp_path):
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import record_cross_topic_relation, record_session_focus_set
    from brain.v5.workspace import bind_session, create_claim, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_topic(ws, "target", context_id="theory", title="Target quantum gravity")
    create_topic(ws, "source", context_id="theory", title="Source algebra method")
    target = create_claim(
        ws,
        topic_id="target",
        statement="TARGET_SCIENTIFIC_STATEMENT needs an independent derivation.",
        evidence_profile="formal_theory",
        confidence_state="hypothesis",
        active_uncertainty="No target-side proof yet.",
    )
    source = create_claim(
        ws,
        topic_id="source",
        statement="REVIEWED_SOURCE_METHOD holds under source assumptions.",
        evidence_profile="formal_theory",
        confidence_state="validated",
        active_uncertainty="Its target applicability is open.",
    )
    unrelated = create_claim(
        ws,
        topic_id="source",
        statement="UNRELATED_SOURCE_RESULT must never leak through the program lane.",
        evidence_profile="formal_theory",
        confidence_state="validated",
        active_uncertainty="Unrelated to the target session.",
    )
    bind_session(ws, "s1", topic_id="target", context_id="theory", active_claim=target.claim_id)
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-reviewed",
            source_topic_id="source",
            target_topic_id="target",
            source_ref=f"claim:{source.claim_id}",
            target_ref=f"claim:{target.claim_id}",
            relation_kind="method_candidate",
            transfer_rationale="Reuse only the formal manipulation.",
            applicability_boundary="The target claim keeps independent trust.",
            revalidation_requirements=["rederive under target assumptions"],
            status="reviewed",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-1",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-reviewed"],
        ),
        actor=_actor(),
    )
    build_query_index(ws)
    return ws, target, source, unrelated


def test_context_request_rejects_unknown_disclosure_level():
    from brain.v5.context_compiler import ContextRequest

    with pytest.raises(ValueError, match="disclosure_level"):
        ContextRequest(session_id="s1", disclosure_level="everything")


def test_route_hint_contains_handles_but_no_scientific_content(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle

    ws, target, _source, _unrelated = _seed_scoped_workspace(tmp_path)
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            objective_text="SECRET_USER_PHYSICS_PROMPT",
            disclosure_level="route_hint",
        ),
    )

    assert bundle.disclosure_level == "route_hint"
    assert bundle.candidate_summaries == ()
    assert bundle.current_boundary["claim_id"] == ""
    assert f"claim:{target.claim_id}" not in bundle.markdown
    assert "TARGET_SCIENTIFIC_STATEMENT" not in bundle.markdown
    assert "SECRET_USER_PHYSICS_PROMPT" not in bundle.markdown
    assert bundle.next_level_handles["next_disclosure_level"] == "startup_orientation"
    assert validate_context_bundle(bundle) == ()


def test_normal_context_includes_only_explicit_reviewed_cross_topic_support(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context

    ws, target, source, unrelated = _seed_scoped_workspace(tmp_path)
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            objective_text="continue the target derivation",
            disclosure_level="normal_research",
            candidate_limit=20,
        ),
    )

    refs = set(bundle.record_refs)
    assert f"claim:{target.claim_id}" in refs
    assert "cross_topic_relation:bridge-reviewed" in refs
    assert f"claim:{source.claim_id}" in refs
    assert f"claim:{unrelated.claim_id}" not in refs
    assert "cross_topic_relation:bridge-reviewed" in bundle.scope["requires_revalidation_refs"]
    assert bundle.scope["claim_trust_transfer"] == "forbidden"


def test_exact_disclosure_returns_only_requested_canonical_refs(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context

    ws, _target, source, unrelated = _seed_scoped_workspace(tmp_path)
    requested = (f"claim:{source.claim_id}", f"claim:{unrelated.claim_id}")
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level="exact_expansion",
            exact_refs=requested,
            record_limit=1,
        ),
    )

    assert bundle.record_refs == requested[:1]
    assert bundle.expansion["requested_refs"] == list(requested)
    assert bundle.expansion["next_offset"] == 1
    assert bundle.expansion["canonical_record_payloads_in_expansion"] is True
    assert bundle.expansion["items"][0]["record_ref"] == requested[0]
    assert bundle.expansion["items"][0]["record"]["claim_id"] == source.claim_id
    assert bundle.expansion["checked_requested_refs"] == [requested[0]]
    assert bundle.expansion["unchecked_requested_refs"] == [requested[1]]
    assert bundle.coverage["exhaustive"] is False
    assert bundle.coverage["can_claim_no_result"] is False
    assert bundle.total_candidates == len(requested)
    assert bundle.not_found_refs == ()
    assert bundle.next_level_handles["next_disclosure_level"] == ""


@pytest.mark.parametrize("level", ["startup_orientation", "normal_research"])
def test_non_exact_context_blocks_unbridged_cross_topic_exact_refs(tmp_path, level):
    from brain.v5.context_compiler import ContextRequest, compile_research_context

    ws, _target, _source, unrelated = _seed_scoped_workspace(tmp_path)
    unrelated_ref = f"claim:{unrelated.claim_id}"
    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level=level,
            exact_refs=(unrelated_ref,),
        ),
    )

    assert unrelated_ref not in bundle.record_refs
    assert unrelated_ref in bundle.scope["blocked_explicit_refs"]
    assert unrelated_ref not in bundle.not_found_refs
    assert bundle.scope["claim_trust_transfer"] == "forbidden"


def test_scope_exclusion_is_not_reported_as_not_found(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import record_cross_topic_relation, record_session_focus_set

    ws, target, _source, unrelated = _seed_scoped_workspace(tmp_path)
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-pending",
            source_topic_id="source",
            target_topic_id="target",
            source_ref=f"claim:{unrelated.claim_id}",
            target_ref=f"claim:{target.claim_id}",
            relation_kind="analogy",
            transfer_rationale="Discovery only.",
            applicability_boundary="Not reviewed.",
            revalidation_requirements=["review and rederive"],
            status="pending_review",
        ),
        actor=_actor(),
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-2",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-pending"],
            created_at="2099-01-01T00:00:00Z",
        ),
        actor=_actor(),
    )
    build_query_index(ws)

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level="normal_research",
            exact_refs=("claim:missing",),
            include_cross_topic_discovery=True,
        ),
    )

    assert "claim:missing" in bundle.not_found_refs
    assert "cross_topic_relation:bridge-pending" in bundle.scope["excluded_refs"]
    assert "cross_topic_relation:bridge-pending" in bundle.scope["discovery_refs"]
    assert "cross_topic_relation:bridge-pending" not in bundle.not_found_refs
    assert f"claim:{unrelated.claim_id}" not in bundle.record_refs


@pytest.mark.parametrize(
    ("level", "next_level"),
    [
        ("route_hint", "startup_orientation"),
        ("startup_orientation", "normal_research"),
        ("normal_research", "exact_expansion"),
        ("exact_expansion", ""),
    ],
)
def test_disclosure_ladder_has_explicit_next_level_handles(tmp_path, level, next_level):
    from brain.v5.context_compiler import ContextRequest, compile_research_context

    ws, target, _source, _unrelated = _seed_scoped_workspace(tmp_path)
    exact_refs = (f"claim:{target.claim_id}",) if level == "exact_expansion" else ()
    bundle = compile_research_context(
        ws,
        ContextRequest(session_id="s1", disclosure_level=level, exact_refs=exact_refs),
    )

    assert bundle.next_level_handles["next_disclosure_level"] == next_level
    assert "checked_refs" in bundle.scope
    assert "unchecked_refs" in bundle.scope


def test_context_contract_rejects_scope_trust_or_disclosure_leakage(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle

    ws, _target, _source, _unrelated = _seed_scoped_workspace(tmp_path)
    bundle = compile_research_context(
        ws,
        ContextRequest(session_id="s1", disclosure_level="normal_research"),
    )

    unsafe_scope = dict(bundle.scope)
    unsafe_scope["claim_trust_transfer"] = "allowed"
    assert "scope claim_trust_transfer must be forbidden" in validate_context_bundle(
        replace(bundle, scope=unsafe_scope)
    )

    excluded = list(bundle.scope["excluded_refs"])
    excluded.append("claim:excluded")
    overlapping_scope = dict(bundle.scope)
    overlapping_scope["excluded_refs"] = excluded
    assert "scope-excluded refs cannot be reported as not_found" in validate_context_bundle(
        replace(
            bundle,
            scope=overlapping_scope,
            not_found_refs=("claim:excluded",),
        )
    )

    exact = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level="exact_expansion",
            exact_refs=(bundle.record_refs[0],),
        ),
    )
    assert "exact expansion returned an unrequested ref" in validate_context_bundle(
        replace(exact, record_refs=("claim:not-requested",))
    )


def test_normal_context_reserves_bounded_space_for_reviewed_support(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws, _target, _source, _unrelated = _seed_scoped_workspace(tmp_path)
    for index in range(8):
        create_claim(
            ws,
            topic_id="target",
            statement=f"Primary candidate {index} remains open.",
            evidence_profile="formal_theory",
            confidence_state="candidate",
            active_uncertainty="Synthetic scope-capacity fixture.",
        )
    build_query_index(ws)

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level="normal_research",
            record_limit=4,
            candidate_limit=4,
        ),
    )

    assert len(bundle.record_refs) <= 4
    assert "cross_topic_relation:bridge-reviewed" in bundle.record_refs
    assert bundle.not_shown_count > 0


def test_normal_context_accounts_for_paginated_reviewed_support(tmp_path):
    from brain.v5.context_compiler import ContextRequest, compile_research_context
    from brain.v5.context_compiler_contracts import validate_context_bundle
    from brain.v5.lifecycle_models import CrossTopicRelationRecord, SessionFocusSetRecord
    from brain.v5.query_index import build_query_index
    from brain.v5.research_scope import record_cross_topic_relation, record_session_focus_set
    from brain.v5.workspace import create_claim

    ws, target, _source, _unrelated = _seed_scoped_workspace(tmp_path)
    supporting_refs = ["cross_topic_relation:bridge-reviewed"]
    for index in range(5):
        source = create_claim(
            ws,
            topic_id="source",
            statement=f"Reviewed source method {index} has a distinct applicability boundary.",
            evidence_profile="formal_theory",
            confidence_state="validated",
            active_uncertainty="Target-side revalidation remains required.",
        )
        relation_id = f"bridge-reviewed-{index}"
        record_cross_topic_relation(
            ws,
            CrossTopicRelationRecord(
                relation_id=relation_id,
                source_topic_id="source",
                target_topic_id="target",
                source_ref=f"claim:{source.claim_id}",
                target_ref=f"claim:{target.claim_id}",
                relation_kind="method_candidate",
                transfer_rationale="Expose one reviewed source method without transferring trust.",
                applicability_boundary="The target topic must rederive the result independently.",
                revalidation_requirements=["rederive under target assumptions"],
                status="reviewed",
            ),
            actor=_actor(),
        )
        supporting_refs.append(f"cross_topic_relation:{relation_id}")
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-many-supports",
            session_id="s1",
            primary_topic_id="target",
            focus_kind="claim",
            focus_ref=f"claim:{target.claim_id}",
            supporting_refs=supporting_refs,
            created_at="2099-01-01T00:00:00+00:00",
        ),
        actor=_actor(),
    )
    build_query_index(ws)

    bundle = compile_research_context(
        ws,
        ContextRequest(
            session_id="s1",
            disclosure_level="normal_research",
            record_limit=4,
            candidate_limit=4,
        ),
    )

    omitted_support = set(bundle.scope["supporting_refs"]) - set(bundle.record_refs)
    assert omitted_support
    assert bundle.not_shown_count >= len(omitted_support)
    assert omitted_support <= set(bundle.next_level_handles["exact_expansion_refs"])
    assert bundle.next_level_handles["exact_expansion_refs_truncated"] is False
    assert validate_context_bundle(bundle) == ()
