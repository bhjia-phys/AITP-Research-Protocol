from __future__ import annotations

import importlib.util
import importlib
from dataclasses import FrozenInstanceError
from dataclasses import replace
import json

import pytest


def test_host_route_contract_module_exists():
    assert importlib.util.find_spec("brain.v5.host_route_contracts") is not None


def test_route_contracts_expose_versioned_statuses():
    contracts = importlib.import_module("brain.v5.host_route_contracts")

    assert contracts.HOST_ROUTE_REQUEST_SCHEMA_VERSION == "aitp.host_route_request.v1"
    assert contracts.HOST_ROUTE_DECISION_SCHEMA_VERSION == "aitp.host_route_decision.v1"
    assert contracts.HOST_ROUTE_STATUSES == frozenset(
        {
            "outside_aitp",
            "selected",
            "ambiguous",
            "workspace_recovery",
            "conflict",
            "coverage_blocked",
        }
    )


def test_host_route_request_normalization_is_bounded_immutable_and_deterministic():
    from brain.v5.host_route_contracts import (
        HOST_ROUTE_REQUEST_SCHEMA_VERSION,
        HostRouteRequest,
        host_route_request_fingerprint,
        normalize_host_route_request,
    )

    request = HostRouteRequest(
        request_summary="  Continue the LibRPA screening run  ",
        host=" Codex ",
        host_session_id=" host-turn-1 ",
        project_root=" F:/AI_Workspace/Theoretical-Physics ",
        current_path=" research/librpa/run.py ",
        repo_id=" theoretical-physics ",
        branch=" main ",
        visible_files=("research/librpa/run.py", "README.md", "README.md"),
        explicit_topic_ids=("topic-b", "topic-a", "topic-a"),
        explicit_session_ids=("session-b", "session-a"),
        exact_refs=("claim:claim-b", "claim:claim-a", "claim:claim-a"),
        semantic_assessment={"research_relevant": True, "confidence": 0.9},
    )

    normalized = normalize_host_route_request(request)

    assert normalized.schema_version == HOST_ROUTE_REQUEST_SCHEMA_VERSION
    assert normalized.request_summary == "Continue the LibRPA screening run"
    assert normalized.host == "codex"
    assert normalized.host_session_id == "host-turn-1"
    assert normalized.visible_files == ("README.md", "research/librpa/run.py")
    assert normalized.explicit_topic_ids == ("topic-a", "topic-b")
    assert normalized.explicit_session_ids == ("session-a", "session-b")
    assert normalized.exact_refs == ("claim:claim-a", "claim:claim-b")
    with pytest.raises(TypeError):
        normalized.semantic_assessment["research_relevant"] = False
    with pytest.raises(FrozenInstanceError):
        normalized.host = "other"

    reordered = HostRouteRequest(
        request_summary="Continue the LibRPA screening run",
        host="codex",
        host_session_id="host-turn-1",
        project_root="F:/AI_Workspace/Theoretical-Physics",
        current_path="research/librpa/run.py",
        repo_id="theoretical-physics",
        branch="main",
        visible_files=("README.md", "research/librpa/run.py"),
        explicit_topic_ids=("topic-a", "topic-b"),
        explicit_session_ids=("session-a", "session-b"),
        exact_refs=("claim:claim-a", "claim:claim-b"),
        semantic_assessment={"confidence": 0.9, "research_relevant": True},
    )
    assert host_route_request_fingerprint(normalized) == host_route_request_fingerprint(
        reordered
    )


def test_host_route_request_rejects_hidden_pin_and_unbounded_transcript():
    from brain.v5.host_route_contracts import HostRouteRequest, normalize_host_route_request

    with pytest.raises(ValueError, match="dynamic routing cannot include a pinned session"):
        normalize_host_route_request(
            HostRouteRequest(
                request_summary="Continue the calculation",
                routing_mode="dynamic",
                pinned_session_id="session-a",
            )
        )
    with pytest.raises(TypeError):
        HostRouteRequest(
            request_summary="Continue the calculation",
            transcript="full conversation",
        )


def _strong_route_coverage(**overrides):
    from brain.v5.host_route_contracts import HostRouteCoverage

    values = {
        "checked_families": ("sessions", "topics"),
        "not_shown_families": (),
        "not_checked_families": (),
        "malformed_count": 0,
        "read_errors": (),
        "truncated": False,
        "index_status": "fresh",
        "index_generation": 7,
        "canonical_watermark": "a" * 64,
        "scope_fresh": True,
        "strong_selection_eligible": True,
    }
    values.update(overrides)
    return HostRouteCoverage(**values)


def _route_candidate(topic_id="topic-a", session_id="session-a", **overrides):
    from brain.v5.host_route_contracts import HostRouteCandidate

    values = {
        "topic_id": topic_id,
        "session_id": session_id,
        "score": 1000,
        "evidence_tier": "explicit",
        "component_scores": {"explicit_session": 1000},
        "reason_codes": ("explicit_session",),
        "exact_refs": (f"topic:{topic_id}", f"session:{session_id}"),
    }
    values.update(overrides)
    return HostRouteCandidate(**values)


def test_selected_route_decision_is_bounded_exact_and_trust_neutral():
    from brain.v5.host_route_contracts import (
        HOST_ROUTE_DECISION_SCHEMA_VERSION,
        HostRouteDecision,
        route_decision_payload,
    )

    candidate = _route_candidate()
    decision = HostRouteDecision(
        status="selected",
        request_fingerprint="b" * 64,
        candidates=(candidate,),
        coverage=_strong_route_coverage(),
        selected_topic_id="topic-a",
        selected_session_id="session-a",
        reason_codes=("unique_explicit_session",),
        recommended_next_operation="enter_selected_session",
    )

    payload = route_decision_payload(decision)

    assert payload["schema_version"] == HOST_ROUTE_DECISION_SCHEMA_VERSION
    assert payload["status"] == "selected"
    assert payload["selected_topic_id"] == "topic-a"
    assert payload["selected_session_id"] == "session-a"
    assert len(payload["candidates"]) == 1
    assert payload["coverage"]["strong_selection_eligible"] is True
    assert payload["orientation_only"] is True
    assert payload["summary_inputs_trusted"] is False
    assert payload["canonical_write_allowed"] is False
    assert payload["can_update_kernel_state"] is False
    assert payload["can_update_claim_trust"] is False
    assert payload["trust_effect"] == "none"
    assert "request_summary" not in payload

    with pytest.raises(ValueError, match="canonical_write_allowed must be false"):
        replace(decision, canonical_write_allowed=True)


def test_selected_route_requires_strong_coverage_and_matching_candidate():
    from brain.v5.host_route_contracts import HostRouteDecision

    candidate = _route_candidate()
    blocked = _strong_route_coverage(
        read_errors=("sessions index read failed",),
        strong_selection_eligible=False,
    )
    with pytest.raises(ValueError, match="selected routes require strong coverage"):
        HostRouteDecision(
            status="selected",
            request_fingerprint="c" * 64,
            candidates=(candidate,),
            coverage=blocked,
            selected_topic_id="topic-a",
            selected_session_id="session-a",
            reason_codes=("candidate_not_verified",),
            recommended_next_operation="repair_coverage",
        )

    with pytest.raises(ValueError, match="selected route must match a primary candidate"):
        HostRouteDecision(
            status="selected",
            request_fingerprint="d" * 64,
            candidates=(candidate,),
            coverage=_strong_route_coverage(),
            selected_topic_id="topic-b",
            selected_session_id="session-b",
            reason_codes=("candidate_mismatch",),
            recommended_next_operation="enter_selected_session",
        )


def test_route_decision_preserves_ambiguity_and_limits_candidate_cards():
    from brain.v5.host_route_contracts import HostRouteDecision

    candidates = tuple(
        _route_candidate(f"topic-{index}", f"session-{index}", score=1000 - index)
        for index in range(4)
    )
    with pytest.raises(ValueError, match="at most 3 candidates"):
        HostRouteDecision(
            status="ambiguous",
            request_fingerprint="e" * 64,
            candidates=candidates,
            coverage=_strong_route_coverage(),
            reason_codes=("multiple_primary_candidates",),
            recommended_next_operation="choose_candidate",
        )

    ambiguous = HostRouteDecision(
        status="ambiguous",
        request_fingerprint="f" * 64,
        candidates=candidates[:2],
        coverage=_strong_route_coverage(),
        reason_codes=("multiple_primary_candidates",),
        recommended_next_operation="choose_candidate",
    )
    assert ambiguous.selected_topic_id == ""
    assert ambiguous.selected_session_id == ""
    assert ambiguous.canonical_write_allowed is False


def test_supporting_route_candidate_requires_target_revalidation():
    with pytest.raises(ValueError, match="supporting candidates require target revalidation"):
        _route_candidate(
            "topic-b",
            "session-b",
            evidence_tier="supporting_scope",
            supporting_only=True,
            requires_target_revalidation=False,
        )


def test_route_decision_payload_round_trip_rejects_authority_tampering():
    from brain.v5.host_route_contracts import (
        HostRouteDecision,
        host_route_decision_from_payload,
        route_decision_payload,
        validate_host_route_decision_payload,
    )

    decision = HostRouteDecision(
        status="selected",
        request_fingerprint="1" * 64,
        candidates=(_route_candidate(),),
        coverage=_strong_route_coverage(),
        selected_topic_id="topic-a",
        selected_session_id="session-a",
        reason_codes=("unique_explicit_session",),
        recommended_next_operation="enter_selected_session",
    )
    payload = json.loads(json.dumps(route_decision_payload(decision)))

    assert validate_host_route_decision_payload(payload) == ()
    assert host_route_decision_from_payload(payload) == decision

    payload["canonical_write_allowed"] = True
    issues = validate_host_route_decision_payload(payload)
    assert any("canonical_write_allowed must be false" in issue for issue in issues)
    with pytest.raises(ValueError, match="canonical_write_allowed must be false"):
        host_route_decision_from_payload(payload)


def _seed_two_topic_route_workspace(tmp_path):
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import bind_session, create_context, create_topic, init_workspace

    ws = init_workspace(tmp_path)
    create_context(ws, "computational-materials", title="Computational Materials")
    create_context(ws, "formal-theory", title="Formal Theory")
    create_topic(
        ws,
        "librpa-screening",
        context_id="computational-materials",
        title="LibRPA dielectric screening and HPC convergence",
    )
    create_topic(
        ws,
        "quantum-gravity-notes",
        context_id="formal-theory",
        title="Quantum gravity von Neumann algebra notes",
    )
    bind_session(
        ws,
        "session-librpa",
        topic_id="librpa-screening",
        context_id="computational-materials",
        runtime="codex",
    )
    bind_session(
        ws,
        "session-qg",
        topic_id="quantum-gravity-notes",
        context_id="formal-theory",
        runtime="codex",
    )
    build_query_index(ws)
    return ws


def test_resolver_selects_an_explicit_session_after_exact_topic_verification(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.query_index import current_canonical_watermark
    from brain.v5.research_retrieval import QuerySnapshotSession

    ws = _seed_two_topic_route_workspace(tmp_path)
    watermark_before = current_canonical_watermark(ws)
    query_session = QuerySnapshotSession()

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the LibRPA screening convergence run",
            host="codex",
            host_session_id="host-session-1",
            explicit_session_ids=("session-librpa",),
            semantic_assessment={
                "task_kind": "topic_continuation",
                "should_use_aitp": "required",
                "confidence": "high",
            },
        ),
        query_session=query_session,
    )

    from brain.v5.host_route_contracts import route_decision_payload

    assert decision.status == "selected", json.dumps(
        route_decision_payload(decision), indent=2
    )
    assert decision.selected_topic_id == "librpa-screening"
    assert decision.selected_session_id == "session-librpa"
    assert decision.candidates[0].evidence_tier == "explicit"
    assert decision.candidates[0].exact_refs == (
        "session:session-librpa",
        "topic:librpa-screening",
    )
    assert decision.coverage.strong_selection_eligible is True
    assert query_session.snapshot is not None
    assert current_canonical_watermark(ws) == watermark_before


def test_resolver_skips_index_for_explicit_generic_textbook_request(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.research_retrieval import QuerySnapshotSession

    ws = _seed_two_topic_route_workspace(tmp_path)
    query_session = QuerySnapshotSession()

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="What is the Fourier transform of a Gaussian?",
            semantic_assessment={
                "task_kind": "generic_question",
                "is_generic_textbook_question": True,
                "should_use_aitp": "not_required",
                "confidence": "high",
            },
        ),
        query_session=query_session,
    )

    assert decision.status == "outside_aitp"
    assert decision.candidates == ()
    assert decision.recommended_next_operation == "none"
    assert query_session.snapshot is None
    assert decision.canonical_write_allowed is False


@pytest.mark.parametrize(
    ("summary", "expected_topic", "expected_session"),
    (
        (
            "Continue the LibRPA dielectric screening HPC convergence",
            "librpa-screening",
            "session-librpa",
        ),
        (
            "Continue the quantum gravity von Neumann algebra notes",
            "quantum-gravity-notes",
            "session-qg",
        ),
    ),
)
def test_resolver_selects_different_sessions_from_indexed_topic_intent(
    tmp_path,
    summary,
    expected_topic,
    expected_session,
):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.host_route_payloads import route_decision_payload

    ws = _seed_two_topic_route_workspace(tmp_path)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary=summary,
            host="codex",
            host_session_id=f"host-{expected_session}",
            semantic_assessment={
                "task_kind": "topic_continuation",
                "needs_prior_research_state": True,
                "confidence": "high",
            },
        ),
    )

    assert decision.status == "selected", json.dumps(
        route_decision_payload(decision), indent=2
    )
    assert decision.selected_topic_id == expected_topic
    assert decision.selected_session_id == expected_session
    assert decision.candidates[0].evidence_tier == "indexed_text"
    assert decision.coverage.strong_selection_eligible is True


def test_resolver_preserves_equal_indexed_topics_as_ambiguous(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.host_route_payloads import route_decision_payload
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    for topic_id in ("librpa-screening", "quantum-gravity-notes"):
        create_claim(
            ws,
            topic_id=topic_id,
            statement="Shared frontier consistency question",
            evidence_profile="formal_theory",
            confidence_state="candidate",
            active_uncertainty="The shared frontier comparison remains open.",
        )
    build_query_index(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the shared frontier consistency question",
            semantic_assessment={
                "task_kind": "topic_continuation",
                "needs_prior_research_state": True,
                "confidence": "high",
            },
        ),
    )

    assert decision.status == "ambiguous", json.dumps(
        route_decision_payload(decision), indent=2
    )
    assert decision.selected_topic_id == ""
    assert decision.selected_session_id == ""
    assert {
        (candidate.topic_id, candidate.session_id) for candidate in decision.candidates
    } == {
        ("librpa-screening", "session-librpa"),
        ("quantum-gravity-notes", "session-qg"),
    }
    assert decision.canonical_write_allowed is False


def test_resolver_accepts_exact_session_and_topic_refs(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the exact bound research session",
            exact_refs=(
                "session:session-librpa",
                "topic:librpa-screening",
            ),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "selected"
    assert decision.selected_topic_id == "librpa-screening"
    assert decision.selected_session_id == "session-librpa"
    assert decision.candidates[0].evidence_tier == "explicit"


@pytest.mark.parametrize(
    ("request_fields", "expected_reason"),
    (
        (
            {"explicit_session_ids": ("session-librpa", "session-qg")},
            "multiple_explicit_sessions_require_choice",
        ),
        (
            {
                "explicit_session_ids": ("session-librpa",),
                "pinned_session_id": "session-qg",
                "routing_mode": "pinned",
            },
            "pinned_session_conflicts_with_explicit_session",
        ),
        (
            {
                "exact_refs": (
                    "session:session-librpa",
                    "session:session-qg",
                )
            },
            "multiple_explicit_sessions_require_choice",
        ),
    ),
)
def test_resolver_reports_explicit_route_conflicts_without_loading_index(
    tmp_path,
    request_fields,
    expected_reason,
):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.research_retrieval import QuerySnapshotSession

    ws = _seed_two_topic_route_workspace(tmp_path)
    query_session = QuerySnapshotSession()
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue an explicitly bound research session",
            semantic_assessment={"should_use_aitp": "required"},
            **request_fields,
        ),
        query_session=query_session,
    )

    assert decision.status == "conflict"
    assert expected_reason in decision.reason_codes
    assert query_session.snapshot is None


def test_resolver_rejects_explicit_topic_session_mismatch(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the requested formal theory topic",
            explicit_session_ids=("session-librpa",),
            explicit_topic_ids=("quantum-gravity-notes",),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "conflict"
    assert "explicit_topic_conflicts_with_session_binding" in decision.reason_codes


def test_resolver_blocks_a_missing_explicit_session(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the missing research session",
            explicit_session_ids=("session-missing",),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "coverage_blocked"
    assert decision.coverage.strong_selection_eligible is False
    assert "explicit_session_not_found" in decision.reason_codes


def test_resolver_blocks_indexed_selection_when_index_is_stale(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    create_claim(
        ws,
        topic_id="librpa-screening",
        statement="LibRPA dielectric screening convergence changed after indexing",
        evidence_profile="numerical",
        confidence_state="candidate",
        active_uncertainty="The derived index has not been rebuilt.",
    )

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the LibRPA dielectric screening convergence",
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "coverage_blocked"
    assert decision.coverage.index_status == "stale"
    assert decision.coverage.scope_fresh is False


def test_resolver_blocks_malformed_in_scope_route_family(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.query_index import build_query_index

    ws = _seed_two_topic_route_workspace(tmp_path)
    malformed = ws.registry_dir("routes") / "malformed-route.md"
    malformed.write_text("---\n: invalid yaml\n---\n", encoding="utf-8")
    build_query_index(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the LibRPA dielectric screening convergence",
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "coverage_blocked"
    assert decision.coverage.malformed_count > 0


def test_resolver_blocks_truncated_discovery(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    for index in range(50):
        create_claim(
            ws,
            topic_id="librpa-screening",
            statement=f"LibRPA dielectric screening convergence sample {index}",
            evidence_profile="numerical",
            confidence_state="candidate",
            active_uncertainty="The route fixture intentionally exceeds its bound.",
        )
    build_query_index(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the LibRPA dielectric screening convergence",
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "coverage_blocked"
    assert decision.coverage.truncated is True


def test_resolver_uses_workspace_recovery_when_no_indexed_candidate_exists(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the xylophonic superspace investigation",
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "workspace_recovery"
    assert decision.candidates == ()
    assert decision.coverage.strong_selection_eligible is True


def test_resolver_exposes_reviewed_cross_topic_scope_as_supporting_only(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.lifecycle_models import (
        CrossTopicRelationRecord,
        ResearchProgramRecord,
        SessionFocusSetRecord,
    )
    from brain.v5.query_index import build_query_index, current_canonical_watermark
    from brain.v5.record_envelope import RecordActor
    from brain.v5.research_scope import (
        record_cross_topic_relation,
        record_research_program,
        record_session_focus_set,
    )
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    actor = RecordActor(actor_type="model", actor_id="route-scope-test", host="pytest")
    target = create_claim(
        ws,
        topic_id="librpa-screening",
        statement="The LibRPA target requires independent convergence validation.",
        evidence_profile="numerical",
        confidence_state="candidate",
        active_uncertainty="Cross-topic reasoning has not been revalidated.",
    )
    source = create_claim(
        ws,
        topic_id="quantum-gravity-notes",
        statement="The formal source method is valid only in its original scope.",
        evidence_profile="formal_theory",
        confidence_state="validated",
        active_uncertainty="Transfer to LibRPA is not evidence.",
    )
    record_research_program(
        ws,
        ResearchProgramRecord(
            program_id="program-route-scope",
            title="Reviewed cross-topic method comparison",
            primary_topic_ids=["librpa-screening"],
            supporting_topic_ids=["quantum-gravity-notes"],
            scientific_boundary="No claim trust transfers between topics.",
            inclusion_rules=["reviewed bridges only"],
            review_status="reviewed",
        ),
        actor=actor,
    )
    record_cross_topic_relation(
        ws,
        CrossTopicRelationRecord(
            relation_id="bridge-route-scope",
            source_topic_id="quantum-gravity-notes",
            target_topic_id="librpa-screening",
            source_ref=f"claim:{source.claim_id}",
            target_ref=f"claim:{target.claim_id}",
            relation_kind="method_candidate",
            transfer_rationale="Only the comparison pattern may be useful.",
            applicability_boundary="The source conclusion is never target evidence.",
            revalidation_requirements=["validate against the LibRPA target assumptions"],
            status="reviewed",
        ),
        actor=actor,
    )
    record_session_focus_set(
        ws,
        SessionFocusSetRecord(
            focus_set_id="focus-route-scope",
            session_id="session-librpa",
            primary_topic_id="librpa-screening",
            focus_kind="claim",
            focus_ref=f"claim:{target.claim_id}",
            supporting_refs=["cross_topic_relation:bridge-route-scope"],
            program_id="program-route-scope",
        ),
        actor=actor,
    )
    build_query_index(ws)
    watermark_before = current_canonical_watermark(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the exact LibRPA research session",
            explicit_session_ids=("session-librpa",),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "selected"
    assert decision.selected_topic_id == "librpa-screening"
    assert decision.supporting_topic_ids == ("quantum-gravity-notes",)
    assert decision.requires_target_revalidation is True
    supporting = [candidate for candidate in decision.candidates if candidate.supporting_only]
    assert len(supporting) == 1
    assert supporting[0].topic_id == "quantum-gravity-notes"
    assert supporting[0].session_id == "session-qg"
    assert supporting[0].requires_target_revalidation is True
    assert f"claim:{source.claim_id}" not in decision.candidates[0].exact_refs
    assert current_canonical_watermark(ws) == watermark_before


def test_resolver_routes_from_an_exact_non_session_record_anchor(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    claim = create_claim(
        ws,
        topic_id="quantum-gravity-notes",
        statement="A precise algebraic anchor for the formal theory topic.",
        evidence_profile="formal_theory",
        confidence_state="candidate",
        active_uncertainty="The next derivation remains open.",
    )
    build_query_index(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue from this exact canonical anchor",
            exact_refs=(f"claim:{claim.claim_id}",),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "selected"
    assert decision.selected_topic_id == "quantum-gravity-notes"
    assert decision.selected_session_id == "session-qg"
    assert decision.candidates[0].evidence_tier == "exact_anchor"
    assert f"claim:{claim.claim_id}" in decision.candidates[0].exact_refs


def test_exact_route_constraint_overrides_untrusted_generic_semantic_hint(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    claim = create_claim(
        ws,
        topic_id="quantum-gravity-notes",
        statement="The exact formal-theory route anchor.",
        evidence_profile="formal_theory",
        confidence_state="candidate",
        active_uncertainty="The semantic hint is intentionally contradictory.",
    )
    build_query_index(ws)

    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="What is the Fourier transform of a Gaussian?",
            exact_refs=(f"claim:{claim.claim_id}",),
            semantic_assessment={
                "task_kind": "generic_question",
                "is_generic_textbook_question": True,
                "should_use_aitp": "not_required",
            },
        ),
    )

    assert decision.status == "selected"
    assert decision.selected_topic_id == "quantum-gravity-notes"
    assert decision.candidates[0].evidence_tier == "exact_anchor"


def test_resolver_routes_from_one_explicit_topic_without_a_session_id(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    decision = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="Continue the explicitly selected research topic",
            explicit_topic_ids=("quantum-gravity-notes",),
            semantic_assessment={"should_use_aitp": "required"},
        ),
    )

    assert decision.status == "selected"
    assert decision.selected_topic_id == "quantum-gravity-notes"
    assert decision.selected_session_id == "session-qg"
    assert decision.candidates[0].evidence_tier == "explicit"


def test_resolver_uses_one_bounded_snapshot_and_never_calls_a_writer(
    tmp_path,
    monkeypatch,
):
    import brain.v5.dynamic_host_routing as routing
    import brain.v5.host_route_scope as route_scope
    import brain.v5.research_retrieval as retrieval
    import brain.v5.research_scope as research_scope
    from brain.v5.host_route_contracts import HostRouteRequest, route_decision_payload
    from brain.v5.record_repository import RecordRepository
    from brain.v5.research_retrieval import QuerySnapshotSession

    ws = _seed_two_topic_route_workspace(tmp_path)
    query_session = QuerySnapshotSession()
    calls = []
    original_query = retrieval.query_records

    def tracked_query(ws_arg, query, *, query_session=None):
        calls.append((query, query_session))
        return original_query(ws_arg, query, query_session=query_session)

    def forbidden_write(*_args, **_kwargs):
        pytest.fail("dynamic route resolution must never call a canonical writer")

    monkeypatch.setattr(routing, "query_records", tracked_query)
    monkeypatch.setattr(route_scope, "query_records", tracked_query)
    monkeypatch.setattr(research_scope, "query_records", tracked_query)
    monkeypatch.setattr(RecordRepository, "write", forbidden_write)
    request = HostRouteRequest(
        request_summary="Continue the quantum gravity von Neumann algebra notes",
        semantic_assessment={"should_use_aitp": "required"},
    )

    first = routing.resolve_host_research_route(
        ws,
        request,
        query_session=query_session,
    )
    second = routing.resolve_host_research_route(
        ws,
        request,
        query_session=QuerySnapshotSession(),
    )

    assert first.status == "selected"
    assert all(session is query_session for _query, session in calls[:4])
    assert all(query.limit <= 200 for query, _session in calls)
    assert any(query.limit == 48 for query, _session in calls)
    assert query_session.snapshot is not None
    assert route_decision_payload(first) == route_decision_payload(second)


def _cache_request(host_session_id="host-cache-1", **changes):
    from brain.v5.host_route_contracts import HostRouteRequest

    fields = {
        "request_summary": "Continue the exact LibRPA route",
        "host": "codex",
        "host_session_id": host_session_id,
        "project_root": "F:/AI_Workspace/Theoretical-Physics",
        "current_path": "research/librpa/run.py",
        "repo_id": "theoretical-physics",
        "branch": "main",
        "explicit_session_ids": ("session-librpa",),
        "semantic_assessment": {"should_use_aitp": "required"},
    }
    fields.update(changes)
    return HostRouteRequest(**fields)


def _selected_cache_decision(ws, request):
    from brain.v5.dynamic_host_routing import resolve_host_research_route

    decision = resolve_host_research_route(ws, request)
    assert decision.status == "selected"
    return decision


def _route_canonical_snapshot(ws):
    import hashlib

    patterns = (
        (ws.root / "registry", "**/*.md"),
        (ws.root / "contexts", "*/context.md"),
        (ws.root / "topics", "*/topic.md"),
        (ws.root / "runtime" / "sessions", "*.md"),
        (ws.root / "memory" / "l2" / "entries", "*.md"),
        (ws.root / "revisions", "**/*.md"),
    )
    return {
        path.resolve(): hashlib.sha256(path.read_bytes()).hexdigest()
        for root, pattern in patterns
        if root.exists()
        for path in root.glob(pattern)
    }


@pytest.mark.parametrize(
    "host_session_id",
    (
        "CON",
        "../../escape\\nested",
        "e\u0301-route-session",
        "x" * 500,
    ),
)
def test_route_cache_uses_only_contained_sha256_namespaces(tmp_path, host_session_id):
    from brain.v5.host_route_cache import write_host_route_mapping

    ws = _seed_two_topic_route_workspace(tmp_path)
    request = _cache_request(host_session_id)
    mapping = write_host_route_mapping(
        ws,
        request,
        _selected_cache_decision(ws, request),
    )
    path = (ws.base / mapping.runtime_path).resolve(strict=False)
    root = (ws.root / "runtime" / "host_routes").resolve(strict=False)

    assert path.is_relative_to(root)
    assert path.name == f"{mapping.namespace_sha256}.json"
    assert path.parent.name == mapping.namespace_sha256[:2]
    assert len(mapping.namespace_sha256) == 64
    assert host_session_id not in path.as_posix()


def test_route_cache_normalizes_unicode_identity_and_separates_namespaces(tmp_path):
    import unicodedata

    from brain.v5.host_route_cache import write_host_route_mapping

    ws = _seed_two_topic_route_workspace(tmp_path / "workspace-a")
    nfd = "e\u0301-host-session"
    nfc = unicodedata.normalize("NFC", nfd)
    first_request = _cache_request(nfd)
    second_request = _cache_request(nfc)
    first = write_host_route_mapping(
        ws,
        first_request,
        _selected_cache_decision(ws, first_request),
    )
    second = write_host_route_mapping(
        ws,
        second_request,
        _selected_cache_decision(ws, second_request),
    )
    other_request = _cache_request("other-host-session")
    other_session = write_host_route_mapping(
        ws,
        other_request,
        _selected_cache_decision(ws, other_request),
    )
    other_ws = _seed_two_topic_route_workspace(tmp_path / "workspace-b")
    other_workspace = write_host_route_mapping(
        other_ws,
        second_request,
        _selected_cache_decision(other_ws, second_request),
    )

    assert first.namespace_sha256 == second.namespace_sha256
    assert first.namespace_sha256 != other_session.namespace_sha256
    assert first.namespace_sha256 != other_workspace.namespace_sha256


def test_route_cache_rejects_runtime_symlink_escape(tmp_path):
    from brain.v5.host_route_cache import write_host_route_mapping

    ws = _seed_two_topic_route_workspace(tmp_path / "workspace")
    outside = tmp_path / "outside"
    outside.mkdir()
    route_root = ws.root / "runtime" / "host_routes"
    try:
        route_root.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")
    request = _cache_request()

    with pytest.raises(ValueError, match="escapes AITP runtime"):
        write_host_route_mapping(
            ws,
            request,
            _selected_cache_decision(ws, request),
        )


def test_route_cache_write_read_clear_is_canonical_neutral(tmp_path):
    from brain.v5.host_route_cache import (
        clear_host_route_mapping,
        read_host_route_mapping,
        write_host_route_mapping,
    )
    from brain.v5.query_index import current_canonical_watermark

    ws = _seed_two_topic_route_workspace(tmp_path)
    request = _cache_request()
    decision = _selected_cache_decision(ws, request)
    canonical_before = _route_canonical_snapshot(ws)
    watermark_before = current_canonical_watermark(ws)

    mapping = write_host_route_mapping(ws, request, decision)
    runtime_text = (ws.base / mapping.runtime_path).read_text(encoding="utf-8")
    assert request.request_summary not in runtime_text
    assert request.current_path not in runtime_text
    changed_summary = _cache_request(
        request_summary="A later turn in the same exact host route"
    )
    assert read_host_route_mapping(ws, changed_summary) == mapping
    assert clear_host_route_mapping(ws, changed_summary) is True
    assert clear_host_route_mapping(ws, changed_summary) is False

    assert _route_canonical_snapshot(ws) == canonical_before
    assert current_canonical_watermark(ws) == watermark_before


def test_route_cache_rejects_non_selected_decisions(tmp_path):
    from brain.v5.dynamic_host_routing import resolve_host_research_route
    from brain.v5.host_route_cache import write_host_route_mapping
    from brain.v5.host_route_contracts import HostRouteRequest

    ws = _seed_two_topic_route_workspace(tmp_path)
    outside = resolve_host_research_route(
        ws,
        HostRouteRequest(
            request_summary="What is the Fourier transform of a Gaussian?",
            semantic_assessment={
                "is_generic_textbook_question": True,
                "should_use_aitp": "not_required",
            },
        ),
    )

    with pytest.raises(ValueError, match="strongly verified selected route"):
        write_host_route_mapping(ws, _cache_request(), outside)


def test_route_cache_invalidates_after_index_generation_changes(tmp_path):
    from brain.v5.host_route_cache import (
        read_host_route_mapping,
        write_host_route_mapping,
    )
    from brain.v5.query_index import build_query_index

    ws = _seed_two_topic_route_workspace(tmp_path)
    request = _cache_request()
    write_host_route_mapping(
        ws,
        request,
        _selected_cache_decision(ws, request),
    )
    build_query_index(ws)

    assert read_host_route_mapping(ws, request) is None


def test_route_cache_tampering_and_continuity_changes_invalidate_mapping(tmp_path):
    from brain.v5.host_route_cache import (
        read_host_route_mapping,
        write_host_route_mapping,
    )

    ws = _seed_two_topic_route_workspace(tmp_path)
    request = _cache_request()
    mapping = write_host_route_mapping(
        ws,
        request,
        _selected_cache_decision(ws, request),
    )
    path = ws.base / mapping.runtime_path
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["selected_topic_id"] = "quantum-gravity-notes"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert read_host_route_mapping(ws, request) is None

    write_host_route_mapping(ws, request, _selected_cache_decision(ws, request))
    assert read_host_route_mapping(
        ws,
        _cache_request(repo_id="another-repository"),
    ) is None
    assert read_host_route_mapping(
        ws,
        _cache_request(explicit_session_ids=("session-qg",)),
    ) is None


def test_route_cache_expiry_and_missing_anchor_invalidate_mapping(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone

    import brain.v5.host_route_cache as cache

    ws = _seed_two_topic_route_workspace(tmp_path)
    request = _cache_request()
    now = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(cache, "_utc_now", lambda: now)
    cache.write_host_route_mapping(
        ws,
        request,
        _selected_cache_decision(ws, request),
    )

    monkeypatch.setattr(cache, "_utc_now", lambda: now + timedelta(days=2))
    assert cache.read_host_route_mapping(ws, request) is None

    monkeypatch.setattr(cache, "_utc_now", lambda: now)
    cache.write_host_route_mapping(
        ws,
        request,
        _selected_cache_decision(ws, request),
    )
    (ws.topic_dir("librpa-screening") / "topic.md").unlink()
    assert cache.read_host_route_mapping(ws, request) is None


def _seed_single_topic_route_workspace(base, topic_id, session_id):
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import bind_session, create_context, create_topic, init_workspace

    ws = init_workspace(base)
    create_context(ws, "shared-context", title="Shared Research Context")
    create_topic(
        ws,
        topic_id,
        context_id="shared-context",
        title="Shared observable continuation workflow",
    )
    bind_session(
        ws,
        session_id,
        topic_id=topic_id,
        context_id="shared-context",
        runtime="codex",
    )
    build_query_index(ws)
    return ws


def test_compact_autoroute_uses_requested_workspace_and_persists_selected_route(
    tmp_path,
):
    from brain.v5.capability_registry import compact_mcp_tools
    from brain.v5.compact_mcp_tools import aitp_v5_codex_autoroute
    from brain.v5.host_route_cache import read_host_route_mapping
    from brain.v5.host_route_contracts import HostRouteRequest

    left = _seed_single_topic_route_workspace(
        tmp_path / "left",
        "left-topic",
        "left-session",
    )
    right = _seed_single_topic_route_workspace(
        tmp_path / "right",
        "right-topic",
        "right-session",
    )

    def route(ws, host_session_id):
        return aitp_v5_codex_autoroute(
            str(ws.base),
            request_summary="Continue the shared observable workflow",
            route_context={
                "host": "codex",
                "host_session_id": host_session_id,
                "project_root": str(ws.base),
                "repo_id": "shared-repository",
                "branch": "main",
            },
            semantic_assessment={"should_use_aitp": "required"},
        )

    left_route = route(left, "host-left")
    right_route = route(right, "host-right")

    assert left_route["host_route_decision"]["status"] == "selected"
    assert left_route["host_route_decision"]["selected_topic_id"] == "left-topic"
    assert left_route["host_route_decision"]["selected_session_id"] == "left-session"
    assert right_route["host_route_decision"]["selected_topic_id"] == "right-topic"
    assert right_route["host_route_decision"]["selected_session_id"] == "right-session"
    assert left_route["recommended_next_tool"] == "aitp_v5_codex_enter"
    assert left_route["recommended_args"]["session_id"] == "left-session"
    assert left_route["runtime_continuity"]["status"] == "stored"
    assert len(compact_mcp_tools()) == 10

    cache_request = HostRouteRequest(
        request_summary="A later summary is allowed in the same host session",
        host="codex",
        host_session_id="host-left",
        project_root=str(left.base),
        repo_id="shared-repository",
        branch="main",
        semantic_assessment={"should_use_aitp": "required"},
    )
    assert read_host_route_mapping(left, cache_request) is not None
    assert len(json.dumps(left_route, ensure_ascii=False).encode("utf-8")) < 24_000
    serialized = json.dumps(left_route, ensure_ascii=False).casefold()
    for forbidden in ("skill_body", "raw_transcript", "context_pack", "full_memory"):
        assert forbidden not in serialized


def test_compact_autoroute_preserves_ambiguity_and_does_not_cache(tmp_path):
    from brain.v5.compact_mcp_tools import aitp_v5_codex_autoroute
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    for topic_id in ("librpa-screening", "quantum-gravity-notes"):
        create_claim(
            ws,
            topic_id=topic_id,
            statement="Shared compact ambiguity anchor",
            evidence_profile="formal_theory",
            confidence_state="candidate",
            active_uncertainty="A primary topic has not been chosen.",
        )
    build_query_index(ws)

    route = aitp_v5_codex_autoroute(
        str(ws.base),
        request_summary="Continue the shared compact ambiguity anchor",
        route_context={
            "host": "codex",
            "host_session_id": "host-ambiguous",
            "project_root": str(ws.base),
            "repo_id": "multi-topic-repository",
            "branch": "main",
        },
        semantic_assessment={"should_use_aitp": "required"},
    )

    assert route["host_route_decision"]["status"] == "ambiguous"
    assert len(route["host_route_decision"]["candidates"]) == 2
    assert route["recommended_next_tool"] == "none"
    assert route["runtime_continuity"]["status"] == "not_stored"
    route_root = ws.root / "runtime" / "host_routes"
    assert not route_root.exists() or not list(route_root.rglob("*.json"))


def test_compact_autoroute_rejects_unknown_route_context_fields(tmp_path):
    from brain.v5.compact_mcp_tools import aitp_v5_codex_autoroute

    ws = _seed_single_topic_route_workspace(
        tmp_path,
        "bounded-topic",
        "bounded-session",
    )
    with pytest.raises(ValueError, match="unsupported route_context fields"):
        aitp_v5_codex_autoroute(
            str(ws.base),
            request_summary="Continue the bounded route",
            route_context={
                "host": "codex",
                "host_session_id": "host-bounded",
                "raw_transcript": "must never enter the route contract",
            },
        )


@pytest.mark.parametrize(
    ("native_event", "expected_operation"),
    (
        ("PreToolUse", "delegate_existing_pre_tool_policy"),
        ("PostToolUse", "delegate_existing_post_tool_trace"),
    ),
)
def test_unresolved_dynamic_lifecycle_is_route_gated_before_bound_operations(
    tmp_path,
    monkeypatch,
    native_event,
    expected_operation,
):
    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )

    ws = _seed_two_topic_route_workspace(tmp_path)

    def forbidden(*_args, **_kwargs):
        pytest.fail("unresolved dynamic lifecycle crossed a bound or writer boundary")

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.get_session_binding", forbidden)
    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", forbidden)
    monkeypatch.setattr("brain.v5.research_moments.apply_research_moment_decision", forbidden)
    for target in (
        "brain.v5.evidence.record_evidence",
        "brain.v5.trust_updates.apply_trust_update",
        "brain.v5.memory.apply_promotion_packet",
        "brain.v5.skill_candidates.apply_project_skill",
        "brain.v5.skill_install_transactions.apply_skill_install_plan",
        "brain.v5.execution_baselines.accept_execution_baseline",
        "brain.v5.active_claim_focus.confirm_active_claim_rebind",
        "brain.v5.research_scope.record_session_focus_set",
        "brain.v5.workspace.bind_session",
        "brain.v5.lifecycle_facade.apply_session_closeout",
    ):
        monkeypatch.setattr(target, forbidden)
    event = normalize_host_lifecycle_event(
        "codex",
        native_event,
        {
            "event_id": f"event-unresolved-{native_event}",
            "host_session_id": "host-unresolved",
            "topic_id": "untrusted-topic-from-host",
            "tool_name": "pytest",
            "status": "completed",
            "raw_prompt": "must not be routed or persisted",
            "tool_output": {"nested": "must not become semantic input"},
        },
        session_id="",
        routing_mode="dynamic",
    )

    result = dispatch_host_lifecycle_event(ws, event)

    assert event.session_id == ""
    assert event.routing_mode == "dynamic"
    assert event.route_status == "unresolved"
    assert result.status == "route_required"
    assert result.operation == expected_operation
    assert result.session_id == ""
    assert result.topic_id == ""
    assert result.runtime_write is False
    assert result.canonical_write is False
    assert result.trust_effect == "none"
    assert "raw_prompt" not in repr(event)
    assert "nested" not in repr(event)


def test_dynamic_prompt_selects_before_context_and_pretool_reuses_exact_cache(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )

    ws = _seed_two_topic_route_workspace(tmp_path)
    captured = {}

    def prepare(ws_arg, request, *, deliver=None):
        captured["workspace"] = ws_arg
        captured["request"] = request
        return SimpleNamespace(
            receipt_id="context-injection-dynamic",
            injection_status="prepared",
        )

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", prepare)
    prompt = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "event-dynamic-prompt-qg",
            "host_session_id": "host-dynamic-qg",
            "research_relevant": True,
            "objective_text": "Continue the quantum gravity von Neumann algebra notes",
            "project_root": str(ws.base),
            "repo_id": "multi-topic-repository",
            "branch": "main",
        },
        session_id="",
        routing_mode="dynamic",
    )

    result = dispatch_host_lifecycle_event(ws, prompt)

    assert result.status == "context_prepared"
    assert result.session_id == "session-qg"
    assert result.topic_id == "quantum-gravity-notes"
    assert result.routing_mode == "dynamic"
    assert result.route_status == "selected"
    assert captured["request"].session_id == "session-qg"
    assert captured["request"].topic_id == "quantum-gravity-notes"

    pre_tool = normalize_host_lifecycle_event(
        "codex",
        "PreToolUse",
        {
            "event_id": "event-dynamic-pretool-qg",
            "host_session_id": "host-dynamic-qg",
            "project_root": str(ws.base),
            "repo_id": "multi-topic-repository",
            "branch": "main",
            "tool_name": "pytest",
        },
        session_id="",
        routing_mode="dynamic",
    )
    pre_result = dispatch_host_lifecycle_event(ws, pre_tool)

    assert pre_result.status == "policy_only"
    assert pre_result.session_id == "session-qg"
    assert pre_result.topic_id == "quantum-gravity-notes"
    assert pre_result.route_status == "selected"


def test_dynamic_prompt_exact_ref_is_selection_evidence_not_a_later_event_requirement(
    tmp_path,
    monkeypatch,
):
    from types import SimpleNamespace

    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    claim = create_claim(
        ws,
        topic_id="quantum-gravity-notes",
        statement="The exact QG claim selects the formal-theory session.",
        evidence_profile="formal_theory",
        confidence_state="candidate",
        active_uncertainty="The claim is routing evidence only.",
    )
    build_query_index(ws)
    monkeypatch.setattr(
        "brain.v5.host_lifecycle_dispatch.prepare_context_injection",
        lambda *_args, **_kwargs: SimpleNamespace(
            receipt_id="context-injection-exact-ref",
            injection_status="prepared",
        ),
    )
    prompt = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "event-dynamic-prompt-exact-ref",
            "host_session_id": "host-dynamic-exact-ref",
            "research_relevant": True,
            "objective_text": "Continue the exact referenced research item",
            "subject_refs": [f"claim:{claim.claim_id}"],
            "project_root": str(ws.base),
            "repo_id": "multi-topic-repository",
            "branch": "main",
        },
        routing_mode="dynamic",
    )
    selected = dispatch_host_lifecycle_event(ws, prompt)
    assert selected.route_status == "selected"
    assert selected.session_id == "session-qg"

    pre_tool = normalize_host_lifecycle_event(
        "codex",
        "PreToolUse",
        {
            "event_id": "event-dynamic-pretool-after-exact-ref",
            "host_session_id": "host-dynamic-exact-ref",
            "project_root": str(ws.base),
            "repo_id": "multi-topic-repository",
            "branch": "main",
            "tool_name": "pytest",
        },
        routing_mode="dynamic",
    )
    result = dispatch_host_lifecycle_event(ws, pre_tool)

    assert result.status == "policy_only"
    assert result.route_status == "selected"
    assert result.session_id == "session-qg"
    assert result.topic_id == "quantum-gravity-notes"


def test_ambiguous_dynamic_prompt_never_prepares_context_or_cache(tmp_path, monkeypatch):
    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    ws = _seed_two_topic_route_workspace(tmp_path)
    for topic_id in ("librpa-screening", "quantum-gravity-notes"):
        create_claim(
            ws,
            topic_id=topic_id,
            statement="Shared lifecycle ambiguity anchor",
            evidence_profile="formal_theory",
            confidence_state="candidate",
            active_uncertainty="No primary topic has been selected.",
        )
    build_query_index(ws)

    def forbidden(*_args, **_kwargs):
        pytest.fail("ambiguous dynamic prompt must not prepare session context")

    monkeypatch.setattr("brain.v5.host_lifecycle_dispatch.prepare_context_injection", forbidden)
    event = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "event-dynamic-ambiguous",
            "host_session_id": "host-dynamic-ambiguous",
            "research_relevant": True,
            "objective_text": "Continue the shared lifecycle ambiguity anchor",
            "project_root": str(ws.base),
        },
        session_id="",
        routing_mode="dynamic",
    )

    result = dispatch_host_lifecycle_event(ws, event)

    assert result.status == "route_ambiguous"
    assert result.session_id == ""
    assert result.topic_id == ""
    assert result.runtime_write is False
    assert result.canonical_write is False
    route_root = ws.root / "runtime" / "host_routes"
    assert not route_root.exists() or not list(route_root.rglob("*.json"))


def _seed_dynamic_qg_lifecycle_route(ws, monkeypatch, *, host_session_id):
    from types import SimpleNamespace

    from brain.v5.host_lifecycle_facade import (
        dispatch_host_lifecycle_event,
        normalize_host_lifecycle_event,
    )
    from brain.v5.query_index import build_query_index
    from brain.v5.workspace import create_claim

    claim = create_claim(
        ws,
        topic_id="quantum-gravity-notes",
        statement="The bounded QG route may stage a reviewed open direction.",
        evidence_profile="formal_theory",
        confidence_state="candidate",
        active_uncertainty="The open direction is not evidence.",
    )
    build_query_index(ws)
    monkeypatch.setattr(
        "brain.v5.host_lifecycle_dispatch.prepare_context_injection",
        lambda *_args, **_kwargs: SimpleNamespace(
            receipt_id="context-injection-dynamic-moment",
            injection_status="prepared",
        ),
    )
    prompt = normalize_host_lifecycle_event(
        "codex",
        "aitp_v5_codex_enter",
        {
            "event_id": "event-dynamic-prompt-moment",
            "host_session_id": host_session_id,
            "research_relevant": True,
            "objective_text": "Continue the quantum gravity von Neumann algebra notes",
            "project_root": str(ws.base),
        },
        routing_mode="dynamic",
    )
    selected = dispatch_host_lifecycle_event(ws, prompt)
    assert selected.route_status == "selected"
    assert selected.session_id == "session-qg"
    return claim


def _dynamic_qg_research_payload(claim_id, *, host_session_id, event_overrides=None):
    from dataclasses import asdict
    from datetime import datetime, timezone

    from brain.v5.research_moment_contracts import ResearchEvent

    source_event_id = "event-dynamic-post-moment"
    event = ResearchEvent(
        event_id="moment-event-dynamic-qg",
        event_type="RouteChanged",
        occurred_at=datetime.now(timezone.utc).isoformat(),
        host="codex",
        host_session_id=host_session_id,
        session_id="session-qg",
        topic_id="quantum-gravity-notes",
        subject_refs=(f"claim:{claim_id}",),
        objective_payload={},
        semantic_payload={
            "candidate_kind": "open_direction",
            "semantic_key": "bounded-qg-open-direction",
            "summary": "Review the bounded QG open direction.",
            "payload": {"status": "open"},
        },
        source_event_id=source_event_id,
        recursion_origin="host_native",
    )
    if event_overrides:
        event = replace(event, **event_overrides)
    return {
        "event_id": source_event_id,
        "host_session_id": host_session_id,
        "tool_name": "pytest",
        "status": "completed",
        "aitp_research_event": asdict(event),
    }


def test_dynamic_hook_moment_uses_exact_cached_route_and_preserves_five_pins(
    tmp_path,
    monkeypatch,
):
    from brain.v5.hook_research_moment_bridge import (
        process_explicit_hook_research_moment,
    )

    ws = _seed_two_topic_route_workspace(tmp_path)
    host_session_id = "host-dynamic-moment"
    claim = _seed_dynamic_qg_lifecycle_route(
        ws,
        monkeypatch,
        host_session_id=host_session_id,
    )
    result = process_explicit_hook_research_moment(
        ws,
        _dynamic_qg_research_payload(
            claim.claim_id,
            host_session_id=host_session_id,
        ),
        host="codex",
        session_id="",
        routing_mode="dynamic",
    )

    assert result["operation"] == "dispatch_validated_research_moment"
    assert result["status"] == "moment_staged"
    assert result["session_id"] == "session-qg"
    assert result["topic_id"] == "quantum-gravity-notes"
    assert result["route_status"] == "selected"
    assert result["canonical_write"] is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("host", "claude_code"),
        ("host_session_id", "other-host-session"),
        ("session_id", "session-librpa"),
        ("topic_id", "librpa-screening"),
        ("source_event_id", "other-source-event"),
    ),
)
def test_dynamic_hook_moment_rejects_each_identity_pin_drift(
    tmp_path,
    monkeypatch,
    field,
    replacement,
):
    from brain.v5.hook_research_moment_bridge import (
        process_explicit_hook_research_moment,
    )

    ws = _seed_two_topic_route_workspace(tmp_path)
    host_session_id = "host-dynamic-moment-drift"
    claim = _seed_dynamic_qg_lifecycle_route(
        ws,
        monkeypatch,
        host_session_id=host_session_id,
    )
    result = process_explicit_hook_research_moment(
        ws,
        _dynamic_qg_research_payload(
            claim.claim_id,
            host_session_id=host_session_id,
            event_overrides={field: replacement},
        ),
        host="codex",
        session_id="",
        routing_mode="dynamic",
    )

    assert result["kind"] == "research_moment_hook_diagnostic"
    assert result["status"] == "rejected"
    assert result["can_update_kernel_state"] is False
    assert result["can_update_claim_trust"] is False
